import numpy as np
from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity

input_dict = {
	"Technical Operating Parameters and Specifications": {
		"Design output per Day": {
			"Value": {
				"type": {float,},
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": "mass",
			},
			"optional": False,
			"description": "Design output in mass per day."
		},
	},
	"PEC Cells": {
		"Cell cost": {
			"Value": {
				"type": {float,},
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": "currency / area",
			},
			"optional": False,
			"description": "Cost of PEC cells."
		},
		"Lifetime": {
			"Value": {
				"type": {float,},
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
				"type": {float,},
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
				"type": {float,},
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
				"type": {float,},
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
				"type": {float,},
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
				"type": {float,},
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
				"type": {float,},
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
				"type": {float,},
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": "power / area",
			},
			"optional": False,
			"description": "Mean solar input in power / area and yearly average of solar input."
		}
	}
}

output_dict = {
	"Non-Depreciable Capital Costs": {
		"Land required": {
			"Value": {
				"inserted_value": "total_land_area", 
				"type": {float,}, 
				"dimension":"area",
        	},
			"description": "Total land area required.",
			"optional": False,
		},
		"Solar collection area": {
			"Value": {
				"inserted_value": "total_solar_collection_area",
				"type": {float,},
				"dimension":"area",
			},
			"description": "Solar collection area.",
			"optional": False,
		}
	},
	"Planned Replacement": {
		"Planned replacement PEC Cells": {
			"Cost": {
				"inserted_value": "cell_cost",
				"type": {float,},
				"dimension":"currency",
			},
			"Frequency": {
				"inserted_value": "input_dict_resolved['PEC Cells']['Lifetime']['Value']",
				"type": {float,}, 
				"dimension":"time",
			},
			"description": "Total cost of replacing all PEC cells once.",
			"optional": False,		
		}
	},
 	"Direct capital costs - PEC Cells": {
		"PEC cell cost": {
			"Value": {
				"inserted_value": "cell_cost",
				"type": {float,}, 
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
				"type": {float,}, 
				"dimension":"dimensionless",
			},
			"description": "Number of individual PEC cells required for design H2 output capacity.",
			"optional": False,
		}
	},
}

class PEC_Plugin:
	'''Simulating H2 production using photoelectrochemical water splitting.

	Parameters
	----------
	Technical Operating Parameters and Specifications > Design Output per Day > Value : float
		Design output in (kg of H2)/day, ``process_table()`` is used.
	PEC Cells > Cell Cost ($/m2) > Value : float
		Cost of PEC cells in $/m2.
	PEC Cells > Lifetime (year) > Value : float
		Lifetime of PEC cells in years before replacement is required.
	PEC Cells > Length (m) > Value : float
		Length of single PEC cell in m.
	PEC Cells > Width (m) > Value : float
		Width of single PEC cell in m.
	Land Area Requirement > Cell Angle (degree) > Value : float
		Angle of PEC cells from the ground, in degrees.
	Land Area Requirement > South Spacing (m) > Value : float
		South spacing of PEC cells in m.
	Land Area Requirement > East/West Spacing (m) > Value : float
		East/West Spacing of PEC cells in m.
	Solar-to-Hydrogen Efficiency > STH (%) > Value : float
		Solar-to-hydrogen efficiency in percentage or as a value between 0 and 1.
	Solar Input > Mean solar input (kWh/m2/day) > Value : float
		Mean solar input in kWh/m2/day, ``process_table()`` is used.

	Returns
	-------
	Non-Depreciable Capital Costs > Land required (acres) > Value : float
		Total land area required in acres.
	Non-Depreciable Capital Costs > Solar Collection Area (m2) > Value : float
		Solar collection area in m2.
	Planned Replacement > Planned Replacement PEC Cells > Cost ($) : float
		Total cost of replacing all PEC cells once.
	Planned Replacement > Planned Replacement PEC Cells > Frequency (years) : float
		Replacement frequency of PEC cells in years, identical to PEC cell lifetime.
	Direct Capital Costs - PEC Cells > PEC Cell Cost ($) > Value : float
		Total cost of all PEC cells.
	PEC Cells > Number > Value : float
		Number of individual PEC cells required for design H2 output capacity.
	'''

	def __init__(self, dcf, print_info):
		self.input_dict_resolved = input_resolver_function(input_dict, dcf, 'PEC_Plugin')

		self.hydrogen_production()
		self.PEC_cost()
		self.land_area()

		output_inserter_function(output_dict, self, dcf, 'PEC_Plugin') 

	def hydrogen_production(self):
		'''Calculation of (kg of H2)/day produced by single PEC cell.
		'''

		pec = self.input_dict_resolved['PEC Cells']

		self.cell_area = Quantity(pec['Length']['Value'].unit['m'] * pec['Width']['Value'].unit['m'], 'm2')
		cell_insolation = self.cell_area.unit['m2'] * self.input_dict_resolved['Solar Input']['Mean solar input']['Value'].unit['W/m2']
		self.H2_molecule_energy = Quantity(2*1.229, 'eV/entity')
		self.H2_molecular_weight = Quantity(2, 'g/mol')
		mol_H2_per_cell_per_second = cell_insolation * self.input_dict_resolved['Solar-to-Hydrogen Efficiency']['STH']['Value'].unit['-'] / self.H2_molecule_energy.unit['J/mol']
		self.mass_rate_H2_per_cell = Quantity(mol_H2_per_cell_per_second*self.H2_molecular_weight.unit['kg/mol'], 'kg/s')
		self.mol_rate_H2_per_m2 = Quantity(mol_H2_per_cell_per_second / self.cell_area.unit['m2'], 'mol/s')

	def PEC_cost(self):
		'''Calculation of cost per cell, number of required cells and total cell cost.
		'''

		cost_per_cell = self.cell_area.unit['m2'] * self.input_dict_resolved['PEC Cells']['Cell Cost']['Value'].unit['USD/m2']
		self.cell_number = Quantity(np.ceil(self.input_dict_resolved['Technical Operating Parameters and Specifications']['Design Output per Day']['Value'].unit['kg'] / self.mass_rate_H2_per_cell.unit['kg/day']), '-')
		self.cell_cost = Quantity(self.cell_number.unit['-'] * cost_per_cell, 'USD')

	def land_area(self):
		'''Calculation of total required land area and solar collection area.
		'''

		self.land = self.input_dict_resolved['Land Area Requirement']
		self.pec = self.input_dict_resolved['PEC Cells']

		self.total_solar_collection_area = Quantity(self.cell_area.unit['m2'] * self.cell_number.unit['-'], 'm2')

		cell_plan_view = self.pec['Length']['Value'].unit['m'] * np.cos(self.land['Cell Angle']['Value'].unit['rad'])
		total_length = cell_plan_view + self.land['South Spacing']['Value'].unit['m']	
		total_width = self.pec['Width']['Value'].unit['m2'] + self.land['East/West Spacing']['Value'].unit['m2']

		self.total_land_area = Quantity(total_width * total_length * self.cell_number.unit['-'], 'm2')
