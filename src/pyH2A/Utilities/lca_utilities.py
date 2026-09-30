from __future__ import annotations
import csv
import importlib
import os
from typing import List
import numpy
import scipy.linalg
import scipy.sparse
import scipy.sparse.linalg
from pathlib import Path

# Try to import pypardiso (Windows and Linux)
try:
    pypardiso = importlib.import_module('pypardiso')
except ImportError:
    pypardiso = None

# Try to import scikit-umfpack (macOS)
try:
    scikit_umfpack = importlib.import_module('scikits.umfpack')
except ImportError:
    scikit_umfpack = None

# Source files of an openLCA export that the cached artifacts are derived from.
SOURCE_FILES = ('A', 'B', 'C', 'index_A.csv', 'index_C.csv')

#### ----------------------------------------------------------------- ####
#### Functions for reading in OpenLCA matrix exports and their indices ####
#### ----------------------------------------------------------------- ####

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

    Raises
    ------
    ValueError
        If a provider UUID appears on more than one row, which would silently
        drop technosphere columns.
    '''
    path = os.path.join(folder, 'index_A.csv')

    # If the index file is absent, return an empty dict. 
    if not os.path.exists(path):
        return {}
    
    rows = _csv_rows(path)
    index = {row[1]: (int(row[0]), row[8]) for row in rows}

    # If the number of unique provider IDs is less than the number of rows, there are duplicates.
    if len(index) != len(rows):
        raise ValueError(f"{path} contains duplicate provider IDs; "
                         "multi-output processes are not supported.")
    
    return index

def dense_column(matrix, index: int) -> numpy.ndarray:
    '''Return one column of a dense or sparse matrix as a 1-D dense array.

    Parameters
    ----------
    matrix : ndarray or scipy.sparse.spmatrix
        Matrix to take the column from.
    index : int
        Column index.

    Returns
    -------
    numpy.ndarray
        The column, flattened to one dimension.
    '''
    column = matrix[:, [index]]

    return numpy.asarray(column.todense() if scipy.sparse.issparse(column) else column).reshape(-1)

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
        row for nonzero components of the first technosphere column, ordered by
        index so that the first row is always the reference flow.

    Raises
    ------
    ValueError
        If the first technosphere column has no positive entry in row 0, i.e. if
        it does not produce the reference flow the demand vector asks for.
    '''

    a_column_0 = dense_column(matrix_a, 0)
    nonzero = set(numpy.flatnonzero(a_column_0).tolist())

    rows = [
        (idx, uuid, a_column_0[idx], flow_unit)
        for uuid, (idx, flow_unit) in _load_tech_index(matrix_folder).items()
        if idx in nonzero
    ]

    rows.sort(key=lambda row: row[0])

    # Row 0 is the reference flow of the product system. The demand vector, the rank-1
    # update and the product flow unit all address it by position, so an export whose first
    # technosphere column does not produce flow 0 would be solved for a different product
    # without anything downstream noticing.
    if not rows or rows[0][0] != 0 or rows[0][2] <= 0:
        raise ValueError(
            f"The first technosphere column of the export in '{matrix_folder}' does not produce "
            "its own reference flow: row 0 of A[:, 0] must be a positive (output) entry.")

    return numpy.array(rows, dtype=object)

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

    # If the index file is absent, return an empty list.
    if not os.path.exists(path):
        return []

    # Read all rows and convert to a list of dicts with the desired keys.
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

        # If the file exists, return its path. Otherwise, continue to the next suffix.
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

    # If the file has a .npz extension, load it as a sparse matrix using scipy.sparse.load_npz.
    if file_path.endswith('.npz'):
        return scipy.sparse.load_npz(file_path)

    # Otherwise, load it as a dense array using numpy.load.
    else:
        return numpy.load(file_path)

def _load(matrix_folder: str, name: str) -> numpy.ndarray | scipy.sparse.spmatrix | None:
    '''Load a matrix from a folder, returning None if the file is absent.

    Parameters
    ----------
    matrix_folder : str
        Path to the openLCA matrix export folder.
    name : str
        Base matrix name (e.g. ``'A'``, ``'B'`, or ``'C'``).

    Returns
    -------
    numpy.ndarray or scipy.sparse.spmatrix or None
        The loaded matrix, or ``None`` if the file does not exist.
    '''

    path = find_matrix_path(matrix_folder, name)

    return matrix_of(path) if path is not None else None

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

    Raises
    ------
    ValueError
        If any required matrix or index file could not be loaded.

    Notes
    -----
    The exported demand vector ``f`` is not read: the demand is always one unit
    of the reference flow, which is built directly by the caller.
    '''
    A = _load(matrix_folder, 'A')
    B = _load(matrix_folder, 'B')
    C = _load(matrix_folder, 'C')

    techno_index_uuid = tech_process_indices(matrix_folder, A) if A is not None else None
    impact_index = _load_impact_index(matrix_folder)

    missing = [name for name, m in zip(('A', 'B', 'C', 'index_A.csv'),
                                       (A, B, C, techno_index_uuid))
               if m is None]

    # If any required matrix or index file could not be loaded, raise a ValueError with the missing files listed.
    if missing:
        raise ValueError(f"{', '.join(missing)} could not be loaded from the specified folder.")
    
    return impact_index, techno_index_uuid, A, B, C

#### ----------------------------------------------------------------- ####
#### Functions for saving artefacts and retrieving them from cache     ####
#### ----------------------------------------------------------------- ####

def atomic_savez(path: Path, **kwargs):
    '''Save arrays to a ``.npz`` file atomically using a temporary file.

    Parameters
    ----------
    path : Path
        Destination ``.npz`` file path.
    **kwargs
        Named arrays passed directly to :func:`numpy.savez`.
    '''
    # Create a temporary file with a unique name based on the process ID to avoid conflicts in parallel runs.
    tmp = Path(str(path) + f".{os.getpid()}.tmp.npz")
    # Save the arrays to the temporary file using numpy.savez
    numpy.savez(tmp, **kwargs)
    # Then replace the target file with the temporary file atomically.
    os.replace(tmp, path)

def get_cache_paths(matrix_folder: str) -> dict:
    '''Create the ``Initial_Artifacts`` cache directory and return its file paths.

    Creates the directory if it does not already exist.

    Parameters
    ----------
    matrix_folder : str
        Path to the openLCA matrix export folder.

    Returns
    -------
    dict
        Mapping from each ``LCA_Plugin._cache`` key to its
        ``.npz`` file path inside the ``Initial_Artifacts`` subdirectory, plus
        ``'fingerprint'`` for the export identity written by
        :func:`export_fingerprint`.
    '''
    cache_dir = Path(matrix_folder) / 'Initial_Artifacts'
    cache_dir.mkdir(parents = True, exist_ok = True)

    return {
        'base_scaling_vector': cache_dir / 'base_scaling_vector.npz',
        'A0_column':           cache_dir / 'A0_column.npz',
        'basis_component':     cache_dir / 'basis_component.npz',
        'h_base':              cache_dir / 'h_base.npz',
        'h_basis':             cache_dir / 'h_basis.npz',
        'impact_index':        cache_dir / 'impact_index.npz',
        'fingerprint':         cache_dir / 'fingerprint.txt',
    }

def export_fingerprint(matrix_folder: str) -> str:
    '''Identity of the openLCA export; changes whenever any source file does.

    Used to invalidate cached artifacts when the export is replaced. Files that
    cannot be resolved are skipped, so a missing matrix still surfaces as the
    explicit error from :func:`load_matrices_from_folder`.

    Parameters
    ----------
    matrix_folder : str
        Path to the openLCA matrix export folder.

    Returns
    -------
    str
        Name, size and modification time of every source file of the export.
    '''
    paths = [find_matrix_path(matrix_folder, name) for name in SOURCE_FILES]

    # Return a string representation of the list of tuples (name, size, mtime) for each source file that exists.
    return str([(name, os.path.getsize(p), os.path.getmtime(p))
                for name, p in zip(SOURCE_FILES, paths) if p])

#### ----------------------------------------------------------------- ####
#### Utility function for factorizing matrices                         ####
#### ----------------------------------------------------------------- ####

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
        # If matrix is sparse and pypardiso is available, use it for fast solving
        if pypardiso is not None:
            return lambda rhs: pypardiso.spsolve(matrix, numpy.asarray(rhs))

        # Cconvert to CSC format for splu or scikit-umfpack, which require it
        csc = matrix.tocsc() if not scipy.sparse.isspmatrix_csc(matrix) else matrix

        # If scikit-umfpack is available, use it for solving
        if scikit_umfpack is not None:
            lu = scikit_umfpack.UmfpackLU(csc)
            return lambda rhs: lu.solve(numpy.asarray(rhs))

        # Convert to CSC format to LU and solve with scipy.sparse.linalg.splu
        lu = scipy.sparse.linalg.splu(csc)
        return lambda rhs: lu.solve(numpy.asarray(rhs))

    # If matrix is dense, use scipy.linalg.lu_factor and lu_solve
    else:
        lu, piv = scipy.linalg.lu_factor(matrix)
        return lambda rhs: scipy.linalg.lu_solve((lu, piv), numpy.asarray(rhs))