from pyH2A.Utilities.input_modification import sum_all_tables
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
                        "type": {int, float},
                    },
                    "optional": True,
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
		Number of staff, ``process_table()`` is used.
	Fixed Operating Costs > hourly labor cost > Value : float
		Hourly labor cost of staff, ``process_table()`` is used.
	<...> Other Fixed Operating Cost <...> >> Value : float
		Yearly other fixed operating costs, ``sum_all_tables()`` is used.

	Returns
	-------
	<...> Other Fixed Operating Cost <...> > Summed Total > Value : float
		Summed total for each individual table in "Other Fixed Operating Cost" group.
	Fixed Operating Costs > Labor Cost - Uninflated > Value : float
		Yearly total labor cost.
	Fixed Operating Costs > Labor Cost > Value : float
		Yearly total labor cost multiplied by labor inflator.
	Fixed Operating Costs > Total > Value : float
		Sum of total yearly labor costs and yearly other fixed operating costs.
	'''


	def __init__(self, dcf, print_info):
		self.input_dict_resolved = input_resolver_function(input_dict, dcf, 'Fixed_Operating_Cost_Plugin')
		
		self.labor_cost(dcf)
		other = self.other_cost(dcf, print_info)

		# The self variables are converted into Quantities at the last moment to avoid unnecessary complications
		self.labor_uninflated = Quantity(self.labor_uninflated, 'USD')
		self.total_fixed_operating_cost = Quantity(self.labor + other, 'USD')		
		self.labor = Quantity(self.labor, 'USD')
		output_inserter_function(output_dict, self, dcf, 'Fixed_Operating_Cost_Plugin')  

	def labor_cost(self, dcf):
		'''Calculation of yearly labor costs by multiplying number of staff times hourly labor cost.'''
		work_hours_per_year = 2080.
		self.labor_uninflated = self.input_dict_resolved['Fixed Operating Costs']['Staff']['Value'].unit['-'] * self.input_dict_resolved['Fixed Operating Costs']['Hourly labor cost']['Value'].unit['USD/h']*work_hours_per_year
		self.labor = self.labor_uninflated * dcf.labor_inflator 
	
	def other_cost(self, dcf, print_info):
		'''Calculation of yearly other fixed operating costs by applying ``sum_all_tables()`` 
		to "Other Fixed Operating Cost" group.'''
		other = sum_all_tables(self.input_dict_resolved, 'Other Fixed Operating Cost', 'Value', insert_total = True, class_object = dcf, print_info = print_info).unit['USD'] * dcf.combined_inflator

		return other 

