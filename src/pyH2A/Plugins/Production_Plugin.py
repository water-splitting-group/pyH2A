from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
import numpy as np

class Production_Plugin:

	def __init__(self, dcf, print_info, run = True):
		self._set_up(dcf)
		if run:
			self._run(dcf)

	def _set_up(self, dcf):

		self.functional_unit = dcf.functional_unit

		self.input_dict = {
		    "Time": {
		        "Years": {
		            "Value": {
		                "type": {dict,},
		                "bounds": (None, None),
		            },
		            "Unit": {
		                "dimension": "dimensionless",
		            },
		            "optional": False,
		            "description": "Dictionary containing all time-related quantities."
		        }, 
		    },    	
		    "Technical Operating Parameters and Specifications": {
				"Plant design capacity": { 
					"Value": {
						"type": {float, int}, 
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": f"{self.functional_unit.dimension}/time",
					},
					"optional": True,
					"description": "Plant design capacity in functional unit of product / time."
				},
				"Design output by year": { 
					"Value": {
						"type": {np.ndarray},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": self.functional_unit.dimension,
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

		self.output_dict = {
			"Technical Operating Parameters and Specifications": {
				"Design output by year": { 
					"Value": {
						"inserted_value": "design_output_by_year",
						"type": {np.ndarray,},
						"dimension": self.functional_unit.dimension,
					},
					"optional": False,
					"description": "Yearly output, ignoring the capacity factor."
				},
				"Total design output": { 
					"Value": {
						"inserted_value": "sum_design_output",
						"type": {float, int},
						"dimension": self.functional_unit.dimension,
					},
					"optional": False,
					"description": "Cumulated output during plant lifetime, ignoring the capacity factor."
				},		
				"Output at gate by year": { 
					"Value": {
						"inserted_value": "output_per_year_at_gate",
						"type": {np.ndarray,},
						"dimension": self.functional_unit.dimension,
					},
					"optional": False,
					"description": "Actual output at gate by year."
				},
				"Total output at gate": { 
					"Value": {
						"inserted_value": "sum_output_gate",
						"type": {float, int},
						"dimension": self.functional_unit.dimension,
					},
					"optional": False,
					"description": "Cumulated output at gate during plant lifetime."
				},			
			},
		}

	def _run(self, dcf):
		self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, 'Production_Plugin')

		self.calculate_output()

		output_inserter_function(self.output_dict, self, dcf, 'Production_Plugin')     

	def calculate_output(self):
		'''Calculation of yearly output and yearly output at gate, 
		as well as their sum over the plant lifetime.
		'''

		operating_parameters = self.input_dict_resolved['Technical Operating Parameters and Specifications']

		# Use design output by year array, if available
		if 'Design output by year' in operating_parameters:
			self.design_output_by_year = operating_parameters['Design output by year']['Value']

		# Otherwise fall back to plant design capacity
		else:
			design_output_by_year_funct_units = (operating_parameters['Plant design capacity']['Value'].unit[self.functional_unit.unit_per_year]
							   			         * self.input_dict_resolved['Time']['Years']['Value']['Operation years ones'].unit['-'])
			self.design_output_by_year = Quantity(design_output_by_year_funct_units, self.functional_unit.unit)

		# Calculation of output at gate by year array,
		# by multiplying design output with operating capacity factor (what fraction of time is the plant operating)
		# and with the fraction of output that reaches the gate (what fraction of the raw production reaches the gate after losses)
		self.output_per_year_at_gate = Quantity(self.design_output_by_year.unit[self.functional_unit.unit]
										        * operating_parameters['Operating capacity factor']['Value'].unit['-']
										        * operating_parameters['Fraction of output that reaches gate']['Value'].unit['-'],
												self.functional_unit.unit)

		# Computing sum of design output and output at gate
		self.sum_design_output = Quantity(np.sum(self.design_output_by_year.unit[self.functional_unit.unit]), self.functional_unit.unit)
		self.sum_output_gate = Quantity(np.sum(self.output_per_year_at_gate.unit[self.functional_unit.unit]), self.functional_unit.unit)