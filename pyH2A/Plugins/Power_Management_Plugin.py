from pyH2A.Utilities.input_modification import insert, process_table
import numpy as np

class Power_Management_Plugin:	
	def __init__(
			self, 
			dcf : dict, 
			print_info : bool
			) -> None:
		self.dcf = dcf
		self.process_input_data()
		self.calculate_plant_energy_ratios()
		self.setup_inserts(print_info)
                
	def process_input_data(
			self,
			) -> None:
		process_table(self.dcf.inp, 'Electrolyzer', 'Value')
		process_table(self.dcf.inp, 'Reverse Osmosis', 'Value')
	
	def calculate_plant_power_demand(
			self,
			electrolyser_power_demand
			) -> None:
		MOLAR_RATIO_WATER = 18.01528 / 2.016
		h2_production = electrolyser_power_demand * self.dcf.inp['Electrolyzer']['Conversion efficiency (kg H2/kWh)']['Value']
		volume_fresh_water_demand = h2_production * MOLAR_RATIO_WATER / 997
		volume_sea_water_demand = volume_fresh_water_demand / self.dcf.inp['Reverse Osmosis']['Recovery Rate']['Value']
		osmosis_power_demand = self.dcf.inp['Reverse Osmosis']['Power Demand (kWh/m3)']['Value'] * volume_sea_water_demand
		return electrolyser_power_demand + osmosis_power_demand


	def calculate_plant_energy_ratios(
			self
			) -> None:
		self.bottom_threshold = self.dcf.inp['Electrolyzer']['Minimum capacity']['Value']
		self.upper_threshold = np.array([(1. + self.dcf.inp['Electrolyzer']['Power requirement increase per year']['Value']) ** year 
									  * self.dcf.inp['Electrolyzer']['Maximal electrolyzer capacity']['Value'] for year in self.dcf.operation_years])
		self.electrolyser_plant_energy_ratio = self.bottom_threshold/self.calculate_plant_power_demand(self.bottom_threshold)
		self.osmosis_plant_energy_ratio = 1 - self.electrolyser_plant_energy_ratio
		
	def setup_inserts(
			self,
			print_info
			) -> None:
		inserts = [
			('Technical Operating Parameters and Specifications', 'Plant Minimum Energy Threshold (kW)', self.bottom_threshold),
			('Technical Operating Parameters and Specifications', 'Yearly Plant Maximum Energy Threshold (kW)', self.upper_threshold),
			('Technical Operating Parameters and Specifications', 'Electrolyser Plant Energy Ratio', self.electrolyser_plant_energy_ratio),
			('Technical Operating Parameters and Specifications', 'Reverse Osmosis Plant Energy Ratio', self.osmosis_plant_energy_ratio),
		]
		for category, name, value in inserts:
			insert(self.dcf, category, name, 'Value', value, __name__, print_info=print_info)