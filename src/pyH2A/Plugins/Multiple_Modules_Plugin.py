import numpy as np
from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity

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
					"optional": True,
					"description": "Solar collection area for one plant module."
				},
			},
			"Battery": {
				"Number of needed modules": {
					"Value": {
						"type": {float, int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "dimensionless",
					},
					"optional": True,
					"description": "Number of battery modules."
				},
			},		
			"Wind Turbine": {
				"Number of wind turbines": {
					"Value": {
						"type": {float, int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "dimensionless",
					},
					"optional": True,
					"description": "Number of wind turbines needed to match the required installed power."
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
					"optional": True,
					"description": "Solar collection area that can be covered by one staffer."
				},
				"Battery modules per staffer": {
					"Value": {
						"type": {int, float,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "dimensionless",
					},
					"optional": True,
					"description": "Number of battery modules that can be handeled by one staffer."
				},
				"Wind turbines per staffer": {
					"Value": {
						"type": {int, float,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "dimensionless",
					},
					"optional": True,
					"description": "Number of battery modules that can be maintained by one staffer."
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

	def _run(self, dcf):
		self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, 'Multiple_Modules_Plugin')
		
		self.required_staff()
		
		output_inserter_function(self.output_dict, self, dcf, 'Multiple_Modules_Plugin') 

	def required_staff(self):
		'''Calculation of total required staff for all plant modules, then scaling down to staff
		requirements for one module.'''

		if 'Solar collection area' in self.input_dict_resolved['Non-Depreciable Capital Costs']:
			area = (self.input_dict_resolved['Technical Operating Parameters and Specifications']['Plant modules']['Value'].unit['-'] 
				* self.input_dict_resolved['Non-Depreciable Capital Costs']['Solar collection area']['Value'].unit['m2'])

			staff_solar = (np.ceil(area 
							/ self.input_dict_resolved['Fixed Operating Costs']['Solar collection area per staffer']['Value'].unit['m2'])
							)
		else:
			staff_solar = 0

		if 'Wind Turbine' in self.input_dict_resolved:
			turbines_number = (self.input_dict_resolved['Technical Operating Parameters and Specifications']['Plant modules']['Value'].unit['-'] 
				* self.input_dict_resolved['Wind Turbine']['Number of wind turbines']['Value'].unit['-'])

			staff_wind = (np.ceil(turbines_number 
							/ self.input_dict_resolved['Fixed Operating Costs']['Wind turbines per staffer']['Value'].unit['-'])
							)
		else:
			staff_wind = 0

		if 'Battery' in self.input_dict_resolved and 'Number of needed modules' in self.input_dict_resolved['Battery']:
			storage = (self.input_dict_resolved['Technical Operating Parameters and Specifications']['Plant modules']['Value'].unit['-'] 
				* self.input_dict_resolved['Battery']['Number of needed modules']['Value'].unit['-'])
			
			staff_storage = (np.ceil(storage 
							/ self.input_dict_resolved['Fixed Operating Costs']['Battery modules per staffer']['Value'].unit['-'])
							)
		else:
			staff_storage = 0
		
		staff = ((staff_solar + staff_wind + staff_storage + self.input_dict_resolved['Fixed Operating Costs']['Number of supervisors']['Value'].unit['-']) 
		   			* self.input_dict_resolved['Fixed Operating Costs']['Number of 8-hour shifts']['Value'].unit['-']
					)

		self.staff_per_module = Quantity(staff 
										 / self.input_dict_resolved['Technical Operating Parameters and Specifications']['Plant modules']['Value'].unit['-'], 
								'-')
