from pyH2A.Utilities.input_modification import read_textfile, hourly_to_daily_power
from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
import numpy as np

class Photovoltaic_Plugin:
	'''Simulation of electricity production using PV.

	Parameters
	----------
    Time > Years > Value : dict
        Dictionary containing plant life time-related quantities	
	Irradiation Used > Data > Value : str or ndarray
		Hourly power ratio data for electricity production calculation. Either a 
		path to a text file containing the data or ndarray. A suitable array 
		can be retrieved from "Hourly Irradiation > *type of tracking* > Value".
	Photovoltaic > Nominal power > Value : float
		Nominal power of PV array.
	Photovoltaic > Power loss per year > Value : float
		Reduction in power produced by PV array per year due to degradation. Percentage or value
		> 0. Reduction calculated as: (1 - loss per year) ^ year.
	Photovoltaic > Efficiency > Value : float
		Power conversion efficiency of used solar cells. Percentage or value between 0 and 1.

	Returns
	-------
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
					"description": "Hourly energy / area data for electricity production calculation. Either a path to a text file containing the data (in this case, it is assumed that data is in kWh/m2 and that relevant data is in column 1) or ndarray. A suitable array can be retrieved from 'Hourly Irradiation > *type of tracking* > Value'."
				},
			},
			"Photovoltaic": {
				"Nominal power": {
					"Value": {	
						"type": {float,int,},
						"bounds": (0, None),
					},
					"Unit": {	
						"dimension": "power",
					},
					"optional": False,
					"description": "Nominal power of PV array."
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
					"description": "Reduction in power produced by PV array per year due to degradation. Percentage or value > 0. Reduction calculated as: (1 - loss per year) ^ year."
				},
				"Efficiency": {
					"Value": {
						"type": {float,int,},
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

		self.output_dict = {
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
				"PV yearly power generation": {
					"Value": {
						"inserted_value": "electric_energy_generation_yearly_array",
						"type": {np.ndarray,},
						"dimension": "energy",
					},
					"description": "Yearly power generation of PV array (array).",
					"optional": False,
				},
				"Total yearly power generation": {
					"Value": {
						"inserted_value": "electric_energy_generation_yearly_array",
						"type": {np.ndarray,},
						"dimension": "energy",
					},
					"description": "Yearly power generation of PV array (array).",
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
						"inserted_value": "electric_energy_generation_yearly_data_daily_energy",
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

	def _run(self, dcf):
		self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, 'Photovoltaic_Plugin')

		self.calculate_power_production()
		self.calculate_area()

		output_inserter_function(self.output_dict, self, dcf, 'Photovoltaic_Plugin') 

	def calculate_power_production(self):
		'''Using hourly irradiation data and PV array parameters,
		power production is calculated.
		'''

		if isinstance(self.input_dict_resolved['Irradiation Used']['Data']['Value'], str):
			data = read_textfile(self.input_dict_resolved['Irradiation Used']['Data']['Value'], delimiter = '	')[:,1]
			data = Quantity(data, 'kWh/m2').unit['J/m2']
		else:
			data = self.input_dict_resolved['Irradiation Used']['Data']['Value'].unit['J/m2']

		yearly_data = {}
		yearly_data_daily_energy = {}
		yearly_energy_generation = []

		for year in self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-']:
			data_loss_corrected = self.calculate_photovoltaic_loss_correction(data, year)

			# Multiplying irradiance data (J/m2) by nominal power in kW 
			# to obtain electrical energy generated in J, since peak irradiance is 1 kW/m2
			# (which is used to define nominal power
			# nominal power is essentially just the 1/m2 multiplier, to convert J/m2 to J
			electric_energy_generation = (data_loss_corrected  
										  * self.input_dict_resolved['Photovoltaic']['Nominal power']['Value'].unit['kW'])

			yearly_data[year] = Quantity(electric_energy_generation, 'J') 
			yearly_data_daily_energy[year] = Quantity(hourly_to_daily_power(electric_energy_generation), 'J')			
			yearly_energy_generation.append(electric_energy_generation.sum())

		self.electric_energy_generation_yearly_data = yearly_data
		self.electric_energy_generation_yearly_data_daily_energy = yearly_data_daily_energy
		self.electric_energy_generation_yearly_array = Quantity(np.array(yearly_energy_generation), 'J')

	def calculate_photovoltaic_loss_correction(self, data, year):
		'''Calculation of yearly reduction in electricity production by PV array.
		'''

		return data * (1. - self.input_dict_resolved['Photovoltaic']['Power loss per year']['Value'].unit['-']) ** year

	def calculate_area(self):
		'''Area requirement calculation assuming 1000 W/m2 peak power.'''

		# Efficiency automatically converts 1 kW/m2 to actual usuable power per m2
		peak_kW_per_m2 = self.input_dict_resolved['Photovoltaic']['Efficiency']['Value'].unit['-']
		
		self.area = Quantity(self.input_dict_resolved['Photovoltaic']['Nominal power']['Value'].unit['kW'] 
							 / peak_kW_per_m2, 
					'm2')