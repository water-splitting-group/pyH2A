from pyH2A.Utilities.input_modification import read_textfile
from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
import pyH2A.Utilities.find_nearest as fn
import numpy as np
from pyH2A.Utilities.docstring_generation import generate_docstring

class Variable_Operating_Cost_Plugin:

	def __init__(self, dcf, print_info, run = True):
		self._set_up(dcf)
		if run:
			self._run(dcf)

	def _set_up(self, dcf):

		self.functional_unit = dcf.functional_unit

		self.input_dict = {
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
			"Inflation": {
				"Inflation correction": {
					"Value": {
						"type": {int, float},
						"bounds": (0, None)
					},
					"Unit": {
						"dimension": "dimensionless"
					},
					"optional": False,
					"description": "Inflation correction accounting for startup year offset"
				}, 
				"Chemical inflator": {
					"Value": {
						"type": {int, float},
						"bounds": (0, None)
					},
					"Unit": {
						"dimension": "dimensionless"
					},
					"optional": False,
					"description": "Inflation factor for chemicals"
				},
				"Inflation factor full": {
					"Value": {
						"type": {np.ndarray},
						"bounds": (0, None)
					},
					"Unit": {
						"dimension": "dimensionless"
					},
					"optional": False,
					"description": "Inflation factor of each year"
				},
			},
			"Financial Input Values": {
				"Start-up time": {
					"Value": {
						"type": {int, float},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "time",
					},
					"optional": False,
					"description": "Start-up time in years."
				},
				"Fraction of variable operating costs during start-up": {
					"Value": {
						"type": {int, float},
						"bounds": (0, 1),
					},
					"Unit": {
						"dimension": "dimensionless",
					},
					"optional": False,
					"description": "Fraction of variable operating costs incurred during start-up."
				},
			},
			"Technical Operating Parameters and Specifications": {
				"Design output by year": {
					"Value": {
						"type": {np.ndarray},
						"bounds": (0, None)
					},
					"Unit": {
						"dimension": self.functional_unit.dimension,
					},
					"optional": False,
					"description": "Yearly production of product, ignoring the capacity factor"
				},
				"Operating capacity factor": { 
					"Value": {
						"type": {float, int},
						"bounds": (0, 1),
					},
					"Unit": {
						"dimension": "dimensionless",
					},
					"optional": False,
					"description": "Operating capacity factor value between 0 and 1."
				},	
			},
			"Utilities": {
				"<...>": {
					"Cost_Value": {
						"type": {int, float, str, np.ndarray},
						"bounds": (0, None),
						"path": "Cost_Path"
					},
					"Cost_Unit": {
						"dimension": "currency" # we omit the basis on purpose, at it is transparent, and will simplify with the basis per functional unit; the ratio is precisely what the conversion factor is there for
					},			
					"Usage_Value": {
						"type": {int, float},
						"bounds": (0, None), 
						"path": "Usage_Path"
					},
					"Usage_Unit": {
						"dimension": f"1/{self.functional_unit.dimension}" # basis per functional unit of product
					},			
					"Price_Conversion_Factor_Value": {
						"type": {int, float},
						"bounds": (0, None)
					},
					"Price_Conversion_Factor_Unit": {
						"dimension": "dimensionless"
					},		
					"optional": True,
					"description": "Utilities are specified by specifying the cost of "
								   "a given utility (e.g. USD of each kWh of electricity) and"
								   " specifying the usage of the utility per functional dimension of product"
								   " (e.g. kWh of electricity consumption /kg (H2). "
								   "The cost of the utility may be either a float, "
								   "a ndarray with the same length as `dcf.inflation_correction` "
								   "or a textfile containing cost values "
								   "(cost values have to be in second column). "
								   "For cost the path key is Cost_Path and for usage the path key is Usage_Path"
				}
			},
			"<...> Other Variable Operating Cost <...>": {
				"<...>": {
					"Value": {
						"type": {int, float, np.ndarray},
						"bounds": (0, None)
					},
					"Unit": {
						"dimension": "currency"
					},
					"optional": True,
					"description": "Value for variable operating cost. `sum_all_tables()` is used for summing all tables in this group."
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

		self.output_dict = {
		    "Variable Operating Costs": {
				"Total": {
					"Value": {
						"inserted_value": "total_variable_costs",
						"type": {np.ndarray},
						"dimension": "currency",
					},
					"optional": False,
					"description": "Total variable operating costs, including utilities and other variable operating costs."
				},
				"Utilities": {
					"Value": {
						"inserted_value": "utilities",
						"type": {np.ndarray},
						"dimension": "currency",
					},
					"optional": False,
					"description": "Total variable operating costs for utilities, including inflation correction."
				},
				"Other": {
					"Value": {
						"inserted_value": "other",
						"type": {int, float, np.ndarray},
						"dimension": "currency",
					},
					"optional": False,
					"description": "Total variable operating costs for other variable operating costs."
				},
				"Annual": {
					"Value": {
						"inserted_value": "annual_variable_operating_cost",
						"type": {np.ndarray},
						"dimension": "currency",
					},
					"optional": False,
					"description": "Total variable operating cost for each year of the analysis, expanded to "
								   "the full analysis period (non-zero only from the start of operation "
								   "onward), corrected for inflation, reduced by the applicable fraction "
								   "during the start-up years, and set to zero before the start of operation "
								   "(i.e. during construction). Used by the discounted cash flow analysis."
				},
			},
		    "special_insertions":
		        {"sum_all_tables": {
		            "<...> Other Variable Operating Cost <...>": {
		                "Summed total": {
		                    "Value": {
		                        "type": {int, float},
								"dimension": "currency"
		                    },
		                    "description": "Summed total of other variable operating costs in each table"
		                },
		            },
		            "Other Variable Operating Cost": {
						"Summed total": {
							"Value": {
								'type': {int, float},
								"dimension": "currency"
							},
							"description": "Summed total of other variable operating costs in this table."
						},
		                "Summed group total": {
		                    "Value": {
		                        "type": {int, float},
								"dimension": "currency"
		                    },
		                    "description": "Summed total of other variable operating costs across all tables"
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
			}
		}

	def _run(self, dcf):
		self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, 'Variable_Operating_Cost_Plugin')

		self.calculate_utilities_cost()
		self.other_variable_costs()

		self.total_variable_costs = Quantity(self.utilities.unit['USD'] + self.other.unit['USD'], 'USD')

		self.annual_variable_operating_cost = self.calculate_annual_variable_operating_cost()

		output_inserter_function(self.output_dict, self, dcf, 'Variable_Operating_Cost_Plugin')

	def calculate_utilities_cost(self):
		'''Iterating over all utilities and computing summed yearly costs.
		'''

		self.utilities = 0.

		for key in self.input_dict_resolved['Utilities']:
			utility = Utility(self.input_dict_resolved['Utilities'][key], self.input_dict_resolved, self.functional_unit)
			self.utilities += utility.cost_per_unit_of_product.unit[f'USD/{self.functional_unit.unit}']

		self.utilities = (self.utilities 
						  * self.input_dict_resolved['Technical Operating Parameters and Specifications']['Design output by year']['Value'].unit[f'{self.functional_unit.unit}']
						  * self.input_dict_resolved['Technical Operating Parameters and Specifications']['Operating capacity factor']['Value'].unit['-'])
		self.utilities = Quantity(self.utilities, 'USD')

	def other_variable_costs(self):
		'''
		Applying inflation correct to summed other variable operating costs
		'''
		self.other = Quantity(
						self.input_dict_resolved['Inflation']['Chemical inflator']['Value'].unit['-']
						* self.input_dict_resolved['Other Variable Operating Cost']['Summed group total']['Value'].unit['USD'],
					 'USD')

	def calculate_annual_variable_operating_cost(self):
		'''Calculation of total variable operating cost for each year of the analysis, required by
		the discounted cash flow analysis. `Variable Operating Costs > Total` (covering only the
		operation years) is expanded to the full analysis period, corrected for inflation, and
		reduced by the applicable fraction during the start-up years.
		'''

		# Reading time and inflation information from input dictionary
		time_dict = self.input_dict_resolved['Time']['Years']['Value']
		analysis_years_ones = time_dict['Analysis years ones']
		start_idx = int(round(time_dict['Start index'].unit['-']))

		inflation_factor_full = self.input_dict_resolved['Inflation']['Inflation factor full']['Value']
		start_up_time = self.input_dict_resolved['Financial Input Values']['Start-up time']['Value']
		fraction_during_start_up = self.input_dict_resolved['Financial Input Values']['Fraction of variable operating costs during start-up']['Value']

		# Expanding total variable operating costs to the full analysis period 
		expanded_total = np.zeros_like(analysis_years_ones.unit['-'])
		expanded_total[start_idx:] = self.total_variable_costs.unit['USD']

		annual_variable_operating_cost = expanded_total * inflation_factor_full.unit['-']

		start_up_time_idx = start_idx + int(round(start_up_time.unit['year']))

		annual_variable_operating_cost[:start_up_time_idx] = (annual_variable_operating_cost[:start_up_time_idx]
															  * fraction_during_start_up.unit['-'])
		annual_variable_operating_cost[:start_idx] = 0

		return Quantity(annual_variable_operating_cost, 'USD')

class Utility:
	'''Individual utility objects.

	Methods 
	-------
	calculate_cost_per_unit_of_product:
		Calculation of utility cost per functional unit of product with inflation correction.
	'''

	def __init__(self, dictionary, full_dict, functional_unit):
		self.calculate_cost_per_unit_of_product(dictionary, full_dict, functional_unit)

	def calculate_cost_per_unit_of_product(self, dictionary, full_dict, functional_unit):
		'''Calculation of utility cost per unit of product with inflation correction.
		'''
		
		if isinstance(dictionary['Cost_Value'], str):
			prices = read_textfile(dictionary['Cost_Value'], delimiter = '	')
			years_idx = fn.find_nearest(prices, full_dict['Time']['Years']['Value']['Operation years'].unit['-'])
			prices = prices[years_idx]

			self.cost_per_unit_of_product = Quantity(prices[:,1] 
													 * full_dict['Inflation']['Inflation correction']['Value'].unit['-']
													 * dictionary['Price_Conversion_Factor_Value'].unit['-'] 
													 * dictionary['Usage_Value'].unit[f'1/{functional_unit.unit}'], 
											 f'USD/{functional_unit.unit}') 

		elif isinstance(dictionary['Cost_Value'], Quantity):

			annual_cost_per_unit_of_product = (dictionary['Cost_Value'].unit['USD'] 
											   * full_dict['Inflation']['Inflation correction']['Value'].unit['-']
											   * dictionary['Price_Conversion_Factor_Value'].unit['-']
											   * dictionary['Usage_Value'].unit[f'1/{functional_unit.unit}'])
			
			self.cost_per_unit_of_product = Quantity(full_dict['Time']['Years']['Value']['Operation years ones'].unit['-'] 
													 * annual_cost_per_unit_of_product, 
											f'USD/{functional_unit.unit}')

		else:
			raise ValueError(f"Unsupported type for Cost_Value ({dictionary['Cost_Value']}): {type(dictionary['Cost_Value'])}. Must be either str or Quantity.")