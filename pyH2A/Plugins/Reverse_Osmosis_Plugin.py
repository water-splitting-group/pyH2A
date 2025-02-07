import numpy as np
from pyH2A.Utilities.input_modification import insert, process_table, read_textfile

class Reverse_Osmosis_Plugin:
    def __init__(
			self, 
			dcf : dict, 
			print_info : bool
			) -> None:
        self.dcf = dcf
        self.calculate_osmosis_power_demand()
        self.setup_inserts(print_info)

    def calculate_osmosis_power_demand(self):
        MOLAR_RATIO_WATER = 18.01528 / 2.016
        mass_fresh_water_demand = self.dcf.inp['LCA Parameters Photovoltaic']['H2 produced (kg)']['Value'] * MOLAR_RATIO_WATER
        volume_fresh_water_demand = mass_fresh_water_demand / 997
        self.total_volume_of_fresh_water = np.sum(volume_fresh_water_demand)

        volume_sea_water_demand = volume_fresh_water_demand / self.dcf.inp['Reverse Osmosis']['Recovery Rate']['Value']
        self.total_volume_of_sea_water = np.sum(volume_sea_water_demand)

        self.anual_reverse_osmosis_power_demand = self.dcf.inp['Reverse Osmosis']['Power Demand (kWh/m3)']['Value'] * volume_sea_water_demand

        mass_brine = mass_fresh_water_demand * 0.035
        self.total_mass_brine = np.sum(mass_brine)

    def setup_inserts(
			self, 
			print_info : bool
			) -> None:
        inserts = [
			('Technical Operating Parameters and Specifications', 'Electrolyzer Anual Power Demand (kWh)', self.anual_reverse_osmosis_power_demand),
			('LCA Parameters Photovoltaic', 'Sea water demand (m3)', self.total_volume_of_sea_water),
			('LCA Parameters Photovoltaic', 'Mass of brine (kg)', self.total_mass_brine),
			('LCA Parameters Photovoltaic', 'Amount of fresh water (m3)', self.total_volume_of_fresh_water)
        ]
        for category, name, value in inserts:
            insert(self.dcf, category, name, 'Value', value, __name__, print_info=print_info)
	