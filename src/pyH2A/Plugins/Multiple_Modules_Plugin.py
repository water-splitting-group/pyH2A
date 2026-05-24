import numpy as np
from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity

input_dict = {
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
				"type": {float,},
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
				"type": {float,},
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

output_dict = {
	"Fixed Operating Costs": {
		"Staff": {
			"Value": {
				"inserted_value": "staff_per_module",
				"type": {float,},
				"dimension": "dimensionless",
			},
			"description": "Number of 8-hour equivalent staff required for operating one plant module.",
			"optional": False,
		},
	},
}

class Multiple_Modules_Plugin:
	''' Simulating mutliple plant modules which are operated together, assuming that only labor cost is reduced. 
	Calculation of required labor to operate all modules, scaling down labor requirement to one module for subsequent calculations.

	Parameters
	----------
	Technical Operating Parameters and Specifications > Plant modules > Value : float or int
		Number of plant modules considered in this calculation.
	Non-Depreciable Capital Costs > Solar collection area > Value : float
		Solar collection area for one plant module.
	Fixed Operating Costs > Solar collection area per staffer > Value : float
		Solar collection area that can be covered by one staffer.
	Fixed Operating Costs > Number of 8-hour shifts > Value : float or int
		Number of 8-hour shifts (typically 3 for 24h operation).
	Fixed Operating Costs > Number of supervisors > Value : float or int
		Number of shift supervisors.

	Returns
	-------
	Fixed Operating Costs > Staff > Value : float
		Number of 8-hour equivalent staff required for operating one plant module.
	''' 

	def __init__(self, dcf, print_info):
		self.input_dict_resolved = input_resolver_function(input_dict, dcf, 'Multiple_Modules_Plugin')
		
		self.required_staff()
		
		output_inserter_function(output_dict, self, dcf, 'Multiple_Modules_Plugin') 

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
