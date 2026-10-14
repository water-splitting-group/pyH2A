Optimization_Analysis
=====================

.. contents:: Table of Contents
    :depth: 2
    :local:
    :class: this-will-duplicate-information-and-it-is-still-useful-here

Overview
--------

The ``Optimization_Analysis`` module optimizes parameters of a pyH2A model in order to minimize
or maximize a dependent variable, for example the levelized cost or a life cycle impact per
functional unit. The optimization is performed with differential evolution
(``scipy.optimize.differential_evolution``), a global optimizer which only requires bounds for
each parameter and no gradients, which makes it suitable for pyH2A models (which contain discrete
steps, e.g. the number of electrolyzer units).

The module is executed by pyH2A if an ``Optimization_Analysis`` table is present in the input
file. It:

1. evaluates the dependent variable for the base case (the unmodified input),
2. optimizes the specified parameters within their bounds,
3. prints the results and saves a report to the specified output file,
4. can plot the convergence of the optimization (requested via a ``Methods`` table).

The optimization itself is performed by the module-level function
:func:`~pyH2A.Analysis.Optimization_Analysis.perform_optimization`, which can also be used
directly from Python or by other analysis modules (see `Use from Python and other analysis
modules`_).

Input
-----

The optimization is specified by three tables. The following example
(``src/tests/Analysis/Optimization/PV_E_Optimization_Test.md``) minimizes the global warming
potential of the PV-E model by sizing the electrolyzer, the PV system and the battery:

.. code-block:: markdown

	# Dependent variable

	Name | Path to variable | Variable unit
	--- | --- | ---
	Global warming potential (GWP100) | Dependent Variables > Climate change: fossil - Global warming potential (GWP100) > Value | kg[$CO_{2}$-Eq]/kg[H2]

	# Optimization_Analysis

	Name | Value | Comment
	--- | --- | ---
	Direction | minimize | Minimizing the dependent variable
	Output File | Optimization_Output.txt | Text file with optimization report
	Maximum iterations | 20 | Maximum number of generations
	Population size | 5 | Population has 5 x 3 parameters = 15 members
	Seed | 42 | Seed of random number generator for reproducible results
	Polish | False | No polishing of the best member with L-BFGS-B

	# Parameters - Optimization_Analysis

	Name | Parameter path | Values | Comment
	--- | --- | --- | ---
	Electrolyzer nominal power / MW | Electrolyzer > Nominal power > Value | 100 ; 1000 | Sizing of electrolyzer
	Photovoltaic nominal power / MW | Photovoltaic > Nominal power > Value | 500 ; 3000 | Sizing of PV system
	Battery design capacity / MWh | Battery > Design capacity > Value | 300 ; 4000 | Sizing of battery

``Dependent variable``
	``Path to variable`` is the path to the dependent variable (top key > middle key > bottom key)
	and ``Variable unit`` the unit in which it is optimized and reported. The dependent variable
	has to be a scalar. Only the first row is optimized, so that the table can be shared with
	other analysis modules (such as ``Monte_Carlo_Analysis``, which additionally requires a
	``Target range`` column).

``Parameters - Optimization_Analysis``
	Each row is a parameter which is varied during the optimization. The first column is the
	display name of the parameter. ``Parameter path`` is the path to the parameter in the input
	file (without braces and unit, the value is replaced directly). ``Values`` are the bounds of
	the parameter in the format ``lower ; upper`` (the order is irrelevant). ``Base`` or
	``Reference`` can be used as one of the bounds to refer to the base value of the parameter,
	e.g. ``Base ; 3000``.

``Optimization_Analysis``
	Direction, output file and settings of the optimizer. All rows are optional. Settings which
	are not specified use SciPy's defaults. Rows which are not listed below raise an error, so that
	a typo does not silently fall back to a default (e.g. 1000 generations).

Settings
--------

.. list-table::
   :header-rows: 1
   :widths: 20 20 15 45

   * - Row
     - Argument of ``differential_evolution``
     - Default
     - Description
   * - Direction
     - --
     - minimize
     - ``minimize`` or ``maximize`` the dependent variable.
   * - Output File
     - --
     - --
     - Path to the text file in which the optimization report is saved. No report is saved if not
       specified.
   * - Maximum iterations
     - ``maxiter``
     - 1000
     - Maximum number of generations.
   * - Population size
     - ``popsize``
     - 15
     - Multiplier for the size of the population. The population has ``Population size`` x number
       of parameters members (at least 5).
   * - Relative tolerance
     - ``tol``
     - 0.01
     - Relative tolerance for convergence.
   * - Absolute tolerance
     - ``atol``
     - 0
     - Absolute tolerance for convergence.
   * - Mutation
     - ``mutation``
     - 0.5 ; 1
     - Mutation constant, either a number or a range ``min ; max`` (dithering).
   * - Recombination
     - ``recombination``
     - 0.7
     - Recombination constant (crossover probability).
   * - Strategy
     - ``strategy``
     - best1bin
     - Differential evolution strategy.
   * - Initialization
     - ``init``
     - latinhypercube
     - Initialization of the population (``latinhypercube``, ``sobol``, ``halton`` or ``random``).
   * - Polish
     - ``polish``
     - True
     - If ``True``, the best member is polished with L-BFGS-B at the end of the optimization.
       Since pyH2A models often contain discrete steps, polishing typically yields little
       improvement and can be switched off with ``False``.
   * - Seed
     - ``seed``
     - --
     - Seed of the random number generator, for reproducible results.
   * - Workers
     - ``workers``
     - 1
     - Number of parallel processes used to evaluate the model (``-1``: all available CPUs).
   * - Updating
     - ``updating``
     - immediate
     - ``immediate`` (best member is updated within a generation) or ``deferred`` (once per
       generation). ``deferred`` is always used if ``Workers`` is not 1. With ``deferred``, a
       seeded optimization gives the same result for any number of workers.

Each model evaluation takes the full pyH2A calculation, so the run time is approximately the
number of function evaluations multiplied by the run time of the model. Without polishing, at
most (``Maximum iterations`` + 1) x number of population members evaluations are performed.

Output
------

During the optimization, the best value of the dependent variable is printed after each
generation and a summary of the results is printed at the end.

If ``Output File`` is specified, a report is saved. It is written as Markdown tables in the
format of pyH2A input files, so that it is human-readable and can be read back with
:func:`~pyH2A.Utilities.input_modification.convert_file_to_dictionary`. The report contains the
following tables:

``Optimization summary``
	Input file, date, pyH2A and SciPy versions, dependent variable (name, path and unit),
	direction, optimal value, base case value, absolute and relative change, success flag and
	termination message of the optimizer, number of generations, number of function
	evaluations by the optimizer (including polishing), base case evaluations, total number of
	model evaluations, run time and run time per model evaluation.

``Optimal parameters``
	For each parameter: path, lower and upper bound, base case value, optimal value and
	relative position of the optimal value within the bounds (0: lower bound, 1: upper bound).
	Values close to 0 or 1 indicate that the bounds may have to be widened.

``Optimization settings``
	All settings of the optimizer (including SciPy's defaults for settings which are not
	specified) and the corresponding row of the ``Optimization_Analysis`` table.

``Convergence history``
	Number of function evaluations, best value of the dependent variable and convergence measure
	after each generation (SciPy's convergence measure, values of 1 or larger indicate convergence
	if the absolute tolerance is 0).

``Final population``
	Parameter values and dependent variable of all members of the final population, sorted from
	best to worst member. Members close to the optimum show which parameter combinations perform
	similarly well.

Convergence plot
----------------

The convergence of the optimization (best value of the dependent variable after each generation,
with the base case as reference) is plotted by
:meth:`~pyH2A.Analysis.Optimization_Analysis.Optimization_Analysis.plot_convergence`, which is
requested via a ``Methods`` table:

.. code-block:: markdown

	# Methods - Optimization_Analysis

	Name | Method Name | Arguments
	--- | --- | ---
	Convergence plot | plot_convergence | {'show': False, 'save': True}

With ``save`` set to ``True``, the plot is saved in the output directory of the pyH2A run.

Use from Python and other analysis modules
------------------------------------------

The results of a pyH2A run are accessible via the module instance:

.. code-block:: Python

	from pyH2A.run_pyH2A import pyH2A

	result = pyH2A('PV_E_Optimization_Test.md', '.')
	optimization = result.meta_modules['Optimization_Analysis']['Module']

	optimization.results['Optimal value']       # optimal value of the dependent variable
	optimization.results['Optimal parameters']  # optimal value of each parameter

The optimization is performed by the module-level function
:func:`~pyH2A.Analysis.Optimization_Analysis.perform_optimization`. It only requires the input
dictionary, the parameters (as processed by
:func:`~pyH2A.Utilities.Analysis_Utilities.analysis_utilities.process_parameters`) and the
dependent variable (as read by
:func:`~pyH2A.Utilities.Analysis_Utilities.analysis_utilities.read_dependent_variable`), so that it
can be called by other analysis modules, for example to optimize parameters for every sample of
a Monte Carlo analysis:

.. code-block:: Python

	from pyH2A.Utilities.IO import input_resolver_function
	from pyH2A.Utilities.input_modification import convert_input_to_dictionary, Inp_Wrapper
	from pyH2A.Utilities.Analysis_Utilities.analysis_utilities import (read_dependent_variable,
	                                                                   process_parameters)
	from pyH2A.Analysis.Optimization_Analysis import Optimization_Analysis, perform_optimization

	input_file = 'PV_E_Optimization_Test.md'

	inp = convert_input_to_dictionary(input_file)
	input_dict = Optimization_Analysis(input_file, run = False).input_dict
	inp_resolved = input_resolver_function(input_dict, Inp_Wrapper(inp), 'Optimization_Analysis')

	dependent_variable = read_dependent_variable(inp_resolved['Dependent variable'],
	                                             keys = ['Path to variable', 'Variable unit'])
	parameters = process_parameters(inp_resolved['Parameters - Optimization_Analysis'], inp,
	                                keys = ['Parameter path', 'Values'])

	# `inp` may be modified before the optimization, e.g. by random Monte Carlo parameter variations
	results = perform_optimization(inp, parameters, dependent_variable,
	                               direction = 'minimize',
	                               settings = {'maxiter': 50, 'seed': 1, 'workers': 1},
	                               evaluate_base_case = False)

When ``perform_optimization`` is called within parallel worker processes (e.g. per Monte Carlo
sample), ``workers`` should be 1 to avoid nested parallelisation, and ``evaluate_base_case`` can
be set to ``False`` to avoid an additional model evaluation per call.

API
---

.. automodule:: pyH2A.Analysis.Optimization_Analysis
    :members:
