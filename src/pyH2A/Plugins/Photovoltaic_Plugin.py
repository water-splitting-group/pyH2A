from pyH2A.Utilities.input_modification import insert, process_table, read_textfile, hourly_to_daily_power
import numpy as np

class Photovoltaic_Plugin:
	'''Simulation of electricity production using PV.

	Parameters
	----------
	Irradiation Used > Data > Value : str or ndarray
		Hourly power ratio data for electricity production calculation. Either a 
		path to a text file containing the data or ndarray. A suitable array 
		can be retrieved from "Hourly Irradiation > *type of tracking* > Value".
	CAPEX Multiplier > Multiplier > Value : float
		Multiplier to describe cost reduction of PV CAPEX for every ten-fold
		increase of power relative to CAPEX reference power. Based on the multiplier the CAPEX
		scaling factor is calculated as: multiplier ^ (number of ten-fold increases). A value
		of 1 leads to no CAPEX reduction, a value < 1 enables cost reduction.
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
	Photovoltaic > Scaling Factor > Value : float
		CAPEX scaling factor for PV array calculated based on CAPEX multiplier, 
		reference and nominal power.
	Power Generation > PV Hourly Power Generation (kWh) > Value : dict
		Hourly power generation of PV array in kWh (dictionary of years).
	Power Generation > Available Power (hourly, kWh) > Value : dict
		Available power, hourly basis, dictionary of years (in kWh).
	Power Generation > Available Power (daily, kWh) > Value : dict
		Available power, daily basis, dictionary of years (in kWh).
	Non-Depreciable Capital Costs > Land required (acres) > Value : float
		Total land required in acres.
	Non-Depreciable Capital Costs > Solar Collection Area (m2) > Value : float
		Solar collection area in m2.
	'''

	def __init__(self, dcf, print_info):
		process_table(dcf.inp, 'Irradiation Used', 'Value')
		process_table(dcf.inp, 'CAPEX Multiplier', 'Value')
		process_table(dcf.inp, 'Photovoltaic', 'Value', print_processing_warning = False)

		self.calculate_power_production(dcf)
		self.calculate_scaling_factors(dcf)
		self.calculate_area(dcf)

		insert(dcf, 'Photovoltaic', 'Scaling Factor', 'Value', 
				self.pv_scaling_factor, __name__, print_info = print_info)
		
		insert(dcf, 'Power Generation', 'PV Hourly Power Generation (kWh)', 'Value',
				self.power_generation_yearly_data, __name__, print_info = print_info)
		insert(dcf, 'Power Generation', 'Available Power (hourly, kWh)', 'Value',
				self.power_generation_yearly_data, __name__, print_info = print_info)
		insert(dcf, 'Power Generation', 'Available Power (daily, kWh)', 'Value',
		 		self.power_generation_yearly_data_daily_power, __name__, print_info = print_info)

		insert(dcf, 'Non-Depreciable Capital Costs', 'Land required (acres)', 'Value', 
				self.area_acres, __name__, print_info = print_info)
		insert(dcf, 'Non-Depreciable Capital Costs', 'Solar Collection Area (m2)', 'Value', 
				self.area_m2, __name__, print_info = print_info)

	def calculate_power_production(self, dcf):
		'''Using hourly irradiation data and PV array parameters,
		power production is calculated.
		'''

		if isinstance(dcf.inp['Irradiation Used']['Data']['Value'], str):
			data = read_textfile(dcf.inp['Irradiation Used']['Data']['Value'], delimiter = '	')[:,1]
		else:
			data = dcf.inp['Irradiation Used']['Data']['Value']

		yearly_data = {}
		yearly_data_daily_power = {}

		for year in dcf.operation_years:
			data_loss_corrected = self.calculate_photovoltaic_loss_correction(dcf, data, year)
			power_generation = data_loss_corrected * dcf.inp['Photovoltaic']['Nominal Power (kW)']['Value']

			yearly_data[year] = power_generation
			yearly_data_daily_power[year] = hourly_to_daily_power(power_generation)

		self.power_generation_yearly_data = yearly_data
		self.power_generation_yearly_data_daily_power = yearly_data_daily_power

	def calculate_photovoltaic_loss_correction(self, dcf, data, year):
		'''Calculation of yearly reduction in electricity production by PV array.
		'''

		return data * (1. - dcf.inp['Photovoltaic']['Power loss per year']['Value']) ** year

	def calculate_scaling_factors(self, dcf):
		'''Calculation of PV CAPEX scaling factors.
		'''

		self.pv_scaling_factor = self.scaling_factor(dcf, dcf.inp['Photovoltaic']['Nominal Power (kW)']['Value'], dcf.inp['Photovoltaic']['CAPEX Reference Power (kW)']['Value'])
		
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

