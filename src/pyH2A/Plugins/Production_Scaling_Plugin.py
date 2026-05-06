from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity

# edit the following strings according to the system
FD = "energy" # Dimension of the functional unit. 
FU = "kWh" # functional unit.
FD_dot = 'power' # Dimension of the functional unit per time. 
FU_dot = 'W' # functional unit per time, SI by default. 
FU_per_year = 'kWh_per_year' # needed because we want to integrate FUs over periods of 1 year. 

input_dict = {
    "Technical Operating Parameters and Specifications": {
		"Plant design capacity": {
			"Value": {
				"type": {float,},
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": FD_dot,
			},
			"optional": False,
			"description": "Plant design capacity in functional units (e.g. mass of H2) / time."
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
		"Maximum output rate at gate": {
			"Value": {
				"type": {float,},
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": FD_dot,
			},
			"optional": True,
			"description": "Maximum output rate at gate. If not specified it defaults to `Plant Design Capacity`."
		},
		"New plant design capacity": {
			"Value": {
				"type": {float,},
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": FD_dot,
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
		"Design output rate": {
			"Value": {
				"inserted_value": "scaled_design_output",
				"type": {float,},
				"dimension": FD_dot,
			},
			"optional": False,
			"description": "Design output of hydrogen production plant per unit time."
		},
		"Max gate output rate": {
			"Value": {
				"inserted_value": "max_gate_output_rate",
				"type": {float,},
				"dimension": FD_dot,
    		},
			"optional": False,
			"description": "Maximum gate ouput per unit time."
		},
		"Output per year": {
			"Value": {
				"inserted_value": "output_per_year",
				"type": {float,},
				"dimension": FD,
			},
			"optional": False,
			"description": "Yearly output taking operating capacity factor into account."
		},
		"Output per year at gate": {
			"Value": {
				"inserted_value": "output_per_year_at_gate",
				"type": {float,},
				"dimension": FD,
			},
			"optional": False,
			"description": "Actual yearly output at gate."
		},
		"Maximum output rate at gate": {
			"Value": {
				"inserted_value": "maximum_output_at_gate",
				"type": {float,},
				"dimension": FD_dot,
			},
			"optional": False,
			"description": "Maximum output rate at gate. If not specified it defaults to `Plant Design Capacity`."
		},
		"Scaling ratio": {
			"Value": {
				"inserted_value": "scaling_ratio",
				"type": {float,},
				"dimension": "dimensionless",
			},
			"optional": True,
			"description": "Returned or overwritten if New Plant Design Capacity was specified."
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
			"description": "Returned if scaling is active (`Scaling Ratio` or `New Plant Design Capacity` specified)."
		},
		"Labor scaling factor": {
			"Value": {
				"inserted_value": "labor_scaling_factor",
				"type": {float,},
				"dimension": "dimensionless",
			},
			"optional": True,
			"description": "Returned if scaling is active (`Scaling Ratio` or `New Plant Design Capacity` specified)."
		},
	},
}

class Production_Scaling_Plugin:
	'''Calculation of plant output and potential scaling.

	Parameters
	----------
	Technical Operating Parameters and Specifications > Plant design capacity > Value : float
		Plant design capacity (mass per time).
	Technical Operating Parameters and Specifications > Operating capacity factor > Value : float
		Operating capacity factor.
	Technical Operating Parameters and Specifications > Maximum output rate at gate > Value : float, optional
		Maximum output rate at gate in (mass of H2)/time. 
		If this parameter is not specified it defaults to `Plant design capacity`.
	Technical Operating Parameters and Specifications > New plant design capacity > Value : float, optional
		New plant design capacity in mass of H2/time to calculate scaling, which overwrites possible Scaling ratio.
	Technical Operating Parameters and Specifications > Scaling ratio > Value : float, optional
		Scaling ratio which is multiplied by current plant design capacity to obtain scaled plant size.
	Technical Operating Parameters and Specifications > Capital scaling exponent > Value : float, optional
		Exponent to calculate capital scaling factor. Defaults to 0.78.
	Technical Operating Parameters and Specifications > Labor scaling exponent > Value : float, optional
		Exponent to calculcate labor scaling factor. Defaults to 0.25.

	Returns
	-------
	Technical Operating Parameters and Specifications > Design output rate > Value : float
		Design output.
	Technical Operating Parameters and Specifications > Max gate output rate > Value : float
		Maximum gate ouput.
	Technical Operating Parameters and Specifications > Yearly averaged output flowrate > Value : float
		Yearly output taking operating capacity factor into account.
	Technical Operating Parameters and Specifications > Yearly averaged output flowrate at gate > Value	: float
		Actual yearly output at gate.
	Technical Operating Parameters and Specifications > Maximum output rate at gate > Value	: float
		Specified or equal to to `Plant design capacity`.				
	Technical Operating Parameters and Specifications > Scaling ratio > Value : float or None
		Returned if New plant design capacity was specified.
	Scaling > Capital scaling factor > Value : float or None
		Returned if scaling is active (`Scaling Ratio` or `New plant design capacity` specified).
	Scaling > Labor scaling factor > Value : float or None
		Returned if scaling is active (`Scaling ratio` or `New plant design capacity` specified).

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
		`Scaling Ratio` was provided). Otherwise returns regular design output and output at gate per time in FUncitonal units.
		'''

		if 'Maximum output rate at gate' in self.dictionary:
			self.maximum_output_at_gate = self.dictionary['Maximum output rate at gate']['Value']
		else:
			self.maximum_output_at_gate = self.dictionary['Plant design capacity']['Value']

		if ('Scaling ratio' in self.dictionary):
			self.scaling_ratio = self.dictionary['Scaling ratio']['Value']

		if 'New plant design capacity' in self.dictionary: # possibility to overwrite the existing scaling ratio
			self.scaling_ratio = Quantity(self.dictionary['New plant design capacity']['Value'].unit[FU_dot] / self.dictionary['Plant design capacity']['Value'].unit[FU_dot], '-')

		if ('Scaling ratio' in self.dictionary) or ('New plant design capacity' in self.dictionary):
			self.scaled_design_output = Quantity(self.dictionary['Plant design capacity']['Value'].unit[FU_dot] * self.scaling_ratio.unit['-'], FU_dot)
			self.max_gate_output_rate = Quantity(self.maximum_output_at_gate.unit[FU_dot] * self.scaling_ratio.unit['-'], FU_dot)

			if 'Capital scaling exponent' in self.dictionary:
				self.capital_scaling_factor = Quantity(self.scaling_ratio.unit['-'] ** self.dictionary['Capital scaling exponent']['Value'].unit['-'], '-')
			else:
				self.capital_scaling_factor = Quantity(self.scaling_ratio.unit['-'] ** 0.78, '-')

			if 'Labor scaling exponent' in self.dictionary:
				self.labor_scaling_factor = Quantity(self.scaling_ratio.unit['-'] ** self.dictionary['Labor scaling exponent']['Value'].unit['-'], '-')
			else:
				self.labor_scaling_factor = Quantity(self.scaling_ratio.unit['-'] ** 0.25, '-')

		else:
			self.scaled_design_output = self.dictionary['Plant design capacity']['Value']
			self.max_gate_output_rate = self.maximum_output_at_gate

	def calculate_output(self):
		'''Calculation of yearly output in kg and yearly output at gate in kg.
		'''

		self.output_per_year = Quantity(self.scaled_design_output.unit[FU_per_year] * self.dictionary['Operating capacity factor']['Value'].unit['-'], FU)
		self.output_per_year_at_gate = Quantity(self.max_gate_output_rate.unit[FU_per_year] * self.dictionary['Operating capacity factor']['Value'].unit['-'], FU)
		