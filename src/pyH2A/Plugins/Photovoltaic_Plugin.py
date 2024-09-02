from pyH2A.Utilities.input_modification import insert, process_table, read_textfile
import numpy as np
import pprint as pp
import matplotlib.pyplot as plt

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
	Electrolyzer > Maximal electrolyzer capacity > Value : float
		Maximal electrolyzer capacity.
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
	Photovoltaic > Power per module (kW) > Value : float
		Power of a PV module in kW.
	Battery > Capacity (kWh) > Value : float
		Capacity of battery storage in kWh.
	Battery > Round trip efficiency > Value : float
		Round trip efficiency of battery.
	Reverse Osmosis > Power Demand (kWh/m3) > Value : float
		Power demand for the desalination of water using reverse osmosis in kWh/m3.
	Reverse Osmosis > Recovery Rate > Value : float
		Recovery rate of obtained pure water vs sea water using reverse osmosis.
	

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
		process_table(dcf.inp, 'Irradiation Used', 'Value')
		process_table(dcf.inp, 'CAPEX Multiplier', 'Value')
		process_table(dcf.inp, 'Electrolyzer', 'Value')
		process_table(dcf.inp, 'Photovoltaic', 'Value')
		if 'Battery' in dcf.inp:
			process_table(dcf.inp, 'Battery', 'Value')
		process_table(dcf.inp, 'Reverse Osmosis', 'Value')

		self.calculate_H2_production(dcf)
		#self.calculate_initial_h2_production(dcf)
		#self.calculate_osmosis_power_demand(dcf)
		self.calculate_stack_replacement(dcf)
		self.calculate_scaling_factors(dcf)
		self.calculate_area(dcf)
		self.calculate_amount_of_PV(dcf)

		insert(dcf, 'Technical Operating Parameters and Specifications', 'Plant Design Capacity (kg of H2/day)', 'Value', 
			   self.h2_production/365., __name__, print_info = print_info)
		insert(dcf, 'Technical Operating Parameters and Specifications', 'Operating Capacity Factor (%)', 'Value', 
				1., __name__, print_info = print_info)
	
		insert(dcf, 'Planned Replacement', 'Electrolyzer Stack Replacement', 'Frequency (years)', 
				self.replacement_frequency, __name__, print_info = print_info, add_processed = False,
				insert_path = False)

		insert(dcf, 'Electrolyzer', 'Scaling Factor', 'Value', 
				self.electrolyzer_scaling_factor, __name__, print_info = print_info)
		insert(dcf, 'Photovoltaic', 'Scaling Factor', 'Value', 
				self.pv_scaling_factor, __name__, print_info = print_info)

		insert(dcf, 'Non-Depreciable Capital Costs', 'Land required (acres)', 'Value', 
				self.area_acres, __name__, print_info = print_info)
		insert(dcf, 'Non-Depreciable Capital Costs', 'Solar Collection Area (m2)', 'Value', 
				self.area_m2, __name__, print_info = print_info)
		#data needed for LCA calculation for V2
		insert(dcf, 'LCA Parameters Photovoltaic', 'Sea water demand (m3)', 'Value',
				self.total_volume_of_sea_water, __name__, print_info = print_info)
		insert(dcf, 'LCA Parameters Photovoltaic', 'Mass of brine (kg)', 'Value',
				self.total_mass_brine, __name__, print_info = print_info)
		insert(dcf, 'LCA Parameters Photovoltaic', 'Production and maintenance electrolyzer', 'Value',
				self.production_maintanence_electrolyser, __name__, print_info = print_info)
		insert(dcf, 'LCA Parameters Photovoltaic', 'H2 produced (kg)', 'Value',
				self.total_h2_produced, __name__, print_info = print_info)
		insert(dcf, 'LCA Parameters Photovoltaic', 'O2 produced (kg)', 'Value',
				self.total_o2_produced, __name__, print_info = print_info)
		insert(dcf, 'LCA Parameters Photovoltaic', 'Amount of PV modules', 'Value',
				self.amount_of_PV_modules, __name__, print_info = print_info)
		#extras for V1
		insert(dcf, 'LCA Parameters Photovoltaic', 'Amount of fresh water (m3)', 'Value',
				self.total_volume_of_fresh_water, __name__, print_info = print_info)
		insert(dcf, 'LCA Parameters Photovoltaic', 'Produced electricity PV (kW)', 'Value',
				self.total_power_generation, __name__, print_info = print_info)
		insert(dcf, 'LCA Parameters Photovoltaic', 'Electrolyzer power consumption (kW)', 'Value',
				self.total_electrolyzer_power_consumption, __name__, print_info = print_info)
		insert(dcf, 'LCA Parameters Photovoltaic', 'Electricity stored in battery (kW)', 'Value',
				self.total_daily_stored_power, __name__, print_info = print_info)
		insert(dcf, 'LCA Parameters Photovoltaic', 'Electricity reverse osmosis (kW)', 'Value',
				self.total_osmosis_power_demand, __name__, print_info = print_info)
		insert(dcf, 'LCA Parameters Photovoltaic', 'Electricity from battery (kW)', 'Value',
				self.total_additional_power_consumption, __name__, print_info = print_info)


	def calculate_H2_production(self, dcf):
		'''Using hourly irradiation data and electrolyzer as well as PV array parameters,
		H2 production is calculated.
		'''

		if isinstance(dcf.inp['Irradiation Used']['Data']['Value'], str):
			data = read_textfile(dcf.inp['Irradiation Used']['Data']['Value'], delimiter = '	')[:,1]
		else:
			data = dcf.inp['Irradiation Used']['Data']['Value']

		yearly_data = []

		electrolyzer_capacity = dcf.inp['Electrolyzer']['Maximal electrolyzer capacity']['Value']
		initial_h2_production = self.calculate_initial_h2_production(dcf, electrolyzer_capacity)
		osmosis_power_demand = self.calculate_osmosis_power_demand(dcf, initial_h2_production)
		
		for year in dcf.operation_years:
			cumulative_h2_production, cumulative_running_hours = self.annual_electrolyzer_operation_calculation(dcf, year, data, osmosis_power_demand)
			yearly_data.append([year, cumulative_h2_production, cumulative_running_hours])

		self.yearly_data = np.asarray(yearly_data)
		self.h2_production = np.concatenate([np.zeros(dcf.inp['Financial Input Values']['construction time']['Value']), 
												self.yearly_data[:,1]])
		self.total_h2_produced = np.sum(self.yearly_data[:,1]) + initial_h2_production
		
	def annual_electrolyzer_operation_calculation(self, dcf, year, data, osmosis_power_demand):
		'''Annual calculation to calculate power generation, electrolzer power demand, capacity and H2 Produced
		'''

		data_loss_corrected = self.calculate_photovoltaic_loss_correction(dcf, data, year)
		power_generation = data_loss_corrected * dcf.inp['Photovoltaic']['Nominal Power (kW)']['Value'] - osmosis_power_demand
		self.total_power_generation = np.sum(power_generation) + np.sum(osmosis_power_demand)

		electrolyzer_power_demand, power_increase = self.calculate_electrolyzer_power_demand(dcf, year) 
		electrolyzer_power_demand *= np.ones(len(power_generation))
		electrolyzer_power_consumption = np.amin(np.c_[power_generation, electrolyzer_power_demand], axis = 1)
		self.total_electrolyzer_power_consumption = np.sum(electrolyzer_power_consumption)

		threshold = dcf.inp['Electrolyzer']['Minimum capacity']['Value']
		electrolyzer_capacity = electrolyzer_power_consumption / electrolyzer_power_demand
		electrolyzer_capacity[electrolyzer_capacity > threshold] = 1
		electrolyzer_capacity[electrolyzer_capacity <= threshold] = 0

		h2_produced = electrolyzer_power_consumption * dcf.inp['Electrolyzer']['Conversion efficiency (kg H2/kWh)']['Value'] / power_increase
		h2_produced *= electrolyzer_capacity
		
		osmosis_power_demand = self.calculate_osmosis_power_demand(dcf, h2_produced)

		if 'Battery' in dcf.inp:
			additional_H2, additional_working_hours = self.annual_electroyzer_operation_calculation_with_battery(dcf, data,
																	 power_generation, electrolyzer_power_consumption,
																	 electrolyzer_capacity, electrolyzer_power_demand, power_increase)
			return np.sum(h2_produced) + additional_H2, np.sum(electrolyzer_capacity) + additional_working_hours

		else:
			# total_power = np.sum(power_generation)
			# total_consumed = np.sum(electrolyzer_power_consumption * electrolyzer_capacity)
			# print(total_consumed/total_power)
			return np.sum(h2_produced), np.sum(electrolyzer_capacity)	
	
	def annual_electroyzer_operation_calculation_with_battery(self, dcf, data, 
																	power_generation, electrolyzer_power_consumption,
																	electrolyzer_capacity, electrolyzer_power_demand, power_increase):
		'''Calculation of additional H2 production using stored power from battery.
		'''

		if len(data) % 24 != 0:
			raise ValueError("Data length is not a multiple of 24")
		daily_power_generation = power_generation.reshape(-1, 24)	
		daily_power_generation =  daily_power_generation.sum(axis=1)	

		daily_power_consumption = electrolyzer_power_consumption.reshape(-1, 24)
		daily_power_consumption = daily_power_consumption.sum(axis=1)
		daily_excess_power = daily_power_generation - daily_power_consumption
		#battery charging
		capacity = dcf.inp['Battery']['Capacity (kWh)']['Value']
		capacity *= np.ones(len(daily_excess_power))
		daily_stored_power = np.amin(np.c_[daily_excess_power, capacity], axis = 1) * dcf.inp['Battery']['Round trip efficiency']['Value']
		self.total_daily_stored_power = np.sum(daily_stored_power)

		unused_power = electrolyzer_power_consumption * (1 - electrolyzer_capacity)
		daily_unused_power = unused_power.reshape(-1, 24)
		daily_unused_power = daily_unused_power.sum(axis = 1)
		# below-threshold power is used if stored power is greater than below-threshold power (assuming half/half stored + below threshold power to reach above threshold)
		daily_recovered_power = np.where(daily_stored_power > daily_unused_power, daily_unused_power, 0) 
		additional_daily_power = daily_recovered_power + daily_stored_power

		daily_electrolyzer_capacity = electrolyzer_capacity.reshape(-1, 24)
		daily_electrolyzer_working_hours = daily_electrolyzer_capacity.sum(axis =1)
		daily_electrolyzer_off_hours = 24 - daily_electrolyzer_working_hours
		daily_maximum_additional_power_consumption = daily_electrolyzer_off_hours * electrolyzer_power_demand[0]
		#additional h2 generation
		daily_additional_power_consumption = np.amin(np.c_[additional_daily_power, daily_maximum_additional_power_consumption], axis = 1)
		self.total_additional_power_consumption = np.sum(daily_additional_power_consumption)
		daily_additional_H2_production = daily_additional_power_consumption * dcf.inp['Electrolyzer']['Conversion efficiency (kg H2/kWh)']['Value'] / power_increase

		additional_daily_operating_hours = np.ceil(daily_additional_power_consumption / electrolyzer_power_demand[0])	

		# total_power = np.sum(power_generation)
		# total_consumed = np.sum(electrolyzer_power_consumption * electrolyzer_capacity) + np.sum(daily_additional_power_consumption)
		# print(total_consumed/total_power)

		return np.sum(daily_additional_H2_production), np.sum(additional_daily_operating_hours) 
	
	def calculate_initial_h2_production(self, dcf, electrolyzer_capacity):
		'''Calculation of the initial h2 production.
		'''
		
		return electrolyzer_capacity * dcf.inp['Electrolyzer']['Conversion efficiency (kg H2/kWh)']['Value'] * 8766
	
	def calculate_osmosis_power_demand(self, dcf, total_h2_produced):
		'''Calculation of the reverse osmosis power demand and the amount of byprododucts (brine, O2) during electrolysis.
		'''
		
		MOLAR_RATIO_WATER = 18.01528 / 2.016 #molar ratio of for water production, M(H2O) = 18.01528 g/mol, M(H2) = 2.016 g/mol
		mass_fresh_water_demand = total_h2_produced * MOLAR_RATIO_WATER #in kg
		volume_fresh_water_demand = mass_fresh_water_demand / 997 #in m3, density of water = 997 kg/m3
		self.total_volume_of_fresh_water = np.sum(volume_fresh_water_demand)
		volume_sea_water_demand = volume_fresh_water_demand / dcf.inp['Reverse Osmosis']['Recovery Rate']['Value'] #in m3
		self.total_volume_of_sea_water = np.sum(volume_sea_water_demand)
		osmosis_power_demand = dcf.inp['Reverse Osmosis']['Power Demand (kWh/m3)']['Value'] * volume_sea_water_demand / 8766  #kW
		self.total_osmosis_power_demand = np.sum(osmosis_power_demand)
		#calculation for amount of brine
		mass_brine = mass_fresh_water_demand * 0.035 #factor 0.035: per 1 kg of H2O, 0.035 kg of NaCl/brine are obtained during the desalination process starting from 0.6 M NaCl solution (which is sea water)
		self.total_mass_brine = np.sum(mass_brine)
		#calculation for amount of o2
		MOLAR_RATIO_O2_H2 = 31.999 / 2.016 #M(O2) = 31.999 g/mol, M(H2) = 2-016 g/mol
		o2_produced = 1/2 * total_h2_produced * MOLAR_RATIO_O2_H2 #in kg, factor 1/2 due to the H2/O2 ratio (2H2O —› 2H2 + O2
		self.total_o2_produced = np.sum(o2_produced)

		return osmosis_power_demand
	
	def calculate_photovoltaic_loss_correction(self, dcf, data, year):
		'''Calculation of yearly reduction in electricity production by PV array.
		'''

		return data * (1. - dcf.inp['Photovoltaic']['Power loss per year']['Value']) ** year

	def calculate_electrolyzer_power_demand(self, dcf, year):
		'''Calculation of yearly increase in electrolyzer power demand.
		'''

		increase = (1. + dcf.inp['Electrolyzer']['Power requirement increase per year']['Value']) ** year
		demand = increase * dcf.inp['Electrolyzer']['Nominal Power (kW)']['Value']

		return demand, increase
		
	
	def calculate_stack_replacement(self, dcf):
		'''Calculation of stack replacement frequency for electrolyzer.
		'''

		cumulative_running_time = np.cumsum(self.yearly_data[:,2])

		stack_usage = cumulative_running_time / dcf.inp['Electrolyzer']['Replacement time (h)']['Value']
		number_of_replacements = np.floor_divide(stack_usage[-1], 1)

		self.production_maintanence_electrolyser = 1 + number_of_replacements
		self.replacement_frequency = len(stack_usage) / (number_of_replacements + 1.)


	def calculate_scaling_factors(self, dcf):
		'''Calculation of electrolyzer and PV CAPEX scaling factors.
		'''

		self.pv_scaling_factor = self.scaling_factor(dcf, dcf.inp['Photovoltaic']['Nominal Power (kW)']['Value'], dcf.inp['Photovoltaic']['CAPEX Reference Power (kW)']['Value'])
		self.electrolyzer_scaling_factor = self.scaling_factor(dcf, dcf.inp['Electrolyzer']['Nominal Power (kW)']['Value'], dcf.inp['Electrolyzer']['CAPEX Reference Power (kW)']['Value'])
		
	def scaling_factor(self, dcf, power, reference):
		'''Calculation of CAPEX scaling factor based on nominal and reference power.
		'''
		
		number_of_tenfold_increases = np.log10(power/reference)

		return dcf.inp['CAPEX Multiplier']['Multiplier']['Value'] ** number_of_tenfold_increases

	def calculate_area(self, dcf):
		'''Area requirement calculation assuming 1000 W/m2 peak power.'''
		
		peak_kW_per_m2 = dcf.inp['Photovoltaic']['Efficiency']['Value'] * 1.
		self.area_m2 = dcf.inp['Photovoltaic']['Nominal Power (kW)']['Value'] / peak_kW_per_m2
		self.area_acres = self.area_m2 * 0.000247105

	def calculate_amount_of_PV(self, dcf):
		'''Amount of PV modules needed for the h2_production.'''

		self.amount_of_PV_modules = np.ceil(dcf.inp['Photovoltaic']['Nominal Power (kW)']['Value'] / dcf.inp['Photovoltaic']['Power per module (kW)']['Value'])

	
	
	

