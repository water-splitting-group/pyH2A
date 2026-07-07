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

LCA is an optional feature: adding a ``# Life Cycle Assessment`` section to the input file
activates it. If the section is absent, pyH2A runs as a pure techno-economic model. However,
once activated, the folder containing the openLCA matrix export must be present and correctly
specified in the input file. In addition, every foreground process in the technosphere matrix
must be listed in one or more ``# LCA - ...`` tables in the input file. The section name must
begin with ``LCA`` (case-insensitive).

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

The ``index_B.csv`` file is bundled with the export but is not read by pyH2A.

Configure the input file for LCA
=================================

Life Cycle Assessment section
------------------------------

Add a ``# Life Cycle Assessment`` section to the input file with the path to the export folder, , as illustrated in the example below:

.. code-block:: markdown

   # Life Cycle Assessment 
   
   Name | Value
   --- | ---
   Matrix Folder | examples/LCA_example/LCA_Test_PVE_EF

The path is relative to the working directory from which pyH2A is invoked.

LCA component table
-------------------

One or more ``# LCA - ...`` sections list the foreground processes whose exchange amounts will
be updated for each scenario. Below is an example of a complete LCA input file for the foreground
 process of PV + Electrolysis (PVE).

.. code-block:: markdown

	# LCA - PVE Components

    Name | Value | Unit | UUID
    --- | --- | --- | ---
    Total H2 Production | {Technical Operating Parameters and Specifications > Total output at gate > Value, kg} | kg | 50e1c844-e481-4c14-a3ca-1948f1d2fe37
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
listed. Omitting one raises a ``ValueError``.

Users always supply positive magnitudes. pyH2A inherits the sign from the original matrix: the
functional unit process (typically H2 production) is positive; all consumed inputs are stored
as negative values internally.

Multiple ``# LCA - ...`` tables are supported and their rows are merged, which allows grouping
components by subsystem for readability.

Plugin LCA outputs — PVE example
=================================

.. note::

   The plugin descriptions below are specific to the **PV + Electrolysis (PVE)** reference
   model bundled with pyH2A (``examples/LCA_example/PVE.md``). PVE is one example of a complete
   TEA–LCA coupling; other H2 production pathways (e.g. PEC, photocatalytic) define a
   different set of ``# LCA - ...`` rows and rely on different plugin outputs. The general
   principle — plugins run first, their outputs are referenced by path in the LCA table —
   applies to any model.

In a full PVE model, all five LCA component values are computed by plugins and referenced via
path expressions in the ``# LCA - ...`` table. The plugins run before LCA is triggered, so
their outputs are already available in ``dcf.inp`` when the LCA table is processed.

Production_Plugin
-------------------

Computes annual H2 output at the plant gate.

- **LCA input required:** none (outputs are always computed)
- **Output used by LCA:** ``Technical Operating Parameters and Specifications > Total output at gate > Value`` — cumulative H2 production at gate over the plant lifetime, in kg, used to scale the H2 Production foreground process.

Photovoltaic_Plugin
--------------------

Simulates PV electricity production and calculates the array area.

- **LCA input required:** none (outputs are always computed)
- **Output used by LCA:** ``Non-Depreciable Capital Costs > Solar collection area > Value`` — total PV area in m², used to scale the PV module manufacturing foreground process.

Electrolyzer_Plugin
--------------------

Models electrolyzer operation and calculates the required number of units.

- **LCA input required:** ``Electrolyzer > Unit nominal power > Value`` must be present in the input file. This is the rated power of one electrolyzer unit.
- **Output used by LCA:** ``Electrolyzer > Number of electrolyzers required > Value`` — total nominal power divided by unit nominal power, used to scale the electrolyzer manufacturing foreground process.

To enable this output, add ``Unit nominal power`` to the ``# Electrolyzer`` table:

.. code-block:: markdown

	# Electrolyzer

	Name | Value | Unit | Comment
	--- | --- | --- | ---
	Nominal power | 5,500.0 | kW | Total plant electrolyzer power
	...
	Unit nominal power | 1,100.0 | kW | Rated power of one electrolyzer unit (gives 5 units)

Battery_Plugin
---------------

Models battery storage and calculates installed battery mass.

- **LCA input required:** ``Battery > Energy density > Value`` must be present (optional input; if absent, the mass is not computed and the path reference in the LCA table will fail to resolve).
- **Output used by LCA:** ``Battery > Mass > Value`` — design capacity divided by energy density, used to scale the battery manufacturing foreground process.

Add the energy density to the ``# Battery`` table:

.. code-block:: markdown

	# Battery

	Name | Value | Unit | Comment
	--- | --- | --- | ---
	Design capacity | 800000 | kWh | Full design capacity of battery.
	...
	Energy density | 0.2 | kWh/kg | Battery specific energy for mass calculation

Reverse_Osmosis_Plugin
-----------------------

Models the reverse osmosis water treatment system and calculates the number of devices.

- **LCA input required:** ``Reverse Osmosis > Device throughput > Value`` must be present (throughput of one device unit).
- **Output used by LCA:** ``Reverse Osmosis > Number of devices required > Value`` — total annual sea-water demand divided by device throughput, used to scale the reverse osmosis manufacturing foreground process.

Add the device throughput to the ``# Reverse Osmosis`` table:

.. code-block:: markdown

	# Reverse Osmosis

	Name | Value | unit |Comment
	--- | --- | ---
	Power Demand | 2.71 | kWh/m3
	...
	Device throughput | 6.23e10 | L/year | Throughput of one RO device per year

Run pyH2A with LCA
==================

The run command is identical to a standard TEA run:

.. code-block:: bash

	pyH2A run -i input.md -o .

LCA is triggered automatically at the end of the financial workflow whenever the
``# Life Cycle Assessment`` section is present. No additional flags are required. 

Monte Carlo analysis with LCA
------------------------------

To propagate parameter uncertainty through both TEA and LCA, include ``Monte_Carlo_Analysis``
in the input file and set ``Dependent Variable`` to ``Climate change``:

.. code-block:: markdown

	# Monte_Carlo_Analysis

	Name | Value
	--- | ---
	Samples | 50000
	Dependent Variable | Climate change
	Output File | examples/LCA_example/Monte_Carlo_Output.csv

The Monte Carlo engine samples the specified input parameters, re-runs the full pipeline (including LCA)
for each sample, and collects the chosen output.

Access LCA results
==================

When running from a Python script, LCA results are accessible on the DCF object:

.. code-block:: Python

	from pyH2A.run_pyH2A import pyH2A

	result = pyH2A('input.md', '.')
	lca = result.base_case.lca

``lca.lca_results`` is a dictionary keyed by the verbatim impact category name from
``index_C.csv``:

.. code-block:: Python

	for name, entry in lca.lca_results.items():
	    print(f"{name}: {entry['value']:.6f} {entry['unit']}")

Example output for an IPCC 2013 no LT export:

.. code-block:: text

	Climate change no LT - Global warming potential (GWP100) no LT: 0.454132 kg CO2-Eq
	Climate change no LT - Global warming potential (GWP20) no LT: 1.234567 kg CO2-Eq
	...

To retrieve a single result by impact name:

.. code-block:: Python

	gwp100_key = 'Climate change no LT - Global warming potential (GWP100) no LT'
	gwp100 = result.base_case.lca.lca_results[gwp100_key]['value']


Artifact folder and maintenance
================================

On first run, pyH2A factorises the technosphere matrix and pre-computes basis vectors. These
are saved to an ``Initial_Artifacts`` subdirectory inside the matrix export folder so that
subsequent runs (including every Monte Carlo worker) can skip the expensive factorisation.
It stores only the minimum information needed to perform the Sherman-Morrison update.

.. code-block:: text

	<export_folder>/
	    Initial_Artifacts/
	        base_scaling_vector.npz   — A⁻¹f for the original demand vector
	        A0_column.npz             — UUIDs and values of nonzero column-0 entries
	        basis_component.npz       — A⁻¹ eᵢ columns for each foreground component
	        matrix_B.npz              — copy of the intervention matrix
	        matrix_C.npz              — copy of the characterisation matrix
	        impact_index.npz          — impact category names and units

The artifacts are valid as long as the matrix export does not change. **Delete the
``Initial_Artifacts`` folder whenever you export the new matrices from openLCA**.

Within a Python process, the artifacts are also held in a process-local RAM cache
(``LCA._cache``). Multiprocessing workers each build their own RAM cache from disk on first
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

For a system with four foreground components, ``basis_component`` has shape ``(n, 4)`` where
``n`` is the total number of processes. The ``(n, 4)`` multiply replaces an ``(n³)`` factorisation.

See :class:`~pyH2A.LCA.LCA.LCA` for the complete API reference and full mathematical
derivation.

Troubleshooting
===============

``ValueError: No LCA component tables found in input``
--------------------------------------------------------

No section whose name starts with ``LCA`` was found in the input file. Check that the
``# LCA - ...`` section header is spelled correctly and that the file was loaded without
parsing errors.

``ValueError: UUID '...' ... is missing from the input LCA component tables``
-------------------------------------------------------------------------------

A UUID in the nonzero entries of the technosphere matrix first column has no matching entry in
any ``# LCA - ...`` table. Every foreground component must be listed. Find the missing UUID in
``index_A.csv`` to identify the process.

``ValueError: Expected N LCA components ... but got M``
--------------------------------------------------------

More rows were found across all ``# LCA - ...`` tables than there are nonzero entries in
column 0 of the technosphere matrix. Remove the extra rows or check that the correct matrix
export folder is specified.

``ZeroDivisionError: Sherman-Morrison denominator is too small``
----------------------------------------------------------------

The scenario values caused the functional unit production amount to approach zero, making the
rank-1 update numerically singular. Verify that the exchange amount for the H2 production
foreground process is non-zero.

``KeyError: 'Unit'``
----------------------

An ``# LCA - ...`` table row is missing its ``Unit`` column. Every row must declare a ``Unit`` —
it is required to convert the resolved ``Value`` into the flow unit recorded in ``index_A.csv``,
not merely informational. Add a ``Unit`` entry for the affected row.

``ValueError: Dimension mismatch: original dimension '...', but requested dimension '...'``
-----------------------------------------------------------------------------------------------

The ``Unit`` declared for an LCA component does not share a physical dimension with the flow's
unit in ``index_A.csv`` (e.g. supplying a mass unit for a flow whose unit is energy). Check the
``Unit`` column against the ``flow unit`` recorded for that UUID in ``index_A.csv`` and correct
the mismatch.