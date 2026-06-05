'''Life cycle assessment workflow for openLCA matrix exports.

This module provides :class:`LCA`, which loads matrices exported from openLCA,
applies scenario-specific updates to the first technosphere column, computes
the activity scaling vector, and evaluates life cycle impact assessment (LCIA)
indicator results.

Scaling vectors are built via Sherman-Morrison rank-1 updates rather than
repeated full factorizations. The base scaling vector and component basis
vectors, ``A^{-1} e_i``, are cached so Monte Carlo workers can reconstruct
scenario-specific scaling vectors without re-factorizing the technosphere
matrix.

Notes
-----
Cache entries are split across three tiers:

* Base artifacts: process-local RAM and disk.
* Component basis vectors: process-local RAM and disk.
* Solver/factorization objects: process-local RAM only.
'''

import os
from functools import lru_cache
from pathlib import Path
import numpy as np

from pyH2A import Discounted_Cash_Flow
from pyH2A.Utilities.input_modification import process_table
from pyH2A.Utilities.lca_utils import (
    ExportFolder,
    Matrix,
    factorize,
    get_disk_cache_dir,
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
    export_folder : ExportFolder
        Loaded openLCA export folder. Stored as a class attribute.
    tech_index : numpy.ndarray
        Two-column object array containing technosphere row indices and process
        UUIDs for nonzero entries in the first technosphere column. Stored as a
        class attribute.
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
    Matrix and artifact caches are class-level and process-local unless noted
    otherwise. Disk artifacts are stored next to the matrix export through
    :func:`pyH2A.Utilities.lca_utils.get_disk_cache_dir`.

    The following private attributes are populated during initialization:

    matrix_folder : str
        Path to the openLCA matrix export folder, also used as the RAM cache key.
    _component_indices : numpy.ndarray
        Technosphere row indices updated by LCA input components.
    _component_values : numpy.ndarray
        Signed scenario component values aligned with ``_component_indices``.
    '''

    _SM_TOL = 1e-12
    _base_solver_cache = {}  # {matrix_key: (_base_scaling_vector, _A_col0)} cached in RAM
    _component_basis_cache = {}  # {matrix_key: basis_matrix} cached in RAM for component basis vectors
    _uuid_index_cache = {}  # {matrix_key: {uuid: tech_index}} cached in RAM
    _impact_index_cache = {}  # {matrix_key: [ImpactEntry, ...]} cached in RAM
    _matrix_bc_cache = {}  # {matrix_key: (B, C)} cached in RAM
      
    def __init__(self, matrix_folder: str, dcf: Discounted_Cash_Flow):
        '''Initialize and run the LCA calculation workflow.

        This constructor loads all matrices, prepares solver and cache state, updates
        the first column of the technosphere matrix with scenario-specific values,
        builds the scaling vector, and computes LCIA results.

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
        self.initialize_base_solver_and_artifacts()
        self.update_technosphere_column_with_components(dcf)
        self.build_scaling_vector()
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
        tech_index : numpy.ndarray
            Two-column array with ``[index, uuid]`` per row.
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

    def initialize_base_solver_and_artifacts(self):
        '''Prepare base matrix artifacts and component basis vectors.

        Initializes the matrix cache key, then fills the class-level RAM caches
        from disk if available, or computes and writes them if not. Solver and
        factorization objects are kept in RAM only; all other artifacts are also
        written to disk atomically for reuse by worker processes.

        Parameters
        ----------
        matrix_folder : str
            Path to the openLCA matrix export folder.

        Notes
        -----
        Populates ``self.matrix_folder`` and the class-level caches for the
        base scaling vector, original first A-column, B/C matrices, and component
        basis vectors. Disk writes use ``os.replace`` for atomic file replacement
        with no explicit locking.
        '''
        if not all(hasattr(LCA, attr) for attr in ('export_folder', 'techno_index_uuid', 'A', 'B', 'C', 'f')):
            (
                LCA.export_folder,
                LCA.techno_index_uuid,
                LCA.A,
                LCA.B,
                LCA.C,
                LCA.f,
            ) = self.load_matrices_from_folder(self.matrix_folder)

        LCA._matrix_bc_cache[self.matrix_folder] = (LCA.B, LCA.C)

        # Try to load solver and artifacts from RAM (process-local cache)
        base_cached = LCA._base_solver_cache.get(self.matrix_folder)
        component_basis_cached = LCA._component_basis_cache.get(self.matrix_folder)

        if (base_cached is not None) and (component_basis_cached is not None):
            return

        # Not in RAM: try to load artifacts from disk cache (solver is not stored on disk).
        cache_path = get_disk_cache_dir(self.matrix_folder)
        base_cache_path = cache_path / "scalingvector.npz"
        basis_cache_path = cache_path / "basis_component.npz"
        base_loaded = self.load_artifacts_from_disk_to_ram(base_cache_path)
        basis_loaded = self.load_basis_vectors_from_disk_to_ram(basis_cache_path)
        if base_loaded is True and basis_loaded is True:
            return
        # Not in RAM or disk: compute artifacts/compute basis vectors and cache to disk and RAM for future reuse.
        solver = factorize(LCA.A)  # Only stored in RAM
        f_vector = np.asarray(LCA.f).reshape(-1)
        _base_scaling_vector = solver.solve(f_vector)

        # Write only the artifacts to disk cache (not the solver)
        tmp_path = Path(str(base_cache_path) + f".{os.getpid()}.tmp.npz")
        np.savez(tmp_path, base_scaling_vector=_base_scaling_vector)
        os.replace(tmp_path, base_cache_path)

        # Store in-process artifacts in RAM for fast reuse.
        LCA._base_solver_cache[self.matrix_folder] = _base_scaling_vector

        nonzero_indices = np.asarray(LCA.techno_index_uuid[:, 0], dtype=int)
        n_rows = LCA.A.shape[0]
        n_cols = len(nonzero_indices)

        eye_subset = np.zeros((n_rows, n_cols), dtype=float)
        eye_subset[nonzero_indices, np.arange(n_cols)] = 1.0
        basis = np.asarray(solver.solve(eye_subset))
        tmp_path = Path(str(basis_cache_path) + f".{os.getpid()}.tmp.npz")
        np.savez(tmp_path, basis=basis)
        os.replace(tmp_path, basis_cache_path)
        LCA._component_basis_cache[self.matrix_folder] = basis

    def load_artifacts_from_disk_to_ram(self, base_cache_path) -> bool:
        '''Load base artifacts from disk into process-local RAM.

        The disk cache contains only artifacts (base scaling vector and first
        A-column). Solver/factorization objects are reconstructed in memory
        when needed and are not read from disk.

        Parameters
        ----------
        base_cache_path : pathlib.Path
            Path to the ``.npz`` file containing the base scaling vector and
            original first technosphere column.

        Returns
        -------
        bool
            ``True`` if cache data were loaded successfully, otherwise
            ``False``.

        Notes
        -----
        On success, ``LCA._base_solver_cache`` is updated for the current
        matrix cache key.
        '''

        if not base_cache_path.exists():
            return False

        try:
            with np.load(base_cache_path) as data:
                LCA._base_solver_cache[self.matrix_folder] = np.asarray(data['base_scaling_vector'])
            return True
        except Exception:
            return False

    def load_basis_vectors_from_disk_to_ram(self, basis_cache_path):
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
        On success, ``LCA._component_basis_cache`` is updated for the current
        matrix cache key. The basis matrix columns are ``A^{-1} e_i`` for the
        nonzero rows of the original first technosphere column.
        '''

        if not basis_cache_path.exists():
            return False

        try:
            with np.load(basis_cache_path) as data:
                LCA._component_basis_cache[self.matrix_folder] = np.asarray(data['basis'], dtype=float)
            return True
        except Exception:
            return False
        
    def _uuid_index_map(self) -> dict:
        '''Return the cached UUID-to-technosphere-index mapping.

        Returns
        -------
        dict
            Mapping from process UUID strings to technosphere row indices for
            the current matrix cache key.
        '''
        mapping = LCA._uuid_index_cache.get(self.matrix_folder)
        if mapping is None:
            mapping = {str(uuid): int(index) for index, uuid, _ in LCA.techno_index_uuid}
            LCA._uuid_index_cache[self.matrix_folder] = mapping
        return mapping
 
    def update_technosphere_column_with_components(self, dcf):

        '''Build an updated first technosphere column from LCA inputs.

        For each LCA component defined in dcf.inp with a UUID, this method finds
        the corresponding index in the technosphere matrix and sets that row in a
        copied first-column vector. If the value is an array/list (e.g., yearly H2
        production), the sum is used.

        Parameters
        ----------
        dcf : pyH2A.Discounted_Cash_Flow
            Discounted cash flow object containing one or more LCA component
            tables. Table names must start with ``"LCA"``.

        Returns
        -------
        None

        Raises
        ------
        ValueError
            Raised when no LCA tables are present, no components are resolved,
            a component is missing required fields, or a component UUID is not
            present in the technosphere index.

        Notes
        -----
        Updates ``self._component_indices`` and ``self._component_values`` in
        place. The first discovered component is treated as the positive
        reference contribution; subsequent components are signed negatively.
        '''

        lca_table_names = [table_name for table_name in dcf.inp if table_name.lower().startswith('lca')]
        if not lca_table_names: 
            raise ValueError("No LCA component tables found in input. Define at least one table whose name starts with 'LCA'.")

        # Resolve any path-based references (e.g. "A > B > Value") into numbers.
        [process_table(dcf.inp, lca_table_name, 'Value') for lca_table_name in lca_table_names]
        component_map = self.apply_component_updates(dcf, lca_table_names)

        if not component_map:
            raise ValueError("No LCA component indices found after processing input tables. Ensure at least one valid LCA component is defined.")

        self._component_indices = np.asarray(list(component_map.keys()), dtype=int)
        self._component_values = np.asarray(list(component_map.values()), dtype=float)
        sort_order = np.argsort(self._component_indices)
        self._component_indices = self._component_indices[sort_order]
        self._component_values = self._component_values[sort_order]
    
    def apply_component_updates(self, dcf, lca_table_names):
        '''Resolve LCA component rows and signed values.

        Parameters
        ----------
        dcf : pyH2A.Discounted_Cash_Flow
            Discounted cash flow object containing the parsed input dictionary.
        lca_table_names : list of str
            Names of LCA tables to read components from.

        Returns
        -------
        dict
            Mapping from technosphere row index to signed component value.

        Raises
        ------
        ValueError
            Raised when a component is missing required fields or when its UUID
            is absent from the technosphere index.

        Notes
        -----
        Array-like component values are summed before signing. The first
        component encountered is positive and all later components are negative.
        '''
        component_map = {}
        component_items = enumerate(
            item
            for lca_table_name in lca_table_names
            for item in dcf.inp[lca_table_name].items()
        )
        uuid_map = self._uuid_index_map()

        for component_position, component in component_items:
            component_name, component_data = component
            uuid, raw_value = self.extract_component_uuid_and_value(component_name, component_data)
            if uuid not in uuid_map:
                raise ValueError(
                    f"LCA component '{component_name}' has UUID '{uuid}' "
                    f"which was not found in the technosphere matrix index."
                )
            tech_index = uuid_map[uuid]
            scalar_value = float(np.sum(raw_value) if isinstance(raw_value, (np.ndarray, list, tuple)) else raw_value)
            signed_value = scalar_value if component_position == 0 else -scalar_value
            component_map[tech_index] = signed_value

        return component_map
        
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
    
    def build_scaling_vector(self):
        '''Compute the scenario scaling vector.

        The scaling vector is computed with a Sherman-Morrison rank-1 update.
        The scenario change is represented by the updated first technosphere
        column created in :meth:`update_technosphere_column_with_components`.

        Raises
        ------
        ZeroDivisionError
            Raised when ``abs(1 + z[0])`` is below ``self._SM_TOL``. In this
            implementation, no direct-solve fallback is used.

        Notes
        -----
        Stores the computed vector on ``self.scaling_vector``.

        The update uses
        ``x' = y - z * (y[0] / (1 + z[0]))``, where ``y`` is the base scaling
        vector and ``z = A^{-1} u`` is the correction vector. Basis matrix
        columns are ``A^{-1} e_i`` for changed rows, avoiding a full linear
        solve for each Monte Carlo sample.
        '''

        basis = LCA._component_basis_cache[self.matrix_folder]
        if basis is None:
            return None

        base_scaling_vector = LCA._base_solver_cache[self.matrix_folder]
        delta_coeff = self._component_values - np.array(LCA.techno_index_uuid[:, 2], dtype=float)
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

        matrix_b, matrix_c = self._matrix_bc_entries()
        g = matrix_b @ self.scaling_vector
        h = matrix_c @ g

        # Store LCIA results on the instance for downstream use.
        self.lca_results = {}
        for i in self._impact_index_entries():
            self.lca_results[i.impact_name] = {
                'value': h[i.index],
                'unit': i.impact_unit
            }

    def _impact_index_entries(self):
        '''Return cached impact-index entries.

        Returns
        -------
        list of ImpactEntry
            Ordered impact entries loaded from the current export folder.
        '''
        entries = LCA._impact_index_cache.get(self.matrix_folder)
        if entries is None:
            entries = list(LCA.export_folder.impact_index())
            LCA._impact_index_cache[self.matrix_folder] = entries
        return entries

    def _matrix_bc_entries(self):
        '''Return cached intervention and characterization matrices.

        Returns
        -------
        tuple
            Pair ``(B, C)`` containing the intervention and characterization
            matrices for the current matrix cache key.
        '''
        entries = LCA._matrix_bc_cache.get(self.matrix_folder)
        if entries is None:
            entries = (LCA.B, LCA.C)
            LCA._matrix_bc_cache[self.matrix_folder] = entries
        return entries