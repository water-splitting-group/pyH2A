import numpy as np

from pyH2A.Plugins.Life_Cycle_Assessment_Plugin.config import CONFIG
from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.lca_utils import (
    atomic_savez,
    export_fingerprint,
    factorize,
    get_cache_paths,
    load_matrices_from_folder,
)
from pyH2A.Utilities.Unit_Handler.quantity import Quantity


def flow_unit(unit: str) -> str:
    '''Strip the pluralisation suffix openLCA attaches to some flow units.

    ``"Item(s)"`` becomes ``"Item"``; parentheses are grouping syntax to the
    unit parser and cannot be passed through.
    '''
    return unit.replace('(s)', '')


class Life_Cycle_Assessment_Plugin:
    '''Performs life-cycle assessment to determine environmental impacts, from an
    openLCA matrix export.

    Runs as an ordinary Workflow plugin (see ``Config/Defaults_LCA.md`` and
    ``Config/Defaults_TEA_LCA.md``). Whether LCA runs at all is
    controlled by which default file is merged in (``Defaults_TEA.md`` omits this
    plugin entirely), not by any conditional logic here.

    Parameters
    ----------
    Life Cycle Assessment > Matrix Folder > Value : str
        Path to the openLCA matrix export folder containing the technosphere
        (A), intervention (B), characterization (C), and demand (f) matrices.
    <...>LCA<...> >> Value : float, int, or ndarray
        Value of an individual LCA technosphere component entry, in a
        component-specific unit. Every table in ``dcf.inp`` whose name
        contains ``"LCA"`` is matched (``sum_all_tables()``-style wildcard
        table group, and every row within each matched table is resolved 
        regardless of its name.
    <...>LCA<...> >> UUID : str
        openLCA technosphere UUID identifying which technosphere column entry
        this component value updates.

    Returns
    -------
    Life Cycle Assessment > Results > Value : dict
        LCIA results keyed by impact name. Each value is a
        :class:`~pyH2A.Utilities.Unit_Handler.quantity.Quantity` instance,
        inherently expressed per 1 unit of the reference flow (the demand is
        always exactly one unit of it, regardless of the magnitude reported by
        openLCA), as a composite unit of
        ``<impact unit> / <reference flow unit>``. Computed by :meth:`perform_lca`.
    ['Life_Cycle_Assessment_Plugin'].lca_results : dict
        Identical to the value inserted into ``dcf.inp`` above, accessible
        directly off the plugin instance via
        ``dcf.plugs['Life_Cycle_Assessment_Plugin']``.
    self.matrix_folder : str
        Path to the openLCA matrix export folder.
    self.component_values : numpy.ndarray
        Scenario-specific technosphere column values aligned to the cached
        ``A0_column`` ordering. Set by :meth:`apply_component_updates`.
    self.scaling_vector : numpy.ndarray
        Scenario-specific activity scaling vector, for contribution analysis.
        Computed on demand; not used by :meth:`perform_lca`.

    Raises
    ------
    ValueError
        Raised when no LCA input tables are found in ``dcf.inp``, when a UUID
        present in the technosphere matrix is absent from the LCA input tables,
        when a resolved component value is negative, or when the export's
        reference flow unit differs from the declared Functional Unit (see
        :meth:`apply_component_updates`).
    KeyError
        Raised when an impact unit of the export has no entry in
        ``Life_Cycle_Assessment_Plugin/config.py``.
    ZeroDivisionError
        Raised when the Sherman-Morrison denominator is singular to working
        precision.

    Notes
    -----
    All caches are class-level and process-local. Disk artifacts are stored
    inside an ``Initial_Artifacts`` subdirectory of the matrix export folder,
    managed by :func:`pyH2A.Utilities.lca_utils.get_cache_paths`. Both the RAM
    and disk caches are keyed by
    :func:`~pyH2A.Utilities.lca_utils.export_fingerprint`, so switching matrix
    folder or replacing the export invalidates them.
    '''

    _SM_TOL = 1e-8  # Relative tolerance for cancellation in the Sherman-Morrison update denominator.
    # Class-level RAM cache. Not shared across multiprocessing workers; disk caching covers cross-process reuse.
    _cache = {
        'base_scaling_vector':    None,
        'A0_column':        None,
        'basis_component':  None,
        'h_base':           None,
        'h_basis':          None,
        'impact_index':     None,
    }
    # (matrix folder, export fingerprint) the RAM cache above was built from.
    _cache_key = None

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
            "<...>LCA<...>": {
                "<...>": {
                    "Value": {
                        "type": {int, float, np.ndarray},
                        "bounds": (None, None),
                    },
                    "Unit": {
                        "dimension": "flexible",
                    },
                    "UUID": {
                        "type": {str,},
                    },
                    "optional": True,
                    "description": "Individual LCA technosphere component entry: value (in a "
                                   "component-specific unit) and the corresponding openLCA "
                                   "technosphere UUID."
                },
            },
        }

        self.output_dict = {
            "Life Cycle Assessment": {
                "Results": {
                    "Value": {
                        "inserted_value": "lca_results",
                        "type": {dict,},
                        "dimension": "flexible",
                    },
                    "optional": False,
                    "description": "LCIA results keyed by impact name, each a Quantity expressed "
                                   "per 1 unit of the functional flow, as a composite unit of "
                                   "'<impact unit> / <functional unit>'."
                },
            },
        }

    def _run(self, dcf):
        '''Resolve the matrix folder and run the full LCA calculation workflow.

        Loads all matrices, prepares the class-level cache, cross-checks the
        declared Functional Unit against the matrix's own reference flow (see
        :meth:`apply_component_updates`), and computes LCIA results.
        '''

        self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, 'Life_Cycle_Assessment_Plugin')

        self.matrix_folder = self.input_dict_resolved['Life Cycle Assessment']['Matrix Folder']['Value']

        self.initialize_all_artifacts()
        self.apply_component_updates(dcf)
        self.perform_lca()

        output_inserter_function(self.output_dict, self, dcf, 'Life_Cycle_Assessment_Plugin')

    def initialize_all_artifacts(self):
        '''Prepare all cached artifacts for this matrix folder.

        Both caches are keyed by the export's fingerprint, so replacing the
        openLCA export or switching matrix folder invalidates them.

        Notes
        -----
        Populates ``_cache`` with keys ``base_scaling_vector``, ``A0_column``
        (nonzero first-column entries as UUIDs, values, and flow units),
        ``basis_component`` (precomputed ``A^{-1} e_i`` basis vectors),
        ``h_base`` and ``h_basis`` (the precomputed LCIA operator), and
        ``impact_index``. Disk paths are resolved by
        :func:`~pyH2A.Utilities.lca_utils.get_cache_paths`, which also creates the
        ``Initial_Artifacts`` subdirectory.

        Every artifact is written through
        :func:`~pyH2A.Utilities.lca_utils.atomic_savez` and the fingerprint is
        written last, so an interrupted write simply leaves no fingerprint and
        the next run recomputes.
        '''

        fingerprint = export_fingerprint(self.matrix_folder)
        if Life_Cycle_Assessment_Plugin._cache_key == (self.matrix_folder, fingerprint):
            return

        paths = get_cache_paths(self.matrix_folder)

        if paths['fingerprint'].exists() and paths['fingerprint'].read_text() == fingerprint:
            self.load_all_from_disk_to_ram(paths)
        else:
            self.compute_all_artifacts_from_scratch()
            self.save_all_to_disk(paths)
            paths['fingerprint'].write_text(fingerprint)

        Life_Cycle_Assessment_Plugin._cache_key = (self.matrix_folder, fingerprint)

    def load_all_from_disk_to_ram(self, paths: dict):
        '''Load all cached artifacts from disk into process-local RAM.

        Parameters
        ----------
        paths : dict
            Mapping from each ``_cache`` key to its ``.npz`` file path,
            as built in :meth:`initialize_all_artifacts`.
        '''

        Life_Cycle_Assessment_Plugin._cache['base_scaling_vector']   = np.asarray(np.load(paths['base_scaling_vector'])['base_scaling_vector'])
        a0 = np.load(paths['A0_column'])
        Life_Cycle_Assessment_Plugin._cache['A0_column']       = (np.asarray(a0['uuids'], dtype=str), np.asarray(a0['values']), np.asarray(a0['units'], dtype=str))
        Life_Cycle_Assessment_Plugin._cache['basis_component'] = np.asarray(np.load(paths['basis_component'])['basis_component'])
        Life_Cycle_Assessment_Plugin._cache['h_base']          = np.asarray(np.load(paths['h_base'])['h_base'])
        Life_Cycle_Assessment_Plugin._cache['h_basis']         = np.asarray(np.load(paths['h_basis'])['h_basis'])
        Life_Cycle_Assessment_Plugin._cache['impact_index']    = list(np.load(str(paths['impact_index']), allow_pickle=True)['impact_index'])

    def compute_all_artifacts_from_scratch(self):
        '''Compute all LCA artifacts from source matrices and populate the RAM cache.

        Loads matrices via :func:`~pyH2A.Utilities.lca_utils.load_matrices_from_folder`,
        factorizes the technosphere matrix, solves for the base scaling vector,
        precomputes Sherman-Morrison basis columns and the LCIA operator, and
        populates ``_cache``.

        Notes
        -----
        The demand is always exactly one unit of the reference flow, so the
        demand vector is built here rather than read from the export. The base
        scaling vector - and every downstream LCIA result - is therefore
        inherently expressed per 1 unit of the reference flow, without needing
        a separate normalization step.
        '''
        (   impact_index,
            techno_index_uuid_values,
            A,
            B,
            C,
        ) = load_matrices_from_folder(self.matrix_folder)
        solver = factorize(A)
        f_vector = np.zeros(A.shape[0])
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
        # Impacts are affine in the scenario's component values, so characterize the base scaling
        # vector and the basis columns once here. Each sample then costs one (impacts x components)
        # matrix-vector product instead of a pass over B and C. See ``perform_lca``.
        characterization = C @ B
        Life_Cycle_Assessment_Plugin._cache['h_base'] = np.asarray(
            characterization @ Life_Cycle_Assessment_Plugin._cache['base_scaling_vector']).reshape(-1)
        Life_Cycle_Assessment_Plugin._cache['h_basis'] = np.asarray(characterization @ basis_component)


    def save_all_to_disk(self, paths: dict):
        '''Save all artifacts from RAM to disk cache.

        Parameters
        ----------
        paths : dict
            Mapping from each ``_cache`` key to its ``.npz`` file path,
            as built in :meth:`initialize_all_artifacts`.

        Notes
        -----
        Writes the current RAM cache state to disk using atomic file
        replacement, for reuse by future processes. The caller writes the
        export fingerprint afterwards, so a write interrupted here leaves a
        cache that the next run ignores rather than trusts.
        '''
        atomic_savez(paths['base_scaling_vector'],   base_scaling_vector=Life_Cycle_Assessment_Plugin._cache['base_scaling_vector'])
        atomic_savez(paths['A0_column'],       uuids=np.asarray(Life_Cycle_Assessment_Plugin._cache['A0_column'][0], dtype=str),
                                               values=np.asarray(Life_Cycle_Assessment_Plugin._cache['A0_column'][1], dtype=float),
                                               units=np.asarray(Life_Cycle_Assessment_Plugin._cache['A0_column'][2], dtype=str))
        atomic_savez(paths['basis_component'], basis_component=Life_Cycle_Assessment_Plugin._cache['basis_component'])
        atomic_savez(paths['h_base'],          h_base=Life_Cycle_Assessment_Plugin._cache['h_base'])
        atomic_savez(paths['h_basis'],         h_basis=Life_Cycle_Assessment_Plugin._cache['h_basis'])
        atomic_savez(paths['impact_index'],    impact_index=np.array(Life_Cycle_Assessment_Plugin._cache['impact_index'], dtype=object))

    def apply_component_updates(self, dcf):
        '''Store resolved LCA input values aligned to the technosphere column,
        then cross-check the declared Functional Unit.

        Reads every ``<...>LCA<...>`` wildcard table already resolved into
        ``self.input_dict_resolved`` (path-based references such as
        ``"A > B > Value"`` are resolved by :func:`input_resolver_function`
        itself), then matches each component to its position in the cached
        first technosphere column by UUID. The sign of each value is
        preserved from the original column. The result is stored on
        ``self.component_values`` for use in :meth:`build_scaling_vector`.

        Parameters
        ----------
        dcf : pyH2A.Discounted_Cash_Flow
            Discounted cash flow object whose input dictionary contains at
            least one table whose name contains ``"LCA"``, and whose resolved
            ``functional_unit`` is cross-checked against the flow unit the
            export records for the reference flow (see
            :func:`~pyH2A.Utilities.functional_unit.resolve_functional_unit`).

        Raises
        ------
        ValueError
            Raised when no LCA tables are found in ``dcf.inp``, when a UUID
            present in the cached technosphere column is absent from the
            input tables, when a resolved component value is negative, or when
            the export's reference flow unit differs from
            ``dcf.functional_unit.unit``.

        Array-like ``Value`` entries are reduced to a scalar by summation.
        The ordering of ``self.component_values`` follows ``A0_column``, not
        the order of rows in the input tables. Each component's declared
        ``Unit`` is converted to the flow unit cached in ``A0_column`` via
        :class:`~pyH2A.Utilities.Unit_Handler.quantity.Quantity`.
        '''

        A0_uuids = Life_Cycle_Assessment_Plugin._cache['A0_column'][0]
        A0_values = Life_Cycle_Assessment_Plugin._cache['A0_column'][1]
        A0_units = Life_Cycle_Assessment_Plugin._cache['A0_column'][2]

        lca_table_names = [table_name for table_name in dcf.inp if 'LCA' in table_name]
        if not lca_table_names:
            raise ValueError("No LCA component tables found in input. Define at least one table whose name contains 'LCA'.")

        rows = []
        for lca_table_name in lca_table_names:
            for component_data in self.input_dict_resolved[lca_table_name].values():
                value_quantity = component_data['Value']
                scalar_quantity = Quantity(float(np.sum(value_quantity.base_value)), value_quantity.base_unit)
                rows.append((component_data['UUID'], scalar_quantity))

        if len(rows) > len(A0_uuids):
            raise ValueError(
                f"Expected {len(A0_uuids)} LCA components (one per nonzero column-0 entry), "
                f"but got {len(rows)}."
            )
        uuid_to_quantity = {str(uuid): quantity for uuid, quantity in rows}

        self.component_values = A0_values.copy()
        for i, uuid in enumerate(A0_uuids):
            if str(uuid) not in uuid_to_quantity:
                raise ValueError(
                    f"UUID '{uuid}' from the technosphere matrix is missing from the input "
                    "LCA component tables. All UUIDs must be present for a complete scenario definition."
                )
            converted_value = uuid_to_quantity[str(uuid)].unit[flow_unit(str(A0_units[i]))]
            if converted_value < 0:
                raise ValueError(
                    f"Negative value for LCA component '{uuid}'. Declare magnitudes only; "
                    "the sign is taken from the technosphere matrix."
                )
            self.component_values[i] = np.sign(A0_values[i]) * converted_value

        # Results are expressed per 1 unit of the reference flow in the export's own unit, so
        # that unit has to be the one cost results are expressed per. The reference flow is the
        # first row of the technosphere column.
        reference_flow_unit = flow_unit(str(A0_units[0]))
        if reference_flow_unit != dcf.functional_unit.unit:
            raise ValueError(
                f"Functional Unit mismatch: the input file declares Functional Unit "
                f"'{dcf.functional_unit.unit}', but the reference flow of the openLCA export is in "
                f"'{reference_flow_unit}'. LCA results are expressed per 1 unit of that flow, so cost "
                "and LCA results would otherwise be reported on two different bases."
            )

    def perform_lca(self):
        '''Perform the life cycle impact assessment calculation.

        Applies the Sherman-Morrison rank-1 update to the precomputed LCIA
        operator, which characterizes the base scaling vector and the basis
        columns once per export (see :meth:`compute_all_artifacts_from_scratch`).
        Impacts are therefore obtained without touching the intervention or
        characterization matrices.

        Raises
        ------
        ZeroDivisionError
            Raised when ``1 + correction[0]`` is lost to cancellation relative
            to ``correction[0]``, i.e. when the scenario's technosphere matrix
            is numerically singular. No direct-solve fallback is applied.

        Notes
        -----
        With ``delta`` the element-wise change in the first technosphere column,
        ``P`` the basis columns (``A^{-1} e_i``) and ``y`` the base scaling
        vector, the scenario scaling vector is
        ``x = y - (P @ delta) * (y[0] / (1 + (P @ delta)[0]))``.
        Since impacts are linear in ``x``, the same factor applies to the
        characterized quantities directly:
        ``h = h_base - (h_basis @ delta) * (y[0] / (1 + P[0] @ delta))``.
        ``P[0] @ delta`` is ``(P @ delta)[0]``, so the full correction vector is
        never formed here; :attr:`scaling_vector` builds it on demand.

        Stores results on ``self.lca_results`` as a dictionary mapping impact
        names to ``Quantity`` instances, each expressed as a composite unit of
        ``<impact unit> / <reference flow unit>`` (e.g. ``'kg / kg'``). No
        normalization is performed: the demand is one unit of the reference
        flow by construction.
        '''
        cache = Life_Cycle_Assessment_Plugin._cache
        # Difference between the scenario and original values for the nonzero entries of the
        # first technosphere column, aligned by UUID matching.
        self.delta = self.component_values - cache['A0_column'][1]
        correction_0 = cache['basis_component'][0] @ self.delta
        denominator = 1.0 + correction_0
        if abs(denominator) <= self._SM_TOL * (1.0 + abs(correction_0)):
            raise ZeroDivisionError(
                "Sherman-Morrison denominator is singular to working precision; "
                "fallback direct solve is disabled."
            )
        self.factor = cache['base_scaling_vector'][0] / denominator
        h = cache['h_base'] - (cache['h_basis'] @ self.delta) * self.factor

        reference_flow_unit = flow_unit(str(cache['A0_column'][2][0]))
        unknown_units = {i['impact_unit'] for i in cache['impact_index']} - CONFIG.keys()
        if unknown_units:
            raise KeyError(
                f"Impact units missing from Life_Cycle_Assessment_Plugin/config.py: "
                f"{sorted(unknown_units)}"
            )

        self.lca_results = {}
        for i in cache['impact_index']:
            self.lca_results[i['impact_name']] = Quantity(
                h[i['index']],
                f"{CONFIG[i['impact_unit']]['unit']} / {reference_flow_unit}"
            )

    @property
    def scaling_vector(self):
        '''Per-process activity levels for this scenario, for contribution analysis.

        Computed on demand from the cached basis columns; :meth:`perform_lca`
        does not need it and so does not pay for it per Monte Carlo sample.
        '''
        cache = Life_Cycle_Assessment_Plugin._cache
        correction = np.asarray(cache['basis_component'] @ self.delta).reshape(-1)
        return cache['base_scaling_vector'] - correction * self.factor
