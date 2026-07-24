====================
Monte Carlo Analysis
====================

.. contents:: Table of Contents
    :depth: 2
    :local:
    :class: this-will-duplicate-information-and-it-is-still-useful-here

Overview
========

Monte Carlo analysis answers a "what if" question: given uncertainty (or a plausible future
range) in a set of input parameters, what range of outcomes results, and how far does the model
have to move from its base case to reach a target outcome?

Concretely, pyH2A repeatedly re-runs the full model (the discounted cash flow workflow, and LCA
if it is active) with randomly sampled combinations of the chosen input parameters, each drawn
uniformly from a specified range. Every sample produces one value of a single chosen output
(the "dependent variable" — e.g. levelized H2 cost, or an LCA impact category). The collection
of samples is then used to:

- Show the overall distribution of possible outcomes (histogram).
- Identify which samples fall within a target range for the dependent variable.
- Compute how "far" each sample is from the base case, in terms of how much the varied
  parameters had to change (the *development distance*, see below) — and relate that distance
  to the outcome (the *distance-cost relationship*).

Monte Carlo analysis is requested by adding a ``Monte_Carlo_Analysis`` module to the input file.
It works with a pure techno-economic (TEA) run, and equally with a TEA+LCA run (see
:doc:`lca_guide` for how LCA is coupled in) — the only difference is which dependent variable is
selected.

Two input tables
=================

Monte Carlo analysis is configured with two tables in the input file:

- ``# Monte_Carlo_Analysis`` — overall settings: how many samples, which output to track, what
  target range to look for, and where to read/write results.
- ``# Parameters - Monte_Carlo_Analysis`` — which input parameters to vary, and over what range.

Monte_Carlo_Analysis table
---------------------------

.. code-block:: markdown

	# Monte_Carlo_Analysis

	Name | Value
	--- | ---
	Samples | 50000
	Dependent Variable | h2_cost
	Target Response Range | 1.5; 2.6
	Output File | examples/PV_E_example/Monte_Carlo_Output.csv

- **Samples** — number of random parameter combinations to evaluate. Every sample re-runs the
  entire model from scratch, so the run time scales roughly linearly with this number (samples
  are distributed across all available CPU cores, see :ref:`mc_performance_label`).
- **Dependent Variable** — the single model output that Monte Carlo analysis tracks for every
  sample, such as:

  - ``h2_cost`` — the levelized cost of hydrogen (:attr:`~pyH2A.Discounted_Cash_Flow.Discounted_Cash_Flow.h2_cost`).
  - ``Climate change``, ``Cumulative energy demand``, or
    ``Climate change no LT - Global warming potential (GWP100) no LT`` — an LCA impact category
    result (:attr:`~pyH2A.LCA.LCA.LCA.lca_results`). Requires an active ``# Life Cycle
    Assessment`` section (see :doc:`lca_guide`); the string must match one of the impact names
    produced by the openLCA matrix export in use.

  Choosing the dependent variable is really choosing the question you want answered: "how does
  H2 cost respond to this uncertainty?" versus "how does this technology's carbon footprint
  respond?". Only one dependent variable can be tracked per Monte Carlo run — running both cost
  and an LCA metric requires two separate runs (with two separate ``Output File`` values).
- **Target Response Range** — two values (``lower; upper``) bounding the outcome you're
  interested in, in the same unit as the dependent variable. Samples whose dependent-variable
  value falls inside this range are used for the development-distance analysis (see below).
- **Output File** — where the raw results (every sample's parameter values and dependent-variable
  outcome) are written for later reuse or manual inspection.
- **Input File** *(optional, alternative to Output File)* — if set, no new samples are
  generated. Instead, results are read back from a file previously written by ``Output File``
  (e.g. from an earlier long run), letting you re-plot the same data without re-running the
  whole model. See :meth:`~pyH2A.Analysis.Monte_Carlo_Analysis.Monte_Carlo_Analysis.read_results`
  for the exact file format and how parameter renaming across runs is handled via ``File Index``
  (below).

Parameters - Monte_Carlo_Analysis table
------------------------------------------

Each row of this table defines one input parameter to vary and the range to sample it over.

.. code-block:: markdown

	# Parameters - Monte_Carlo_Analysis

	Parameter | Name | Type | Values | File Index | Comment
	--- | --- | --- | --- | --- | ---
	{Photovoltaic > Efficiency > Value, -} | PV efficiency (%) | value | Base; 0.4 | 0 | PV module efficiency uncertainty range.
	{Battery > Energy density > Value, kWh/kg} | Battery density kWh / kg | value | 0.1; 0.2 | 1 | Battery specific energy uncertainty range.
	{Reverse Osmosis > Recovery rate > Value, -} | Reverse osmosis recovery rate | value | 0.4; 0.9 | 2 | Reverse osmosis recovery range.
	{Electrolyzer > Hydrogen yield per unit energy > Value, kg/kWh} | Electrolyzer efficiency kg($H_{2}$) / kWh | value | Base; 0.025 | 3 | Same Monte Carlo range convention as other PV_E files.

- **Parameter** — the ``top key > middle key > bottom key`` path to the value being varied
  (identical path syntax used everywhere else in pyH2A input files).
- **Name** — display label used in plots and tables; does not need to match anything in the
  input file.
- **Type** — how the sampled number is applied to the existing value at ``Parameter``:

  - ``value`` — the sampled number *replaces* the existing value outright.
  - ``factor`` — the sampled number *multiplies* the existing value.

  ``factor`` is convenient for keeping a parameter's uncertainty proportional to whatever its
  base-case value happens to be (e.g. "50% to 100% of current cost"), while ``value`` is more
  direct for absolute targets (e.g. "somewhere between 0.1 kWh/kg and 0.2 kWh/kg").
- **Values** — the two bounds of the sampling range, separated by ``;``. Each bound is either:

  - a plain number (interpreted according to ``Type``, so for a ``factor`` row ``1.0`` means "no
    change" and ``0.5`` means "half of base"), or
  - the special keyword ``Base`` or ``Reference`` — resolves to the parameter's current value in
    the input file, so one side of the range is always exactly the base case. This is the most
    common pattern: one bound is ``Base`` (today's value) and the other is a projected future
    value, describing "how might this parameter move from where it is today". 
- **File Index** *(optional)* — only relevant when reading results back via ``Input File``
  (above). If a parameter's ``Name`` has since been changed, ``File Index`` maps it back to the
  column position it had when the results file was written, so old runs stay reusable after
  renaming a parameter for display purposes.
- **Comment** — free text, ignored by pyH2A; use it to record the rationale/source for a chosen
  range.

The order of rows in this table matters for plotting: the first parameter maps to the x-axis,
the second to the y-axis, and the third to the color axis in
:meth:`~pyH2A.Analysis.Monte_Carlo_Analysis.Monte_Carlo_Analysis.plot_colored_scatter`. Reordering
rows changes which parameter lands on which axis without changing the analysis itself.

Choosing parameters and ranges
================================

There's no automatic parameter selection — the modeler picks which inputs to vary. Good
candidates are usually the parameters with the largest known uncertainty or the ones a
techno-economic projection most depends on (e.g. capital cost learning curves, conversion
efficiencies, replacement costs). A useful starting point might be to vary the same parameters already
covered by a sensitivity analysis, since those are, by construction, the ones the base case is
most sensitive to.

Practical guidance:

- Start with 3-6 parameters. Every added parameter increases the dimensionality of the sampled
  space, which both dilutes the density of samples landing inside any given
  ``Target Response Range`` and makes the resulting scatter/distance plots harder to interpret.
- Anchor one bound at ``Base``/``Reference`` whenever the question is "how far can this
  parameter plausibly move from where it is today", which is the most common framing for
  technology-learning projections.
- Keep ``Values`` ranges physically meaningful — pyH2A does not clip or validate that sampled
  values stay sensible (e.g. an efficiency above 1 will simply be used as given), so overly wide
  ranges can produce nonsensical intermediate model runs.

Development distance
======================

Once samples within the ``Target Response Range`` are identified, pyH2A computes each one's
*development distance*: how far its combination of parameter values is from the base case,
normalized so that every parameter's own sampled range spans the same [0, 1] scale (so a
parameter with a huge absolute range doesn't automatically dominate the distance just because of
its units). A distance of 0 means every varied parameter is still at its base-case value; a
distance of 1 means every parameter has moved all the way to the edge of its sampled range.

This distance is computed twice, over two different sets of samples, feeding two different plots:

- :meth:`~pyH2A.Analysis.Monte_Carlo_Analysis.Monte_Carlo_Analysis.development_distance` computes
  it only for the samples already inside ``Target Response Range`` — this feeds
  :meth:`~pyH2A.Analysis.Monte_Carlo_Analysis.Monte_Carlo_Analysis.plot_distance_histogram`, a plain
  histogram of how far the *qualifying* samples are from the base case.
- :meth:`~pyH2A.Analysis.Monte_Carlo_Analysis.Monte_Carlo_Analysis.full_distance_response_relationship`
  computes it for **every** sample (not just the ones inside the target range), sorts them by
  distance, and fits a Savitzky-Golay smoothed trendline through the full distance-vs-dependent-variable
  relationship. This feeds
  :meth:`~pyH2A.Analysis.Monte_Carlo_Analysis.Monte_Carlo_Analysis.plot_distance_response_relationship`:
  development distance on the x-axis, the dependent variable on the y-axis, the smoothed trendline
  showing the overall trend, and the target range highlighted as a horizontal band so you can see
  where the trend crosses into it. In plain terms, it answers "how much do these parameters need
  to collectively improve before the model lands in the target range?" — a small required distance
  suggests the target is achievable with modest, incremental progress; a distance close to 1
  suggests every parameter needs to move to its most optimistic assumption simultaneously.

.. warning::

   ``full_distance_response_relationship`` is called unconditionally when ``Monte_Carlo_Analysis`` is
   constructed, with its default smoothing window
   (``window_length = int(Samples / 25)``, must exceed a polynomial order of 4). With too few
   ``Samples`` (roughly under 100-125 with the defaults), ``scipy.signal.savgol_filter`` raises
   ``ValueError``.

Running Monte Carlo analysis
===============================

The run command is identical to a standard pyH2A run:

.. code-block:: bash

	pyH2A run -i input.md -o .

.. _mc_performance_label:

Performance
-------------

Each sample is a full, independent model run (deep-copying the input dictionary and constructing
a fresh :class:`~pyH2A.Discounted_Cash_Flow.Discounted_Cash_Flow`), so samples are distributed
across all available CPU cores via multiprocessing
(:meth:`~pyH2A.Analysis.Monte_Carlo_Analysis.Monte_Carlo_Analysis.perform_monte_carlo_multiprocessing`).
Wall-clock time scales with ``Samples`` divided by the number of cores available, plus a small
fixed overhead per worker process. If LCA is active, every sample also triggers an LCA
evaluation — this is inexpensive per sample thanks to the Sherman-Morrison shortcut described in
:doc:`lca_guide`, but still adds up across tens of thousands of samples.

Generating plots
-------------------

As with any analysis module, plotting methods are requested via a ``Methods`` table:

.. code-block:: markdown

	# Methods - Monte_Carlo_Analysis

	Name | Method Name | Arguments
	--- | --- | ---
	distance_cost_relationship | plot_distance_response_relationship | {'show': True, 'save': True}
	colored_scatter | plot_colored_scatter | {'show': True, 'save': True}
	complete_histogram | plot_complete_histogram | {'show': True, 'save': True}
	distance_histogram | plot_distance_histogram | {'show': True, 'save': True}

See :class:`~pyH2A.Analysis.Monte_Carlo_Analysis.Monte_Carlo_Analysis` for the full list of
plotting methods and their arguments, and :doc:`guide` for the general mechanics of the
``Methods`` table syntax (inline argument dictionaries vs. a separate ``Arguments`` table).

.. seealso::

   :doc:`lca_guide` — coupling Monte Carlo analysis with life cycle assessment, including how the
   LCA-specific dependent variables are computed for each sample.
