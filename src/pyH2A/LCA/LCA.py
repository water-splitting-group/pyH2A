import os
import shutil
from functools import lru_cache
from pathlib import Path
import numpy as np

from pyH2A import Discounted_Cash_Flow
from pyH2A.Utilities.input_modification import process_table
from pyH2A.Utilities.lca_utils import (
    ExportFolder,
    Matrix,
    factorize,
    find_matrix_path,
    get_disk_cache_dir,
    matrix_of,
)

class LCA:
    '''Perform LCA calculations from an openLCA matrix export.

    Parameters
    ----------
    matrix_folder : str
        Path to the openLCA matrix export folder containing the technosphere
        (A), intervention (B), characterization (C), and demand (f) matrices.
    dcf : pyH2A.Discounted_Cash_Flow
        Discounted cash flow object containing the parsed model inputs. Tables
        whose names start with ``"LCA"`` are used to update technosphere
        component values.

    Attributes
    ----------
    matrix_folder : str
        Path to the openLCA matrix export folder, used as the RAM cache key.
    export_folder : ExportFolder
        Loaded openLCA export folder. Stored as a class attribute.
    techno_index_uuid : numpy.ndarray
        Three-column object array ``[index, uuid, value]`` for each nonzero
        entry in the first technosphere column. Stored as a class attribute.
    A : numpy.ndarray or scipy.sparse.spmatrix
        Technosphere matrix. Stored as a class attribute.
    B : numpy.ndarray or scipy.sparse.spmatrix
        Intervention matrix. Stored as a class attribute.
    C : numpy.ndarray or scipy.sparse.spmatrix
        Characterization matrix. Stored as a class attribute.
    f : numpy.ndarray
        Demand vector. Stored as a class attribute.
    scaling_vector : numpy.ndarray
        Scenario-specific activity scaling vector.
    lca_results : dict
        LCIA results keyed by impact name. Each value is a dictionary with
        ``"value"`` and ``"unit"`` entries.

    Raises
    ------
    ValueError
        Raised when no LCA input tables are found, an LCA component is missing
        required fields, or a component UUID is absent from the technosphere
        index.
    ZeroDivisionError
        Raised when the Sherman-Morrison denominator is too small for a stable
        rank-1 update.

    Notes
    -----
    All caches are class-level and process-local. Disk artifacts are stored
    inside an ``Initial_Artifacts`` subdirectory of the matrix export folder,
    managed by :func:`pyH2A.Utilities.lca_utils.get_disk_cache_dir`.
    '''

    _SM_TOL = 1e-12
    _base_scaling_vector_cache = {}     # {matrix_folder: base_scaling_vector}
    _A0_cache = {}              # {matrix_folder: (indices_int, uuids_str, values_float)} — nonzero rows of A[:, 0]
    _component_basis_cache = {} # {matrix_folder: basis_matrix} — columns are A^{-1} e_i for each nonzero row
    _uuid_index_cache = {}      # {matrix_folder: {uuid_str: int_index}}
    _impact_index_cache = {}    # {matrix_folder: [ImpactEntry, ...]}
    _matrix_bc_cache = {}       # {matrix_folder: (B, C)} — sparse originals
      
    def __init__(self, matrix_folder: str, dcf: Discounted_Cash_Flow):
        '''Initialize and run the LCA calculation workflow.

        This constructor loads all matrices, prepares solver and cache state,
        builds the scenario scaling vector via Sherman-Morrison update, and
        computes LCIA results.

        Parameters
        ----------
        matrix_folder : str
            Path to the openLCA matrix export folder.
        dcf : pyH2A.Discounted_Cash_Flow
            Discounted cash flow object containing model inputs used to
            construct the scaling vector.

        Raises
        ------
        ValueError
            Raised when LCA component input is missing or invalid.
        ZeroDivisionError
            Raised when the Sherman-Morrison update is numerically singular.
        '''
        self.matrix_folder = matrix_folder
        self.initialize_all_artifacts()
        self.build_scaling_vector(dcf)
        self.perform_lca()
    
      
    @classmethod
    @lru_cache(maxsize=None)
    def load_matrices_from_folder(cls, matrix_folder: str):
        '''Load openLCA folder metadata and matrices.

        Parameters
        ----------
        matrix_folder : str
            Path to the openLCA matrix export folder.

        Returns
        -------
        export_folder : ExportFolder
            Loaded export folder.
        techno_index_uuid : numpy.ndarray
            Three-column object array with ``[index, uuid, value]`` per row
            for each nonzero entry in the first technosphere column.
        A : numpy.ndarray or scipy.sparse.spmatrix
            Technosphere matrix.
        B : numpy.ndarray or scipy.sparse.spmatrix
            Intervention matrix.
        C : numpy.ndarray or scipy.sparse.spmatrix
            Characterization matrix.
        f : numpy.ndarray
            Demand vector.

        Notes
        -----
        This method is backed by :func:`functools.lru_cache`, so repeated calls
        with the same ``matrix_folder`` reuse loaded objects within a process.
        The cache is not shared across multiprocessing workers.
        '''
        print(f"Loading matrices from folder:")
        loaded_folder = ExportFolder(matrix_folder)
        cls.export_folder = loaded_folder
        cls.A = loaded_folder.load(Matrix.A)
        # Load technosphere index with UUIDs and first column values of A for nonzero first-column entries with the order of indeces
        cls.techno_index_uuid = loaded_folder.tech_process_indices(matrix_a=cls.A) 
        cls.B = loaded_folder.load(Matrix.B)
        cls.C = loaded_folder.load(Matrix.C)
        cls.f = loaded_folder.load(Matrix.f)
        return cls.export_folder, cls.techno_index_uuid, cls.A, cls.B, cls.C, cls.f

    def initialize_all_artifacts(self):
        '''Prepare all matrix artifacts and component basis vectors.

        Fills the class-level RAM caches from disk if available, or computes
        and writes them if not. Solver and factorization objects are kept in
        RAM only; all other artifacts are also written to disk atomically for
        reuse by worker processes and any future computations.

        Notes
        -----
        Populates the class-level caches for the base scaling vector,
        ``_A0_cache`` (nonzero first-column entries as indices, UUIDs, and
        values), ``_component_basis_cache`` (precomputed ``A^{-1} e_i``
        basis vectors), ``_matrix_bc_cache`` (dense B and C), and
        ``_impact_index_cache``. Disk writes use ``os.replace`` for atomic
        file replacement with no explicit locking.
        '''

        # Try to load artifacts from RAM (process-local cache)
        base_cached = LCA._base_scaling_vector_cache.get(self.matrix_folder)
        component_basis_cached = LCA._component_basis_cache.get(self.matrix_folder)
        A0_cached = LCA._A0_cache.get(self.matrix_folder)
        bc_cached = LCA._matrix_bc_cache.get(self.matrix_folder)
        impact_index_cached = LCA._impact_index_cache.get(self.matrix_folder)
        if base_cached is not None and component_basis_cached is not None and A0_cached is not None and bc_cached is not None and impact_index_cached is not None:
            return

        # Not in RAM: try to load artifacts from disk cache (solver is not stored on disk).
        cache_path = get_disk_cache_dir(self.matrix_folder)
        base_cache_path = cache_path / "scalingvector.npz"
        A0_cache_path = cache_path / "A0_column.npz"
        basis_cache_path = cache_path / "basis_component.npz"
        bc_B_cache_path = cache_path / "matrix_b.npz"
        bc_C_cache_path = cache_path / "matrix_c.npz"
        base_loaded = self.load_artifacts_from_disk_to_ram(base_cache_path)
        A0_loaded = self.load_A0_from_disk_to_ram(A0_cache_path)
        basis_component_loaded = self.load_basis_component_from_disk_to_ram(basis_cache_path)
        bc_loaded = self.load_matrix_bc_from_disk_to_ram(bc_B_cache_path, bc_C_cache_path)
        impact_index_loaded = self.load_impact_index_from_disk_to_ram(cache_path / "impact_index.npz")
        if base_loaded and basis_component_loaded and A0_loaded and bc_loaded and impact_index_loaded:
            return


        # Not in RAM or disk: compute artifacts/compute basis vectors and cache to disk and RAM for future reuse.
        (
            LCA.export_folder,
            LCA.techno_index_uuid,
            LCA.A,
            LCA.B,
            LCA.C,
            LCA.f,
        ) = self.load_matrices_from_folder(self.matrix_folder)

        solver = factorize(LCA.A)  # Only stored in RAM
        f_vector = np.asarray(LCA.f).reshape(-1)
        _base_scaling_vector = solver.solve(f_vector)

        # Write only the artifacts to disk cache (not the solver)
        tmp_path = Path(str(base_cache_path) + f".{os.getpid()}.tmp.npz")
        np.savez(tmp_path, base_scaling_vector=_base_scaling_vector)
        os.replace(tmp_path, base_cache_path)
        # Store in-process artifacts in RAM for fast reuse.
        LCA._base_scaling_vector_cache[self.matrix_folder] = _base_scaling_vector

        # Cache index and value columns of techno_index_uuid (UUID column is a string and cannot be serialised as numeric).
        tmp_path = Path(str(A0_cache_path) + f".{os.getpid()}.tmp.npz")
        np.savez(tmp_path,
                 indices=np.asarray(LCA.techno_index_uuid[:, 0], dtype=int),
                 uuids=np.asarray(LCA.techno_index_uuid[:, 1], dtype=str),
                 values=np.asarray(LCA.techno_index_uuid[:, 2], dtype=float))
        os.replace(tmp_path, A0_cache_path)
        LCA._A0_cache[self.matrix_folder] = (
            np.asarray(LCA.techno_index_uuid[:, 0], dtype=int),
            np.asarray(LCA.techno_index_uuid[:, 1], dtype=str),
            np.asarray(LCA.techno_index_uuid[:, 2], dtype=float),
        )
        # Compute and cache component basis vectors for the nonzero rows of the original first technosphere column.
        # Each column of the basis matrix is ``A^{-1} e_i`` for a changed row, enabling efficient Sherman-Morrison 
        # updates without full solves for each Monte Carlo sample.
        nonzero_indices = np.asarray(LCA.techno_index_uuid[:, 0], dtype=int)
        n_rows = LCA.A.shape[0]
        n_cols = len(nonzero_indices)
        eye_subset = np.zeros((n_rows, n_cols), dtype=float) 
        eye_subset[nonzero_indices, np.arange(n_cols)] = 1.0
        basis_component = np.asarray(solver.solve(eye_subset))
        tmp_path = Path(str(basis_cache_path) + f".{os.getpid()}.tmp.npz")
        np.savez(tmp_path, basis_component=basis_component)
        os.replace(tmp_path, basis_cache_path)
        LCA._component_basis_cache[self.matrix_folder] = basis_component

        # Copy the original sparse B and C files to disk (Initial_Artifacts) and load them to RAM.
        src_b = find_matrix_path(self.matrix_folder, Matrix.B)
        src_c = find_matrix_path(self.matrix_folder, Matrix.C)
        if src_b is not None and not bc_B_cache_path.exists():
            shutil.copy2(src_b, str(bc_B_cache_path))
        if src_c is not None and not bc_C_cache_path.exists():
            shutil.copy2(src_c, str(bc_C_cache_path))
        LCA._matrix_bc_cache[self.matrix_folder] = (LCA.B, LCA.C)

        #store impact index to disk and RAM for later use in result assembly
        tmp_path = Path(str(cache_path / "impact_index.npz") + f".{os.getpid()}.tmp.npz")
        np.savez(tmp_path, impact_index=np.array(list(LCA.export_folder.impact_index()), dtype=object))
        os.replace(tmp_path, cache_path / "impact_index.npz")
        LCA._impact_index_cache[self.matrix_folder] = list(LCA.export_folder.impact_index())

    def load_artifacts_from_disk_to_ram(self, base_cache_path) -> bool:
        '''Load base artifacts from disk into process-local RAM.

        Parameters
        ----------
        base_cache_path : pathlib.Path
            Path to the ``.npz`` file containing the base scaling vector.

        Returns
        -------
        bool
            ``True`` if cache data were loaded successfully, otherwise
            ``False``.

        Notes
        -----
        On success, ``LCA._base_scaling_vector_cache[self.matrix_folder]`` is
        populated with the base scaling vector. Solver/factorization objects
        are not stored on disk and must be recomputed when needed.
        '''

        if not base_cache_path.exists():
            return False

        try:
            with np.load(base_cache_path) as data:
                LCA._base_scaling_vector_cache[self.matrix_folder] = np.asarray(data['base_scaling_vector'])
            return True
        except:
            return False

    def load_A0_from_disk_to_ram(self, A0_cache_path) -> bool:
        '''Load the nonzero first-column entries of the technosphere matrix from disk into RAM.

        Parameters
        ----------
        A0_cache_path : pathlib.Path
            Path to the ``.npz`` file containing the ``indices``, ``uuids``,
            and ``values`` arrays for nonzero entries of ``A[:, 0]``.

        Returns
        -------
        bool
            ``True`` if data were loaded successfully, otherwise ``False``.

        Notes
        -----
        On success, ``LCA._A0_cache[self.matrix_folder]`` is set to a tuple
        ``(indices_int, uuids_str, values_float)``.
        '''

        if not A0_cache_path.exists():
            return False

        try:
            with np.load(A0_cache_path) as data:
                LCA._A0_cache[self.matrix_folder] = (
                    np.asarray(data['indices'], dtype=int),
                    np.asarray(data['uuids'], dtype=str),
                    np.asarray(data['values'], dtype=float),
                )
            return True
        except:
            return False
 
    def load_basis_component_from_disk_to_ram(self, basis_cache_path):
        '''Load cached component basis vectors from disk into RAM.

        Parameters
        ----------
        basis_cache_path : pathlib.Path
            Path to the component basis cache .npz file.

        Returns
        -------
        bool
            ``True`` if basis vectors were loaded successfully, ``False``
            when the cache file is missing or cannot be read.

        Notes
        -----
        On success, ``LCA._component_basis_cache[self.matrix_folder]`` is set
        to a dense matrix whose columns are ``A^{-1} e_i`` for each nonzero
        row of the original first technosphere column.
        '''

        if not basis_cache_path.exists():
            return False

        try:
            with np.load(basis_cache_path) as data:
                LCA._component_basis_cache[self.matrix_folder] = np.asarray(data['basis_component'], dtype=float)
            return True
        except:
            return False

    def load_matrix_bc_from_disk_to_ram(self, bc_B_cache_path, bc_C_cache_path) -> bool:
        '''Load cached intervention and characterization matrices from disk into RAM.

        Parameters
        ----------
        bc_B_cache_path : pathlib.Path
            Path to the cached B matrix file (sparse ``.npz``).
        bc_C_cache_path : pathlib.Path
            Path to the cached C matrix file (sparse ``.npz``).

        Returns
        -------
        bool
            ``True`` if both matrices were loaded successfully, ``False``
            when either file is missing or cannot be read.

        Notes
        -----
        Files are loaded via :func:`matrix_of`, which uses
        ``scipy.sparse.load_npz`` for ``.npz`` files, preserving the sparse
        format. On success, ``LCA._matrix_bc_cache`` is updated for the
        current matrix folder key.
        '''
        if not bc_B_cache_path.exists() or not bc_C_cache_path.exists():
            return False

        try:
            LCA._matrix_bc_cache[self.matrix_folder] = (
                matrix_of(str(bc_B_cache_path)),
                matrix_of(str(bc_C_cache_path)),
            )
            return True
        except:
            return False
   
    def load_impact_index_from_disk_to_ram(self, impact_index_cache_path) -> bool:
        '''Load cached impact index from disk into RAM.

        Parameters
        ----------
        impact_index_cache_path : pathlib.Path
            Path to the ``.npz`` file containing the impact index.

        Returns
        -------
        bool
            ``True`` if the impact index was loaded successfully, ``False``
            when the cache file is missing or cannot be read.

        Notes
        -----
        On success, ``LCA._impact_index_cache`` is updated for the current
        matrix folder key.
        '''
        if not impact_index_cache_path.exists():
            return False

        try:
            with np.load(impact_index_cache_path, allow_pickle=True) as data:
                LCA._impact_index_cache[self.matrix_folder] = list(data['impact_index'])
            return True
        except:
            return False

    def apply_component_updates(self, dcf):
        '''Collect UUID and value pairs from all LCA input tables.

        Parameters
        ----------
        dcf : pyH2A.Discounted_Cash_Flow
            Discounted cash flow object containing the parsed input dictionary.
            All tables whose names start with ``"LCA"`` (case-insensitive) are
            read.

        Returns
        -------
        numpy.ndarray
            Two-column object array with ``[uuid, value]`` per row, one row
            per LCA component entry across all input tables. No sorting or
            sign adjustment is applied here.

        Raises
        ------
        ValueError
            Raised when no LCA tables are found or when a component is missing
            the required ``"UUID"`` or ``"Value"`` fields.

        Notes
        -----
        Array-like ``Value`` entries are reduced to a scalar by summation
        before being stored. Sign alignment with the original technosphere
        column is handled downstream in :meth:`build_scaling_vector`.
        '''
        lca_table_names = [table_name for table_name in dcf.inp if table_name.lower().startswith('lca')]
        if not lca_table_names: 
            raise ValueError("No LCA component tables found in input. Define at least one table whose name starts with 'LCA'.")

        # Resolve any path-based references (e.g. "A > B > Value") into numbers.
        [process_table(dcf.inp, lca_table_name, 'Value') for lca_table_name in lca_table_names]        
        rows = []
        for component_name, component_data in (
            item
            for lca_table_name in lca_table_names
            for item in dcf.inp[lca_table_name].items()
        ):
            uuid, raw_value = self.extract_component_uuid_and_value(component_name, component_data)
            scalar_value = float(np.sum(raw_value) if isinstance(raw_value, (np.ndarray, list, tuple)) else raw_value)
            rows.append((uuid, scalar_value))

        return np.array(rows, dtype=object)
        
    def extract_component_uuid_and_value(self, component_name, component_data):
        '''Extract required UUID and value fields from a component.

        Parameters
        ----------
        component_name : str
            Human-readable component name used in error messages.
        component_data : dict
            Component dictionary expected to contain 'UUID' and 'Value'.

        Returns
        -------
        tuple
            Pair ``(uuid, value)`` extracted from ``component_data``.

        Raises
        ------
        ValueError
            Raised when ``"UUID"`` or ``"Value"`` is missing.
        '''
        missing_fields = [
            key
            for key in ('UUID', 'Value')
            if key not in component_data
        ]
        if missing_fields:
            raise ValueError(
                f"LCA component '{component_name}' is missing required "
                f"field(s): {missing_fields}"
            )

        return component_data['UUID'], component_data['Value']
    
    def build_scaling_vector(self, dcf):
        '''Compute the scenario scaling vector using a Sherman-Morrison rank-1 update.

        Parameters
        ----------
        dcf : pyH2A.Discounted_Cash_Flow
            Discounted cash flow object whose LCA tables define the scenario
            component values.

        Raises
        ------
        ZeroDivisionError
            Raised when ``abs(1 + correction[0])`` is below ``self._SM_TOL``.
            No direct-solve fallback is applied.

        Notes
        -----
        Component values from ``dcf`` are aligned to the ``_A0_cache`` entry
        by UUID matching. Sign of each updated value is preserved from the
        original technosphere column (``_A0_cache`` values).

        The update formula is:
        ``x' = y - z * (y[0] / (1 + z[0]))``,
        where ``y`` is the base scaling vector, ``z = basis @ delta_coeff``
        is the correction vector, and ``delta_coeff`` is the element-wise
        difference between the scenario and original first-column values.
        Precomputed basis columns (``A^{-1} e_i``) avoid a full linear solve
        per Monte Carlo sample. The result is stored on ``self.scaling_vector``.
        '''
        A0_uuids  = LCA._A0_cache[self.matrix_folder][1]
        A0_values = LCA._A0_cache[self.matrix_folder][2]
        component_uuid_values = self.apply_component_updates(dcf)

        uuid_to_value = {str(uuid): float(val) for uuid, val in component_uuid_values}
        component_values = A0_values.copy()
        for i, uuid in enumerate(A0_uuids):
            if str(uuid) in uuid_to_value:
                component_values[i] = np.sign(A0_values[i]) * abs(uuid_to_value[str(uuid)])

        basis = LCA._component_basis_cache[self.matrix_folder]
        if basis is None:
            return None

        base_scaling_vector = LCA._base_scaling_vector_cache[self.matrix_folder]
        delta_coeff = component_values - A0_values
        correction = np.asarray(basis @ delta_coeff).reshape(-1)
        numerator = base_scaling_vector[0]
        denominator = 1.0 + correction[0]
        if abs(denominator) <= self._SM_TOL:
            raise ZeroDivisionError(
                "Sherman-Morrison denominator is too small; "
                "fallback direct solve is disabled."
            )

        self.scaling_vector = base_scaling_vector - correction * (numerator / denominator)
    
    def perform_lca(self):
        '''Perform the life cycle impact assessment calculation.

        Computes intermediate flows and final impact results using the intervention
        and characterization matrices. Results are stored in the class instance.

        Notes
        -----
        Stores results on ``self.lca_results`` as a dictionary mapping impact
        names to dictionaries with ``"value"`` and ``"unit"`` entries.
        '''

        matrix_b, matrix_c = LCA._matrix_bc_cache[self.matrix_folder]
        g = matrix_b @ self.scaling_vector
        h = matrix_c @ g

        # Store LCIA results on the instance for downstream use.
        self.lca_results = {}
        for i in LCA._impact_index_cache[self.matrix_folder]:
            self.lca_results[i.impact_name] = {
                'value': h[i.index],
                'unit': i.impact_unit
            }