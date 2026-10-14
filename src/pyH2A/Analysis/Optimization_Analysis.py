'''Optimization of pyH2A models using differential evolution.

The optimization is performed by the module-level function :func:`perform_optimization`,
which only requires an input dictionary, the parameters which are to be optimized and the
dependent variable. It can hence be reused by other analysis modules, for example to optimize
parameters for every sample of a Monte Carlo analysis.

:class:`Optimization_Analysis` is the analysis module which is executed by pyH2A if an
``Optimization_Analysis`` table is present in the input file. It reads the optimization
specification from the input file, performs the optimization, prints the results, saves a
report and plots the convergence of the optimization.
'''

import inspect
import warnings
from datetime import datetime
from timeit import default_timer as timer
from typing import Any, Dict, Optional, Tuple

import numpy as np
import scipy
import matplotlib.ticker as mticker
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from scipy.optimize import OptimizeResult, differential_evolution

from pyH2A import __version__ as pyH2A_version
from pyH2A.Utilities.IO import input_resolver_function
from pyH2A.Utilities.IO.input_processing import parse_parameter_to_array
from pyH2A.Utilities.input_modification import (convert_input_to_dictionary,
												deep_get,
												parse_parameter,
												reverse_parameter_to_string,
												Inp_Wrapper)
from pyH2A.Utilities.Analysis_Utilities.analysis_utilities import (read_dependent_variable,
																   process_parameters,
																   substitute_parameters_and_run)
from pyH2A.Utilities.output_utilities import Figure_Lean
from pyH2A.Utilities.plugin_input_output_processing import Template_File

# Supported optimization directions and the factor with which the dependent variable is
# multiplied (differential evolution always minimizes)
DIRECTIONS = {'minimize': 1., 'maximize': -1.}

# Rows of the `Optimization_Analysis` table which are passed to
# `scipy.optimize.differential_evolution`: name of the keyword argument, accepted types,
# options (if restricted) and description. Rows which are not specified use SciPy's defaults.
DE_SETTINGS = {
	'Maximum iterations': {
		'keyword': 'maxiter',
		'type': {int},
		'description': 'Maximum number of generations.'
	},
	'Population size': {
		'keyword': 'popsize',
		'type': {int},
		'description': 'Multiplier for the size of the population (the population has '
					   '"Population size" x number of parameters members).'
	},
	'Relative tolerance': {
		'keyword': 'tol',
		'type': {int, float},
		'description': 'Relative tolerance for convergence.'
	},
	'Absolute tolerance': {
		'keyword': 'atol',
		'type': {int, float},
		'description': 'Absolute tolerance for convergence.'
	},
	'Mutation': {
		'keyword': 'mutation',
		'type': {int, float, str},
		'description': 'Mutation constant, either a number or a range "min; max" (dithering).'
	},
	'Recombination': {
		'keyword': 'recombination',
		'type': {int, float},
		'description': 'Recombination constant (crossover probability).'
	},
	'Strategy': {
		'keyword': 'strategy',
		'type': {str},
		'description': 'Differential evolution strategy, e.g. "best1bin".'
	},
	'Initialization': {
		'keyword': 'init',
		'type': {str},
		'description': 'Initialization of the population, e.g. "latinhypercube", "sobol", '
					   '"halton" or "random".'
	},
	'Polish': {
		'keyword': 'polish',
		'type': {str},
		'options': {'True', 'False'},
		'description': 'If "True", the best member is polished with L-BFGS-B at the end of '
					   'the optimization.'
	},
	'Seed': {
		'keyword': 'seed',
		'type': {int},
		'description': 'Seed of the random number generator, for reproducible results.'
	},
	'Workers': {
		'keyword': 'workers',
		'type': {int},
		'description': 'Number of parallel processes used to evaluate the model (-1: all '
					   'available CPUs).'
	},
	'Updating': {
		'keyword': 'updating',
		'type': {str},
		'options': {'immediate', 'deferred'},
		'description': 'Update of the best member, either "immediate" (within a generation) '
					   'or "deferred" (once per generation). "deferred" is always used if '
					   '"Workers" is not 1.'
	},
}

def get_bounds(parameters: Dict[str, dict]) -> np.ndarray:
	'''Lower and upper bounds of the parameters which are optimized.

	Parameters
	----------
	parameters : dict
		Parameters which are optimized, as returned by
		:func:`~pyH2A.Utilities.Analysis_Utilities.analysis_utilities.process_parameters`.
		The two `Values` of each parameter are used as its bounds.

	Returns
	-------
	bounds : ndarray
		Array of shape (number of parameters, 2) containing the lower and upper bound of
		each parameter. Parameters are ordered by their `Index`, which is the order of the
		parameter values in the vector that is optimized.

	Raises
	------
	ValueError
		If a parameter does not have exactly two values or if its lower bound is not
		smaller than its upper bound.
	'''

	bounds = np.empty((len(parameters), 2))

	for name, parameter in parameters.items():
		values = np.sort(np.asarray(parameter['Values'], dtype = float))

		if values.shape != (2,):
			raise ValueError(f"Parameter '{name}' requires exactly two values (lower and upper bound), "
							 f"got {parameter['Values']}.")

		if not values[0] < values[1]:
			raise ValueError(f"Lower bound of parameter '{name}' has to be smaller than its upper bound, "
							 f"got {parameter['Values']}.")

		bounds[parameter['Index']] = values

	return bounds

def evaluate_dependent_variable(values: np.ndarray,
								parameters: Dict[str, dict],
								inp: dict,
								dependent_variable: dict) -> float:
	'''Run the pyH2A model with substituted parameter values and return the dependent variable.

	Parameters
	----------
	values : ndarray
		1D array of parameter values, ordered by the `Index` of the parameters.
	parameters : dict
		Parameters whose values are substituted, as returned by
		:func:`~pyH2A.Utilities.Analysis_Utilities.analysis_utilities.process_parameters`.
		An empty dictionary runs the model for the unmodified input (base case).
	inp : dict
		Input dictionary of the pyH2A model. It is not modified (the model is run on a copy).
	dependent_variable : dict
		Dependent variable, as returned by
		:func:`~pyH2A.Utilities.Analysis_Utilities.analysis_utilities.read_dependent_variable`.

	Returns
	-------
	value : float
		Value of the dependent variable in its specified unit.

	Raises
	------
	ValueError
		If the dependent variable is not a scalar.
	'''

	result = substitute_parameters_and_run(parameters, values, inp, dependent_variable)

	if np.ndim(result) != 0:
		raise ValueError(f"Dependent variable '{dependent_variable['Name']}' has to be a scalar to be "
						 f"optimized, got an array of shape {np.shape(result)}.")

	return float(result)

def optimization_objective(values: np.ndarray,
						   parameters: Dict[str, dict],
						   inp: dict,
						   dependent_variable: dict,
						   sign: float = 1.) -> float:
	'''Objective function which is minimized by differential evolution.

	Parameters
	----------
	values : ndarray
		1D array of parameter values, ordered by the `Index` of the parameters.
	parameters : dict
		Parameters which are optimized, as returned by
		:func:`~pyH2A.Utilities.Analysis_Utilities.analysis_utilities.process_parameters`.
	inp : dict
		Input dictionary of the pyH2A model. It is not modified (the model is run on a copy).
	dependent_variable : dict
		Dependent variable, as returned by
		:func:`~pyH2A.Utilities.Analysis_Utilities.analysis_utilities.read_dependent_variable`.
	sign : float, optional
		Factor with which the dependent variable is multiplied: 1 to minimize and -1 to
		maximize it (differential evolution always minimizes).

	Returns
	-------
	objective : float
		Dependent variable multiplied by `sign`. Non-finite results (e.g. NaN from a failed
		model evaluation) are returned as `inf`, so that they are never selected as optimum.
	'''

	objective = sign * evaluate_dependent_variable(values, parameters, inp, dependent_variable)

	if not np.isfinite(objective):
		return np.inf

	return objective

def get_effective_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
	'''Complete differential evolution settings with SciPy's default values.

	Parameters
	----------
	settings : dict
		Keyword arguments which are passed to ``scipy.optimize.differential_evolution``.

	Returns
	-------
	effective_settings : dict
		`settings` complemented by SciPy's default value for each keyword argument listed in
		``DE_SETTINGS`` which is not specified in `settings`.
	'''

	signature = inspect.signature(differential_evolution).parameters

	defaults = {setting['keyword']: signature[setting['keyword']].default
				for setting in DE_SETTINGS.values() if setting['keyword'] in signature}

	return {**defaults, **settings}

def perform_optimization(inp: dict,
						 parameters: Dict[str, dict],
						 dependent_variable: dict,
						 direction: str = 'minimize',
						 settings: Optional[Dict[str, Any]] = None,
						 evaluate_base_case: bool = True,
						 print_progress: bool = False) -> Dict[str, Any]:
	'''Optimize parameters of a pyH2A model using differential evolution.

	Parameters
	----------
	inp : dict
		Input dictionary of the pyH2A model (e.g. generated by
		:func:`~pyH2A.Utilities.input_modification.convert_input_to_dictionary`). It is not
		modified, each model evaluation uses a copy.
	parameters : dict
		Parameters which are optimized, as returned by
		:func:`~pyH2A.Utilities.Analysis_Utilities.analysis_utilities.process_parameters`.
		The two `Values` of each parameter are used as its bounds.
	dependent_variable : dict
		Dependent variable which is optimized, as returned by
		:func:`~pyH2A.Utilities.Analysis_Utilities.analysis_utilities.read_dependent_variable`.
		It has to be a scalar.
	direction : {'minimize', 'maximize'}, optional
		Direction of the optimization.
	settings : dict, optional
		Keyword arguments passed to ``scipy.optimize.differential_evolution`` (e.g. `maxiter`,
		`popsize`, `seed` or `workers`), except for `func`, `bounds`, `args` and `callback`,
		which are set by this function. Unspecified arguments use SciPy's defaults. If
		`workers` is not 1, `updating` is set to 'deferred' (required by SciPy for parallel
		evaluation).
	evaluate_base_case : bool, optional
		If True, the dependent variable is evaluated for the unmodified input (base case)
		before the optimization. Besides providing a reference value, this initialises objects
		which are cached on disk (e.g. by the LCA plugin) before parallel workers start.
	print_progress : bool, optional
		If True, the progress of the optimization is printed after each generation.

	Returns
	-------
	results : dict
		Results of the optimization with the following entries:

		- 'Direction' (str): direction of the optimization.
		- 'Optimal parameters' (dict): optimal value of each parameter, by parameter name.
		- 'Optimal value' (float): dependent variable at the optimum (in its unit).
		- 'Base case value' (float or None): dependent variable for the base case, None if
		  `evaluate_base_case` is False.
		- 'Success' (bool): whether the optimizer reports convergence.
		- 'Message' (str): termination message of the optimizer.
		- 'Generations' (int): number of generations (iterations) performed.
		- 'Function evaluations' (int): number of model evaluations by the optimizer
		  (including polishing, excluding the base case evaluation).
		- 'Run time' (float): run time in seconds (including the base case evaluation).
		- 'Settings' (dict): effective keyword arguments of the optimizer, including SciPy's
		  defaults for unspecified settings.
		- 'History' (list of dict): progress after each generation, with 'Generation',
		  'Function evaluations', 'Best value' and 'Convergence' (SciPy's convergence
		  measure, values of 1 or larger indicate convergence if the absolute tolerance
		  is 0).
		- 'Population' (ndarray or None): parameter values of the final population (one row
		  per member, columns ordered by parameter `Index`).
		- 'Population values' (ndarray or None): dependent variable of each member of the
		  final population.
		- 'Optimizer result' (OptimizeResult): result returned by
		  ``scipy.optimize.differential_evolution``. Its objective values are multiplied by
		  -1 if the dependent variable is maximized.

	Raises
	------
	ValueError
		If `direction` is not supported, if the bounds of a parameter are invalid or if the
		dependent variable is not a scalar.

	Notes
	-----
	This function can be used by other analysis modules, for example to optimize parameters
	for every sample of a Monte Carlo analysis. In that case, `workers` should be 1 (no
	nested parallelisation), `evaluate_base_case` can be set to False to avoid an additional
	model evaluation per call and `print_progress` should be False.
	'''

	if direction not in DIRECTIONS:
		raise ValueError(f"Direction '{direction}' is not supported, use one of {list(DIRECTIONS)}.")

	sign = DIRECTIONS[direction]
	bounds = get_bounds(parameters)
	unit = dependent_variable['Unit']

	settings = dict(settings) if settings is not None else {}

	# Parallel evaluation requires deferred updating (SciPy would otherwise override it with a warning)
	if settings.get('workers', 1) != 1:
		if settings.get('updating', 'deferred') != 'deferred':
			warnings.warn("'updating' is set to 'deferred', which is required if 'workers' is not 1.")
		settings['updating'] = 'deferred'

	history = []

	def record_generation(intermediate_result: OptimizeResult) -> None:
		'''Record (and optionally print) the progress after each generation.

		Parameters
		----------
		intermediate_result : OptimizeResult
			Intermediate result passed by ``scipy.optimize.differential_evolution`` after each
			generation (the parameter name is required by SciPy to pass the result).
		'''

		entry = {'Generation': int(intermediate_result.nit),
				 'Function evaluations': int(intermediate_result.nfev),
				 'Best value': sign * float(intermediate_result.fun),
				 'Convergence': float(intermediate_result.convergence)}

		history.append(entry)

		if print_progress:
			print(f"  Generation {entry['Generation']}: best value {entry['Best value']:.6g} {unit} "
				  f"({entry['Function evaluations']} function evaluations)")

	start = timer()

	base_case_value = None

	if evaluate_base_case:
		base_case_value = evaluate_dependent_variable(np.empty(0), {}, inp, dependent_variable)

	if print_progress:
		print(f"Optimization_Analysis: {direction} '{dependent_variable['Name']}' by varying "
			  f"{len(parameters)} parameter(s) with differential evolution...")
		if base_case_value is not None:
			print(f'  Base case: {base_case_value:.6g} {unit}')

	result = differential_evolution(optimization_objective,
									bounds,
									args = (parameters, inp, dependent_variable, sign),
									callback = record_generation,
									**settings)

	run_time = timer() - start

	population = result.get('population')
	population_values = None

	if population is not None:
		population_values = sign * np.asarray(result.population_energies, dtype = float)

	results = {
		'Direction': direction,
		'Optimal parameters': {name: float(result.x[parameter['Index']])
							   for name, parameter in parameters.items()},
		'Optimal value': sign * float(result.fun),
		'Base case value': base_case_value,
		'Success': bool(result.success),
		'Message': str(result.message),
		'Generations': int(result.nit),
		'Function evaluations': int(result.nfev),
		'Run time': run_time,
		'Settings': get_effective_settings(settings),
		'History': history,
		'Population': population,
		'Population values': population_values,
		'Optimizer result': result,
	}

	return results

def read_optimization_settings(optimization_table: Optional[Dict[str, Dict[str, Any]]]) -> Tuple[str, Dict[str, Any]]:
	'''Read direction and differential evolution settings from the `Optimization_Analysis` table.

	Parameters
	----------
	optimization_table : dict or None
		`Optimization_Analysis` table resolved by the input resolver, mapping row names to
		``{'Value': value}``. Rows which are not present use default values.

	Returns
	-------
	direction : str
		Direction of the optimization ('minimize' if not specified).
	settings : dict
		Keyword arguments for ``scipy.optimize.differential_evolution``, for all rows of
		``DE_SETTINGS`` which are specified. 'Polish' is converted to bool and a 'Mutation'
		range ("min; max") to a tuple.
	'''

	optimization_table = optimization_table or {}

	direction = deep_get(optimization_table, 'Direction', 'Value', default = 'minimize')

	settings = {}

	for row, setting in DE_SETTINGS.items():
		if row in optimization_table:
			settings[setting['keyword']] = optimization_table[row]['Value']

	if 'polish' in settings:
		settings['polish'] = settings['polish'] == 'True'

	if isinstance(settings.get('mutation'), str):
		settings['mutation'] = tuple(float(value) for value in
									 parse_parameter_to_array(settings['mutation'], delimiter = ';'))

	return direction, settings

def format_report_value(value: Any) -> Any:
	'''Convert a value to a single table cell of the optimization report.

	Parameters
	----------
	value : Any
		Value to be written into the report.

	Returns
	-------
	cell : int, float or str
		Numbers are returned as Python int or float, booleans and None as strings. Arrays,
		lists and tuples are returned as string of their elements separated by " ; ". Other
		values are converted to single-line strings without "|" (the column separator).
	'''

	if value is None or isinstance(value, (bool, np.bool_)):
		return str(value)

	elif isinstance(value, (int, np.integer)):
		return int(value)

	elif isinstance(value, (float, np.floating)):
		return float(value)

	elif isinstance(value, (list, tuple, np.ndarray)):
		elements = np.ravel(np.asarray(value, dtype = object))
		return ' ; '.join(str(format_report_value(element)) for element in elements)

	else:
		return ' '.join(str(value).replace('|', '/').split())

def generate_report(results: Dict[str, Any],
					parameters: Dict[str, dict],
					dependent_variable: dict,
					input_file: Optional[str] = None) -> Dict[str, Dict[str, Dict[str, Any]]]:
	'''Generate the optimization report as a dictionary of tables.

	Parameters
	----------
	results : dict
		Results of the optimization, as returned by :func:`perform_optimization`.
	parameters : dict
		Parameters which were optimized, as returned by
		:func:`~pyH2A.Utilities.Analysis_Utilities.analysis_utilities.process_parameters`.
	dependent_variable : dict
		Dependent variable which was optimized, as returned by
		:func:`~pyH2A.Utilities.Analysis_Utilities.analysis_utilities.read_dependent_variable`.
	input_file : str, optional
		Path to the input file of the optimization, listed in the report.

	Returns
	-------
	report : dict
		Report in the structure of a pyH2A input dictionary ({table: {row: {column: value}}})
		with the tables 'Optimization summary', 'Optimal parameters', 'Optimization settings',
		'Convergence history' (if at least one generation was performed) and 'Final population'
		(if provided by SciPy). It can be written with
		:class:`~pyH2A.Utilities.plugin_input_output_processing.Template_File` and read with
		:func:`~pyH2A.Utilities.input_modification.convert_file_to_dictionary`.
	'''

	unit = dependent_variable['Unit']
	optimal_value = results['Optimal value']
	base_case_value = results['Base case value']
	base_case_evaluations = 0 if base_case_value is None else 1
	model_evaluations = results['Function evaluations'] + base_case_evaluations

	if base_case_value is None:
		absolute_change = relative_change = 'n/a'
		base_case_value = 'n/a'
	else:
		absolute_change = optimal_value - base_case_value
		relative_change = absolute_change / abs(base_case_value) if base_case_value != 0 else 'n/a'

	summary = {
		'Input file': (input_file, 'Input file of the optimization'),
		'Date': (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'Date and time at which the report was generated'),
		'pyH2A version': (pyH2A_version, 'Version of pyH2A used for the optimization'),
		'SciPy version': (scipy.__version__, 'Version of SciPy used for the optimization'),
		'Optimizer': ('scipy.optimize.differential_evolution', 'Optimization algorithm'),
		'Dependent variable': (dependent_variable['Name'], 'Optimized dependent variable'),
		'Path to variable': (reverse_parameter_to_string(dependent_variable['Path']), 'Path to dependent variable in model'),
		'Variable unit': (unit, 'Unit of all values of the dependent variable in this report'),
		'Direction': (results['Direction'], 'Direction of the optimization'),
		'Optimal value': (optimal_value, 'Dependent variable at the optimum'),
		'Base case value': (base_case_value, 'Dependent variable for the base case (unmodified input)'),
		'Absolute change': (absolute_change, 'Optimal value minus base case value'),
		'Relative change': (relative_change, 'Absolute change divided by magnitude of base case value'),
		'Success': (results['Success'], 'Whether the optimizer reports convergence (see message)'),
		'Message': (results['Message'], 'Termination message of the optimizer'),
		'Generations': (results['Generations'], 'Number of generations (iterations) performed'),
		'Function evaluations': (results['Function evaluations'], 'Model evaluations by the optimizer (including polishing)'),
		'Base case evaluations': (base_case_evaluations, 'Model evaluations of the base case'),
		'Model evaluations': (model_evaluations, 'Total number of model evaluations'),
		'Run time': (results['Run time'], 'Total run time in seconds'),
		'Time per evaluation': (results['Run time'] / model_evaluations, 'Run time per model evaluation in seconds'),
	}

	summary_table = {row: {'Value': format_report_value(value), 'Comment': comment}
					 for row, (value, comment) in summary.items()}

	parameter_names = sorted(parameters, key = lambda name: parameters[name]['Index'])
	bounds = get_bounds(parameters)

	optimal_parameters_table = {}

	for name in parameter_names:
		lower, upper = bounds[parameters[name]['Index']]
		optimal = results['Optimal parameters'][name]

		optimal_parameters_table[name] = {
			'Parameter path': format_report_value(reverse_parameter_to_string(parameters[name]['Parameter'])),
			'Lower bound': format_report_value(lower),
			'Upper bound': format_report_value(upper),
			'Base case value': format_report_value(parameters[name]['Reference']),
			'Optimal value': format_report_value(optimal),
			'Relative position in bounds': format_report_value((optimal - lower) / (upper - lower)),
		}

	input_file_rows = {setting['keyword']: row for row, setting in DE_SETTINGS.items()}

	settings_table = {keyword: {'Value': format_report_value(value),
								'Input file row': input_file_rows.get(keyword, 'n/a')}
					  for keyword, value in results['Settings'].items()}

	report = {
		'Optimization summary': summary_table,
		'Optimal parameters': optimal_parameters_table,
		'Optimization settings': settings_table,
	}

	if len(results['History']) > 0:
		report['Convergence history'] = {
			f"Generation {entry['Generation']}": {
				'Function evaluations': format_report_value(entry['Function evaluations']),
				'Best value': format_report_value(entry['Best value']),
				'Convergence': format_report_value(entry['Convergence']),
			} for entry in results['History']
		}

	if results['Population'] is not None:
		population_values = np.asarray(results['Population values'], dtype = float)
		order = np.argsort(DIRECTIONS[results['Direction']] * population_values) # best member first

		population_table = {}

		for rank, member in enumerate(order, start = 1):
			row = {name: format_report_value(results['Population'][member][parameters[name]['Index']])
				   for name in parameter_names}
			row[dependent_variable['Name']] = format_report_value(population_values[member])
			population_table[f'Member {rank}'] = row

		report['Final population'] = population_table

	return report

class Optimization_Analysis:
	'''Optimization of pyH2A models using differential evolution.

	Parameters
	----------
	Dependent variable > [...] > Path to variable : str
		Path to the dependent variable which is optimized, in the format top key > middle key >
		bottom key (e.g. "Dependent Variables > Levelized cost > Value"). Only the first
		dependent variable in the table is optimized.
	Dependent variable > [...] > Variable unit : str
		Unit in which the dependent variable is optimized and reported.
	Optimization_Analysis > Direction > Value : str, optional
		Direction of the optimization, either "minimize" (default) or "maximize".
	Optimization_Analysis > Output File > Value : str, optional
		Path to the text file in which the optimization report is saved.
	Optimization_Analysis > Maximum iterations > Value : int, optional
		Maximum number of generations (`maxiter`, default: 1000).
	Optimization_Analysis > Population size > Value : int, optional
		Multiplier for the size of the population (`popsize`, default: 15). The population has
		"Population size" x number of parameters members.
	Optimization_Analysis > Relative tolerance > Value : float, optional
		Relative tolerance for convergence (`tol`, default: 0.01).
	Optimization_Analysis > Absolute tolerance > Value : float, optional
		Absolute tolerance for convergence (`atol`, default: 0).
	Optimization_Analysis > Mutation > Value : float or str, optional
		Mutation constant, either a number or a range "min; max" for dithering (`mutation`,
		default: "0.5; 1").
	Optimization_Analysis > Recombination > Value : float, optional
		Recombination constant (`recombination`, default: 0.7).
	Optimization_Analysis > Strategy > Value : str, optional
		Differential evolution strategy (`strategy`, default: "best1bin").
	Optimization_Analysis > Initialization > Value : str, optional
		Initialization of the population (`init`, default: "latinhypercube").
	Optimization_Analysis > Polish > Value : str, optional
		"True" (default) or "False". If "True", the best member is polished with L-BFGS-B at
		the end of the optimization (`polish`).
	Optimization_Analysis > Seed > Value : int, optional
		Seed of the random number generator, for reproducible results (`seed`).
	Optimization_Analysis > Workers > Value : int, optional
		Number of parallel processes used to evaluate the model, -1 uses all available CPUs
		(`workers`, default: 1).
	Optimization_Analysis > Updating > Value : str, optional
		"immediate" or "deferred" update of the best member (`updating`). Defaults to
		"immediate" for one worker, "deferred" is always used for multiple workers.
	Parameters - Optimization_Analysis > [...] > Parameter path : str
		Path to the parameter which is optimized, in the format top key > middle key > bottom
		key (without braces and unit, the parameter is adjusted directly in place).
	Parameters - Optimization_Analysis > [...] > Values : str
		Bounds of the parameter in the format "lower; upper" (order is irrelevant). Instead of
		a number, "Base" or "Reference" can be used to retrieve the base value of the parameter.

	Attributes
	----------
	input_file : str
		Path to the input file.
	inp : dict
		Input dictionary generated from the input file.
	inp_resolved : dict
		Input of the analysis module, resolved by the input resolver.
	dependent_variable : dict
		Dependent variable which is optimized (see
		:func:`~pyH2A.Utilities.Analysis_Utilities.analysis_utilities.read_dependent_variable`).
	parameters : dict
		Parameters which are optimized (see
		:func:`~pyH2A.Utilities.Analysis_Utilities.analysis_utilities.process_parameters`).
	direction : str
		Direction of the optimization.
	settings : dict
		Settings for ``scipy.optimize.differential_evolution`` specified in the input file.
	results : dict
		Results of the optimization (see :func:`perform_optimization`).

	Notes
	-----
	The optimization settings in the `Optimization_Analysis` table are passed to
	``scipy.optimize.differential_evolution`` (keyword argument in parentheses), unspecified
	settings use SciPy's defaults. Before the optimization, the dependent variable is
	evaluated for the base case. The results are printed and, if an output file is specified,
	a report is saved (see :func:`generate_report`). The convergence of the optimization can be
	plotted with :meth:`plot_convergence`.
	'''

	def __init__(self, input_file: str, run: bool = True) -> None:
		'''Set up the analysis module and perform the optimization.

		Parameters
		----------
		input_file : str
			Path to the input file.
		run : bool, optional
			If True, the optimization is performed. If False, only the input specification
			(`input_dict`) is set up.
		'''

		self._set_up()
		if run:
			self._run(input_file)

	def _set_up(self) -> None:
		'''Define the input specification (`input_dict`) of the analysis module.
		'''

		optimization_table = {
			'Direction': {
				'Value': {
					'type': {str},
					'options': set(DIRECTIONS),
				},
				'optional': True,
				'description': 'Direction of the optimization, either "minimize" (default) or "maximize".'
			},
			'Output File': {
				'Value': {
					'type': {str},
				},
				'optional': True,
				'description': 'Path to the text file in which the optimization report is saved.'
			},
		}

		for row, setting in DE_SETTINGS.items():
			value_specification = {'type': setting['type']}

			if 'options' in setting:
				value_specification['options'] = setting['options']

			optimization_table[row] = {
				'Value': value_specification,
				'optional': True,
				'description': f"{setting['description']} (`{setting['keyword']}` of "
							   'scipy.optimize.differential_evolution, default value is used if not specified).'
			}

		self.input_dict = {
			'Dependent variable': {
				'<...>': {
					'Path to variable': {
						'type': {str},
					},
					'Variable unit': {
						'type': {str},
					},
					'description': 'The dependent variable to be optimized, e.g. levelized cost or kg[CO2-eq]/kg[H2]. '
								   '"Path to variable": path to the dependent variable (top key > middle key > bottom key). '
								   '"Variable unit": unit in which the dependent variable is optimized and reported. '
								   'Only the first dependent variable is optimized.'
				}
			},
			'Optimization_Analysis': optimization_table,
			'Parameters - Optimization_Analysis': {
				'<...>': {
					'Parameter path': {
						'type': {str},
					},
					'Values': {
						'type': {str},
					},
					'description': 'The parameters to be optimized. '
								   '"Parameter path": path to the parameter in the input file (without braces and units '
								   'since the parameter is adjusted directly in place). '
								   '"Values": bounds of the parameter, specified in the format "lower; upper" (order is '
								   'irrelevant). Instead of actual values, "Base" or "Reference" can be used to retrieve '
								   'the base value of the parameter in the input file as one of the bounds. E.g. "Base; 3000".'
				}
			}
		}

	def _run(self, input_file: str) -> None:
		'''Read the input file, perform the optimization, print the results and save the report.

		Parameters
		----------
		input_file : str
			Path to the input file.
		'''

		self.input_file = input_file
		self.inp = convert_input_to_dictionary(input_file)
		self.inp_resolved = input_resolver_function(self.input_dict, Inp_Wrapper(self.inp), 'Optimization_Analysis')

		self.check_input_tables()

		# Set color and display name for plotting (based on 'Display Parameters' table in input file, if specified)
		self.color = deep_get(self.inp, 'Display Parameters', 'Color', 'Value', default = 'darkgreen')
		self.display_name = deep_get(self.inp, 'Display Parameters', 'Name', 'Value', default = 'Model')

		self.dependent_variable = read_dependent_variable(self.inp_resolved['Dependent variable'],
														  keys = ['Path to variable', 'Variable unit'])
		self.parameters = process_parameters(self.inp_resolved['Parameters - Optimization_Analysis'],
											 self.inp,
											 keys = ['Parameter path', 'Values'])
		self.direction, self.settings = read_optimization_settings(self.inp_resolved.get('Optimization_Analysis'))

		self.results = perform_optimization(self.inp,
											self.parameters,
											self.dependent_variable,
											direction = self.direction,
											settings = self.settings,
											print_progress = True)

		self.print_results()

		output_file = deep_get(self.inp_resolved, 'Optimization_Analysis', 'Output File', 'Value')

		if output_file is not None:
			self.save_results(output_file)

	def check_input_tables(self) -> None:
		'''Check the input tables for errors which are not detected by the input resolver.

		Raises
		------
		ValueError
			If the `Optimization_Analysis` table contains unknown rows (which would otherwise
			be silently ignored, e.g. in case of a typo), if no parameters are specified or if
			the `Values` of a parameter do not contain exactly two entries.

		Notes
		-----
		A warning is issued if more than one dependent variable is specified, since only the
		first one is optimized.
		'''

		known_rows = self.input_dict['Optimization_Analysis']
		unknown_rows = [row for row in self.inp.get('Optimization_Analysis', {}) if row not in known_rows]

		if len(unknown_rows) > 0:
			raise ValueError(f"[Optimization_Analysis] Unknown row(s) {unknown_rows} in 'Optimization_Analysis' table. "
							 f"Supported rows are: {list(known_rows)}.")

		parameters_table = self.inp_resolved['Parameters - Optimization_Analysis']

		if len(parameters_table) == 0:
			raise ValueError("[Optimization_Analysis] No parameters specified in 'Parameters - Optimization_Analysis' table.")

		for name, row in parameters_table.items():
			if len(parse_parameter(row['Values'], delimiter = ';')) != 2:
				raise ValueError(f"[Optimization_Analysis] 'Values' of parameter '{name}' has to contain exactly two "
								 f"entries (lower and upper bound) separated by ';', got '{row['Values']}'.")

		dependent_variables = list(self.inp_resolved['Dependent variable'])

		if len(dependent_variables) > 1:
			warnings.warn(f"[Optimization_Analysis] Only the first dependent variable ('{dependent_variables[0]}') "
						  f"is optimized, {dependent_variables[1:]} are ignored.")

	def print_results(self) -> None:
		'''Print a summary of the optimization results.
		'''

		results = self.results
		unit = self.dependent_variable['Unit']
		separator = '-' * 80

		print('Optimization results:')
		print(separator)

		for name, parameter in self.parameters.items():
			lower, upper = parameter['Values']
			print(f"{name} ({reverse_parameter_to_string(parameter['Parameter'])}): "
				  f"optimal value is {results['Optimal parameters'][name]:.6g} "
				  f"(bounds: {lower} - {upper}, base case: {parameter['Reference']})")

		print(f"Optimal {self.dependent_variable['Name']}: {results['Optimal value']:.6g} {unit} ({results['Direction']})")

		if results['Base case value'] is not None:
			print(f"Base case {self.dependent_variable['Name']}: {results['Base case value']:.6g} {unit}")

		print(f"Generations: {results['Generations']}, function evaluations: {results['Function evaluations']}, "
			  f"run time: {results['Run time']:.1f} s")
		print(f"Optimizer message: {results['Message']}")
		print(separator)

	def save_results(self, file_name: str) -> None:
		'''Save the optimization report to `file_name`.

		Parameters
		----------
		file_name : str
			Path to the file in which the report is saved.

		Notes
		-----
		The report (see :func:`generate_report`) is written as Markdown tables in the format of
		pyH2A input files, so that it can be read with
		:func:`~pyH2A.Utilities.input_modification.convert_file_to_dictionary`.
		'''

		report = generate_report(self.results,
								 self.parameters,
								 self.dependent_variable,
								 input_file = self.input_file)

		Template_File(report).write_template_file(file_name)

		print(f'Optimization report saved to {file_name}')

	def plot_convergence(self,
						 ax: Optional[Axes] = None,
						 figure_lean: bool = True,
						 xlabel_string: str = 'Generation',
						 ylabel_string: Optional[str] = None,
						 show_base_case: bool = True,
						 legend_loc: str = 'best',
						 plot_kwargs: Optional[Dict[str, Any]] = None,
						 **kwargs: Any) -> Optional[Figure]:
		'''Plot the best value of the dependent variable after each generation.

		Parameters
		----------
		ax : matplotlib.axes.Axes, optional
			Axes object in which the plot is drawn. Default is None, creating a new plot.
		figure_lean : bool, optional
			If `figure_lean` is True and `ax` is None, the figure is shown and/or saved (as
			specified by `show` and `save` in `kwargs`) and returned.
		xlabel_string : str, optional
			String for x axis label.
		ylabel_string : str, optional
			String for y axis label. Defaults to name and unit of the dependent variable.
		show_base_case : bool, optional
			If True, the dependent variable for the base case is shown as dashed line.
		legend_loc : str, optional
			Location of the legend.
		plot_kwargs : dict, optional
			Dictionary containing optional keyword arguments for
			:func:`~pyH2A.Utilities.output_utilities.Figure_Lean`, has priority over `**kwargs`.
		**kwargs : Any
			Additional `kwargs` passed to
			:func:`~pyH2A.Utilities.output_utilities.Figure_Lean`.

		Returns
		-------
		figure : matplotlib.figure.Figure or None
			Figure, if `figure_lean` is True and `ax` is None.
		'''

		kwargs = {**{'left': 0.17, 'right': 0.95, 'bottom': 0.13, 'top': 0.95,
					 'fig_width': 6.4, 'fig_height': 4.0, 'font_size': 12,
					 'name': 'Optimization_Convergence', 'directory': '.'},
				  **kwargs, **(plot_kwargs or {})}

		create_figure = ax is None

		if create_figure:
			figure = Figure_Lean(**kwargs)
			ax = figure.ax

		generations = [entry['Generation'] for entry in self.results['History']]
		best_values = [entry['Best value'] for entry in self.results['History']]

		ax.plot(generations, best_values, color = self.color, linewidth = 2, marker = 'o',
				markersize = 4, label = f'Best value ({self.display_name})')

		if show_base_case and self.results['Base case value'] is not None:
			ax.axhline(self.results['Base case value'], color = 'grey', linestyle = '--',
					   linewidth = 1.5, label = 'Base case')

		if ylabel_string is None:
			ylabel_string = f"{self.dependent_variable['Name']}\n/ {self.dependent_variable['Unit']}"

		ax.set_xlabel(xlabel_string)
		ax.set_ylabel(ylabel_string)
		ax.xaxis.set_major_locator(mticker.MaxNLocator(integer = True))
		ax.grid(color = 'grey', linestyle = '--', linewidth = 0.2, zorder = 0)
		ax.legend(loc = legend_loc)

		if create_figure and figure_lean:
			figure.execute()
			return figure.fig

		return None
