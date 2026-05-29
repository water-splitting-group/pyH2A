from pyH2A.Utilities.input_modification import sum_all_tables
from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
import pyH2A.Utilities.find_nearest as fn
import numpy as np

input_dict = {
	"Planned Replacement": {
		"<...>": {
			"Frequency_Value": {
				"type": {float,},
				"bounds": (0, None),
			},
			"Frequency_Unit": {
				"dimension": "time",
			},
			"Cost_Value": {
				"type": {float,},
				"bounds": (0, None),
				"path": "Cost_Path"
			},		
			"Cost_Unit": {
				"dimension": "currency",
			},
   			"optional": True,
			"description": "One-time replacement cost of <...>. Iteration over all entries in `Planned Replacement` table. Path key is 'Path'."
		},		
	},
	"<...> Unplanned Replacement <...>": {
		"<...>": {
			"Value": {
				"type": {float,},
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

output_dict = {
	"Replacement": {
		"Total": {
			"Value": {
				"inserted_value": "yearly_inflated",
				"type": {np.ndarray,},
				"dimension": "currency",
			},
			"optional": False,
			"description": "Total replacement costs for each year, including both planned and unplanned replacement costs, and corrected for inflation."
		},
	},
	"special_insertions":
        {"sum_all_tables": {
            "<...> Unplanned Replacement <...>": {
                "Summed Total": {
                    "Value": {
                        "type": {float},
                    },
                    "optional": False,
                    "description": "Summed total of unplanned replacement across all tables"
                },
            },
		}
	},
}	

class Replacement_Plugin:
	'''Calculating yearly overall replacement costs based on one-time replacement costs and frequency.

	Parameters
	----------
	Planned Replacement > [...] > Frequency : float
		Replacement frequency of [...]. 
		Iteration over all entries in `Planned Replacement` table. No path key
		available.
	Planned Replacement > [...] > Cost : float
		One-time replacement cost of [...].
		Iteration over all entries in `Planned Replacement` table. Path key
		is 'Path'.
	[...] Unplanned Replacement [...] >> Value : float
		``sum_all_tables()`` is used.

	Returns
	-------
	[...] Unplanned Replacement [...] > Summed Total > Value : float
		Summed total for each individual table in "Unplanned Replacement" group.
	Replacement > Total > Value : ndarray
		Total inflated replacement costs (sum of `Planned Replacement` entries and
		unplanned replacement costs).
	'''

	def __init__(self, dcf, print_info):
		self.input_dict_resolved = input_resolver_function(input_dict, dcf, 'Replacement_Plugin')
		
		self.initialize_yearly_costs(dcf)
		self.initialize_contributions()
		self.calculate_planned_replacement(dcf)
		self.unplanned_replacement()
		# contrary to the general rule of having self.* as Quantity objects, in the present plugin, only self.yearly_inflated, self.unplanned and self.contributions['Total'] are Quantity objects 
		# to avoid the unnecessary complication of having in each look "self.X = Quantity(self.X.unit[] + ...) ".
		self.contributions['Total'] = Quantity(np.sum(self.yearly), 'USD')
		
		self.yearly_inflated = Quantity(self.yearly * dcf.inflation_correction * dcf.inflation_factor, 'USD')
		output_inserter_function(output_dict, self, dcf, 'Replacement_Plugin') 
	
	def initialize_yearly_costs(self, dcf):
		'''Initializes ndarray filled with zeros with same length as dcf.inflation_factor.
		'''

		self.yearly = np.zeros(len(dcf.inflation_factor))

	def initialize_contributions(self):
		'''Initializes contributions to replacement costs.
		'''
		self.contributions = {}
		self.contributions['Data'] = {}
		self.contributions['Table Group'] = 'Replacement Costs'

	def calculate_planned_replacement(self, dcf):
		'''Calculation of yearly replacement costs by iterating over all entries of 
		`Planned Replacement`.
		'''

		for key in dcf.inp['Planned Replacement']:
			planned_replacement = Planned_Replacement(self.input_dict_resolved['Planned Replacement'][key], dcf)
			self.yearly[planned_replacement.years_idx] += planned_replacement.cost
			self.contributions['Data'][key] = planned_replacement.total_cost

	def unplanned_replacement(self):
		'''Calculating unplanned replacement costs by appling ``sum_all_tables()`` to 
		"Unplanned Replacement" group.
		'''

		self.unplanned = self.input_dict_resolved['Unplanned Replacement']['Summed group total']['Value'] # Calculated by sum_tables
		self.yearly += self.unplanned.unit['USD']
		self.contributions['Data']['Unplanned Replacement'] = np.sum(np.ones_like(self.yearly) * self.unplanned.unit['USD'])

class Planned_Replacement:
	'''
	Individual planned replacement objects.

	Methods
	-------
	calculate_yearly_cost:
		Calculation of yearly costs from one-time cost and replacement frequency.
	'''

	def __init__(self, dictionary, dcf):
		self.calculate_yearly_cost(dictionary, dcf)
		
	def calculate_yearly_cost(self, dictionary, dcf):
		'''Calculation of yearly replacement costs.

		Replacement costs are billed annually, replacements which are performed at a non-integer rate 
		are corrected using non_integer_correction.
		'''

		replacement_frequency = int(np.ceil(dictionary['Frequency_Value'].unit['year']))
		non_integer_correction = replacement_frequency / dictionary['Frequency_Value'].unit['year']

		raw_replacement_cost = dictionary['Cost_Value'].unit['USD'] 
		initial_replacement_year_idx = fn.find_nearest(dcf.plant_years, replacement_frequency)[0]

		self.cost = raw_replacement_cost * non_integer_correction * dcf.combined_inflator
		self.years = dcf.plant_years[initial_replacement_year_idx:][0::replacement_frequency]
		self.years_idx = fn.find_nearest(dcf.plant_years, self.years)

		self.total_cost = np.sum(np.ones_like(self.years) * self.cost)
