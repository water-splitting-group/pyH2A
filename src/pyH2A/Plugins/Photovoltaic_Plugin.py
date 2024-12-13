from pyH2A.Utilities.input_modification import insert, process_table, read_textfile
import numpy as np

class Photovoltaic_Plugin:
	'''Simulation of hydrogen production using PV + electrolysis.

	Parameters
	----------
	Financial Input Values > construction time > Value : int
		Construction time of hydrogen production plant in years.
	Irradiation Used > Data > Value : str or ndarray
		Hourly power ratio data for electricity production calculation. Either a 
		path to a text file containing the data or ndarray. A suitable array 
		can be retrieved from "Hourly Irradiation > *type of tracking* > Value".
	CAPEX Multiplier > Multiplier > Value : float
		Multiplier to describe cost reduction of PV and electrolysis CAPEX for every ten-fold
		increase of power relative to CAPEX reference power. Based on the multiplier the CAPEX
		scaling factor is calculated as: multiplier ^ (number of ten-fold increases). A value
		of 1 leads to no CAPEX reduction, a value < 1 enables cost reduction.
	Electrolyzer > Nominal Power (kW) > Value : float
		Nominal power of electrolyzer in kW.
	Electrolyzer > CAPEX Reference Power (kW) > Value : float
		Reference power of electrolyzer in kW for cost reduction calculation.
	Electrolyzer > Power requirement increase per year > Value : float
		Electrolyzer power requirement increase per year due to stack degradation. Percentage 
		or value > 0. Increase calculated as: (1 + increase per year) ^ year.
	Electrolyzer > Minimum capacity > Value : float
		Minimum capacity required for electrolyzer operation. Percentage or value between 0 and 1.
	Electrolyzer > Conversion efficiency (kg H2/kWh) > Value : float
		Electrical conversion efficiency of electrolyzer in (kg H2)/kWh.
	Electrolyzer > Replacement time (h) > Value : float
		Operating time in hours before stack replacement of electrolyzer is required.
	Photovoltaic > Nominal Power (kW) > Value : float
		Nominal power of PV array in kW.
	Photovoltaic > CAPEX Reference Power (kW) > Value : float
		Reference power of PV array for cost reduction calculations.
	Photovoltaic > Power loss per year > Value : float
		Reduction in power produced by PV array per year due to degradation. Percentage or value
		> 0. Reduction calculated as: (1 - loss per year) ^ year.
	Photovoltaic > Efficiency > Value : float
		Power conversion efficiency of used solar cells. Percentage or value between 0 and 1.

	Returns
	-------
	Technical Operating Parameters and Specifications > Plant Design Capacity (kg of H2/day) > Value : float
		Plant design capacity in (kg of H2)/day calculated from installed 
		PV + electrolysis power capacity and hourly irradiation data.
	Technical Operating Parameters and Specifications >	Operating Capacity Factor (%) > Value : float
		Operating capacity factor is set to 1 (100%).
	Planned Replacement > Electrolyzer Stack Replacement > Frequency (years) : float
		Frequency of electrolyzer stack replacements in years, calculated from replacement time and hourly
		irradiation data.
	Electrolyzer > Scaling Factor > Value : float
		CAPEX scaling factor for electrolyzer calculated based on CAPEX multiplier, 
		reference and nominal power.
	Photovoltaic > Scaling Factor > Value : float
		CAPEX scaling factor for PV array calculated based on CAPEX multiplier, 
		reference and nominal power.
	Non-Depreciable Capital Costs > Land required (acres) > Value : float
		Total land required in acres.
	Non-Depreciable Capital Costs > Solar Collection Area (m2) > Value : float
		Solar collection area in m2.
	'''

	def __init__(self, dcf, print_info):
		self.dcf = dcf
		self.process_input_data()

		# Perform main calculations for the plugin
		self.calculate_H2_production()
		self.calculate_stack_replacement()
		self.calculate_scaling_factors()
		self.calculate_area()

		# Initialize and populate output values
		self.setup_inserts(print_info)
		
	def process_input_data(self):
		'''
        Prepares input data by processing tables and validating required parameters.
        '''
		process_table(self.dcf.inp, 'Irradiation Used', 'Value')
		process_table(self.dcf.inp, 'CAPEX Multiplier', 'Value')
		process_table(self.dcf.inp, 'Electrolyzer', 'Value')
		process_table(self.dcf.inp, 'Photovoltaic', 'Value')
		if 'Battery' in self.dcf.inp:
			process_table(self.dcf.inp, 'Battery', 'Value')
		process_table(self.dcf.inp, 'Reverse Osmosis', 'Value')

	def calculate_H2_production(self):
		'''Using hourly irradiation data and electrolyzer as well as PV array parameters,
		H2 production is calculated.
		'''

		if isinstance(self.dcf.inp['Irradiation Used']['Data']['Value'], str):
			data = read_textfile(self.dcf.inp['Irradiation Used']['Data']['Value'], delimiter = '	')[:,1]
		else:
			data = self.dcf.inp['Irradiation Used']['Data']['Value']

		yearly_data = []

		for year in self.dcf.operation_years:
			data_loss_corrected = self.calculate_photovoltaic_loss_correction(data, year)
			power_generation = data_loss_corrected * self.dcf.inp['Photovoltaic']['Nominal Power (kW)']['Value']

			electrolyzer_power_demand, power_increase = self.calculate_electrolyzer_power_demand(year) 
			electrolyzer_power_demand *= np.ones(len(power_generation))
			electrolyzer_power_consumption = np.amin(np.c_[power_generation, electrolyzer_power_demand], axis = 1)

			threshold = self.dcf.inp['Electrolyzer']['Minimum capacity']['Value']
			electrolyzer_capacity = electrolyzer_power_consumption / electrolyzer_power_demand
			electrolyzer_capacity[electrolyzer_capacity > threshold] = 1
			electrolyzer_capacity[electrolyzer_capacity <= threshold] = 0

			h2_produced = electrolyzer_power_consumption * self.dcf.inp['Electrolyzer']['Conversion efficiency (kg H2/kWh)']['Value'] / power_increase
			h2_produced *= electrolyzer_capacity

			yearly_data.append([year, np.sum(h2_produced), np.sum(electrolyzer_capacity)])

		self.yearly_data = np.asarray(yearly_data)
		self.h2_production = np.concatenate([np.zeros(self.dcf.inp['Financial Input Values']['construction time']['Value']), 
												self.yearly_data[:,1]])

	def calculate_photovoltaic_loss_correction(self, data, year):
		'''Calculation of yearly reduction in electricity production by PV array.
		'''

		return data * (1. - self.dcf.inp['Photovoltaic']['Power loss per year']['Value']) ** year

	def calculate_electrolyzer_power_demand(self, year):
		'''Calculation of yearly increase in electrolyzer power demand.
		'''

		increase = (1. + self.dcf.inp['Electrolyzer']['Power requirement increase per year']['Value']) ** year
		demand = increase * self.dcf.inp['Electrolyzer']['Nominal Power (kW)']['Value']

		return demand, increase

	def calculate_stack_replacement(self):
		'''Calculation of stack replacement frequency for electrolyzer.
		'''

		cumulative_running_time = np.cumsum(self.yearly_data[:,2])
		stack_usage = cumulative_running_time / self.dcf.inp['Electrolyzer']['Replacement time (h)']['Value']

		number_of_replacements = np.floor_divide(stack_usage[-1], 1)

		self.replacement_frequency = len(stack_usage) / (number_of_replacements + 1.)

	def calculate_scaling_factors(self):
		'''Calculation of electrolyzer and PV CAPEX scaling factors.
		'''

		self.pv_scaling_factor = self.scaling_factor(self.dcf.inp['Photovoltaic']['Nominal Power (kW)']['Value'], self.dcf.inp['Photovoltaic']['CAPEX Reference Power (kW)']['Value'])
		self.electrolyzer_scaling_factor = self.scaling_factor(self.dcf.inp['Electrolyzer']['Nominal Power (kW)']['Value'], self.dcf.inp['Electrolyzer']['CAPEX Reference Power (kW)']['Value'])
		
	def scaling_factor(self, power, reference):
		'''Calculation of CAPEX scaling factor based on nominal and reference power.
		'''
		
		number_of_tenfold_increases = np.log10(power/reference)

		return self.dcf.inp['CAPEX Multiplier']['Multiplier']['Value'] ** number_of_tenfold_increases

	def calculate_area(self):
		'''Area requirement calculation assuming 1000 W/m2 peak power.'''

		peak_kW_per_m2 = self.dcf.inp['Photovoltaic']['Efficiency']['Value'] * 1.
		self.area_m2 = self.dcf.inp['Photovoltaic']['Nominal Power (kW)']['Value'] / peak_kW_per_m2
		self.area_acres = self.area_m2 * 0.000247105

	def setup_inserts(self, print_info):
		'''Sets up the output inserts for reporting the results of the calculations.
		
		This method prepares the results to be inserted into the output data structure, including plant design capacity, scaling factors, 
		area required, and other important technical parameters for the system. The data is organized into a list of tuples.
		
		Args:
			print_info (bool): Flag to control whether the information should be printed.
		'''

		inserts = [
			('Technical Operating Parameters and Specifications', 'Plant Design Capacity (kg of H2/day)', self.h2_production/365.),
			('Technical Operating Parameters and Specifications', 'Operating Capacity Factor (%)', 1.),
			('Electrolyzer', 'Scaling Factor', self.electrolyzer_scaling_factor),
			('Photovoltaic', 'Scaling Factor', self.pv_scaling_factor),
			('Non-Depreciable Capital Costs', 'Land required (acres)', self.area_acres),
			('Non-Depreciable Capital Costs', 'Solar Collection Area (m2)', self.area_m2),
			('LCA Parameters Photovoltaic', 'Sea water demand (m3)', self.total_volume_of_sea_water),
			('LCA Parameters Photovoltaic', 'Mass of brine (kg)', self.total_mass_brine),
			('LCA Parameters Photovoltaic', 'Production and maintenance electrolyzer', self.production_maintanence_electrolyser),
			('LCA Parameters Photovoltaic', 'H2 produced (kg)', self.total_h2_produced),
			('LCA Parameters Photovoltaic', 'O2 produced (kg)', self.total_o2_produced),
			('LCA Parameters Photovoltaic', 'Amount of PV modules', self.amount_of_PV_modules),
			('LCA Parameters Photovoltaic', 'Amount of fresh water (m3)', self.total_volume_of_fresh_water),
			# Optional: Uncomment to allow specifying an alternative power source for the plants
			#('LCA Parameters Photovoltaic', 'Produced electricity PV (kW)', self.total_power_generation),
			#('LCA Parameters Photovoltaic', 'Electrolyzer power consumption (kW)', self.total_electrolyzer_power_consumption),
			#('LCA Parameters Photovoltaic', 'Electricity stored in battery (kW)', self.total_daily_stored_power),
			#('LCA Parameters Photovoltaic', 'Electricity reverse osmosis (kW)', self.total_osmosis_power_demand),
			#('LCA Parameters Photovoltaic', 'Electricity from battery (kW)', self.total_additional_power_consumption)
		]

		for category, name, value in inserts:
			insert(self.dcf, category, name, 'Value', value, __name__, print_info=print_info)
	
		insert(self.dcf, 'Planned Replacement', 'Electrolyzer Stack Replacement', 'Frequency (years)', 
				self.replacement_frequency, __name__, print_info = print_info, add_processed = False,
				insert_path = False)