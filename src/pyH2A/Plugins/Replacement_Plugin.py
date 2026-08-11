from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
import pyH2A.Utilities.find_nearest as fn
import numpy as np

class Replacement_Plugin:

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
						"type": {float,},
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
				"Combined inflator": {
					"Value": {
						"type": {float,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "dimensionless",
					},
		   			"optional": False,
					"description": "Combined inflation factor"
				},	 
			},
			"Planned Replacement": {
				"<...>": {
					"Frequency_Value": {
						"type": {int, float,},
						"bounds": (0, None),
						"path": "Frequency_Path"
					},
					"Frequency_Unit": {
						"dimension": "time",
					},
					"Cost_Value": {
						"type": {int, float,},
						"bounds": (0, None),
						"path": "Cost_Path"
					},		
					"Cost_Unit": {
						"dimension": "currency",
					},
		   			"optional": True,
					"description": "Replacement frequency and one-time replacement cost of <...>. ."
				},		
			},
			"<...> Unplanned Replacement <...>": {
				"<...>": {
					"Value": {
						"type": {int, float,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "currency",
					},
					"optional": True,
					"description": "Unplanned replacement costs. Can be provided for multiple entries under Unplanned Replacement, in which case they will be summed up to the total unplanned replacement costs."
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
			"Replacement": {
				"Total": {
					"Value": {
						"inserted_value": "yearly_inflated",
						"type": {np.ndarray,},
						"dimension": "currency",
					},
					"optional": False,
					"description": "Total replacement costs for each year, "
								   "including both planned and unplanned replacement costs, "
								   "and corrected for inflation. Set to zero for the years before "
								   "the start of operation (i.e. during construction)."
				},
				"Contributions": {
					"Value": {
						"inserted_value": "contributions",
						"type": {dict,},
						"dimension": "currency",
					},
					"optional": False,
					"description": "Contributions of each entry in `Planned Replacement` and the summed total of `Unplanned Replacement`"
								   " to the total replacement costs."
				},
			},
			"special_insertions":
		        {"sum_all_tables": {
		            "<...> Unplanned Replacement <...>": {
		                "Summed total": {
		                    "Value": {
		                        "type": {float},
								"dimension": "currency"
		                    },
		                    "optional": False,
		                    "description": "Summed total of unplanned replacement in each table"
		                },		
		            },
		            "Unplanned Replacement": {
						"Summed total" : {
							"Value": {
								"type": {float},
								"dimension": "currency"
							},
							"optional": False,
							"description": "Summed total of unplanned replacement costs for this table"
						},
		                "Summed group total": {
		                    "Value": {
		                        "type": {float},
								"dimension": "currency"
		                    },
		                    "optional": False,
		                    "description": "Summed total of unplanned replacement across all tables"
		                },
						"Contributions": {
							"Value": {
								"type": {dict,},
								"dimension": "currency",
							},
							"description": "Contributions of each table to the summed total of unplanned replacement costs."
						},
		            },
				},
			},
		}	

	def _run(self, dcf):
		self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, 'Replacement_Plugin')
		
		# Initialize self.yearly as an array of zeros with the same length as the number of plant years to store yearly replacement costs.
		self.yearly = np.zeros_like(self.input_dict_resolved['Time']['Years']['Value']['Plant years relative'].unit['-'])

		# Initialize contributions
		self.contributions = {}
		self.contributions['Data'] = {}
		self.contributions['Table Group'] = 'Replacement Costs'

		self.calculate_planned_replacement()
		self.calculate_unplanned_replacement()
		self.calculate_total()

		output_inserter_function(self.output_dict, self, dcf, 'Replacement_Plugin') 
	
	def calculate_planned_replacement(self):
		'''Calculation of yearly replacement costs by iterating over all entries of 
		`Planned Replacement`.
		'''

		for key in self.input_dict_resolved['Planned Replacement']:
			planned_replacement = Planned_Replacement(self.input_dict_resolved['Planned Replacement'][key], 
													  self.input_dict_resolved['Time']['Years']['Value']['Plant years relative'].unit['-'], 
													  self.input_dict_resolved['Inflation']['Combined inflator']['Value'].unit['-'])
			
			self.yearly[planned_replacement.years_idx] += planned_replacement.cost.unit['USD']
			self.contributions['Data'][key] = planned_replacement.total_cost

	def calculate_unplanned_replacement(self):
		'''Calculating unplanned replacement costs 
		'''

		self.unplanned = self.input_dict_resolved['Unplanned Replacement']['Summed group total']['Value'] # Calculated by sum_tables
		self.yearly += self.unplanned.unit['USD']
		self.contributions['Data']['Unplanned Replacement'] = Quantity(np.sum(np.ones_like(self.yearly) 
																	   * self.unplanned.unit['USD']), 
															  'USD')
	
	def calculate_total(self):
		'''Calculating total replacement costs. Replacement costs occurring before the start of
		operation (i.e. during construction) are set to zero, as no replacements are performed
		while the plant is not yet operational.
		'''

		self.contributions['Total'] = Quantity(np.sum(self.yearly), 'USD')
		yearly_inflated = (self.yearly
						   * self.input_dict_resolved['Inflation']['Inflation correction']['Value'].unit['-']
						   * self.input_dict_resolved['Inflation']['Inflation factor full']['Value'].unit['-'])

		start_idx = int(round(self.input_dict_resolved['Time']['Years']['Value']['Start index'].unit['-']))
		yearly_inflated[:start_idx] = 0

		self.yearly_inflated = Quantity(yearly_inflated, 'USD')

class Planned_Replacement:
	'''
	Individual planned replacement objects.

	Methods
	-------
	calculate_yearly_cost:
		Calculation of yearly costs from one-time cost and replacement frequency.
	'''

	def __init__(self, dictionary, plant_years_relative, combined_inflator):
		self.calculate_yearly_cost(dictionary, plant_years_relative, combined_inflator)
		
	def calculate_yearly_cost(self, dictionary, plant_years_relative, combined_inflator):
		'''Calculation of yearly replacement costs.

		Replacement costs are billed annually, replacements which are performed at a non-integer rate 
		are corrected using non_integer_correction.
		'''

		replacement_frequency = int(np.ceil(dictionary['Frequency_Value'].unit['year']))
		non_integer_correction = replacement_frequency / dictionary['Frequency_Value'].unit['year']
 
		initial_replacement_year_idx = fn.find_nearest(plant_years_relative, replacement_frequency)[0]

		self.cost = Quantity(dictionary['Cost_Value'].unit['USD'] 
					   		 * non_integer_correction 
							 * combined_inflator, 
					'USD')

		self.years = plant_years_relative[initial_replacement_year_idx:][0::replacement_frequency]
		self.years_idx = fn.find_nearest(plant_years_relative, self.years)

		self.total_cost = Quantity(np.sum(np.ones_like(self.years) 
								    * self.cost.unit['USD']), 
						  'USD')