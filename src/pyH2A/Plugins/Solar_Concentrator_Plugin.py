import numpy as np
from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity

input_dict = {
	"Solar Concentrator": {
		"Concentration factor": {
			"Value": {
				"type": {float,},
				"bounds": (1, None),
			},
			"Unit": {
				"dimension": "dimensionless",
			},
			"optional": False,	
			"description": "Concentration factor of solar concentration, value > 1."
		},
		"Cost": {
			"Value": {
				"type": {float,},
				"bounds": (0, None),
			},	
			"Unit": {
				"dimension": "currency / area",
			},
			"optional": False,
			"description": "Cost of solar concentrator in currency / area."
		},
	},
	"PEC Cells": {
		"Number": {
			"Value": {
				"type": {float,},
				"bounds": (1, None),
			},	
			"Unit": {
				"dimension": "dimensionless",
			},
			"optional": False,
			"description": "Number of PEC cells required for design H2 production capacity."
		},
	},
	"Land Area Requirement": {
		"South spacing": {
			"Value": {
				"type": {float,},
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": "length",	
			},
			"optional": False,
			"description": "South spacing of solar concentrators."
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
			"description": "East/West Spacing of solar concentrators."
		},
	},
	"Non-Depreciable Capital Costs": {
		"Solar collection area": {
			"Value": {
				"type": {float,},
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": "area",
			},
			"optional": False,
			"description": "Total solar collection area."
		},
	},
}

output_dict = {
	"Non-Depreciable Capital Costs": {
		"Land required": {
			"Value": {
				"inserted_value": "total_land_area",
				"type": {float,},
				"dimension": "area",
			},
			"optional": False,
			"description": "Total land requirement."
		},
		"Solar collection area": {
			"Value": {
				"inserted_value": "total_solar_collection_area",
				"type": {float,},
				"dimension": "area",
			},
			"optional": False,
			"description": "Total solar collection area."
		},
	},
	"Itemized Direct Capital Costs - Solar Concentrator": {
		"Solar concentrator cost": {
			"Value": {
				"inserted_value": "concentrator_cost",
				"type": {float,},
				"dimension": "currency",
			},
			"optional": False,
			"description": "Total cost of all solar concentrators."
		},
	},
}

class Solar_Concentrator_Plugin:
	'''Simulation of solar concentration (used in combination with PEC cells).

	Parameters
	----------
	Solar Concentrator > Concentration factor > Value : float
		Concentration factor of solar concentration, value > 1.
	Solar Concentrator > Cost > Value : float
		Cost of solar concentrator.
	PEC Cells > Number > Value : float
		Number of PEC cells required for design H2 production capacity.
	Land Area Requirement > South spacing > Value : float
		South spacing of solar concentrators in m.
	Land Area Requirement > East/West spacing > Value : float
		East/West spacing of solar concentrators.
	Non-Depreciable Capital Costs > Solar Collection Area > Value : float
		Total solar collection area.

	Returns
	-------
	Non-Depreciable Capital Costs > Land required > Value : float
		Total land requirement.
	Non-Depreciable Capital Costs > Land required > Value : float
		Total land requirement.
	Non-Depreciable Capital Costs > Solar Collection Area > Value : float
		Total solar collection area.
	Itemized Direct Capital Costs - Solar Concentrator > Solar Concentrator Cost > Value : float
		Total cost of all solar concentrators.
	'''

	def __init__(self, dcf, print_info):
		self.input_dict_resolved = input_resolver_function(input_dict, dcf, 'Solar_Concentrator_Plugin')

		self.land_area()
		self.calculate_cost()

		output_inserter_function(output_dict, self, dcf, 'Solar_Concentrator_Plugin') 

	def land_area(self):
		'''Calculation of solar collection area by multiplying concentration factor by supplied
		(unconcentrated) solar collection area. Calculation of total land area requirement based
		on number of PEC cells and spacing of solar concentrators.
		'''

		land = self.input_dict_resolved['Land Area Requirement']

		self.total_solar_collection_area = Quantity(self.input_dict_resolved['Solar Concentrator']['Concentration factor']['Value'].unit['-'] * self.input_dict_resolved['Non-Depreciable Capital Costs']['Solar collection area']['Value'].unit['m2'], 'm2')

		area_per_element_m2 = self.total_solar_collection_area.unit['m2'] / self.input_dict_resolved['PEC Cells']['Number']['Value'].unit['-']
		side_length_m = np.sqrt(area_per_element_m2)

		x_length_m = side_length_m + land['East/West spacing']['Value'].unit['m']/2.
		y_length_m = side_length_m + land['South spacing']['Value'].unit['m']/2.

		spaced_area_per_element_m2 = x_length_m * y_length_m

		self.total_land_area = Quantity(spaced_area_per_element_m2 * self.input_dict_resolved['PEC Cells']['Number']['Value'].unit['-'], 'm2')
		#self.total_land_area = Quantity(self.total_solar_collection_area.unit['m2'] + land['South Spacing']['Value'].unit['m'] * land['East/West Spacing (m)']['Value'].unit['m']  * self.input_dict_resolved['PEC Cells']['Number']['Value'].unit['-'] , m2)

	def calculate_cost(self):
		'''Calculation of solar concentrator cost based on cost per m2 and total solar collection area.
		'''

		self.concentrator_cost = Quantity(self.input_dict_resolved['Solar Concentrator']['Cost']['Value'].unit['USD/m2'] * self.total_solar_collection_area.unit['m2'], 'USD')
