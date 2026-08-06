from __future__ import annotations
import csv
from functools import lru_cache
import importlib
import os
from typing import List
import numpy
import scipy.linalg
import scipy.sparse
import scipy.sparse.linalg
from pathlib import Path

try:
    pypardiso = importlib.import_module('pypardiso')
except ImportError:
    pypardiso = None

try:
    scikit_umfpack = importlib.import_module('scikits.umfpack')
except ImportError:
    scikit_umfpack = None


def _csv_rows(path: str) -> List[List[str]]:
    '''Read all data rows from a CSV file, skipping the header.

    Parameters
    ----------
    path : str
        Path to the UTF-8 encoded CSV file.

    Returns
    -------
    List[List[str]]
        All rows after the header, where each row is a list of string fields.
    '''
    with open(path, 'r', encoding='utf-8') as stream:
        reader = csv.reader(stream)
        next(reader)
        return list(reader)


def _load_tech_index(folder: str) -> dict:
    '''Load technosphere index from ``index_A.csv`` as ``{process_id: (row_index, flow_unit)}``.

    Parameters
    ----------
    folder : str
        Path to the openLCA matrix export directory.

    Returns
    -------
    dict
        Mapping from process UUID (str) to a ``(row_index, flow_unit)`` tuple,
        where ``row_index`` is the integer row/column index in A and
        ``flow_unit`` is the unit string of the associated flow.
        Returns an empty dict if ``index_A.csv`` does not exist.
    '''
    path = os.path.join(folder, 'index_A.csv')
    if not os.path.exists(path):
        return {}
    return {row[1]: (int(row[0]), row[8]) for row in _csv_rows(path)}


def _load_impact_index(folder: str) -> List[dict]:
    '''Load impact category index from ``index_C.csv``.

    Parameters
    ----------
    folder : str
        Path to the openLCA matrix export directory.

    Returns
    -------
    List[dict]
        Ordered list of dicts with keys ``index`` (int), ``impact_name`` (str),
        and ``impact_unit`` (str). Returns an empty list if ``index_C.csv``
        does not exist.
    '''
    path = os.path.join(folder, 'index_C.csv')
    if not os.path.exists(path):
        return []
    return [{'index': int(row[0]), 'impact_name': row[2].strip(), 'impact_unit': row[3].strip()}
            for row in _csv_rows(path)]


def find_matrix_path(folder: str, name: str):
    '''Return the path of a matrix file in a folder, or ``None`` if absent.

    Parameters
    ----------
    folder : str
        Directory to search in.
    name : str
        Base matrix name (e.g. ``'B'`` or ``'C'``). Tried with ``.npz``,
        then ``.npy``, then without extension.

    Returns
    -------
    str or None
        Full path to the first matching file, or ``None`` if none found.
    '''
    for suffix in ('.npz', '.npy', ''):
        p = os.path.join(folder, name + suffix)
        if os.path.exists(p):
            return p
    return None


def matrix_of(file_path: str):
    '''Load a matrix from a file.

    Parameters
    ----------
    file_path : str
        Path to the matrix file. ``.npz`` files are loaded as sparse
        matrices via :func:`scipy.sparse.load_npz`; all other extensions
        are loaded as dense arrays via :func:`numpy.load`.

    Returns
    -------
    scipy.sparse.spmatrix or numpy.ndarray
        The loaded matrix.
    '''
    if file_path.endswith('.npz'):
        return scipy.sparse.load_npz(file_path)
    return numpy.load(file_path)


def atomic_savez(path: Path, **kwargs):
    '''Save arrays to a ``.npz`` file atomically using a temporary file.

    Parameters
    ----------
    path : Path
        Destination ``.npz`` file path.
    **kwargs
        Named arrays passed directly to :func:`numpy.savez`.
    '''
    tmp = Path(str(path) + f".{os.getpid()}.tmp.npz")
    numpy.savez(tmp, **kwargs)
    os.replace(tmp, path)


def factorize(matrix):
    '''Factorize a matrix and return a callable for repeated solves.

    Performs the (potentially expensive) factorization once and returns a
    callable ``solver(rhs)`` that reuses the stored factors. The backend is
    selected in priority order: pypardiso → scikit-umfpack → scipy splu
    (sparse), or scipy dense LU (dense).

    Parameters
    ----------
    matrix : ndarray or scipy.sparse matrix
        The coefficient matrix to factorize.

    Returns
    -------
    callable
        A function ``solver(rhs)`` that solves ``matrix @ x = rhs`` for ``x``.

    Notes
    -----
    Stores sparse LU factors (L and U), not the dense inverse. The explicit
    inverse of a sparse matrix is generally dense and should never be formed.
    '''
    if scipy.sparse.issparse(matrix):
        if pypardiso is not None:
            return lambda rhs: pypardiso.spsolve(matrix, numpy.asarray(rhs))
        csc = matrix.tocsc() if not scipy.sparse.isspmatrix_csc(matrix) else matrix
        if scikit_umfpack is not None:
            lu = scikit_umfpack.UmfpackLU(csc)
            return lambda rhs: lu.solve(numpy.asarray(rhs))
        lu = scipy.sparse.linalg.splu(csc)
        return lambda rhs: lu.solve(numpy.asarray(rhs))
    lu, piv = scipy.linalg.lu_factor(matrix)
    return lambda rhs: scipy.linalg.lu_solve((lu, piv), numpy.asarray(rhs))


def tech_process_indices(matrix_folder: str, matrix_a) -> numpy.ndarray:
    '''Extract technosphere indices, UUIDs, and flow units for nonzero entries in ``A[:, 0]``.

    Parameters
    ----------
    matrix_folder : str
        Path to the openLCA matrix export directory, used to load ``index_A.csv``.
    matrix_a : ndarray or scipy.sparse.spmatrix
        Technosphere matrix.

    Returns
    -------
    numpy.ndarray
        Four-column object array with ``[index, uuid, value, flow_unit]`` per
        row for nonzero components of the first technosphere column.
    '''
    col0 = matrix_a[:, 0]
    a_col0 = numpy.asarray(col0.toarray() if scipy.sparse.issparse(matrix_a) else col0).reshape(-1)
    nonzero = set(numpy.flatnonzero(a_col0).tolist())
    rows = [
        (idx, uuid, a_col0[idx], flow_unit)
        for uuid, (idx, flow_unit) in _load_tech_index(matrix_folder).items()
        if idx in nonzero
    ]
    return numpy.array(rows, dtype=object)


def load_matrices_from_folder(matrix_folder: str):
    '''Load openLCA folder metadata and matrices.

    Parameters
    ----------
    matrix_folder : str
        Path to the openLCA matrix export folder.

    Returns
    -------
    impact_index : List[dict]
        Ordered list of dicts with keys ``index``, ``impact_name``, and
        ``impact_unit``, loaded from ``index_C.csv``.
    techno_index_uuid : numpy.ndarray
        Four-column object array with ``[index, uuid, value, flow_unit]``
        per row for each nonzero entry in the first technosphere column.
    A : numpy.ndarray or scipy.sparse.spmatrix
        Technosphere matrix.
    B : numpy.ndarray or scipy.sparse.spmatrix
        Intervention matrix.
    C : numpy.ndarray or scipy.sparse.spmatrix
        Characterization matrix.
    f : numpy.ndarray
        Demand vector.

    Raises
    ------
    ValueError
        If any required matrix or index file could not be loaded.
    '''
    print("Loading matrices from folder:")

    def _load(name):
        path = find_matrix_path(matrix_folder, name)
        return matrix_of(path) if path is not None else None

    A = _load('A')
    techno_index_uuid = tech_process_indices(matrix_folder, A) if A is not None else None
    B = _load('B')
    C = _load('C')
    f = _load('f')
    impact_index = _load_impact_index(matrix_folder)
    missing = [name for name, m in zip(('A', 'B', 'C', 'f', 'index_A.csv'),
                                       (A, B, C, f, techno_index_uuid))
               if m is None]
    if missing:
        raise ValueError(f"{', '.join(missing)} could not be loaded from the specified folder.")
    return impact_index, techno_index_uuid, A, B, C, f


@lru_cache(maxsize=None)
def get_cache_paths(matrix_folder: str) -> dict:
    '''Create the ``Initial_Artifacts`` cache directory and return its ``.npz`` file paths.

    Creates the directory if it does not already exist. Results are cached by
    :func:`functools.lru_cache` so the directory is created at most once per
    process per ``matrix_folder`` path.

    Parameters
    ----------
    matrix_folder : str
        Path to the openLCA matrix export folder.

    Returns
    -------
    dict
        Mapping from each ``LCA._cache`` key to its ``.npz`` file path inside
        the ``Initial_Artifacts`` subdirectory.
    '''
    cache_dir = Path(matrix_folder) / 'Initial_Artifacts'
    cache_dir.mkdir(parents=True, exist_ok=True)
    b_suffix = Path(find_matrix_path(matrix_folder, 'B') or 'B.npz').suffix
    c_suffix = Path(find_matrix_path(matrix_folder, 'C') or 'C.npz').suffix
    return {
        'base_scaling_vector': cache_dir / 'base_scaling_vector.npz',
        'A0_column':           cache_dir / 'A0_column.npz',
        'basis_component':     cache_dir / 'basis_component.npz',
        'matrix_B':            cache_dir / f'matrix_B{b_suffix}',
        'matrix_C':            cache_dir / f'matrix_C{c_suffix}',
        'impact_index':        cache_dir / 'impact_index.npz',
    }
