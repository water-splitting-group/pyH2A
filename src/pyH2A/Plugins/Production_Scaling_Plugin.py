from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity

input_dict = {
    "Technical Operating Parameters and Specifications": {
		"Plant design capacity": {
			"Value": {
				"type": {float,},
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": "mass / time",
			},
			"optional": False,
			"description": "Plant design capacity in mass(product) / time."
		},
		"Operating capacity factor": {
			"Value": {
				"type": {float,},
				"bounds": (0, 1),
			},
			"Unit": {
				"dimension": "dimensionless",
			},
			"optional": False,
			"description": "Operating capacity factor value between 0 and 1 or percentage value."
		},
		"Maximum output at gate": {
			"Value": {
				"type": {float,},
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": "mass / time",
			},
			"optional": True,
			"description": "Maximum output at gate. If not specified it defaults to `Plant Design Capacity`."
		},
		"New plant design capacity": {
			"Value": {
				"type": {float,},
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": "mass / time",
			},
			"optional": True,
			"description": "New plant design capacity in mass(product) / time to calculate scaling, which overwrites possible Scaling Ratio."
		},
		"Scaling ratio": {
			"Value": {
				"type": {float,},
				"bounds": (0, None), 
			},
			"Unit": {
				"dimension": "dimensionless",
			},
			"optional": True,
			"description": "Scaling ratio which is multiplied by current plant design capacity to obtain scaled plant size. Overwritten by `New Plant Design Capacity` if that is specified."
		},
		"Capital scaling exponent": {
			"Value": {
				"type": {float,},
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": "dimensionless",
			},
			"optional": True,
			"description": 	"Exponent to calculate capital scaling factor. Defaults to 0.78 if not specified."
		},
		"Labor scaling exponent": {
			"Value": {
				"type": {float,},
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": "dimensionless",
			},
			"optional": True,
			"description": 	"Exponent to calculcate labor scaling factor. Defaults to 0.25 if not specified."
		},
	},	
}

output_dict = {
	"Technical Operating Parameters and Specifications": {
		"Design output per day": {
			"Value": {
				"inserted_value": "design_output_per_day",
				"type": {float,},
				"dimension": "mass / time",
			},
			"optional": False,
			"description": "Design output of hydrogen production plant per day."
		},
		"Max gate output per day": {
			"Value": {
				"inserted_value": "max_gate_output_per_day",
				"type": {float,},
				"dimension": "mass / time",
    		},
			"optional": False,
			"description": "Maximum gate ouput per day."
		},
		"Output per year": {
			"Value": {
				"inserted_value": "output_per_year",
				"type": {float,},
				"dimension": "mass / time",
			},
			"optional": False,
			"description": "Yearly output taking operating capacity factor into account."
		},
		"Output per year at gate": {
			"Value": {
				"inserted_value": "output_per_year_at_gate",
				"type": {float,},
				"dimension": "mass / time",
			},
			"optional": False,
			"description": "Actual yearly output at gate."
		},
		"Maximum output at gate": {
			"Value": {
				"inserted_value": "maximum_output_at_gate",
				"type": {float,},
				"dimension": "mass / time",
			},
			"optional": True,
			"description": "Maximum output at gate. If not specified it defaults to `Plant Design Capacity`."
		},
		"Scaling ratio": {
			"Value": {
				"inserted_value": "scaling_ratio",
				"type": {float,},
				"dimension": "dimensionless",
			},
			"optional": True,
			"description": "Returned if New Plant Design Capacity was specified."
		},
	},
	"Scaling": {
		"Capital scaling factor": {
			"Value": {
				"inserted_value": "capital_scaling_factor",
				"type": {float,},
				"dimension": "dimensionless",
			},
			"optional": True,
			"description": "Returned if scaling is active (`Scaling Ratio` or `New Plant Design Capacity (kg of H2/day)` specified)."
		},
		"Labor scaling factor": {
			"Value": {
				"inserted_value": "labor_scaling_factor",
				"type": {float,},
				"dimension": "dimensionless",
			},
			"optional": True,
			"description": "Returned if scaling is active (`Scaling Ratio` or `New Plant Design Capacity (kg of H2/day)` specified)."
		},
	},
}

class Production_Scaling_Plugin:
	'''Calculation of plant output and potential scaling.

	Parameters
	----------
	Technical Operating Parameters and Specifications > Plant Design Capacity (kg of H2/day) > Value : float
		Plant design capacity in kg of H2/day, ``process_table()`` is used.
	Technical Operating Parameters and Specifications > Operating Capacity Factor (%) > Value : float
		Operating capacity factor in %, ``process_table()`` is used.
	Technical Operating Parameters and Specifications > Maximum Output at Gate > Value : float, optional
		Maximum output at gate in (kg of H2)/day, ``process_table()`` is used. If this parameter is
		not specified it defaults to `Plant Design Capacity (kg of H2/day)`.
	Technical Operating Parameters and Specifications > New Plant Design Capacity (kg of H2/day) > Value : float, optional
		New plant design capacity in kg of H2/day to calculate scaling, which overwrites possible Scaling Ratio,
		``process_table()`` is used.
	Technical Operating Parameters and Specifications > Scaling Ratio > Value : float, optional
		Scaling ratio which is multiplied by current plant design capacity to obtain scaled plant size,
		``process_table`` is used.
	Technical Operating Parameters and Specifications > Capital Scaling Exponent > Value : float, optional
		Exponent to calculate capital scaling factor, ``process_table()`` is used. Defaults to 0.78.
	Technical Operating Parameters and Specifications > Labor Scaling Exponent > Value : float, optional
		Exponent to calculcate labor scaling factor, ``process_table()`` is used. Defaults to 0.25.

	Returns
	-------
	Technical Operating Parameters and Specifications > Design Output per Day > Value : float
		Design output in (kg of H2)/day.
	Technical Operating Parameters and Specifications > Max Gate Output per Day > Value : float
		Maximum gate ouput in (kg of H2)/day.
	Technical Operating Parameters and Specifications > Output per Year > Value : float
		Yearly output taking operating capacity factor into account, in (kg of H2)/year.
	Technical Operating Parameters and Specifications > Output per Year at Gate > Value	: float
		Actual yearly output at gate, in (kg of H2)/year.
	Technical Operating Parameters and Specifications > Scaling Ratio > Value : float or None
		Returned if New Plant Design Capacity was specified.
	Scaling > Capital Scaling Factor > Value : float or None
		Returned if scaling is active (`Scaling Ratio` or `New Plant Design Capacity (kg of H2/day)` specified).
	Scaling > Labor Scaling Factor > Value : float or None
		Returned if scaling is active (`Scaling Ratio` or `New Plant Design Capacity (kg of H2/day)` specified).

	Notes
	-----
	To scale capital or labor costs, a path to `Scaling > Capital Scaling Factor > Value`
	or `Scaling > Labor Scaling Factor > Value` has to specified for the respective table entry.
	'''

	def __init__(self, dcf, print_info):
		self.input_dict_resolved = input_resolver_function(input_dict, dcf, 'Production_Scaling_Plugin')
		self.dictionary = self.input_dict_resolved['Technical Operating Parameters and Specifications']

		self.calculate_scaling()
		self.calculate_output()

		output_inserter_function(output_dict, self, dcf, 'Production_Scaling_Plugin')     

	def calculate_scaling(self):
		'''Calculation of scaling if scaling is requested (either `New Plant Design Capacity` or
		`Scaling Ratio` was provided). Otherwise returns regular design output and output at gate per day in (kg H2).
		'''

		if 'Maximum Output at Gate' in self.dictionary:
			self.maximum_output_at_gate = self.dictionary['Maximum Output at Gate']['Value']
		else:
			self.maximum_output_at_gate = self.dictionary['Plant Design Capacity']['Value']

		if ('Scaling Ratio' in self.dictionary):
			self.scaling_ratio = self.dictionary['Scaling Ratio']['Value']

		if 'New Plant Design Capacity' in self.dictionary: # possibility to overwrite the existing scaling ratio
			self.scaling_ratio = Quantity(self.dictionary['New plant design capacity']['Value'].unit['kg/day'] / self.dictionary['Plant design capacity']['Value'].unit['kg/day'], '-')

		if ('Scaling Ratio' in self.dictionary) or ('New plant design capacity' in self.dictionary):
			self.design_output_per_day = Quantity(self.dictionary['Plant design capacity']['Value'].unit['kg/day'] * self.scaling_ratio.unit['-'], 'kg/day')
			self.max_gate_output_per_day = Quantity(self.maximum_output_at_gate.unit['kg/day'] * self.scaling_ratio.unit['-'], 'kg/day')

			if 'Capital Scaling Exponent' in self.dictionary:
				self.capital_scaling_factor = Quantity(self.scaling_ratio.unit['-'] ** self.dictionary['Capital scaling exponent']['Value'].unit['-'], '-')
			else:
				self.capital_scaling_factor = Quantity(self.scaling_ratio.unit['-'] ** 0.78, '-')

			if 'Labor Scaling Exponent' in self.dictionary:
				self.labor_scaling_factor = Quantity(self.scaling_ratio.unit['-'] ** self.dictionary['Labor Scaling exponent']['Value'].unit['-'], '-')
			else:
				self.labor_scaling_factor = Quantity(self.scaling_ratio.unit['-'] ** 0.25, '-')

		else:
			self.design_output_per_day = self.dictionary['Plant Design Capacity']['Value']
			self.max_gate_output_per_day = self.maximum_output_at_gate

	def calculate_output(self):
		'''Calculation of yearly output in kg and yearly output at gate in kg.
		'''

		self.output_per_year = Quantity(self.design_output_per_day.unit['kg/year'] * self.dictionary['Operating capacity factor']['Value'].unit['-'], 'kg/year')
		self.output_per_year_at_gate = Quantity(self.max_gate_output_per_day.unit['kg/year'] * self.dictionary['Operating capacity factor']['Value'].unit['-'], 'kg/year')
		