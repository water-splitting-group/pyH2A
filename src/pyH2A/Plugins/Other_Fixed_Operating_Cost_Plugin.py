from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity

input_dict = {
	"Fixed Operating Costs": {
		"Labor cost": {
			"Value": {
				"type": {float,},
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": "currency",
			},
			"optional": False,		
			"description": "Cost of labor."
		},
	},
	"<...> Other Fixed Operating Cost <...>": {
		"<...>": {
			"Value": {
				"type": {float,},	
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": "currency",
			},
			"optional": True,
			"description": "Yearly other fixed operating cost contribution, summed for each individual table in ther Fixed Operating Cost group."
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
				"type": {float,},
				"dimension": "currency",	
			},
			"optional": False,
			"description": "Total yearly fixed operating cost, sum of total labor cost and total other fixed operating cost."
		},
	},	
	"special_insertions":
		{"sum_all_tables": {
			"<...> Other Fixed Operating Cost <...>": {
				"Summed Total": {
					"Value": {
						"type": {float},
					},
					"optional": False,
					"description": "Summed total of other fixed operating costs across all tables"
				},
			},
		},
	},
}

class Other_Fixed_Operating_Cost_Plugin:
	'''Calculation of yearly fixed operating costs.

	Parameters
	----------
	<...> Other Fixed Operating Cost <...> >> Value : float
		Yearly other fixed operating costs, ``sum_all_tables()`` is used.

	Returns
	-------
	<...> Other Fixed Operating Cost <...> > Summed Total > Value : float
		Summed total for each individual table in "Other Fixed Operating Cost" group.
	Fixed Operating Costs > Total > Value : float
		Sum of total yearly labor costs and yearly other fixed operating costs.
	'''


	def __init__(self, dcf, print_info):

		self.input_dict_resolved = input_resolver_function(input_dict, dcf, 'Other_Fixed_Operating_Cost_Plugin')

		labor = self.input_dict_resolved['Fixed Operating Costs']['Labor cost']['Value'].unit['USD']
		other = self.other_cost(dcf)	
		self.total_fixed_operating_cost = Quantity(labor + other, 'USD')		

		output_inserter_function(output_dict, self, dcf, 'Other_Fixed_Operating_Cost_Plugin')  

	
	def other_cost(self, dcf):
		'''Calculation of yearly other fixed operating costs by applying ``sum_all_tables()`` 
		to "Other Fixed Operating Cost" group.'''
		other = self.input_dict_resolved['Other Fixed Operating Cost']['Summed group total']['Value'].unit['USD'] * dcf.combined_inflator

		return other 

