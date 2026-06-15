"""Unit tests for pyH2A.Utilities.lca_utils."""
import os
from pathlib import Path

import numpy as np
import pytest
import scipy.sparse

from pyH2A.Utilities.lca_utils import (
    _csv_rows,
    _load_impact_index,
    _load_tech_index,
    atomic_savez,
    factorize,
    find_matrix_path,
    get_disk_cache_dir,
    matrix_of,
    tech_process_indices,
)


# ── _csv_rows ──────────────────────────────────────────────────────────────

class TestCsvRows:
    def test_skips_header_row(self, tmp_path):
        f = tmp_path / 'test.csv'
        f.write_text('header1,header2\nval1,val2\n', encoding='utf-8')
        assert _csv_rows(str(f)) == [['val1', 'val2']]

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

    def test_returns_list(self, tmp_path):
        f = tmp_path / 'test.csv'
        f.write_text('h\n1\n', encoding='utf-8')
        assert isinstance(_csv_rows(str(f)), list)

    def test_values_are_strings(self, tmp_path):
        f = tmp_path / 'test.csv'
        f.write_text('num\n42\n', encoding='utf-8')
        rows = _csv_rows(str(f))
        assert isinstance(rows[0][0], str)


# ── _load_tech_index ───────────────────────────────────────────────────────

_TECH_HEADER = 'index,provider ID\n'


class TestLoadTechIndex:
    def _write_csv(self, tmp_path, rows):
        csv = tmp_path / 'index_A.csv'
        csv.write_text(_TECH_HEADER + ''.join(rows), encoding='utf-8')

    def test_missing_file_returns_empty_dict(self, tmp_path):
        assert _load_tech_index(str(tmp_path)) == {}

    def test_keyed_by_uuid(self, tmp_path):
        self._write_csv(tmp_path, ['0,uuid-1\n'])
        assert 'uuid-1' in _load_tech_index(str(tmp_path))

    def test_values_are_integers(self, tmp_path):
        self._write_csv(tmp_path, ['5,uuid-x\n'])
        d = _load_tech_index(str(tmp_path))
        assert d['uuid-x'] == 5
        assert isinstance(d['uuid-x'], int)

    def test_multiple_entries(self, tmp_path):
        self._write_csv(tmp_path, ['0,uid-0\n', '2,uid-2\n'])
        d = _load_tech_index(str(tmp_path))
        assert set(d.keys()) == {'uid-0', 'uid-2'}
        assert d['uid-0'] == 0
        assert d['uid-2'] == 2

    def test_empty_csv_returns_empty_dict(self, tmp_path):
        self._write_csv(tmp_path, [])
        assert _load_tech_index(str(tmp_path)) == {}


# ── _load_impact_index ─────────────────────────────────────────────────────

_IMPACT_HEADER = 'index,indicator ID,indicator name,indicator unit\n'


class TestLoadImpactIndex:
    def _write_csv(self, tmp_path, rows):
        csv = tmp_path / 'index_C.csv'
        csv.write_text(_IMPACT_HEADER + ''.join(rows), encoding='utf-8')

    def test_missing_file_returns_empty_list(self, tmp_path):
        assert _load_impact_index(str(tmp_path)) == []

    def test_returns_list_of_dicts(self, tmp_path):
        self._write_csv(tmp_path, ['0,id-0,Global Warming,kg CO2 eq\n'])
        result = _load_impact_index(str(tmp_path))
        assert isinstance(result, list)
        assert isinstance(result[0], dict)

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
        result = find_matrix_path(str(tmp_path), 'M')
        assert result.endswith('.npz')


# ── matrix_of ──────────────────────────────────────────────────────────────

class TestMatrixOf:
    def test_load_npy_returns_ndarray(self, tmp_path):
        arr = np.array([[1.0, 2.0], [3.0, 4.0]])
        path = str(tmp_path / 'mat.npy')
        np.save(path, arr)
        loaded = matrix_of(path)
        assert isinstance(loaded, np.ndarray)
        np.testing.assert_array_equal(loaded, arr)

    def test_load_npz_returns_sparse(self, tmp_path):
        m = scipy.sparse.eye(3, format='csc')
        path = str(tmp_path / 'mat.npz')
        scipy.sparse.save_npz(path, m)
        loaded = matrix_of(path)
        assert scipy.sparse.issparse(loaded)
        np.testing.assert_array_equal(loaded.toarray(), m.toarray())

    def test_npy_preserves_shape(self, tmp_path):
        arr = np.arange(6).reshape(2, 3).astype(float)
        path = str(tmp_path / 'arr.npy')
        np.save(path, arr)
        assert matrix_of(path).shape == (2, 3)

    def test_npy_preserves_values(self, tmp_path):
        arr = np.array([1.5, 2.5, 3.5])
        path = str(tmp_path / 'vec.npy')
        np.save(path, arr)
        np.testing.assert_allclose(matrix_of(path), arr)


# ── atomic_savez ───────────────────────────────────────────────────────────

class TestAtomicSavez:
    def test_file_is_created(self, tmp_path):
        path = tmp_path / 'out.npz'
        atomic_savez(path, arr=np.array([1.0, 2.0]))
        assert path.exists()

    def test_saved_data_is_loadable(self, tmp_path):
        path = tmp_path / 'out.npz'
        arr = np.array([3.0, 4.0])
        atomic_savez(path, data=arr)
        np.testing.assert_array_equal(np.load(str(path))['data'], arr)

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
    def test_dense_returns_callable(self):
        assert callable(factorize(np.eye(3)))

    def test_sparse_returns_callable(self):
        assert callable(factorize(scipy.sparse.eye(3, format='csc')))

    def test_dense_diagonal_correct(self):
        A = np.diag([2.0, 3.0, 4.0])
        b = np.array([4.0, 9.0, 8.0])
        np.testing.assert_allclose(factorize(A)(b), [2.0, 3.0, 2.0], rtol=1e-12)

    def test_sparse_diagonal_correct(self):
        A = scipy.sparse.diags([2.0, 3.0, 4.0], format='csc')
        b = np.array([2.0, 6.0, 8.0])
        np.testing.assert_allclose(factorize(A)(b), [1.0, 2.0, 2.0], rtol=1e-12)

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


# ── tech_process_indices ───────────────────────────────────────────────────

class TestTechProcessIndices:
    def _make_folder(self, tmp_path, uuid_index_pairs):
        csv = tmp_path / 'index_A.csv'
        rows = ''.join(f'{idx},{uuid}\n' for uuid, idx in uuid_index_pairs.items())
        csv.write_text('index,provider ID\n' + rows, encoding='utf-8')

    def test_returns_ndarray(self, tmp_path):
        self._make_folder(tmp_path, {'uid-0': 0})
        A = np.array([[1.0], [0.0]])
        assert isinstance(tech_process_indices(str(tmp_path), A), np.ndarray)

    def test_only_nonzero_entries_included(self, tmp_path):
        self._make_folder(tmp_path, {'uid-0': 0, 'uid-1': 1})
        A = np.array([[1.0], [0.0]])
        result = tech_process_indices(str(tmp_path), A)
        uuids = result[:, 1].tolist()
        assert 'uid-0' in uuids
        assert 'uid-1' not in uuids

    def test_three_columns(self, tmp_path):
        self._make_folder(tmp_path, {'uid': 0})
        result = tech_process_indices(str(tmp_path), np.array([[5.0]]))
        assert result.shape[1] == 3

    def test_value_column_matches_matrix(self, tmp_path):
        self._make_folder(tmp_path, {'uid': 0})
        result = tech_process_indices(str(tmp_path), np.array([[7.5]]))
        assert result[0, 2] == pytest.approx(7.5)

    def test_sparse_matrix_input(self, tmp_path):
        self._make_folder(tmp_path, {'uid': 0})
        A = scipy.sparse.csc_matrix(np.array([[3.0]]))
        result = tech_process_indices(str(tmp_path), A)
        assert result.shape[0] == 1


# ── get_disk_cache_dir ─────────────────────────────────────────────────────

class TestGetDiskCacheDir:
    def test_returns_path(self, tmp_path):
        assert isinstance(get_disk_cache_dir(str(tmp_path)), Path)

    def test_creates_initial_artifacts_subdir(self, tmp_path):
        result = get_disk_cache_dir(str(tmp_path))
        assert result.name == 'Initial_Artifacts'
        assert result.exists()

    def test_dir_is_inside_matrix_folder(self, tmp_path):
        result = get_disk_cache_dir(str(tmp_path))
        assert result.parent == tmp_path

    def test_idempotent_on_repeated_calls(self, tmp_path):
        r1 = get_disk_cache_dir(str(tmp_path))
        r2 = get_disk_cache_dir(str(tmp_path))
        assert r1 == r2
