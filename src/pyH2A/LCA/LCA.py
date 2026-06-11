import shutil
import numpy as np

from pyH2A import Discounted_Cash_Flow
from pyH2A.Utilities.input_modification import process_table
from pyH2A.Utilities.lca_utils import (
    ExportFolder,
    Matrix,
    atomic_savez,
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

    _SM_TOL = 1e-12  # Tolerance for detecting numerical singularity in the Sherman-Morrison update denominator.
    # Class-level RAM cache. Not shared across multiprocessing workers; disk caching covers cross-process reuse.
    _cache = {
        'scalingvector':    None,
        'a0_column':        None,
        'basis_component':  None,
        'matrix_b':         None,
        'matrix_c':         None,
        'impact_index':     None,
    }

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
        self.apply_component_updates(dcf)
        self.build_scaling_vector()
        self.perform_lca()

    @classmethod
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
        print("Loading matrices from folder:")
        loaded_folder = ExportFolder(matrix_folder)
        cls.export_folder = loaded_folder
        cls.A = loaded_folder.load(Matrix.A)
        # Load technosphere index: UUIDs and first-column values for nonzero entries, in row-index order.
        cls.techno_index_uuid = loaded_folder.tech_process_indices(matrix_a=cls.A)
        cls.B = loaded_folder.load(Matrix.B)
        cls.C = loaded_folder.load(Matrix.C)
        cls.f = loaded_folder.load(Matrix.f)
        if any(m is None for m in (cls.A, cls.B, cls.C, cls.f, cls.techno_index_uuid)):
            raise ValueError("One or more required matrices (A, B, C, f, index_A.csv) could not be loaded from the specified folder.")
        return cls.export_folder, cls.techno_index_uuid, cls.A, cls.B, cls.C, cls.f

    def initialize_all_artifacts(self):
        '''Prepare all matrix artifacts and component basis vectors.

        Fills the class-level RAM cache from disk if available, or computes
        and writes them if not. All artifacts are also written to disk atomically for
        reuse by worker processes and any future computations.

        Notes
        -----
        Populates ``LCA._cache`` with keys ``scalingvector``, ``a0_column``
        (nonzero first-column entries as UUIDs and values), ``basis_component``
        (precomputed ``A^{-1} e_i`` basis vectors), ``matrix_b`` and
        ``matrix_c`` (sparse originals), and ``impact_index``. Disk writes use
        :func:`~pyH2A.Utilities.lca_utils.atomic_savez` for atomic file replacement.
        '''

        # Try to load artifacts from RAM (process-local cache).
        if all(LCA._cache[k] is not None for k in LCA._cache):
            return

        # Not in RAM: try to load artifacts from disk cache
        cache_path = get_disk_cache_dir(self.matrix_folder)
        paths = {
            'scalingvector':   cache_path / "scalingvector.npz",
            'a0_column':       cache_path / "A0_column.npz",
            'basis_component': cache_path / "basis_component.npz",
            'matrix_b':        cache_path / "matrix_b.npz",
            'matrix_c':        cache_path / "matrix_c.npz",
            'impact_index':    cache_path / "impact_index.npz",
        }
        
        try:
                     
            self.load_all_from_disk_to_ram(paths)

        except FileNotFoundError:

            self.compute_all_artifacts_from_scratch()
            self.save_all_to_disk(paths)
            self.load_all_from_disk_to_ram(paths) 

    def load_all_from_disk_to_ram(self, paths: dict):
        '''Load all cached artifacts from disk into process-local RAM.

        Parameters
        ----------
        paths : dict
            Mapping from each ``LCA._cache`` key to its ``.npz`` file path,
            as built in :meth:`initialize_all_artifacts`.

        Raises
        ------
        FileNotFoundError
            Propagated from :func:`numpy.load` or :func:`~pyH2A.Utilities.lca_utils.matrix_of`
            when a cache file is absent from disk.
        '''
 
        LCA._cache['scalingvector']   = np.asarray(np.load(paths['scalingvector'])['base_scaling_vector'])
        a0 = np.load(paths['a0_column'])
        LCA._cache['a0_column']       = (np.asarray(a0['uuids'], dtype=str), np.asarray(a0['values']))
        LCA._cache['basis_component'] = np.asarray(np.load(paths['basis_component'])['basis_component'])
        LCA._cache['matrix_b']        = matrix_of(str(paths['matrix_b']))
        LCA._cache['matrix_c']        = matrix_of(str(paths['matrix_c']))
        LCA._cache['impact_index']    = list(np.load(str(paths['impact_index']), allow_pickle=True)['impact_index'])
    
    def compute_all_artifacts_from_scratch(self):
        '''Compute all LCA artifacts from source matrices and populate the RAM cache.

        Loads matrices from the export folder, factorizes the technosphere matrix,
        solves for the base scaling vector, precomputes Sherman-Morrison basis columns,
        and stores all results in ``LCA._cache``. Does not write anything to disk.
        '''
        (   LCA.export_folder,
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
        LCA._cache['scalingvector'] = _base_scaling_vector
         # Cache index and value columns of techno_index_uuid (UUID column is a string and cannot be serialised as numeric).
        LCA._cache['a0_column'] = (
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
        LCA._cache['basis_component'] = basis_component
        LCA._cache['impact_index'] = list(LCA.export_folder.impact_index()) 
        # Cache the original sparse B and C matrices for reuse by worker processes 
        LCA._cache['matrix_b'] = LCA.B
        LCA._cache['matrix_c'] = LCA.C 
        
    
    def save_all_to_disk(self, paths: dict):
        '''Save all artifacts from RAM to disk cache.

        Parameters
        ----------
        paths : dict
            Mapping from each ``LCA._cache`` key to its ``.npz`` file path,
            as built in :meth:`initialize_all_artifacts`.

        Notes
        -----
        This method is intended for use after computing artifacts that are not
        present in RAM or on disk, to save them for future reuse. It does not
        recompute any artifacts; it simply writes the current RAM cache state to
        disk using atomic file replacement.
        '''
        atomic_savez(paths['scalingvector'],   base_scaling_vector=LCA._cache['scalingvector'])
        atomic_savez(paths['a0_column'],       uuids=np.asarray(LCA._cache['a0_column'][0], dtype=str),
                                               values=np.asarray(LCA._cache['a0_column'][1], dtype=float))
        atomic_savez(paths['basis_component'], basis_component=LCA._cache['basis_component'])
        atomic_savez(paths['impact_index'],    impact_index=np.array(LCA._cache['impact_index'], dtype=object))
        # Copy the original sparse B and C files to disk (Initial_Artifacts)
        mat_b = find_matrix_path(self.matrix_folder, Matrix.B)
        mat_c = find_matrix_path(self.matrix_folder, Matrix.C)
        shutil.copy2(mat_b, str(paths['matrix_b']))
        shutil.copy2(mat_c, str(paths['matrix_c']))
        
    def apply_component_updates(self, dcf):
        '''Resolve LCA input values and store them aligned to the technosphere column.

        Reads all LCA input tables from ``dcf.inp``, resolves path-based
        references via :func:`process_table`, then matches each component to
        its position in the cached first technosphere column by UUID. The
        sign of each value is preserved from the original column. The result
        is stored on ``self.component_values`` for use in
        :meth:`build_scaling_vector`.

        Parameters
        ----------
        dcf : pyH2A.Discounted_Cash_Flow
            Discounted cash flow object whose input dictionary contains at
            least one table whose name starts with ``"LCA"`` (case-insensitive).

        Raises
        ------
        ValueError
            Raised when no LCA tables are found in ``dcf.inp``, or when a
            UUID present in the cached technosphere column is absent from the
            input tables (every nonzero entry must be explicitly specified).

        Notes
        -----
        Array-like ``Value`` entries are reduced to a scalar by summation.
        The ordering of ``self.component_values`` follows ``a0_column``, not
        the order of rows in the input tables.
        '''
        lca_table_names = [table_name for table_name in dcf.inp if table_name.lower().startswith('lca')]
        if not lca_table_names:
            raise ValueError("No LCA component tables found in input. Define at least one table whose name starts with 'LCA'.")

        # Resolve any path-based references (e.g. "A > B > Value") into numbers.
        for lca_table_name in lca_table_names:
            process_table(dcf.inp, lca_table_name, 'Value')
        rows = []
        for _, component_data in (
            item
            for lca_table_name in lca_table_names
            for item in dcf.inp[lca_table_name].items()
        ):
            uuid, raw_value = component_data['UUID'], component_data['Value']
            scalar_value = float(np.sum(raw_value) if isinstance(raw_value, (np.ndarray, list, tuple)) else raw_value)
            rows.append((uuid, scalar_value))

        A0_uuids = LCA._cache['a0_column'][0]
        A0_values = LCA._cache['a0_column'][1]
        uuid_to_value = {str(uuid): float(val) for uuid, val in rows}
        self.component_values = A0_values.copy()
        for i, uuid in enumerate(A0_uuids):
            if str(uuid) in uuid_to_value:
                self.component_values[i] = np.sign(A0_values[i]) * abs(uuid_to_value[str(uuid)])
            else:
                raise ValueError(
                    f"UUID '{uuid}' from the technosphere matrix is missing from the input "
                    "LCA component tables. All UUIDs must be present for a complete scenario definition."
                )

    def build_scaling_vector(self):
        '''Compute the scenario scaling vector using a Sherman-Morrison rank-1 update.

        Reads ``self.component_values`` (set by :meth:`apply_component_updates`)
        and applies the rank-1 correction to the base scaling vector.

        Raises
        ------
        ZeroDivisionError
            Raised when ``abs(1 + correction[0])`` is below ``self._SM_TOL``.
            No direct-solve fallback is applied.

        Notes
        -----
        The update formula is:
        ``x' = y - z * (y[0] / (1 + z[0]))``,
        where ``y`` is the base scaling vector, ``z = basis @ delta_coeff``
        is the correction vector, and ``delta_coeff`` is the element-wise
        difference between the scenario and original first-column values.
        Precomputed basis columns (``A^{-1} e_i``) avoid a full linear solve
        per Monte Carlo sample. The result is stored on ``self.scaling_vector``.
        '''
        base_scaling_vector = LCA._cache['scalingvector']
        # Difference between the scenario and original values for the nonzero entries of the first technosphere column, aligned by UUID matching.
        delta_coeff = self.component_values - LCA._cache['a0_column'][1]
        correction = np.asarray(LCA._cache['basis_component'] @ delta_coeff).reshape(-1)
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
        g = LCA._cache['matrix_b'] @ self.scaling_vector
        h = LCA._cache['matrix_c'] @ g

        self.lca_results = {}
        for i in LCA._cache['impact_index']:
            self.lca_results[i.impact_name] = {
                'value': h[i.index],
                'unit': i.impact_unit
            }
