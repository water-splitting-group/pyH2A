import numpy as np

from pyH2A.Config.OpenLCA_config import openLCA_to_pyH2A_unit
from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.lca_utilities import (
    dense_column,
    load_matrices_from_folder,
    atomic_savez,
    export_fingerprint,
    get_cache_paths,
    factorize,
)
from pyH2A.Utilities.Unit_Handler.quantity import Quantity


class LCA_Plugin:
    '''Performs life-cycle assessment to determine environmental impacts, from an
    openLCA matrix export.

    Runs as an ordinary Workflow plugin (see ``Config/Defaults_LCA.md`` and
    ``Config/Defaults_TEA_LCA.md``). Whether LCA runs at all is
    controlled by which default file is merged in (``Defaults_TEA.md`` omits this
    plugin entirely).

    Parameters
    ----------
    Technical Operating Parameters and Specifications > Total output at gate > Value : float or int
        Cumulated output of product at the gate over the plant lifetime, in the
        functional unit of the product. Computed by
        :class:`~pyH2A.Plugins.Production_Plugin.Production_Plugin`, and used as
        the amount of the reference flow in the technosphere column.
    Life Cycle Assessment > Matrix Folder > Value : str
        Path to the openLCA matrix export folder containing the technosphere
        (A), intervention (B) and characterization (C) matrices.
    Life Cycle Assessment > UUID of product > Value : str
        openLCA technosphere UUID of the product flow, i.e. the entry of the
        technosphere column that ``Total output at gate`` supplies the value of.
    <...> LCA <...> >> Value : float, int, or ndarray
        Value of an individual LCA technosphere component entry, in a
        component-specific unit. Every table in ``dcf.inp`` whose name
        contains ``"LCA"`` is matched (``sum_all_tables()``-style wildcard
        table group, and every row within each matched table is resolved
        regardless of its name.
    <...> LCA <...> >> UUID : str
        openLCA technosphere UUID identifying which technosphere column entry
        this component value updates.

    Returns
    -------
    Dependent Variables > <impact name> > Value : Quantity
        One row per impact category of the export, keyed by the verbatim impact
        name of ``index_C.csv``. Each value is a
        :class:`~pyH2A.Utilities.Unit_Handler.quantity.Quantity` instance,
        inherently expressed per 1 unit of the reference flow (the demand is
        always exactly one unit of it, regardless of the magnitude reported by
        openLCA), as a composite unit of
        ``<impact unit> / <functional unit>``. Computed by :meth:`perform_lca`.
    ['LCA_Plugin'].lca_results : dict
        The same results as a single dictionary keyed by impact name, accessible
        directly off the plugin instance via
        ``dcf.plugs['LCA_Plugin']``.
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
        Raised when the UUIDs of the LCA input tables and of the product do not
        match the nonzero entries of the technosphere column exactly, when a UUID
        is declared more than once, when ``UUID of product`` is not the export's
        reference flow, when a resolved component value is negative, when a
        declared Unit cannot be converted into the flow unit the export records
        for that entry, when the declared Functional Unit carries no reference, or
        when an impact unit of the export is neither a pyH2A unit nor mapped in
        ``Config/OpenLCA_config.py``.
    ZeroDivisionError
        Raised when the Sherman-Morrison denominator is singular to working
        precision.

    Notes
    -----
    Every amount in the technosphere column is a plant-lifetime total, because
    ``Total output at gate`` is; a component supplied per year, or an installed
    stock supplied as a per-year array (which is summed), is out by the number of
    operating years. Only entries that are already nonzero in the export's first
    technosphere column can be given a scenario value, so a process a scenario may
    need has to be present in the export, with a placeholder amount if necessary.

    All caches are class-level and process-local. Disk artifacts are stored
    inside an ``Initial_Artifacts`` subdirectory of the matrix export folder,
    managed by :func:`pyH2A.Utilities.lca_utilities.get_cache_paths`. Both the RAM
    and disk caches are keyed by
    :func:`~pyH2A.Utilities.lca_utilities.export_fingerprint`, so switching matrix
    folder or replacing the export invalidates them.
    '''

    _SHERMAN_MORRISON_TOLERANCE = 1e-8  # Relative tolerance for cancellation in the Sherman-Morrison update denominator.
    # Class-level RAM cache. Not shared across multiprocessing workers; disk caching covers cross-process reuse.
    _cache = {
        'base_scaling_vector':  None,
        'A0_column':            None,
        'basis_component':      None,
        'h_base':               None,
        'h_basis':              None,
        'impact_index':         None,
    }
    # (matrix folder, export fingerprint) the RAM cache above was built from.
    _cache_key = None

    def __init__(self, dcf, print_info, run = True):
        self._set_up(dcf)
        if run:
            self._run(dcf)

    def _set_up(self, dcf):

        self.functional_unit = dcf.functional_unit

        self.input_dict = {
            "Technical Operating Parameters and Specifications": {
                "Total output at gate": {
                    "Value": {
                        "type": {float, int},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": self.functional_unit.dimension
                    },
                    "optional": False,
                    "description": "Total output of product at the gate (sum of yearly outputs), in functional unit of product."
                },
            },
            "Life Cycle Assessment": {
                "Matrix Folder": {
                    "Value": {
                        "type": {str,},
                    },
                    "optional": False,
                    "description": "Path to the openLCA matrix export folder."
                },
                "UUID of product": {
                    "Value": {
                        "type": {str,},
                    },
                    "optional": False,
                    "description": "UUID of the product flow in the openLCA export."
                }
            },
            "<...> LCA <...>": {
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
                                   "technosphere UUID. Arrays are summed and then used for the"
                                   "calculation."
                },
            },
        }

        self.output_dict = {
            'Dependent Variables': {
                '<...>': {
                    'Value': {
                        'inserted_value': 'lca_results',
                        'type': {int, float,},
                        'dimension': "flexible",
                    },
                    'optional': False,
                    'description': "Life-cycle impact assessment results, with the middle key being the impact name"
                }
            }
        }

    def _run(self, dcf):
        '''Resolve the matrix folder and run the full LCA calculation workflow.

        Loads all matrices, prepares the class-level cache, cross-checks the
        declared Functional Unit against the matrix's own reference flow (see
        :meth:`apply_component_updates`), and computes LCIA results.
        ''' 

        self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, 'LCA_Plugin')

        self.matrix_folder = self.input_dict_resolved['Life Cycle Assessment']['Matrix Folder']['Value']

        self.initialize_all_artifacts()
        self.apply_component_updates()
        self.perform_lca()

        output_inserter_function(self.output_dict, self, dcf, 'LCA_Plugin')

    def initialize_all_artifacts(self):
        '''Prepare all cached artifacts for this matrix folder.

        Both caches are keyed by the export's fingerprint, so replacing the
        openLCA export or switching matrix folder invalidates them.

        Notes
        -----
        Populates ``_cache`` with keys ``base_scaling_vector``, ``A0_column``
        (nonzero first-column entries as UUIDs, values, and flow units),
        ``basis_component`` (precomputed ``A^{-1} e_i`` basis vectors),
        ``h_base`` and ``h_basis`` (the precomputed LCIA operator, whose column 0
        also carries the restatement of the foreground process's own elementary
        flows), and ``impact_index``. A cache directory is only reused when the
        fingerprint matches *and* every artifact file is present, so an incomplete
        one - from an older pyH2A, or partially deleted - is rebuilt rather than
        loaded from. Disk paths are resolved by
        :func:`~pyH2A.Utilities.lca_utilities.get_cache_paths`, which also creates the
        ``Initial_Artifacts`` subdirectory.

        Every artifact is written through
        :func:`~pyH2A.Utilities.lca_utilities.atomic_savez` and the fingerprint is
        written last, so an interrupted write simply leaves no fingerprint and
        the next run recomputes.
        '''

        # Get the export fingerprint (file names, sizes and modification times of the source matrices) 
        fingerprint = export_fingerprint(self.matrix_folder)

        # If the RAM cache is already built for this matrix folder and fingerprint, do nothing.
        # (cache is already correctly populated for this matrix folder) 
        if LCA_Plugin._cache_key == (self.matrix_folder, fingerprint):
            return

        # Get the disk paths for all artifacts, creating the Initial_Artifacts subdirectory if needed.
        paths = get_cache_paths(self.matrix_folder)

        # If the fingerprint file matches and every artifact is present, load them into RAM.
        # The completeness check also covers a cache directory written by an older pyH2A that
        # did not yet produce every artifact, and one a user has partially deleted.
        if (paths['fingerprint'].exists() and paths['fingerprint'].read_text() == fingerprint
                and all(path.exists() for path in paths.values())):
            self.load_all_from_disk_to_ram(paths)

        # If the fingerprint file is missing or does not match (or files are missing), 
        # compute all artifacts from scratch and save them to disk.
        else:
            self.compute_all_artifacts_from_scratch()
            self.save_all_to_disk(paths)
            paths['fingerprint'].write_text(fingerprint)

        # Update the RAM cache key to reflect the current matrix folder and fingerprint.
        LCA_Plugin._cache_key = (self.matrix_folder, fingerprint)

    def load_all_from_disk_to_ram(self, paths: dict):
        '''Load all cached artifacts from disk into process-local RAM.

        Parameters
        ----------
        paths : dict
            Mapping from each ``_cache`` key to its ``.npz`` file path,
            as built in :meth:`initialize_all_artifacts`.
        '''

        a0 = np.load(paths['A0_column'])

        LCA_Plugin._cache['A0_column']              = (np.asarray(a0['uuids'], dtype=str), 
                                                       np.asarray(a0['values']), 
                                                       np.asarray(a0['units'], dtype=str))
        LCA_Plugin._cache['base_scaling_vector']    = np.asarray(np.load(paths['base_scaling_vector'])['base_scaling_vector'])
        LCA_Plugin._cache['basis_component']        = np.asarray(np.load(paths['basis_component'])['basis_component'])
        LCA_Plugin._cache['h_base']                 = np.asarray(np.load(paths['h_base'])['h_base'])
        LCA_Plugin._cache['h_basis']                = np.asarray(np.load(paths['h_basis'])['h_basis'])
        LCA_Plugin._cache['impact_index']           = list(np.load(str(paths['impact_index']), allow_pickle=True)['impact_index'])

    def compute_all_artifacts_from_scratch(self):
        '''Compute all LCA artifacts from source matrices and populate the RAM cache.

        Loads matrices via :func:`~pyH2A.Utilities.lca_utilities.load_matrices_from_folder`,
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

        # Load matrices from the export folder 
        impact_index, techno_index_uuid_values, A, B, C = load_matrices_from_folder(self.matrix_folder)

        # Factorize the technosphere matrix and obtain the callable solver 
        solver = factorize(A)

        # Initialize the demand vector to 1 unit of the reference flow (first row of the technosphere column)
        f_vector = np.zeros(A.shape[0])
        f_vector[0] = 1.0

        # Compute and cache component basis vectors for the nonzero rows of the original first technosphere column.
        # Each column of the basis matrix is ``A^{-1} e_i`` for a changed row, enabling efficient Sherman-Morrison
        # updates without full solves for each Monte Carlo sample.
        nonzero_indices = np.asarray(techno_index_uuid_values[:, 0], dtype=int)
        n_rows = A.shape[0]
        n_cols = len(nonzero_indices)
        eye_subset = np.zeros((n_rows, n_cols), dtype=float)
        eye_subset[nonzero_indices, np.arange(n_cols)] = 1.0
        basis_component = np.asarray(solver(eye_subset))

        # Impacts are affine in the scenario's component values, so characterize the base scaling
        # vector and the basis columns once here. Each sample then costs one (impacts x components)
        # matrix-vector product instead of a pass over B and C. See ``perform_lca``.
        characterization = C @ B

        # Restatement of the foreground process's own elementary flows, folded into the same
        # operator. Column 0 of B is declared for the reference amount ``alpha`` the export was
        # written at, so a scenario reference amount of ``alpha + delta[0]`` restates it by
        # ``r = 1 + delta[0] / alpha``, and the characterized correction
        # ``h_direct * (r - 1) * factor`` is ``(h_direct / alpha) * delta[0] * factor`` - a
        # column-0 term of the very ``(h_basis @ delta) * factor`` product ``perform_lca``
        # already forms. Subtracting it here therefore leaves the per-sample cost untouched.
        # Column 0 is the reference flow because ``tech_process_indices`` orders by row index
        # and requires row 0 to be the product.
        h_basis = np.asarray(characterization @ basis_component)
        h_basis[:, 0] -= dense_column(characterization, 0) / float(techno_index_uuid_values[0][2])

        # Cache all artifacts in RAM for this matrix folder and fingerprint
        LCA_Plugin._cache['base_scaling_vector'] = solver(f_vector)
        LCA_Plugin._cache['A0_column'] = (np.asarray(techno_index_uuid_values[:,1], dtype=str),
                                          np.asarray(techno_index_uuid_values[:,2], dtype=float),
                                          np.asarray(techno_index_uuid_values[:,3], dtype=str),)
        LCA_Plugin._cache['basis_component'] = basis_component
        LCA_Plugin._cache['impact_index'] = impact_index
        LCA_Plugin._cache['h_base'] = np.asarray(characterization @ LCA_Plugin._cache['base_scaling_vector']).reshape(-1)
        LCA_Plugin._cache['h_basis'] = h_basis

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

        atomic_savez(paths['base_scaling_vector'],
                     base_scaling_vector = LCA_Plugin._cache['base_scaling_vector'])
        atomic_savez(paths['A0_column'],
                     uuids = np.asarray(LCA_Plugin._cache['A0_column'][0], dtype=str),
                     values = np.asarray(LCA_Plugin._cache['A0_column'][1], dtype=float),
                     units = np.asarray(LCA_Plugin._cache['A0_column'][2], dtype=str))
        atomic_savez(paths['basis_component'], 
                     basis_component=LCA_Plugin._cache['basis_component'])
        atomic_savez(paths['h_base'],          
                     h_base=LCA_Plugin._cache['h_base'])
        atomic_savez(paths['h_basis'],
                     h_basis=LCA_Plugin._cache['h_basis'])
        atomic_savez(paths['impact_index'],
                     impact_index=np.array(LCA_Plugin._cache['impact_index'], dtype=object))

    def apply_component_updates(self):
        '''Store resolved LCA input values aligned to the technosphere column.

        The product entry is taken from ``Total output at gate`` under the UUID
        declared as ``UUID of product``; every other entry comes from a
        ``<...>LCA<...>`` wildcard table already resolved into
        ``self.input_dict_resolved`` (path-based references such as
        ``"A > B > Value"`` are resolved by :func:`input_resolver_function`
        itself). Each component is then matched to its position in the cached
        first technosphere column by UUID. The sign of each value is
        preserved from the original column. The result is stored on
        ``self.component_values`` for use in :meth:`perform_lca`.

        Raises
        ------
        ValueError
            Raised when ``UUID of product`` is not the export's reference flow
            (row 0 of the technosphere column), when a UUID is declared by more
            than one row, when the set of UUIDs collected here does not match the
            set of nonzero entries of the cached technosphere column exactly (in
            either direction), when a resolved component value is negative, or
            when a declared ``Unit`` cannot be converted into the flow unit the
            export records for that entry - which is also what cross-checks the
            declared Functional Unit, since the product's value is supplied in it.

        Notes
        -----
        Array-like ``Value`` entries are reduced to a scalar by summation.
        The ordering of ``self.component_values`` follows ``A0_column``, not
        the order of rows in the input tables. Each component's declared
        ``Unit`` is converted to the flow unit cached in ``A0_column`` via
        :class:`~pyH2A.Utilities.Unit_Handler.quantity.Quantity`.
        '''

        A0_uuids    = LCA_Plugin._cache['A0_column'][0]
        A0_values   = LCA_Plugin._cache['A0_column'][1]
        A0_units    = LCA_Plugin._cache['A0_column'][2]

        self.total_output = self.input_dict_resolved['Technical Operating Parameters and Specifications']['Total output at gate']['Value']
        uuid_of_product = self.input_dict_resolved['Life Cycle Assessment']['UUID of product']['Value']

        # The demand vector, the rank-1 update and the product flow unit all address the
        # reference flow by position (row 0), so the declared product has to be that row and
        # not merely one of the column's entries. Without this, a product swapped with a
        # component of the same dimension passes every remaining check - the UUID sets still
        # match, the units still convert - and silently answers a different question.
        if str(A0_uuids[0]) != uuid_of_product:
            raise ValueError(
                f"'UUID of product' ({uuid_of_product}) is not the reference flow of the export: "
                f"row 0 of the technosphere column is '{A0_uuids[0]}'.")

        # Initialize uuid_to_quantity with the product's UUID and total output at gate
        uuid_to_quantity = {uuid_of_product: self.total_output}

        # Find all tables in the input dictionary whose name contains "LCA" and extract their component data.
        lca_table_names = [table_name for table_name in self.input_dict_resolved if 'LCA' in table_name]

        for lca_table_name in lca_table_names:
            for component_data in self.input_dict_resolved[lca_table_name].values():
                value_quantity = component_data['Value']
                scalar_quantity = Quantity(float(np.sum(value_quantity.base_value)), value_quantity.base_unit)

                # Map the component's UUID to its resolved scalar quantity. Every technosphere
                # entry is declared exactly once, so a repeat is rejected rather than allowed to
                # overwrite the earlier row - the set comparison below cannot see it, because a
                # duplicate paired with a missing component leaves both sets the same size.
                if component_data['UUID'] in uuid_to_quantity:
                    raise ValueError(
                        f"LCA component UUID '{component_data['UUID']}' is declared more than "
                        "once. Declare each technosphere entry exactly once, with its total "
                        "amount, rather than spread over several rows.")

                uuid_to_quantity[component_data['UUID']] = scalar_quantity

        # Check that every UUID in the cached A0 column has a corresponding entry in the input tables
        # and that no additional UUIDs are present in the input tables that are not in the cached A0 column.
        if len(A0_uuids) != len(uuid_to_quantity) or set(A0_uuids) != set(uuid_to_quantity):
            raise ValueError("Mismatch between A0 column UUIDs and input LCA component UUIDs.")

        self.component_values = np.zeros_like(A0_values)

        # Populate self.component_values with the resolved values
        for index, uuid_from_A0 in enumerate(A0_uuids):
            # Get the unit from the A0 column (removing "(s)" is present)
            # Retrieve the corresponding quantity from the input tables using the UUID
            # Convert the value to the unit from the A0 column
            unit_from_A0 = openLCA_to_pyH2A_unit(A0_units[index])
            value = uuid_to_quantity[str(uuid_from_A0)]
            converted_value = value.unit[unit_from_A0]   

            if converted_value < 0:
                raise ValueError(
                    f"Negative value for LCA component '{uuid_from_A0}'. Declare magnitudes only; "
                    "the sign is taken from the technosphere matrix.")

            # Multiply by the sign of the original A0 value to preserve the correct sign in the scenario
            self.component_values[index] = np.sign(A0_values[index]) * converted_value

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
        ValueError
            Raised when an impact unit of the export is neither a pyH2A unit nor
            mapped in ``Config/OpenLCA_config.py``, in which case the unit parser
            names the offending token.

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

        The foreground process's own elementary flows are restated for the
        scenario's reference amount as part of the same product. Column 0 of ``B``
        is declared for the amount ``alpha`` the export was written at, so with
        ``r = 1 + delta[0] / alpha`` the scenario intervention matrix is
        ``B + (r - 1) B[:, 0] e0^T``; ``e0^T x`` is ``x[0]``, which the rank-1
        update makes exactly ``y[0] / (1 + correction[0])``, i.e. ``factor``. The
        added term ``h_direct * (r - 1) * factor`` is therefore
        ``(h_direct / alpha) * delta[0] * factor``, a column-0 term of
        ``(h_basis @ delta) * factor``, and
        :meth:`compute_all_artifacts_from_scratch` subtracts ``h_direct / alpha``
        from column 0 of ``h_basis`` once per export rather than adding a term per
        sample. This is what makes the result independent of the size the openLCA
        product system happened to be defined at: without it, direct foreground
        emissions keep the amount they had at the export's own size while being
        attributed to ``r`` times as much product.

        Stores results on ``self.lca_results`` as a dictionary mapping impact
        names to ``Quantity`` instances. Impacts are computed in the export's own
        reference flow unit and then restated per declared Functional Unit, as a
        composite unit of ``<impact unit> / <functional unit>``
        (e.g. ``'kg[$CO_{2}$-Eq] / kg[H2]'``). No normalization is performed: the
        demand is one unit of the reference flow by construction.

        Because the reference amount is ``Total output at gate``, every other
        amount in the rewritten column has to be stated on that same basis, as a
        plant-lifetime total. Array values are reduced by summation, which is what
        an operating flow reported year by year needs and what an installed stock
        repeated year by year does not.
        '''
        cache = LCA_Plugin._cache

        # Difference between the scenario and original values for the nonzero entries of the
        # first technosphere column, aligned by UUID matching.
        self.delta = self.component_values - cache['A0_column'][1]
        correction_0 = cache['basis_component'][0] @ self.delta
        denominator = 1.0 + correction_0

        # If the denominator is too small relative to the magnitude of the correction, 
        # it indicates that the Sherman-Morrison update is numerically unstable. 
        # In this case, raise a ZeroDivisionError to indicate that the update cannot be performed accurately.
        if abs(denominator) <= self._SHERMAN_MORRISON_TOLERANCE * (1.0 + abs(correction_0)):
            raise ZeroDivisionError(
                "Sherman-Morrison denominator is singular to working precision; "
                "fallback direct solve is disabled.")
        
        self.factor = cache['base_scaling_vector'][0] / denominator

        # ``h_basis`` already carries the restatement of the foreground process's own elementary
        # flows in its column 0, folded in when the artifacts were built, so this single product
        # covers both the technosphere and the direct exchanges. See the Notes below.
        h = cache['h_base'] - (cache['h_basis'] @ self.delta) * self.factor

        # Retrieving unit of product flow in OpenLCA matrix
        product_flow_unit = openLCA_to_pyH2A_unit(cache['A0_column'][2][0])

        self.lca_results = {}

        # Iterating over each impact index to create the corresponding Quantity
        for index in cache['impact_index']:
            impact_unit, impact_reference = openLCA_to_pyH2A_unit(index['impact_unit'], return_reference = True)

            # Two different units: OpenLCA internal product flow unit and pyH2A functional unit 
            # and full reference based on functional unit reference
            product_flow_impact_unit = f"{impact_unit} / {product_flow_unit}"
            functional_unit_impact_unit = f"{impact_unit} / {self.functional_unit.unit_no_reference}"
            full_reference = [impact_reference, *self.functional_unit.reference]

            # Creating quantity initially in OpenLCA internal product flow unit 
            # (as this is the unit in which the LCIA results are computed)
            impact_quantity = Quantity(h[index['index']],
                                       product_flow_impact_unit,
                                       reference = full_reference)
            
            # Then converting it to pyH2A functional unit (with full reference) for output
            # (this only so that the printed results are in the same units as the functional unit, for easier comparison)
            impact_quantity_functional_unit = Quantity(impact_quantity.unit[functional_unit_impact_unit],
                                                       functional_unit_impact_unit,
                                                       reference = full_reference)

            # Storing the impact quantity in the output dictionary, keyed by impact name
            self.lca_results[index['impact_name']] = impact_quantity_functional_unit

    @property
    def scaling_vector(self):
        '''Per-process activity levels for this scenario, for contribution analysis.

        Computed on demand from the cached basis columns; :meth:`perform_lca`
        does not need it and so does not pay for it per Monte Carlo sample.
        '''
        cache = LCA_Plugin._cache
        correction = np.asarray(cache['basis_component'] @ self.delta).reshape(-1)
        scaling_vector = cache['base_scaling_vector'] - correction * self.factor

        # For the reference entry that subtraction is ``y[0] - correction[0] * factor``, which
        # is algebraically ``y[0] / (1 + correction[0])``, i.e. ``self.factor`` itself. Evaluated
        # as written it cancels about log10(alpha_scenario / alpha_export) digits - at plant
        # scale it is the difference of two numbers agreeing to within 1e-8 - and the error is
        # then amplified by the large entries of the rewritten column. Take the closed form.
        scaling_vector[0] = self.factor

        return scaling_vector
