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
		process_table(dcf.inp, 'Irradiation Used', 'Value')
		process_table(dcf.inp, 'CAPEX Multiplier', 'Value')
		process_table(dcf.inp, 'Electrolyzer', 'Value')
		process_table(dcf.inp, 'Photovoltaic', 'Value')

		self.calculate_H2_production(dcf)
		self.calculate_stack_replacement(dcf)
		self.calculate_scaling_factors(dcf)
		self.calculate_area(dcf)
		self.calculate_water_osmosis()

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

	def calculate_H2_production(self, dcf):
		'''Using hourly irradiation data and electrolyzer as well as PV array parameters,
		H2 production is calculated.
		'''

		if isinstance(dcf.inp['Irradiation Used']['Data']['Value'], str):
			data = read_textfile(dcf.inp['Irradiation Used']['Data']['Value'], delimiter = '	')[:,1]
		else:
			data = dcf.inp['Irradiation Used']['Data']['Value']

		yearly_data = []

		for year in dcf.operation_years:
			data_loss_corrected = self.calculate_photovoltaic_loss_correction(dcf, data, year)
			power_generation = data_loss_corrected * dcf.inp['Photovoltaic']['Nominal Power (kW)']['Value'] - self.calculate_water_osmosis()
			
			electrolyzer_power_demand, power_increase = self.calculate_electrolyzer_power_demand(dcf, year) 
			electrolyzer_power_demand *= np.ones(len(power_generation))
			electrolyzer_power_consumption = np.amin(np.c_[power_generation, electrolyzer_power_demand], axis = 1)

			#BATTERY

			#here battery parameters are listed, which will later be added to the .md file
			battery_capacity_maximum = 375000  # in kW, based on Palmer 2021 1500 MWh —› depending on the rate in hours e.g. 4 h rate —> 375 MW power capacity
			battery_capacity_minimum = 0.2 * battery_capacity_maximum  # lithium-ion batteries threshold
			battery_efficiency = 0.9  # round_trip_efficiency from 0.85 - 0.95 for Li-ion batteries (also in Palmer 2021)
			battery_charge = battery_capacity_minimum
			#extra power
			extra_power = power_generation - electrolyzer_power_demand
			extra_power = np.array([power if power > 0 else 0 for power in extra_power])
			
		# 	electrolyzer_power_consumption = []
		#	if [extra_power > 0]:
		#		electrolyzer_power_consumption.append(electrolyzer_power_demand)
		#		battery_charge += (extra_power * battery_efficiency)
		#		if [battery_charge > battery_capacity_maximum]:
		#			battery_charge = battery_capacity_maximum			
		#	if [extra_power <= 0]:
		#		electrolyzer_power_deficit = electrolyzer_power_demand - power_generation
		#		if [battery_charge >= electrolyzer_power_deficit / battery_efficiency] and [battery_charge >= battery_capacity_minimum]:								
		#			electrolyzer_power_consumption.append(power_generation + (electrolyzer_power_deficit / battery_efficiency))
		#			battery_charge -= (electrolyzer_power_deficit / battery_efficiency)		
		#		else: 
		#			electrolyzer_power_consumption.append(power_generation)
		#			battery_charge = battery_capacity_minimum
		
	
	
	#		#charging
	#		if [extra_power > 0]:
	#			extra = extra_power * battery_efficiency
	#			battery_charge += (extra_power * battery_efficiency) 
	#			battery_charge[battery_charge > battery_capacity_maximum] = battery_capacity_maximum
	#			battery_charge[battery_charge < battery_capacity_minimum] = battery_capacity_minimum
	#		else:
	#			battery_charge += 0 
	#		#print(battery_charge)
			
			
	#		if [extra_power > 0]:
	#			electrolyzer_power_consumption = electrolyzer_power_demand
	#			battery_charge += (extra_power * battery_efficiency)
	#			print(battery_charge)
	#		else: #when power_generation < electrolyzer_power_demand
	#			electrolyzer_power_deficit = electrolyzer_power_demand - power_generation
	#			if [battery_charge >= electrolyzer_power_deficit / battery_efficiency] and [battery_charge >= battery_capacity_minimum]:
	#				battery_charge -= (electrolyzer_power_deficit / battery_efficiency)					
	#				electrolyzer_power_consumption = power_generation + (electrolyzer_power_deficit / battery_efficiency)
	#			else: 
	#				electrolyzer_power_consumption = power_generation + (battery_charge * battery_efficiency)
	#				battery_charge = battery_capacity_minimum
			#print(electrolyzer_power_consumption)
					
			#OG code
			threshold = dcf.inp['Electrolyzer']['Minimum capacity']['Value']
			electrolyzer_capacity = electrolyzer_power_consumption / electrolyzer_power_demand
			electrolyzer_capacity[electrolyzer_capacity > threshold] = 1
			electrolyzer_capacity[electrolyzer_capacity <= threshold] = 0

			h2_produced = electrolyzer_power_consumption * dcf.inp['Electrolyzer']['Conversion efficiency (kg H2/kWh)']['Value'] / power_increase
			h2_produced *= electrolyzer_capacity

			yearly_data.append([year, np.sum(h2_produced), np.sum(electrolyzer_capacity), np.sum(power_generation)])
			#import pprint
			#pprint.pprint(yearly_data)

		self.yearly_data = np.asarray(yearly_data)
		self.h2_production = np.concatenate([np.zeros(dcf.inp['Financial Input Values']['construction time']['Value']), 
												self.yearly_data[:,1]])

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
		#print('peak_kW/m2', peak_kW_per_m2)
		self.area_m2 = dcf.inp['Photovoltaic']['Nominal Power (kW)']['Value'] / peak_kW_per_m2
		self.area_acres = self.area_m2 * 0.000247105
		#print('self_asea_m2:', self.area_m2, 'self_area_acres:', self.area_acres)

		#PV amount calculation 
		amount_PV = round(dcf.inp['Photovoltaic']['Nominal Power (kW)']['Value'] / dcf.inp['Photovoltaic']['Power (kW)']['Value'])
		print('amount of PV:', amount_PV)
		#PV amount calculation 2 —› depending on the area of the PV
		#area_PV_m2 = #here add the area of the PV
		#amount_PV_check = self.area_m2 / area_PV_m2
		#print('amount_PV_check:', amount_PV_check)

	def calculate_water_osmosis(self):
		'''How much water is needed and what power would reverse osmosis need on a daily basis, since this is then extracted from power generation'''
		
		#yearly water demand is calculated using the estimate of 365 t/year of H2 production
		demand_fresh_water_day = 1 * 18.01528 / 2.016  #in t
		demand_fresh_water_day *= 1 / 0.997 #in m3
		#yearly power demand for pure water with a two-pass reverse osmosis (< 10 ppm of dissolved salt —› needed depending on electrolyzer)
		#the parameters for osmosis should be later added to the .md file 
		osmosis_power_demand = 2.71 #kWh/m3 based on Hausmann 2021 and Kim 208
		osmosis_recovery_rate = 0.4 #based on the ecoinvent database (and Palmer 2021 or Tewlour 2022)
		osmosis_power_demand_day = osmosis_power_demand * demand_fresh_water_day / osmosis_recovery_rate #kWh
		#print(osmosis_power_demand_day)
		
		return osmosis_power_demand_day

		
		

		

