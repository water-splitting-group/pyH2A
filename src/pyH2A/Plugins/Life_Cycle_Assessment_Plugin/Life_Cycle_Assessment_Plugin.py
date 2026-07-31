import shutil
import numpy as np

from pyH2A.Plugins.Life_Cycle_Assessment_Plugin.config import CONFIG
from pyH2A.Utilities.IO import input_resolver_function
from pyH2A.Utilities.input_modification import process_table
from pyH2A.Utilities.lca_utils import (
    atomic_savez,
    factorize,
    find_matrix_path,
    get_cache_paths,
    load_matrices_from_folder,
    matrix_of,
)
from pyH2A.Utilities.Unit_Handler.quantity import Quantity


class Life_Cycle_Assessment_Plugin:
    '''Performs life-cycle assessment to determine environmental impacts, from an
    openLCA matrix export.

    Runs as an ordinary Workflow plugin (see ``Config/Defaults_LCA.md`` and
    ``Config/Defaults_TEA_LCA.md``), rather than being unconditionally triggered
    from inside ``Discounted_Cash_Flow.__init__``. Whether LCA runs at all is
    controlled by which default file is merged in (``Defaults_TEA.md`` omits this
    plugin entirely), not by any conditional logic here.

    Parameters
    ----------
    Life Cycle Assessment > Matrix Folder > Value : str
        Path to the openLCA matrix export folder containing the technosphere
        (A), intervention (B), characterization (C), and demand (f) matrices.
        Tables in ``dcf.inp`` whose names start with ``"LCA"`` are used to update
        technosphere component values.

    Returns
    -------
    self.matrix_folder : str
        Path to the openLCA matrix export folder.
    self.component_values : numpy.ndarray
        Scenario-specific technosphere column values aligned to the cached
        ``A0_column`` ordering. Set by :meth:`apply_component_updates`.
    self.scaling_vector : numpy.ndarray
        Scenario-specific activity scaling vector. Set by :meth:`build_scaling_vector`.
    self.lca_results : dict
        LCIA results keyed by impact name. Each value is a
        :class:`~pyH2A.Utilities.Unit_Handler.quantity.Quantity` instance,
        inherently expressed per 1 unit of the functional flow (the demand
        vector's first entry is always solved as exactly ``1.0``, regardless
        of the real magnitude reported by openLCA), as a composite unit of
        ``<impact unit> / <functional unit>``. Set by :meth:`perform_lca`.
    dcf.lca : Life_Cycle_Assessment_Plugin
        This plugin instance is also assigned to ``dcf.lca``, preserved for
        backward compatibility with consumers that read ``dcf.lca.lca_results``
        directly (e.g. :mod:`pyH2A.Analysis.Monte_Carlo_Analysis`).

    Raises
    ------
    ValueError
        Raised when no LCA input tables are found in ``dcf.inp``, when a UUID
        present in the technosphere matrix is absent from the LCA input tables,
        when the declared Functional Unit's dimension does not match the LCA
        matrix export's functional-flow dimension (see
        :meth:`apply_component_updates`), or when that flow's unit is not
        recognized by the unit handler.
    ZeroDivisionError
        Raised when the Sherman-Morrison denominator is too small for a stable
        rank-1 update.

    Notes
    -----
    All caches are class-level and process-local. Disk artifacts are stored
    inside an ``Initial_Artifacts`` subdirectory of the matrix export folder,
    managed by :func:`pyH2A.Utilities.lca_utils.get_cache_paths`.
    '''

    _SM_TOL = 1e-12  # Tolerance for detecting numerical singularity in the Sherman-Morrison update denominator.
    # Class-level RAM cache. Not shared across multiprocessing workers; disk caching covers cross-process reuse.
    _cache = {
        'base_scaling_vector':    None,
        'A0_column':        None,
        'basis_component':  None,
        'matrix_B':         None,
        'matrix_C':         None,
        'impact_index':     None,
    }

    def __init__(self, dcf, print_info, run = True):
        self._set_up(dcf)
        if run:
            self._run(dcf)

    def _set_up(self, dcf):

        self.input_dict = {
            "Life Cycle Assessment": {
                "Matrix Folder": {
                    "Value": {
                        "type": {str,},
                    },
                    "optional": False,
                    "description": "Path to the openLCA matrix export folder."
                },
            },
        }

    def _run(self, dcf):
        '''Resolve the matrix folder and run the full LCA calculation workflow.

        Loads all matrices, prepares the class-level cache, cross-checks the
        declared Functional Unit against the matrix's own functional flow (see
        :meth:`apply_component_updates`), builds the scenario scaling vector via
        Sherman-Morrison update, and computes LCIA results.
        '''

        self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, 'Life_Cycle_Assessment_Plugin')

        self.matrix_folder = self.input_dict_resolved['Life Cycle Assessment']['Matrix Folder']['Value']

        self.initialize_all_artifacts()
        self.apply_component_updates(dcf)
        self.build_scaling_vector()
        self.perform_lca()

        dcf.lca = self  # preserve `dcf.lca` for existing consumers (Monte_Carlo_Analysis, tests)

    def initialize_all_artifacts(self):
        '''Prepare all matrix artifacts and component basis vectors.

        Fills the class-level RAM cache from disk if available. If any cache
        file is missing, computes all artifacts from scratch and writes them
        to disk atomically for reuse by future processes.

        Notes
        -----
        Populates ``_cache`` with keys ``base_scaling_vector``, ``A0_column``
        (nonzero first-column entries as UUIDs, values, and flow units),
        ``basis_component`` (precomputed ``A^{-1} e_i`` basis vectors),
        ``matrix_B`` and ``matrix_C`` (sparse originals), and ``impact_index``.
        Disk paths are resolved by :func:`~pyH2A.Utilities.lca_utils.get_cache_paths`,
        which also creates the ``Initial_Artifacts`` subdirectory on first call.
        Disk writes use :func:`~pyH2A.Utilities.lca_utils.atomic_savez` for atomic
        file replacement.
        '''

        # Try to load artifacts from RAM (process-local cache).
        if all(Life_Cycle_Assessment_Plugin._cache[k] is not None for k in Life_Cycle_Assessment_Plugin._cache):
            return

        # Not in RAM: try to load artifacts from disk cache
        paths = get_cache_paths(self.matrix_folder)

        try:

            self.load_all_from_disk_to_ram(paths)

        except FileNotFoundError:

            self.compute_all_artifacts_from_scratch()
            self.save_all_to_disk(paths)

    def load_all_from_disk_to_ram(self, paths: dict):
        '''Load all cached artifacts from disk into process-local RAM.

        Parameters
        ----------
        paths : dict
            Mapping from each ``_cache`` key to its ``.npz`` file path,
            as built in :meth:`initialize_all_artifacts`.

        Raises
        ------
        FileNotFoundError
            Propagated from :func:`numpy.load` or :func:`~pyH2A.Utilities.lca_utils.matrix_of`
            when a cache file is absent from disk.
        '''

        Life_Cycle_Assessment_Plugin._cache['base_scaling_vector']   = np.asarray(np.load(paths['base_scaling_vector'])['base_scaling_vector'])
        a0 = np.load(paths['A0_column'])
        Life_Cycle_Assessment_Plugin._cache['A0_column']       = (np.asarray(a0['uuids'], dtype=str), np.asarray(a0['values']), np.asarray(a0['units'], dtype=str))
        Life_Cycle_Assessment_Plugin._cache['basis_component'] = np.asarray(np.load(paths['basis_component'])['basis_component'])
        Life_Cycle_Assessment_Plugin._cache['matrix_B']        = matrix_of(str(paths['matrix_B']))
        Life_Cycle_Assessment_Plugin._cache['matrix_C']        = matrix_of(str(paths['matrix_C']))
        Life_Cycle_Assessment_Plugin._cache['impact_index']    = list(np.load(str(paths['impact_index']), allow_pickle=True)['impact_index'])

    def compute_all_artifacts_from_scratch(self):
        '''Compute all LCA artifacts from source matrices and populate the RAM cache.

        Loads matrices via :func:`~pyH2A.Utilities.lca_utils.load_matrices_from_folder`,
        factorizes the technosphere matrix, solves for the base scaling vector,
        precomputes Sherman-Morrison basis columns, and populates ``_cache``.

        Notes
        -----
        The demand vector's first entry (``f[0]``) is always solved as
        exactly ``1.0``, regardless of the real magnitude reported by
        openLCA, so that the resulting scaling vector - and every downstream
        LCIA result - is inherently expressed per 1 unit of the functional
        flow, without needing a separate normalization step or cached
        artifact for the real demand magnitude.
        '''
        (   impact_index,
            techno_index_uuid_values,
            A,
            B,
            C,
            f,
        ) = load_matrices_from_folder(self.matrix_folder)
        solver = factorize(A)
        f_vector = np.asarray(f, dtype=float).reshape(-1).copy()
        f_vector[0] = 1.0
        Life_Cycle_Assessment_Plugin._cache['base_scaling_vector'] = solver(f_vector)
         # Cache uuid, value, and flow unit columns of techno_index_uuid_values (UUID and unit columns are strings and cannot be serialised as numeric).
        Life_Cycle_Assessment_Plugin._cache['A0_column'] = (
            np.asarray(techno_index_uuid_values[:, 1], dtype=str),
            np.asarray(techno_index_uuid_values[:, 2], dtype=float),
            np.asarray(techno_index_uuid_values[:, 3], dtype=str),
        )
        # Compute and cache component basis vectors for the nonzero rows of the original first technosphere column.
        # Each column of the basis matrix is ``A^{-1} e_i`` for a changed row, enabling efficient Sherman-Morrison
        # updates without full solves for each Monte Carlo sample.
        nonzero_indices = np.asarray(techno_index_uuid_values[:, 0], dtype=int)
        n_rows = A.shape[0]
        n_cols = len(nonzero_indices)
        eye_subset = np.zeros((n_rows, n_cols), dtype=float)
        eye_subset[nonzero_indices, np.arange(n_cols)] = 1.0
        basis_component = np.asarray(solver(eye_subset))
        Life_Cycle_Assessment_Plugin._cache['basis_component'] = basis_component
        Life_Cycle_Assessment_Plugin._cache['impact_index'] = impact_index
        # Cache the original sparse B and C matrices for future reuse
        Life_Cycle_Assessment_Plugin._cache['matrix_B'] = B
        Life_Cycle_Assessment_Plugin._cache['matrix_C'] = C


    def save_all_to_disk(self, paths: dict):
        '''Save all artifacts from RAM to disk cache.

        Parameters
        ----------
        paths : dict
            Mapping from each ``_cache`` key to its ``.npz`` file path,
            as built in :meth:`initialize_all_artifacts`.

        Notes
        -----
        This method is intended for use after computing artifacts that are not
        present in RAM or on disk, to save them for future reuse. It writes the current RAM cache state to
        disk using atomic file replacement.
        In case of permission issues during atomic save, the cache will simply not be saved for future runs.
        This is a non-critical failure and may occur when base case is not run from run_pyH2A while Monte Carlo samples
        is set to very low values and multiple processes attempt to write the same cache file simultaneously.
        Log the error and continue without caching. All workers compute identical results, so the loser can
        safely ignore it.
        '''
        try:
            atomic_savez(paths['base_scaling_vector'],   base_scaling_vector=Life_Cycle_Assessment_Plugin._cache['base_scaling_vector'])
            atomic_savez(paths['A0_column'],       uuids=np.asarray(Life_Cycle_Assessment_Plugin._cache['A0_column'][0], dtype=str),
                                                   values=np.asarray(Life_Cycle_Assessment_Plugin._cache['A0_column'][1], dtype=float),
                                                   units=np.asarray(Life_Cycle_Assessment_Plugin._cache['A0_column'][2], dtype=str))
            atomic_savez(paths['basis_component'], basis_component=Life_Cycle_Assessment_Plugin._cache['basis_component'])
            atomic_savez(paths['impact_index'],    impact_index=np.array(Life_Cycle_Assessment_Plugin._cache['impact_index'], dtype=object))
            # Copy the original sparse B and C files to disk (Initial_Artifacts)
            mat_b = find_matrix_path(self.matrix_folder, 'B')
            mat_c = find_matrix_path(self.matrix_folder, 'C')
            shutil.copy2(mat_b, str(paths['matrix_B']))
            shutil.copy2(mat_c, str(paths['matrix_C']))
        except PermissionError:
            pass

    def apply_component_updates(self, dcf):
        '''Cross-check the declared Functional Unit, then resolve LCA input values
        and store them aligned to the technosphere column.

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
            least one table whose name starts with ``"LCA"`` (case-insensitive),
            and whose resolved ``functional_unit`` is cross-checked against the
            ``Unit`` declared for the functional-flow row in that table (see
            :func:`~pyH2A.Utilities.functional_unit.resolve_functional_unit`).

        Raises
        ------
        ValueError
            Raised when no LCA tables are found in ``dcf.inp``, when a UUID
            present in the cached technosphere column (including the
            functional-flow row) is absent from the input tables, or when the
            functional-flow row's declared dimension does not match
            ``dcf.functional_unit.dimension``.

        Notes
        -----
        The functional-flow row is ``A0_column`` index 0 (the technosphere
        matrix's own product-output entry, always present and always the
        lowest row index, see :meth:`perform_lca`). The Functional Unit
        cross-check compares this row's user-declared ``Unit`` (what the user
        is expected to set consistently with the ``# Functional Unit`` table)
        against ``dcf.functional_unit``, by physical dimension (e.g.
        ``'mass'``) rather than exact unit string, so a Functional Unit of
        ``kg`` is considered consistent with a functional-flow row declared in
        ``g`` (both ``'mass'``), but not with one declared in ``item`` or
        ``MJ``. This is deliberately checked against the input file's own
        declared unit rather than the raw openLCA matrix export's internal
        unit string for that row - the latter is already cross-checked for
        dimension compatibility against the declared unit for every row
        (including this one) in the component-matching loop below, via the
        ``Quantity`` unit conversion.

        Array-like ``Value`` entries are reduced to a scalar by summation.
        The ordering of ``self.component_values`` follows ``A0_column``, not
        the order of rows in the input tables. Each component's declared
        ``Unit`` is converted to the flow unit cached in ``A0_column`` via
        :class:`~pyH2A.Utilities.Unit_Handler.quantity.Quantity`.
        '''

        A0_uuids = Life_Cycle_Assessment_Plugin._cache['A0_column'][0]
        A0_values = Life_Cycle_Assessment_Plugin._cache['A0_column'][1]
        A0_units = Life_Cycle_Assessment_Plugin._cache['A0_column'][2]

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
            uuid, raw_value, unit = component_data['UUID'], component_data['Value'], component_data['Unit']
            scalar_value = float(np.sum(raw_value) if isinstance(raw_value, (np.ndarray, list, tuple)) else raw_value)
            rows.append((uuid, scalar_value, unit))

        if len(rows) > len(A0_uuids):
            raise ValueError(
                f"Expected {len(A0_uuids)} LCA components (one per nonzero column-0 entry), "
                f"but got {len(rows)}."
            )
        uuid_to_quantity = {str(uuid): Quantity(val, unit) for uuid, val, unit in rows}

        functional_flow_uuid = str(A0_uuids[0])
        if functional_flow_uuid not in uuid_to_quantity:
            raise ValueError(
                f"UUID '{functional_flow_uuid}' from the technosphere matrix's functional flow "
                "(A0_column row 0) is missing from the input LCA component tables. All UUIDs must "
                "be present for a complete scenario definition."
            )
        functional_flow_quantity = uuid_to_quantity[functional_flow_uuid]
        if functional_flow_quantity.dimension != dcf.functional_unit.dimension:
            raise ValueError(
                f"Functional Unit mismatch: the input file declares Functional Unit "
                f"'{dcf.functional_unit.unit}' (dimension '{dcf.functional_unit.dimension}'), but the "
                f"LCA component table declares the functional flow's Unit as "
                f"'{functional_flow_quantity.supplied_unit}' (dimension '{functional_flow_quantity.dimension}'). "
                f"Cost results (per {dcf.functional_unit.unit}) and LCA results (per "
                f"{functional_flow_quantity.supplied_unit}) would otherwise be silently expressed on two "
                "different physical bases. Update the '# Functional Unit' table's Unit, or the functional-flow "
                "row's Unit in the LCA component table, so both share the same dimension."
            )

        self.component_values = A0_values.copy()
        for i, uuid in enumerate(A0_uuids):
            if str(uuid) in uuid_to_quantity:
                # openLCA flow units sometimes carry a pluralization suffix (e.g. "Item(s)")
                # that the unit parser cannot handle, since parentheses are grouping syntax.
                target_unit = str(A0_units[i]).replace('(s)', '')
                converted_value = uuid_to_quantity[str(uuid)].unit[target_unit]
                self.component_values[i] = np.sign(A0_values[i]) * abs(converted_value)
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
        base_scaling_vector = Life_Cycle_Assessment_Plugin._cache['base_scaling_vector']
        # Difference between the scenario and original values for the nonzero entries of the first technosphere column, aligned by UUID matching.
        delta_coeff = self.component_values - Life_Cycle_Assessment_Plugin._cache['A0_column'][1]
        correction = np.asarray(Life_Cycle_Assessment_Plugin._cache['basis_component'] @ delta_coeff).reshape(-1)
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
        names to ``Quantity`` instances. No normalization is performed here:
        since :meth:`compute_all_artifacts_from_scratch` always solves with
        the demand vector's first entry forced to ``1.0``, ``h[i]`` is
        already expressed per 1 unit of the functional flow. Each result is
        expressed as a composite unit of ``<impact unit> / <functional unit>``
        (e.g. ``'kg / kg'``), where the functional unit's flow unit is read
        directly from the cached ``A0_column`` (technosphere row 0, the
        reference/functional flow, always present as the process's own
        product-output entry and always first in ``A0_column`` since it is
        the lowest possible row index).
        '''
        g = Life_Cycle_Assessment_Plugin._cache['matrix_B'] @ self.scaling_vector
        h = Life_Cycle_Assessment_Plugin._cache['matrix_C'] @ g

        # openLCA flow units sometimes carry a pluralization suffix (e.g. "Item(s)")
        # that the unit parser cannot handle, since parentheses are grouping syntax.
        functional_unit_unit = str(Life_Cycle_Assessment_Plugin._cache['A0_column'][2][0]).replace('(s)', '')

        self.lca_results = {}
        for i in Life_Cycle_Assessment_Plugin._cache['impact_index']:
            unit_map = CONFIG[i['impact_unit']]
            self.lca_results[i['impact_name']] = Quantity(
                h[i['index']],
                f"{unit_map['unit']} / {functional_unit_unit}"
            )
