from pyH2A.Utilities.input_modification import sum_all_tables
from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity

input_dict_fixed = {
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

input_dict_other = {

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

output_dict_fixed = {
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

output_dict_total = {
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
                "Summed total": {
                    "Value": {
                        "type": {float},
                    },
                    "optional": False,
                    "description": "Summed total of other fixed operating costs for each table"
                },
            },
            "Other Fixed Operating Cost": {
                "Summed group total": {
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

class Fixed_Operating_Cost_Plugin:
	'''Calculation of yearly fixed operating costs.

	Parameters
	----------
	Fixed Operating Costs > staff > Value : float
		Number of staff.
	Fixed Operating Costs > hourly labor cost > Value : float
		Hourly labor cost of staff.
	<...> Other Fixed Operating Cost <...> >> Value : float
		Yearly other fixed operating costs, ``sum_all_tables()`` is used.

	Returns
	-------
	<...> Other Fixed Operating Cost <...> > Summed total > Value : float
		Summed total for each individual table in "Other Fixed Operating Cost" group.
	Other Fixed Operating Cost > Summed group total > Value : float
		Summed total for each individual table in "Other Fixed Operating Cost" group.		
	Fixed Operating Costs > Labor Cost - Uninflated > Value : float
		Yearly total labor cost.
	Fixed Operating Costs > Labor Cost > Value : float
		Yearly total labor cost multiplied by labor inflator.
	Fixed Operating Costs > Total > Value : float
		Sum of total yearly labor costs and yearly other fixed operating costs.
	'''


	def __init__(self, dcf, print_info):
		self.input_dict_resolved_fixed = input_resolver_function(input_dict_fixed, dcf, 'Fixed_Operating_Cost_Plugin')
		
		labor_uninflated, labor = self.labor_cost(dcf)
		self.labor_uninflated = Quantity(labor_uninflated, 'USD')
		self.labor = Quantity(labor, 'USD')	

		output_inserter_function(output_dict_fixed, self, dcf, 'Fixed_Operating_Cost_Plugin')  

		self.input_dict_resolved_other = input_resolver_function(input_dict_other, dcf, 'Fixed_Operating_Cost_Plugin')

		other = self.other_cost()	
		self.total_fixed_operating_cost = Quantity(labor + other, 'USD')		

		output_inserter_function(output_dict_total, self, dcf, 'Fixed_Operating_Cost_Plugin')  

	def labor_cost(self, dcf):
		'''Calculation of yearly labor costs by multiplying number of staff times hourly labor cost.'''
		work_hours_per_year = 2080.
		labor_uninflated = self.input_dict_resolved_fixed['Fixed Operating Costs']['Staff']['Value'].unit['-'] * self.input_dict_resolved_fixed['Fixed Operating Costs']['Hourly labor cost']['Value'].unit['USD/h']*work_hours_per_year
		labor = labor_uninflated * dcf.labor_inflator 

		return labor_uninflated, labor
	
	def other_cost(self):
		'''Calculation of yearly other fixed operating costs by applying ``sum_all_tables()`` 
		to "Other Fixed Operating Cost" group.'''
		other = self.input_dict_resolved_other['Other Fixed Operating Cost']['Summed group total']['Value'].unit['USD']

		return other 

