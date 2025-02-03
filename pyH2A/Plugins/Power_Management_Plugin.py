from pyH2A.Utilities.input_modification import insert, process_table

class Power_Management_Plugin:	
	def __init__(
			self, 
			dcf : dict, 
			print_info : bool
			) -> None:
		self.dcf = dcf
		self.process_input_data()
		self.calculate_plant_energy_range()
		self.setup_inserts(print_info)
                
	def process_input_data(
			self,
			) -> None:
		process_table(self.dcf.inp, 'Electrolyzer', 'Value')
		process_table(self.dcf.inp, 'Reverse Osmosis', 'Value')
 	
	def calculate_plant_energy_range(
			self,
			) -> None:
		self.bottom_threshold = self.dcf.inp['Electrolyzer']['Minimum capacity']['Value']
		self.upper_threshold = self.dcf.inp['Electrolyzer']['Maximal electrolyzer capacity']['Value']

		bottom_h2_production = self.bottom_threshold * self.dcf.inp['Electrolyzer']['Conversion efficiency (kg H2/kWh)']['Value']
		upper_h2_production = self.upper_threshold * self.dcf.inp['Electrolyzer']['Conversion efficiency (kg H2/kWh)']['Value']

		MOLAR_RATIO_WATER = 18.01528 / 2.016
		bottom_volume_fresh_water_demand = bottom_h2_production * MOLAR_RATIO_WATER / 997
		upper_volume_fresh_water_demand = upper_h2_production * MOLAR_RATIO_WATER / 997
		bottom_volume_sea_water_demand = bottom_volume_fresh_water_demand / self.dcf.inp['Reverse Osmosis']['Recovery Rate']['Value']
		bottom_volume_sea_water_demand = upper_volume_fresh_water_demand / self.dcf.inp['Reverse Osmosis']['Recovery Rate']['Value']

		bottom_osmosis_power_demand = self.dcf.inp['Reverse Osmosis']['Power Demand (kWh/m3)']['Value'] * bottom_volume_sea_water_demand
		upper_osmosis_power_demand = self.dcf.inp['Reverse Osmosis']['Power Demand (kWh/m3)']['Value'] * bottom_volume_sea_water_demand

		self.bottom_threshold += bottom_osmosis_power_demand
		self.upper_threshold += upper_osmosis_power_demand
	
	def setup_inserts(
			self,
			print_info
			) -> None:
		inserts = [
			('Technical Operating Parameters and Specifications', 'Plant Minimum Energy Threshold (kW)', self.bottom_threshold),
			('Technical Operating Parameters and Specifications', 'Plant Maximum Energy Threshold (kW)', self.upper_threshold),
		]
		for category, name, value in inserts:
			insert(self.dcf, category, name, 'Value', value, __name__, print_info=print_info)