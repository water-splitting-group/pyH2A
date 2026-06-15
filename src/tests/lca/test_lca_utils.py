"""Unit tests for pyH2A.LCA.LCA_lib."""
import os

import numpy as np
import pytest
import scipy.sparse

from pyH2A.Utilities.lca_utils import (
    _FactorizedSolver,
    _csv_rows_of,
    ExportFolder,
    ImpactEntry,
    Matrix,
    TechEntry,
    factorize,
    matrix_of,
)


# ── TechEntry defaults ─────────────────────────────────────────────────────

class TestTechEntryInit:
    def test_default_index(self):
        e = TechEntry()
        assert e.index == -1

    def test_all_string_fields_empty(self):
        e = TechEntry()
        for attr in (
            'process_id', 'process_name', 'process_category',
            'process_location', 'flow_id', 'flow_name',
            'flow_category', 'flow_unit', 'flow_type',
        ):
            assert getattr(e, attr) == ''


# ── TechEntry._from_csv ────────────────────────────────────────────────────

class TestTechEntryFromCsv:
    ROW = [
        '5', 'uuid-abc', 'My Process', 'Cat A', 'US',
        'flow-uuid', 'Flow Name', 'Flow Cat', 'kg', 'product',
    ]

    def test_index_parsed_as_int(self):
        assert TechEntry._from_csv(self.ROW).index == 5

    def test_zero_index(self):
        row = ['0'] + self.ROW[1:]
        assert TechEntry._from_csv(row).index == 0

    def test_process_id(self):
        assert TechEntry._from_csv(self.ROW).process_id == 'uuid-abc'

    def test_process_name(self):
        assert TechEntry._from_csv(self.ROW).process_name == 'My Process'

    def test_process_category(self):
        assert TechEntry._from_csv(self.ROW).process_category == 'Cat A'

    def test_process_location(self):
        assert TechEntry._from_csv(self.ROW).process_location == 'US'

    def test_flow_id(self):
        assert TechEntry._from_csv(self.ROW).flow_id == 'flow-uuid'

    def test_flow_name(self):
        assert TechEntry._from_csv(self.ROW).flow_name == 'Flow Name'

    def test_flow_category(self):
        assert TechEntry._from_csv(self.ROW).flow_category == 'Flow Cat'

    def test_flow_unit(self):
        assert TechEntry._from_csv(self.ROW).flow_unit == 'kg'

    def test_flow_type(self):
        assert TechEntry._from_csv(self.ROW).flow_type == 'product'


# ── TechEntry.dict_of ──────────────────────────────────────────────────────

TECH_CSV_HEADER = (
    'index,provider ID,provider name,provider category,provider location,'
    'flow ID,flow name,flow category,flow unit,flow type\n'
)


class TestTechEntryDictOf:
    def test_keyed_by_process_id(self, tmp_path):
        csv_file = tmp_path / 'index_A.csv'
        csv_file.write_text(
            TECH_CSV_HEADER
            + '0,uuid-1,Process A,Cat X,DE,fid-1,Flow A,FlowCat,kg,product\n'
            + '1,uuid-2,Process B,Cat Y,US,fid-2,Flow B,FlowCat2,L,waste\n',
            encoding='utf-8',
        )
        d = TechEntry.dict_of(str(csv_file))
        assert set(d.keys()) == {'uuid-1', 'uuid-2'}

    def test_correct_index_stored(self, tmp_path):
        csv_file = tmp_path / 'index_A.csv'
        csv_file.write_text(
            TECH_CSV_HEADER
            + '0,uid-0,P0,C,DE,f0,F0,FC,kg,product\n'
            + '2,uid-2,P2,C,AU,f2,F2,FC,L,waste\n',
            encoding='utf-8',
        )
        d = TechEntry.dict_of(str(csv_file))
        assert d['uid-0'].index == 0
        assert d['uid-2'].index == 2

    def test_process_name_preserved(self, tmp_path):
        csv_file = tmp_path / 'index_A.csv'
        csv_file.write_text(
            TECH_CSV_HEADER
            + '0,uid,My Special Process,,,,,,,product\n',
            encoding='utf-8',
        )
        d = TechEntry.dict_of(str(csv_file))
        assert d['uid'].process_name == 'My Special Process'

    def test_empty_file_returns_empty_dict(self, tmp_path):
        csv_file = tmp_path / 'index_A.csv'
        csv_file.write_text(TECH_CSV_HEADER, encoding='utf-8')
        assert TechEntry.dict_of(str(csv_file)) == {}


# ── ImpactEntry defaults ───────────────────────────────────────────────────

class TestImpactEntryInit:
    def test_default_index(self):
        e = ImpactEntry()
        assert e.index == -1

    def test_all_string_fields_empty(self):
        e = ImpactEntry()
        for attr in ('impact_id', 'impact_name', 'impact_unit'):
            assert getattr(e, attr) == ''


# ── ImpactEntry._from_csv ──────────────────────────────────────────────────

class TestImpactEntryFromCsv:
    ROW = ['3', 'impact-uuid', 'Global Warming', 'kg CO2 eq']

    def test_index_parsed_as_int(self):
        assert ImpactEntry._from_csv(self.ROW).index == 3

    def test_zero_index(self):
        assert ImpactEntry._from_csv(['0', 'id', 'name', 'unit']).index == 0

    def test_impact_id(self):
        assert ImpactEntry._from_csv(self.ROW).impact_id == 'impact-uuid'

    def test_impact_name(self):
        assert ImpactEntry._from_csv(self.ROW).impact_name == 'Global Warming'

    def test_impact_unit(self):
        assert ImpactEntry._from_csv(self.ROW).impact_unit == 'kg CO2 eq'


# ── ImpactEntry.index_of ───────────────────────────────────────────────────

IMPACT_CSV_HEADER = 'index,indicator ID,indicator name,indicator unit\n'


class TestImpactEntryIndexOf:
    def test_returns_list_in_file_order(self, tmp_path):
        csv_file = tmp_path / 'index_C.csv'
        csv_file.write_text(
            IMPACT_CSV_HEADER
            + '0,id-0,Global Warming,kg CO2 eq\n'
            + '1,id-1,Ozone Depletion,kg CFC-11 eq\n',
            encoding='utf-8',
        )
        lst = ImpactEntry.index_of(str(csv_file))
        assert len(lst) == 2
        assert lst[0].index == 0
        assert lst[0].impact_name == 'Global Warming'
        assert lst[1].index == 1
        assert lst[1].impact_unit == 'kg CFC-11 eq'

    def test_single_entry(self, tmp_path):
        csv_file = tmp_path / 'index_C.csv'
        csv_file.write_text(
            IMPACT_CSV_HEADER + '0,id,Name,unit\n',
            encoding='utf-8',
        )
        lst = ImpactEntry.index_of(str(csv_file))
        assert len(lst) == 1
        assert isinstance(lst[0], ImpactEntry)

    def test_header_only_returns_empty_list(self, tmp_path):
        csv_file = tmp_path / 'index_C.csv'
        csv_file.write_text(IMPACT_CSV_HEADER, encoding='utf-8')
        assert ImpactEntry.index_of(str(csv_file)) == []


# ── _csv_rows_of ───────────────────────────────────────────────────────────

class TestCsvRowsOf:
    def test_skips_header_row(self, tmp_path):
        f = tmp_path / 'test.csv'
        f.write_text('header1,header2\nval1,val2\n', encoding='utf-8')
        rows = _csv_rows_of(str(f))
        assert rows == [['val1', 'val2']]

    def test_multiple_rows_returned(self, tmp_path):
        f = tmp_path / 'test.csv'
        f.write_text('a,b\n1,2\n3,4\n5,6\n', encoding='utf-8')
        rows = _csv_rows_of(str(f))
        assert len(rows) == 3
        assert rows[0] == ['1', '2']
        assert rows[2] == ['5', '6']

    def test_header_only_returns_empty(self, tmp_path):
        f = tmp_path / 'test.csv'
        f.write_text('col1,col2\n', encoding='utf-8')
        assert _csv_rows_of(str(f)) == []

    def test_returns_list(self, tmp_path):
        f = tmp_path / 'test.csv'
        f.write_text('h\n1\n', encoding='utf-8')
        result = _csv_rows_of(str(f))
        assert isinstance(result, list)

    def test_values_are_strings(self, tmp_path):
        f = tmp_path / 'test.csv'
        f.write_text('num\n42\n', encoding='utf-8')
        rows = _csv_rows_of(str(f))
        assert isinstance(rows[0][0], str)


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


# ── ExportFolder ───────────────────────────────────────────────────────────

_REAL_DATA = os.path.normpath(os.path.join(
    os.path.dirname(__file__), '..', '..', '..', 'data', 'LCA', 'LCA_Test_Data'
))


class TestExportFolder:
    def test_folder_attribute_stored(self):
        ef = ExportFolder('/some/path')
        assert ef.folder == '/some/path'

    def test_has_impacts_true_for_real_data(self):
        ef = ExportFolder(_REAL_DATA)
        assert ef.has_impacts() is True

    def test_has_impacts_false_when_missing(self, tmp_path):
        ef = ExportFolder(str(tmp_path))
        assert ef.has_impacts() is False

    def test_tech_index_returns_nonempty_dict(self):
        ef = ExportFolder(_REAL_DATA)
        d = ef.tech_index()
        assert isinstance(d, dict)
        assert len(d) > 0

    def test_tech_index_values_are_tech_entries(self):
        ef = ExportFolder(_REAL_DATA)
        d = ef.tech_index()
        for entry in d.values():
            assert isinstance(entry, TechEntry)

    def test_tech_index_missing_returns_empty(self, tmp_path):
        ef = ExportFolder(str(tmp_path))
        assert ef.tech_index() == {}

    def test_impact_index_returns_nonempty_list(self):
        ef = ExportFolder(_REAL_DATA)
        lst = ef.impact_index()
        assert isinstance(lst, list)
        assert len(lst) > 0

    def test_impact_index_entries_are_impact_entries(self):
        ef = ExportFolder(_REAL_DATA)
        for entry in ef.impact_index():
            assert isinstance(entry, ImpactEntry)

    def test_impact_index_missing_returns_empty(self, tmp_path):
        ef = ExportFolder(str(tmp_path))
        assert ef.impact_index() == []

    def test_load_npy_returns_ndarray(self):
        ef = ExportFolder(_REAL_DATA)
        A = ef.load('A')
        assert isinstance(A, np.ndarray)
        assert A.ndim == 2

    def test_load_npz_returns_sparse(self):
        ef = ExportFolder(_REAL_DATA)
        C = ef.load('C')
        assert scipy.sparse.issparse(C)

    def test_load_missing_returns_none(self, tmp_path):
        ef = ExportFolder(str(tmp_path))
        assert ef.load('nonexistent') is None

    def test_load_npy_extension_fallback(self, tmp_path):
        arr = np.array([1.0, 2.0, 3.0])
        np.save(str(tmp_path / 'f.npy'), arr)
        loaded = ExportFolder(str(tmp_path)).load('f')
        np.testing.assert_array_equal(loaded, arr)

    def test_load_npz_extension_fallback(self, tmp_path):
        m = scipy.sparse.eye(2, format='csc')
        scipy.sparse.save_npz(str(tmp_path / 'C.npz'), m)
        loaded = ExportFolder(str(tmp_path)).load('C')
        assert scipy.sparse.issparse(loaded)

    def test_load_exact_path_first(self, tmp_path):
        # File without extension takes priority over .npy variant
        arr = np.array([9.0, 8.0])
        np.save(str(tmp_path / 'f'), arr)  # saves as 'f.npy' by numpy
        # Create a file literally named 'f' (non-numpy, to verify priority)
        exact_arr = np.array([1.0, 2.0])
        np.save(str(tmp_path / 'g.npy'), exact_arr)
        loaded = ExportFolder(str(tmp_path)).load('g')
        np.testing.assert_array_equal(loaded, exact_arr)


# ── Matrix constants ───────────────────────────────────────────────────────

class TestMatrix:
    def test_A_constant(self):
        assert Matrix.A == 'A'

    def test_B_constant(self):
        assert Matrix.B == 'B'

    def test_C_constant(self):
        assert Matrix.C == 'C'

    def test_f_constant(self):
        assert Matrix.f == 'f'


# ── _FactorizedSolver ──────────────────────────────────────────────────────

class TestFactorizedSolver:
    def test_stores_solve_fn(self):
        fn = lambda x: x
        solver = _FactorizedSolver(fn)
        assert solver._solve_fn is fn

    def test_solve_1d_delegates_to_fn(self):
        solver = _FactorizedSolver(lambda rhs: rhs * 2.0)
        result = solver.solve(np.array([1.0, 2.0, 3.0]))
        np.testing.assert_array_equal(result, [2.0, 4.0, 6.0])

    def test_solve_2d_delegates_to_fn(self):
        solver = _FactorizedSolver(lambda rhs: rhs + 1.0)
        rhs = np.array([[1.0, 2.0], [3.0, 4.0]])
        result = solver.solve(rhs)
        np.testing.assert_array_equal(result, [[2.0, 3.0], [4.0, 5.0]])

    def test_solve_converts_list_to_array(self):
        solver = _FactorizedSolver(lambda rhs: rhs)
        result = solver.solve([1.0, 2.0])
        assert isinstance(result, np.ndarray)


# ── factorize ──────────────────────────────────────────────────────────────

class TestFactorize:
    def test_dense_returns_factorized_solver(self):
        solver = factorize(np.eye(3))
        assert isinstance(solver, _FactorizedSolver)

    def test_sparse_returns_factorized_solver(self):
        solver = factorize(scipy.sparse.eye(3, format='csc'))
        assert isinstance(solver, _FactorizedSolver)

    def test_dense_diagonal_correct(self):
        A = np.diag([2.0, 3.0, 4.0])
        b = np.array([4.0, 9.0, 8.0])
        x = factorize(A).solve(b)
        np.testing.assert_allclose(x, [2.0, 3.0, 2.0], rtol=1e-12)

    def test_sparse_diagonal_correct(self):
        A = scipy.sparse.diags([2.0, 3.0, 4.0], format='csc')
        b = np.array([2.0, 6.0, 8.0])
        x = factorize(A).solve(b)
        np.testing.assert_allclose(x, [1.0, 2.0, 2.0], rtol=1e-12)

    def test_dense_satisfies_ax_equals_b(self):
        rng = np.random.default_rng(42)
        n = 5
        A = rng.random((n, n)) + n * np.eye(n)
        b = rng.random(n)
        x = factorize(A).solve(b)
        np.testing.assert_allclose(A @ x, b, rtol=1e-10)

    def test_sparse_satisfies_ax_equals_b(self):
        rng = np.random.default_rng(7)
        n = 5
        A_dense = rng.random((n, n)) + n * np.eye(n)
        A_sparse = scipy.sparse.csc_matrix(A_dense)
        b = rng.random(n)
        x = factorize(A_sparse).solve(b)
        np.testing.assert_allclose(A_dense @ x, b, rtol=1e-10)

    def test_dense_multi_rhs(self):
        A = np.diag([2.0, 3.0])
        B = np.array([[2.0, 4.0], [3.0, 6.0]])
        X = factorize(A).solve(B)
        np.testing.assert_allclose(X, [[1.0, 2.0], [1.0, 2.0]], rtol=1e-12)

    def test_sparse_csr_converted_internally(self):
        A = scipy.sparse.eye(3, format='csr')
        b = np.ones(3)
        x = factorize(A).solve(b)
        np.testing.assert_allclose(x, np.ones(3), rtol=1e-12)

    def test_sparse_full_lower_triangular(self):
        # The 3x3 test data matrix
        A_dense = np.array([
            [1000., 0., 0.],
            [-20., 1., 0.],
            [-5.2, 0., 1.],
        ])
        A_sparse = scipy.sparse.csc_matrix(A_dense)
        f = np.array([1000., 0., 0.])
        x = factorize(A_sparse).solve(f)
        np.testing.assert_allclose(x, [1.0, 20.0, 5.2], rtol=1e-10)
