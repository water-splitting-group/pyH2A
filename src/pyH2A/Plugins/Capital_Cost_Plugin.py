from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
import numpy as np

input_dict = {
	"Time": {
		"Years": {
			"Value": {
				"type": {dict,},
				"bounds": (None, None),
			},
			"Unit": {
				"dimension": "dimensionless",
			},
			"optional": False,
			"description": "Dictionary containing all time-related quantities."
		},
	},
	"Construction": {
		"<...>": {
			"Value": {
				"type": {int, float},
				"bounds": (0, 1),
			},
			"Unit": {
				"dimension": "dimensionless",
			},
			"optional": False,
			"description": "Fraction of capital spent during each construction year."
		},
	},
	"Financial Input Values": {
		"Fraction equity financing": {
			"Value": {
				"type": {int, float},
				"bounds": (0, 1),
			},
			"Unit": {
				"dimension": "dimensionless",
			},
			"optional": False,
			"description": "Fraction of depreciable capital costs financed through equity (as opposed to debt)."
		},
	},
	"Inflation":{
		"Combined inflator": {
			"Value": {
				"type": {int, float,},
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
				"type": {int, float,},
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": "dimensionless",
			},	
			"optional": False,
			"description": "CI inflator."
		},
		"Inflation correction": {
			"Value": {
				"type": {int, float,},
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": "dimensionless",
			},
			"optional": False,
			"description": "Inflation correction accounting for startup year offset."
		},
		"Inflation factor full": {
			"Value": {
				"type": {np.ndarray,},
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": "dimensionless",
			},
			"optional": False,
			"description": "Inflation factor of each year."
		},
	},
	"<...> Direct Capital Cost <...>": {
		"<...>": {
			"Value": {
				"type": {int, float,},
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": "currency",
			},	
			"optional": True,
			"description": "Individual entry of direct capital cost."
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
				"type": {int, float,},
				"bounds": (0, None),
			},	
			"Unit": {
				"dimension": "currency",
			},		
			"optional": True,
			"description": "Individual entry of indirect capital cost."
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
				"type": {int, float,},
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
				"type": {int, float,},
				"bounds": (0, None),
			},	
			"Unit": {
				"dimension": "area",
			},		
			"optional": False,
			"description": "Total land area are required."
		},
	},
	"<...> Other Non-Depreciable Capital Cost <...>": {
		"<...>": {
			"Value": {
				"type": {int, float,},
				"bounds": (0, None),
			},	
			"Unit": {
				"dimension": "currency",
			},		
			"optional": True,
			"description": "Individual entry of other non-depreciable capital cost."
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
				"type": {int, float,},
				"dimension": "currency",
			},
			"description": "Total direct capital costs multiplied by combined inflator.",
		},
	},
	"Indirect Capital Costs": {
		"Inflated": {
			"Value": {
				"inserted_value": "indirect_inflated",
				"type": {int,float,},
				"dimension": "currency",
			},
			"description": "Total indirect capital costs multiplied by combined inflator.",
		},
	},
	"Non-Depreciable Capital Costs": {
		"Total": {
			"Value": {	
				"inserted_value": "non_depreciable",
				"type": {int, float,},
				"dimension": "currency",		
			},
			"description": "Total non-depreciable capital costs.",
		},
		"Inflated": {
			"Value": {
				"inserted_value": "non_depreciable_inflated",
				"type": {int, float,},
				"dimension": "currency",
			},
			"description": "Total non-depreciable capital costs multiplied by combined inflator.",
		},
		"Inflation corrected": {
			"Value": {
				"inserted_value": "non_depreciable_capital_dcf_inflation_corrected",
				"type": {int, float,},
				"dimension": "currency",
			},
			"description": "Non-depreciable capital costs, inflated and further corrected for the startup "
						   "year offset. Used by the discounted cash flow analysis for "
						   "salvage/decommissioning calculations.",
		},
		"Annual": {
			"Value": {
				"inserted_value": "annual_non_depreciable_capital",
				"type": {np.ndarray,},
				"dimension": "currency",
			},
			"description": "Non-depreciable capital costs spent in each year of the analysis, "
						   "non-zero only in the first year of construction.",
		},
	},
	"Depreciable Capital Costs": {
		"Total": {
			"Value": {
				"inserted_value": "depreciable",
				"type": {int, float,},
				"dimension": "currency",
			},
			"description": "Total depreciable capital costs (direct + indirect capital costs).",
		},
		"Inflated": {
			"Value": {
				"inserted_value": "depreciable_inflated",
				"type": {int, float,},
				"dimension": "currency",
			},
			"description": "Total depreciable capital costs (direct + indirect capital costs) multiplied by combined inflator.",
		},
		"Inflation corrected": {
			"Value": {
				"inserted_value": "depreciable_capital_dcf_inflation_corrected",
				"type": {int, float,},
				"dimension": "currency",
			},
			"description": "Depreciable capital costs, inflated and further corrected for the startup year "
						   "offset. Used by the discounted cash flow analysis for debt financing and "
						   "salvage/decommissioning calculations.",
		},
		"Initial equity": {
			"Value": {
				"inserted_value": "initial_equity_depreciable_capital",
				"type": {int, float,},
				"dimension": "currency",
			},
			"description": "Total equity-financed depreciable capital spent during construction, "
						   "summed over all construction years.",
		},
		"Annual equity": {
			"Value": {
				"inserted_value": "annual_initial_equity_depreciable_capital",
				"type": {np.ndarray,},
				"dimension": "currency",
			},
			"description": "Equity-financed depreciable capital spent in each year of the analysis, "
						   "non-zero only during the construction years.",
		},
	},
	"Total Capital Costs": {
		"Total": {
			"Value": {
				"inserted_value": "total",
				"type": {int, float,},
				"dimension": "currency",
			},	
			"description": "Total capital costs (depreciable + non-depreciable capital costs).",
		},
		"Inflated": {
			"Value": {
				"inserted_value": "total_inflated",
				"type": {int, float,},
				"dimension": "currency",
			},
			"description": "Total capital costs (depreciable + non-depreciable capital costs) multiplied by combined inflator.",
		},
	},
	"special_insertions":
        {"sum_all_tables": {
            "<...> Direct Capital Cost <...>": {
                "Summed total": {
                    "Value": {
                        "type": {int, float},
						"dimension": "currency"
                    },
                    "description": "Summed total of direct capital costs for each table"
                },
            },
            "<...> Indirect Capital Cost <...>": {
                "Summed total": {
                    "Value": {
                        "type": {int, float},
						"dimension": "currency"
                    },
                    "description": "Summed total of indirect capital costs for each table"
                },
            },
            "<...> Other Non-Depreciable Capital Cost <...>": {
                "Summed total": {
                    "Value": {
                        "type": {int, float},
						"dimension": "currency"
                    },
                    "description": "Summed total of other non-depreciable capital costs for each table"
                },
            },
            "Direct Capital Cost": {
				"Summed total": {
					"Value": {
						"type": {int, float},
						"dimension": "currency"
					},
					"description": "Summed total of this table."
				},
                "Summed group total": {
                    "Value": {
                        "type": {int, float},
						"dimension": "currency"
                    },
                    "description": "Summed total of direct capital costs across all tables"
                },
				'Contributions': {
                    'Value': {
                        'type': {dict},
                        'dimension': 'currency',
                    },
                    'description': 'Contributions to the sum'
                },
            },
            "Indirect Capital Cost": {
				"Summed total": {
					"Value": {
						"type": {int, float},
						"dimension": "currency"
					},
					"optional": False,
					"description": "Summed total of this table."
				},
                "Summed group total": {
                    "Value": {
                        "type": {int, float},
						"dimension": "currency"
                    },
                    "optional": False,
                    "description": "Summed total of indirect capital costs across all tables"
                },
				'Contributions': {
                    'Value': {
                        'type': {dict},
                        'dimension': 'currency',
                    },
                    'description': 'Contributions to the sum'
                },
            },
            "Other Non-Depreciable Capital Cost": {
				"Summed total": {
					"Value": {
						"type": {int, float},
						"dimension": "currency"
					},
					"optional": False,
					"description": "Summed total of this table."
				},
                "Summed group total": {
                    "Value": {
                        "type": {int, float},
                        "dimension": "currency"
                    },
                    "description": "Summed total of other non-depreciable capital costs across all tables"
                },
				'Contributions': {
                    'Value': {
                        'type': {dict},
                        'dimension': 'currency',
                    },
                    'description': 'Contributions to the sum'
                },
            },			
        },
    },
}

class Capital_Cost_Plugin:
	'''

	Parameters
	----------
	Time > Years > Value : dict
		Dictionary containing all time-related quantities.
	Inflation > Combined inflator > Value: float
		Combined inflator.
	Inflation > CI inflator > Value: float
		CI inflator.
	Inflation > Inflation correction > Value : float
		Inflation correction accounting for startup year offset.
	Inflation > Inflation factor full > Value : ndarray
		Inflation factor of each year.
	Construction > [...] > Value : float
		Fraction of capital spent during each construction year.
		Iteration over all entries in `Construction` table.
	Financial Input Values > Fraction equity financing > Value : float
		Fraction of depreciable capital costs financed through equity (as opposed to debt).
	<...> Direct Capital Cost <...> >> Value : float
		``sum_all_tables()`` is used in the input resolver.
	<...> Indirect Capital Cost <...> >> Value : float
		``sum_all_tables()`` is used in the input resolver.
	Non-Depreciable Capital Costs > Cost of land > Value : float
		Cost of land.
	Non-Depreciable Capital Costs > Land required > Value : float
		Total land area required.
	<...> Other Non-Depreciable Capital Cost <...> >> Value : float
		``sum_all_tables()`` is used in the input resolver.

	Returns
	-------
	<...> Direct Capital Cost <...> > Summed total > Value : float
		Summed total for each individual table in "Direct Capital Cost" group.
	<...> Indirect Capital Cost <...> > Summed total > Value : float
		Summed total for each individual table in "Indirect Capital Cost" group.
	<...> Other Non-Depreciable Capital Cost  <...> > Summed total > Value : float
		Summed total for each individual table in "Other Non-Depreciable Capital Cost" group.
	Direct Capital Cost > Summed group total > Value : float
		Summed total for all the tables in "Direct Capital Cost" group.
	Indirect Capital Cost > Summed group total > Value : float
		Summed total for all the tables in "Indirect Capital Cost" group.
	Other Non-Depreciable Capital Cost > Summed group total > Value : float
		Summed total for all the tables in "Other Non-Depreciable Capital Cost" group.
	Direct Capital Costs > Inflated > Value : float
		Total direct capital costs multiplied by combined inflator.
	Indirect Capital Costs > Inflated > Value : float
		Total indirect capital costs multiplied by combined inflator.
	Non-Depreciable Capital Costs > Total > Value : float
		Total non-depreciable capital costs.
	Non-Depreciable Capital Costs > Inflated > Value : float
		Total non-depreciable capital costs multiplied by combined inflator.
	Non-Depreciable Capital Costs > Inflation corrected > Value : float
		Non-depreciable capital costs, inflated and further corrected for the startup year offset.
		Used by the discounted cash flow analysis for salvage/decommissioning calculations.
	Non-Depreciable Capital Costs > Annual > Value : ndarray
		Non-depreciable capital costs spent in each year of the analysis, non-zero only in the
		first year of construction. Used by the discounted cash flow analysis.
	Depreciable Capital Costs > Total > Value : float
		Sum of direct and indirect capital costs.
	Depreciable Capital Costs > Inflated > Value : float
		Sum of direct and indirect capital costs multiplied by combined inflator.
	Depreciable Capital Costs > Inflation corrected > Value : float
		Depreciable capital costs, inflated and further corrected for the startup year offset.
		Used by the discounted cash flow analysis for debt financing and salvage/decommissioning
		calculations.
	Depreciable Capital Costs > Initial equity > Value : float
		Total equity-financed depreciable capital spent during construction, summed over all
		construction years. Used by the discounted cash flow analysis.
	Depreciable Capital Costs > Annual equity > Value : ndarray
		Equity-financed depreciable capital spent in each year of the analysis, non-zero only
		during the construction years. Used by the discounted cash flow analysis.
	Total Capital Costs > Total > Value : float
		Sum of depreciable and non-depreciable capital costs.
	Total Capital Costs > Inflated > Value : float
		Sum of depreicable and non-depreciable capital costs multiplied by combined inflator.
	'''
	def __init__(self, dcf, print_info):
		self.input_dict_resolved = input_resolver_function(input_dict, dcf, 'Capital_Cost_Plugin')
		
		direct_capital_costs = self.input_dict_resolved['Direct Capital Cost']['Summed group total']['Value'] # Calculated during the call of sum_tables
		indirect_capital_costs = self.input_dict_resolved['Indirect Capital Cost']['Summed group total']['Value'] # Calculated during the call of sum_tables
		
		self.direct_inflated = Quantity(direct_capital_costs.unit['USD'] 
								  		* self.input_dict_resolved['Inflation']['Combined inflator']['Value'].unit['-'], 
								'USD')
		self.indirect_inflated = Quantity(indirect_capital_costs.unit['USD'] 
										  * self.input_dict_resolved['Inflation']['Combined inflator']['Value'].unit['-'], 
								'USD')

		self.depreciable = Quantity(direct_capital_costs.unit['USD'] 
							        + indirect_capital_costs.unit['USD'], 
							'USD')
		self.depreciable_inflated = Quantity(self.depreciable.unit['USD'] 
										  * self.input_dict_resolved['Inflation']['Combined inflator']['Value'].unit['-'], 
								    'USD')

		self.non_depreciable = self.non_depreciable_capital_costs()
		self.non_depreciable_inflated = Quantity(self.non_depreciable.unit['USD'] 
										         * self.input_dict_resolved['Inflation']['CI inflator']['Value'].unit['-'], 
								         'USD')
		
		self.total = Quantity(self.depreciable.unit['USD'] 
							  + self.non_depreciable.unit['USD'],
					 'USD')
		self.total_inflated = Quantity(self.depreciable_inflated.unit['USD']
									 + self.non_depreciable_inflated.unit['USD'],
							  'USD')

		self.calculate_depreciable_capital_dcf_inputs()
		self.calculate_non_depreciable_capital_dcf_inputs()

		output_inserter_function(output_dict, self, dcf, 'Capital_Cost_Plugin')

	def non_depreciable_capital_costs(self):
		'''Calculation of non-depreciable capital costs by calculating cost of land and
			obtaining the total of the "Other Non-Depreciable Capital Cost" group.
		'''

		non_depreciable_costs = (self.input_dict_resolved['Non-Depreciable Capital Costs']['Cost of land']['Value'].unit['USD/m2']
						   		 * self.input_dict_resolved['Non-Depreciable Capital Costs']['Land required']['Value'].unit['m2'])

		non_depreciable_costs += self.input_dict_resolved['Other Non-Depreciable Capital Cost']['Summed group total']['Value'].unit['USD']

		return Quantity(non_depreciable_costs, 'USD')

	def calculate_depreciable_capital_dcf_inputs(self):
		'''Calculation of depreciable capital cost quantities required by the discounted cash flow
		analysis: depreciable capital cost inflated and corrected for the startup year offset,
		equity-financed depreciable capital spent during each construction year, and the total
		equity-financed depreciable capital spent during construction.
		'''

		self.analysis_years_ones = self.input_dict_resolved['Time']['Years']['Value']['Analysis years ones']
		self.inflation_factor_full = self.input_dict_resolved['Inflation']['Inflation factor full']['Value']
		self.inflation_correction = self.input_dict_resolved['Inflation']['Inflation correction']['Value']
		fraction_equity_financing = self.input_dict_resolved['Financial Input Values']['Fraction equity financing']['Value']

		self.depreciable_capital_dcf_inflation_corrected = Quantity(self.depreciable_inflated.unit['USD']
														            * self.inflation_correction.unit['-'],
														   'USD')

		construction_years = []
		for counter, key in enumerate(self.input_dict_resolved['Construction']):
			cost = (self.input_dict_resolved['Construction'][key]['Value'].unit['-']
	   				* fraction_equity_financing.unit['-']
					* self.depreciable_capital_dcf_inflation_corrected.unit['USD']
					* self.inflation_factor_full.unit['-'][counter])
			construction_years.append(cost)

		self.initial_equity_depreciable_capital = Quantity(np.sum(construction_years), 'USD')

		annual_initial_equity_depreciable_capital = np.zeros_like(self.analysis_years_ones.unit['-'])
		annual_initial_equity_depreciable_capital[:len(construction_years)] = construction_years
		self.annual_initial_equity_depreciable_capital = Quantity(annual_initial_equity_depreciable_capital, 'USD')

	def calculate_non_depreciable_capital_dcf_inputs(self):
		'''Calculation of non-depreciable capital cost quantities required by the discounted cash
		flow analysis: non-depreciable capital cost inflated and corrected for the startup year
		offset, and non-depreciable capital cost spent in each year of the analysis (non-zero only
		in the first year of construction).
		'''

		self.non_depreciable_capital_dcf_inflation_corrected = Quantity(self.non_depreciable_inflated.unit['USD']
																		* self.inflation_correction.unit['-'],
															   'USD')

		non_depreciable_capital_initial = (self.non_depreciable_capital_dcf_inflation_corrected.unit['USD']
											* self.inflation_factor_full.unit['-'][0])

		annual_non_depreciable_capital = np.zeros_like(self.analysis_years_ones.unit['-'])
		annual_non_depreciable_capital[0] = non_depreciable_capital_initial
		self.annual_non_depreciable_capital = Quantity(annual_non_depreciable_capital, 'USD')
