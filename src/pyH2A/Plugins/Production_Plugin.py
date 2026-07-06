from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities import functional_unit as fu

import numpy as np

input_dict = {
    "Technical Operating Parameters and Specifications": {
		"Plant design capacity": { 
			"Value": {
				"type": {float, int}, 
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": fu.Functional_Dimension_dot,
			},
			"optional": True,
			"description": "Plant design capacity in functional units / time."
		},
		"Design output by year": { 
			"Value": {
				"type": {np.ndarray},
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": fu.Functional_Dimension,
			},
			"optional": True,
			"description": "Yearly production of product, ignoring the capacity factor"
		},
		"Operating capacity factor": { 
			"Value": {
				"type": {float, int},
				"bounds": (0, 1),
			},
			"Unit": {
				"dimension": "dimensionless",
			},
			"optional": False,
			"description": "Operating capacity factor value between 0 and 1."
		},
		"Fraction of output that reaches gate": { 
			"Value": {
				"type": {float},
				"bounds": (0, 1),
			},
			"Unit": {
				"dimension": "dimensionless",
			},
			"optional": False,
			"description": "Ratio between the gate production and the raw production"
		},
	},
}

output_dict = {
	"Technical Operating Parameters and Specifications": {
		"Design output by year": { 
			"Value": {
				"inserted_value": "design_output_by_year",
				"type": {np.ndarray,},
				"dimension": fu.Functional_Dimension,
			},
			"optional": False,
			"description": "Yearly output, ignoring the capacity factor."
		},
		"Total design output": { 
			"Value": {
				"inserted_value": "sum_design_output",
				"type": {float, int},
				"dimension": fu.Functional_Dimension,
			},
			"optional": False,
			"description": "Cumulated output during plant lifetime, ignoring the capacity factor."
		},		
		"Output at gate by year": { 
			"Value": {
				"inserted_value": "output_per_year_at_gate",
				"type": {np.ndarray,},
				"dimension": fu.Functional_Dimension,
			},
			"optional": False,
			"description": "Actual output at gate by year."
		},
		"Total output at gate": { 
			"Value": {
				"inserted_value": "sum_output_gate",
				"type": {float, int},
				"dimension": fu.Functional_Dimension,
			},
			"optional": False,
			"description": "Cumulated output at gate during plant lifetime."
		},			
	},
}

class Production_Plugin:
	'''Calculation of plant output.

	Parameters
	----------
	Technical Operating Parameters and Specifications > Plant design capacity > Value : float or int
		Plant design capacity in functional unit per time.
	Technical Operating Parameters and Specifications > Design output by year > Value : np.ndarray
		Yearly production of the plant, ignoring the capacity factor.
	Technical Operating Parameters and Specifications > Operating capacity factor > Value : float
		Operating capacity factor value between 0 and 1.
	Technical Operating Parameters and Specifications > Fraction of output that reaches gate > Value : float
		Ratio between the gate production and the raw production.
		
	Returns
	-------
	Technical Operating Parameters and Specifications > Design output by year > Value : np.ndarray
		Yearly production of the plant, ignoring the capacity factor.
	Technical Operating Parameters and Specifications > Total design output > Value : float, int
		Cumulated output during plant lifetime, ignoring the capacity factor
	Technical Operating Parameters and Specifications > Output at gate by year > Value : np.ndarray
		Actual yearly output at gate.
	Technical Operating Parameters and Specifications > Total output at gate > Value : float
		Cumulated output at gate during plant lifetime.

	'''

	def __init__(self, dcf, print_info):
		self.input_dict_resolved = input_resolver_function(input_dict, dcf, 'Production_Plugin')

		self.calculate_output(dcf)

		output_inserter_function(output_dict, self, dcf, 'Production_Plugin')     

	def calculate_output(self, dcf):
		'''Calculation of yearly output and yearly output at gate, 
		as well as their sum over the plant lifetime.
		'''

		operating_parameters = self.input_dict_resolved['Technical Operating Parameters and Specifications']

		# Use design output by year array, if available
		if 'Design output by year' in operating_parameters:
			self.design_output_by_year = operating_parameters['Design output by year']['Value']

		# Otherwise fall back to plant design capacity
		else:
			# Horrible ugly mess, which will be fixed with time plugin
			design_output_by_year_funct_units = (operating_parameters['Plant design capacity']['Value'].unit[fu.Functional_Unit_per_year]
							   			* np.ones(len(dcf.inflation_factor)))
			design_output_by_year_funct_units[:dcf.inp['Financial Input Values']['Construction time']['Value']] = 0.0
			self.design_output_by_year = Quantity(design_output_by_year_funct_units, fu.Functional_Unit)

		# Calculation of output at gate by year array,
		# by multiplying design output with operating capacity factor (what fraction of time is the plant operating)
		# and with the fraction of output that reaches the gate (what fraction of the raw production reaches the gate after losses)
		self.output_per_year_at_gate = Quantity(self.design_output_by_year.unit[fu.Functional_Unit]
										        * operating_parameters['Operating capacity factor']['Value'].unit['-']
										        * operating_parameters['Fraction of output that reaches gate']['Value'].unit['-'],
												fu.Functional_Unit)

		# Computing sum of design output and output at gate
		self.sum_design_output = Quantity(np.sum(self.design_output_by_year.unit[fu.Functional_Unit]), fu.Functional_Unit)
		self.sum_output_gate = Quantity(np.sum(self.output_per_year_at_gate.unit[fu.Functional_Unit]), fu.Functional_Unit)