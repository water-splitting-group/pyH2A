from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity

input_dict = {
	"Inflation":{
		"Labor inflator": {
			"Value": {
				"type": {float,},
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": "dimensionless",
			},	
			"optional": False,
			"description": "Labor inflator."
		},
	},		
	"Fixed Operating Costs": {
		"Staff": {
			"Value": {
				"type": {int,float,},
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": "dimensionless",
			},
			"description": "Total Number of staff (full time equivalents) required for operation of the plant."
		},
		"Hourly labor cost": {
			"Value": {
				"type": {int, float,},
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": "currency / time",
			},
			"description": "Hourly labor cost of staff."
		},
	},
}

output_dict = {
	"Fixed Operating Costs": {
		"Labor cost": {
			"Value": {
				"inserted_value": "labor_uninflated",
				"type": {int, float,},
				"dimension": "currency",
			},	
			"description": "Yearly total labor cost without applying labor inflator."
		},
		"Labor cost - inflated": {
			"Value": {
				"inserted_value": "labor_inflated",
				"type": {int, float,},
				"dimension": "currency",	
			},
			"description": "Yearly total labor cost after applying labor inflator."
		},
	},
}


class Labor_Operating_Cost_Plugin:
	'''Calculation of yearly Labor operating costs.

	Parameters
	----------
	Inflation > Labor inflator > Value : float
		Cost of labor inflation factor. 
	Fixed Operating Costs > Staff > Value : float
		Number of staff.
	Fixed Operating Costs > Hourly labor cost > Value : float
		Hourly labor cost of staff.

	Returns
	-------
	Fixed Operating Costs > Labor Cost > Value : float
		Yearly total labor cost.
	Fixed Operating Costs > Labor Cost - Inflated > Value : float
		Yearly total labor cost multiplied by labor inflator.
	'''

	def __init__(self, dcf, print_info):
		self.input_dict_resolved = input_resolver_function(input_dict, dcf, 'Labor_Operating_Cost_Plugin')
		
		self.labor_uninflated, self.labor_inflated = self.labor_cost()

		output_inserter_function(output_dict, self, dcf, 'Labor_Operating_Cost_Plugin')  

	def labor_cost(self):
		'''Calculation of yearly labor costs by multiplying number of staff times hourly labor cost.'''

		work_hours_in_a_year = Quantity(2080, 'h') # Assuming 40 hours per week and 52 weeks per year

		labor_uninflated = Quantity(self.input_dict_resolved['Fixed Operating Costs']['Staff']['Value'].unit['-'] 
						            * self.input_dict_resolved['Fixed Operating Costs']['Hourly labor cost']['Value'].unit['USD/h']
						            * work_hours_in_a_year.unit['h'],
						   'USD')
		
		labor_inflated = Quantity(labor_uninflated.unit['USD'] 
								       * self.input_dict_resolved['Inflation']['Labor inflator']['Value'].unit['-'], 
						 'USD')
		
		return labor_uninflated, labor_inflated




