import numpy as np
from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.docstring_generation import generate_docstring

class Multiple_Modules_Plugin:

	def __init__(self, dcf, print_info, run = True):
		self._set_up(dcf)
		if run:
			self._run(dcf)

	def _set_up(self, dcf):

		self.functional_unit = dcf.functional_unit

		self.input_dict = {
			"Technical Operating Parameters and Specifications": {
				"Plant modules": {
					"Value": {
						"type": {float, int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "dimensionless",
					},
					"optional": False,
					"description": "Number of plant modules considered in this calculation."
				},
			},
			"Non-Depreciable Capital Costs": {
				"Solar collection area": {
					"Value": {
						"type": {int, float,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "area",
					},
					"optional": False,
					"description": "Solar collection area for one plant module."
				},
			},
			"Fixed Operating Costs": {
				"Solar collection area per staffer": {
					"Value": {
						"type": {int, float,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "area",
					},
					"optional": False,
					"description": "Solar collection area that can be covered by one staffer."
				},
				"Number of 8-hour shifts": {
					"Value": {
						"type": {float, int,},
						"bounds": (1, 3),
					},
					"Unit": {
						"dimension": "dimensionless",
					},
					"optional": False,
					"description": "Number of 8-hour shifts (typically 3 for 24h operation)."
				},
				"Number of supervisors": {
					"Value": {
						"type": {float, int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "dimensionless",
					},
					"optional": False,
					"description": "Number of shift supervisors."
				},
			},
		}

		self.output_dict = {
			"Fixed Operating Costs": {
				"Staff": {
					"Value": {
						"inserted_value": "staff_per_module",
						"type": {int, float,},
						"dimension": "dimensionless",
					},
					"description": "Number of 8-hour equivalent staff required for operating one plant module.",
					"optional": False,
				},
			},
		}
  
		summary = """
			Simulating mutliple plant modules which are operated together, assuming that only labor cost is reduced. 
			Calculation of required labor to operate all modules, scaling down labor requirement to one module for subsequent calculations.
  		"""
  
  
		self.__class__.__doc__ = generate_docstring(
            summary,
            self.input_dict,
            self.output_dict
        )

	def _run(self, dcf):
		self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, 'Multiple_Modules_Plugin')
		
		self.required_staff()
		
		output_inserter_function(self.output_dict, self, dcf, 'Multiple_Modules_Plugin') 

	def required_staff(self):
		'''Calculation of total required staff for all plant modules, then scaling down to staff
		requirements for one module.'''

		area = (self.input_dict_resolved['Technical Operating Parameters and Specifications']['Plant modules']['Value'].unit['-'] 
			   * self.input_dict_resolved['Non-Depreciable Capital Costs']['Solar collection area']['Value'].unit['m2'])

		staff = (np.ceil(area 
						 / self.input_dict_resolved['Fixed Operating Costs']['Solar collection area per staffer']['Value'].unit['m2'])
		         + self.input_dict_resolved['Fixed Operating Costs']['Number of supervisors']['Value'].unit['-'])
		
		staff = staff * self.input_dict_resolved['Fixed Operating Costs']['Number of 8-hour shifts']['Value'].unit['-']

		self.staff_per_module = Quantity(staff 
										 / self.input_dict_resolved['Technical Operating Parameters and Specifications']['Plant modules']['Value'].unit['-'], 
								'-')
