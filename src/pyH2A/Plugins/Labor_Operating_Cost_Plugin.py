from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity

input_dict = {
	"Fixed Operating Costs": {
		"Staff": {
			"Value": {
				"type": {float,},
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": "dimensionless",
			},
			"optional": False,		
			"description": "Number of staff."
		},
		"Hourly labor cost": {
			"Value": {
				"type": {float,},
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": "currency / time",
			},
			"optional": False,
			"description": "Hourly labor cost of staff."
		},
	},
}

output_dict = {
	"Fixed Operating Costs": {
		"Labor cost - uninflated": {
			"Value": {
				"inserted_value": "labor_uninflated",
				"type": {float,},
				"dimension": "currency",
			},	
			"optional": False,
			"description": "Yearly total labor cost without applying labor inflator."
		},
		"Labor cost": {
			"Value": {
				"inserted_value": "labor",
				"type": {float,},
				"dimension": "currency",	
			},
			"optional": False,
			"description": "Yearly total labor cost after applying labor inflator."
		},
	},
}


class Labor_Operating_Cost_Plugin:
	'''Calculation of yearly Labor operating costs.

	Parameters
	----------
	Fixed Operating Costs > staff > Value : float
		Number of staff.
	Fixed Operating Costs > hourly labor cost > Value : float
		Hourly labor cost of staff.

	Returns
	-------
	Fixed Operating Costs > Labor Cost - Uninflated > Value : float
		Yearly total labor cost.
	Fixed Operating Costs > Labor Cost > Value : float
		Yearly total labor cost multiplied by labor inflator.
	'''


	def __init__(self, dcf, print_info):
		self.input_dict_resolved = input_resolver_function(input_dict, dcf, 'Labor_Operating_Cost_Plugin')
		
		labor_uninflated, labor = self.labor_cost(dcf)
		self.labor_uninflated = Quantity(labor_uninflated, 'USD')
		self.labor = Quantity(labor, 'USD')	

		output_inserter_function(output_dict, self, dcf, 'Labor_Operating_Cost_Plugin')  


	def labor_cost(self, dcf):
		'''Calculation of yearly labor costs by multiplying number of staff times hourly labor cost.'''
		work_hours_per_year = 2080.
		labor_uninflated = self.input_dict_resolved['Fixed Operating Costs']['Staff']['Value'].unit['-'] * self.input_dict_resolved['Fixed Operating Costs']['Hourly labor cost']['Value'].unit['USD/h']*work_hours_per_year
		labor = labor_uninflated * dcf.labor_inflator 

		return labor_uninflated, labor
	


