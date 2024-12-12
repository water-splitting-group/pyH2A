from pyH2A.Utilities.input_modification import insert, process_table, read_textfile
import numpy as np
import pprint as pp
import matplotlib.pyplot as plt

class Photovoltaic_Plugin:
	"""
	Simulation of hydrogen production using a photovoltaic (PV) system combined with electrolysis.

    Attributes:
    ----------
    dcf : object
        Data container framework that holds input parameters and operational data.
    
    print_info : bool
        Flag to determine if debugging or summary information should be printed.

    Methods:
    -------
    process_input_data()
        Prepares and validates input data for further calculations.

    calculate_H2_production()
        Calculates hydrogen production based on irradiation data and system parameters.

    load_irradiation_data()
        Loads and processes hourly irradiation data from a file or ndarray.

    calculate_yearly_h2_production(data, initial_h2_production)
        Computes yearly hydrogen production and operational data.

    annual_electrolyzer_operation_calculation(year, data, osmosis_power_demand)
        Performs annual calculations for electrolyzer operation.

    calculate_initial_h2_production(electrolyzer_capacity)
        Computes the initial hydrogen production based on electrolyzer capacity.

    calculate_osmosis_power_demand(total_h2_produced)
        Estimates the power demand for reverse osmosis and byproducts of electrolysis.

    calculate_photovoltaic_loss_correction(data, year)
        Adjusts power generation data for yearly PV losses.

    calculate_electrolyzer_power_demand(year)
        Determines the yearly power demand for the electrolyzer, accounting for degradation.

    calculate_stack_replacement()
        Calculates the frequency of stack replacements for the electrolyzer.

    calculate_scaling_factors()
        Computes scaling factors for PV and electrolyzer capital expenditures (CAPEX).

    calculate_area()
        Estimates the land and collection area required for the PV system.

    calculate_amount_of_PV()
        Determines the number of PV modules needed.

    initialize_inserts(print_info)
        Populates the output dictionary with calculated values for reporting.

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
	"""

	def __init__(self, dcf, print_info):
		self.dcf = dcf
		self.process_input_data()

		# Perform main calculations for the plugin
		self.calculate_H2_production()
		#self.calculate_initial_h2_production(dcf)
		#self.calculate_osmosis_power_demand(dcf)
		self.calculate_stack_replacement()
		self.calculate_scaling_factors()
		self.calculate_area()
		self.calculate_amount_of_PV()

		# Initialize and populate output values
		self.setup_inserts(print_info)

	def process_input_data(self):
		"""
        Prepares input data by processing tables and validating required parameters.
        """
		process_table(self.dcf.inp, 'Irradiation Used', 'Value')
		process_table(self.dcf.inp, 'CAPEX Multiplier', 'Value')
		process_table(self.dcf.inp, 'Electrolyzer', 'Value')
		process_table(self.dcf.inp, 'Photovoltaic', 'Value')
		if 'Battery' in self.dcf.inp:
			process_table(self.dcf.inp, 'Battery', 'Value')
		process_table(self.dcf.inp, 'Reverse Osmosis', 'Value')

	def calculate_H2_production(self):
		"""
        Calculates hydrogen production using hourly irradiation data, PV, and electrolyzer parameters.
        """

		data = self.load_irradiation_data()
		electrolyzer_capacity = self.dcf.inp['Electrolyzer']['Maximal electrolyzer capacity']['Value']
		initial_h2_production = self.calculate_initial_h2_production(electrolyzer_capacity)
		self.yearly_data = self.calculate_yearly_h2_production(data, initial_h2_production)
		self.h2_production = np.concatenate([np.zeros(self.dcf.inp['Financial Input Values']['construction time']['Value']), 
												self.yearly_data[:,1]])
		self.total_h2_produced = np.sum(self.yearly_data[:,1]) + initial_h2_production

	def load_irradiation_data(self):
		"""
        Loads hourly irradiation data from a file or array.

        Returns:
        	ndarray: Array containing hourly irradiation data.
        """
		if isinstance(self.dcf.inp['Irradiation Used']['Data']['Value'], str):
			return read_textfile(self.dcf.inp['Irradiation Used']['Data']['Value'], delimiter = '	')[:, 1]
		else:
			return self.dcf.inp['Irradiation Used']['Data']['Value']
	
	def calculate_yearly_h2_production(self, data, initial_h2_production):
		"""
        Computes yearly hydrogen production using irradiation data and system parameters.

        Args:
			data (ndarray): Hourly irradiation data.
	        initial_h2_production (float): Initial hydrogen production based on electrolyzer capacity.

        Returns:
        	ndarray: Array containing yearly hydrogen production and operational metrics.
        """
		yearly_data = []
		osmosis_power_demand = self.calculate_osmosis_power_demand(initial_h2_production)
		
		for year in self.dcf.operation_years:
			cumulative_h2_production, cumulative_running_hours = self.annual_electrolyzer_operation_calculation(year, data, osmosis_power_demand)
			yearly_data.append([year, cumulative_h2_production, cumulative_running_hours])

		return np.asarray(yearly_data)
		
	def annual_electrolyzer_operation_calculation(self, year, data, osmosis_power_demand):
		"""
        Calculates yearly power generation, electrolyzer power demand, capacity, and hydrogen production.

        Parameters:
        	year (int): Current operational year.
        	data (ndarray): Hourly irradiation data.
        	osmosis_power_demand (float): Power demand for reverse osmosis operations.

        Returns:
        	float: Total hydrogen production and operational hours for the electrolyzer.
        """
		# Adjust irradiation data based on yearly photovoltaic losses
		data_loss_corrected = self.calculate_photovoltaic_loss_correction(data, year)
		# Calculate power generation from the PV array
		power_generation = data_loss_corrected * self.dcf.inp['Photovoltaic']['Nominal Power (kW)']['Value'] - osmosis_power_demand
		self.total_power_generation = np.sum(power_generation) + np.sum(osmosis_power_demand)

		# Calculate electrolyzer power demand and increase due to degradation
		electrolyzer_power_demand, power_increase = self.calculate_electrolyzer_power_demand(year) 
		electrolyzer_power_demand *= np.ones(len(power_generation))
		electrolyzer_power_consumption = np.amin(np.c_[power_generation, electrolyzer_power_demand], axis = 1)
		self.total_electrolyzer_power_consumption = np.sum(electrolyzer_power_consumption)

		# Determine the electrolyzer capacity based on a minimum threshold
		threshold = self.dcf.inp['Electrolyzer']['Minimum capacity']['Value']
		electrolyzer_capacity = electrolyzer_power_consumption / electrolyzer_power_demand
		electrolyzer_capacity[electrolyzer_capacity > threshold] = 1
		electrolyzer_capacity[electrolyzer_capacity <= threshold] = 0

		# Calculate hydrogen produced by electrolyzer
		h2_produced = electrolyzer_power_consumption * self.dcf.inp['Electrolyzer']['Conversion efficiency (kg H2/kWh)']['Value'] / power_increase
		h2_produced *= electrolyzer_capacity
		
		# Recalculate osmosis power demand based on hydrogen production
		osmosis_power_demand = self.calculate_osmosis_power_demand(h2_produced)

		# Handle battery-based system for additional hydrogen production
		if 'Battery' in self.dcf.inp:
			additional_H2, additional_working_hours = self.annual_electroyzer_operation_calculation_with_battery(data,
																	 power_generation, electrolyzer_power_consumption,
																	 electrolyzer_capacity, electrolyzer_power_demand, power_increase)
			return np.sum(h2_produced) + additional_H2, np.sum(electrolyzer_capacity) + additional_working_hours

		else:
			# total_power = np.sum(power_generation)
			# total_consumed = np.sum(electrolyzer_power_consumption * electrolyzer_capacity)
			# print(total_consumed/total_power)
			return np.sum(h2_produced), np.sum(electrolyzer_capacity)	
	
	def annual_electroyzer_operation_calculation_with_battery(self, data, 
																	power_generation, electrolyzer_power_consumption,
																	electrolyzer_capacity, electrolyzer_power_demand, power_increase):
		"""
		Calculation of additional hydrogen (H2) production using stored power from a battery.

		This method computes the additional hydrogen produced when a battery stores excess power generated by a photovoltaic system.
		It calculates how much excess power can be used to produce hydrogen when the electrolyzer's daily capacity exceeds the available power from direct generation.

		Args:
			data (ndarray): Hourly data used for power generation analysis.
			power_generation (ndarray): Array of power generation values (kW) from the solar system.
			electrolyzer_power_consumption (ndarray): Power consumption of the electrolyzer over time.
			electrolyzer_capacity (ndarray): The capacity of the electrolyzer system at each time point.
			electrolyzer_power_demand (ndarray): The power demand required by the electrolyzer to operate.
			power_increase (float): Power increase factor accounting for efficiency or other operational adjustments.

		Returns:
			tuple: 
				- Total additional hydrogen production (float), calculated from the recovered and stored power.
				- Total additional operating hours (float), based on the recovered and stored power.

		"""
		# Check if data length is a multiple of 24 hours (daily data)
		if len(data) % 24 != 0:
			raise ValueError("Data length is not a multiple of 24")
		
		# Reshape the power generation data into daily sums
		daily_power_generation = power_generation.reshape(-1, 24)	
		daily_power_generation =  daily_power_generation.sum(axis=1)  # Sum generation for each day

		# Reshape the electrolyzer power consumption into daily sums
		daily_power_consumption = electrolyzer_power_consumption.reshape(-1, 24)
		daily_power_consumption = daily_power_consumption.sum(axis=1)  # Sum consumption for each day

		# Calculate excess power generated each day
		daily_excess_power = daily_power_generation - daily_power_consumption
		
		# Battery charging based on excess power and battery capacity
		capacity = self.dcf.inp['Battery']['Capacity (kWh)']['Value']
		capacity *= np.ones(len(daily_excess_power))  # Ensure capacity is the same length as daily data
		# Store excess power in battery, considering round trip efficiency
		daily_stored_power = np.amin(np.c_[daily_excess_power, capacity], axis = 1) * self.dcf.inp['Battery']['Round trip efficiency']['Value']
		self.total_daily_stored_power = np.sum(daily_stored_power)

		# Calculate unused power if electrolyzer capacity is below its maximum
		unused_power = electrolyzer_power_consumption * (1 - electrolyzer_capacity)
		daily_unused_power = unused_power.reshape(-1, 24)
		daily_unused_power = daily_unused_power.sum(axis = 1)
		
		# Use stored power only if it exceeds the unused power, assuming stored + below-threshold power is used
		daily_recovered_power = np.where(daily_stored_power > daily_unused_power, daily_unused_power, 0) 

		# Additional power available for electrolyzer operation (stored + recovered)
		additional_daily_power = daily_recovered_power + daily_stored_power

		# Calculate daily electrolyzer working hours based on its capacity
		daily_electrolyzer_capacity = electrolyzer_capacity.reshape(-1, 24)
		daily_electrolyzer_working_hours = daily_electrolyzer_capacity.sum(axis =1)
		daily_electrolyzer_off_hours = 24 - daily_electrolyzer_working_hours

		# Maximum additional power consumption when electrolyzer is not operating
		daily_maximum_additional_power_consumption = daily_electrolyzer_off_hours * electrolyzer_power_demand[0]
		
		# Determine the additional power consumption based on available stored and recovered power
		daily_additional_power_consumption = np.amin(np.c_[additional_daily_power, daily_maximum_additional_power_consumption], axis = 1)
		self.total_additional_power_consumption = np.sum(daily_additional_power_consumption)

		# Calculate the additional hydrogen produced based on the additional power consumed
		daily_additional_H2_production = daily_additional_power_consumption * self.dcf.inp['Electrolyzer']['Conversion efficiency (kg H2/kWh)']['Value'] / power_increase

		# Calculate the additional operating hours based on the additional power consumption
		additional_daily_operating_hours = np.ceil(daily_additional_power_consumption / electrolyzer_power_demand[0])	

		# total_power = np.sum(power_generation)
		# total_consumed = np.sum(electrolyzer_power_consumption * electrolyzer_capacity) + np.sum(daily_additional_power_consumption)
		# print(total_consumed/total_power)

		# Return the total additional hydrogen production and total additional operating hours
		return np.sum(daily_additional_H2_production), np.sum(additional_daily_operating_hours) 
	
	def calculate_initial_h2_production(self, electrolyzer_capacity):
		"""
		Calculation of the initial hydrogen production from the electrolyzer's capacity.
		
		Args:
			electrolyzer_capacity (float): The maximal electrolyzer capacity in kW.

		Returns:
			float: Initial hydrogen production in kg, based on electrolyzer efficiency and operational time.
		"""
		
		return electrolyzer_capacity * self.dcf.inp['Electrolyzer']['Conversion efficiency (kg H2/kWh)']['Value'] * 8766
	
	def calculate_osmosis_power_demand(self, total_h2_produced):
		"""Estimates the power demand for reverse osmosis and byproducts of electrolysis (brine, O2).
		
		Args:
			total_h2_produced (float): Total hydrogen produced during the year.

		Returns:
			ndarray: Estimated power demand for desalination using reverse osmosis in kW.
		"""
		
		MOLAR_RATIO_WATER = 18.01528 / 2.016 # Molar ratio for water production (H2O) and hydrogen (H2)
		mass_fresh_water_demand = total_h2_produced * MOLAR_RATIO_WATER # Mass of fresh water required (kg)
		volume_fresh_water_demand = mass_fresh_water_demand / 997 # Convert mass to volume (m^3), assuming water density = 997 kg/m3
		self.total_volume_of_fresh_water = np.sum(volume_fresh_water_demand)

		# Calculate the volume of seawater required based on recovery rate
		volume_sea_water_demand = volume_fresh_water_demand / self.dcf.inp['Reverse Osmosis']['Recovery Rate']['Value'] #in m3
		self.total_volume_of_sea_water = np.sum(volume_sea_water_demand)

		# Calculate the power demand for reverse osmosis
		osmosis_power_demand = self.dcf.inp['Reverse Osmosis']['Power Demand (kWh/m3)']['Value'] * volume_sea_water_demand / 8766  #kW
		self.total_osmosis_power_demand = np.sum(osmosis_power_demand)

		# Calculate amount of brine during desalination
		mass_brine = mass_fresh_water_demand * 0.035 #factor 0.035: per 1 kg of H2O, 0.035 kg of NaCl/brine are obtained during the desalination process starting from 0.6 M NaCl solution (which is sea water)
		self.total_mass_brine = np.sum(mass_brine)

		# Calculate the O2 produced in electrolysis
		MOLAR_RATIO_O2_H2 = 31.999 / 2.016 # Molar ratio for O2 and H2
		o2_produced = 1/2 * total_h2_produced * MOLAR_RATIO_O2_H2 #in kg, factor 1/2 due to the H2/O2 ratio (2H2O —› 2H2 + O2
		self.total_o2_produced = np.sum(o2_produced)

		return osmosis_power_demand
	
	def calculate_photovoltaic_loss_correction(self, data, year):
		"""
		Adjusts the photovoltaic power generation data for losses due to degradation over the years.
		
		Args:
			data (ndarray): Hourly irradiation data used for calculating power generation.
			year (int): Current operational year for which degradation needs to be applied.

		Returns:
			ndarray: Corrected hourly irradiation data accounting for yearly degradation.
		"""

		return data * (1. - self.dcf.inp['Photovoltaic']['Power loss per year']['Value']) ** year

	def calculate_electrolyzer_power_demand(self, year):
		"""Calculates the increase in electrolyzer power demand over time due to degradation.
		
		Args:
			year (int): The operational year for which the power demand increase is calculated.

		Returns:
			tuple: Electrolyzer power demand in kW and the power increase factor.
		"""

		increase = (1. + self.dcf.inp['Electrolyzer']['Power requirement increase per year']['Value']) ** year
		demand = increase * self.dcf.inp['Electrolyzer']['Nominal Power (kW)']['Value']

		return demand, increase
		
	
	def calculate_stack_replacement(self):
		"""
		Calculates the frequency of electrolyzer stack replacements based on operational time and usage.
		
		This method computes the total running time of the electrolyzer and calculates how often the stack needs replacement.
		The frequency is determined based on the total operational hours and the specified replacement time.

		
		"""
		# Cumulative running time for each year
		cumulative_running_time = np.cumsum(self.yearly_data[:,2])

		# Calculate stack usage based on replacement time
		stack_usage = cumulative_running_time / self.dcf.inp['Electrolyzer']['Replacement time (h)']['Value']
		number_of_replacements = np.floor_divide(stack_usage[-1], 1)

		# Calculate the frequency of stack replacements
		self.production_maintanence_electrolyser = 1 + number_of_replacements
		self.replacement_frequency = len(stack_usage) / (number_of_replacements + 1.)


	def calculate_scaling_factors(self):
		"""
		Calculates the CAPEX scaling factors for both electrolyzer and photovoltaic systems.
		
		This method uses the scaling factor formula based on the nominal and reference power of the systems.
		The multiplier from the input data is applied to calculate the scaling factors for both PV and electrolyzer.
		"""
		# Calculate scaling factors for PV and electrolyzer
		self.pv_scaling_factor = self.scaling_factor(self.dcf.inp['Photovoltaic']['Nominal Power (kW)']['Value'], self.dcf.inp['Photovoltaic']['CAPEX Reference Power (kW)']['Value'])
		self.electrolyzer_scaling_factor = self.scaling_factor(self.dcf.inp['Electrolyzer']['Nominal Power (kW)']['Value'], self.dcf.inp['Electrolyzer']['CAPEX Reference Power (kW)']['Value'])
		
	def scaling_factor(self, power, reference):
		"""Calculates the CAPEX scaling factor for a system based on its nominal power and reference power.
		
		Args:
			power (float): Nominal power of the system.
			reference (float): Reference power used for scaling calculations.

		Returns:
			float: CAPEX scaling factor.
		"""
		# Calculate the number of ten-fold increases
		number_of_tenfold_increases = np.log10(power/reference)

		# Apply the CAPEX multiplier to calculate the scaling factor
		return self.dcf.inp['CAPEX Multiplier']['Multiplier']['Value'] ** number_of_tenfold_increases

	def calculate_area(self):
		"""Calculates the land area required for the photovoltaic (PV) system.
		
		This method calculates the area in square meters (m^2) required for the PV system, assuming peak efficiency of 1000 W/m2 for the solar panels.

		
		"""
		
		peak_kW_per_m2 = self.dcf.inp['Photovoltaic']['Efficiency']['Value'] * 1.
		self.area_m2 = self.dcf.inp['Photovoltaic']['Nominal Power (kW)']['Value'] / peak_kW_per_m2
		self.area_acres = self.area_m2 * 0.000247105 # Convert m^2 to acres

	def calculate_amount_of_PV(self):
		"""Calculates the number of photovoltaic (PV) modules required for the hydrogen production capacity.
		
		Args:
			None

		
		"""
		# Calculate the number of PV modules required based on nominal power and module power
		self.amount_of_PV_modules = np.ceil(self.dcf.inp['Photovoltaic']['Nominal Power (kW)']['Value'] / self.dcf.inp['Photovoltaic']['Power per module (kW)']['Value'])

	def setup_inserts(self, print_info):
		"""Sets up the output inserts for reporting the results of the calculations.
		
		This method prepares the results to be inserted into the output data structure, including plant design capacity, scaling factors, 
		area required, and other important technical parameters for the system. The data is organized into a list of tuples.
		
		Args:
			print_info (bool): Flag to control whether the information should be printed.

		
		"""
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
			('LCA Parameters Photovoltaic', 'Produced electricity PV (kW)', self.total_power_generation),
			('LCA Parameters Photovoltaic', 'Electrolyzer power consumption (kW)', self.total_electrolyzer_power_consumption),
			('LCA Parameters Photovoltaic', 'Electricity stored in battery (kW)', self.total_daily_stored_power),
			('LCA Parameters Photovoltaic', 'Electricity reverse osmosis (kW)', self.total_osmosis_power_demand),
			('LCA Parameters Photovoltaic', 'Electricity from battery (kW)', self.total_additional_power_consumption)
		]

		for category, name, value in inserts:
			insert(self.dcf, category, name, 'Value', value, __name__, print_info=print_info)
	
		insert(self.dcf, 'Planned Replacement', 'Electrolyzer Stack Replacement', 'Frequency (years)', 
				self.replacement_frequency, __name__, print_info = print_info, add_processed = False,
				insert_path = False)
