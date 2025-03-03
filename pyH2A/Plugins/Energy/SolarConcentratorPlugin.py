import numpy as np
from pyH2A.Plugins.Plugin import Plugin
import logging

class SolarConcentratorPlugin(Plugin):
	'''Simulation of solar concentration (used in combination with PEC cells).

	Parameters
	----------
	Solar Concentrator > Concentration Factor > Value : float
		Concentration factor of solar concentration, value > 1.
	Solar Concentrator > Cost ($/m2) > Value : float
		Cost of solar concentrator in $/m2.
	PEC Cells > Number > Value : float
		Number of PEC cells required for design H2 production capacity.
	Land Area Requirement > South Spacing (m) > Value : float
		South spacing of solar concentrators in m.
	Land Area Requirement > East/West Spacing (m) > Value : float
		East/West Spacing (m) of solar concentrators in m.
	Non-Depreciable Capital Costs > Solar Collection Area (m2) > Value : float
		Total solar collection area in m2.

	Returns
	-------
	Non-Depreciable Capital Costs > Land required (m2) > Value : float
		Total land requirement in m2.
	Non-Depreciable Capital Costs > Land required (acres) > Value : float
		Total land requirement in acres.
	Non-Depreciable Capital Costs > Solar Collection Area (m2) > Value : float
		Total solar collection area in m2.
	Direct Capital Costs - Solar Concentrator > Solar Concentrator Cost ($) > Value : float
		Total cost of all solar concentrators.
	'''

	def __init__(
			self, 
			dcf: dict, 
			print_info: bool = False
			) -> None:
		super().__init__(dcf, print_info)

		self.logger = logging.getLogger("pyH2A.Plugins.Energy.SolarConcentratorPlugin")
		self.logger.info("Starting SolarConcentratorPlugin")

		table_keys = ['Solar Concentrator', 'PEC Cells', 'Land Area Requirement', 'Non-Depreciable Capital Costs']
		self.process_table(table_keys)

		self.land_area()
		self.calculate_cost()

		self.insert_table()

	def land_area(
			self
			) -> None:
		'''Calculation of solar collection area by multiplying concentration factor by supplied
		(unconcentrated) solar collection area. Calculation of total land area requirement based
		on number of PEC cells and spacing of solar concentrators.
		'''

		land = self.dcf.inp['Land Area Requirement']

		self.total_solar_collection_area_m2 = self.dcf.inp['Solar Concentrator']['Concentration Factor']['Value'] * self.dcf.inp['Non-Depreciable Capital Costs']['Solar Collection Area (m2)']['Value']

		area_per_element_m2 = self.total_solar_collection_area_m2 / self.dcf.inp['PEC Cells']['Number']['Value']
		side_length_m = np.sqrt(area_per_element_m2)

		x_length_m = side_length_m + land['East/West Spacing (m)']['Value']/2.
		y_length_m = side_length_m + land['South Spacing (m)']['Value']/2.

		spaced_area_per_element_m2 = x_length_m * y_length_m

		total_land_area_m2 = spaced_area_per_element_m2 * self.dcf.inp['PEC Cells']['Number']['Value']
		#total_land_area_m2 = self.total_solar_collection_area_m2 + land['South Spacing (m)']['Value'] * land['East/West Spacing (m)']['Value'] * dcf.inp['PEC Cells']['Number']['Value']
		total_land_area_acres = total_land_area_m2 * 0.000247105
		self.insert_queue.extend([
			('Non-Depreciable Capital Costs', 'Solar Collection Area (m2)', self.total_solar_collection_area_m2),
			('Non-Depreciable Capital Costs', 'Land required (m2)', total_land_area_m2),
			('Non-Depreciable Capital Costs', 'Land required (acres)', total_land_area_acres)
		])

	def calculate_cost(
			self
			) -> None:
		'''Calculation of solar concentrator cost based on cost per m2 and total solar collection area.
		'''

		concentrator_cost = self.dcf.inp['Solar Concentrator']['Cost ($/m2)']['Value'] * self.total_solar_collection_area_m2
		self.insert_queue.append(('Direct Capital Costs - Solar Concentrator', 'Solar Concentrator Cost ($)', concentrator_cost))