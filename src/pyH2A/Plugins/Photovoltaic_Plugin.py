from pyH2A.Utilities.input_modification import read_textfile, hourly_to_daily_power
from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
import numpy as np

input_dict = {
	"Irradiation Used": {
		"Data": {
			"Value": {
				"type": {str, np.ndarray,},
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": "energy / area",
			},
			"optional": False,
			"description": "Hourly power ratio data for electricity production calculation. Either a path to a text file containing the data or ndarray. A suitable array can be retrieved from 'Hourly Irradiation > *type of tracking* > Value'."
		},
	},
	"CAPEX Multiplier": {
		"Multiplier": {
			"Value": {
				"type": {float,},
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": "dimensionless",
			},
			"optional": False,
			"description": "Multiplier to describe cost reduction of PV CAPEX for every ten-fold increase of power relative to CAPEX reference power. Based on the multiplier the CAPEX scaling factor is calculated as: multiplier ^ (number of ten-fold increases). A value of 1 leads to no CAPEX reduction, a value < 1 enables cost reduction."
		},
	},
	"Electrolyzer": {
		"Nominal power": {
			"Value": {	
				"type": {float,},
				"bounds": (0, None),
			},
			"Unit": {	
				"dimension": "power",
			},
			"optional": True,
			"description": "Nominal power of electrolyzer; can be used to size the PV array."
		},
	},	
	"Photovoltaic": {
		"Nominal power": {
			"Value": {	
				"type": {float,},
				"bounds": (0, None),
			},
			"Unit": {	
				"dimension": "power",
			},
			"optional": False,
			"description": "Nominal power of PV array."
		},
		"CAPEX reference power": {	
			"Value": {
				"type": {float,},
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": "power",
			},
			"optional": False,
			"description": "Reference power of PV array for cost reduction calculations."
		},
		"Power loss per year": {
			"Value": {
				"type": {float,},
				"bounds": (0, 1),
			},
			"Unit": {
				"dimension": "dimensionless",
			},
			"optional": False,
			"description": "Reduction in power produced by PV array per year due to degradation. Percentage or value > 0. Reduction calculated as: (1 - loss per year) ^ year."
		},
		"Efficiency": {
			"Value": {
				"type": {float,},
				"bounds": (0, 1),
			},
			"Unit": {
				"dimension": "dimensionless",
			},
			"optional": False,
			"description": "Power conversion efficiency of used solar cells. Percentage or value between 0 and 1."
		},
	},
}

output_dict = {
    "Photovoltaic": {
		"Scaling factor": {
			"Value": {
       			"inserted_value": "pv_scaling_factor",
				"type": {float,},
				"dimension": "dimensionless",
       		},
            "description": "CAPEX scaling factor for PV array calculated based on CAPEX multiplier, reference and nominal power.",
            "optional": False,
		},
    },
	"Power Generation": {
		"PV hourly power generation": {
			"Value": {
				"inserted_value": "electric_energy_generation_yearly_data",
				"type": {dict,},
				"dimension": "energy",
			},
			"description": "Hourly power generation of PV array (dictionary of years).",
			"optional": False,
		},
		"Available energy (hourly)": {
			"Value": {
				"inserted_value": "electric_energy_generation_yearly_data",
				"type": {dict,},
				"dimension": "energy",
			},
			"description": "Available energy, hourly basis, dictionary of years.",
			"optional": False,
		},
		"Available energy (daily)": {
			"Value": {
				"inserted_value": "electric_energy_generation_yearly_data_daily_power",
				"type": {dict,},
				"dimension": "energy",
			},
			"description": "Available energy, daily basis, dictionary of years.",
			"optional": False,
		},
	},
	"Non-Depreciable Capital Costs": {
		"Land required": {
			"Value": {
				"inserted_value": "area",
				"type": {float,},
				"dimension": "area",
			},
			"description": "Total land required.",
			"optional": False,	
		},
		"Solar collection area": {
			"Value": {
				"inserted_value": "area",
				"type": {float,},
				"dimension": "area",
			},
			"description": "Solar collection area.",
			"optional": False,	
		},
	},
}

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
	Photovoltaic > Nominal power > Value : float
		Nominal power of PV array.
	Photovoltaic > CAPEX reference power > Value : float
		Reference power of PV array for cost reduction calculations.
	Photovoltaic > Power loss per year > Value : float
		Reduction in power produced by PV array per year due to degradation. Percentage or value
		> 0. Reduction calculated as: (1 - loss per year) ^ year.
	Photovoltaic > Efficiency > Value : float
		Power conversion efficiency of used solar cells. Percentage or value between 0 and 1.

	Returns
	-------
	Photovoltaic > Scaling factor > Value : float
		CAPEX scaling factor for PV array calculated based on CAPEX multiplier, 
		reference and nominal power.
	Power Generation > PV hourly power generation > Value : dict
		Hourly power generation of PV array (dictionary of years).
	Power Generation > Available energy (hourly) > Value : dict
		Available power, hourly basis, dictionary of years
    Power Generation > Available energy (daily) > Value : dict
		Available energy, daily basis, dictionary of years .
	Non-Depreciable Capital Costs > Land required > Value : float
		Total land required.
	Non-Depreciable Capital Costs > Solar collection area > Value : float
		Solar collection area.
	'''


	def __init__(self, dcf, print_info):
		self.input_dict_resolved = input_resolver_function(input_dict, dcf, 'Photovoltaic_Plugin')

		self.calculate_power_production(dcf)
		self.calculate_scaling_factors(dcf)
		self.calculate_area(dcf)

		output_inserter_function(output_dict, self, dcf, 'Photovoltaic_Plugin') 

	def calculate_power_production(self, dcf):
		'''Using hourly irradiation data and PV array parameters,
		power production is calculated.
		'''

		if isinstance(self.input_dict_resolved['Irradiation Used']['Data']['Value'], str):
			data = Quantity(read_textfile(self.input_dict_resolved['Irradiation Used']['Data']['Value'], delimiter = '	')[:,1], 'kWh/m2').unit['J/m2']
		else:
			data = self.input_dict_resolved['Irradiation Used']['Data']['Value'].unit['J/m2']

		yearly_data = {}
		yearly_data_daily_power = {}

		for year in dcf.operation_years:
			data_loss_corrected = self.calculate_photovoltaic_loss_correction(data, year)
			electric_energy_generation = data_loss_corrected * self.input_dict_resolved['Photovoltaic']['Nominal power']['Value'].unit['kW']

			yearly_data[year] = Quantity(electric_energy_generation, 'J') 
			yearly_data_daily_power[year] = Quantity(hourly_to_daily_power(electric_energy_generation), 'J')			

		self.electric_energy_generation_yearly_data = yearly_data
		self.electric_energy_generation_yearly_data_daily_power = yearly_data_daily_power

	def calculate_photovoltaic_loss_correction(self, data, year):
		'''Calculation of yearly reduction in electricity production by PV array.
		'''

		return data * (1. - self.input_dict_resolved['Photovoltaic']['Power loss per year']['Value'].unit['-']) ** year

	def calculate_scaling_factors(self, dcf):
		'''Calculation of PV CAPEX scaling factors.
		'''

		self.pv_scaling_factor = Quantity(self.scaling_factor(self.input_dict_resolved['Photovoltaic']['Nominal power']['Value'].unit['W'], self.input_dict_resolved['Photovoltaic']['CAPEX reference power']['Value'].unit['W']), '-')
		
	def scaling_factor(self, power, reference):
		'''Calculation of CAPEX scaling factor based on nominal and reference power.
		'''
		
		number_of_tenfold_increases = np.log10(power/reference)

		return self.input_dict_resolved['CAPEX Multiplier']['Multiplier']['Value'].unit['-'] ** number_of_tenfold_increases

	def calculate_area(self, dcf):
		'''Area requirement calculation assuming 1000 W/m2 peak power.'''

		peak_kW_per_m2 = self.input_dict_resolved['Photovoltaic']['Efficiency']['Value'].unit['-'] * 1.
		self.area = Quantity(self.input_dict_resolved['Photovoltaic']['Nominal power']['Value'].unit['kW'] / peak_kW_per_m2, 'm2')