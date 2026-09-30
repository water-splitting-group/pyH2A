"""Unit tests for pyH2A.Utilities.lca_utilities."""
import numpy as np
import pytest
import scipy.sparse

from pyH2A.Utilities import lca_utilities
from pyH2A.Utilities.lca_utilities import (
    _csv_rows,
    _load_impact_index,
    _load_tech_index,
    atomic_savez,
    dense_column,
    export_fingerprint,
    factorize,
    find_matrix_path,
    get_cache_paths,
    load_matrices_from_folder,
    tech_process_indices,
)


# ── _csv_rows ──────────────────────────────────────────────────────────────

class TestCsvRows:
    def test_multiple_rows_returned(self, tmp_path):
        f = tmp_path / 'test.csv'
        f.write_text('a,b\n1,2\n3,4\n5,6\n', encoding='utf-8')
        rows = _csv_rows(str(f))
        assert len(rows) == 3
        assert rows[0] == ['1', '2']
        assert rows[2] == ['5', '6']

    def test_header_only_returns_empty(self, tmp_path):
        f = tmp_path / 'test.csv'
        f.write_text('col1,col2\n', encoding='utf-8')
        assert _csv_rows(str(f)) == []

    def test_values_are_strings(self, tmp_path):
        f = tmp_path / 'test.csv'
        f.write_text('num\n42\n', encoding='utf-8')
        rows = _csv_rows(str(f))
        assert isinstance(rows[0][0], str)


# ── _load_tech_index ───────────────────────────────────────────────────────

# Mirrors the real openLCA export header; flow unit is column index 8.
_TECH_HEADER = 'index,provider ID,provider name,provider category,provider location,flow ID,flow name,flow category,flow unit,flow type\n'


class TestLoadTechIndex:
    def _write_csv(self, tmp_path, rows):
        csv = tmp_path / 'index_A.csv'
        csv.write_text(_TECH_HEADER + ''.join(rows), encoding='utf-8')

    def test_missing_file_returns_empty_dict(self, tmp_path):
        assert _load_tech_index(str(tmp_path)) == {}

    def test_values_are_integers(self, tmp_path):
        self._write_csv(tmp_path, ['5,uuid-x,,,,,,,kg,product\n'])
        d = _load_tech_index(str(tmp_path))
        idx, flow_unit = d['uuid-x']
        assert idx == 5
        assert isinstance(idx, int)
        assert flow_unit == 'kg'

    def test_multiple_entries(self, tmp_path):
        self._write_csv(tmp_path, ['0,uid-0,,,,,,,kg,product\n', '2,uid-2,,,,,,,MJ,product\n'])
        d = _load_tech_index(str(tmp_path))
        assert set(d.keys()) == {'uid-0', 'uid-2'}
        assert d['uid-0'] == (0, 'kg')
        assert d['uid-2'] == (2, 'MJ')

    def test_empty_csv_returns_empty_dict(self, tmp_path):
        self._write_csv(tmp_path, [])
        assert _load_tech_index(str(tmp_path)) == {}

    def test_duplicate_provider_id_raises(self, tmp_path):
        """A provider on two rows is a multi-output process: keying by provider
        would silently drop one of its technosphere columns."""
        self._write_csv(tmp_path, ['0,uid,,,,,,,kg,product\n', '1,uid,,,,,,,kg,product\n'])
        with pytest.raises(ValueError, match='duplicate provider IDs'):
            _load_tech_index(str(tmp_path))


# ── _load_impact_index ─────────────────────────────────────────────────────

_IMPACT_HEADER = 'index,indicator ID,indicator name,indicator unit\n'


class TestLoadImpactIndex:
    def _write_csv(self, tmp_path, rows):
        csv = tmp_path / 'index_C.csv'
        csv.write_text(_IMPACT_HEADER + ''.join(rows), encoding='utf-8')

    def test_missing_file_returns_empty_list(self, tmp_path):
        assert _load_impact_index(str(tmp_path)) == []

    def test_dict_keys(self, tmp_path):
        self._write_csv(tmp_path, ['0,id-0,Global Warming,kg CO2 eq\n'])
        entry = _load_impact_index(str(tmp_path))[0]
        assert set(entry.keys()) == {'index', 'impact_name', 'impact_unit'}

    def test_index_parsed_as_int(self, tmp_path):
        self._write_csv(tmp_path, ['3,id-3,Ozone Depletion,kg CFC-11 eq\n'])
        entry = _load_impact_index(str(tmp_path))[0]
        assert entry['index'] == 3
        assert isinstance(entry['index'], int)

    def test_impact_name_and_unit(self, tmp_path):
        self._write_csv(tmp_path, ['0,id,Global Warming,kg CO2 eq\n'])
        entry = _load_impact_index(str(tmp_path))[0]
        assert entry['impact_name'] == 'Global Warming'
        assert entry['impact_unit'] == 'kg CO2 eq'

    def test_multiple_entries_order_preserved(self, tmp_path):
        self._write_csv(tmp_path, [
            '0,id-0,Global Warming,kg CO2 eq\n',
            '1,id-1,Ozone Depletion,kg CFC-11 eq\n',
        ])
        lst = _load_impact_index(str(tmp_path))
        assert len(lst) == 2
        assert lst[0]['impact_name'] == 'Global Warming'
        assert lst[1]['impact_name'] == 'Ozone Depletion'

    def test_header_only_returns_empty_list(self, tmp_path):
        self._write_csv(tmp_path, [])
        assert _load_impact_index(str(tmp_path)) == []


# ── find_matrix_path ───────────────────────────────────────────────────────

class TestFindMatrixPath:
    def test_finds_npz(self, tmp_path):
        (tmp_path / 'A.npz').write_bytes(b'')
        assert find_matrix_path(str(tmp_path), 'A') == str(tmp_path / 'A.npz')

    def test_finds_npy(self, tmp_path):
        (tmp_path / 'B.npy').write_bytes(b'')
        assert find_matrix_path(str(tmp_path), 'B') == str(tmp_path / 'B.npy')

    def test_returns_none_when_absent(self, tmp_path):
        assert find_matrix_path(str(tmp_path), 'X') is None

    def test_npz_takes_priority_over_npy(self, tmp_path):
        (tmp_path / 'M.npz').write_bytes(b'')
        (tmp_path / 'M.npy').write_bytes(b'')
        assert find_matrix_path(str(tmp_path), 'M').endswith('.npz')


# ── atomic_savez ───────────────────────────────────────────────────────────

class TestAtomicSavez:
    def test_no_temp_file_left_behind(self, tmp_path):
        atomic_savez(tmp_path / 'out.npz', x=np.ones(3))
        assert list(tmp_path.glob('*.tmp.npz')) == []

    def test_overwrites_existing(self, tmp_path):
        path = tmp_path / 'out.npz'
        atomic_savez(path, v=np.array([1.0]))
        atomic_savez(path, v=np.array([9.0]))
        np.testing.assert_array_equal(np.load(str(path))['v'], [9.0])


# ── factorize ──────────────────────────────────────────────────────────────

class TestFactorize:
    def test_dense_satisfies_ax_equals_b(self):
        rng = np.random.default_rng(42)
        n = 5
        A = rng.random((n, n)) + n * np.eye(n)
        b = rng.random(n)
        np.testing.assert_allclose(A @ factorize(A)(b), b, rtol=1e-10)

    def test_sparse_satisfies_ax_equals_b(self):
        rng = np.random.default_rng(7)
        n = 5
        A_dense = rng.random((n, n)) + n * np.eye(n)
        A_sparse = scipy.sparse.csc_matrix(A_dense)
        b = rng.random(n)
        np.testing.assert_allclose(A_dense @ factorize(A_sparse)(b), b, rtol=1e-10)

    def test_dense_multi_rhs(self):
        A = np.diag([2.0, 3.0])
        B = np.array([[2.0, 4.0], [3.0, 6.0]])
        np.testing.assert_allclose(factorize(A)(B), [[1.0, 2.0], [1.0, 2.0]], rtol=1e-12)

    def test_sparse_csr_converted_internally(self):
        A = scipy.sparse.eye(3, format='csr')
        np.testing.assert_allclose(factorize(A)(np.ones(3)), np.ones(3), rtol=1e-12)

    def test_sparse_full_lower_triangular(self):
        A_dense = np.array([[1000., 0., 0.], [-20., 1., 0.], [-5.2, 0., 1.]])
        A_sparse = scipy.sparse.csc_matrix(A_dense)
        f = np.array([1000., 0., 0.])
        np.testing.assert_allclose(factorize(A_sparse)(f), [1.0, 20.0, 5.2], rtol=1e-10)

    @pytest.mark.parametrize('disabled', [(), ('pypardiso',), ('pypardiso', 'scikit_umfpack')])
    def test_every_available_sparse_backend_agrees(self, monkeypatch, disabled):
        """Whichever optional solver is installed, all backends solve identically.

        Each parametrisation disables one more of them, so the scipy splu
        fallback is exercised even when the [performance] extra is installed."""
        for name in disabled:
            monkeypatch.setattr(lca_utilities, name, None)
        A_dense = np.array([[1000., 0., 0.], [-20., 1., 0.], [-5.2, 0., 1.]])
        f = np.array([1000., 0., 0.])
        solver = factorize(scipy.sparse.csc_matrix(A_dense))
        np.testing.assert_allclose(solver(f), [1.0, 20.0, 5.2], rtol=1e-10)


# ── tech_process_indices ───────────────────────────────────────────────────

class TestTechProcessIndices:
    def _make_folder(self, tmp_path, uuid_index_pairs, flow_unit='kg'):
        csv = tmp_path / 'index_A.csv'
        rows = ''.join(f'{idx},{uuid},,,,,,,{flow_unit},product\n' for uuid, idx in uuid_index_pairs.items())
        csv.write_text(_TECH_HEADER + rows, encoding='utf-8')

    def test_only_nonzero_entries_included(self, tmp_path):
        self._make_folder(tmp_path, {'uid-0': 0, 'uid-1': 1})
        A = np.array([[1.0], [0.0]])
        result = tech_process_indices(str(tmp_path), A)
        uuids = result[:, 1].tolist()
        assert 'uid-0' in uuids
        assert 'uid-1' not in uuids

    def test_output_shape_and_sparse_input(self, tmp_path):
        self._make_folder(tmp_path, {'uid': 0})
        A = scipy.sparse.csc_matrix(np.array([[3.0]]))
        result = tech_process_indices(str(tmp_path), A)
        assert result.shape == (1, 4)

    def test_value_column_matches_matrix(self, tmp_path):
        self._make_folder(tmp_path, {'uid': 0})
        result = tech_process_indices(str(tmp_path), np.array([[7.5]]))
        assert result[0, 2] == pytest.approx(7.5)

    def test_flow_unit_column_matches_csv(self, tmp_path):
        self._make_folder(tmp_path, {'uid': 0}, flow_unit='MJ')
        result = tech_process_indices(str(tmp_path), np.array([[7.5]]))
        assert result[0, 3] == 'MJ'

    def test_rows_are_ordered_by_index(self, tmp_path):
        """Row order follows the matrix, not index_A.csv, so that the reference
        flow is always first and component values align with A[:, 0]."""
        self._make_folder(tmp_path, {'uid-2': 2, 'uid-0': 0, 'uid-1': 1})
        result = tech_process_indices(str(tmp_path), np.array([[4.0], [-1.0], [-2.0]]))
        assert result[:, 0].tolist() == [0, 1, 2]
        assert result[:, 1].tolist() == ['uid-0', 'uid-1', 'uid-2']

    # The demand vector, the rank-1 update and the product flow unit all address the
    # reference flow by position, so "row 0 is the product" is load-bearing rather than
    # a convention: an export that breaks it has to be refused here, where it is visible.

    def test_column_without_row_zero_is_rejected(self, tmp_path):
        """A first column that does not produce flow 0 would be solved for a
        different product, with A0_column[0] silently becoming another process."""
        self._make_folder(tmp_path, {'uid-0': 0, 'uid-1': 1})
        with pytest.raises(ValueError, match='does not produce'):
            tech_process_indices(str(tmp_path), np.array([[0.0], [-1.0]]))

    def test_negative_reference_flow_is_rejected(self, tmp_path):
        """Row 0 has to be an output; a negative entry there is an input, so the
        column produces nothing the demand vector can ask for."""
        self._make_folder(tmp_path, {'uid-0': 0, 'uid-1': 1})
        with pytest.raises(ValueError, match='does not produce'):
            tech_process_indices(str(tmp_path), np.array([[-1.0], [2.0]]))

    def test_empty_column_is_rejected(self, tmp_path):
        self._make_folder(tmp_path, {'uid-0': 0})
        with pytest.raises(ValueError, match='does not produce'):
            tech_process_indices(str(tmp_path), np.array([[0.0]]))


# ── dense_column ───────────────────────────────────────────────────────────

class TestDenseColumn:
    _MATRIX = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])

    def test_dense_input(self):
        np.testing.assert_array_equal(dense_column(self._MATRIX, 1), [2.0, 4.0, 6.0])

    def test_sparse_input_matches_dense(self):
        sparse = scipy.sparse.csc_matrix(self._MATRIX)
        np.testing.assert_array_equal(dense_column(sparse, 0), dense_column(self._MATRIX, 0))

    def test_result_is_one_dimensional(self):
        assert dense_column(scipy.sparse.csc_matrix(self._MATRIX), 0).ndim == 1


# ── load_matrices_from_folder ──────────────────────────────────────────────

class TestLoadMatricesFromFolder:
    def _write_export(self, tmp_path, matrices=('A', 'B', 'C')):
        (tmp_path / 'index_A.csv').write_text(_TECH_HEADER + '0,uid,,,,,,,kg,product\n',
                                              encoding='utf-8')
        (tmp_path / 'index_C.csv').write_text(_IMPACT_HEADER + '0,id,Global Warming,kg CO2 eq\n',
                                              encoding='utf-8')
        for name in matrices:
            np.save(str(tmp_path / f'{name}.npy'), np.array([[1.0]]))

    def test_demand_vector_is_not_required(self, tmp_path):
        """The demand is always one unit of the reference flow, built by the
        caller, so an export without f.npy still loads."""
        self._write_export(tmp_path)
        impact_index, techno_index, A, B, C = load_matrices_from_folder(str(tmp_path))
        assert impact_index[0]['impact_name'] == 'Global Warming'
        assert techno_index[0, 1] == 'uid'
        assert A.shape == (1, 1)

    def test_missing_matrix_is_named(self, tmp_path):
        self._write_export(tmp_path, matrices=('A', 'B'))
        with pytest.raises(ValueError, match='C could not be loaded'):
            load_matrices_from_folder(str(tmp_path))


# ── export_fingerprint ─────────────────────────────────────────────────────

class TestExportFingerprint:
    def _write_export(self, tmp_path):
        (tmp_path / 'index_A.csv').write_text(_TECH_HEADER, encoding='utf-8')
        (tmp_path / 'index_C.csv').write_text(_IMPACT_HEADER, encoding='utf-8')
        for name in ('A', 'B', 'C'):
            np.save(str(tmp_path / f'{name}.npy'), np.array([[1.0]]))

    def test_stable_for_an_unchanged_export(self, tmp_path):
        self._write_export(tmp_path)
        assert export_fingerprint(str(tmp_path)) == export_fingerprint(str(tmp_path))

    def test_changes_when_a_source_file_changes(self, tmp_path):
        self._write_export(tmp_path)
        before = export_fingerprint(str(tmp_path))
        np.save(str(tmp_path / 'A.npy'), np.array([[1.0, 2.0], [3.0, 4.0]]))
        assert export_fingerprint(str(tmp_path)) != before

    def test_ignores_files_that_are_not_sources(self, tmp_path):
        """f.npy is bundled with an openLCA export but never read, so re-exporting
        it alone must not invalidate the cached artifacts."""
        self._write_export(tmp_path)
        before = export_fingerprint(str(tmp_path))
        np.save(str(tmp_path / 'f.npy'), np.array([1.0]))
        assert export_fingerprint(str(tmp_path)) == before

    def test_missing_source_files_are_skipped(self, tmp_path):
        """A missing matrix still surfaces as the explicit error from
        load_matrices_from_folder, not as a failure to fingerprint."""
        assert export_fingerprint(str(tmp_path)) == '[]'


# ── get_cache_paths ────────────────────────────────────────────────────────

class TestGetCachePaths:
    def test_creates_initial_artifacts_subdir(self, tmp_path):
        result = get_cache_paths(str(tmp_path))
        assert (tmp_path / 'Initial_Artifacts').exists()

    def test_returns_paths_inside_initial_artifacts(self, tmp_path):
        paths = get_cache_paths(str(tmp_path))
        assert all(p.parent == tmp_path / 'Initial_Artifacts' for p in paths.values())

    def test_idempotent_on_repeated_calls(self, tmp_path):
        r1 = get_cache_paths(str(tmp_path))
        r2 = get_cache_paths(str(tmp_path))
        assert r1 == r2

    def test_covers_every_cached_artifact(self, tmp_path):
        """LCA_Plugin only reuses a cache directory in which every path here exists,
        so a cache key without a path could never be written and would force a
        rebuild on every run."""
        from pyH2A.Plugins.LCA_Plugin import LCA_Plugin

        assert set(LCA_Plugin._cache) | {'fingerprint'} == set(get_cache_paths(str(tmp_path)))
