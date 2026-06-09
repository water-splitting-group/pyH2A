from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
import numpy as np

input_dict = {
    "Technical Operating Parameters and Specifications": {
		"Plant design capacity": { 
			"Value": {
				"type": {float, int}, 
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": "mass/time",
			},
			"optional": True,
			"description": "Plant design capacity in mass of H2 / time."
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
		"Design output by year": { 
			"Value": {
				"type": {np.ndarray},
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": "mass",
			},
			"optional": True,
			"description": "Yearly production of hydrogen, ignoring the capacity factor"
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
				"dimension": "mass",
			},
			"optional": False,
			"description": "Yearly output, ignoring the capacity factor."
		},
		"Sum of design output": { 
			"Value": {
				"inserted_value": "sum_design_output",
				"type": {float, int},
				"dimension": "mass",
			},
			"optional": False,
			"description": "Cumulated output during plant lifetime, ignoring the capacity factor."
		},		
		"Output at gate by year": { 
			"Value": {
				"inserted_value": "output_per_year_at_gate",
				"type": {np.ndarray,},
				"dimension": "mass",
			},
			"optional": False,
			"description": "Actual yearly output at gate."
		},
		"Sum of output at gate": { 
			"Value": {
				"inserted_value": "sum_output_gate",
				"type": {float, int},
				"dimension": "mass",
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
		Plant design capacity in mass per time.
	Technical Operating Parameters and Specifications > Operating capacity factor > Value : float
		Operating capacity factor value between 0 and 1.
	Technical Operating Parameters and Specifications > Design output by year > Value : np.ndarray
		Yearly production of hydrogen, ignoring the capacity factor.
	Technical Operating Parameters and Specifications > Fraction of output that reaches gate > Value : float
		Ratio between the gate production and the raw production.
		
	Returns
	-------
	Technical Operating Parameters and Specifications > Design output by year > Value : np.ndarray
		Yearly production of hydrogen, ignoring the capacity factor.
	Technical Operating Parameters and Specifications > Sum of design output > Value : float, int
		Cumulated output during plant lifetime, ignoring the capacity factor
	Technical Operating Parameters and Specifications > Output at gate by year > Value : np.ndarray
		Actual yearly output at gate.
	Technical Operating Parameters and Specifications > Sum of output at gate > Value : float
		Cumulated output at gate during plant lifetime.

	'''

	def __init__(self, dcf, print_info):
		self.input_dict_resolved = input_resolver_function(input_dict, dcf, 'Production_Plugin')
		self.dictionary = self.input_dict_resolved['Technical Operating Parameters and Specifications']

		self.calculate_output(dcf)

		output_inserter_function(output_dict, self, dcf, 'Production_Plugin')     

	def calculate_output(self, dcf):
		'''Calculation of yearly output and yearly output at gate, as well as their sum over the plant lifetime.
		'''

		if 'Plant design capacity' in self.dictionary and 'Design output by year' not in self.dictionary:
			design_output_kg_by_year = (self.dictionary['Plant design capacity']['Value'].unit['kg/year'] 
											* np.ones(len(dcf.inflation_factor))
										)
			
			design_output_kg_by_year[0:dcf.inp['Financial Input Values']['Construction time']['Value']] = 0.0

		elif 'Plant design capacity' not in self.dictionary and 'Design output by year' in self.dictionary:
			if len(dcf.inflation_factor) == len(self.dictionary['Design output by year']['Value'].unit['kg']):
				design_output_kg_by_year = self.dictionary['Design output by year']['Value'].unit['kg']  
			else:
				raise ValueError(
					f"Production plugin: Design output by year, of length "
					f"{len(self.dictionary['Design output by year']['Value'].unit['kg'])} "
					f", differs from the number of operation years {len(dcf.inflation_factor)}."
				)

		else:
			raise ValueError (f"Production plugin: either the Plant design capacity, or the Design output by year, must be specified.")

		self.design_output_by_year = Quantity(design_output_kg_by_year, "kg")

		output_kg_per_year_at_gate = (design_output_kg_by_year 
										* self.dictionary['Operating capacity factor']['Value'].unit['-'] 
										* self.dictionary['Fraction of output that reaches gate']['Value'].unit['-'])
		
		self.output_per_year_at_gate = Quantity(output_kg_per_year_at_gate, "kg")

		self.sum_design_output = Quantity(np.sum(design_output_kg_by_year), "kg")
		self.sum_output_gate = Quantity(np.sum(output_kg_per_year_at_gate), "kg")



