import numpy as np
from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity

class Solar_Concentrator_Plugin:

	def __init__(self, dcf, print_info, run = True):
		self._set_up(dcf)
		if run:
			self._run(dcf)

	def _set_up(self, dcf):

		self.functional_unit = dcf.functional_unit

		self.input_dict = {
			"Solar Concentrator": {
				"Concentration factor": {
					"Value": {
						"type": {int, float,},
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
						"type": {int, float,},
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
						"type": {int, float,},
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
						"type": {int, float,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "length",	
					},
					"optional": False,
					"description": "South spacing of solar concentrators (length)."
				},
				"East/West spacing": {
					"Value": {
						"type": {int, float,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "length",	
					},
					"optional": False,
					"description": "East/West Spacing of solar concentrators (length)."
				},
			},
			"Non-Depreciable Capital Costs": {
				"Solar collection area": {
					"Value": {
						"type": {int, float,},
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

		self.output_dict = {
			"Non-Depreciable Capital Costs": {
				"Land required": {
					"Value": {
						"inserted_value": "total_land_area",
						"type": {int, float,},
						"dimension": "area",
					},
					"optional": False,
					"description": "Total land requirement."
				},
				"Solar collection area": {
					"Value": {
						"inserted_value": "total_solar_collection_area",
						"type": {int, float,},
						"dimension": "area",
					},
					"optional": False,
					"description": "Total solar collection area."
				},
			},
			"Direct Capital Costs - Solar Concentrator": {
				"Solar concentrator cost": {
					"Value": {
						"inserted_value": "concentrator_cost",
						"type": {int, float,},
						"dimension": "currency",
					},
					"optional": False,
					"description": "Total cost of all solar concentrators."
				},
			},
		}

	def _run(self, dcf):
		self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, 'Solar_Concentrator_Plugin')

		self.land_area()
		self.calculate_cost()

		output_inserter_function(self.output_dict, self, dcf, 'Solar_Concentrator_Plugin') 

	def land_area(self):
		'''Calculation of solar collection area by multiplying concentration factor by supplied
		solar collection area (the calculation assumes that concentrated solar light 
		is passed as input to the PEC_Plugin, where the corresponding area of PEC cells is calculated. This is the
		supplied solar collection area). 
		Calculation of total land area requirement based on number of PEC cells and spacing of solar concentrators.
		'''

		land = self.input_dict_resolved['Land Area Requirement']

		self.total_solar_collection_area = Quantity(
											  self.input_dict_resolved['Solar Concentrator']['Concentration factor']['Value'].unit['-'] 
											  * self.input_dict_resolved['Non-Depreciable Capital Costs']['Solar collection area']['Value'].unit['m2'], 
										   'm2')

		area_per_element_m2 = self.total_solar_collection_area.unit['m2'] / self.input_dict_resolved['PEC Cells']['Number']['Value'].unit['-']
		side_length_m = np.sqrt(area_per_element_m2)

		x_length_m = side_length_m + land['East/West spacing']['Value'].unit['m']/2.
		y_length_m = side_length_m + land['South spacing']['Value'].unit['m']/2.

		spaced_area_per_element_m2 = x_length_m * y_length_m

		self.total_land_area = Quantity(spaced_area_per_element_m2 
										* self.input_dict_resolved['PEC Cells']['Number']['Value'].unit['-'], 
								'm2')

	def calculate_cost(self):
		'''Calculation of solar concentrator cost based on cost per m2 and total solar collection area.
		'''

		self.concentrator_cost = Quantity(self.input_dict_resolved['Solar Concentrator']['Cost']['Value'].unit['USD/m2'] 
										  * self.total_solar_collection_area.unit['m2'], 
								'USD')
