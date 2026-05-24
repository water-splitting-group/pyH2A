from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity

input_dict = {
	"Technical Operating Parameters and Specifications": {
		"Design output flowrate": {
			"Value": {
				"type": {float,},
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": "mass / time",	
			},
			"optional": False,
			"description": "Design output of hydrogen production plant per unit of time."
		},
	},	
	"Solar-to-Hydrogen Efficiency": {
		"STH": {
			"Value": {
				"type": {float,},
				"bounds": (0, 1),	
			},
			"Unit": {
				"dimension": "dimensionless",	
			},
			"optional": False,
			"description": "Solar-to-Hydrogen Efficiency of thermal water splitting process. Percentage or value between 0 and 1."
		},
	},
	"Solar Input": {
		"Mean solar input": {	
			"Value": {
				"type": {float,},
				"bounds": (0, None),	
			},
			"Unit": {
				"dimension": "power / area",	
			},
			"optional": False,
			"description": "Mean solar input."
		},
	},
	"Non-Depreciable Capital Costs": {
		"Additional land area": {
			"Value": {
				"type": {float,},
				"bounds": (0, None),	
			},
			"Unit": {
				"dimension": "dimensionless",	
			},
			"optional": False,
			"description": "Additional land area required. Percentage or value > 0. Calculated as: (1 + Addtional Land Area) * solar collection area."
		},
	},
}

output_dict = {
	"Non-Depreciable Capital Costs": {
		"Land required": {
			"Value": {
				"inserted_value": "area",
				"type": {float,}, 
				"dimension": "area",
			},
			"description": "Total land requirement.",
			"optional": False,	
		},
	},
}

class Solar_Thermal_Plugin:
	'''Simulation of hydrogen production using solar thermal water splitting.

	Parameters
	----------
	Technical Operating Parameters and Specifications > Design output flowrate > Value : float
		Design output of hydrogen production plant per day.
	Solar-to-Hydrogen Efficiency > STH > Value : float
		Solar-to-Hydrogen Efficiency of thermal water splitting process. Percentage of value 
		between 0 and 1.
	Solar Input > Mean solar input > Value : float
		Mean solar input.
	Non-Depreciable Capital Costs > Additional land area > Value : float
		Additional land area required. Percentage or value > 0. Calculated as:
		(1 + Addtional Land Area) * solar collection area.

	Returns
	-------
	Non-Depreciable Capital Costs > Land required > Value : float
		Total land requirement in acres.
	'''
	
	def __init__(self, dcf, print_info):
		self.input_dict_resolved = input_resolver_function(input_dict, dcf, 'Solar_Thermal_Plugin')

		self.calculate_land_area()
		
		output_inserter_function(output_dict, self, dcf, 'Solar_Thermal_Plugin')  		

	def calculate_land_area(self):
		'''Calculation of required land area based on solar input, solar-to-hydrogen efficiency
		and addtional land are requirements.
		'''
		
		self.H2_molecule_energy = Quantity(2*1.229, 'eV/entity')
		self.H2_molecular_weight = Quantity(2, 'g/mol')
		
		H2_mol_per_m2_per_s = ((self.input_dict_resolved['Solar Input']['Mean solar input']['Value'].unit['W/m2'] 
						  * self.input_dict_resolved['Solar-to-Hydrogen Efficiency']['STH']['Value'].unit['-']) 
						 / self.H2_molecule_energy.unit['J/mol'])
		H2_kg_per_m2_per_s = H2_mol_per_m2_per_s * self.H2_molecular_weight.unit['kg/mol']

		required_area_m2 = (self.input_dict_resolved['Technical Operating Parameters and Specifications']['Design output flowrate']['Value'].unit['kg/s'] 
							/ H2_kg_per_m2_per_s)

		self.area = Quantity(required_area_m2 
							 * (1. + self.input_dict_resolved['Non-Depreciable Capital Costs']['Additional land area']['Value'].unit['-']), 
					'm2')
