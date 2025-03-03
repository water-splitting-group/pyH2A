from pyH2A import Discounted_Cash_Flow
from pyH2A.Utilities.input_modification import read_textfile, hourly_to_daily_power
from pyH2A.Plugins.Plugin import Plugin
import numpy as np
import logging

class Photovoltaic_Plugin(Plugin):
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

	def __init__(
			self, 
			dcf: dict, 
			print_info: bool = False
			) -> None:
		super().__init__(dcf, print_info)

		self.logger = logging.getLogger("pyH2A.Plugins.Energy.Photosoltaic_Plugin")
		self.logger.info("Starting Photovoltaic_Plugin")

		table_keys = ['Irradiation Used', 'CAPEX Multiplier', 'Photovoltaic']
		self.process_table(table_keys)

		self.calculate_power_production()
		self.calculate_scaling_factors()
		self.calculate_area()

		LCA_exports = Photovoltaic_Plugin_LCA_Export(self)
		LCA_exports.inserts
		self.insert_table()


	def calculate_power_production(
			self
			) -> None:
		'''Using hourly irradiation data and PV array parameters,
		power production is calculated.
		'''

		if isinstance(self.dcf.inp['Irradiation Used']['Data']['Value'], str):
			data = read_textfile(self.dcf.inp['Irradiation Used']['Data']['Value'], delimiter = '	')[:,1]
		else:
			data = self.dcf.inp['Irradiation Used']['Data']['Value']

		yearly_data = {}
		yearly_data_daily_power = {}

		for year in self.dcf.operation_years:
			data_loss_corrected = self.calculate_photovoltaic_loss_correction(data, year)
			power_generation = data_loss_corrected * self.dcf.inp['Photovoltaic']['Nominal Power (kW)']['Value']

			yearly_data[year] = power_generation
			yearly_data_daily_power[year] = hourly_to_daily_power(power_generation)
		
		self.insert_queue.extend([
			('Power Generation', 'PV Hourly Power Generation (kWh)', yearly_data),
			('Power Generation', 'Available Power (hourly, kWh)', yearly_data),
			('Power Generation', 'Available Power (daily, kWh)', yearly_data_daily_power)
		])

	def calculate_photovoltaic_loss_correction(
			self, 
			data: np.ndarray, 
			year: int
			) -> np.ndarray:
		'''Calculation of yearly reduction in electricity production by PV array.
		'''

		return data * (1. - self.dcf.inp['Photovoltaic']['Power loss per year']['Value']) ** year

	def calculate_scaling_factors(
			self
			) -> None:
		'''Calculation of PV CAPEX scaling factors.
		'''

		pv_scaling_factor = self.scaling_factor(
			self.dcf.inp['Photovoltaic']['Nominal Power (kW)']['Value'], 
			self.dcf.inp['Photovoltaic']['CAPEX Reference Power (kW)']['Value']
		)
		self.insert_queue.append(('Photovoltaic', 'Scaling Factor', pv_scaling_factor))

	def scaling_factor(
			self, 
			power: float, 
			reference: float
			) -> float:
		'''Calculation of CAPEX scaling factor based on nominal and reference power.
		'''
		number_of_tenfold_increases = np.log10(power/reference)
		return self.dcf.inp['CAPEX Multiplier']['Multiplier']['Value'] ** number_of_tenfold_increases

	def calculate_area(
			self
			) -> None:
		'''Area requirement calculation assuming 1000 W/m2 peak power.'''

		peak_kW_per_m2 = self.dcf.inp['Photovoltaic']['Efficiency']['Value'] * 1.
		area_m2 = self.dcf.inp['Photovoltaic']['Nominal Power (kW)']['Value'] / peak_kW_per_m2
		area_acres = area_m2 * 0.000247105

		self.insert_queue.extend([
			('Non-Depreciable Capital Costs', 'Land required (acres)', area_acres),
			('Non-Depreciable Capital Costs', 'Solar Collection Area (m2)', area_m2)
		])
class Photovoltaic_Plugin_LCA_Export(Photovoltaic_Plugin):
	
	def __init__(
			self, 
			) -> None:
		
		self.inserts = []
	
	def calculate_panel_number(self, dcf, PV_plugin_instance):

		self.inserts['PV Panels'] = 10

		return 