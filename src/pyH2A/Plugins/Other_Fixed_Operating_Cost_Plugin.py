from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity

input_dict = {
	"Fixed Operating Costs": {
		"Labor cost - inflated": {
			"Value": {
				"type": {int, float,},
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": "currency",
			},
			"description": "Yearly total labor cost after applying labor inflator."
		},
	},
	"<...> Other Fixed Operating Cost <...>": {
		"<...>": {
			"Value": {
				"type": {int, float,},	
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": "currency",
			},
			"optional": True,
			"description": "Other yearly fixed operating costs."
		},
		'sum_tables': {
			'mode': 'all',
			'arguments': {
				'bottom_key': 'Value',
				'middle_key_total_insertion': 'Summed total',
				'middle_key_total_group_insertion': 'Summed group total',
				'middle_key_contributions_insertion': 'Contributions',
				'bottom_key_insertion': 'Value'
			}
		},			
	},
}

output_dict = {
	"Fixed Operating Costs": {
		"Total": {
			"Value": {
				"inserted_value": "total_fixed_operating_cost",
				"type": {int, float,},
				"dimension": "currency",	
			},
			"optional": False,
			"description": "Total yearly fixed operating cost, sum of total labor cost and total other fixed operating cost, with inflators applied."
		},
	},	
	"special_insertions":
		{"sum_all_tables": {
			"<...> Other Fixed Operating Cost <...>": {
				"Summed total": {
					"Value": {
						"type": {int, float},
						"dimension": "currency"
					},
					"description": "Summed total of other fixed operating costs for each table."
				},
			},
			"Other Fixed Operating Cost": {
				"Summed total": {
					"Value": {
						"type": {int, float},
						"dimension": "currency"
					},
					"description": "Summed total of other fixed operating costs for this table."
				},
				"Summed group total": {
					"Value": {
						"type": {int, float},
						"dimension": "currency"
					},
					"description": "Summed total of other fixed operating costs for all the tables"
				},
				"Contributions": {
					"Value": {
						"type": {int, float},
						"dimension": "currency"
					},
					"description": "Contribution of each table to total other fixed operating costs."
				},
			},			
		},
	},
}

class Other_Fixed_Operating_Cost_Plugin:
	'''Calculation of yearly fixed operating costs.

	Parameters
	----------
	Fixed Operating Costs > Labor Cost - inflated > Value : float, int
		Yearly total labor cost after applying labor inflator.
	<...> Other Fixed Operating Cost <...> >> Value : float
		Yearly other fixed operating costs, ``sum_all_tables()`` is used.

	Returns
	-------
	<...> Other Fixed Operating Cost <...> > Summed total > Value : float
		Summed total for each individual table in "Other Fixed Operating Cost" group.
	Other Fixed Operating Cost > Summed group total > Value : float
		Summed total for all the tables in "Other Fixed Operating Cost" group.		
	Fixed Operating Costs > Total > Value : float
		Sum of total yearly labor costs and yearly other fixed operating costs.
	'''
	def __init__(self, dcf, print_info):

		self.input_dict_resolved = input_resolver_function(input_dict, dcf, 'Other_Fixed_Operating_Cost_Plugin')

		self.total_fixed_operating_cost = self.calculate_total_fixed_operating_cost(dcf)

		output_inserter_function(output_dict, self, dcf, 'Other_Fixed_Operating_Cost_Plugin')  

	def calculate_total_fixed_operating_cost(self, dcf):
		'''Calculation of total fixed operating cost by summing total labor cost and total other fixed operating cost.'''

		labor = self.input_dict_resolved['Fixed Operating Costs']['Labor cost - inflated']['Value']
		other = self.input_dict_resolved['Other Fixed Operating Cost']['Summed group total']['Value']

		other_inflated = Quantity(other.unit['USD'] 
								  * dcf.combined_inflator, 
						 'USD')
		
		total = Quantity(labor.unit['USD'] + other_inflated.unit['USD'], 'USD')

		return total