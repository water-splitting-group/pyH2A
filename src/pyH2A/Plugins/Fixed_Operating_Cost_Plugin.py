from pyH2A.Utilities.input_modification import insert, sum_all_tables, process_table

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
				"insert_value": "labor_uninflated",
				"type": {float,},
				"dimension": "currency / time",
			},	
			"optional": False,
			"description": "Yearly total labor cost without applying labor inflator."
		},
		"Labor cost": {
			"Value": {
				"insert_value": "labor",
				"type": {float,},
				"dimension": "currency / time",	
			},
			"optional": False,
			"description": "Yearly total labor cost after applying labor inflator."
		},
		"Total": {
			"Value": {
				"insert_value": "labor + other",
				"type": {float,},
				"dimension": "currency / time",	
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
	[...] Other Fixed Operating Cost [...] >> Value : float
		Yearly other fixed operating costs, ``sum_all_tables()`` is used.

	Returns
	-------
	[...] Other Fixed Operating Cost [...] > Summed Total > Value : float
		Summed total for each individual table in "Other Fixed Operating Cost" group.
	Fixed Operating Costs > Labor Cost - Uninflated > Value : float
		Yearly total labor cost.
	Fixed Operating Costs > Labor Cost > Value : float
		Yearly total labor cost multiplied by labor inflator.
	Fixed Operating Costs > Total > Value : float
		Sum of total yearly labor costs and yearly other fixed operating costs.
	'''


	def __init__(self, dcf, print_info):
		self.labor_cost(dcf)
		insert(dcf, 'Fixed Operating Costs', 'Labor Cost - Uninflated', 'Value', self.labor_uninflated, __name__, print_info = print_info)
		insert(dcf, 'Fixed Operating Costs', 'Labor Cost', 'Value', self.labor, __name__, print_info = print_info)

		self.other_cost(dcf, print_info)
		insert(dcf, 'Fixed Operating Costs', 'Total', 'Value', self.labor + self.other, __name__, print_info = print_info)

	def labor_cost(self, dcf):
		'''Calculation of yearly labor costs by multiplying number of staff times hourly labor cost.'''

		process_table(dcf.inp, 'Fixed Operating Costs', 'Value')

		self.labor_uninflated = dcf.inp['Fixed Operating Costs']['staff']['Value'] * dcf.inp['Fixed Operating Costs']['hourly labor cost']['Value'] * 2080.
		self.labor = self.labor_uninflated * dcf.labor_inflator 
	
	def other_cost(self, dcf, print_info):
		'''Calculation of yearly other fixed operating costs by applying ``sum_all_tables()`` 
		to "Other Fixed Operating Cost" group.'''

		self.other = sum_all_tables(dcf.inp, 'Other Fixed Operating Cost', 'Value', insert_total = True, class_object = dcf, print_info = print_info) * dcf.combined_inflator

