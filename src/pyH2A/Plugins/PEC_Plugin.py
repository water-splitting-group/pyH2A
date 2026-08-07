import numpy as np
from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.docstring_generation import generate_docstring

class PEC_Plugin:

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
						"type": {float,int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "mass / time",
					},
					"optional": False,
					"description": "Plant design capacity, in mass of hydrogen/time."
				},
			},
			"PEC Cells": {
				"Cell cost": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "currency / area",
					},
					"optional": False,
					"description": "Cost of PEC cells per cell area."
				},
				"Lifetime": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "time",
					},
					"optional": False,
					"description": "Lifetime of PEC cells before replacement is required."
				},
				"Length": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "length",
					},
					"optional": False,
					"description": "Length of single PEC cell."
				},
				"Width": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "length",
					},
					"optional": False,
					"description": "Width of single PEC cell."
				}
			},
			"Land Area Requirement": {
				"Cell angle": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, np.pi / 2), 
					},
					"Unit": {
						"dimension": "angle",
					},
					"optional": False,
					"description": "Angle of PEC cells from the ground."
				},
				"South spacing": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "length",
					},
					"optional": False,
					"description": "South spacing of PEC cells."
				},
				"East/West spacing": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "length",
					},
					"optional": False,
					"description": "East/West Spacing of PEC cells."
				}
			},
			"Solar-to-Hydrogen Efficiency": {
				"STH": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, 1),
					},
					"Unit": {
						"dimension": "dimensionless", 
					},
					"optional": False,
					"description": "Solar-to-hydrogen efficiency in percentage or as a value between 0 and 1."
				}
			},
			"Solar Input": {
				"Mean solar input": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "power / area",
					},
					"optional": False,
					"description": "Mean solar input in power / area, yearly average of solar input."
				}
			}
		}

		self.output_dict = {
			"Non-Depreciable Capital Costs": {
				"Land required": {
					"Value": {
						"inserted_value": "total_land_area", 
						"type": {float,int,}, 
						"dimension":"area",
		        	},
					"description": "Total land area required.",
					"optional": False,
				},
				"Solar collection area": {
					"Value": {
						"inserted_value": "total_solar_collection_area",
						"type": {float,int,},
						"dimension":"area",
					},
					"description": "Solar collection area.",
					"optional": False,
				}
			},
			"Planned Replacement": {
				"Planned replacement PEC cells": {
					"Cost_Value": {
						"inserted_value": "cell_cost",
						"type": {float,int,},
						"dimension":"currency",
					},
					"Frequency_Value": {
						"inserted_value": "cell_lifetime",
						"type": {float,int,}, 
						"dimension":"time",
					},
					"description": "Total cost of replacing all PEC cells once.",
					"optional": False,		
				}
			},
		 	"Direct Capital Costs - PEC Cells": {
				"PEC cell cost": {
					"Value": {
						"inserted_value": "cell_cost",
						"type": {float,int,}, 
						"dimension": "currency"
					},
					"description": "Total cost of all PEC cells.",
					"optional": False,
				}
			},
			"PEC Cells": {
				"Number": {
					"Value": {
						"inserted_value": "cell_number",
						"type": {float,int}, 
						"dimension":"dimensionless",
					},
					"description": "Number of individual PEC cells required for design H2 output capacity.",
					"optional": False,
				}
			},
		}
  
		summary = "Simulating H2 production using photoelectrochemical water splitting."

		self.__class__.__doc__ = generate_docstring(
            summary,
            self.input_dict,
            self.output_dict
        )

	def _run(self, dcf):
		self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, 'PEC_Plugin')
		
		self.hydrogen_production()
		self.PEC_cost()
		self.land_area()

		self.cell_lifetime = self.input_dict_resolved['PEC Cells']['Lifetime']['Value']

		output_inserter_function(self.output_dict, self, dcf, 'PEC_Plugin') 

	def hydrogen_production(self):
		'''Calculation of (kg of H2)/day produced by single PEC cell.
		'''

		pec = self.input_dict_resolved['PEC Cells']

		self.cell_area = Quantity(pec['Length']['Value'].unit['m'] 
								  * pec['Width']['Value'].unit['m'], 
						'm2')
		cell_insolation = (self.cell_area.unit['m2'] 
						   * self.input_dict_resolved['Solar Input']['Mean solar input']['Value'].unit['W/m2'])
		
		self.H2_molecule_energy = Quantity(2 * 1.229, 'eV/entity')
		self.H2_molecular_weight = Quantity(2, 'g/mol')
		
		mol_H2_per_cell_per_second = (cell_insolation 
									  * self.input_dict_resolved['Solar-to-Hydrogen Efficiency']['STH']['Value'].unit['-']
									  / self.H2_molecule_energy.unit['J/mol'])
		
		self.mass_rate_H2_per_cell = Quantity(mol_H2_per_cell_per_second 
											  * self.H2_molecular_weight.unit['kg/mol'], 
									 'kg/s')
		self.mol_rate_H2_per_surface = Quantity(mol_H2_per_cell_per_second 
												/ self.cell_area.unit['m2'], 
									   'mol/s/m2')

	def PEC_cost(self):
		'''Calculation of cost per cell, number of required cells and total cell cost.
		'''

		cost_per_cell = (self.cell_area.unit['m2'] 
						 * self.input_dict_resolved['PEC Cells']['Cell cost']['Value'].unit['USD/m2'])

		self.cell_number = Quantity(np.ceil(
			   							self.input_dict_resolved['Technical Operating Parameters and Specifications']['Plant design capacity']['Value'].unit['kg/day'] 
										/ self.mass_rate_H2_per_cell.unit['kg/day']
										), 
							'-')
		
		self.cell_cost = Quantity(self.cell_number.unit['-'] 
								  * cost_per_cell, 
						'USD')

	def land_area(self):
		'''Calculation of total required land area and solar collection area.
		'''

		self.land = self.input_dict_resolved['Land Area Requirement']
		self.pec = self.input_dict_resolved['PEC Cells']

		self.total_solar_collection_area = Quantity(self.cell_area.unit['m2'] 
													* self.cell_number.unit['-'], 
										   'm2')

		cell_plan_view = self.pec['Length']['Value'].unit['m'] * np.cos(self.land['Cell angle']['Value'].unit['rad'])
		total_length = cell_plan_view + self.land['South spacing']['Value'].unit['m']	
		total_width = self.pec['Width']['Value'].unit['m'] + self.land['East/West spacing']['Value'].unit['m']

		self.total_land_area = Quantity(total_width 
										* total_length 
										* self.cell_number.unit['-'], 
								'm2')
