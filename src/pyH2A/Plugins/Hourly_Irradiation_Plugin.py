import numpy as np
from functools import lru_cache
from pyH2A.Utilities.input_modification import read_textfile, file_import
from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity

input_dict = {
	"Hourly Irradiation": {		
		"File": {
			"Value": {	
				"type": {str,},
			},
			"optional": False,
			"description": "Path to a `.csv` file containing hourly irradiance data"
		},
	},
	"Irradiance Area Parameters": {	
		"Module tilt": {
			"Value": {
				"type": {float,},
				"bounds": (0, np.pi / 2),
			},
			"Unit": {
				"dimension": "angle",
			},
			"optional": True, # we always need a tilt, but it's optional as an explicit input because it defaults to the latitude
			"description": "Tilt of irradiated module."
		},
		"Array azimuth": {
			"Value": {
				"type": {float,},
				"bounds": (0, np.pi),
			},
			"Unit": {
				"dimension": "angle",
			},
			"optional": False,
			"description": "Azimuth angle of irradiated module."
		},
		"Nominal operating temperature": {
			"Value": {
				"type": {float,},
				"bounds": (250, 500),
			},
			"Unit": {
				"dimension": "absolute_temperature",
			},
			"optional": False,
			"description": "Nominal operating temperature of irradiated module."
		},
		"Mismatch derating": {
			"Value": {
				"type": {float,},
				"bounds": (0, 1), 
			},
			"Unit": {
				"dimension": "dimensionless",
			},
			"optional": False,
			"description": "Derating value due to mismatch (percentage or value between 0 and 1)."
		},
		"Dirt derating": {
			"Value": {
				"type": {float,},
				"bounds": (0, 1), 
			},
			"Unit": {
				"dimension": "dimensionless",
			},
			"optional": False,
			"description": "Derating value due to dirt buildup (percentage or value between 0 and 1)."
		},
		"Temperature coefficient": {
			"Value": {
				"type": {float,},
				"bounds": (-0.1, 0), 
			},
			"Unit": {
				"dimension": "dimensionless/temperature_diff",
			},
			"optional": False,
			"description": "Performance decrease of irradiated module per degree increase."
		},
	},
}

output_dict = {
	"Hourly Irradiation": {
		"No tracking": {
			"Value": {
				"inserted_value": "power",
				"type": {np.ndarray,},
				"dimension": "power / area",
			},
			"optional": False,
			"description": "Hourly irradiation with no tracking per m2."
		},
		"Horizontal single axis tracking": {
			"Value": {
				"inserted_value": "power_sat",
				"type": {np.ndarray,},
				"dimension": "power / area",
			},
			"optional": False,
			"description": "Hourly irradiation with single axis tracking per m2."
		},
		"Two axis tracking": {
			"Value": {
				"inserted_value": "power_dat",
				"type": {np.ndarray,},
				"dimension": "power / area",
			},
			"optional": False,
			"description": "Hourly irradiation with two axis tracking per m2."
		},
		"Mean solar input no tracking": {
			"Value": {
				"inserted_value": "yearly_averaged_power",
				"type": {float,},
				"dimension": "power / area",
			},
			"optional": False,
			"description": "Mean solar input with no tracking."
		},
		"Mean solar input single axis tracking": {
			"Value": {
				"inserted_value": "yearly_averaged_power_sat",
				"type": {float,},
				"dimension": "power / area",
			},
			"optional": False,
			"description": "Mean solar input with single axis tracking."
		},
		"Mean solar input two axis tracking": {
			"Value": {
				"inserted_value": "yearly_averaged_power_dat",
				"type": {float,},
				"dimension": "power / area",
			},
			"optional": False,
			"description": "Mean solar input with two axis tracking."
		},
	},
}

class Hourly_Irradiation_Plugin:
	'''Calculation of hourly and mean daily irradiation data with different module configurations.
	
	Parameters
	----------
	Hourly Irradiation > File > Value : str
		Path to a `.csv` file containing hourly irradiance data as provided by
		https://re.jrc.ec.europa.eu/pvg_tools/en/#TMY.
	Irradiance Area Parameters > Module tilt > Value : float, optional
		Tilt angle of irradiated module. Defaults to the absolute value of the latitude.
	Irradiance Area Parameters > Array azimuth > Value : float
		Azimuth angle of irradiated module.
	Irradiance Area Parameters > Nominal operating temperature > Value : float
		Nominal operating temperature of irradiated module.
	Irradiance Area Parameters > Mismatch derating > Value : float
		Derating value due to mismatch (dimensionless value between 0 and 1).
	Irradiance Area Parameters > Dirt derating > Value : float
		Derating value due to dirt buildup (dimensionless value between 0 and 1).
	Irradiance Area Parameters > Temperature coefficient > Value : float
		Performance decrease of irradiated module per temperature unit increase.

	Returns
	-------
	Hourly Irradiation > No tracking > Value : ndarray
		Hourly irradiation poer with no tracking per area.
	Hourly Irradiation > Horizontal single axis tracking > Value : ndarray
		Hourly irradiation power with single axis tracking per area.
	Hourly Irradiation > Two axis tracking > Value : ndarray
		Hourly irradiation power with two axis tracking per area.
	Hourly Irradiation > Mean solar input > Value : float
		Mean solar input power with no tracking in per area.
	Hourly Irradiation > Mean solar input, single axis tracking > Value : float
		Mean solar input power with single axis tracking per area.
	Hourly Irradiation > Mean solar input, two axis tracking > Value : float
		Mean solar input power with two axis tracking per area.
	'''

	def __init__(self, dcf, print_info):

		self.input_dict_resolved = input_resolver_function(input_dict, dcf, 'Hourly_Irradiation_Plugin')

		pv = self.input_dict_resolved['Irradiance Area Parameters']
		if 'Module tilt' in pv:
			tilt = pv['Module tilt']['Value']
		else: # if we want to make the tilt equal to latitude, we don't point it through a path in the input fiale, we let it be the default
			tilt = 'Default' 

		self.power, self.power_sat, self.power_dat, self.yearly_averaged_power, self.yearly_averaged_power_sat, self.yearly_averaged_power_dat = calculate_PV_power_ratio(dcf.inp['Hourly Irradiation']['File']['Value'],
											tilt, pv['Array azimuth']['Value'],
											pv['Nominal operating temperature']['Value'], 
											pv['Temperature coefficient']['Value'],
											pv['Mismatch derating']['Value'], pv['Dirt derating']['Value'])

		output_inserter_function(output_dict, self, dcf, 'Hourly_Irradiation_Plugin') 

def converter_function(string):
	'''Converter function for datetime of hourly irradiation data.'''

	#decoded = string.decode('utf-8')
	split = string.split(':')

	return float(split[1][:2]) #- 0.5

def import_Chang_data(file_name):
	'''Import of Chang 2020 data, for debugging.'''

	file_name = 'pyH2A.Lookup_Tables.Hourly_Irradiation_Data~Hourly_Irradiation_Data_Townsville_Chang_2020.csv'

	data = read_textfile(file_name, delimiter = '	')

	data_dict = {'Time': Quantity(data[:,0] - 10., '-'), 'Temperature': Quantity(data[:,1], 'degC'),
				  'Direct Normal Irradiance': Quantity(data[:,2], 'W/m2'), 'Diffuse Horizontal Irradiance': Quantity(data[:,3], 'W/m2')}

	location = {'Latitude (decimal degrees)': -19.25, 'Longitude (decimal degrees)': 146.77}

	return data_dict, location
	
@lru_cache(maxsize = None)
def import_hourly_data(file_name):
	'''Imports hourly irradiation data and location coordinates from the `.csv` format provided 
	by: https://re.jrc.ec.europa.eu/pvg_tools/en/#TMY.
	``@lru_cache`` is used for fast repeated reads
	'''

	data = np.genfromtxt(file_import(file_name, mode = 'r'), 
						  delimiter = ',', skip_header = 17, 
						  skip_footer = 9, converters = {0: converter_function})

	strings = ['Latitude (decimal degrees)', 'Longitude (decimal degrees)']
	location = {}

	file_read = file_import(file_name, mode = 'r')
	for row_counter, line in enumerate(file_read):

		split = line.split(':')

		if split[0] in strings:
			location[split[0]] = float(split[1].strip(' '))
		else:
			break
	file_read.close()

	data_dict = {'Time': Quantity(data[:,0], '-'), 'Temperature': Quantity(data[:,1], 'degC'), 'Global Horizontal Irradiance':  Quantity(data[:,3], 'W/m2'),
				 'Direct Normal Irradiance': Quantity(data[:,4], 'W/m2'), 'Diffuse Horizontal Irradiance': Quantity(data[:,5], 'W/m2')}

	return data_dict, location

@lru_cache(maxsize = None)
def calculate_PV_power_ratio(file_name, module_tilt, array_azimuth, nominal_operating_temperature,
							 temperature_coefficient, mismatch_derating, dirt_derating):
	'''Calculation based on Chang 2020, https://doi.org/10.1016/j.xcrp.2020.100209
	SAT: horzontal single axis tracking
	DAT: dual axis tracking, no diffuse radiation
	'''

	data, location = import_hourly_data(file_name)
	#data, location = import_Chang_data(file_name)

	# all the arguments, except the file_name, are Quantity objects
	# all the angles below are Quantity objects, without the need to be 'self.'

	latitude = Quantity(location['Latitude (decimal degrees)'], 'deg')
	longitude = Quantity(location['Longitude (decimal degrees)'], 'deg')

	if module_tilt == 'Default':
		module_tilt = Quantity(np.abs(location['Latitude (decimal degrees)']), 'deg')

	day_number = np.arange(1, len(data['Time'].unit['-']) + 1) / 24
	#day_number = np.arange(0, len(data['Time'])) / 24

	declination_angle = Quantity(23.45 * np.sin((day_number - 81) * 2 * np.pi / 365.),'deg')
	hour_angle = Quantity((data['Time'].unit['-'] - 12) * 15 + longitude.unit['deg'], 'deg')

	altitude_angle = Quantity(
					np.arcsin(np.sin(declination_angle.unit['rad']) * 
					np.sin(latitude.unit['rad']) + np.cos(declination_angle.unit['rad']) * 
					np.cos(latitude.unit['rad']) * np.cos(hour_angle.unit['rad'])), 
					'rad')

	azimuth_angle = Quantity(
					np.arccos((np.sin(declination_angle.unit['rad']) * 
					np.cos(latitude.unit['rad']) - np.cos(declination_angle.unit['rad']) * 
					np.sin(latitude.unit['rad']) * np.cos(hour_angle.unit['rad'])) / 
					np.cos(altitude_angle.unit['rad'])) * np.sign(hour_angle.unit['rad']), 
					'rad')

	dni_fraction = np.cos(altitude_angle.unit['rad']) * np.sin(module_tilt.unit['rad']) * np.cos(array_azimuth.unit['rad'] - azimuth_angle.unit['rad']) + np.sin(altitude_angle.unit['rad']) * np.cos(module_tilt.unit['rad'])
	
	dni_fraction = dni_fraction.clip(min = 0)

	direct_plane_radiation = data['Direct Normal Irradiance'].unit['W/m2'] * dni_fraction
	diffuse_plane_radiation = data['Diffuse Horizontal Irradiance'].unit['W/m2'] * (180 - module_tilt.unit['deg']) / 180
	total_plane_radiation = direct_plane_radiation + diffuse_plane_radiation

	cell_temperature = data['Temperature'].unit['degC'] + (nominal_operating_temperature.unit['degC'] - 
					   20) * total_plane_radiation/800  

	temperature_derating = 1 + temperature_coefficient.unit['-/delta_degC'] * (cell_temperature - 25)  

	power = Quantity((temperature_derating * mismatch_derating.unit['-'] * 
					 dirt_derating.unit['-'] * total_plane_radiation), 'W/m2')

	sat_azimuth = Quantity(np.sign(azimuth_angle.unit['rad']) * np.pi/2, 'rad')

	sat_tilt = Quantity(np.arctan(1 / np.tan(altitude_angle.unit['rad']) * 
			   np.cos(sat_azimuth.unit['rad'] - azimuth_angle.unit['rad'])), 
			   'rad')

	sat_fraction = (np.cos(altitude_angle.unit['rad']) * np.sin(sat_tilt.unit['rad']) * 
					np.cos(sat_azimuth.unit['rad'] - azimuth_angle.unit['rad']) + np.sin(altitude_angle.unit['rad']) * 
					np.cos(sat_tilt.unit['rad']))
	sat_fraction = sat_fraction.clip(min = 0)

	sat_direct_POA = sat_fraction * data['Direct Normal Irradiance'].unit['W/m2']
	sat_diffuse_POA = data['Diffuse Horizontal Irradiance'].unit['W/m2'] * (180 - sat_tilt.unit['deg']) / 180
	sat_total_POA = sat_direct_POA + sat_diffuse_POA

	power_sat = Quantity(temperature_derating * mismatch_derating.unit['-'] * dirt_derating.unit['-'] * sat_total_POA, 'W/m2')

	power_dat = Quantity(data['Direct Normal Irradiance'].unit['W/m2'] * temperature_derating * mismatch_derating.unit['-'] * dirt_derating.unit['-'], 'W/m2')

	yearly_averaged_power = Quantity(np.sum(power.unit['W/m2'])/(365*24), 'W/m2') 
	yearly_averaged_power_sat = Quantity(np.sum(power_sat.unit['W/m2'])/(365*24), 'W/m2')
	yearly_averaged_power_dat = Quantity(np.sum(power_dat.unit['W/m2'])/(365*24), 'W/m2')

	return power, power_sat, power_dat, yearly_averaged_power, yearly_averaged_power_sat, yearly_averaged_power_dat

