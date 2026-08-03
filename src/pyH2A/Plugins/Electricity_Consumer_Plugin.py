import numpy as np
from functools import lru_cache
from pyH2A.Utilities.input_modification import file_import
from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Plugins.Hourly_Irradiation_Plugin import converter_function

class Electricity_Consumer_Plugin:
	'''Calculation of hourly energy excess and default.
	
	Parameters
	----------
    Time > Years > Value : dict
        Dictionary containing plant life time-related quantities
	Hourly Consumer Profile > File > Value : str
		Path to a `.csv` file containing hourly consumer data.			
	Power Generation > Available energy (hourly) > Value : dict, optional
		Available power, hourly basis, dictionary of years

	Returns
	-------
	Hourly Consumer Profile > Unsatisfied demand > Value : dict
		Energy demand that is not met by the direct supply, dictionary of years
	Power Generation > Available energy (hourly) > Value : dict
		Total available power, hourly basis, dictionary of years				
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
			"Hourly Consumer Profile": {		
				"File": {
					"Value": {	
						"type": {str,},
					},
					"optional": False,
					"description": "Path to a `.csv` file containing hourly power consumption"
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
					"optional": False, 
					"description": "Available energy, hourly basis, dictionary of years."
				},
			},
		}

		self.output_dict = {
			"Hourly Consumer Profile": {		
				"Unsatisfied demand": {
					"Value": {
						"inserted_value": "unsatisfied_demand",
						"type": {dict,},
						"dimension": "energy",
					},
					"description": "Energy demand that is not met by the direct supply, dictionary of years.",
					"optional": False,
				},
			},	
			"Power Generation": {
				"Available energy (hourly)": {
					"Value": {
						"inserted_value": "total_electric_energy_available_yearly_data",
						"type": {dict,},
						"dimension": "energy",
					},
					"description": "Available energy, hourly basis, dictionary of years.",
					"optional": False,
				},
			},	
		}


	def _run(self, dcf):

		self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, 'Electricity_Consumer_Plugin')

		self.consumption_data = import_hourly_data(self.input_dict_resolved['Hourly Consumer Profile']['File']['Value'])

		self.calculate_supply_demand_difference()

		output_inserter_function(self.output_dict, self, dcf, 'Electricity_Consumer_Plugin') 



	def calculate_supply_demand_difference(self):
		'''
		Calculates the excess or default of production on an hourly basis, and attributes the excess | default 
													  to total_electric_energy_available_yearly_data | unsatisfied_demand , respectively
		'''



		self.unsatisfied_demand = {}
		self.total_electric_energy_available_yearly_data = {}

		for year in self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-']:
			energy_excess = (self.input_dict_resolved['Power Generation']['Available energy (hourly)']['Value'][year].unit['J']
							-
							self.consumption_data['Consumption'].unit['J']
							)

			self.total_electric_energy_available_yearly_data[year] = Quantity(np.where(energy_excess>0, energy_excess, 0), 'J')
			self.unsatisfied_demand[year] = Quantity(np.where(energy_excess<=0, -energy_excess, 0), 'J')		
			
	
@lru_cache(maxsize = None)
def import_hourly_data(file_name):
	'''Imports hourly wind data and location coordinates from the `.csv` format.
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
		skip_header=skip_header, skip_footer = 0, 
		converters={0: converter_function}
	)


	data_dict = {
		'Time': Quantity(data[:,0], '-'),
		'Consumption': Quantity(data[:,1], 'MWh'),
}

	return data_dict

