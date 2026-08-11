from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity

class Solar_Thermal_Plugin:

	def __init__(self, dcf, print_info, run = True):
		self._set_up(dcf)
		if run:
			self._run(dcf)

	def _set_up(self, dcf):

		self.functional_unit = dcf.functional_unit

		self.input_dict = {
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
					"description": "Plant design capacity (mass of hydrogen/time)."
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

		self.output_dict = {
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

	def _run(self, dcf):
		self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, 'Solar_Thermal_Plugin')

		self.calculate_land_area()
		
		output_inserter_function(self.output_dict, self, dcf, 'Solar_Thermal_Plugin')  		

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

		required_area_m2 = (self.input_dict_resolved['Technical Operating Parameters and Specifications']['Plant design capacity']['Value'].unit['kg/s'] 
							/ H2_kg_per_m2_per_s)

		self.area = Quantity(required_area_m2 
							 * (1. + self.input_dict_resolved['Non-Depreciable Capital Costs']['Additional land area']['Value'].unit['-']), 
					'm2')
