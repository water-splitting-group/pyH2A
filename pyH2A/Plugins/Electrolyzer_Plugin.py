import numpy as np
from pyH2A.Utilities.input_modification import insert, process_table

class Electrolyzer_Plugin:	
	def __init__(
			self, 
			dcf: dict,  # Dictionary containing input data
			print_info: bool  # Flag to control output verbosity
			) -> None:
		"""
		Initializes the Electrolyzer Plugin.

		Parameters:
		dcf (dict): Dictionary containing input data.
		print_info (bool): Flag to print processing information.
		"""
		self.dcf: dict = dcf  # Store input data dictionary
		self.process_input_data()
		self.calculate_h2_production()
		self.calculate_o2_production()
		self.calculate_scaling_factor()
		self.calculate_stack_replacement()
		self.setup_inserts(print_info)
                
	def process_input_data(
			self
			) -> None:
		"""
		Processes input data tables related to electrolyzer operations.
		"""
		process_table(self.dcf.inp, 'Technical Operating Parameters and Specifications', 'Value')
		process_table(self.dcf.inp, 'Electrolyzer', 'Value')
		process_table(self.dcf.inp, 'CAPEX Multiplier', 'Value')

	def calculate_h2_production(
			self
			) -> None:
		"""
		Calculates yearly hydrogen production based on energy generation and efficiency.
		"""
		yearly_energy_generated_electrolyzer: float = self.dcf.inp['Technical Operating Parameters and Specifications']['Yearly Plant Energy Generation (kWh)']['Value']

		# Adjust based on energy ratio if available
		if 'Electrolyzer Plant Energy Ratio' in self.dcf.inp['Technical Operating Parameters and Specifications']:
			yearly_energy_generated_electrolyzer *= self.dcf.inp['Technical Operating Parameters and Specifications']['Electrolyzer Plant Energy Ratio']['Value']
		
		yearly_h2_production: float = (
			yearly_energy_generated_electrolyzer 
			* self.dcf.inp['Electrolyzer']['Conversion efficiency (kg H2/kWh)']['Value'] 
			/ self.dcf.inp['Technical Operating Parameters and Specifications']['Threshold Increase']['Value']
		)  # Hydrogen production in kg per year

		self.h2_production: np.ndarray = np.concatenate([
			np.zeros(self.dcf.inp['Financial Input Values']['construction time']['Value']),  # Zero production during construction
			yearly_h2_production
		])  # Yearly hydrogen production array

		self.total_h2_produced: float = np.sum(yearly_h2_production)  # Total hydrogen produced
	
	def calculate_o2_production(
			self
			) -> None:
		"""
		Calculates total oxygen production based on hydrogen output.
		"""
		MOLAR_RATIO_O2_H2: float = 31.999 / 2.016  # Molar ratio for O2 to H2
		o2_produced: float = (
			1/2 * self.total_h2_produced * MOLAR_RATIO_O2_H2
		)  # Oxygen produced in kg (factor 1/2 due to H2/O2 ratio in electrolysis)

		self.total_o2_produced: float = np.sum(o2_produced)  # Total oxygen produced

	def calculate_scaling_factor(
			self
			) -> None:
		"""
		Computes the scaling factor based on nominal and reference power.
		"""
		number_of_tenfold_increases: float = np.log10(
			self.dcf.inp['Electrolyzer']['Nominal Power (kW)']['Value'] / 
			self.dcf.inp['Electrolyzer']['CAPEX Reference Power (kW)']['Value']
		)  # Logarithmic scaling factor based on power increase

		self.scaling_factor: float = (
			self.dcf.inp['CAPEX Multiplier']['Multiplier']['Value'] ** number_of_tenfold_increases
		)  # Final scaling factor for CAPEX adjustments

	def calculate_stack_replacement(
			self
			) -> None:
		"""
		Determines stack replacement frequency based on operating hours.
		"""
		cumulative_running_time: np.ndarray = np.cumsum(
			self.dcf.inp['Technical Operating Parameters and Specifications']['Plant Active Hours']['Value']
		)  # Cumulative running hours of the plant

		stack_usage: np.ndarray = (
			cumulative_running_time / self.dcf.inp['Electrolyzer']['Replacement time (h)']['Value']
		)  # Stack usage as a fraction of replacement time

		number_of_replacements: int = np.floor_divide(stack_usage[-1], 1)  # Total number of replacements needed

		self.production_maintanence_electrolyzer: float = 1 + number_of_replacements  # Adjusted production & maintenance cost factor

		self.replacement_frequency: float = (
			len(stack_usage) / (number_of_replacements + 1.)
		)  # Frequency of replacements in years

	def setup_inserts(
			self, 
			print_info: bool  # Flag to control output verbosity
			) -> None:
		"""
		Inserts calculated values into the data structure for further processing.

		Parameters:
		print_info (bool): Flag to print inserted values.
		"""
		inserts: list[tuple[str, str, float | np.ndarray]] = [  # List of values to be inserted into the data structure
			('Technical Operating Parameters and Specifications', 'Plant Design Capacity (kg of H2/day)', self.h2_production / 365.),
			('LCA Parameters Photovoltaic', 'H2 produced (kg)', self.total_h2_produced),
			('Technical Operating Parameters and Specifications', 'Operating Capacity Factor (%)', 1.),
			('Electrolyzer', 'Scaling Factor', self.scaling_factor),
			('LCA Parameters Photovoltaic', 'Production and maintenance electrolyzer', self.production_maintanence_electrolyzer),
			('LCA Parameters Photovoltaic', 'H2 produced (kg)', self.total_h2_produced),
			('LCA Parameters Photovoltaic', 'O2 produced (kg)', self.total_o2_produced)
		]

		# Insert values into the data structure
		for category, name, value in inserts:
			insert(self.dcf, category, name, 'Value', value, __name__, print_info=print_info)
		
		# Insert stack replacement frequency separately
		insert(
			self.dcf, 'Planned Replacement', 'Electrolyzer Stack Replacement', 'Frequency (years)', 
			self.replacement_frequency, __name__, print_info=print_info, add_processed=False, insert_path=False
		)
