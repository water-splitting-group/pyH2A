from pyH2A.Utilities.input_modification import insert, sum_all_tables, process_table

input_dict = {
	"<...> Direct Capital Cost <...>": {
		"<...>": {
			"Value": {
				"type": {float,},
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": "currency",
			},	
			"optional": True,
			"description": "Direct capital cost contribution, summed for each individual table in 'Direct Capital Cost' group."
		},
	},
	"<...> Indirect Capital Cost <...>": {
		"<...>": {
			"Value": {
				"type": {float,},
				"bounds": (0, None),
			},	
			"Unit": {
				"dimension": "currency",
			},		
			"optional": True,
			"description": "Indirect capital cost contribution, summed for each individual table in 'Indirect Capital Cost' group."
		},
	},
	"Non-Depreciable Capital Costs": {
		"Cost of land": {
			"Value": {
				"type": {float,},
				"bounds": (0, None),
			},	
			"Unit": {
				"dimension": "currency / area",
			},		
			"optional": False,
			"description": "Cost per surface area."
		},
		"Land required": {
			"Value": {
				"type": {float,},
				"bounds": (0, None),
			},	
			"Unit": {
				"dimension": "area",
			},		
			"optional": False,
			"description": "Total land Area are required."
		},
	},
	"<...> Other Non-Depreciable Capital Cost <...>": {
		"<...>": {
			"Value": {
				"type": {float,},
				"bounds": (0, None),
			},	
			"Unit": {
				"dimension": "currency",
			},		
			"optional": True,
			"description": "Other non-depreciable capital cost contribution, summed for each individual table in 'Other Non-Depreciable Capital Cost' group."
		},
	}
}


output_dict = {
	"Direct Capital Costs": {
		"Total": {
			"Value": {
				"inserted_value": "direct",
				"type": {float,},	
				"dimension": "currency",
			},
			"description": "Total direct capital costs.",
			"optional": False,
		},
		"Inflated": {
			"Value": {
				"inserted_value": "direct_inflated",
				"type": {float,},
				"dimension": "currency",
			},
			"description": "Total direct capital costs multiplied by combined inflator.",
			"optional": False,
		},
	},
	"Indirect Capital Costs": {
		"Total": {
			"Value": {
				"inserted_value": "indirect",
				"type": {float,},
				"dimension": "currency",
			},
			"description": "Total indirect capital costs.",
			"optional": False,
		},
		"Inflated": {
			"Value": {
				"inserted_value": "indirect_inflated",
				"type": {float,},
				"dimension": "currency",
			},
			"description": "Total indirect capital costs multiplied by combined inflator.",
			"optional": False,
		},
	},
	"Non-Depreciable Capital Costs": {
		"Total": {
			"Value": {	
				"inserted_value": "non_depreciable",
				"type": {float,},
				"dimension": "currency",		
			},
			"description": "Total non-depreciable capital costs.",
			"optional": False,
		},
		"Inflated": {
			"Value": {
				"inserted_value": "non_depreciable_inflated",
				"type": {float,},
				"dimension": "currency",
			},
			"description": "Total non-depreciable capital costs multiplied by combined inflator.",
			"optional": False,
		},
	},
	"Depreciable Capital Costs": {
		"Total": {
			"Value": {
				"inserted_value": "depreciable",
				"type": {float,},
				"dimension": "currency",
			},	
			"description": "Total depreciable capital costs.",
			"optional": False,
		},
		"Inflated": {
			"Value": {
				"inserted_value": "depreciable_inflated",
				"type": {float,},	
				"dimension": "currency",
			},	
			"description": "Total depreciable capital costs multiplied by combined inflator.",
			"optional": False,
		},
	},
	"Total Capital Costs": {
		"Total": {
			"Value": {
				"inserted_value": "total",
				"type": {float,},
				"dimension": "currency",
			},	
			"description": "Total capital costs.",
			"optional": False,
		},
		"Inflated": {
			"Value": {
				"inserted_value": "total_inflated",
				"type": {float,},
				"dimension": "currency",
			},
			"description": "Total capital costs multiplied by combined inflator.",
			"optional": False,	
		},
	},
	"special_insertions":
        {"sum_all_tables": {
            "<...> Direct Capital Cost <...>": {
                "Summed Total": {
                    "Value": {
                        "type": {int, float},
                    },
                    "optional": True,
                    "description": "Summed total of direct capital costs across all tables"
                },
            },
            "<...> Indirect Capital Cost <...>": {
                "Summed Total": {
                    "Value": {
                        "type": {int, float},
                    },
                    "optional": True,
                    "description": "Summed total of indirect capital costs across all tables"
                },
            },
            "<...> Other Non-Depreciable Capital Cost <...>": {
                "Summed Total": {
                    "Value": {
                        "type": {int, float},
                    },
                    "optional": True,
                    "description": "Summed total of other non-depreciable capital costs across all tables"
                },
            },
        },
    },
}

class Capital_Cost_Plugin:
	'''

	Parameters
	----------
	[...] Direct Capital Cost [...] >> Value : float
		``sum_all_tables()`` is used.
	[...] Indirect Capital Cost [...] >> Value : float
		``sum_all_tables()`` is used.
	Non-Depreciable Capital Costs > Cost of land ($ per acre) > Value : float
		Cost of land in $ per acre, ``process_table()`` is used.
	Non-Depreciable Capital Costs > Land required (acres) > Value : float
		Total land are required in acres, ``process_table()`` is used.
	[...] Other Non-Depreciable Capital Cost [...] >> Value : float
		``sum_all_tables()`` is used.

	Returns
	-------
	[...] Direct Capital Cost [...] > Summed Total > Value : float
		Summed total for each individual table in "Direct Capital Cost" group.
	[...] Indirect Capital Cost [...] > Summed Total > Value : float
		Summed total for each individual table in "Indirect Capital Cost" group.
	[...] Other Non-Depreciable Capital Cost  [...] > Summed Total > Value : float
		Summed total for each individual table in "Other Non-Depreciable Capital Cost" group.
	Direct Capital Costs > Total > Value : float
		Total direct capital costs.
	Direct Capital Costs > Inflated > Value : float
		Total direct capital costs multiplied by combined inflator.
	Indirect Capital Costs > Total > Value : float
		Total indirect capital costs.
	Indirect Capital Costs > Inflated > Value : float
		Total indirect capital costs multiplied by combined inflator.
	Non-Depreciable Capital Costs > Total > Value : float
		Total non-depreciable capital costs.
	Non-Depreciable Capital Costs > Inflated > Value : float
		Total non-depreciable capital costs multiplied by combined inflator.
	Depreciable Capital Costs > Total > Value : float
		Sum of direct and indirect capital costs.
	Depreciable Capital Costs > Inflated > Value : float
		Sum of direct and indirect capital costs multiplied by combined inflator.
	Total Capital Costs > Total > Value : float
		Sum of depreciable and non-depreciable capital costs.
	Total Capital Costs > Inflated > Value : float
		Sum of depreicable and non-depreciable capital costs multiplied by combined inflator.
	['Capital_Cost_Plugin'].direct_contributions : dict
		Attribute containing cost contributions for "Direct Capital Cost" group.
	'''
	def __init__(self, dcf, print_info):

		self.direct_capital_costs(dcf, print_info)  
		direct_inflated = self.direct * dcf.combined_inflator

		insert(dcf, 'Direct Capital Costs', 'Total', 'Value', self.direct, __name__, print_info = print_info)
		insert(dcf, 'Direct Capital Costs', 'Inflated', 'Value', direct_inflated, __name__, print_info = print_info)

		self.indirect_capital_costs(dcf, print_info)

		indirect_inflated = self.indirect * dcf.combined_inflator
		depreciable = self.direct + self.indirect
		depreciable_inflated = direct_inflated + indirect_inflated
		
		insert(dcf, 'Indirect Capital Costs', 'Total', 'Value', self.indirect, __name__, print_info = print_info)
		insert(dcf, 'Indirect Capital Costs', 'Inflated', 'Value', indirect_inflated, __name__, print_info = print_info)
		
		insert(dcf, 'Depreciable Capital Costs', 'Total', 'Value', depreciable, __name__, print_info = print_info)
		insert(dcf, 'Depreciable Capital Costs', 'Inflated', 'Value', depreciable_inflated, __name__, print_info = print_info)
		
		self.non_depreciable_capital_costs(dcf, print_info)

		non_depreciable_inflated = self.non_depreciable * dcf.ci_inflator
		total = depreciable + self.non_depreciable
		total_inflated = depreciable_inflated + non_depreciable_inflated

		insert(dcf, 'Non-Depreciable Capital Costs', 'Total', 'Value', self.non_depreciable, __name__, print_info = print_info)
		insert(dcf, 'Non-Depreciable Capital Costs', 'Inflated', 'Value', non_depreciable_inflated, __name__, print_info = print_info)
		
		insert(dcf, 'Total Capital Costs', 'Total', 'Value', total, __name__, print_info = print_info)
		insert(dcf, 'Total Capital Costs', 'Inflated', 'Value', total_inflated, __name__, print_info = print_info)

	def direct_capital_costs(self, dcf, print_info):
		'''Calculation of direct capital costs by applying ``sum_all_tables()`` to "Direct Capital Cost" group.'''

		self.direct, self.direct_contributions = sum_all_tables(dcf.inp, 'Direct Capital Cost', 'Value', insert_total = True, 
																class_object = dcf, print_info = print_info, 
																return_contributions = True)

	def indirect_capital_costs(self, dcf, print_info):
		'''Calculation of indirect capital costs by applying ``sum_all_tables()`` to "Indirect Capital Cost" group.'''

		self.indirect = sum_all_tables(dcf.inp, 'Indirect Capital Cost', 'Value', insert_total = True, 
									   class_object = dcf, print_info = print_info)

	def non_depreciable_capital_costs(self, dcf, print_info):
		'''Calculation of non-depreciable capital costs by calculating cost of land and applying
		``sum_all_tables()`` to "Other Non-Depreciable Capital Cost" group.
		'''

		process_table(dcf.inp, 'Non-Depreciable Capital Costs', 'Value')

		non_depreciable = dcf.inp['Non-Depreciable Capital Costs']
		self.non_depreciable = non_depreciable['Cost of land ($ per acre)']['Value'] * non_depreciable['Land required (acres)']['Value']
		self.non_depreciable += sum_all_tables(dcf.inp, 'Other Non-Depreciable Capital Cost', 'Value', insert_total = True, class_object = dcf, print_info = print_info)

