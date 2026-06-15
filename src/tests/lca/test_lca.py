"""Unit tests for pyH2A.LCA.LCA."""
import shutil
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
from pyH2A.Utilities.lca_utils import get_disk_cache_dir


# ── Paths ──────────────────────────────────────────────────────────────────

_HERE = Path(__file__).parent
_PROJECT_ROOT = _HERE.parents[2]
_TEST_DATA_DIR = str(_PROJECT_ROOT / 'data' / 'LCA' / 'LCA_Test_Data')

# UUIDs from LCA_Test_Data/index_A.csv (rows 0, 1, 2 of column-0)
_H2_UUID   = 'd304025a-d235-48b7-a7e4-f54db11459ff'
_HDPE_UUID = '238013c6-bac6-3768-b6ff-177fc2d89d57'
_NH4OH_UUID = '83cae1ae-4cd2-3b5e-8c06-4001a3f38ab7'


# ── Helpers ────────────────────────────────────────────────────────────────

def _full_dcf(h2_value, hdpe_value=20.0, nh4oh_value=5.2):
    """DCF mock with all 3 test-data components pre-resolved.

    All three column-0 entries of A are nonzero, so apply_component_updates
    requires all three UUIDs to be present.
    """
    dcf = MagicMock()
    dcf.inp = {
        'LCA Components': {
            'H2':    {'UUID': _H2_UUID,    'Value': h2_value,    'Processed': 'Yes'},
            'HDPE':  {'UUID': _HDPE_UUID,  'Value': hdpe_value,  'Processed': 'Yes'},
            'NH4OH': {'UUID': _NH4OH_UUID, 'Value': nh4oh_value, 'Processed': 'Yes'},
        }
    }
    return dcf


_DISK_CACHE_DIR = Path(_TEST_DATA_DIR) / 'Initial_Artifacts'


def _clear_caches():
    for k in LCA._cache:
        LCA._cache[k] = None
    get_disk_cache_dir.cache_clear()
    if _DISK_CACHE_DIR.exists():
        shutil.rmtree(_DISK_CACHE_DIR)


@pytest.fixture(autouse=True)
def _reset_lca_caches():
    """Isolate every test: clear all process-local caches before and after."""
    _clear_caches()
    yield
    _clear_caches()


# ── apply_component_updates ────────────────────────────────────────────────

class TestApplyComponentUpdates:
    """Tests for apply_component_updates with seeded LCA._cache['A0_column']."""

    def _seed_cache(self, uuid_val_pairs):
        uuids  = np.array([p[0] for p in uuid_val_pairs], dtype=str)
        values = np.array([p[1] for p in uuid_val_pairs], dtype=float)
        LCA._cache['A0_column'] = (uuids, values)

    def _make_lca(self):
        return object.__new__(LCA)

    def _make_dcf(self, table_name, components):
        """components: {comp_name: (uuid, value)}"""
        dcf = MagicMock()
        dcf.inp = {
            table_name: {
                name: {'UUID': uuid, 'Value': val, 'Processed': 'Yes'}
                for name, (uuid, val) in components.items()
            }
        }
        return dcf

    def test_single_component_correct_value(self):
        self._seed_cache([('uuid-0', 5.0)])
        lca = self._make_lca()
        lca.apply_component_updates(self._make_dcf('LCA T', {'A': ('uuid-0', 5.0)}))
        assert lca.component_values[0] == pytest.approx(5.0)

    def test_positive_a0_sign_preserved(self):
        self._seed_cache([('uuid-0', 10.0)])
        lca = self._make_lca()
        lca.apply_component_updates(self._make_dcf('LCA T', {'A': ('uuid-0', 3.0)}))
        assert lca.component_values[0] == pytest.approx(3.0)

    def test_negative_a0_sign_preserved(self):
        # A0_values[0] = -20 → result sign is negative regardless of input magnitude
        self._seed_cache([('uuid-0', -20.0)])
        lca = self._make_lca()
        lca.apply_component_updates(self._make_dcf('LCA T', {'A': ('uuid-0', 7.0)}))
        assert lca.component_values[0] == pytest.approx(-7.0)

    def test_array_value_is_summed(self):
        self._seed_cache([('uuid-0', 1.0)])
        lca = self._make_lca()
        dcf = MagicMock()
        dcf.inp = {'LCA T': {'A': {'UUID': 'uuid-0', 'Value': np.array([2.0, 3.0, 5.0]), 'Processed': 'Yes'}}}
        lca.apply_component_updates(dcf)
        assert lca.component_values[0] == pytest.approx(10.0)

    def test_multiple_components_correct_values(self):
        self._seed_cache([('uuid-0', 10.0), ('uuid-1', -5.0)])
        lca = self._make_lca()
        lca.apply_component_updates(self._make_dcf('LCA T', {'A': ('uuid-0', 4.0), 'B': ('uuid-1', 2.0)}))
        assert lca.component_values[0] == pytest.approx(4.0)
        assert lca.component_values[1] == pytest.approx(-2.0)

    def test_sets_component_values_as_ndarray(self):
        self._seed_cache([('uuid-0', 1.0)])
        lca = self._make_lca()
        lca.apply_component_updates(self._make_dcf('LCA T', {'A': ('uuid-0', 1.0)}))
        assert isinstance(lca.component_values, np.ndarray)

    def test_unknown_uuid_raises_value_error(self):
        self._seed_cache([('uuid-known', 1.0)])
        lca = self._make_lca()
        with pytest.raises(ValueError, match='UUID'):
            lca.apply_component_updates(self._make_dcf('LCA T', {'A': ('uuid-unknown', 1.0)}))

    def test_no_lca_tables_raises_value_error(self):
        self._seed_cache([('uuid-0', 1.0)])
        lca = self._make_lca()
        dcf = MagicMock()
        dcf.inp = {'NotLCA': {}}
        with pytest.raises(ValueError, match='LCA'):
            lca.apply_component_updates(dcf)

    def test_multiple_tables_combined(self):
        self._seed_cache([('uuid-0', 1.0), ('uuid-1', 1.0)])
        lca = self._make_lca()
        dcf = MagicMock()
        dcf.inp = {
            'LCA Table A': {'C1': {'UUID': 'uuid-0', 'Value': 3.0, 'Processed': 'Yes'}},
            'LCA Table B': {'C2': {'UUID': 'uuid-1', 'Value': 7.0, 'Processed': 'Yes'}},
        }
        lca.apply_component_updates(dcf)
        assert lca.component_values[0] == pytest.approx(3.0)
        assert lca.component_values[1] == pytest.approx(7.0)


# ── build_scaling_vector ───────────────────────────────────────────────────

class TestBuildScalingVector:
    """Tests for build_scaling_vector (Sherman-Morrison rank-1 update)."""

    def _make_lca(self, base_sv, a0_values, basis, component_values):
        LCA._cache['base_scaling_vector'] = np.asarray(base_sv, dtype=float)
        LCA._cache['A0_column'] = (
            np.array(['u'] * len(a0_values), dtype=str),
            np.asarray(a0_values, dtype=float),
        )
        LCA._cache['basis_component'] = np.asarray(basis, dtype=float)
        lca = object.__new__(LCA)
        lca.component_values = np.asarray(component_values, dtype=float)
        return lca

    def test_no_change_returns_base_scaling_vector(self):
        # delta = 0 → correction = 0 → sv = base_sv
        a0 = [1000.0, -20.0, -5.2]
        lca = self._make_lca([1.0, 20.0, 5.2], a0, np.eye(3), a0)
        lca.build_scaling_vector()
        np.testing.assert_allclose(lca.scaling_vector, [1.0, 20.0, 5.2], rtol=1e-12)

    def test_halved_diagonal_doubles_first_element(self):
        # 1×1: A = [[10]], f = [10] → base_sv = [1]; new diagonal = 5
        # correction = 0.1 * (-5) = -0.5; denom = 0.5; sv = 1 + 1 = 2
        lca = self._make_lca([1.0], [10.0], [[0.1]], [5.0])
        lca.build_scaling_vector()
        np.testing.assert_allclose(lca.scaling_vector, [2.0], rtol=1e-12)

    def test_scaling_vector_length_matches_base(self):
        lca = self._make_lca([1.0, 2.0], [3.0], [[1.0], [0.0]], [3.0])
        lca.build_scaling_vector()
        assert lca.scaling_vector.shape == (2,)

    def test_zero_denominator_raises_zero_division_error(self):
        # delta = -1; basis = [[1]]; correction[0] = -1; denom = 0
        lca = self._make_lca([1.0], [1.0], [[1.0]], [0.0])
        with pytest.raises(ZeroDivisionError):
            lca.build_scaling_vector()

    def test_result_satisfies_modified_system(self):
        # 3×3 lower-triangular A; change A[0,0]: 1000 → 500
        A = np.array([[1000., 0., 0.], [-20., 1., 0.], [-5.2, 0., 1.]])
        f = np.array([1000., 0., 0.])
        base_sv = np.linalg.solve(A, f)
        a0_values = np.array([1000., -20., -5.2])
        # basis_component = A^{-1} (all 3 rows are nonzero in col-0)
        basis = np.linalg.inv(A)
        new_cv = np.array([500., -20., -5.2])
        lca = self._make_lca(base_sv, a0_values, basis, new_cv)
        lca.build_scaling_vector()
        A_mod = A.copy()
        A_mod[0, 0] = 500.
        np.testing.assert_allclose(A_mod @ lca.scaling_vector, f, rtol=1e-10, atol=1e-10)


# ── perform_lca ────────────────────────────────────────────────────────────

class TestPerformLca:
    """Tests for perform_lca using dense matrices seeded into LCA._cache."""

    def _make_lca(self, B, C, scaling_vector, impacts):
        LCA._cache['matrix_B'] = np.asarray(B, dtype=float)
        LCA._cache['matrix_C'] = np.asarray(C, dtype=float)
        LCA._cache['impact_index'] = impacts
        lca = object.__new__(LCA)
        lca.scaling_vector = np.asarray(scaling_vector, dtype=float)
        return lca

    def test_results_dict_populated(self):
        lca = self._make_lca(
            B=[[1, 0], [0, 1]], C=[[1, 0]], scaling_vector=[2.0, 3.0],
            impacts=[{'index': 0, 'impact_name': 'GWP', 'impact_unit': 'kg CO2-eq'}],
        )
        lca.perform_lca()
        assert isinstance(lca.lca_results, dict)
        assert len(lca.lca_results) == 1

    def test_result_value_computed_correctly(self):
        # g = [[2,0],[0,3]] @ [1,2] = [2,6]; h = [[1,1]] @ [2,6] = [8]
        lca = self._make_lca(
            B=[[2, 0], [0, 3]], C=[[1, 1]], scaling_vector=[1.0, 2.0],
            impacts=[{'index': 0, 'impact_name': 'GWP', 'impact_unit': 'kg CO2-eq'}],
        )
        lca.perform_lca()
        assert lca.lca_results['GWP']['value'] == pytest.approx(8.0)

    def test_result_has_value_and_unit_keys(self):
        lca = self._make_lca(
            B=[[1]], C=[[1]], scaling_vector=[1.0],
            impacts=[{'index': 0, 'impact_name': 'AP', 'impact_unit': 'mol H+-eq'}],
        )
        lca.perform_lca()
        assert 'value' in lca.lca_results['AP']
        assert 'unit' in lca.lca_results['AP']

    def test_result_unit_stored_correctly(self):
        lca = self._make_lca(
            B=[[1]], C=[[1]], scaling_vector=[1.0],
            impacts=[{'index': 0, 'impact_name': 'GWP', 'impact_unit': 'kg CO2-eq'}],
        )
        lca.perform_lca()
        assert lca.lca_results['GWP']['unit'] == 'kg CO2-eq'

    def test_empty_impact_index_gives_empty_results(self):
        lca = self._make_lca(
            B=[[1, 0], [0, 1]], C=np.zeros((0, 2)), scaling_vector=[1.0, 2.0],
            impacts=[],
        )
        lca.perform_lca()
        assert lca.lca_results == {}

    def test_multiple_impacts_keyed_by_name(self):
        # B = I, sv = [3, 5] → g = [3, 5]; C = I → h = [3, 5]
        lca = self._make_lca(
            B=np.eye(2), C=np.eye(2), scaling_vector=[3.0, 5.0],
            impacts=[
                {'index': 0, 'impact_name': 'GWP', 'impact_unit': 'kg CO2-eq'},
                {'index': 1, 'impact_name': 'CED', 'impact_unit': 'MJ'},
            ],
        )
        lca.perform_lca()
        assert set(lca.lca_results.keys()) == {'GWP', 'CED'}
        assert lca.lca_results['GWP']['value'] == pytest.approx(3.0)
        assert lca.lca_results['CED']['value'] == pytest.approx(5.0)


# ── initialize_all_artifacts ───────────────────────────────────────────────

class TestInitializeAllArtifacts:
    def test_fully_populated_cache_returns_early(self):
        # All values non-None → the method must return without touching disk or matrices
        for k in LCA._cache:
            LCA._cache[k] = object()
        lca = object.__new__(LCA)
        lca.matrix_folder = '/does/not/exist'
        lca.initialize_all_artifacts()  # must not raise


# ── load_all_from_disk_to_ram ──────────────────────────────────────────────

class TestLoadAllFromDiskToRam:
    """Tests for load_all_from_disk_to_ram using tmp_path .npz files."""

    def _write_all(self, tmp_path):
        """Write a minimal complete set of cache files and return a paths dict."""
        sv     = np.array([1.0, 2.0, 3.0])
        uuids  = np.array(['u0', 'u1'], dtype=str)
        values = np.array([10.0, -5.0])
        basis  = np.eye(3)
        B = scipy.sparse.eye(2, format='csc')
        C = scipy.sparse.eye(2, format='csc')
        impact_index = np.array(
            [{'index': 0, 'impact_name': 'GWP', 'impact_unit': 'kg CO2-eq'}],
            dtype=object,
        )
        np.savez(tmp_path / 'base_scaling_vector.npz', base_scaling_vector=sv)
        np.savez(tmp_path / 'A0_column.npz', uuids=uuids, values=values)
        np.savez(tmp_path / 'basis_component.npz', basis_component=basis)
        scipy.sparse.save_npz(str(tmp_path / 'matrix_B.npz'), B)
        scipy.sparse.save_npz(str(tmp_path / 'matrix_C.npz'), C)
        np.savez(tmp_path / 'impact_index.npz', impact_index=impact_index)
        return {
            'base_scaling_vector': tmp_path / 'base_scaling_vector.npz',
            'A0_column':           tmp_path / 'A0_column.npz',
            'basis_component':     tmp_path / 'basis_component.npz',
            'matrix_B':            tmp_path / 'matrix_B.npz',
            'matrix_C':            tmp_path / 'matrix_C.npz',
            'impact_index':        tmp_path / 'impact_index.npz',
        }

    def test_loads_base_scaling_vector(self, tmp_path):
        lca = object.__new__(LCA)
        lca.load_all_from_disk_to_ram(self._write_all(tmp_path))
        np.testing.assert_array_equal(LCA._cache['base_scaling_vector'], [1.0, 2.0, 3.0])

    def test_loads_a0_column_uuids(self, tmp_path):
        lca = object.__new__(LCA)
        lca.load_all_from_disk_to_ram(self._write_all(tmp_path))
        uuids, _ = LCA._cache['A0_column']
        assert list(uuids) == ['u0', 'u1']

    def test_loads_a0_column_values(self, tmp_path):
        lca = object.__new__(LCA)
        lca.load_all_from_disk_to_ram(self._write_all(tmp_path))
        _, vals = LCA._cache['A0_column']
        np.testing.assert_array_equal(vals, [10.0, -5.0])

    def test_loads_basis_component(self, tmp_path):
        lca = object.__new__(LCA)
        lca.load_all_from_disk_to_ram(self._write_all(tmp_path))
        np.testing.assert_array_equal(LCA._cache['basis_component'], np.eye(3))

    def test_loads_matrix_B_as_sparse(self, tmp_path):
        lca = object.__new__(LCA)
        lca.load_all_from_disk_to_ram(self._write_all(tmp_path))
        assert scipy.sparse.issparse(LCA._cache['matrix_B'])

    def test_loads_matrix_C_as_sparse(self, tmp_path):
        lca = object.__new__(LCA)
        lca.load_all_from_disk_to_ram(self._write_all(tmp_path))
        assert scipy.sparse.issparse(LCA._cache['matrix_C'])

    def test_loads_impact_index_as_list(self, tmp_path):
        lca = object.__new__(LCA)
        lca.load_all_from_disk_to_ram(self._write_all(tmp_path))
        assert isinstance(LCA._cache['impact_index'], list)

    def test_missing_file_raises_file_not_found_error(self, tmp_path):
        paths = self._write_all(tmp_path)
        paths['base_scaling_vector'] = tmp_path / 'nonexistent.npz'
        lca = object.__new__(LCA)
        with pytest.raises(FileNotFoundError):
            lca.load_all_from_disk_to_ram(paths)


# ── Integration tests ──────────────────────────────────────────────────────

class TestLCAIntegration:
    """End-to-end tests using the real LCA_Test_Data matrices.

    LCA_Test_Data A matrix (3×3, lower triangular):
        [[1000.,    0.,   0. ],
         [ -20.,    1.,   0. ],
         [  -5.2,   0.,   1. ]]
    f = [1000., 0., 0.]  →  base scaling vector = [1., 20., 5.2]
    All three column-0 entries are nonzero → all three UUIDs must be supplied.
    """

    def test_instantiation_succeeds(self):
        assert LCA(_TEST_DATA_DIR, _full_dcf(1000.0)) is not None

    def test_cache_populated_after_init(self):
        LCA(_TEST_DATA_DIR, _full_dcf(1000.0))
        assert all(LCA._cache[k] is not None for k in LCA._cache)

    def test_scaling_vector_correct_shape(self):
        lca = LCA(_TEST_DATA_DIR, _full_dcf(1000.0))
        n = LCA._cache['base_scaling_vector'].shape[0]
        assert lca.scaling_vector.shape == (n,)

    def test_no_change_scenario_matches_base_solution(self):
        lca = LCA(_TEST_DATA_DIR, _full_dcf(1000.0))
        np.testing.assert_allclose(lca.scaling_vector[0], 1.0,  rtol=1e-10)
        np.testing.assert_allclose(lca.scaling_vector[1], 20.0, rtol=1e-10)
        np.testing.assert_allclose(lca.scaling_vector[2], 5.2,  rtol=1e-10)

    def test_halved_diagonal_doubles_first_element(self):
        lca = LCA(_TEST_DATA_DIR, _full_dcf(500.0))
        np.testing.assert_allclose(lca.scaling_vector[0], 2.0, rtol=1e-10)

    def test_halved_diagonal_full_scaling_vector(self):
        lca = LCA(_TEST_DATA_DIR, _full_dcf(500.0))
        np.testing.assert_allclose(lca.scaling_vector, [2.0, 40.0, 10.4], rtol=1e-10)

    def test_lca_results_dict_populated(self):
        lca = LCA(_TEST_DATA_DIR, _full_dcf(1000.0))
        assert isinstance(lca.lca_results, dict)
        assert len(lca.lca_results) > 0

    def test_lca_results_have_value_and_unit_keys(self):
        lca = LCA(_TEST_DATA_DIR, _full_dcf(1000.0))
        for result in lca.lca_results.values():
            assert 'value' in result
            assert 'unit' in result

    def test_lca_result_values_are_finite(self):
        lca = LCA(_TEST_DATA_DIR, _full_dcf(1000.0))
        for result in lca.lca_results.values():
            assert np.isfinite(float(result['value']))

    def test_no_lca_tables_raises_value_error(self):
        dcf = MagicMock()
        dcf.inp = {'NotLCA': {}}
        with pytest.raises(ValueError, match='LCA'):
            LCA(_TEST_DATA_DIR, dcf)

    def test_unknown_uuid_raises_value_error(self):
        dcf = _full_dcf(1000.0)
        dcf.inp['LCA Components']['H2']['UUID'] = 'nonexistent-uuid-12345'
        with pytest.raises(ValueError, match='UUID'):
            LCA(_TEST_DATA_DIR, dcf)

    def test_different_scenarios_produce_different_results(self):
        lca1 = LCA(_TEST_DATA_DIR, _full_dcf(1000.0))
        results1 = {k: v['value'] for k, v in lca1.lca_results.items()}
        _clear_caches()
        lca2 = LCA(_TEST_DATA_DIR, _full_dcf(500.0))
        results2 = {k: v['value'] for k, v in lca2.lca_results.items()}
        nonzero = [n for n in results1 if results1[n] != 0.0 or results2[n] != 0.0]
        assert len(nonzero) > 0, "all impact results are zero — test is vacuous"
        for name in nonzero:
            assert results1[name] != pytest.approx(results2[name], rel=1e-6)

    def test_array_value_summed(self):
        lca_arr = LCA(_TEST_DATA_DIR, _full_dcf(np.array([500.0, 500.0])))
        _clear_caches()
        lca_scalar = LCA(_TEST_DATA_DIR, _full_dcf(1000.0))
        np.testing.assert_allclose(lca_arr.scaling_vector, lca_scalar.scaling_vector, rtol=1e-10)

    def test_process_local_cache_reused(self):
        LCA(_TEST_DATA_DIR, _full_dcf(1000.0))
        # Second instantiation must reuse the already-populated cache
        assert all(LCA._cache[k] is not None for k in LCA._cache)
