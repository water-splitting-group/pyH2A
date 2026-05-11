"""
This is an example module how you can use the openLCA matrix export from Python.
It is part of the openLCA source code which is licensed under the Mozilla Public
License 2.0 (MPL 2.0; see https://github.com/GreenDelta/olca-app).
"""
from __future__ import annotations

import csv
import importlib
import os
from functools import lru_cache
from typing import List
import numpy
import numpy.linalg
import scipy.linalg
import scipy.sparse
import scipy.sparse.linalg

try:
    pypardiso = importlib.import_module('pypardiso')
except ImportError:
    pypardiso = None

try:
    scikit_umfpack = importlib.import_module('scikits.umfpack')
except ImportError:
    scikit_umfpack = None


_SPARSE_CSC_CACHE = {}


class TechEntry:
    """
    A TechEntry contains the meta data of a row or column of the technosphere
    matrix A.
    """

    def __init__(self):
        self.index = -1
        self.process_id = ''
        self.process_name = ''
        self.process_category = ''
        self.process_location = ''
        self.flow_id = ''
        self.flow_name = ''
        self.flow_category = ''
        self.flow_unit = ''
        self.flow_type = ''

    @staticmethod
    def _from_csv(row: List[str]) -> TechEntry:
        e = TechEntry()
        e.index = int(row[0])
        e.process_id = row[1]
        e.process_name = row[2]
        e.process_category = row[3]
        e.process_location = row[4]
        e.flow_id = row[5]
        e.flow_name = row[6]
        e.flow_category = row[7]
        e.flow_unit = row[8]
        e.flow_type = row[9]
        return e

    @staticmethod
    def index_of(file_path: str) -> List[TechEntry]:
        index = []
        for row in _csv_rows_of(file_path):
            index.append(TechEntry._from_csv(row))
        return index
    
    @staticmethod
    def dict_of(file_path: str) -> dict:
        dict_index = {}
        for row in _csv_rows_of(file_path):
            entry = TechEntry._from_csv(row)
            dict_index[entry.process_id] = entry
        return dict_index


class FlowEntry:
    """
    A FlowEntry contains the meta data of a row in the intervention matrix B.
    """

    def __init__(self):
        self.index = -1
        self.flow_id = ''
        self.flow_name = ''
        self.flow_category = ''
        self.flow_unit = ''
        self.flow_type = ''
        self.location_id = ''
        self.location_name = ''
        self.location_code = ''

    @staticmethod
    def _from_csv(row: List[str]) -> FlowEntry:
        e = FlowEntry()
        e.index = int(row[0])
        e.flow_id = row[1]
        e.flow_name = row[2]
        e.flow_category = row[3]
        e.flow_unit = row[4]
        e.flow_type = row[5]
        e.location_id = row[6]
        e.location_name = row[7]
        e.location_code = row[8]
        return e

    @staticmethod
    def index_of(file_path: str) -> List[FlowEntry]:
        index = []
        for row in _csv_rows_of(file_path):
            index.append(FlowEntry._from_csv(row))
        return index
    

class ImpactEntry:
    """
    An ImpactEntry contains the meta data of a row in the characterization
    matrix C.
    """

    def __init__(self):
        self.index = -1
        self.impact_id = ''
        self.impact_name = ''
        self.impact_unit = ''

    @staticmethod
    def _from_csv(row: List[str]) -> ImpactEntry:
        e = ImpactEntry()
        e.index = int(row[0])
        e.impact_id = row[1]
        e.impact_name = row[2]
        e.impact_unit = row[3]
        return e

    @staticmethod
    def index_of(file_path: str) -> List[ImpactEntry]:
        index = []
        for row in _csv_rows_of(file_path):
            index.append(ImpactEntry._from_csv(row))
        return index


@lru_cache(maxsize=None)
def matrix_of(file_path: str):
    if file_path.endswith('.npz'):
        return scipy.sparse.load_npz(file_path)
    else:
        return numpy.load(file_path)


@lru_cache(maxsize=None)
def _csv_rows_of(f: str) -> List[List[str]]:
    with open(f, 'r', encoding='utf-8') as stream:
        reader = csv.reader(stream)
        next(reader)  # skip header
        return list(reader)


class ExportFolder:

    def __init__(self, folder: str):
        self.folder = folder

    def tech_index(self) -> List[TechEntry]:
        path = os.path.join(self.folder, 'index_A.csv')
        if not os.path.exists(path):
            return []
        return TechEntry.dict_of(path)

    def flow_index(self) -> List[FlowEntry]:
        path = os.path.join(self.folder, 'index_B.csv')
        if not os.path.exists(path):
            return []
        return FlowEntry.index_of(path)

    def impact_index(self) -> List[ImpactEntry]:
        path = os.path.join(self.folder, 'index_C.csv')
        if not os.path.exists(path):
            return []
        return ImpactEntry.index_of(path)

    def has_impacts(self):
        path = os.path.join(self.folder, 'index_C.csv')
        return os.path.exists(path)

    def load(self, name: str):
        path = os.path.join(self.folder, name)
        if os.path.exists(path):
            return matrix_of(path)
        p = path + '.npy'
        if os.path.exists(p):
            return matrix_of(p)
        p = path + '.npz'
        if os.path.exists(p):
            return matrix_of(p)
        return None


class Matrix:
    A = 'A'
    B = 'B'
    C = 'C'
    f = 'f'


def _as_dense(matrix):
    if scipy.sparse.issparse(matrix):
        return matrix.todense()
    return matrix


def solve(matrix, f):
    """
    Solve matrix * x = f using sparse backends when possible.
    
    Attempts to use the fastest available solver in this order:
    1. pypardiso (MKL-backed, very fast on Windows/Linux, optional on Mac)
    2. scikit-umfpack (UMFPACK-backed, cross-platform including Mac)
    3. scipy.sparse.linalg.splu (default, always available)
    """
    if scipy.sparse.issparse(matrix):
        rhs = numpy.asarray(f).reshape(-1)

        # Try pypardiso first (MKL-backed, fastest when available)
        if pypardiso is not None:
            return pypardiso.spsolve(matrix, rhs)

        # Try scikit-umfpack next (cross-platform, including Mac)
        if scikit_umfpack is not None:
            try:
                if not scipy.sparse.isspmatrix_csc(matrix):
                    matrix = matrix.tocsc()
                return scikit_umfpack.spsolve(matrix, rhs)
            except Exception:
                # Fall through to scipy default if umfpack fails
                pass

        # Fall back to scipy's default sparse solver
        if scipy.sparse.isspmatrix_csc(matrix):
            csc_matrix = matrix
        else:
            matrix_id = id(matrix)
            csc_matrix = _SPARSE_CSC_CACHE.get(matrix_id)
            if csc_matrix is None:
                csc_matrix = matrix.tocsc()
                _SPARSE_CSC_CACHE[matrix_id] = csc_matrix

        lu_factor = scipy.sparse.linalg.splu(csc_matrix)
        return lu_factor.solve(rhs)

    return numpy.linalg.solve(matrix, f)


def invert(matrix):
    return numpy.linalg.inv(_as_dense(matrix))


class _FactorizedSolver:
    """Holds a pre-factorized matrix for repeated right-hand-side solves."""

    def __init__(self, _solve_fn):
        self._solve_fn = _solve_fn

    def solve(self, rhs):
        """Solve for one or many right-hand sides.

        Parameters
        ----------
        rhs : array-like, shape (n,) or (n, k)
            A single RHS vector or a matrix of k RHS column vectors.

        Returns
        -------
        ndarray, shape (n,) or (n, k)
            Solution vector(s). Shape matches input.
        """
        rhs = numpy.asarray(rhs)
        if rhs.ndim == 1:
            return self._solve_fn(rhs)
        # 2-D: solve each column; underlying solvers (splu, pypardiso) accept 2-D directly
        return self._solve_fn(rhs)


def factorize(matrix):
    """
    Factorize a matrix once and return a solver for repeated solves.

    Unlike :func:`solve`, this function performs the (potentially expensive)
    matrix factorization once and stores the sparse factors so that subsequent
    right-hand-side solves only require triangular back-substitution — no
    re-factorization. This is significantly faster when the same matrix must
    be solved against multiple right-hand sides.

    Note: this stores the sparse LU factors (L and U), not the dense inverse.
    The inverse of a sparse matrix is generally dense and should never be
    formed explicitly.

    Parameters
    ----------
    matrix : ndarray or scipy.sparse matrix
        The coefficient matrix to factorize.

    Returns
    -------
    _FactorizedSolver
        Object with a `.solve(rhs)` method that reuses the stored factors.
    """
    if scipy.sparse.issparse(matrix):
        # pypardiso: spsolve handles factorization internally and is the fastest option
        if pypardiso is not None:
            return _FactorizedSolver(lambda rhs: pypardiso.spsolve(matrix, rhs))

        # splu: factorize once, reuse sparse LU factors for each rhs
        csc = matrix.tocsc() if not scipy.sparse.isspmatrix_csc(matrix) else matrix
        lu = scipy.sparse.linalg.splu(csc)
        return _FactorizedSolver(lu.solve)

    # Dense matrix: LU factorization with partial pivoting
    lu, piv = scipy.linalg.lu_factor(matrix)
    return _FactorizedSolver(lambda rhs: scipy.linalg.lu_solve((lu, piv), rhs))
