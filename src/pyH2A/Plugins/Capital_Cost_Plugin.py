from pyH2A.Utilities.input_modification import sum_all_tables
from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
import numpy as np

input_dict = {
	"Inflation":{
		"Combined inflator": {
			"Value": {
				"type": {float,},
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": "dimensionless",
			},	
			"optional": False,
			"description": "Combined inflator."
		},
		"CI inflator": {
			"Value": {
				"type": {float,},
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": "dimensionless",
			},	
			"optional": False,
			"description": "CI inflator."
		},		
	},
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
	}
}

output_dict = {
	"Direct Capital Costs": {
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
                "Summed total": {
                    "Value": {
                        "type": {float},
                    },
                    "optional": False,
                    "description": "Summed total of direct capital costs across all tables"
                },
            },
            "<...> Indirect Capital Cost <...>": {
                "Summed total": {
                    "Value": {
                        "type": {float},
                    },
                    "optional": False,
                    "description": "Summed total of indirect capital costs across all tables"
                },
            },
            "<...> Other Non-Depreciable Capital Cost <...>": {
                "Summed total": {
                    "Value": {
                        "type": {float},
                    },
                    "optional": False,
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
	<...> Direct Capital Cost <...> >> Value : float
		``sum_all_tables()`` is used.
	<...> Indirect Capital Cost <...> >> Value : float
		``sum_all_tables()`` is used.
	Non-Depreciable Capital Costs > Cost of land > Value : float
		Cost of land.
	Non-Depreciable Capital Costs > Land required > Value : float
		Total land area required.
	<...> Other Non-Depreciable Capital Cost <...> >> Value : float
		``sum_all_tables()`` is used.

	Returns
	-------
	<...> Direct Capital Cost <...> > Summed total > Value : float
		Summed total for each individual table in "Direct Capital Cost" group.
	<...> Indirect Capital Cost <...> > Summed total > Value : float
		Summed total for each individual table in "Indirect Capital Cost" group.
	<...> Other Non-Depreciable Capital Cost  <...> > Summed total > Value : float
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
		self.input_dict_resolved = input_resolver_function(input_dict, dcf, 'Capital_Cost_Plugin')
		
		# Except for self.direct and self.indirect, which are natively Quantities as they are the results of sum_all_tables calls, 
		# all the self.X variable are converted into Quantites just before their insertion, to avoid unnecessary complications
		self.direct = self.input_dict_resolved['Direct Capital Cost']['Summed group total']['Value'] # Calculated during the call of sum_tables
		direct_inflated = self.direct.unit['USD'] * self.input_dict_resolved['Inflation']['Combined inflator']['Value'].unit['-']
		self.indirect = self.input_dict_resolved['Indirect Capital Cost']['Summed group total']['Value'] # Calculated during the call of sum_tables
		indirect_inflated = self.indirect.unit['USD'] * self.input_dict_resolved['Inflation']['Combined inflator']['Value'].unit['-']

		depreciable = self.direct.unit['USD'] + self.indirect.unit['USD']
		depreciable_inflated = direct_inflated + indirect_inflated
		
		non_depreciable = self.non_depreciable_capital_costs(dcf, print_info)

		non_depreciable_inflated = non_depreciable * self.input_dict_resolved['Inflation']['CI inflator']['Value'].unit['-']
		total = depreciable + non_depreciable
		total_inflated = depreciable_inflated + non_depreciable_inflated

		# convert the values into Quantities
		self.direct_inflated = Quantity(direct_inflated, 'USD')
		self.indirect_inflated = Quantity(indirect_inflated, 'USD')
		self.depreciable = Quantity(depreciable, 'USD')
		self.depreciable_inflated = Quantity(depreciable_inflated, 'USD')
		self.non_depreciable = Quantity(non_depreciable, 'USD')
		self.non_depreciable_inflated = Quantity(non_depreciable_inflated, 'USD')        
		self.total = Quantity(total, 'USD')
		self.total_inflated = Quantity(total_inflated, 'USD')     

		output_inserter_function(output_dict, self, dcf, 'Capital_Cost_Plugin')


	def non_depreciable_capital_costs(self, dcf, print_info):
		'''Calculation of non-depreciable capital costs by calculating cost of land and applying
		``sum_all_tables()`` to "Other Non-Depreciable Capital Cost" group.
		'''

		non_depreciable = self.input_dict_resolved['Non-Depreciable Capital Costs']
		non_depreciable = non_depreciable['Cost of land']['Value'].unit['USD/m2'] * non_depreciable['Land required']['Value'].unit['m2']
		non_depreciable += self.input_dict_resolved['Other Non-Depreciable Capital Cost']['Summed group total']['Value'].unit['USD']

		return non_depreciable
