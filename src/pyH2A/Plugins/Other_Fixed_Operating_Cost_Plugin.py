from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
import numpy as np
from pyH2A.Utilities.docstring_generation import generate_docstring

class Other_Fixed_Operating_Cost_Plugin:

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
				"Combined inflator": {
					"Value": {
						"type": {int, float,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "dimensionless",
					},
		   			"optional": False,
					"description": "Combined inflation factor"
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
					"description": "Inflation correction accounting for startup year offset"
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
				"Fraction of fixed operating costs during start-up": {
					"Value": {
						"type": {int, float},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "dimensionless",
					},
					"optional": False,
					"description": "Fraction of fixed operating costs incurred during start-up."
				},
			},
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

		self.output_dict = {
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
				"Annual": {
					"Value": {
						"inserted_value": "annual_fixed_operating_cost",
						"type": {np.ndarray,},
						"dimension": "currency",
					},
					"optional": False,
					"description": "Total fixed operating cost for each year of the analysis, corrected for "
								   "inflation, reduced by the applicable fraction during the start-up years, "
								   "and set to zero before the start of operation (i.e. during construction). "
								   "Used by the discounted cash flow analysis."
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
  
		summary = "Calculation of yearly fixed operating costs."

		self.__class__.__doc__ = generate_docstring(
            summary,
            self.input_dict,
            self.output_dict
        )

	def _run(self, dcf):
		self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, 'Other_Fixed_Operating_Cost_Plugin')

		self.total_fixed_operating_cost = self.calculate_total_fixed_operating_cost()
		self.annual_fixed_operating_cost = self.calculate_annual_fixed_operating_cost()

		output_inserter_function(self.output_dict, self, dcf, 'Other_Fixed_Operating_Cost_Plugin')

	def calculate_total_fixed_operating_cost(self):
		'''Calculation of total fixed operating cost by summing total labor cost and total other fixed operating cost.'''

		labor = self.input_dict_resolved['Fixed Operating Costs']['Labor cost - inflated']['Value']
		other = self.input_dict_resolved['Other Fixed Operating Cost']['Summed group total']['Value']

		other_inflated = Quantity(other.unit['USD']
								  * self.input_dict_resolved['Inflation']['Combined inflator']['Value'].unit['-'],
						 'USD')

		total = Quantity(labor.unit['USD'] + other_inflated.unit['USD'], 'USD')

		return total

	def calculate_annual_fixed_operating_cost(self):
		'''Calculation of total fixed operating cost for each year of the analysis, required by the
		discounted cash flow analysis. The (constant, per-operating-year) total fixed operating cost
		is expanded to the full analysis period (non-zero only from the start of operation onward),
		corrected for inflation, and reduced by the applicable fraction during the start-up years.
		'''

		time_dict = self.input_dict_resolved['Time']['Years']['Value']
		analysis_years_ones = time_dict['Analysis years ones']
		start_idx = int(round(time_dict['Start index'].unit['-']))

		inflation_correction = self.input_dict_resolved['Inflation']['Inflation correction']['Value']
		inflation_factor_full = self.input_dict_resolved['Inflation']['Inflation factor full']['Value']
		start_up_time = self.input_dict_resolved['Financial Input Values']['Start-up time']['Value']
		fraction_during_start_up = self.input_dict_resolved['Financial Input Values']['Fraction of fixed operating costs during start-up']['Value']

		annual_fixed_operating_cost = np.zeros_like(analysis_years_ones.unit['-'])
		annual_fixed_operating_cost[start_idx:] = self.total_fixed_operating_cost.unit['USD']
		annual_fixed_operating_cost = annual_fixed_operating_cost * inflation_correction.unit['-']

		start_up_time_idx = start_idx + int(round(start_up_time.unit['year']))

		annual_fixed_operating_cost = annual_fixed_operating_cost * inflation_factor_full.unit['-']
		annual_fixed_operating_cost[:start_up_time_idx] = (annual_fixed_operating_cost[:start_up_time_idx]
															* fraction_during_start_up.unit['-'])
		annual_fixed_operating_cost[:start_idx] = 0

		return Quantity(annual_fixed_operating_cost, 'USD')