import copy
import numpy as np
from scipy.optimize import (minimize,
							dual_annealing,
							differential_evolution,
							shgo)
import matplotlib.pyplot as plt

from timeit import default_timer as timer

import pyH2A.Utilities.find_nearest as fn
from pyH2A.Utilities.input_modification import (convert_input_to_dictionary,
												parse_parameter,
												parse_parameter_to_array,
												get_by_path,
												set_by_path,
												read_textfile,
												file_import,
												reverse_parameter_to_string)
from pyH2A.Discounted_Cash_Flow import Discounted_Cash_Flow
from pyH2A.Utilities.output_utilities import (make_bold,
											  format_scientific,
											  dynamic_value_formatting,
											  insert_image,
											  Figure_Lean)
from pyH2A.Utilities.dependent_variable_resolution import resolve_dependent_variable, configure_dependent_variable, DEFAULT_DEPENDENT_VARIABLE_STRING


def _optimization_objective(values, parameters, inp, dependent_variable_string):
	'''Module-level objective function for ``scipy.optimize`` (e.g. ``differential_evolution``).

	Parameters
	----------
	values : ndarray
		Candidate parameter values, one per entry in `parameters`.
	parameters : list
		Parameter paths (location within `inp`); format: [top_key, middle_key, bottom_key].
	inp : dict
		Full input dictionary template.
	dependent_variable_string : str
		Path with unit, in "{top_key > middle_key > bottom_key, unit}" notation,
		identifying which value to minimize.

	Returns
	-------
	float
		Resolved dependent variable value for this candidate.
	'''

	input_dict = copy.deepcopy(inp)

	for value, parameter in zip(values, parameters):
		set_by_path(input_dict, parameter, value)

	dcf = Discounted_Cash_Flow(input_dict, print_info = False)

	return resolve_dependent_variable(dcf, dependent_variable_string)

class Optimization_Analysis:
	'''Optimization of pyH2A models.

	Parameters
	----------
	Optimization_Analysis > Dependent Variable > Value : str, optional
		Path (with unit) identifying which value to minimize, in
		"{top_key > middle_key > bottom_key, unit}" notation. If the
		`Optimization_Analysis` table or the `Dependent Variable` row is missing
		entirely, this silently defaults to H2 cost.
	Optimization_Analysis > Dependent Variable > Label : str, optional
		Bare descriptive name used when reporting results, e.g. 'H2 Cost'. Defaults to
		the path's last component if not provided.
	'''

	def __init__(self, input_file):
		'''
		'''

		self.inp = convert_input_to_dictionary(input_file)

		(self.dependent_variable_string, self.dependent_variable_header,
		 self.dependent_variable_unit, self.dependent_variable_label) = configure_dependent_variable(
			self.inp, 'Optimization_Analysis', default_string = DEFAULT_DEPENDENT_VARIABLE_STRING)
		self.process_parameters()
		self.perform_optimization()

	def process_parameters(self):
		'''Processing of parameters that are to be optimized. Parsing of parameter path and
		bounds (seperated by `;`).
		'''

		parameters = self.inp['Parameters - Optimization_Analysis']

		self.parameters = []
		self.bounds = []

		for counter, key in enumerate(parameters):

			parameter = parse_parameter(key)
			bounds = parse_parameter_to_array(parameters[key]['Bounds'], delimiter = ';', 
											  dictionary = self.inp, 
											  top_key = 'Parameters - Optimization_Analysis', 
											  middle_key = key, bottom_key = 'Bounds', 
											  special_values = ['Base', 'Reference'], 
											  path = key)

			self.parameters.append(parameter)
			self.bounds.append(bounds)

		self.bounds = np.asarray(self.bounds)
		self.bounds = np.sort(self.bounds, axis = 1)

	def perform_optimization(self):
		'''Performing optimization using differential evolution algorithm and 
		printing results.
		'''

		p = differential_evolution(func = _optimization_objective,
								   bounds = self.bounds,
								   args = (self.parameters, self.inp, self.dependent_variable_string))

		print('Optimization results:')
		print('--------------------------------------------------------------------------------')
		print(p)
		print('--------------------------------------------------------------------------------')

		for counter, parameter in enumerate(self.parameters):
			print(f'{parameter[0]} > {parameter[1]} > {parameter[2]}	 optimal value is {p.x[counter]}')

		print(f'Optimal {self.dependent_variable_label}: {p.fun} {self.dependent_variable_unit}')
		print('--------------------------------------------------------------------------------')


