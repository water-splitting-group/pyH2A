=====================
Life Cycle Assessment
=====================

.. contents:: Table of Contents
    :depth: 2
    :local:
    :class: this-will-duplicate-information-and-it-is-still-useful-here

Overview
========

pyH2A can couple a full techno-economic analysis with life cycle assessment (LCA) in a single
run. The LCA module reads a technosphere matrix exported from openLCA, updates it with
scenario-specific exchange amounts resolved from the plugin outputs, and returns impact
characterisation results (e.g. GWP100) alongside the levelised H2 cost.

Because pyH2A supplies both the demand (one unit of the reference flow) and every amount in the
foreground column, the size the openLCA product system happened to be drawn at — 1 kg of product,
or 1000 — cancels out: the same physical plant described at any reference amount gives the same
impact per functional unit.

LCA is an optional feature, run by
:class:`~pyH2A.Plugins.LCA_Plugin.LCA_Plugin` as an ordinary Workflow plugin. Which
defaults file the input file merges in decides whether it runs at all:

- ``pyH2A.Config~Defaults_TEA.md`` — techno-economic analysis only, no LCA.
- ``pyH2A.Config~Defaults_LCA.md`` — LCA only (``Time_Plugin``, ``Production_Plugin``,
  ``LCA_Plugin``), without the discounted cash flow.
- ``pyH2A.Config~Defaults_TEA_LCA.md`` — the full TEA workflow with LCA appended.

Once LCA runs, the folder containing the openLCA matrix export must be present and correctly
specified in the input file. Every foreground process in the technosphere matrix must be
accounted for: the product itself through ``UUID of product``, and every other process
through a row of one or more ``# LCA - ...`` tables in the input file. The section name must
contain ``LCA`` (case-sensitive) anywhere in the name, not necessarily at the start.

Similar to the TEA workflow, LCA is fully compatible with Monte Carlo sampling: the plugin
outputs are re-evaluated for each sample, the foreground column of the technosphere matrix
is updated based on Monte Carlo parameters, and the impact results are collected in a CSV file.

Export the matrix from openLCA
==============================

Here's a short guide to export a matrix from openLCA:

1. Open your product system
- In your openLCA instance, in the Navigation panel, go to Product Systems.
- Double-click the product system you want to analyze.
2. Calculate the model
- Click **Calculate** on the **General information** tab.
- Select the desired impact assessment method.
- Run the calculation.
3. Export the Matrices
- In the menue bar, click **Export as matrix**.
- On the **Export matrices** page, specify the target directory in "Folder" and select format as Python (NumPy, SciPy)
- All the matrices will be exported as .npz or .npy files, and the index files will be exported as .csv files. The following files are generated:

Note: Matrix export is available only for product systems that have been successfully calculated, and the exact menu names may vary slightly between openLCA versions (1.11, 2.x, etc.).

The export folder must contain (the python files are not used by pyH2A and can be ignored):

.. code-block:: text

	<export_folder>/
	    A.npz          — technosphere matrix (n × n, scipy sparse CSC)
	    B.npz          — intervention matrix (m × n, scipy sparse)
	    C.npz          — characterisation matrix (p × m, scipy sparse)
	    f.npy          — demand vector (n,)
	    index_A.csv    — process index: row/column → UUID → process name
	    index_B.csv    — elementary flow index: row → UUID → flow name
	    index_C.csv    — impact category index: row → category name → unit

``n`` is the total number of processes, ``m`` the number of elementary flows, and ``p`` the
number of impact categories. For ecoinvent-based systems, ``n`` is typically in the tens of thousands.

The ``f.npy`` and ``index_B.csv`` files are bundled with the export but are not read by pyH2A.
The demand is always exactly one unit of the reference flow, built by pyH2A itself, so that
results are inherently expressed per unit of product regardless of the magnitude openLCA
happened to calculate the product system for.

Configure the input file for LCA
=================================

Life Cycle Assessment section
------------------------------

Add a ``# Life Cycle Assessment`` section to the input file with the path to the export folder
and the UUID of the product, as illustrated in the example below:

.. code-block:: markdown

   # Life Cycle Assessment

   Name | Value
   --- | ---
   Matrix Folder | examples/LCA_example/LCA_Test_PVE_EF
   UUID of product | 50e1c844-e481-4c14-a3ca-1948f1d2fe37

The path is relative to the working directory from which pyH2A is invoked.

``UUID of product`` identifies the reference flow of the product system — the first nonzero
entry of the technosphere matrix's first column, i.e. the process's own product output. Its
amount is not declared here: it is
``Technical Operating Parameters and Specifications > Total output at gate``, the cumulated
output at the gate over the plant lifetime computed by
:class:`~pyH2A.Plugins.Production_Plugin.Production_Plugin`, so that cost and impact results
are driven by the same production figure. Its unit is the declared Functional Unit, converted
into the flow unit the export records for that UUID — which is what cross-checks the two
against each other. A Functional Unit whose dimension the reference flow cannot be expressed
in (an energy unit for a mass flow, say) raises a ``ValueError``.

Functional Unit
---------------

The Functional Unit has to name the product it refers to, as a bracketed reference:

.. code-block:: markdown

	# Functional Unit

	Name | Unit | Comment
	--- | --- | ---
	Functional Unit | kg[H2] | kg[H2] is functional unit

LCA results are reported per unit of that product (e.g. ``kg[$CO_{2}$-Eq] / kg[H2]``), so a
Functional Unit declared as a bare ``kg`` raises a ``ValueError``. The reference is purely
descriptive and plays no part in unit conversion, but it is what keeps an impact per kg of
hydrogen distinguishable from an impact per kg of anything else.

LCA component table
-------------------

One or more ``# LCA - ...`` sections list the remaining foreground processes — everything
except the product itself — whose exchange amounts will be updated for each scenario. Below is
an example of a complete LCA input file for the foreground process of PV + Electrolysis (PVE).

.. code-block:: markdown

	# LCA - PVE Components

    Name | Value | Unit | UUID
    --- | --- | --- | ---
    PV Area | {Non-Depreciable Capital Costs > Solar collection area > Value, m2} | m2 | 0c88e490-56a5-3099-807c-06645527c90e
    Electrolyzer unit number | {Electrolyzer > Number of electrolyzers required > Value, -} | - | 98f950b2-39b0-4374-a400-05984b438be9
    Battery weight | {Battery > Mass > Value, kg} | kg | c341bfcb-5959-3a70-839e-913e8250b237
    Reverse Osmosis Units | {Reverse Osmosis > Number of devices required > Value, -} | - | 056a11ab-0a7a-38dd-a1d3-4058c2a8662d

Column meanings:

- **Name** — free label; used as the row key in the parsed dictionary. Not matched against the matrix.
- **Value** — exchange amount. Can be a number or a path reference wrapped in braces with an explicit
  unit, e.g. ``{Top > Middle > Value, unit}``. The braces are required — a bare ``Top > Middle > Value``
  path raises a ``ValueError`` from the path parser. Multiple bracketed paths separated by ``;`` are
  multiplied together.
- **Unit** — required, and actually enforced. The resolved ``Value`` is converted through
  :class:`~pyH2A.Utilities.Unit_Handler.quantity.Quantity` into the flow unit recorded for that UUID in
  the openLCA export's ``index_A.csv`` (column ``flow unit``). A unit whose dimension doesn't match the
  flow's (e.g. a mass unit for an energy flow) raises a ``ValueError``, and an unrecognized unit string
  raises a ``ValueError`` from the unit parser.
- **UUID** — the openLCA process UUID. Must match a nonzero entry in column 0 of the technosphere matrix.

Every UUID that appears in the nonzero entries of the technosphere matrix first column must be
accounted for exactly once, either as ``UUID of product`` or as a component row. Omitting one,
or listing one that the technosphere column does not contain, raises a ``ValueError``.

Users always supply positive magnitudes. pyH2A inherits the sign from the original matrix: the
product process (typically H2 production) is positive; all consumed inputs are stored
as negative values internally. A negative value in the input file is therefore rejected with a
``ValueError`` rather than silently flipping a flow's direction.

Multiple ``# LCA - ...`` tables are supported and their rows are merged, which allows grouping
components by subsystem for readability. Each UUID is declared exactly once across all of them;
a UUID on two rows raises a ``ValueError`` rather than the second row overwriting the first.

What the amounts have to be
---------------------------

.. important::

   **Every amount in the technosphere column is a plant-lifetime total.** The product's amount
   is ``Total output at gate``, the cumulated output over the plant life, so each component's
   amount is the total consumed or installed over that same life — not a per-year figure. A
   component supplied per year is out by the number of operating years, in a way no check can
   catch.

   Array ``Value`` entries are reduced by **summation**. That is what an operating flow reported
   year by year needs (annual electricity summed to the lifetime total), and the opposite of what
   an installed stock repeated year by year needs (a 20-element array of "400 MW installed"
   becomes 8 000 MW). Supply stocks as scalars.

   Where the model replaces equipment over the plant life, the LCA amount is the total number of
   units manufactured, including replacements — the TEA's replacement costs and the LCA's
   manufacturing burden have to describe the same equipment.

.. note::

   Only entries that are **already nonzero** in the export's first technosphere column can be
   given a scenario value; pyH2A rewrites that column, it does not extend it. A process any
   scenario may need must therefore be present in the openLCA product system, with a placeholder
   amount if the base case does not use it. The placeholder's magnitude does not affect the
   result — it is replaced outright — so an arbitrarily small value such as ``1e-6`` is fine.

Direct emissions of the foreground process
-------------------------------------------

The foreground process may also carry elementary flows of its own (on-site combustion, fugitive
product, direct land occupation) rather than only technosphere inputs. Those are declared in
openLCA per the reference amount the product system was exported at, and pyH2A restates them by
the ratio of ``Total output at gate`` to that exported amount, exactly as it restates the
technosphere exchanges. Their contribution per functional unit is therefore whatever openLCA
records, independent of the size the product system happened to be drawn at.

They are **not** declared in the ``# LCA - ...`` tables and cannot be varied per scenario: only
the technosphere column is parameterised. A direct flow that has to change between scenarios
belongs in a sub-process of its own, listed as a component.

Where the component amounts come from
=====================================

In a coupled TEA–LCA model the component amounts are not literals: they are path references to
outputs the technology plugins have already computed by the time ``LCA_Plugin`` runs. The
product's amount is read directly from ``Production_Plugin``; every other row resolves a
``{Table > Row > Value, unit}`` reference.

The outputs currently available to reference, by plugin:

.. list-table::
   :header-rows: 1
   :widths: 28 44 28

   * - Plugin
     - Output path
     - Typical LCA use
   * - ``Production_Plugin``
     - ``Technical Operating Parameters and Specifications > Total output at gate``
     - the product itself (read automatically, not a table row)
   * - ``Photovoltaic_Plugin``
     - ``Non-Depreciable Capital Costs > Solar collection area``
     - scales PV module manufacturing
   * - ``Photovoltaic_Plugin``
     - ``Non-Depreciable Capital Costs > Land required``
     - scales land transformation / occupation
   * - ``Photovoltaic_Plugin``
     - ``Power Generation > PV yearly power generation``
     - scales an electricity generation process (summed over the plant life)
   * - ``Electrolyzer_Plugin``
     - ``Electrolyzer > H2 production (yearly)``
     - operating flows proportional to production
   * - ``Reverse_Osmosis_Plugin``
     - ``Power Consumption > Reverse osmosis consumption (yearly)``
     - scales the electricity a water treatment process draws
   * - ``Reverse_Osmosis_Plugin``
     - ``Reverse Osmosis > Capacity``
     - scales water treatment equipment

.. warning::

   Equipment **counts** — number of electrolyzer units, number of reverse osmosis devices,
   battery mass — are the natural way to scale a manufacturing process, but no plugin computes
   them today. ``Electrolyzer_Plugin`` exposes ``Actual stack replacement time`` rather than a
   unit count, ``Battery_Plugin`` exposes stored and available energy rather than a mass, and
   ``Reverse_Osmosis_Plugin`` exposes a capacity rather than a device count. Until those outputs
   exist, such amounts have to be given as literals in the ``# LCA - ...`` table, or derived from
   an output that does exist. Earlier revisions of this guide referenced
   ``Electrolyzer > Number of electrolyzers required``, ``Battery > Mass`` and
   ``Reverse Osmosis > Number of devices required``; none of them are implemented.

A worked example, mixing a plugin output with literals:

.. code-block:: markdown

	# LCA - PVE Components

	Name | Value | Unit | UUID
	--- | --- | --- | ---
	PV Area | {Non-Depreciable Capital Costs > Solar collection area > Value, m2} | m2 | 0c88e490-56a5-3099-807c-06645527c90e
	Electrolyzer units | 20 | - | 98f950b2-39b0-4374-a400-05984b438be9
	Battery mass | 150000 | kg | c341bfcb-5959-3a70-839e-913e8250b237

.. note::

   ``LCA_Plugin`` sits last in both ``Defaults_LCA.md`` and ``Defaults_TEA_LCA.md``, so every
   plugin output is already in ``dcf.inp`` when the ``# LCA - ...`` tables are resolved.

Reading cost and impact together
--------------------------------

Both the levelised cost and the impacts land in the ``Dependent Variables`` table and are both
"per kg of H2", but they are not divided by the same kilograms. The levelised cost divides by the
**NPV-discounted** output (with start-up years scaled by ``Fraction of revenues during start-up``),
as a levelised cost must; the LCA divides by the **undiscounted** lifetime total, as physical
flows must. The two denominators differ by roughly the discount factor over the plant life, which
is worth keeping in mind when plotting one against the other.

Run pyH2A with LCA
==================

The run command is identical to a standard TEA run and no additional flags are required:

.. code-block:: bash

	pyH2A run -i input.md -o .

Base case scenario
------------------

``LCA_Plugin`` runs for the base case in its Workflow position — last, after the financial
workflow in ``Defaults_TEA_LCA.md`` — provided that the ``# Life Cycle Assessment`` section
and all the required components of the foreground process in the ``# LCA - ...`` section are
present.

Monte Carlo analysis with LCA
------------------------------

.. seealso::

   :doc:`monte_carlo_guide` — for the general mechanics of Monte Carlo analysis (how samples are
   generated, how parameter ranges and ``Type`` are specified, the ``Target Response Range`` and
   development-distance concepts). This section only covers what's specific to coupling Monte
   Carlo with LCA.

To propagate parameter uncertainty through LCA as well, include ``Monte_Carlo_Analysis``
in the input file and set ``Dependent Variable`` to one of the impact assessment metrics
which is included in Characterisation matrix (C) of the openLCA matrix export. For example,
to collect ``Climate change`` index from the results of EF Impact Assessment Method
(Environmental Footprint Impact Assessment Method), set the dependent variable to ``Climate change``,
as illustrated in the example below. The Monte Carlo engine will sample the specified input parameters,
re-run the full pipeline (including LCA) for each sample, and collect the chosen output.:

.. code-block:: markdown

	# Monte_Carlo_Analysis

	Name | Value
	--- | ---
	Samples | 50000
	Dependent Variable | Climate change
	Output File | examples/LCA_example/Monte_Carlo_Output.csv


	# Parameters - Monte_Carlo_Analysis

    Parameter | Name | Type | Values | File Index | Comment
    --- | --- | --- | --- | --- | --- 
    {Photovoltaic > Efficiency > Value, -} | PV efficiency (%) | value | Base; 0.4 | 0 | PV module efficiency uncertainty range.
    {Battery > Energy density > Value, kWh/kg} |Battery density kWh / kg | value | 0.1; 0.2 | 1 | Battery specific energy uncertainty range.
    {Reverse Osmosis > Recovery rate > Value, -} | Reverse osmosis recovery rate | value | 0.4; 0.9 | 2 | Reverse osmosis recovery range.
    {Electrolyzer > Hydrogen yield per unit energy > Value, kg/kWh} | Electrolyzer efficiency kg($H_{2}$) / kWh | value | Base; 0.025 | 3 | Same Monte Carlo range convention as other PV_E files.


Access LCA results
==================

When running from a Python script, LCA results are accessible on the DCF object's ``inp``,
the same way any other plugin's declared output is read. Every impact category becomes its own
row of the ``Dependent Variables`` table — the same table the levelised cost is written to —
keyed by the verbatim impact category name from ``index_C.csv``:

.. code-block:: Python

	from pyH2A.run_pyH2A import pyH2A

	result = pyH2A('input.md', '.')
	dependent_variables = result.base_case.inp['Dependent Variables']

Each row's ``Value`` is a :class:`~pyH2A.Utilities.Unit_Handler.quantity.Quantity` expressed as
``<impact unit> / <functional unit>``:

.. code-block:: Python

	for name, entry in dependent_variables.items():
	    print(f"{name}: {entry['Value'].supplied_value:.6f} {entry['Value'].supplied_unit_reference}")

Example output for an IPCC 2013 no LT export:

.. code-block:: text

	Climate change no LT - Global warming potential (GWP100) no LT: 0.454132 kg[$CO_{2}$-Eq] / kg[H2]
	Climate change no LT - Global warming potential (GWP20) no LT: 1.234567 kg[$CO_{2}$-Eq] / kg[H2]
	...

To retrieve a single result by impact name:

.. code-block:: Python

	gwp100_key = 'Climate change no LT - Global warming potential (GWP100) no LT'
	gwp100 = result.base_case.inp['Dependent Variables'][gwp100_key]['Value'].supplied_value

The same results are also available as a single dictionary on the plugin instance, keyed by
impact name:

.. code-block:: Python

	lca_results = result.base_case.plugs['LCA_Plugin'].lca_results

The output CSV file from a Monte Carlo run contains the same impact category names as column 
headers, and the values are in the same units as reported in the base case. The CSV file also
contains the sampled input parameters for each row, so that the full uncertainty propagation
can be analyzed in post-processing. The Monte Carlo output file is specified in the 
``# Monte_Carlo_Analysis`` section of the input file. 

Artifact folder and maintenance
================================

On first run, pyH2A factorises the technosphere matrix and pre-computes basis vectors. These,
together with the characterised impact operator and the impact category
index, are saved to an ``Initial_Artifacts`` subdirectory inside the matrix export folder so that
subsequent runs (including every Monte Carlo worker) can skip both the expensive factorisation
and re-loading the original openLCA export.

.. code-block:: text

	<export_folder>/
	    Initial_Artifacts/
	        base_scaling_vector.npz   — A⁻¹f for a demand of one unit of the reference flow
	        A0_column.npz             — UUIDs, values and units of nonzero column-0 entries
	        basis_component.npz       — A⁻¹ eᵢ columns for each foreground component
	        h_base.npz                — C·B·A⁻¹f, the impacts of the base scaling vector
	        h_basis.npz               — C·B·A⁻¹ eᵢ, the impact sensitivity to each component
	        impact_index.npz          — impact category names and units
	        fingerprint.txt           — identity of the export these artifacts came from

The artifacts carry a fingerprint of the openLCA export they were built from (the size and
modification time of ``A``, ``B``, ``C``, ``index_A.csv`` and ``index_C.csv``). Re-exporting the
matrices changes that fingerprint, so pyH2A recomputes the artifacts by itself — there is no
need to delete the ``Initial_Artifacts`` folder by hand. A folder is only reused when the
fingerprint matches *and* every artifact listed above is present, so one written by an older
pyH2A, or partially deleted, is rebuilt rather than loaded from.

Within a Python process, the artifacts are also held in a process-local RAM cache
(``LCA_Plugin._cache``). Multiprocessing workers each build their own RAM cache from disk on first
use, which adds a short startup overhead per worker but avoids recomputing the artifacts within each
process worker.

Sherman-Morrison engine
========================

When exchange amounts change between scenarios (e.g. during Monte Carlo sampling), pyH2A
avoids re-factorising the full matrix. Instead it applies a rank-1 Sherman-Morrison update
to the pre-computed base scaling vector:

.. code-block:: text

	x' = x₀ - correction × (x₀[0] / (1 + correction[0]))

where ``correction = basis_component @ delta``, ``delta`` is the element-wise change in the
foreground column values, and ``basis_component`` holds the pre-computed ``A⁻¹ eᵢ`` columns.
The update is a single dense matrix-vector multiply — typically microseconds — compared to
tens of seconds for a full factorisation.

The foreground process's own elementary flows are restated for the scenario's reference amount
by that same product. Column 0 of ``B`` is declared for the amount α the export was written at,
so with ``r = 1 + delta[0]/α`` the scenario intervention matrix is ``B + (r − 1)·B[:,0]·e₀ᵀ``.
Since ``e₀ᵀx`` is the foreground activity level ``x[0]``, which the rank-1 update makes exactly
``x₀[0] / (1 + correction[0])`` — the ``factor`` above — the characterised correction is

.. code-block:: text

	h_direct × (r − 1) × factor   =   (h_direct / α) × delta[0] × factor

which is a column-0 term of the ``h_basis · delta`` product that is formed anyway. pyH2A
therefore subtracts ``h_direct / α`` from column 0 of ``h_basis`` once per export, when the
artifacts are built, and the per-sample calculation is unchanged — the restatement costs nothing
in the Monte Carlo loop.

This is what makes the result independent of the size the openLCA product system was defined at.
Without it a direct foreground emission keeps the amount it had at the export's own size while
being attributed to ``r`` times as much product, so it is divided by ``r`` and — at plant scale,
where ``r`` is of order 10⁷ — effectively deleted.

For a system with four foreground components, ``basis_component`` has shape ``(n, 4)`` where
``n`` is the total number of processes. The ``(n, 4)`` multiply replaces an ``(n³)`` factorisation.

See :class:`~pyH2A.Plugins.LCA_Plugin.LCA_Plugin` for the
complete API reference and full mathematical derivation.

Troubleshooting
===============

``KeyError: Row 'UUID of product' in table 'Life Cycle Assessment' is required but not found in dcf.inp``
----------------------------------------------------------------------------------------------------------

The ``# Life Cycle Assessment`` section declares a ``Matrix Folder`` but no ``UUID of product``.
Add the openLCA UUID of the product flow — the process whose own product output is the first
nonzero entry of the technosphere matrix's first column.

``ValueError: Mismatch between A0 column UUIDs and input LCA component UUIDs``
------------------------------------------------------------------------------

The set of UUIDs collected from ``UUID of product`` and the ``# LCA - ...`` tables is not
exactly the set of nonzero entries of the technosphere matrix's first column. Either a
foreground component is missing from the input file, or a row lists a UUID the technosphere
column does not contain. Compare the ``# LCA - ...`` rows against the nonzero entries of
column 0 in ``index_A.csv``, and check that the correct matrix export folder is specified.

``ValueError: 'UUID of product' (...) is not the reference flow of the export``
--------------------------------------------------------------------------------

The UUID declared as the product is in the technosphere column, but is not row 0 of it. The
demand vector, the rank-1 update and the product flow unit all address the reference flow by
position, so the product has to be the process the column produces, not one of its inputs. Row 0
of ``index_A.csv`` names it.

``ValueError: LCA component UUID '...' is declared more than once``
---------------------------------------------------------------------

Two rows — possibly in different ``# LCA - ...`` tables — carry the same UUID. Declare each
technosphere entry once, with its total amount, rather than split over several rows.

``ValueError: The first technosphere column of the export in '...' does not produce its own reference flow``
---------------------------------------------------------------------------------------------------------------

Row 0 of ``A[:, 0]`` is zero or negative, so the column produces nothing the demand vector can
ask for. Re-export the product system from openLCA with the intended process as its quantitative
reference.

``ValueError: Negative value for LCA component '...'``
-------------------------------------------------------

An exchange amount resolved to a negative number. Declare magnitudes only: pyH2A takes each
flow's direction from the sign the original technosphere matrix records for it.

``ValueError: Functional Unit '...' carries no reference``
-----------------------------------------------------------

The ``# Functional Unit`` table declares a bare unit such as ``kg``. Name the product it refers
to in brackets (``kg[H2]``), so that results read as an impact per unit of a named product.

``ZeroDivisionError: Sherman-Morrison denominator is singular to working precision``
------------------------------------------------------------------------------------

The scenario values caused the product's production amount to approach zero, making the
rank-1 update numerically singular. Verify that ``Total output at gate`` is non-zero.

``KeyError: 'Unit'``
-----------------------

An ``# LCA - ...`` table row is missing its ``Unit`` column. Every row must declare a ``Unit`` —
it is required to convert the resolved ``Value`` into the flow unit recorded in ``index_A.csv``,
not merely informational. Add a ``Unit`` entry for the affected row.

``ValueError: Dimension mismatch: original dimension '...', but requested dimension '...'``
---------------------------------------------------------------------------------------------

Either the ``Unit`` declared for an LCA component does not share a physical dimension with the
flow's unit in ``index_A.csv`` (e.g. supplying a mass unit for a flow whose unit is energy), or
the declared Functional Unit does not share one with the export's reference flow. Check the
``Unit`` column, and the ``# Functional Unit`` table, against the ``flow unit`` recorded for
that UUID in ``index_A.csv`` and correct the mismatch.

``ValueError: Unknown unit encountered during parsing: '...'``
---------------------------------------------------------------

An impact unit in ``index_C.csv`` is neither a unit pyH2A already knows nor one mapped in
``Config/OpenLCA_config.py``. Add an entry for the openLCA spelling to ``OPEN_LCA_CONFIG``,
giving the pyH2A unit and the reference label to report it with.