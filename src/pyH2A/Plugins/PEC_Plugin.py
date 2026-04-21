import numpy as np
from pyH2A.Utilities.Energy_Conversion import Energy, kWh, eV
from pyH2A.Utilities.input_modification import insert, process_table

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
				"inserted_value": "total_land_area_acres", 
				"type": {float,}
        	},
			"description": "Total land area required.",
			"optional": False,
		},
		"Solar collection area": {
			"Value": {
				"inserted_value": "total_solar_collection_area",
				"type": {float,}
			},
			"description": "Solar collection area.",
			"optional": False,
		}
	},
	"Planned Replacement": {
		"Planned replacement PEC Cells": {
			"Cost": {
				"inserted_value": "cell_cost",
				"type": {float,}
			},
			"Frequency (years)": {
				"inserted_value": "input_dict_resolved['PEC Cells']['Lifetime (years)']['Value'].unit['year']",
				"type": {float,}
			},
			"description": "Total cost of replacing all PEC cells once.",
			"optional": False,		
		}
	},
 	"Direct capital costs - PEC Cells": {
		"PEC cell cost": {
			"Value": {
				"inserted_value": "cell_cost",
				"type": {float,}
			},
			"description": "Total cost of all PEC cells.",
			"optional": False,
		}
	},
	"PEC Cells": {
		"Number": {
			"Value": {
				"inserted_value": "cell_number",
				"type": {float,}
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
		if 'Solar Concentrator' in dcf.inp:
			process_table(dcf.inp, 'Solar Concentrator', 'Value')

		process_table(dcf.inp, 'Solar Input', 'Value')
		process_table(dcf.inp, 'Solar-to-Hydrogen Efficiency', 'Value')
		process_table(dcf.inp, 'PEC Cells', 'Value')
		process_table(dcf.inp, 'Land Area Requirement', 'Value')
		process_table(dcf.inp, 'Technical Operating Parameters and Specifications', 'Value')

		self.hydrogen_production(dcf)
		self.PEC_cost(dcf)
		self.land_area(dcf)

		insert(dcf, 'Non-Depreciable Capital Costs', 'Land required (acres)', 'Value', 
		       self.total_land_area_acres, __name__, print_info = print_info)
		insert(dcf, 'Non-Depreciable Capital Costs', 'Solar Collection Area (m2)', 'Value', 
			   self.total_solar_collection_area, __name__, print_info = print_info)
		
		insert(dcf, 'Planned Replacement', 'Planned Replacement PEC Cells', 'Cost ($)', 
			   self.cell_cost, __name__, print_info = print_info)
		insert(dcf, 'Planned Replacement', 'Planned Replacement PEC Cells', 'Frequency (years)', 
			   dcf.inp['PEC Cells']['Lifetime (years)']['Value'], __name__, print_info = print_info)

		insert(dcf, 'Direct Capital Costs - PEC Cells', 'PEC Cell Cost ($)', 'Value', 
			   self.cell_cost, __name__, print_info = print_info)

		insert(dcf, 'PEC Cells', 'Number', 'Value', self.cell_number, __name__, print_info = print_info)

	def hydrogen_production(self, dcf):
		'''Calculation of (kg of H2)/day produced by single PEC cell.
		'''

		pec = dcf.inp['PEC Cells']

		self.cell_area = pec['Length (m)']['Value'] * pec['Width (m)']['Value']
		cell_insolation = Energy(self.cell_area * dcf.inp['Solar Input']['Mean solar input (kWh/m2/day)']['Value'], kWh)

		mol_H2_per_cell = (cell_insolation.J * dcf.inp['Solar-to-Hydrogen Efficiency']['STH (%)']['Value']) / Energy(2*1.229, eV).Jmol
		self.kg_H2_per_cell = (2 * mol_H2_per_cell) / 1000.
		self.mol_H2_per_m2_per_day = mol_H2_per_cell / self.cell_area

	def PEC_cost(self, dcf):
		'''Calculation of cost per cell, number of required cells and total cell cost.
		'''

		cost_per_cell = self.cell_area * dcf.inp['PEC Cells']['Cell Cost ($/m2)']['Value']
		self.cell_number = np.ceil(dcf.inp['Technical Operating Parameters and Specifications']['Design Output per Day']['Value'] / self.kg_H2_per_cell)
		self.cell_cost = self.cell_number * cost_per_cell

	def land_area(self, dcf):
		'''Calculation of total required land area and solar collection area.
		'''

		land = dcf.inp['Land Area Requirement']
		pec = dcf.inp['PEC Cells']

		self.total_solar_collection_area = self.cell_area * self.cell_number

		cell_plan_view = pec['Length (m)']['Value'] * np.cos(np.radians(land['Cell Angle (degree)']['Value']))
		total_length = cell_plan_view + land['South Spacing (m)']['Value']	
		total_width = pec['Width (m)']['Value'] + land['East/West Spacing (m)']['Value']

		self.total_land_area = total_width * total_length * self.cell_number
		self.total_land_area_acres = self.total_land_area * 0.000247105
		