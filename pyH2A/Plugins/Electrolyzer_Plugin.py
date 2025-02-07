import numpy as np
from pyH2A.Utilities.input_modification import insert, process_table, read_textfile

class Electrolyzer_Plugin:	
	def __init__(
			self, 
			dcf : dict, 
			print_info : bool
			) -> None:
		self.dcf = dcf
		self.calculate_h2_production()
		self.calculate_o2_production()
		self.calculate_scaling_factor()
		self.calculate_stack_replacement()
		self.setup_inserts(print_info)
                
	def process_input_data(
			self,
			) -> None:
		process_table(self.dcf.inp, 'Technical Operating Parameters and Specifications', 'Value')
		process_table(self.dcf.inp, 'Electrolyzer', 'Value')
		process_table(self.dcf.inp, 'CAPEX Multiplier', 'Value')

	def calculate_h2_production(self):
		yearly_energy_generated_electrolyser = self.dcf.inp['Technical Operating Parameters and Specifications']['Yearly Plant Energy Generation (kWh)']['Value']
		if 'Electrolyser Plant Energy Ratio' in self.dcf.inp['Technical Operating Parameters and Specifications']:
			yearly_energy_generated_electrolyser *= self.dcf.inp['Technical Operating Parameters and Specifications']['Electrolyser Plant Energy Ratio']['Value']
		
		yearly_h2_production = yearly_energy_generated_electrolyser * self.dcf.inp['Electrolyzer']['Conversion efficiency (kg H2/kWh)']['Value']
		self.h2_production = np.concatenate([
			np.zeros(self.dcf.inp['Financial Input Values']['construction time']['Value']),
			yearly_h2_production
		])
		self.total_h2_produced = np.sum(yearly_h2_production)
	
	def calculate_o2_production(self):
		MOLAR_RATIO_O2_H2 = 31.999 / 2.016 # Molar ratio for O2 and H2
		o2_produced = 1/2 * self.total_h2_produced * MOLAR_RATIO_O2_H2 #in kg, factor 1/2 due to the H2/O2 ratio (2H2O —› 2H2 + O2
		self.total_o2_produced = np.sum(o2_produced)

	def calculate_scaling_factor(self):
		number_of_tenfold_increases = np.log10(self.dcf.inp['Electrolyzer']['Nominal Power (kW)']['Value']/self.dcf.inp['Electrolyzer']['CAPEX Reference Power (kW)']['Value'])
		self.scaling_factor = self.dcf.inp['CAPEX Multiplier']['Multiplier']['Value'] ** number_of_tenfold_increases

	def calculate_stack_replacement(self):
		cumulative_running_time = np.cumsum(self.dcf.inp['Technical Operating Parameters and Specifications']['Plant Active Hours']['Value'])
		stack_usage = cumulative_running_time / self.dcf.inp['Electrolyzer']['Replacement time (h)']['Value']
		number_of_replacements = np.floor_divide(stack_usage[-1], 1)
		self.production_maintanence_electrolyser = 1 + number_of_replacements
		self.replacement_frequency = len(stack_usage) / (number_of_replacements + 1.)
		

	def setup_inserts(self, print_info):

		inserts = [
			('Technical Operating Parameters and Specifications', 'Plant Design Capacity (kg of H2/day)', self.h2_production/365.),
			('LCA Parameters Photovoltaic', 'H2 produced (kg)', self.total_h2_produced),
			('Technical Operating Parameters and Specifications', 'Operating Capacity Factor (%)', 1.),
			('Electrolyzer', 'Scaling Factor', self.scaling_factor),
			('LCA Parameters Photovoltaic', 'Production and maintenance electrolyzer', self.production_maintanence_electrolyser),
			('LCA Parameters Photovoltaic', 'H2 produced (kg)', self.total_h2_produced),
			('LCA Parameters Photovoltaic', 'O2 produced (kg)', self.total_o2_produced)
		]

		for category, name, value in inserts:
			insert(self.dcf, category, name, 'Value', value, __name__, print_info=print_info)
		
		insert(self.dcf, 'Planned Replacement', 'Electrolyzer Stack Replacement', 'Frequency (years)', 
				self.replacement_frequency, __name__, print_info = print_info, add_processed = False,
				insert_path = False)