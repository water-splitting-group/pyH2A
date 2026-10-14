'''Monte Carlo analysis of a pyH2A model: selected input parameters are varied randomly between
their base and limit values, the dependent variable (e.g. levelized cost or a life cycle impact)
is calculated for each sample and the results are analyzed with respect to a target range of the
dependent variable (development distance analysis).
'''

from __future__ import annotations

import os
import json
import warnings
import concurrent.futures 
from datetime import datetime
from pathlib import Path
from timeit import default_timer as timer

import numpy as np
from scipy.signal import savgol_filter
from scipy.spatial import distance as scipy_distance
from scipy.stats import norm as normal_distribution
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from pyH2A import __version__
from pyH2A.Utilities.IO import input_resolver_function
from pyH2A.Utilities.Unit_Handler import Quantity
from pyH2A.Utilities.input_modification import (convert_input_to_dictionary,
												deep_get,
												Inp_Wrapper)

from pyH2A.Utilities.Analysis_Utilities.analysis_utilities import (select_non_reference_value,
																   read_dependent_variable,
																   dependent_variable_label,
																   process_parameters,
																   substitute_parameters_and_run)

from pyH2A.Utilities.output_utilities import (make_bold, 
											  dynamic_value_formatting, 
											  insert_image, 
											  Figure_Lean)

# Version of the layout of Monte Carlo results files (see `write_results_file`)
RESULTS_FILE_FORMAT_VERSION = 1

def _mc_response_worker(values: np.ndarray,
						inp: dict,
						parameters: dict,
						dependent_variable: dict) -> np.ndarray:
	'''Evaluate the model for each set of parameter values (executed in worker processes).

	Parameters
	----------
	values : np.ndarray
		2D array, each row containing one set of parameter values.
	inp : dict
		Input dictionary of the model.
	parameters : dict
		Varied parameters, see
		:func:`~pyH2A.Utilities.Analysis_Utilities.analysis_utilities.process_parameters`.
	dependent_variable : dict
		Dependent variable, see
		:func:`~pyH2A.Utilities.Analysis_Utilities.analysis_utilities.read_dependent_variable`.

	Returns
	-------
	np.ndarray
		1D array with the dependent variable for each row of `values`.
	'''

	response_values = []

	# Iterating over each 1D array of parameter values in 2D `values` array
	for value_array in values:
		result = substitute_parameters_and_run(parameters, 
											   value_array,
											   inp, 
											   dependent_variable)
		response_values.append(result)

	return np.asarray(response_values)

def normalize_parameter(parameter: float | np.ndarray,
						base: float,
						limit: float,
						log_normalize: bool = False) -> float | np.ndarray:
	'''Linear or log normalization of parameter based on base and limit values.

	Parameters
	----------
	parameter : float or np.ndarray
		Parameter value(s) to be normalized.
	base : float
		Base value, which is normalized to 0.
	limit : float
		Limit value, which is normalized to 1.
	log_normalize : bool, optional
		If True, log normalization is used instead of linear normalization.

	Returns
	-------
	float or np.ndarray
		Normalized parameter value(s).
	'''

	if log_normalize:
		ratio = limit / base
		parameter_ratio = parameter / base
		scaled = np.log10(parameter_ratio) / np.log10(ratio)

	else:
		range_covered = limit - base
		scaled = (parameter - base) / range_covered

	return scaled

def calculate_distance(data: np.ndarray,
					   parameters: dict,
					   selection: list[str],
					   metric: str = 'cityblock',
					   log_normalize: bool = False,
					   sum_distance: bool = False) -> np.ndarray:
	'''Distance of datapoints to reference is calculated using the specified metric.

	Parameters
	----------
	data : np.ndarray
		2D array of datapoints containing parameter values for each model.
	parameters : dict
		Dictionary specifying "Index", "Reference" and "Limit" for each parameter.
	selection : list[str]
		List of parameters names used for distance calculation.
	metric : str, optional
		Metric used for distance calculation (e.g. 'cityblock' or
		'euclidean'). Default is 'cityblock'.
	log_normalize : bool, optional
		Flag to control if log normalization is used instead of linear normalization.
	sum_distance : bool, optional
		Flag to control if distance is calculated by simply summing individual 
		normalized values (equal to cityblock distance but without using absolute values,
		hence distance can be negative).

	Returns
	-------
	distances : np.ndarray
		1D array containing distance for each model.

	Notes
	-----
	Parameter ranges and the reference parameters are scaled to be within 
	a n-dimensional unit cube.
	Distances are normalized by the number of dimensions, so that the maximum 
	distance is always 1.
	'''

	number_of_parameters = len(selection)

	reference = []
	data_scaled = np.empty((len(data), number_of_parameters))

	for counter, key in enumerate(selection):
		idx = parameters[key]['Index']
		data_scaled[:,counter] = normalize_parameter(data[:,idx], parameters[key]['Reference'],
													 parameters[key]['Limit'], 
													 log_normalize = log_normalize)
		reference.append(normalize_parameter(parameters[key]['Reference'], parameters[key]['Reference'],
											 parameters[key]['Limit'],
											 log_normalize = log_normalize))
										
	reference_scaled = np.array([reference])

	if sum_distance:
		distances = np.sum(data_scaled, axis = 1)
	else:
		distances = scipy_distance.cdist(data_scaled, reference_scaled, metric = metric)[:,0]

	if metric == 'cityblock':
		distances = distances / number_of_parameters
	else:
		distances = distances / np.sqrt(number_of_parameters)

	return distances

def extend_limits(limits_original: np.ndarray, extension: float) -> np.ndarray:
	'''Extend limits in both directions by a fraction of their range.

	Parameters
	----------
	limits_original : np.ndarray
		Lower and upper limit.
	extension : float
		Fraction of the range (upper - lower limit) by which each limit is extended.

	Returns
	-------
	np.ndarray
		Extended lower and upper limit.
	'''

	limits = np.copy(limits_original)

	limit_range = limits[1] - limits[0]

	limits[0] -= extension * limit_range
	limits[1] += extension * limit_range

	return limits

def coordinate_position(x_reference: float,
						x_values: np.ndarray,
						y_reference: float,
						y_values: np.ndarray) -> tuple[float, float]:
	'''Determine position (in axes fraction coordinates) of the base case label in
	:meth:`Monte_Carlo_Analysis.plot_colored_scatter`.

	Parameters
	----------
	x_reference : float
		Reference value of the parameter on the x axis.
	x_values : np.ndarray
		Value range of the parameter on the x axis.
	y_reference : float
		Reference value of the parameter on the y axis.
	y_values : np.ndarray
		Value range of the parameter on the y axis.

	Returns
	-------
	xtext : float
		x position of the label.
	ytext : float
		y position of the label.
	'''

	if x_reference - select_non_reference_value(x_reference, x_values) > 0:
		xtext = 0.81
	else:
		xtext = 0.05

	if y_reference - select_non_reference_value(y_reference, y_values) > 0:
		ytext = 0.93
	else:
		ytext = 0.1

	return xtext, ytext

def _savgol_parameters(samples: int,
					   reduction_factor: int,
					   poly_order: int) -> tuple[int, int]:
	'''Window length and polynomial order for the Savitzky-Golay filter.

	Parameters 
	----------
	samples : int
		Number of datapoints to be filtered.
	reduction_factor : int
		The window length is approximately `samples` / `reduction_factor`.
	poly_order : int
		Requested order of the polynomial.

	Returns
	-------
	window_length : int
		Odd window length, larger than the polynomial order (if possible) and
		not larger than `samples`.
	poly_order : int
		Polynomial order, reduced if required by the window length.
	'''

	window_length = min(max(int(samples / reduction_factor), poly_order + 1), samples)

	if window_length % 2 == 0:
		window_length = window_length + 1 if window_length < samples else window_length - 1

	return window_length, min(poly_order, window_length - 1)

def _check_results_path(file_name: str | os.PathLike) -> Path:
	'''Return `file_name` as Path, ensuring that it refers to a NumPy ``.npz`` file.

	Parameters
	----------
	file_name : str or os.PathLike
		Path to Monte Carlo results file.

	Returns
	-------
	Path
		Path to Monte Carlo results file.

	Raises
	------
	ValueError
		If `file_name` does not have the suffix ``.npz``.
	'''

	path = Path(file_name)

	if path.suffix != '.npz':
		raise ValueError(f'Monte Carlo results file "{path}" has to be a NumPy ".npz" file. '
						 'Results saved in the text format of previous pyH2A versions cannot be read and have to be recomputed.')

	return path

def write_results_file(file_name: str | os.PathLike,
					   parameter_values: np.ndarray,
					   dependent_variable_values: np.ndarray,
					   metadata: dict) -> None:
	'''Write Monte Carlo results and their metadata to a NumPy ``.npz`` file.

	Parameters
	----------
	file_name : str or os.PathLike
		Path to results file (suffix ``.npz``). Missing directories are created.
	parameter_values : np.ndarray
		2D array of sampled parameter values with shape (samples, parameters).
	dependent_variable_values : np.ndarray
		1D array with the dependent variable for each sample.
	metadata : dict
		JSON serializable metadata, see
		:meth:`Monte_Carlo_Analysis.save_results` for its content.

	Notes
	-----
	The file contains the arrays ``parameter_values`` and ``dependent_variable_values``
	and the JSON string ``metadata``. It can be read with :func:`read_results_file` or with
	``numpy.load(file_name)`` and ``json.loads(data['metadata'].item())``. The file is
	first written to a temporary file, so that an existing file is never left incomplete.
	'''

	path = _check_results_path(file_name)
	path.parent.mkdir(parents = True, exist_ok = True)

	temporary_path = path.with_name(f'{path.name}.{os.getpid()}.tmp.npz')

	try:
		np.savez(temporary_path,
				 parameter_values = np.asarray(parameter_values, dtype = float),
				 dependent_variable_values = np.asarray(dependent_variable_values, dtype = float),
				 metadata = np.array(json.dumps(metadata, indent = 4)))
		os.replace(temporary_path, path)
	except BaseException:
		temporary_path.unlink(missing_ok = True)
		raise

def read_results_file(file_name: str | os.PathLike) -> tuple[np.ndarray, np.ndarray, dict]:
	'''Read Monte Carlo results written by :func:`write_results_file`.

	Parameters
	----------
	file_name : str or os.PathLike
		Path to results file (suffix ``.npz``).

	Returns
	-------
	parameter_values : np.ndarray
		2D array of sampled parameter values with shape (samples, parameters).
	dependent_variable_values : np.ndarray
		1D array with the dependent variable for each sample.
	metadata : dict
		Metadata of the results (see :meth:`Monte_Carlo_Analysis.save_results`).

	Raises
	------
	ValueError
		If the file does not have the suffix ``.npz``, was written with an unsupported
		file format version or its arrays do not match its metadata.
	'''

	path = _check_results_path(file_name)

	with np.load(path, allow_pickle = False) as data:
		parameter_values = data['parameter_values']
		dependent_variable_values = data['dependent_variable_values']
		metadata = json.loads(data['metadata'].item())

	if metadata.get('File format version') != RESULTS_FILE_FORMAT_VERSION:
		raise ValueError(f'Monte Carlo results file "{path}" has file format version {metadata.get("File format version")}, '
						 f'only version {RESULTS_FILE_FORMAT_VERSION} is supported.')

	if (parameter_values.shape != (metadata['Samples'], len(metadata['Parameters'])) or
		dependent_variable_values.shape != (metadata['Samples'],)):
		raise ValueError(f'Shapes of the results in "{path}" (parameter values: {parameter_values.shape}, dependent variable: '
						 f'{dependent_variable_values.shape}) do not match its metadata ({metadata["Samples"]} samples, '
						 f'{len(metadata["Parameters"])} parameters).')

	return parameter_values, dependent_variable_values, metadata

class Monte_Carlo_Analysis:
	'''Monte Carlo analysis of a techno-economic and/or life cycle assessment model.

	Parameters
	----------
	Dependent variable > [...] > Path to variable : str
		Path to the dependent variable in the processed input, e.g. "Dependent Variables > Levelized cost > Value".
		The row name is the name of the dependent variable (used for plotting). Only the first row is used.
	Dependent variable > [...] > Variable unit : str
		Unit in which the dependent variable is analyzed and displayed, e.g. "USD/kg[H2]".
	Dependent variable > [...] > Target range : str
		Target range of the dependent variable in "Variable unit", specified as "lower; upper", e.g. "1.5; 1.6".
	Monte_Carlo_Analysis > Samples > Value : int, optional
		Number of samples. Required if new results are computed (no "Input File").
	Monte_Carlo_Analysis > Random seed > Value : int, optional
		Seed for the random number generator. If not specified, a seed is drawn and stored in the results file.
	Monte_Carlo_Analysis > Output File > Value : str, optional
		Path to ".npz" file in which newly computed results are saved.
	Monte_Carlo_Analysis > Input File > Value : str, optional
		Path to ".npz" file with previously computed results, which are read instead of computing new results.
		Takes precedence over "Output File".
	Parameters - Monte_Carlo_Analysis > [...] > Parameter path : str
		Path to the varied parameter in the input file ("Table > Row > Column", without braces and unit).
		The row name is the display name of the parameter (including its unit, e.g. "PV efficiency / -").
	Parameters - Monte_Carlo_Analysis > [...] > Type : str {'value', 'factor'}
		If "value", sampled values replace the base value of the parameter. If "factor",
		sampled values are multiplied with the base value.
	Parameters - Monte_Carlo_Analysis > [...] > Values : str
		Value range as "value; value" (order is irrelevant), consisting of the base value ("Base" or
		"Reference", which is 1 for "factor" parameters) and the limit value, e.g. "Base; 0.3".

	Attributes
	----------
	inp : dict
		Input dictionary of the model.
	dependent_variable : dict
		Dependent variable ("Name", "Path", "Unit" and "Target range").
	target_range : np.ndarray
		Sorted target range of the dependent variable.
	parameters : dict
		Varied parameters keyed by their display name, see
		:func:`~pyH2A.Utilities.Analysis_Utilities.analysis_utilities.process_parameters`.
	samples : int
		Number of samples.
	random_seed : int
		Seed used to generate the parameter values.
	values : np.ndarray
		Sampled parameter values with shape (samples, parameters), columns in table order.
	results : np.ndarray
		`values` with the dependent variable as additional last column.
	metadata : dict
		Metadata saved with (or read from) the results file.
	target_range_data : np.ndarray
		Rows of `results` with a dependent variable within the target range, sorted by the dependent variable.
	distances : np.ndarray
		Development distances of `target_range_data`.

	Notes
	-----
	If "Input File" is specified, previously computed results are read from it. Otherwise,
	"Samples" parameter value sets are drawn (uniform distribution within each value range, see
	:meth:`generate_random_values`), the model is evaluated for each set (in parallel) and the results
	are saved in "Output File" (see :meth:`save_results`).

	The order of the parameters determines their mapping in plots (e.g. in :meth:`plot_colored_scatter`
	the first parameter is shown on the x axis, the second on the y axis and the third as color).
	Parameters can be renamed and reordered and the target range can be changed without recomputing
	the results (see :meth:`read_results`).

	For all samples within the target range, the development distance is calculated, which is the
	normalized distance of the sample's parameter values from the base values (see
	:func:`calculate_distance`).
	'''

	def __init__(self, input_file: str, run: bool = True) -> None:
		'''Set up the analysis and, if `run` is True, perform it for `input_file`.

		Parameters
		----------
		input_file : str
			Path to input file.
		run : bool, optional
			If True, the analysis is performed.
		'''

		self._set_up()
		if run:
			self._run(input_file)

	def _set_up(self) -> None:
		'''Define the input requested by the analysis (`input_dict`).'''

		self.input_dict = {
			'Dependent variable': {
				'<...>': {
					'Path to variable': {
						'type': {str},
					},
					'Variable unit': {
						'type': {str},
					},
					'Target range': {
						'type': {str}
					},
					'description': 'The dependent variable to be analyzed, e.g. levelized cost or kg[CO2-Eq]/kg[H2]. The row name is '
								   'the name of the dependent variable, which is used for plotting together with its unit. '
								   '"Path to variable": path to the dependent variable in the processed input, e.g. '
								   '"Dependent Variables > Levelized cost > Value". "Variable unit": unit in which the dependent variable '
								   'is analyzed and displayed. "Target range": target range of the dependent variable in its unit, '
								   'specified as "lower; upper" (e.g. "1.5; 1.6"). Only the first row is used.'
				}
			},
			'Monte_Carlo_Analysis': {
				'Samples': {
					'Value': {
						'type': {int}
					},
					'optional': True,
					'description': 'The number of samples to be generated for the Monte Carlo analysis. '
								   'Required if new results are computed (i.e. if no "Input File" is specified).'
				},
				'Random seed': {
					'Value': {
						'type': {int}
					},
					'optional': True,
					'description': 'Seed for the random number generator, which makes the sampled parameter values reproducible. '
								   'If not specified, a seed is drawn and stored in the results file.'
				},
				'Output File': {
					'Value': {
						'type': {str}
					},
					'optional': True,
					'description': 'Path to location of ".npz" file in which newly computed Monte Carlo analysis results are saved. '
								   'Either "Output File" or "Input File" must be specified.'
				},
				'Input File': {
					'Value': {
						'type': {str}
					},
					'optional': True,
					'description': 'Path to location of ".npz" file containing already computed Monte Carlo analysis results, which '
								   'are read instead of computing new results (takes precedence over "Output File"). '
								   'Either "Output File" or "Input File" must be specified.'
				}
			},
			'Parameters - Monte_Carlo_Analysis': {
				'<...>': {
					'Parameter path': {
						'type': {str},
					},
					'Type': {
						'type': {str},
						'options': {'value', 'factor'},
					},
					'Values': {
						'type': {str},
					},
					'description': 'The parameters to be varied in the Monte Carlo analysis. The row name is the display name of the '
								   'parameter (including its unit, e.g. "PV efficiency / -"), which is used for plotting. '
								   '"Parameter path": the path to the parameter in the input file is specified (without braces and units '
								   'since the parameter is adjusted directly in place). '
								   '"Type": the type of the parameter is specified as either "value" or "factor". '
								   'If "Type" is "value", provided values are used as is. If "Type" is "factor", '
								   'provided values are multiplied with the base value of the parameter in the input file. '
								   '"Values": value range for parameter in Monte Carlo analysis. Specified in following format: '
								   'upper limit; lower limit (order is irrelevant). One of the values has to be the base value, '
								   'for which "Base" or "Reference" can be used (for "factor" parameters, the base value is 1). '
								   'E.g. "Base; 20%".'
				}
			}
		}

	def _run(self, input_file: str) -> None:
		'''Perform the Monte Carlo analysis for `input_file`.

		Parameters
		----------
		input_file : str
			Path to input file.

		Raises
		------
		KeyError
			If new results are computed and "Samples" or "Output File" are not specified.

		Notes 
		-----
		The dependent variable and the parameters are read from the input file. If "Input File"
		is specified in the Monte_Carlo_Analysis table, previously computed results are read from
		it (:meth:`read_results`). Otherwise, the Monte Carlo simulation is performed
		(:meth:`perform_full_monte_carlo`) and the results are saved in "Output File"
		(:meth:`save_results`). Subsequently, the samples within the target range are selected
		and development distances are calculated.
		'''

		self.input_file = input_file
		self.inp = convert_input_to_dictionary(input_file)
		self.inp_resolved = input_resolver_function(self.input_dict, Inp_Wrapper(self.inp), 'Monte_Carlo_Analysis')
		settings = self.inp_resolved.get('Monte_Carlo_Analysis', {})

		# Set color and display name for plotting (based on 'Display Parameters' table in input file, if specified)
		self.color = deep_get(self.inp, 'Display Parameters', 'Color', 'Value', default = 'darkgreen')
		self.display_name = deep_get(self.inp, 'Display Parameters', 'Name', 'Value', default = 'Model')

		self.dependent_variable = read_dependent_variable(self.inp_resolved['Dependent variable'],
														  keys = ['Path to variable', 'Variable unit', 'Target range'])
		self.dependent_variable['Target range'] = np.sort(self.dependent_variable['Target range'])
		self.target_range = self.dependent_variable['Target range']

		self.parameters = process_parameters(self.inp_resolved['Parameters - Monte_Carlo_Analysis'],
											 self.inp,
											 keys = ['Parameter path', 'Type', 'Values'])
		self.check_parameter_definitions()
		self.determine_principal_components()

		# If 'Input File' is specified, previously computed results are read
		if 'Input File' in settings:
			self.read_results(settings['Input File']['Value'])

		# Otherwise, the Monte Carlo simulation is performed and its results are saved in 'Output File'
		else:
			for key in ['Samples', 'Output File']:
				if key not in settings:
					raise KeyError(f'"Monte_Carlo_Analysis > {key}" has to be specified to compute Monte Carlo results '
								   '(alternatively, existing results can be read by specifying an "Input File").')

			_check_results_path(settings['Output File']['Value']) # Checking file name before running the simulation

			self.perform_full_monte_carlo(self.inp,
										  settings['Samples']['Value'],
										  deep_get(settings, 'Random seed', 'Value'))
			self.save_results(settings['Output File']['Value'])

		# Check integrity of parameters in Monte Carlo results,
		# select datapoints within target range and calculate development distances
		self.check_parameter_integrity(self.values)
		self.target_range_components()
		self.development_distance()
		self.full_distance_cost_relationship()

	def check_parameter_definitions(self) -> None:
		'''Check the target range and the parameter definitions before results are computed or read.

		Raises
		------
		ValueError
			If the target range does not consist of two values, if a parameter path is used
			more than once or if the value range of a parameter does not consist of its base
			value and one limit value.
		'''

		if len(self.target_range) != 2:
			raise ValueError(f'Target range of "{self.dependent_variable["Name"]}" has to consist of two values '
							 f'("lower; upper"), got {self.target_range}.')

		paths = [tuple(parameter['Parameter']) for parameter in self.parameters.values()]

		if len(set(paths)) != len(paths):
			raise ValueError('Each parameter path can only be used once in "Parameters - Monte_Carlo_Analysis".')

		for name, parameter in self.parameters.items():
			if len(parameter['Values']) != 2 or parameter['Reference'] not in parameter['Values']:
				raise ValueError(f'"Values" of "{name}" have to consist of the base value and a limit value (e.g. "Base; 0.3"), '
								 f'got {parameter["Values"]} with base value {parameter["Reference"]}.')

	def determine_principal_components(self) -> None:
		'''Store parameter names (`principal`) and reference values (`base_case`) in table order.

		Notes
		-----
		The first parameter of `principal` is shown on the x axis, the second on the y axis and
		the third as color in :meth:`plot_colored_scatter`.
		'''

		# placeholder for actual PCA
		self.principal = list(self.parameters)
		self.base_case = [parameter['Reference'] for parameter in self.parameters.values()]

	def generate_random_values(self, samples: int, random_seed: int) -> np.ndarray:
		'''Draw uniformly distributed values for each parameter within its value range.

		Parameters
		----------
		samples : int
			Number of samples.
		random_seed : int
			Seed for :func:`numpy.random.default_rng`.

		Returns
		-------
		np.ndarray
			2D array of parameter values with shape (samples, parameters).

		Notes
		-----
		The values are drawn parameter by parameter in table order with
		``rng.uniform(lower, upper, samples)``, using ``rng = numpy.random.default_rng(random_seed)``.
		Hence, the same seed reproduces the same values.
		'''

		rng = np.random.default_rng(random_seed)

		return np.column_stack([rng.uniform(*parameter['Values'], samples) for parameter in self.parameters.values()])

	def perform_monte_carlo_multiprocessing(self,
											inp: dict,
											values: np.ndarray,
											return_full_array: bool = True) -> np.ndarray:
		'''Model is evaluated for each set of parameter values with multiprocessing
		parallelization across all available CPUs.

		Parameters
		----------
		inp : dict
			Input dictionary of the model.
		values : np.ndarray
			2D array containing parameters variations which are to be evaluated.
		return_full_array : bool, optional
			If `return_full_array` is True, the full 2D array containing parameter
			variations and target response values is returned. Otherwise, a 1D array containing only
			target response values is returned.

		Returns
		-------
		np.ndarray
			If `return_full_array` is True: 2D array of shape (n_samples, n_parameters + 1)
			with sampled parameter values and the response in the final column.
			Otherwise: 1D array of response values only.

		Notes
		-----
		The first sample is evaluated on its own before the workers start, since it
		initialises objects on disk that the parallel runs read. Its result is the
		first entry of the returned results; row order always matches `values`.
		'''

		# First sample runs alone: it initialises the objects on disk read by the workers
		first_result = _mc_response_worker(values[:1], 
										   inp,
										   self.parameters, 
										   self.dependent_variable)

		remaining = values[1:]
		batch_results = []

		if len(remaining) > 0:
			# os.process_cpu_count is only available for Python >= 3.13
			cpu_count = os.process_cpu_count() if hasattr(os, 'process_cpu_count') else os.cpu_count()
			max_workers = min(cpu_count or 1, len(remaining))

			# ~10 batches per worker, so progress is reported regularly during the run
			value_batches = np.array_split(remaining, min(10 * max_workers, len(remaining)))
			batch_results = [None] * len(value_batches)
			samples_done = len(first_result)

			print(f'Evaluating {len(values)} parameter sets across {max_workers} workers...')

			with concurrent.futures.ProcessPoolExecutor(max_workers = max_workers) as executor:
				future_to_batch_index = {
					executor.submit(_mc_response_worker, 
									batch,
									inp,
									self.parameters,
									self.dependent_variable): batch_index
					for batch_index, batch in enumerate(value_batches)
				}

				for future in concurrent.futures.as_completed(future_to_batch_index):
					batch_index = future_to_batch_index[future]
					batch_results[batch_index] = future.result()
					samples_done += len(batch_results[batch_index])
					print(f'  {samples_done}/{len(values)} parameter sets done ({samples_done / len(values):.0%})')

		response_values = np.concatenate([first_result, *batch_results])

		if return_full_array is True:
			return np.c_[values, response_values]
		else:
			return response_values

	def perform_full_monte_carlo(self,
								 inp: dict,
								 samples: int,
								 random_seed: int | None = None) -> None:
		'''Monte Carlo simulation: random parameter values are generated and the model is
		evaluated for each of them.

		Parameters
		----------
		inp : dict
			Input dictionary of the model.
		samples : int
			Number of samples.
		random_seed : int or None, optional
			Seed for the random number generator. If None, a seed is drawn (and stored in
			`random_seed`, so that the results can be reproduced).

		Raises
		------
		ValueError
			If `samples` is smaller than 1.

		Notes
		-----
		Sets `samples`, `random_seed`, `values` and `results`.
		'''

		if samples < 1:
			raise ValueError(f'Number of Monte Carlo samples has to be at least 1, got {samples}.')

		if random_seed is None:
			random_seed = np.random.SeedSequence().entropy
			print(f'No random seed specified for Monte Carlo analysis, using {random_seed}.')

		self.samples = samples
		self.random_seed = random_seed
		self.values = self.generate_random_values(samples, random_seed)

		start = timer()

		self.results = self.perform_monte_carlo_multiprocessing(inp, self.values)

		end = timer()
		print(f'Monte Carlo simulation with {samples} samples finished in {end - start:.1f} s.')

	def save_results(self, file_name: str) -> None:
		'''Save results of the Monte Carlo simulation together with their metadata in a
		NumPy ``.npz`` file (see :func:`write_results_file`).

		Parameters
		----------
		file_name : str
			Path to results file (suffix ``.npz``).

		Notes
		-----
		The metadata (stored in `metadata`) contain the "File format version", "pyH2A version",
		"NumPy version", "Created" (time stamp), "Input file", "Samples", "Random seed", the
		"Dependent variable" ("Name", "Path", "Unit", "Target range") and the "Parameters", a list
		with one entry ("Name", "Path", "Type", "Values", "Reference", "Limit") for each column of
		the stored parameter values.
		'''

		self.metadata = {
			'File format version': RESULTS_FILE_FORMAT_VERSION,
			'pyH2A version': __version__,
			'NumPy version': np.__version__,
			'Created': datetime.now().astimezone().isoformat(timespec = 'seconds'),
			'Input file': str(self.input_file),
			'Samples': int(self.samples),
			'Random seed': int(self.random_seed),
			'Dependent variable': {'Name': self.dependent_variable['Name'],
								   'Path': self.dependent_variable['Path'],
								   'Unit': self.dependent_variable['Unit'],
								   'Target range': self.target_range.tolist()},
			'Parameters': [{'Name': name,
							'Path': parameter['Parameter'],
							'Type': parameter['Type'],
							'Values': parameter['Values'].tolist(),
							'Reference': float(parameter['Reference']),
							'Limit': float(parameter['Limit'])} for name, parameter in self.parameters.items()],
		}

		write_results_file(file_name, self.values, self.results[:,-1], self.metadata)
		print(f'Monte Carlo results saved in "{file_name}".')

	def read_results(self, file_name: str) -> None:
		'''Read Monte Carlo results from a NumPy ``.npz`` file written by :meth:`save_results`.

		Parameters
		----------
		file_name : str
			Path to results file (suffix ``.npz``).

		Raises
		------
		ValueError
			If the stored results do not match the dependent variable or the parameters
			specified in the input file.

		Notes
		-----
		The stored parameter columns are mapped onto the parameters of the input file by their
		path, so that parameters can be renamed and reordered. The "Type" and the "Values" of each
		parameter as well as the path of the dependent variable have to match the stored ones.
		The stored dependent variable is converted to the "Variable unit" of the input file and
		the target range is taken from the input file. Changes of other model inputs after the
		results were computed cannot be detected.
		Sets `values`, `results`, `metadata`, `samples` and `random_seed`.
		'''

		parameter_values, dependent_variable_values, metadata = read_results_file(file_name)
		stored_dependent_variable = metadata['Dependent variable']

		if stored_dependent_variable['Path'] != self.dependent_variable['Path']:
			raise ValueError(f'"{file_name}" contains results for "{" > ".join(stored_dependent_variable["Path"])}", '
							 f'not for "{" > ".join(self.dependent_variable["Path"])}".')

		stored_parameters = {tuple(parameter['Path']): (column, parameter) for column, parameter in enumerate(metadata['Parameters'])}
		input_parameters = {tuple(parameter['Parameter']): name for name, parameter in self.parameters.items()}
				
		if stored_parameters.keys() != input_parameters.keys():
			not_in_file = [input_parameters[path] for path in input_parameters.keys() - stored_parameters.keys()]
			not_in_input = [stored_parameters[path][1]['Name'] for path in stored_parameters.keys() - input_parameters.keys()]
			raise ValueError(f'Parameters in "Parameters - Monte_Carlo_Analysis" do not match the parameters in "{file_name}". '
							 f'Not contained in file: {not_in_file}. Not contained in input: {not_in_input}.')

		columns = []

		for name, parameter in self.parameters.items():
			column, stored_parameter = stored_parameters[tuple(parameter['Parameter'])]

			if (stored_parameter['Type'] != parameter['Type'] or
				not np.allclose(stored_parameter['Values'], parameter['Values'], rtol = 1e-12, atol = 0.)):
				raise ValueError(f'"{name}" ("Type": {parameter["Type"]}, "Values": {parameter["Values"].tolist()}) differs from the parameter '
								 f'used to compute "{file_name}" ("Type": {stored_parameter["Type"]}, "Values": {stored_parameter["Values"]}). '
								 'The results have to be recomputed.')

			columns.append(column)

		unit = self.dependent_variable['Unit']

		if stored_dependent_variable['Unit'] != unit:
			try:
				dependent_variable_values = Quantity(dependent_variable_values, stored_dependent_variable['Unit']).unit[unit]
			except ValueError as error:
				raise ValueError(f'Results in "{file_name}" (unit: {stored_dependent_variable["Unit"]}) cannot be converted to "{unit}". {error}') from error

		self.metadata = metadata
		self.samples = metadata['Samples']
		self.random_seed = metadata['Random seed']
		self.values = parameter_values[:,columns]
		self.results = np.c_[self.values, dependent_variable_values]

		print(f'Monte Carlo results read from "{file_name}" ({self.samples} samples, computed with pyH2A {metadata["pyH2A version"]}).')

	def check_parameter_integrity(self, values: np.ndarray) -> None:
		'''Checking that parameter values are within the ranges specified in
		`parameters` ("Values").

		Parameters
		----------
		values : np.ndarray
			2D array of parameter values, columns ordered according to the "Index" of each parameter.

		Raises
		------
		ValueError
			If a parameter value lies outside of its range.
		'''

		for name, parameter in self.parameters.items():
			column = values[:,parameter['Index']]
			minimum, maximum = np.amin(column), np.amax(column)
			lower, upper = parameter['Values']
			
			if minimum < lower or maximum > upper:
				raise ValueError(f'Values of "{name}" ({minimum} - {maximum}) lie outside of the specified range ({lower} - {upper}).')

	def generate_parameter_string_table(self,
										base_string: str = 'Base',
										limit_string: str = 'Limit',
										format_cutoff: int = 6) -> None:
		'''String of parameter table is generated, used in :meth:`render_parameter_table`.

		Parameters 
		----------
		base_string : str, optional
			String used to label base column.
		limit_string : str, optional
			String used to label limit column.
		format_cutoff : int, optional
			Length of number string at which it is converted to 
			scientific/millified representation.

		Notes
		-----
		Sets `parameter_string` and `parameter_table`.
		'''

		self.parameter_string = make_bold(self.display_name) + '\n'
		self.parameter_table = {'Table Data': [[make_bold(self.display_name), 
												make_bold(base_string), '', 
												make_bold(limit_string)]], 'Row Labels': []}

		for key, value in self.parameters.items():
			reference_value = dynamic_value_formatting(value['Reference'], cutoff = format_cutoff)
			limit_value = dynamic_value_formatting(value['Limit'], cutoff = format_cutoff)

			string = key + ': ' + reference_value + r'$\rightarrow$' + limit_value + '\n'
			self.parameter_string += string

			self.parameter_table['Table Data'].append([key, reference_value, 
													   r'$\longrightarrow$', limit_value])
			self.parameter_table['Row Labels'].append(key)

	def render_parameter_table(self,
							   ax: Axes,
							   xpos: float = 1.05,
							   ypos: float = 0.0,
							   height: float = 1.0,
							   colWidths: list[float] = [0.55, 0.25, 0.07, 0.25],
							   left_pad: float = 0.01,
							   edge_padding: float = 0.02,
							   fontsize: float = 12,
							   base_string: str = 'Base',
							   limit_string: str = 'Limit',
							   format_cutoff: int = 7) -> None:
		'''Rendering table of parameters which are varied during Monte Carlo analysis.

		Parameters
		----------
		ax : matplotlib.axes.Axes
			Axes object in which parameter table is displayed.
		xpos : float, optional
			x axis position of left edge of table in axis fraction coordinates.
		ypos : float, optional
			y axis position of lower edge of table in axis fraction coordinates.
		height : float, optional
			Height of table in axis fraction coordinates (e.g. height = 0.5 meaning that
			the table has half the height of the plot).
		colWidths : list[float], optional
			List of length 4 with widths for each column from left to right in axis
			fraction coordinates.
		left_pad : float, optional
			Padding of the table on the left site.
		edge_padding: float, optional
			Padding of edges that are drawn.
		fontsize : float, optional
			fontsize for table.
		base_string : str, optional
			String used to label base column.
		limit_string : str, optional
			String used to label limit column.
		format_cutoff : int, optional
			Length of number string at which it is converted to
			scientific/millified representation.

		Notes
		-----
		Table is rendered in provided matplotlib.axes object.
		'''

		self.generate_parameter_string_table(base_string = base_string, limit_string = limit_string,
											 format_cutoff = format_cutoff)

		bbox = [xpos, ypos, sum(colWidths), height]
		number_of_rows = len(self.parameter_table['Table Data'])
		cell_height = bbox[3] / number_of_rows

		table = ax.table(cellText = self.parameter_table['Table Data'],
						 edges = 'open',
						 bbox = bbox,
						 colWidths = colWidths,
						 cellLoc = 'left')

		for key, cell in table.get_celld().items():
			cell.get_text().set_color('black')
			if key[0] == 0 or key[1] >= 1:
				cell.get_text().set_color(self.color)

		table.auto_set_font_size(False)
		table.set_fontsize(fontsize)

		def set_pad_for_column(col: int, pad: float) -> None:
			'''Set padding of all cells in column `col` of the table to `pad`.'''
			cells = table.get_celld()
			column = [cell for cell in table.get_celld() if cell[1] == col]
			for cell in column:
				cells[cell].PAD = pad

		set_pad_for_column(col=0, pad = left_pad)

		def plot_edge(row_position: int | str, edge_padding: float) -> None:
			'''Draw horizontal line below table row `row_position` ("last": bottom of table).'''

			if row_position == 'last':
				y_edge = bbox[1] + edge_padding
			else:
				y_edge = bbox[1] + bbox[3] - (row_position * cell_height) + edge_padding

			table_edge = ax.annotate('', xy = (bbox[0], y_edge), 
									 xytext = (bbox[0] + bbox[2], y_edge), 
									 xycoords = ax.transAxes, textcoords = ax.transAxes, 
									 arrowprops={'arrowstyle': '-', 'color': self.color})

		plot_edge(1, edge_padding)
		plot_edge('last', 0)

	def target_range_components(self) -> None:
		'''Monte Carlo simulation results are sorted by the dependent variable and the entries
		of `results` with a dependent variable within the target range are stored in
		`target_range_data`.

		Warns
		-----
		UserWarning
			If no sample lies within the target range.
		'''

		results_sorted = self.results[np.argsort(self.results[:,-1], kind = 'stable')]
		lower, upper = self.target_range
		within_target_range = (results_sorted[:,-1] >= lower) & (results_sorted[:,-1] <= upper)

		self.target_range_data = results_sorted[within_target_range]

		if len(self.target_range_data) == 0:
			warnings.warn(f'No Monte Carlo sample lies within the target range of "{self.dependent_variable["Name"]}" '
						  f'({lower:g} - {upper:g} {self.dependent_variable["Unit"]}).', UserWarning)

	def target_range_2D_region(self, grid_points: int = 15) -> dict:
		'''Determining largest region spanned by first two parameters within which
		the target range can be reached.

		Parameters
		----------
		grid_points : int, optional
			Number of grid points to determine density of grid evaluation.

		Returns
		-------
		dict
			"Grid Values" (list of two 2D arrays from :func:`numpy.meshgrid`), "Dependent variable 2D"
			(2D array with dependent variable on the grid) and "Base value" (dependent variable with
			all parameters at their base values). Also stored in `target_range_2D_grid`.

		Notes
		-----		
		Model is evaluated on grid spanned by first two parameters (density of grid is controlled by 
		`grid_points`), other parameters are set to their limit (non-reference) values. The output
		is used to overlay the target range region onto the scatter plot in :meth:`plot_colored_scatter`.
		'''

		x_parameter, y_parameter = (self.parameters[name] for name in self.principal[:2])
		grid_values = np.meshgrid(np.linspace(*x_parameter['Values'], grid_points),
								  np.linspace(*y_parameter['Values'], grid_points))

		# All other parameters are set to their limit values, the last row is the base case
		values = np.tile([parameter['Limit'] for parameter in self.parameters.values()], (grid_points**2 + 1, 1))
		values[:-1,x_parameter['Index']] = grid_values[0].ravel()
		values[:-1,y_parameter['Index']] = grid_values[1].ravel()
		values[-1] = self.base_case

		self.check_parameter_integrity(values)	

		response = self.perform_monte_carlo_multiprocessing(self.inp, values, return_full_array = False)

		self.target_range_2D_grid = {'Grid Values': grid_values,
									 'Dependent variable 2D': np.reshape(response[:-1], (grid_points, grid_points)),
									 'Base value': response[-1]}

		return self.target_range_2D_grid

	def development_distance(self,
							 metric: str = 'cityblock',
							 log_normalize: bool = False,
							 sum_distance: bool = False) -> None:
		'''Calculation of development distance for models within target range.

		Parameters
		----------
		metric : str, optional
			Metric used for distance calculation, defaults to `cityblock`.
		log_normalize : bool, optional
			Flag to control if log normalization is used instead of linear normalization.
		sum_distance : bool, optional
			Flag to control if distance is calculated by summing the normalized values
			(see :func:`calculate_distance`).

		Notes
		-----
		The euclidean or cityblock distance in n-dimensional space of each Monte Carlo simulation datapoint within 
		the target range to the reference point is calculated and stored in `distances`.
		Parameter ranges and the reference parameters are scaled to be within a n-dimensional unit cube.
		Distances are normalized by the number of dimensions, so that the maximum distance is always 1.
		The datapoints sorted by distance are stored in `target_distances_sorted` and the datapoint with the
		shortest distance in `shortest_target_distance` (empty if there is no datapoint within the target range).
		'''

		self.distances = calculate_distance(self.target_range_data, self.parameters,
											self.principal, metric = metric,
											log_normalize = log_normalize,
											sum_distance = sum_distance)

		target_distances = np.c_[self.target_range_data, self.distances]
		self.target_distances_sorted = target_distances[np.argsort(target_distances[:,-1], kind = 'stable')]

		self.shortest_target_distance = {}

		if len(self.target_distances_sorted) > 0:
			for key, item in self.parameters.items():
				self.shortest_target_distance[key] = self.target_distances_sorted[0][item['Index']]

			self.shortest_target_distance[dependent_variable_label(self.dependent_variable)] = self.target_distances_sorted[0][-2]
			self.shortest_target_distance['Distance'] = self.target_distances_sorted[0][-1]

	def full_distance_cost_relationship(self,
										metric: str = 'cityblock',
										reduction_factor: int = 25,
										poly_order: int = 4,
										log_normalize: bool = False,
										sum_distance: bool = False) -> None:
		'''Calculation of development distance for all datapoints from Monte Carlo Analysis and
		calculation of Savitzky-Golay filter of the dependent variable.

		Parameters
		----------
		metric : str, optional
			Distance metric used for :func:`calculate_distance`.
		reduction_factor : int, optional
			Determines window size for Savitzky-Golay filter (number of datapoints divided
			by `reduction_factor`).
		poly_order : int, optional
			Order of polynomial for Savitzky-Golay filter (reduced for small numbers of datapoints).
		log_normalize : bool, optional
			Flag to control if log normalization is used instead of linear normalization.
		sum_distance : bool, optional
			Flag to control if distance is calculated by summing the normalized values
			(see :func:`calculate_distance`).

		Notes
		-----
		Sets `results_distances_sorted` (`results` with distances as additional last column, sorted
		by distance) and `distances_cost_savgol` (distances and filtered dependent variable).
		'''

		distances = calculate_distance(self.results, self.parameters, 
									   self.principal, metric = metric,
									   log_normalize = log_normalize,
									   sum_distance = sum_distance)

		results_distances = np.c_[self.results, distances]
		self.results_distances_sorted = results_distances[np.argsort(results_distances[:,-1], kind = 'stable')]

		window_length, poly_order = _savgol_parameters(len(self.results), reduction_factor, poly_order)
		smoothed = savgol_filter(self.results_distances_sorted[:,-2], window_length, poly_order)
	
		self.distances_cost_savgol = np.c_[self.results_distances_sorted[:,-1], smoothed]

	def _target_range_title(self, title_string: str) -> str:
		'''Title showing the target range and the unit of the dependent variable.

		Parameters 
		----------
		title_string : str
			String preceding the target range.

		Returns
		-------
		str
			Title, e.g. "Target range: 1.5 - 1.6 kg[$CO_{2}$-Eq]/kg[H2]".
		'''

		lower, upper = self.target_range

		return f'{title_string.rstrip()} {lower:g} - {upper:g} {self.dependent_variable["Unit"]}'

	def _require_target_range_samples(self) -> None:
		'''Raise an error if no sample lies within the target range.

		Raises
		------
		ValueError
			If `target_range_data` is empty.
		'''

		if len(self.target_range_data) == 0:
			raise ValueError(f'No Monte Carlo sample lies within the target range of "{self.dependent_variable["Name"]}", '
							 f'adjust "Dependent variable > {self.dependent_variable["Name"]} > Target range".')

	def plot_complete_histogram(self,
								bins: int | str | None = None,
								xlim_low: float | None = None,
								xlim_high: float | None = None,
								xlabel_string: str | None = None,
								ylabel_string: str = 'Normalized Frequency',
								image_kwargs: dict = {},
								plot_kwargs: dict = {},
								**kwargs) -> Figure:
		'''Complete histogram of the dependent variable from the Monte Carlo analysis.

		Parameters
		----------
		bins : int, str or None, optional
			Number of bins (or binning strategy) for histogram. If `None`, the bins are
			determined automatically.
		xlim_low : float or None, optional
			Lower x axis limit.
		xlim_high : float or None, optional
			Higher x axis limit.
		xlabel_string : str or None, optional
			String for x axis label. If `None`, name and unit of the dependent variable are used.
		ylabel_string : str, optional
			String for y axis label.
		image_kwargs: dict, optional
			Dictionary containing optional keyword arguments for
			:func:`~pyH2A.Utilities.output_utilities.insert_image`
		plot_kwargs: dict, optional
			Dictionary containing optional keyword arguments for
			:func:`~pyH2A.Utilities.output_utilities.Figure_Lean`, has priority over `**kwargs`.
		**kwargs: 
			Additional `kwargs` passed to 
			:func:`~pyH2A.Utilities.output_utilities.Figure_Lean`

		Returns
		-------
		figure : matplotlib.figure.Figure
			matplotlib figure.
		'''

		kwargs = {**{'right': 0.95, 'bottom': 0.15, 'top': 0.95,
					 'fig_width': 7, 'fig_height': 4, 'font_size': 12,
					 'name': 'Monte_Carlo_Complete_Histogram', 'directory': '.'},
				  **kwargs, **plot_kwargs}

		image_kwargs = {**{'path': None, 'x': 0.5, 'y': 0.8, 'zoom': 0.08}, 
						**image_kwargs}

		figure = Figure_Lean(**kwargs)
		ax = figure.ax

		if bins is None:
			bins = 'auto'

		ax.hist(self.results[:,-1], bins = bins, density=True, color=self.color, edgecolor = 'black')

		ax.set_xlabel(dependent_variable_label(self.dependent_variable) if xlabel_string is None else xlabel_string)
		ax.set_ylabel(ylabel_string)

		if xlim_low is not None:
			ax.set_xlim(xlim_low, xlim_high)

		if image_kwargs['path'] is not None:
			insert_image(ax = ax, **image_kwargs)

		figure.execute()

		return figure.fig

	def plot_colored_scatter(self,
							 limit_extension: float = 0.03,
							 title_string: str = 'Target range:',
							 base_string: str = 'Base',
							 image_kwargs: dict = {},
							 plot_kwargs: dict = {},
							 grid_points: int = 15,
							 **kwargs) -> Figure:
		'''Plotting colored scatter plot showing all models within target range.

		Parameters
		----------
		limit_extension: float, optional
			Amount of limit extension of axes as fraction of axis range.
		title_string : str, optional
			String for title (followed by the target range).
		base_string : str, optional
			String to label base case datapoint.
		image_kwargs: dict, optional
			Dictionary containing optional keyword arguments for
			:func:`~pyH2A.Utilities.output_utilities.insert_image`
		plot_kwargs: dict, optional
			Dictionary containing optional keyword arguments for
			:func:`~pyH2A.Utilities.output_utilities.Figure_Lean`, has priority over `**kwargs`.
		grid_points : int, optional
			Number of grid points per axis for the evaluation of the target range region
			(see :meth:`target_range_2D_region`).
		**kwargs: 
			Additional `kwargs` passed to 
			:func:`~pyH2A.Utilities.output_utilities.Figure_Lean`

		Returns 
		-------
		figure : matplotlib.figure.Figure
			matplotlib figure.

		Raises
		------
		ValueError
			If less than three parameters are varied.

		Notes
		-----
		x, y and color axis are determined by :meth:`determine_principal_components`,
		with pc[0] being the x axis, pc[1] the y axis and pc[2] the color axis. Order can
		be changed by changing order of parameters in input file. The shaded region shows where
		the target range can be reached by varying the first two parameters (with all other
		parameters at their limit values, see :meth:`target_range_2D_region`).
		'''

		if len(self.principal) < 3:
			raise ValueError('plot_colored_scatter requires at least three parameters (x axis, y axis and color).')

		kwargs = {**{'left': 0.15, 'right': 0.9, 'bottom': 0.11, 'top': 0.88,
					 'fig_width': 6.4, 'fig_height': 4.8, 'font_size': 12,
					 'name': 'Monte_Carlo_Colored_Scatter', 'directory': '.'},
				  **kwargs, **plot_kwargs}

		image_kwargs = {**{'path': None, 'x': 0.5, 'y': 0.8, 'zoom': 0.08}, 
						**image_kwargs}

		pc = self.principal
		par = self.parameters

		figure = Figure_Lean(**kwargs)
		ax = figure.ax
		fig = figure.fig

		cm = plt.get_cmap('plasma')

		grid = self.target_range_2D_region(grid_points = grid_points)
		dependent_variable_2D = grid['Dependent variable 2D']

		# Region in which target range is reached, approached from the base case
		# (decreasing dependent variable if base value is above target range, increasing otherwise)
		if grid['Base value'] >= self.target_range[0]:
			levels = [np.nanmin(dependent_variable_2D), self.target_range[1]]
		else:
			levels = [self.target_range[0], np.nanmax(dependent_variable_2D)]

		if levels[0] < levels[1]:
			ax.contourf(*grid['Grid Values'], dependent_variable_2D,
						levels = levels, alpha = 0.1, colors = [cm(0.0)])

		target_range_data_appended = np.vstack((self.target_range_data[:,:-1], self.base_case))

		scatter = ax.scatter(target_range_data_appended[:,par[pc[0]]['Index']],
							 target_range_data_appended[:,par[pc[1]]['Index']],
							 c = target_range_data_appended[:,par[pc[2]]['Index']],
							 cmap = 'plasma', alpha = 1.)

		colorbar = fig.colorbar(scatter, ax=ax)

		ax.set_xlim(extend_limits(par[pc[0]]['Values'], limit_extension))
		ax.set_ylim(extend_limits(par[pc[1]]['Values'], limit_extension))
		scatter.set_clim(par[pc[2]]['Values'])

		ax.set_xlabel(pc[0])
		ax.set_ylabel(pc[1])
		colorbar.set_label(pc[2])

		xtext, ytext = coordinate_position(par[pc[0]]['Reference'], par[pc[0]]['Values'],
										   par[pc[1]]['Reference'], par[pc[1]]['Values']) 

		ax.annotate(make_bold(base_string), xy = (par[pc[0]]['Reference'], 
					par[pc[1]]['Reference']), xytext = (xtext, ytext), 
					textcoords = 'axes fraction')

		ax.set_title(self._target_range_title(title_string))

		ax.grid(color = 'grey', linestyle = '--', linewidth = 0.2, zorder = 0)

		if image_kwargs['path'] is not None:
			insert_image(ax = ax, **image_kwargs)

		figure.execute()

		return figure.fig

	def plot_colored_scatter_3D(self,
								limit_extension: float = 0.03,
								title_string: str = 'Target range:',
								plot_kwargs: dict = {},
								**kwargs) -> Figure:
		'''3D colored scatter plot of models within target range.
	
		Parameters
		----------
		limit_extension: float, optional
			Amount of limit extension of axes as fraction of axis range.
		title_string: str, optional
			String for title (followed by the target range).
		plot_kwargs: dict, optional
			Dictionary containing optional keyword arguments for
			:func:`~pyH2A.Utilities.output_utilities.Figure_Lean`, has priority over `**kwargs`.
		**kwargs:
			Additional `kwargs` passed to
			:func:`~pyH2A.Utilities.output_utilities.Figure_Lean`

		Returns
		-------
		figure : matplotlib.figure.Figure
			matplotlib figure.

		Raises
		------
		ValueError
			If less than four parameters are varied.

		Notes
		-----
		The first, second and fourth parameter are shown on the x, y and z axis,
		the third parameter as color.
		'''

		if len(self.principal) < 4:
			raise ValueError('plot_colored_scatter_3D requires at least four parameters (x, y and z axis and color).')

		kwargs = {**{'left': 0.0, 'right': 0.95, 'bottom': 0.03, 'top': 0.95,
					 'fig_width': 8, 'fig_height': 7, 'font_size': 12,
					 'name': 'Monte_Carlo_Colored_Scatter_3D', 'directory': '.'},
				  **kwargs, **plot_kwargs}
	
		pc = self.principal
		par = self.parameters

		fig = plt.figure(figsize = (kwargs['fig_width'], kwargs['fig_height']))
		ax = fig.add_subplot(projection = '3d')
		figure = Figure_Lean(provided_figure_and_axis = (fig, ax), **kwargs)

		scatter = ax.scatter(self.target_range_data[:,par[pc[0]]['Index']],
							 self.target_range_data[:,par[pc[1]]['Index']],
							 self.target_range_data[:,par[pc[3]]['Index']],
							 c = self.target_range_data[:,par[pc[2]]['Index']],
							 cmap = 'plasma', depthshade = False)
	
		colorbar = fig.colorbar(scatter, ax=ax, shrink = 0.7, pad = 0.12)

		ax.set_xlim(extend_limits(par[pc[0]]['Values'], limit_extension))
		ax.set_ylim(extend_limits(par[pc[1]]['Values'], limit_extension))
		ax.set_zlim(extend_limits(par[pc[3]]['Values'], limit_extension))
		scatter.set_clim(par[pc[2]]['Values'])

		# Additional label padding, since parameter names (including their units) are longer than the tick labels
		ax.set_xlabel(pc[0], labelpad = 12)
		ax.set_ylabel(pc[1], labelpad = 12)
		ax.set_zlabel(pc[3], labelpad = 12)
		ax.set_box_aspect(None, zoom = 0.85)
		colorbar.set_label(pc[2])

		ax.set_title(self._target_range_title(title_string))
	
		ax.grid(color = 'grey', linestyle = '--', linewidth = 0.2, zorder = 0)

		figure.execute()

		return figure.fig

	def plot_distance_histogram(self,
								ax: Axes | None = None,
								bins: int = 25,
								figure_lean: bool = True,
								xlabel: bool = False,
								title: bool = True,
								xlabel_string: str = 'Development distance',
								ylabel_string: str = 'Frequency',
								title_string: str = 'Target range:',
								show_parameter_table: bool = True,
								show_mu: bool = True,
								mu_x: float = 0.2,
								mu_y: float = 0.5,
								table_kwargs: dict = {},
								image_kwargs: dict = {},
								plot_kwargs: dict = {},
								**kwargs) -> Figure | None:
		'''Plotting development distances as histogram.

		Parameters
		----------
		ax : matplotlib.axes.Axes or None, optional
			Axes object in which plot is drawn. Default is None, creating new plot.
		bins : int, optional
			Number of bins for histogram.
		figure_lean : bool, optional
			If figure_lean is True and a new plot is created, the figure is executed
			(shown/saved) and returned.
		xlabel : bool, optional
			Flag to control if x axis label is displayed or not.
		title : bool, optional
			Flag to control if title is displayed or not.
		xlabel_string : str, optional
			String for x axis label.
		ylabel_string : str, optional
			String for y axis label.
		title_string : str, optional
			String for title (followed by the target range).
		show_parameter_table : bool, optional
			Flag to control if parameter table is shown.
		show_mu : bool, optional
			Flag to control if mu and sigma values of normal distribution are shown.
		mu_x : float, optional
			x axis coordinate of shown mu and sigma values in axis coordinates.
		mu_y : float, optional
			y axis coordinate of shown mu and sigma values in axis coordinates.
		table_kwargs : dict, optional
			Dictionary containing optional keyword arguments for :meth:`render_parameter_table`
		image_kwargs: dict, optional
			Dictionary containing optional keyword arguments for
			:func:`~pyH2A.Utilities.output_utilities.insert_image`
		plot_kwargs: dict, optional
			Dictionary containing optional keyword arguments for
			:func:`~pyH2A.Utilities.output_utilities.Figure_Lean`, has priority over `**kwargs`.
		**kwargs: 
			Additional `kwargs` passed to 
			:func:`~pyH2A.Utilities.output_utilities.Figure_Lean`

		Returns 
		-------
		figure : matplotlib.figure.Figure or None
			matplotlib figure, if a new plot is created and `figure_lean` is True.

		Raises
		------
		ValueError
			If no sample lies within the target range.
		'''

		self._require_target_range_samples()

		kwargs = {**{'left': 0.2, 'right': 0.55, 'bottom': 0.25, 'top': 0.85, 'hspace': 0.2,
					 'fig_width': 11, 'fig_height': 2.5, 'font_size': 12,
					 'name': 'Monte_Carlo_Distance_Histogram', 'directory': '.'},
				  **kwargs, **plot_kwargs}

		table_kwargs = {**{'colWidths': [0.55, 0.25, 0.07, 0.25], 'format_cutoff': 7}, 
						**table_kwargs}

		image_kwargs = {**{'path': None, 'x': -0.35, 'y': 0.5, 'zoom': 0.08}, 
						**image_kwargs}

		figure = None

		if ax is None:
			figure = Figure_Lean(**kwargs)
			ax = figure.ax

		if title is True:
			ax.set_title(self._target_range_title(title_string))

		yhist, xhist, rectangle = ax.hist(self.distances, bins = bins, density=False, 
										  color=self.color, edgecolor = 'black')
		density = np.sum(np.diff(xhist) * yhist)
	
		ax.set_xlim(0, 1)

		mu, std = normal_distribution.fit(self.distances)

		# Normal distribution can only be shown for distances with non-zero spread
		if std > 0:
			x = np.linspace(*ax.get_xlim(), 500)
			p = normal_distribution.pdf(x, mu, std)
			ax.plot(x, p * density, 'k', linewidth=2)

			if show_mu:
				ax.annotate(f'$\\mu$ = {mu:.2f}\n$\\sigma$ = {std:.3f}', xy = (mu_x, mu_y),
							va = 'center', ha = 'center', xycoords = ax.transAxes)

		if xlabel:
			ax.set_xlabel(xlabel_string)
		ax.set_ylabel(ylabel_string)

		if image_kwargs['path'] is not None:
			insert_image(ax = ax, **image_kwargs)

		if show_parameter_table:
			self.render_parameter_table(ax, **table_kwargs)
	
		if figure_lean is True and figure is not None:
			figure.execute()
			return figure.fig
								
	def plot_distance_cost_relationship(self,
										ax: Axes | None = None,
										ylim: list[float] | None = None,
										xlim: list[float] | None = None,
										figure_lean: bool = True,
										parameter_table: bool = True,
										legend_loc: str = 'upper left',
										log_scale: bool = False,
										xlabel_string: str = 'Development distance',
										ylabel_string: str | None = None,
										linewidth: float = 1.5,
										markersize: float = 0.2,
										marker_alpha: float = 0.2,
										table_kwargs: dict = {},
										image_kwargs: dict = {},
										plot_kwargs: dict = {},
										**kwargs) -> Figure | None:
		'''Plotting relationship of development distance and dependent variable.

		Parameters
		----------
		ax : matplotlib.axes.Axes or None, optional
			Axes object in which plot is drawn. Default is None, creating new plot.
		ylim : list[float] or None, optional
			Ordered limit values for y axis. Default is None.
		xlim : list[float] or None, optional
			Ordered limit values for x axis. Default is None.
		figure_lean : bool, optional
			If figure_lean is True and a new plot is created, the figure is executed
			(shown/saved) and returned.
		parameter_table : bool, optional
			If parameter_table is True, the parameter table is shown in the plot.
		legend_loc : str, optional
			Controls location of legend in plot. Defaults to 'upper left'.
		log_scale : bool, optional
			If log_scale is True, the y axis will use a log scale.
		xlabel_string : str, optional
			String for x axis label.
		ylabel_string : str or None, optional
			String for y axis label. If `None`, name and unit of the dependent variable are used.
		linewidth : float, optional
			Line width for smoothed trendline.
		markersize : float, optional
			Size of markers in scatter plot.
		marker_alpha : float, optional
			Transparency of markers in scatter plot (0: maximum transpareny, 1: no transparency).
		table_kwargs : dict, optional
			Dictionary containing optional keyword arguments for :meth:`render_parameter_table`
		image_kwargs: dict, optional
			Dictionary containing optional keyword arguments for
			:func:`~pyH2A.Utilities.output_utilities.insert_image`
		plot_kwargs: dict, optional
			Dictionary containing optional keyword arguments for
			:func:`~pyH2A.Utilities.output_utilities.Figure_Lean`, has priority over `**kwargs`.
		**kwargs: 
			Additional `kwargs` passed to 
			:func:`~pyH2A.Utilities.output_utilities.Figure_Lean`

		Returns 
		-------
		figure : matplotlib.figure.Figure or None
			matplotlib figure, if a new plot is created and `figure_lean` is True.
		'''

		kwargs = {**{'left': 0.1, 'right': 0.9, 'bottom': 0.1, 'top': 0.95,
					 'fig_width': 7, 'fig_height': 4, 'font_size': 12,
					 'name': 'Monte_Carlo_Distance_Cost_Relationship', 'directory': '.'},
				  **kwargs, **plot_kwargs}

		table_kwargs = {**{'xpos': 1.4, 'height': 0.23, 'edge_padding': 0.0}, 
						**table_kwargs}

		image_kwargs = {**{'path': None, 'x': 0.5, 'y': 0.8, 'zoom': 0.08}, 
						**image_kwargs}

		figure = None

		if ax is None:
			figure = Figure_Lean(**kwargs)
			ax = figure.ax

		ax.plot(self.results_distances_sorted[:,-1], self.results_distances_sorted[:,-2], '.', 
				markersize = markersize, color = self.color, alpha = marker_alpha)
		ax.plot(self.distances_cost_savgol[:,0], self.distances_cost_savgol[:,1], color = self.color, 
				label = self.display_name, linewidth = linewidth)

		ax.axhspan(self.target_range[0], self.target_range[1], color = 'grey', alpha = 0.7)

		if log_scale:
			ax.set_yscale('log')
			fmt = mticker.StrMethodFormatter("{x:g}")
			ax.yaxis.set_major_formatter(fmt)

		if ylim is not None:
			ax.set_ylim(ylim[0], ylim[1])
		
		if xlim is not None:
			ax.set_xlim(xlim[0], xlim[1])

		ax.set_xlabel(xlabel_string)
		ax.set_ylabel(dependent_variable_label(self.dependent_variable) if ylabel_string is None else ylabel_string)
		ax.grid(color = 'grey', linestyle = '--', linewidth = 0.2, zorder = 0)
		ax.legend(loc = legend_loc)

		if parameter_table is True:
			self.render_parameter_table(ax, **table_kwargs)

		if image_kwargs['path'] is not None:
			insert_image(ax = ax, **image_kwargs)

		if figure_lean is True and figure is not None:
			figure.execute()
			return figure.fig

	def plot_target_parameters_by_distance(self,
										   log_normalize: bool = False,
										   title: bool = True,
										   title_string: str = 'Target range:',
										   xlabel_string: str = 'Development distance',
										   ylabel_string: str = 'Normalized value (0: base, 1: limit)',
										   markersize: float = 6,
										   image_kwargs: dict = {},
										   plot_kwargs: dict = {},
										   **kwargs) -> Figure:
		'''Plotting normalized parameter values of the models within the target range against
		their development distance, with one panel per parameter.

		Parameters
		----------
		log_normalize : bool, optional
			Flag to control if log normalization is used instead of linear normalization
			(see :func:`normalize_parameter`).
		title : bool, optional
			Flag to control if title is displayed or not.
		title_string : str, optional
			String for title (followed by the target range).
		xlabel_string : str, optional
			String for x axis label.
		ylabel_string : str, optional
			String for y axis label (shared by all panels).
		markersize : float, optional
			Size of markers.
		image_kwargs: dict, optional
			Dictionary containing optional keyword arguments for
			:func:`~pyH2A.Utilities.output_utilities.insert_image` (image is inserted in first panel).
		plot_kwargs: dict, optional
			Dictionary containing optional keyword arguments for
			:func:`~pyH2A.Utilities.output_utilities.Figure_Lean`, has priority over `**kwargs`.
		**kwargs: 
			Additional `kwargs` passed to 
			:func:`~pyH2A.Utilities.output_utilities.Figure_Lean`

		Returns 
		-------
		figure : matplotlib.figure.Figure
			matplotlib figure.

		Raises
		------
		ValueError
			If no sample lies within the target range.

		Notes
		-----
		Parameter values are normalized so that the base value corresponds to 0 and the limit 
		value to 1. Each panel is titled with the name of its parameter. The plot shows how much each
		parameter has to be changed to reach the target range at a given development distance.
		'''

		self._require_target_range_samples()

		number_of_parameters = len(self.parameters)

		kwargs = {**{'left': 0.14, 'right': 0.95, 'bottom': 0.4 / number_of_parameters, 'top': 1. - 0.4 / number_of_parameters, 
					 'hspace': 0.7, 'nrows': number_of_parameters, 'sharex': True,
					 'fig_width': 7, 'fig_height': 1.4 * number_of_parameters + 1, 'font_size': 12,
					 'name': 'Monte_Carlo_Target_Parameters_By_Distance', 'directory': '.'}, 
				  **kwargs, **plot_kwargs}

		image_kwargs = {**{'path': None, 'x': 0.5, 'y': 0.8, 'zoom': 0.08}, 
						**image_kwargs}

		figure = Figure_Lean(**kwargs)
		axes = np.atleast_1d(figure.ax)

		distances = self.target_distances_sorted[:,-1]

		# One panel per parameter (small multiples), all sharing the same x axis and normalized y range
		for ax, (name, parameter) in zip(axes, self.parameters.items()):
			normalized_values = normalize_parameter(self.target_distances_sorted[:,parameter['Index']], 
													parameter['Reference'], parameter['Limit'],
													log_normalize = log_normalize)
			ax.plot(distances, normalized_values, 'o', markersize = markersize, color = self.color)
			ax.set_title(name, loc = 'left', fontsize = 'medium')
			ax.set_ylim(-0.15, 1.15)
			ax.set_yticks([0., 0.5, 1.])
			ax.grid(color = 'grey', linestyle = '--', linewidth = 0.2, zorder = 0)

		axes[-1].set_xlabel(xlabel_string)
		figure.fig.supylabel(ylabel_string, fontsize = 'medium')

		if title is True:
			figure.fig.suptitle(self._target_range_title(title_string))

		if image_kwargs['path'] is not None:
			insert_image(ax = axes[0], **image_kwargs)

		figure.execute()

		return figure.fig
