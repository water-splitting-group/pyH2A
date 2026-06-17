from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
import numpy as np
from pyH2A import functional_unit as fu

input_dict = {
    "Technical Operating Parameters and Specifications": {
		"Plant design capacity": { 
			"Value": {
				"type": {float, int}, 
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": fu.FD_dot,
			},
			"optional": True,
			"description": "Plant design capacity in functional units (e.g. mass of H2) / time."
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
			"description": "Operating capacity factor value between 0 and 1 or percentage value."
		},
		"Design output by year": { 
			"Value": {
				"type": {np.ndarray},
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": fu.FD,
			},
			"optional": True,
			"description": "Yearly production of functional units"
		},
		"Fraction of output that reaches gate": { 
			"Value": {
				"type": {float},
				"bounds": (0, 1),
			},
			"Unit": {
				"dimension": "dimensionless",
			},
			"optional": False,
			"description": "Ratio between the gate production and the raw production"
		},
	},
	"Time": {
		"Total years ones": { 
			"Value": {
				"type": {np.ndarray}, 
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": "dimensionless",
			},
			"optional": False,
			"description": "Array of ones, of length equal to the number of operation years."
		},
	}
}

output_dict = {
	"Technical Operating Parameters and Specifications": {
		"Design output by year": { 
			"Value": {
				"inserted_value": "design_output_by_year",
				"type": {np.ndarray,},
				"dimension": fu.FD,
			},
			"optional": False,
			"description": "Yearly output taking operating capacity factor into account."
		},
		"Sum of design output": { 
			"Value": {
				"inserted_value": "sum_design_output",
				"type": {float, int},
				"dimension": fu.FD,
			},
			"optional": False,
			"description": "Cumulated output during plant lifetime, taking operating capacity factor into account."
		},		
		"Output at gate by year": { 
			"Value": {
				"inserted_value": "output_per_year_at_gate",
				"type": {np.ndarray,},
				"dimension": fu.FD,
			},
			"optional": False,
			"description": "Actual yearly output at gate."
		},
		"Sum of output at gate": { 
			"Value": {
				"inserted_value": "sum_output_gate",
				"type": {float, int},
				"dimension": fu.FD,
			},
			"optional": False,
			"description": "Cumulated output at gate during plant lifetime."
		},			
	},
}

class Production_Plugin:
	'''Calculation of plant output and potential scaling.

	Parameters
	----------
	Technical Operating Parameters and Specifications > Plant design capacity > Value : float or nd.array
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
		self.input_dict_resolved = input_resolver_function(input_dict, dcf, 'Production_Plugin')
		self.dictionary = self.input_dict_resolved['Technical Operating Parameters and Specifications']

		self.calculate_output()

		output_inserter_function(output_dict, self, dcf, 'Production_Plugin')     



	def calculate_output(self):
		'''Calculation of yearly output and yearly output at gate.
		'''

		if 'Plant design capacity' in self.dictionary and 'Design output by year' not in self.dictionary:
			design_output_FU_by_year = (self.dictionary['Plant design capacity']['Value'].unit[fu.FU_per_year] 
								 			* self.input_dict_resolved['Time']['Total years ones']['Value'].unit['-'])

		elif 'Plant design capacity' not in self.dictionary and 'Design output by year' in self.dictionary:
			if len(self.input_dict_resolved['Time']['Total years ones']['Value'].unit['-']) == len(self.dictionary['Design output by year']['Value'].unit[fu.FU]):
				design_output_FU_by_year = self.dictionary['Design output by year']['Value'].unit[fu.FU]  
			else:
				raise ValueError(
					f"Production plugin: Design output by year, of length "
					f"{len(self.dictionary['Design output by year']['Value'].unit[fu.FU])} "
					f", differs from the number of operation years {len(self.input_dict_resolved['Time']['Operation years ones']['Value'].unit['-'])}."
				)

		else:
			raise ValueError (f"Production plugin: either the Plant design capacity, or the Design output by year, must be specified.")

		self.design_output_by_year = Quantity(design_output_FU_by_year, fu.FU)

		output_FU_per_year_at_gate = (design_output_FU_by_year 
										* self.dictionary['Operating capacity factor']['Value'].unit['-'] 
										* self.dictionary['Fraction of output that reaches gate']['Value'].unit['-'])
		
		self.output_per_year_at_gate = Quantity(output_FU_per_year_at_gate, fu.FU)

		self.sum_design_output = Quantity(np.sum(design_output_FU_by_year), fu.FU)
		self.sum_output_gate = Quantity(np.sum(output_FU_per_year_at_gate), fu.FU)