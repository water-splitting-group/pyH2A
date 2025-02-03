import numpy as np
from pyH2A.Utilities.input_modification import insert, process_table, read_textfile

class Electrolyser:	
	def __init__(
			self, 
			dcf : dict, 
			print_info : bool
			) -> None:
		self.dcf = dcf
		self.calculate_h2_production()
		self.calculate_o2_production()
		self.calculate_scaling_factor()
		#self.calculate_stack_replacement()
		self.setup_inserts(print_info = False)

	def calculate_h2_production(self):
		electrolyzer_max_capacity = self.dcf.inp['Electrolyzer']['Maximal electrolyzer capacity']['Value']

		self.yearly_data = self.calculate_yearly_h2_production()
		self.h2_production = np.concatenate([np.zeros(self.dcf.inp['Financial Input Values']['construction time']['Value']), 
												self.yearly_data[:,1]])
		self.total_h2_produced = np.sum(self.yearly_data[:,1])

	def calculate_yearly_h2_production(
			self
	 		) -> np.ndarray:
		'''Computes yearly hydrogen production using irradiation data and system parameters.
	
		Parameters
		----------
		data : ndarray
			Hourly irradiation data.
		initial_h2_production : float
			Initial hydrogen production based on electrolyzer capacity.
			
		Returns
		-------
		ndarray
			Array containing yearly hydrogen production and operational metrics.
		'''
		# Calculate yearly hydrogen production and operational metrics
		yearly_data = []
		
		self.anual_electrolyzer_power_demand, _ = self.calculate_electrolyzer_power_demand(0) * 365.25 * 24 
		for year in self.dcf.operation_years:
			electrolyzer_power_demand, power_increase = self.calculate_electrolyzer_power_demand(year)
			h2_produced = electrolyzer_power_demand * 365.25 * 24 * self.dcf.inp['Electrolyzer']['Conversion efficiency (kg H2/kWh)']['Value'] / power_increase
			yearly_data.append([year, h2_produced])

		return np.asarray(yearly_data)

	def calculate_electrolyzer_power_demand(self, year):
		increase = (1. + self.dcf.inp['Electrolyzer']['Power requirement increase per year']['Value']) ** year
		demand = increase * self.dcf.inp['Electrolyzer']['Nominal Power (kW)']['Value']
		return demand, increase
	
	def calculate_o2_production(self):
		MOLAR_RATIO_O2_H2 = 31.999 / 2.016 # Molar ratio for O2 and H2
		o2_produced = 1/2 * self.total_h2_produced * MOLAR_RATIO_O2_H2 #in kg, factor 1/2 due to the H2/O2 ratio (2H2O —› 2H2 + O2
		self.total_o2_produced = np.sum(o2_produced)

	def calculate_scaling_factor(self):
		number_of_tenfold_increases = np.log10(self.dcf.inp['Electrolyzer']['Nominal Power (kW)']['Value']/self.dcf.inp['Electrolyzer']['CAPEX Reference Power (kW)']['Value'])
		self.scaling_factor = self.dcf.inp['CAPEX Multiplier']['Multiplier']['Value'] ** number_of_tenfold_increases

	def calculate_stack_replacement(self, yearly_data):
		cumulative_running_time = np.cumsum(yearly_data[:,2])
		stack_usage = cumulative_running_time / self.dcf.inp['Electrolyzer']['Replacement time (h)']['Value']
		number_of_replacements = np.floor_divide(stack_usage[-1], 1)
		self.production_maintanence_electrolyser = 1 + number_of_replacements
		self.replacement_frequency = len(stack_usage) / (number_of_replacements + 1.)
		

	def setup_inserts(self, print_info):

		inserts = [
			('Technical Operating Parameters and Specifications', 'Plant Design Capacity (kg of H2/day)', self.h2_production/365.),
			('Technical Operating Parameters and Specifications', 'Operating Capacity Factor (%)', 1.),
			('Technical Operating Parameters and Specifications', 'Electrolyzer Anual Power Demand (kWh)', self.anual_electrolyzer_power_demand()),
			('Electrolyzer', 'Scaling Factor', self.scaling_factor),
			#('LCA Parameters Photovoltaic', 'Production and maintenance electrolyzer', self.production_maintanence_electrolyser),
			('LCA Parameters Photovoltaic', 'H2 produced (kg)', self.total_h2_produced),
			('LCA Parameters Photovoltaic', 'O2 produced (kg)', self.total_o2_produced)
		]

		for category, name, value in inserts:
			insert(self.dcf, category, name, 'Value', value, __name__, print_info=print_info)
		
		#insert(self.dcf, 'Planned Replacement', 'Electrolyzer Stack Replacement', 'Frequency (years)', 
		#		self.replacement_frequency, __name__, print_info = print_info, add_processed = False,
		#		insert_path = False)