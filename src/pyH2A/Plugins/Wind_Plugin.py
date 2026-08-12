import numpy as np
from functools import lru_cache
from pyH2A.Utilities.input_modification import file_import
from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Plugins.Hourly_Irradiation_Plugin import converter_function

class Wind_Plugin:
	'''Calculation of hourly wind power generation and needed number of turbines to match a desired nominal power.
	
	Parameters
	----------
    Time > Years > Value : dict
        Dictionary containing plant life time-related quantities
	Hourly Wind > File > Value : str
		Path to a `.csv` file containing hourly wind data as provided by
		https://re.jrc.ec.europa.eu/pvg_tools/en/#TMY.			
	Power Generation > Available energy (hourly) > Value : dict, optional
		Available power, hourly basis, dictionary of years
	Wind Turbine > Installed wind capacity > Value : int or float
		Installed power
	Wind Turbine > Power per wind turbine > Value : int or float
		Nominal power of each turbine			
	Wind Turbine > Power loss per year > Value : int or float
		Reduction in power produced by wind turbine per year due to degradation. Percentage or value > 0. Ageing factor calculated as: (1 - loss per year) ^ year.	

	Returns
	-------
	Power Generation > Wind hourly power generation > Value : dict
		Available energy due to wind power, hourly basis, dictionary of years
	Power Generation > Available energy (hourly) > Value : dict
		Total available power, hourly basis, dictionary of years	
	Wind Turbine > Number of wind turbines > Value : int or float
		Number of wind turbines needed to match the required installed power				
	'''

	def __init__(self, dcf, print_info, run = True):
		self._set_up(dcf)
		if run:
			self._run(dcf)

	def _set_up(self, dcf):

		self.functional_unit = dcf.functional_unit

		self.input_dict = {
			"Time": {
				"Years": {
					"Value": {
						"type": {dict,},
						"bounds": (None, None),
					},
					"Unit": {
						"dimension": "dimensionless",
					},
					"optional": False,
					"description": "Dictionary containing all time-related quantities."
				}, 
			},  	
			"Hourly Wind": {		
				"File": {
					"Value": {	
						"type": {str,},
					},
					"optional": False,
					"description": "Path to a `.csv` file containing hourly wind speed data"
				},	
			},
			"Power Generation": {	
				"Available energy (hourly)": {
					"Value": {
						"type": {dict,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "energy",
					},
					"optional": True, # if we want to run a simulation without any prior PV, Available energy (hourly) will not pre-exist
					"description": "Available energy, hourly basis, dictionary of years."
				},
				"Total yearly power generation": {
					"Value": {
						"type": {np.ndarray,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "energy",
					},
					"optional": True, # same remark as above: we can run wind without PV.
					"description": "Total yearly power generation before wind contribution, e.g.: PV array (array)."
				},				
			},
			"Wind Turbine": {	
				"Installed wind capacity": {
					"Value": {
						"type": {int, float,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "power",
					},
					"optional": False, 
					"description": "Installed power."
				},
				"Power per wind turbine": {
					"Value": {
						"type": {int, float,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "power",
					},
					"optional": False, 
					"description": "Nominal power of each turbine."
				},			
				"Power loss per year": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, 1),
					},
					"Unit": {
						"dimension": "dimensionless",
					},
					"optional": False,
					"description": "Reduction in power produced by wind turbine per year due to degradation. Percentage or value > 0. Ageing factor calculated as: (1 - loss per year) ^ year."
				},			
			},
		}

		self.output_dict = {
			"Power Generation": {
				"Wind hourly power generation": {
					"Value": {
						"inserted_value": "wind_electric_energy_generation_yearly_data",
						"type": {dict,},
						"dimension": "energy",
					},
					"description": "Hourly power generation of wind turbines (dictionary of years).",
					"optional": False,
				},
				"Wind yearly power generation": {
					"Value": {
						"inserted_value": "wind_energy_generation_yearly_array",
						"type": {np.ndarray,},
						"dimension": "energy",
					},
					"description": "Yearly power generation of wind turbines (array).",
					"optional": False,
				},
				"Total yearly power generation": {
					"Value": {
						"inserted_value": "total_energy_generation_yearly_array",
						"type": {np.ndarray,},
						"dimension": "energy",
					},
					"description": "Yearly power generation of all production means (array).",
					"optional": False,
				},	
				"Wind to total production ratio": {
					"Value": {
						"inserted_value": "wind_to_total_production_fraction",
						"type": {float,},
						"dimension": "dimensionless",
					},
					"description": "Total energy production by wind, didvided by the production of PV + wind together.",
					"optional": True,
				},								
				"Available energy (hourly)": {
					"Value": {
						"inserted_value": "total_electric_energy_generation_yearly_data",
						"type": {dict,},
						"dimension": "energy",
					},
					"description": "Available energy, hourly basis, dictionary of years.",
					"optional": False,
				},
			},	
			"Wind Turbine": {
				"Number of wind turbines": {
					"Value": {
						"inserted_value": "number_turbines",
						"type": {int,float},
						"dimension": "dimensionless",
					},
					"optional": False,
					"description": "Number of wind turbines needed to match the required installed power."
				},
			},	
		}


	def _run(self, dcf):

		self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, 'Wind_Plugin')
		self.calculate_turbines_number()

		(self.curtailed_hourly_wind_speed, 
   		self.hourly_density) = calculate_hourly_effective_wind_properties(
			   												self.input_dict_resolved['Hourly Wind']['File']['Value'])

		self.calculate_wind_power_production()

		output_inserter_function(self.output_dict, self, dcf, 'Wind_Plugin') 

	def calculate_turbines_number(self):
		self.number_turbines = Quantity(
										self.input_dict_resolved['Wind Turbine']['Installed wind capacity']['Value'].unit['W']
										/
										self.input_dict_resolved['Wind Turbine']['Power per wind turbine']['Value'].unit['W'], 
								  	'-')

	def calculate_wind_power_production(self):
		'''
		Calculates the hourly energy (power integrated over 1-h slot) delivered by the turbine.
		Wind power is proportional to air density, and to the cube of the (curtailed) wind speed.
		Therefore, the nominal power is reached when (density * velocity**3) is maximum, 
		and the power at any other moment is obtained through a proportionality to (density * velocity**3)
		'''

		# The turbine nominal power is reached when density * curtailed_speed ** 3 is maximum
		reference_production = np.max(self.hourly_density.unit['kg/m3'] * self.curtailed_hourly_wind_speed.unit['m/s']**3) 

		self.wind_electric_energy_generation_yearly_data = {}
		self.total_electric_energy_generation_yearly_data = {}
		wind_energy_generation_yearly_array = []

		for year in self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-']:
			ageing_factor = (1-self.input_dict_resolved['Wind Turbine']['Power loss per year']['Value'].unit['-'])**year
			self.wind_electric_energy_generation_yearly_data[year] = Quantity(
																		ageing_factor
																		*
																		self.input_dict_resolved['Wind Turbine']['Installed wind capacity']['Value'].unit['W']
																		*
																		self.hourly_density.unit['kg/m3'] * self.curtailed_hourly_wind_speed.unit['m/s']**3
																		/
																		reference_production
																		, 
																		'Wh'
																	)
			if 'Power Generation' in self.input_dict_resolved and 'Available energy (hourly)' in self.input_dict_resolved['Power Generation']:
				self.total_electric_energy_generation_yearly_data[year] = Quantity(
																			self.wind_electric_energy_generation_yearly_data[year].unit['J']
																			+
																			self.input_dict_resolved['Power Generation']['Available energy (hourly)']['Value'][year].unit['J']
																			,
																			'J'
																		)
			else: # Wind is used as a standalone, without PV
				self.total_electric_energy_generation_yearly_data[year] = Quantity(
																			self.wind_electric_energy_generation_yearly_data[year].unit['J'],
																			'J'
																		)
			wind_energy_generation_yearly_array.append(self.wind_electric_energy_generation_yearly_data[year].unit['J'].sum())

		self.wind_energy_generation_yearly_array = Quantity(np.array(wind_energy_generation_yearly_array), 'J')

		if 'Power Generation' in self.input_dict_resolved and 'Total yearly power generation' in self.input_dict_resolved['Power Generation']:
			self.total_energy_generation_yearly_array = Quantity(
																self.input_dict_resolved['Power Generation']['Total yearly power generation']['Value'].unit['J']
																+
																self.wind_energy_generation_yearly_array.unit['J'], 
																'J'
															)
			
			self.wind_to_total_production_fraction = Quantity(
																np.sum(self.wind_energy_generation_yearly_array.unit['J'])
																/
																np.sum(self.total_energy_generation_yearly_array.unit['J']),
																'-'
															)
		else: 
			self.total_energy_generation_yearly_array = self.wind_energy_generation_yearly_array

		
@lru_cache(maxsize = None)
def import_hourly_data(file_name):
	'''Imports hourly wind data and location coordinates from the `.csv` format provided 
	by: https://re.jrc.ec.europa.eu/pvg_tools/en/tools.html.
	``@lru_cache`` is used for fast repeated reads
	'''
	file_read = file_import(file_name, mode='r')

	for row_counter, line in enumerate(file_read):

		if line.startswith("time(UTC)"):
			skip_header = row_counter + 1
			break

	file_read.close()

	data = np.genfromtxt(
		file_import(file_name, mode='r'),
		delimiter=',',
		skip_header=skip_header,
		skip_footer=9,
		converters={0: converter_function}
	)

	data_dict = {
		'Time': Quantity(data[:,0], '-'),
		'Temperature': Quantity(data[:,1], 'degC'),
		'Wind Speed': Quantity(data[:,7], 'm/s'),
		'Pressure': Quantity(data[:,9], 'Pa')
}

	return data_dict

@lru_cache(maxsize = None)
def calculate_hourly_effective_wind_properties(file_name):

	data = import_hourly_data(file_name)

	# Wind speed at 100 m (usual altitude for wind turbines sizing) is deduced from the speed at 10 m (available Hourly Wind) according to: 
	# v(100m) = v(10m) * (100 m / 10 m)**alpha with alpha = 0.14 (Wind Energy Handbook, Burton et al, Wiley (2001), section 2.6.2)
	wind_speed_100m = data['Wind Speed'].unit['m/s']*(100/10)**0.14

	# The turbine doesn't start below the cut-in wind speed
	# reaches saturation at the rated wind speed
	# and stops above the cut-out wind speed
	# these values are hardcoded for the moment, we can turn them into inputs in the future if we want to examine the effect of turbine characteristics
	cut_in_wind_speed_m_s = 4 
	rated_wind_speed_m_s = 12 
	cut_out_wind_speed_m_s = 25

	curtailed_speed = np.clip(wind_speed_100m, None, rated_wind_speed_m_s)
	curtailed_speed[(wind_speed_100m < cut_in_wind_speed_m_s) |
					(wind_speed_100m > cut_out_wind_speed_m_s)] = 0.0

	air_density = data['Pressure'].unit['Pa']/(287 * data['Temperature'].unit['K']) # assuming dry air, modelled as an ideal gas of molecular weight 29.97g/mol (specific gas constant = 287 J/kg/K)

	
	return Quantity(curtailed_speed, 'm/s'), Quantity(air_density, 'kg/m3')
