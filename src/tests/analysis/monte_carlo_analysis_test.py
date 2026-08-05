"""Unit tests for pyH2A.Analysis.Monte_Carlo_Analysis.

Covers pure helper functions, _mc_response_worker (h2_cost and LCA paths via
mocked Discounted_Cash_Flow), and Monte_Carlo_Analysis class methods tested in
isolation via minimal mock state — without running the full pipeline or
spawning worker processes.
"""
from unittest.mock import MagicMock, patch, ANY

import numpy as np
import pytest

from pyH2A.Analysis.Monte_Carlo_Analysis import (
    Monte_Carlo_Analysis,
    _mc_response_worker,
    calculate_distance,
    divide_into_batches,
    extend_limits,
    normalize_parameter,
    select_non_reference_value,
)
from pyH2A.Utilities.Unit_Handler.quantity import Quantity


# ── divide_into_batches ────────────────────────────────────────────────────────

class TestDivideIntoBatches:

    def test_even_split_produces_equal_batches(self):
        arr = np.arange(6)
        batches = divide_into_batches(arr, 2)
        assert len(batches) == 3
        assert all(len(b) == 2 for b in batches)

    def test_uneven_split_last_batch_is_smaller(self):
        arr = np.arange(7)
        batches = divide_into_batches(arr, 3)
        assert len(batches) == 3
        assert len(batches[0]) == 3
        assert len(batches[1]) == 3
        assert len(batches[2]) == 1

    def test_batch_size_larger_than_array_gives_single_batch(self):
        arr = np.arange(4)
        batches = divide_into_batches(arr, 10)
        assert len(batches) == 1
        assert len(batches[0]) == 4

    def test_empty_array_returns_empty_list(self):
        assert divide_into_batches(np.array([]), 3) == []

    def test_zero_batch_size_raises_value_error(self):
        with pytest.raises(ValueError, match='batch_size must be larger than zero'):
            divide_into_batches(np.arange(5), 0)

    def test_negative_batch_size_raises_value_error(self):
        with pytest.raises(ValueError, match='batch_size must be larger than zero'):
            divide_into_batches(np.arange(5), -1)

    def test_concatenating_batches_recovers_original_order(self):
        arr = np.arange(11)
        batches = divide_into_batches(arr, 3)
        np.testing.assert_array_equal(np.concatenate(batches), arr)


# ── select_non_reference_value ─────────────────────────────────────────────────

class TestSelectNonReferenceValue:

    def test_returns_second_when_first_is_reference(self):
        values = np.array([2.0, 5.0])
        assert select_non_reference_value(2.0, values) == 5.0

    def test_returns_first_when_second_is_reference(self):
        values = np.array([1.0, 3.5])
        assert select_non_reference_value(3.5, values) == 1.0


# ── normalize_parameter ────────────────────────────────────────────────────────

class TestNormalizeParameter:

    def test_linear_at_base_is_zero(self):
        assert normalize_parameter(1.0, base=1.0, limit=3.0) == pytest.approx(0.0)

    def test_linear_at_limit_is_one(self):
        assert normalize_parameter(3.0, base=1.0, limit=3.0) == pytest.approx(1.0)

    def test_linear_midpoint_is_half(self):
        assert normalize_parameter(1.5, base=1.0, limit=2.0) == pytest.approx(0.5)

    def test_log_at_base_is_zero(self):
        result = normalize_parameter(10.0, base=10.0, limit=100.0, log_normalize=True)
        assert result == pytest.approx(0.0)

    def test_log_at_limit_is_one(self):
        result = normalize_parameter(100.0, base=10.0, limit=100.0, log_normalize=True)
        assert result == pytest.approx(1.0)


# ── extend_limits ──────────────────────────────────────────────────────────────

class TestExtendLimits:

    def test_extends_both_bounds_symmetrically(self):
        result = extend_limits(np.array([0.0, 10.0]), 0.1)
        assert result[0] == pytest.approx(-1.0)
        assert result[1] == pytest.approx(11.0)

    def test_zero_extension_leaves_limits_unchanged(self):
        limits = np.array([2.0, 8.0])
        result = extend_limits(limits, 0.0)
        np.testing.assert_array_equal(result, limits)

    def test_does_not_mutate_original_array(self):
        original = np.array([0.0, 10.0])
        extend_limits(original, 0.2)
        np.testing.assert_array_equal(original, [0.0, 10.0])


# ── calculate_distance ─────────────────────────────────────────────────────────

class TestCalculateDistance:

    @staticmethod
    def _one_param(ref, limit):
        return {
            'param': {
                'Index': 0,
                'Reference': ref,
                'Limit': limit,
                'Values': np.array([ref, limit]),
            }
        }

    def test_reference_point_has_zero_distance(self):
        params = self._one_param(ref=1.0, limit=3.0)
        data = np.array([[1.0]])
        distances = calculate_distance(data, params, ['param'], metric='cityblock')
        assert distances[0, 0] == pytest.approx(0.0)

    def test_limit_point_has_unit_distance(self):
        params = self._one_param(ref=1.0, limit=3.0)
        data = np.array([[3.0]])
        distances = calculate_distance(data, params, ['param'], metric='cityblock')
        assert distances[0, 0] == pytest.approx(1.0)

    def test_midpoint_has_half_distance(self):
        params = self._one_param(ref=0.0, limit=2.0)
        data = np.array([[1.0]])
        distances = calculate_distance(data, params, ['param'], metric='cityblock')
        assert distances[0, 0] == pytest.approx(0.5)

    def test_two_params_both_at_limit_gives_unit_distance(self):
        params = {
            'p1': {'Index': 0, 'Reference': 0.0, 'Limit': 2.0},
            'p2': {'Index': 1, 'Reference': 0.0, 'Limit': 4.0},
        }
        data = np.array([[2.0, 4.0]])
        distances = calculate_distance(data, params, ['p1', 'p2'], metric='cityblock')
        assert distances[0, 0] == pytest.approx(1.0)


# ── _mc_response_worker ────────────────────────────────────────────────────────

class TestMcResponseWorker:

    @patch('pyH2A.Analysis.Monte_Carlo_Analysis.Discounted_Cash_Flow')
    def test_returns_h2_cost_for_every_sample(self, mock_dcf_class):
        mock_inst = MagicMock()
        mock_inst.h2_cost = 3.5
        mock_dcf_class.return_value = mock_inst

        result = _mc_response_worker(np.array([[1.0], [2.0], [3.0]]), {}, {}, 'h2_cost')

        assert result == [3.5, 3.5, 3.5]
        assert mock_dcf_class.call_count == 3

    @patch('pyH2A.Analysis.Monte_Carlo_Analysis.Discounted_Cash_Flow')
    def test_returns_lca_variable_for_non_h2_cost_key(self, mock_dcf_class):
        mock_inst = MagicMock()
        mock_inst.lca.lca_results = {'Climate change': Quantity(0.45, 'kg')}
        mock_dcf_class.return_value = mock_inst

        result = _mc_response_worker(np.array([[1.0], [2.0]]), {}, {}, 'Climate change')

        assert result == [0.45, 0.45]

    @patch('pyH2A.Analysis.Monte_Carlo_Analysis.Discounted_Cash_Flow')
    def test_empty_batch_returns_empty_list_without_calling_dcf(self, mock_dcf_class):
        result = _mc_response_worker(np.empty((0, 1)), {}, {}, 'h2_cost')
        assert result == []
        mock_dcf_class.assert_not_called()

    @patch('pyH2A.Analysis.Monte_Carlo_Analysis.Discounted_Cash_Flow')
    def test_original_inp_is_not_mutated_between_samples(self, mock_dcf_class):
        received = []

        def capture(inp, print_info=False):
            received.append(inp)
            return MagicMock(h2_cost=1.0)

        mock_dcf_class.side_effect = capture

        original_inp = {'key': 'original'}
        _mc_response_worker(np.array([[1.0], [2.0]]), original_inp, {}, 'h2_cost')

        assert original_inp == {'key': 'original'}
        assert all(d is not original_inp for d in received)

    @patch('pyH2A.Analysis.Monte_Carlo_Analysis.set_by_path')
    @patch('pyH2A.Analysis.Monte_Carlo_Analysis.Discounted_Cash_Flow')
    def test_set_by_path_called_with_parameter_value_and_type(
            self, mock_dcf_class, mock_set_by_path):
        mock_dcf_class.return_value = MagicMock(h2_cost=2.0)

        path = ['Section', 'Param', 'Value']
        parameters = {'p': {'Parameter': path, 'Index': 0, 'Type': 'value'}}
        _mc_response_worker(np.array([[7.0]]), {}, parameters, 'h2_cost')

        args, kwargs = mock_set_by_path.call_args
        assert args[1] == path
        assert float(args[2]) == pytest.approx(7.0)
        assert kwargs['value_type'] == 'value'


# ── Monte_Carlo_Analysis class methods ─────────────────────────────────────────

def _make_mc(**attrs):
    """Instantiate Monte_Carlo_Analysis without running __init__."""
    mc = object.__new__(Monte_Carlo_Analysis)
    for k, v in attrs.items():
        setattr(mc, k, v)
    return mc


class TestSaveResults:

    def test_header_contains_parameter_name_and_response_header(self, tmp_path):
        params = {
            'Catalyst Cost': {
                'Parameter': ['Catalyst', 'Cost', 'Value'],
                'Type': 'value',
                'Values': np.array([1.0, 5.0]),
                'Index': 0,
            }
        }
        results = np.array([[1.5, 3.2], [2.0, 4.1]])
        mc = _make_mc(
            parameters=params,
            results=results,
            dependent_variable_header='cost',
        )
        out = tmp_path / 'mc.txt'
        mc.save_results(str(out))

        content = out.read_text()
        assert 'Catalyst Cost' in content
        assert 'cost' in content

    def test_data_rows_are_written_correctly(self, tmp_path):
        params = {
            'p': {'Parameter': ['A', 'B', 'Value'], 'Type': 'value',
                  'Values': np.array([1.0, 3.0]), 'Index': 0}
        }
        results = np.array([[2.0, 7.5]])
        mc = _make_mc(parameters=params, results=results, dependent_variable_header='cost')
        out = tmp_path / 'mc.txt'
        mc.save_results(str(out))

        loaded = np.loadtxt(str(out), comments='#', delimiter='\t', ndmin=2)
        np.testing.assert_allclose(loaded, results)


class TestConfigureDependentVariable:

    def _mc_for(self, dep_var):
        return _make_mc(inp={'Monte_Carlo_Analysis': {'Dependent Variable': {'Value': dep_var}}})

    def test_h2_cost_sets_correct_label_and_header(self):
        mc = self._mc_for('h2_cost')
        mc.configure_dependent_variable()
        assert mc.dependent_variable == 'h2_cost'
        assert 'H2 Cost' in mc.dependent_variable_label
        assert 'cost' in mc.target_range_header

    def test_climate_change_sets_correct_label(self):
        mc = self._mc_for('Climate change')
        mc.configure_dependent_variable()
        assert mc.dependent_variable == 'Climate change'
        assert 'Climate change' in mc.dependent_variable_label

    def test_cumulative_energy_demand_sets_correct_label(self):
        mc = self._mc_for('Cumulative energy demand')
        mc.configure_dependent_variable()
        assert 'energy demand' in mc.dependent_variable_label.lower()

    def test_unsupported_variable_raises_value_error(self):
        mc = self._mc_for('not_a_valid_variable')
        with pytest.raises(ValueError, match='Unsupported Dependent Variable'):
            mc.configure_dependent_variable()

    def test_missing_dependent_variable_key_raises_key_error(self):
        mc = _make_mc(inp={'Monte_Carlo_Analysis': {}})
        with pytest.raises(KeyError):
            mc.configure_dependent_variable()


class TestTargetResponseComponents:

    @staticmethod
    def _results_with_responses(*responses):
        n = len(responses)
        param_cols = np.ones((n, 2))
        return np.c_[param_cols, np.array(responses, dtype=float)]

    def test_keeps_only_samples_within_range(self):
        results = self._results_with_responses(0.3, 0.8, 1.2, 1.8)
        mc = _make_mc(results=results, target_response_range=np.array([0.5, 1.5]))
        mc.target_response_components()
        assert mc.target_response_data.shape[0] == 2
        assert np.all(mc.target_response_data[:, -1] >= 0.5)
        assert np.all(mc.target_response_data[:, -1] <= 1.5)

    def test_output_is_sorted_ascending_by_response(self):
        results = self._results_with_responses(1.2, 0.7, 1.0)
        mc = _make_mc(results=results, target_response_range=np.array([0.5, 1.5]))
        mc.target_response_components()
        responses = mc.target_response_data[:, -1]
        assert list(responses) == sorted(responses)

    def test_no_samples_in_range_raises_value_error(self):
        results = self._results_with_responses(0.1, 0.2, 0.3)
        mc = _make_mc(
            results=results,
            target_response_range=np.array([2.0, 3.0]),
            dependent_variable='h2_cost',
        )
        with pytest.raises(ValueError, match='No Monte Carlo samples'):
            mc.target_response_components()

    def test_boundary_values_are_included(self):
        results = self._results_with_responses(0.5, 1.0, 1.5)
        mc = _make_mc(results=results, target_response_range=np.array([0.5, 1.5]))
        mc.target_response_components()
        assert mc.target_response_data.shape[0] == 3


class TestCheckParameterIntegrity:

    @staticmethod
    def _params(lo, hi, ref, limit, idx=0):
        return {
            'param_a': {
                'Values': np.array([lo, hi]),
                'Reference': ref,
                'Limit': limit,
                'Index': idx,
            }
        }

    def test_valid_data_within_range_passes(self):
        params = self._params(1.0, 3.0, ref=1.0, limit=3.0)
        data = np.array([[1.5, 0.0], [2.0, 0.0]])
        mc = _make_mc(parameters=params)
        mc.check_parameter_integrity(data)  # must not raise

    def test_value_below_minimum_raises_assertion_error(self):
        params = self._params(1.0, 3.0, ref=1.0, limit=3.0)
        data = np.array([[0.5, 0.0]])
        mc = _make_mc(parameters=params)
        with pytest.raises(AssertionError):
            mc.check_parameter_integrity(data)

    def test_value_above_maximum_raises_assertion_error(self):
        params = self._params(1.0, 3.0, ref=1.0, limit=3.0)
        data = np.array([[3.5, 0.0]])
        mc = _make_mc(parameters=params)
        with pytest.raises(AssertionError):
            mc.check_parameter_integrity(data)


class TestDeterminePrincipalComponents:

    def test_principal_list_is_ordered_by_input_index(self):
        parameters = {
            'alpha': {'Input Index': 1, 'Index': 0, 'Reference': 1.0},
            'beta':  {'Input Index': 0, 'Index': 1, 'Reference': 2.0},
        }
        mc = _make_mc(parameters=parameters)
        mc.determine_principal_components()
        assert mc.principal[0] == 'beta'
        assert mc.principal[1] == 'alpha'

    def test_base_case_list_is_ordered_by_column_index(self):
        parameters = {
            'alpha': {'Input Index': 0, 'Index': 1, 'Reference': 5.0},
            'beta':  {'Input Index': 1, 'Index': 0, 'Reference': 3.0},
        }
        mc = _make_mc(parameters=parameters)
        mc.determine_principal_components()
        assert mc.base_case[0] == 3.0
        assert mc.base_case[1] == 5.0

    def test_single_parameter_produces_one_element_lists(self):
        parameters = {
            'only': {'Input Index': 0, 'Index': 0, 'Reference': 7.0},
        }
        mc = _make_mc(parameters=parameters)
        mc.determine_principal_components()
        assert mc.principal == ['only']
        assert mc.base_case == [7.0]
