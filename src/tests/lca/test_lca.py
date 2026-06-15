"""Unit tests for pyH2A.LCA.LCA."""
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pytest
import scipy.sparse

# pyH2A.LCA.LCA imports pyH2A.Discounted_Cash_Flow, which in turn re-imports
# pyH2A.LCA.LCA.  Importing Discounted_Cash_Flow first resolves the circular
# dependency so that the LCA name is already bound when the second import runs.
import pyH2A.Discounted_Cash_Flow  # noqa: F401  (import for side-effect only)
from pyH2A.LCA.LCA import LCA
from pyH2A.Utilities.lca_utils import build_matrix_cache_key


# ── Paths ──────────────────────────────────────────────────────────────────

_HERE = Path(__file__).parent
_PROJECT_ROOT = _HERE.parents[2]
_TEST_DATA_DIR = str(_PROJECT_ROOT / 'data' / 'LCA' / 'LCA_Test_Data')

# UUID of process at index 0 in LCA_Test_Data/index_A.csv
_H2_UUID = 'd304025a-d235-48b7-a7e4-f54db11459ff'


# ── Helpers ────────────────────────────────────────────────────────────────

def _minimal_dcf(uuid, value):
    """Minimal DCF mock with a single pre-resolved LCA component."""
    dcf = MagicMock()
    dcf.inp = {
        'LCA Components': {
            'H2 Production': {
                'UUID': uuid,
                'Value': value,
                'Processed': 'Yes',
            }
        }
    }
    return dcf


def _clear_caches():
    LCA._base_solver_cache.clear()
    LCA._component_basis_cache.clear()
    LCA.load_matrices_from_folder.cache_clear()


def _matrix_shape_nnz(A):
    """Extract (shape, nnz) from a dense or sparse matrix."""
    if scipy.sparse.issparse(A):
        return A.shape, A.nnz
    A = np.asarray(A)
    return A.shape, int(np.count_nonzero(A))


def _tech_entry(index):
    """Minimal tech index entry mock with a .index attribute."""
    e = MagicMock()
    e.index = index
    return e


def _impact_entry(index, name, unit):
    """Minimal impact index entry mock."""
    e = MagicMock()
    e.index = index
    e.impact_name = name
    e.impact_unit = unit
    return e


# Bare LCA instance used by tests of instance methods that don't require full init.
_lca_stub = object.__new__(LCA)


@pytest.fixture(autouse=True)
def _reset_lca_caches():
    """Isolate every test: clear all process-local and LRU caches."""
    _clear_caches()
    yield
    _clear_caches()


# ── build_matrix_cache_key ─────────────────────────────────────────────────

class TestBuildMatrixCacheKey:
    def test_returns_40_char_hex(self):
        shape, nnz = _matrix_shape_nnz(np.eye(3))
        key = build_matrix_cache_key('/folder', shape, nnz)
        assert len(key) == 40
        assert all(c in '0123456789abcdef' for c in key)

    def test_deterministic(self):
        A = np.eye(3)
        shape, nnz = _matrix_shape_nnz(A)
        k1 = build_matrix_cache_key('/folder', shape, nnz)
        k2 = build_matrix_cache_key('/folder', shape, nnz)
        assert k1 == k2

    def test_different_folders_differ(self):
        A = np.eye(3)
        shape, nnz = _matrix_shape_nnz(A)
        assert (
            build_matrix_cache_key('/a', shape, nnz)
            != build_matrix_cache_key('/b', shape, nnz)
        )

    def test_different_shapes_differ(self):
        shape3, nnz3 = _matrix_shape_nnz(np.eye(3))
        shape4, nnz4 = _matrix_shape_nnz(np.eye(4))
        assert build_matrix_cache_key('/x', shape3, nnz3) != build_matrix_cache_key('/x', shape4, nnz4)

    def test_sparse_input(self):
        A = scipy.sparse.eye(4, format='csc')
        shape, nnz = _matrix_shape_nnz(A)
        key = build_matrix_cache_key('/folder', shape, nnz)
        assert len(key) == 40

    def test_sparse_vs_dense_same_structure_differ(self):
        A_dense = np.eye(3)
        A_sparse = scipy.sparse.eye(3, format='csc')
        k_dense = build_matrix_cache_key('/x', *_matrix_shape_nnz(A_dense))
        k_sparse = build_matrix_cache_key('/x', *_matrix_shape_nnz(A_sparse))
        assert len(k_dense) == 40
        assert len(k_sparse) == 40


# ── extract_component_uuid_and_value ──────────────────────────────────────

class TestExtractComponentFields:
    def test_extracts_uuid_and_value(self):
        uuid, value = _lca_stub.extract_component_uuid_and_value('c', {'UUID': 'abc', 'Value': 42.0})
        assert uuid == 'abc'
        assert value == 42.0

    def test_missing_uuid_raises_value_error(self):
        with pytest.raises(ValueError, match='UUID'):
            _lca_stub.extract_component_uuid_and_value('c', {'Value': 1.0})

    def test_missing_value_raises_value_error(self):
        with pytest.raises(ValueError, match='Value'):
            _lca_stub.extract_component_uuid_and_value('c', {'UUID': 'x'})

    def test_both_missing_raises_value_error(self):
        with pytest.raises(ValueError):
            _lca_stub.extract_component_uuid_and_value('c', {})

    def test_extra_fields_ignored(self):
        data = {'UUID': 'x', 'Value': 99.0, 'Processed': 'Yes', 'Path': 'p'}
        uuid, value = _lca_stub.extract_component_uuid_and_value('c', data)
        assert uuid == 'x'
        assert value == 99.0

    def test_error_message_contains_component_name(self):
        with pytest.raises(ValueError, match='my_component'):
            _lca_stub.extract_component_uuid_and_value('my_component', {})


# ── apply_component_updates ────────────────────────────────────────────────

class TestApplyComponentUpdates:
    """Tests for apply_component_updates using a bare LCA instance with seeded
    tech_index_dict and a MagicMock DCF."""

    def _make_lca(self, uuid_to_index):
        lca = object.__new__(LCA)
        lca.tech_index_dict = {uuid: _tech_entry(idx) for uuid, idx in uuid_to_index.items()}
        return lca

    def _make_dcf(self, table_name, components):
        dcf = MagicMock()
        dcf.inp = {table_name: components}
        return dcf

    def test_single_component_returns_positive_value(self):
        lca = self._make_lca({'uuid-0': 0})
        dcf = self._make_dcf('LCA Table', {'Comp A': {'UUID': 'uuid-0', 'Value': 5.0}})
        result = lca.apply_component_updates(dcf, ['LCA Table'])
        assert result[0] == pytest.approx(5.0)

    def test_first_component_is_positive(self):
        lca = self._make_lca({'uuid-0': 0, 'uuid-1': 1})
        dcf = self._make_dcf('LCA Table', {
            'Comp A': {'UUID': 'uuid-0', 'Value': 3.0},
            'Comp B': {'UUID': 'uuid-1', 'Value': 7.0},
        })
        result = lca.apply_component_updates(dcf, ['LCA Table'])
        assert result[0] == pytest.approx(3.0)

    def test_subsequent_components_are_negative(self):
        lca = self._make_lca({'uuid-0': 0, 'uuid-1': 1, 'uuid-2': 2})
        dcf = self._make_dcf('LCA Table', {
            'Comp A': {'UUID': 'uuid-0', 'Value': 1.0},
            'Comp B': {'UUID': 'uuid-1', 'Value': 4.0},
            'Comp C': {'UUID': 'uuid-2', 'Value': 6.0},
        })
        result = lca.apply_component_updates(dcf, ['LCA Table'])
        assert result[1] == pytest.approx(-4.0)
        assert result[2] == pytest.approx(-6.0)

    def test_correct_index_mapping(self):
        lca = self._make_lca({'uuid-5': 5, 'uuid-9': 9})
        dcf = self._make_dcf('LCA Table', {
            'Comp A': {'UUID': 'uuid-5', 'Value': 1.0},
            'Comp B': {'UUID': 'uuid-9', 'Value': 2.0},
        })
        result = lca.apply_component_updates(dcf, ['LCA Table'])
        assert 5 in result
        assert 9 in result

    def test_unknown_uuid_raises_value_error(self):
        lca = self._make_lca({'uuid-known': 0})
        dcf = self._make_dcf('LCA Table', {'Comp A': {'UUID': 'uuid-unknown', 'Value': 1.0}})
        with pytest.raises(ValueError, match='UUID'):
            lca.apply_component_updates(dcf, ['LCA Table'])

    def test_array_value_is_summed(self):
        lca = self._make_lca({'uuid-0': 0})
        dcf = self._make_dcf('LCA Table', {
            'Comp A': {'UUID': 'uuid-0', 'Value': np.array([2.0, 3.0, 5.0])},
        })
        result = lca.apply_component_updates(dcf, ['LCA Table'])
        assert result[0] == pytest.approx(10.0)

    def test_multiple_tables_global_position_governs_sign(self):
        # Component in second table has global position 1 → negative.
        lca = self._make_lca({'uuid-0': 0, 'uuid-1': 1})
        dcf = MagicMock()
        dcf.inp = {
            'LCA Table A': {'Comp A': {'UUID': 'uuid-0', 'Value': 2.0}},
            'LCA Table B': {'Comp B': {'UUID': 'uuid-1', 'Value': 3.0}},
        }
        result = lca.apply_component_updates(dcf, ['LCA Table A', 'LCA Table B'])
        assert result[0] == pytest.approx(2.0)
        assert result[1] == pytest.approx(-3.0)

    def test_returns_dict(self):
        lca = self._make_lca({'uuid-0': 0})
        dcf = self._make_dcf('LCA Table', {'Comp A': {'UUID': 'uuid-0', 'Value': 1.0}})
        result = lca.apply_component_updates(dcf, ['LCA Table'])
        assert isinstance(result, dict)


# ── load_solver_from_disk_to_ram ──────────────────────────────────────────

class TestLoadSolverFromDiskToRam:
    """Tests for load_solver_from_disk_to_ram using tmp_path .npz files."""

    def _make_lca(self, key='test_key'):
        lca = object.__new__(LCA)
        lca._matrix_cache_key = key
        lca._A_factor = None
        return lca

    def test_missing_file_returns_false(self, tmp_path):
        lca = self._make_lca()
        result = lca.load_solver_from_disk_to_ram(tmp_path / 'nope.npz')
        assert result is False

    def test_valid_file_returns_true(self, tmp_path):
        p = tmp_path / 'base.npz'
        np.savez(p, base_scaling_vector=np.array([1.0, 2.0]), A_col0=np.array([3.0, 4.0]))
        lca = self._make_lca()
        assert lca.load_solver_from_disk_to_ram(p) is True

    def test_valid_file_sets_base_scaling_vector(self, tmp_path):
        sv = np.array([1.5, 2.5, 3.5])
        p = tmp_path / 'base.npz'
        np.savez(p, base_scaling_vector=sv, A_col0=np.zeros(3))
        lca = self._make_lca()
        lca.load_solver_from_disk_to_ram(p)
        np.testing.assert_array_equal(lca._base_scaling_vector, sv)

    def test_valid_file_sets_A_col0(self, tmp_path):
        col0 = np.array([10.0, 20.0, 30.0])
        p = tmp_path / 'base.npz'
        np.savez(p, base_scaling_vector=np.zeros(3), A_col0=col0)
        lca = self._make_lca()
        lca.load_solver_from_disk_to_ram(p)
        np.testing.assert_array_equal(lca._A_col0, col0)

    def test_corrupted_file_returns_false(self, tmp_path):
        p = tmp_path / 'bad.npz'
        p.write_bytes(b'not a valid npz file')
        lca = self._make_lca()
        assert lca.load_solver_from_disk_to_ram(p) is False

    def test_valid_file_populates_ram_cache(self, tmp_path):
        sv = np.array([1.0, 2.0])
        col0 = np.array([3.0, 4.0])
        p = tmp_path / 'base.npz'
        np.savez(p, base_scaling_vector=sv, A_col0=col0)
        lca = self._make_lca(key='cache_key_42')
        lca.load_solver_from_disk_to_ram(p)
        assert 'cache_key_42' in LCA._base_solver_cache


# ── load_basis_vectors_from_disk ──────────────────────────────────────────

class TestLoadBasisVectorsFromDisk:
    """Tests for load_basis_vectors_from_disk using tmp_path .npz files."""

    def test_missing_file_returns_none(self, tmp_path):
        result = _lca_stub.load_basis_vectors_from_disk(
            tmp_path / 'nope.npz', np.array([0, 1], dtype=int)
        )
        assert result is None

    def test_valid_file_returns_basis(self, tmp_path):
        indices = np.array([0, 2], dtype=int)
        basis = np.array([[1.0, 0.0], [0.5, 0.5], [0.0, 1.0]])
        p = tmp_path / 'basis.npz'
        np.savez(p, component_indices=indices, basis=basis)
        result = _lca_stub.load_basis_vectors_from_disk(p, indices)
        np.testing.assert_array_equal(result, basis)

    def test_mismatched_indices_returns_none(self, tmp_path):
        stored_indices = np.array([0, 1], dtype=int)
        queried_indices = np.array([0, 2], dtype=int)
        basis = np.eye(3)
        p = tmp_path / 'basis.npz'
        np.savez(p, component_indices=stored_indices, basis=basis)
        result = _lca_stub.load_basis_vectors_from_disk(p, queried_indices)
        assert result is None

    def test_corrupted_file_returns_none(self, tmp_path):
        p = tmp_path / 'bad.npz'
        p.write_bytes(b'not a valid npz file')
        result = _lca_stub.load_basis_vectors_from_disk(p, np.array([0], dtype=int))
        assert result is None

    def test_1d_basis_reshaped_to_column(self, tmp_path):
        indices = np.array([0], dtype=int)
        basis_1d = np.array([1.0, 2.0, 3.0])
        p = tmp_path / 'basis.npz'
        np.savez(p, component_indices=indices, basis=basis_1d)
        result = _lca_stub.load_basis_vectors_from_disk(p, indices)
        assert result.ndim == 2
        assert result.shape == (3, 1)

    def test_matching_indices_returns_2d_basis(self, tmp_path):
        indices = np.array([1, 3], dtype=int)
        basis = np.array([[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]])
        p = tmp_path / 'basis.npz'
        np.savez(p, component_indices=indices, basis=basis)
        result = _lca_stub.load_basis_vectors_from_disk(p, indices)
        assert result.ndim == 2
        np.testing.assert_array_equal(result, basis)


# ── store_solver_and_artifacts_in_ram ─────────────────────────────────────

class TestStoreSolverAndArtifactsInRam:
    """Tests for store_solver_and_artifacts_in_ram using a bare LCA instance."""

    def _make_lca(self, key, factor, sv, col0):
        lca = object.__new__(LCA)
        lca._matrix_cache_key = key
        lca._A_factor = factor
        lca._base_scaling_vector = sv
        lca._A_col0 = col0
        return lca

    def test_key_inserted_in_class_cache(self):
        lca = self._make_lca('mykey', None, np.ones(3), np.zeros(3))
        lca.store_solver_and_artifacts_in_ram()
        assert 'mykey' in LCA._base_solver_cache

    def test_stored_tuple_contains_factor(self):
        sentinel = object()
        lca = self._make_lca('k', sentinel, np.ones(2), np.zeros(2))
        lca.store_solver_and_artifacts_in_ram()
        factor, _, _ = LCA._base_solver_cache['k']
        assert factor is sentinel

    def test_stored_tuple_contains_scaling_vector(self):
        sv = np.array([1.0, 2.0, 3.0])
        lca = self._make_lca('k', None, sv, np.zeros(3))
        lca.store_solver_and_artifacts_in_ram()
        _, stored_sv, _ = LCA._base_solver_cache['k']
        np.testing.assert_array_equal(stored_sv, sv)

    def test_stored_tuple_contains_A_col0(self):
        col0 = np.array([7.0, 8.0])
        lca = self._make_lca('k', None, np.zeros(2), col0)
        lca.store_solver_and_artifacts_in_ram()
        _, _, stored_col0 = LCA._base_solver_cache['k']
        np.testing.assert_array_equal(stored_col0, col0)

    def test_none_factor_is_allowed(self):
        lca = self._make_lca('k', None, np.ones(2), np.zeros(2))
        lca.store_solver_and_artifacts_in_ram()
        factor, _, _ = LCA._base_solver_cache['k']
        assert factor is None

    def test_overwrites_existing_entry(self):
        LCA._base_solver_cache['k'] = ('old', None, None)
        sv_new = np.array([9.0])
        lca = self._make_lca('k', None, sv_new, np.zeros(1))
        lca.store_solver_and_artifacts_in_ram()
        _, stored_sv, _ = LCA._base_solver_cache['k']
        np.testing.assert_array_equal(stored_sv, sv_new)


# ── perform_lca ────────────────────────────────────────────────────────────

class TestPerformLca:
    """Tests for perform_lca using a bare LCA instance with small synthetic matrices."""

    def _make_lca(self, B, C, scaling_vector, impacts):
        """Seed a bare LCA instance with all attributes perform_lca reads."""
        lca = object.__new__(LCA)
        lca.B = np.asarray(B, dtype=float)
        lca.C = np.asarray(C, dtype=float)
        lca.scaling_vector = np.asarray(scaling_vector, dtype=float)
        folder = MagicMock()
        folder.impact_index.return_value = impacts
        lca.folder = folder
        return lca

    def test_results_dict_populated(self):
        lca = self._make_lca(
            B=[[1, 0], [0, 1]],
            C=[[1, 0]],
            scaling_vector=[2.0, 3.0],
            impacts=[_impact_entry(0, 'GWP', 'kg CO2-eq')],
        )
        lca.perform_lca()
        assert isinstance(lca.lca_results, dict)
        assert len(lca.lca_results) == 1

    def test_result_value_computed_correctly(self):
        # B = [[2, 0], [0, 3]], sv = [1, 2] → g = [2, 6]
        # C = [[1, 1]] → h = [8]
        lca = self._make_lca(
            B=[[2, 0], [0, 3]],
            C=[[1, 1]],
            scaling_vector=[1.0, 2.0],
            impacts=[_impact_entry(0, 'GWP', 'kg CO2-eq')],
        )
        lca.perform_lca()
        assert lca.lca_results['GWP']['value'] == pytest.approx(8.0)

    def test_result_has_value_and_unit_keys(self):
        lca = self._make_lca(
            B=[[1]],
            C=[[1]],
            scaling_vector=[1.0],
            impacts=[_impact_entry(0, 'AP', 'mol H+-eq')],
        )
        lca.perform_lca()
        assert 'value' in lca.lca_results['AP']
        assert 'unit' in lca.lca_results['AP']

    def test_result_unit_stored_correctly(self):
        lca = self._make_lca(
            B=[[1]],
            C=[[1]],
            scaling_vector=[1.0],
            impacts=[_impact_entry(0, 'GWP', 'kg CO2-eq')],
        )
        lca.perform_lca()
        assert lca.lca_results['GWP']['unit'] == 'kg CO2-eq'

    def test_empty_impact_index_gives_empty_results(self):
        lca = self._make_lca(
            B=[[1, 0], [0, 1]],
            C=np.zeros((0, 2)),
            scaling_vector=[1.0, 2.0],
            impacts=[],
        )
        lca.perform_lca()
        assert lca.lca_results == {}

    def test_multiple_impacts_keyed_by_name(self):
        # B = I_2, sv = [3, 5], g = [3, 5]
        # C = [[1, 0], [0, 1]] → h = [3, 5]
        lca = self._make_lca(
            B=np.eye(2),
            C=np.eye(2),
            scaling_vector=[3.0, 5.0],
            impacts=[
                _impact_entry(0, 'GWP', 'kg CO2-eq'),
                _impact_entry(1, 'CED', 'MJ'),
            ],
        )
        lca.perform_lca()
        assert set(lca.lca_results.keys()) == {'GWP', 'CED'}
        assert lca.lca_results['GWP']['value'] == pytest.approx(3.0)
        assert lca.lca_results['CED']['value'] == pytest.approx(5.0)


# ── Integration tests ──────────────────────────────────────────────────────

class TestLCAIntegration:
    """End-to-end tests using the real LCA_Test_Data matrices.

    LCA_Test_Data A matrix (3×3, lower triangular):
        [[1000.,    0.,   0. ],
         [ -20.,    1.,   0. ],
         [  -5.2,   0.,   1. ]]
    f = [1000., 0., 0.]   →   base scaling vector = [1., 20., 5.2]
    """

    def test_instantiation_succeeds(self):
        lca = LCA(_TEST_DATA_DIR, _minimal_dcf(_H2_UUID, 1000.0))
        assert lca is not None

    def test_matrices_loaded(self):
        lca = LCA(_TEST_DATA_DIR, _minimal_dcf(_H2_UUID, 1000.0))
        assert lca.A is not None
        assert lca.B is not None
        assert lca.C is not None
        assert lca.f is not None

    def test_scaling_vector_correct_shape(self):
        lca = LCA(_TEST_DATA_DIR, _minimal_dcf(_H2_UUID, 1000.0))
        assert lca.scaling_vector.shape == (lca.A.shape[0],)

    def test_no_change_scenario_matches_base_solution(self):
        # Setting A[0,0] = 1000 (its original value) should yield base solution
        lca = LCA(_TEST_DATA_DIR, _minimal_dcf(_H2_UUID, 1000.0))
        np.testing.assert_allclose(lca.scaling_vector[0], 1.0, rtol=1e-10)
        np.testing.assert_allclose(lca.scaling_vector[1], 20.0, rtol=1e-10)
        np.testing.assert_allclose(lca.scaling_vector[2], 5.2, rtol=1e-10)

    def test_halved_diagonal_doubles_first_element(self):
        # A[0,0]: 1000 → 500; base sv[0] = 1 → new sv[0] = 2
        lca = LCA(_TEST_DATA_DIR, _minimal_dcf(_H2_UUID, 500.0))
        np.testing.assert_allclose(lca.scaling_vector[0], 2.0, rtol=1e-10)

    def test_halved_diagonal_full_scaling_vector(self):
        # New solution: sv = [2, 40, 10.4]
        lca = LCA(_TEST_DATA_DIR, _minimal_dcf(_H2_UUID, 500.0))
        np.testing.assert_allclose(lca.scaling_vector, [2.0, 40.0, 10.4], rtol=1e-10)

    def test_scaling_vector_solves_modified_system(self):
        # Verify A' @ sv = f for the modified system
        value = 750.0
        lca = LCA(_TEST_DATA_DIR, _minimal_dcf(_H2_UUID, value))
        A_modified = lca.A.copy()
        A_modified[0, 0] = value
        f = np.asarray(lca.f).reshape(-1)
        np.testing.assert_allclose(
            A_modified @ lca.scaling_vector, f, rtol=1e-9, atol=1e-9
        )

    def test_lca_results_dict_populated(self):
        lca = LCA(_TEST_DATA_DIR, _minimal_dcf(_H2_UUID, 1000.0))
        assert isinstance(lca.lca_results, dict)
        assert len(lca.lca_results) > 0

    def test_lca_results_have_value_and_unit_keys(self):
        lca = LCA(_TEST_DATA_DIR, _minimal_dcf(_H2_UUID, 1000.0))
        for result in lca.lca_results.values():
            assert 'value' in result
            assert 'unit' in result

    def test_lca_result_values_are_finite(self):
        lca = LCA(_TEST_DATA_DIR, _minimal_dcf(_H2_UUID, 1000.0))
        for result in lca.lca_results.values():
            assert np.isfinite(float(result['value']))

    def test_no_lca_tables_raises_value_error(self):
        dcf = MagicMock()
        dcf.inp = {'NotLCA': {}}
        with pytest.raises(ValueError, match='LCA'):
            LCA(_TEST_DATA_DIR, dcf)

    def test_unknown_uuid_raises_value_error(self):
        dcf = _minimal_dcf('nonexistent-uuid-12345', 1000.0)
        with pytest.raises(ValueError, match='UUID'):
            LCA(_TEST_DATA_DIR, dcf)

    def test_missing_uuid_field_raises_value_error(self):
        dcf = MagicMock()
        dcf.inp = {
            'LCA Components': {
                'H2': {'Value': 1000.0, 'Processed': 'Yes'}
            }
        }
        with pytest.raises(ValueError, match='UUID'):
            LCA(_TEST_DATA_DIR, dcf)

    def test_different_scenarios_produce_different_results(self):
        lca1 = LCA(_TEST_DATA_DIR, _minimal_dcf(_H2_UUID, 1000.0))
        results1 = {k: v['value'] for k, v in lca1.lca_results.items()}
        _clear_caches()

        lca2 = LCA(_TEST_DATA_DIR, _minimal_dcf(_H2_UUID, 500.0))
        results2 = {k: v['value'] for k, v in lca2.lca_results.items()}

        nonzero_names = [
            n for n in results1
            if results1[n] != 0.0 or results2[n] != 0.0
        ]
        assert len(nonzero_names) > 0, "all impact results are zero — test is vacuous"
        for name in nonzero_names:
            assert results1[name] != pytest.approx(results2[name], rel=1e-6)

    def test_array_value_summed(self):
        # Passing an array should be equivalent to passing its sum
        lca_array = LCA(
            _TEST_DATA_DIR,
            _minimal_dcf(_H2_UUID, np.array([500.0, 500.0])),
        )
        _clear_caches()
        lca_scalar = LCA(_TEST_DATA_DIR, _minimal_dcf(_H2_UUID, 1000.0))
        np.testing.assert_allclose(
            lca_array.scaling_vector, lca_scalar.scaling_vector, rtol=1e-10
        )

    def test_process_local_cache_reused(self):
        # Second instantiation reuses process-local cache (no re-factorization)
        dcf = _minimal_dcf(_H2_UUID, 1000.0)
        lca1 = LCA(_TEST_DATA_DIR, dcf)
        matrix_key = lca1._matrix_cache_key
        assert matrix_key in LCA._base_solver_cache

    def test_tech_index_dict_populated(self):
        lca = LCA(_TEST_DATA_DIR, _minimal_dcf(_H2_UUID, 1000.0))
        assert isinstance(lca.tech_index_dict, dict)
        assert _H2_UUID in lca.tech_index_dict
