from pyH2A.Utilities.input_modification import sum_all_tables, read_textfile
from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
import pyH2A.Utilities.find_nearest as fn
import numpy as np

FD = "mass" # dimension of the functional unit
FU = "kg" # functional unit

input_dict = {	
	"Technical Operating Parameters and Specifications": {
		"Output per year": {
			"Value": {
				"type": {float},
				"bounds": (0, None)
			},
			"Unit": {
				"dimension": FD
			},
			"optional": False,
			"description": "Yearly output taking operating capacity factor into account, in amount of functional unit"
		}
	},
	"Utilities": {
		"<...>": {
			"Cost_Value": {
				"type": {float, str, np.ndarray},
				"bounds": (0, None)
			},
			"Cost_Unit": {
				"dimension": "currency" # we omit the basis on purpose, at it is transparent, and will simplify with the basis per kg; the raito is precisely what the conversion factor is there for
			},			
			"Usage_Value": {
				"type": {float},
				"bounds": (0, None)
			},
			"Usage_Unit": {
				"dimension": "dimensionless/"+FD # basis per unit of product
			},			
			"Price_Conversion_Factor_Value": {
				"type": {float},
				"bounds": (0, None)
			},
			"Price_Conversion_Factor_Unit": {
				"dimension": "dimensionless"
			},
			"Cost_Path": {
				"type": {str},
				"bounds": None, 
			},			
			"Usage_Path": {
				"type": {str},
				"bounds": None, 
			},
			"optional": True,
			"description": "Utilities are specified by specifying the cost of a given utility (e.g. USD of each kWh of electricity) and specifying the usage of the utility per mass of product (e.g. kWh of electricity consumption /kg (H2). The cost of the utility may be either a float, a ndarray with the same length as `dcf.inflation_correction` or a textfile containing cost values (cost values have to be in second column). For cost the path key is Cost_Path and for usage the path key is Usage_Path"
		}
	},
	"<...> Other Variable Operating Cost <...>": {
		"<...>": {
			"Value": {
				"type": {float},
				"bounds": (0, None)
			},
			"Unit": {
				"dimension": "currency"
			},
			"optional": True,
			"description": "Value for variable operating cost. `sum_all_tables()` is used for summing all tables in this group."
		}
	}
}

output_dict = {
    "Variable Operating Costs": {
		"Total": {
			"Value": {
				"inserted_value": "total_variable_costs",
				"type": {float, np.ndarray},
				"dimension": "currency",
			},
			"optional": False,
			"description": "Total variable operating costs, including utilities and other variable operating costs."
		},
		"Utilities": {
			"Value": {
				"inserted_value": "utilities",
				"type": {float, np.ndarray},
				"dimension": "currency",
			},
			"optional": False,
			"description": "Total variable operating costs for utilities, including inflation correction."
		},
		"Other": {
			"Value": {
				"inserted_value": "other",
				"type": {float},
				"dimension": "currency",
			},
			"optional": False,
			"description": "Total variable operating costs for other variable operating costs."
		},
	},
    "special_insertions":
        {"sum_all_tables": {
            "<...> Other Variable Operating Cost <...>": {
                "Summed Total": {
                    "Value": {
                        "type": {float},
                    },
                    "optional": False,
                    "description": "Summed total of other variable operating costs across all tables"
                },
            },
		},
	}
}

class Variable_Operating_Cost_Plugin:
	'''Calculation of variable operating costs.

	Parameters
	----------
	Technical Operating Parameters and Specifications > Output per year > Value : float
		Yearly output taking operating capacity factor into account, in amount of functional unit.
	Utilities > [...] > Cost : float, ndarray or str
		Cost of utility (e.g. $/kWh for electricity). May be either a float, a ndarray with the
		same length as `dcf.inflation_correction` or a textfile containing cost values (cost values 
		have to be in second column).
	Utilities > [...] > Usage : float
		Usage of utility per functional unit (e.g. kWh/(kg of H2) for electricity).
	Utilities > [...] > Price_Conversion_Factor : float
		Conversion factor between cost and usage units. Should be set to 1 if no conversion is
		required.
	Utilities > [...] > Cost_Path : str
		Path for `Cost` entry. If no such path is needed, the Cost_Path column must exist and be left empty.
	Utilities > [...] > Usage_Path : str
		Path for `Usage` entry. If no such path is needed, the Usage_Path column must exist and be left empty.
	[...] Other Variable Operating Operating Cost [...] >> Value : float
		``sum_all_tables()`` is used.

	Returns
	-------
	[...] Other Variable Operating Cost [...] > Summed Total > Value : float
		Summed total for each individual table in "Other Variable Operating Cost"
		group.
	Variable Operating Costs > Total > Value : ndarray
		Sum of inflation corrected utilities costs and other variable operating costs.
	Variable Operating Costs > Utilities > Value : ndarray
		Sum of inflation corrected utilities costs.
	Variable Operating Costs > Other > Value : float
		Sum of `Other Variable Operating Cost` entries.
	'''

	def __init__(self, dcf, print_info):

		self.input_dict_resolved = input_resolver_function(input_dict, dcf, 'Variable_Operating_Cost_Plugin')

		self.calculate_utilities_cost(dcf)
		self.other_variable_costs(dcf, print_info)
		self.total_variable_costs = Quantity(self.utilities.unit['USD'] + self.other.unit['USD'], 'USD')	

		output_inserter_function(output_dict, self, dcf, 'Variable_Operating_Cost_Plugin')   


	def calculate_utilities_cost(self, dcf):
		'''Iterating over all utilities and computing summed yearly costs.
		'''

		self.utilities = 0.

		for key in self.input_dict_resolved['Utilities']:
			utility = Utility(self.input_dict_resolved['Utilities'][key], dcf)
			self.utilities += utility.cost_per_functional_unit.unit['USD/'+FU]

		self.utilities = self.utilities * self.input_dict_resolved['Technical Operating Parameters and Specifications']['Output per year']['Value'].unit[FU]
		self.utilities = Quantity(self.utilities, 'USD')

	def other_variable_costs(self, dcf, print_info):
		'''Applying ``sum_all_tables()`` to "Other Variable Operating Cost" group.
		'''

		self.other = dcf.chemical_inflator * sum_all_tables(self.input_dict_resolved, 'Other Variable Operating Cost', 'Value', 
																insert_total = True, class_object = dcf, 
																print_info = print_info).unit['USD'] 
		self.other = Quantity(self.other, 'USD')

class Utility:
	'''Individual utility objects.

	Methods 
	-------
	calculate_cost_per_functional_unit:
		Calculation of utility cost per functional unit with inflation correction.
	'''

	def __init__(self, dictionary, dcf):
		self.calculate_cost_per_functional_unit(dictionary, dcf)

	def calculate_cost_per_functional_unit(self, dictionary, dcf):
		'''Calculation of utility cost per kg of H2 with inflation correction.
		'''
		
		if isinstance(dictionary['Cost_Value'], str):
			prices = read_textfile(dictionary['Cost_Value'], delimiter = '	')
			years_idx = fn.find_nearest(prices, dcf.years)
			prices = prices[years_idx]

			self.cost_per_functional_unit = Quantity(prices[:,1] * dcf.inflation_correction * dictionary['Price_Conversion_Factor_Value'].unit['-'] * dictionary['Usage_Value'].unit['-/'+FU], 'USD/'+FU) 

		else:
			annual_cost_per_functional_unit = dcf.inflation_correction * dictionary['Cost_Value'].unit['USD'] * dictionary['Usage_Value'].unit['-/'+FU] * dictionary['Price_Conversion_Factor_Value'].unit['-']
			self.cost_per_functional_unit = Quantity(np.ones(len(dcf.inflation_factor)) * annual_cost_per_functional_unit, 'USD/'+FU)
