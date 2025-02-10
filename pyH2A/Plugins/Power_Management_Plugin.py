from pyH2A.Utilities.input_modification import insert, process_table
import numpy as np

class Power_Management_Plugin:	
	def __init__(
			self, 
			dcf: dict,  # Dictionary containing input data
			print_info: bool  # Flag to control output verbosity
			) -> None:
		"""
		Initializes the power management plugin.

		Parameters:
		dcf (dict): Dictionary containing input data.
		print_info (bool): Flag to print processing information.
		"""
		self.dcf: dict = dcf  # Store input data dictionary
		self.process_input_data()
		self.calculate_plant_energy_ratios()
		self.setup_inserts(print_info)
                
	def process_input_data(
			self
			) -> None:
		"""
		Processes input data for the Electrolyzer and Reverse Osmosis system.
		"""
		process_table(self.dcf.inp, 'Electrolyzer', 'Value')
		process_table(self.dcf.inp, 'Reverse Osmosis', 'Value')
	
	def calculate_plant_power_demand(
			self,
			electrolyser_power_demand: float  # Power demand of the electrolyzer in kW
			) -> float:
		"""
		Calculates the total plant power demand by considering both electrolyzer 
		and reverse osmosis power consumption.

		Parameters:
		electrolyser_power_demand (float): Power demand of the electrolyzer in kW.

		Returns:
		float: Total plant power demand including reverse osmosis energy consumption.
		"""
		MOLAR_RATIO_WATER: float = 18.01528 / 2.016  # Molar ratio of water to hydrogen

		h2_production: float = (
			electrolyser_power_demand * 
			self.dcf.inp['Electrolyzer']['Conversion efficiency (kg H2/kWh)']['Value']
		)  # Hydrogen production in kg

		volume_fresh_water_demand: float = h2_production * MOLAR_RATIO_WATER / 997  # Required fresh water volume (m³)

		volume_sea_water_demand: float = (
			volume_fresh_water_demand / 
			self.dcf.inp['Reverse Osmosis']['Recovery Rate']['Value']
		)  # Required seawater volume (m³)

		osmosis_power_demand: float = (
			self.dcf.inp['Reverse Osmosis']['Power Demand (kWh/m3)']['Value'] * volume_sea_water_demand
		)  # Power demand for reverse osmosis in kWh

		return electrolyser_power_demand + osmosis_power_demand  # Total plant power demand

	def calculate_plant_energy_ratios(
			self
			) -> None:
		"""
		Computes energy ratios for electrolyzer and reverse osmosis operations.
		"""
		self.threshold_increase: np.ndarray = np.array([
			(1. + self.dcf.inp['Electrolyzer']['Power requirement increase per year']['Value']) ** year 
			for year in self.dcf.operation_years
		])  # Yearly power increase factor

		self.upper_threshold: np.ndarray = (
			self.threshold_increase * self.dcf.inp['Electrolyzer']['Nominal Power (kW)']['Value']
		)  # Maximum power threshold per year

		self.bottom_threshold: np.ndarray = (
			self.dcf.inp['Electrolyzer']['Minimum capacity']['Value'] * self.upper_threshold
		)  # Minimum power threshold per year

		self.electrolyser_plant_energy_ratio: np.ndarray = (
			self.bottom_threshold / self.calculate_plant_power_demand(self.bottom_threshold)
		)  # Ratio of energy used by the electrolyzer

		self.osmosis_plant_energy_ratio: np.ndarray = (
			1 - self.electrolyser_plant_energy_ratio
		)  # Ratio of energy used by reverse osmosis

	def setup_inserts(
			self,
			print_info: bool  # Flag to control output verbosity
			) -> None:
		"""
		Inserts calculated values into the data structure for further processing.

		Parameters:
		print_info (bool): Flag to print inserted values.
		"""
		inserts: list[tuple[str, str, np.ndarray]] = [  # List of values to be inserted into the data structure
			('Technical Operating Parameters and Specifications', 'Yearly Plant Minimum Energy Threshold (kW)', self.bottom_threshold),
			('Technical Operating Parameters and Specifications', 'Yearly Plant Maximum Energy Threshold (kW)', self.upper_threshold),
			('Technical Operating Parameters and Specifications', 'Threshold Increase', self.threshold_increase),
			('Technical Operating Parameters and Specifications', 'Electrolyzer Plant Energy Ratio', self.electrolyser_plant_energy_ratio),
			('Technical Operating Parameters and Specifications', 'Reverse Osmosis Plant Energy Ratio', self.osmosis_plant_energy_ratio),
		]
		for category, name, value in inserts:
			insert(self.dcf, category, name, 'Value', value, __name__, print_info=print_info)  # Insert values into the data structure
