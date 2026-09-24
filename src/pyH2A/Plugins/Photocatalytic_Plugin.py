import numpy as np
import math
from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.input_modification import smoothened_production
from pyH2A.Utilities.Physical_Properties.Physical_properties import Physical_properties as PP
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from numba import njit
import matplotlib.pyplot as plt

class Photocatalytic_Plugin:
	'''Simulating H2 production using photocatalytic water splitting in plastic baggie reactors.

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
			"Technical Operating Parameters and Specifications": {
				"Design output by year": {
					"Value": {
						"type": {np.ndarray},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "mass",
					},
					"optional": False,
					"description": "Yearly output, ignoring the capacity factor."
				},				
			},
			"Reactor Baggies": {
				"Cost material top": {
					"Value": {
						"type": {int,float},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "currency / area",
					},
					"optional": False,
					"description": "Cost of baggie top material in currency / area."
				},
				"Cost material bottom": {
					"Value": {
						"type": {int,float},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "currency / area",
					},
					"optional": False,
					"description": "Cost of baggie bottom material in currency / area."
				},
				"Number of ports per baggie": {
					"Value": {
						"type": {int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "dimensionless",
					},
					"optional": False,
					"description": "Number of ports per baggie."
				},
				"Cost of port": {
					"Value": {
						"type": {int,float,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "currency",
					},
					"optional": False,
					"description": "Cost of a port."
				},		
				"Other costs per baggie": {
					"Value": {
						"type": {int,float,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "currency",
					},
					"optional": False,
					"description": "Other costs per baggie."
				},
				"Markup factor": {
					"Value": {
						"type": {int,float,},
						"bounds": (1, None),
					},
					"Unit": {
						"dimension": "dimensionless",
					},
					"optional": False,
					"description": "Markup factor for baggies, typically > 1."
				},
				"Length": {
					"Value": {
						"type": {int,float,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "length",
					},
					"optional": False,
					"description": "Length of single baggie."
				},
				"Width": {
					"Value": {
						"type": {int,float,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "length",
					},
					"optional": False,
					"description": "Width of single baggie."
				},
				"Filling height": {
					"Value": {
						"type": {int,float,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "length",
					},
					"optional": False,
					"description": "Height of reactor baggie. In this simulation this value determines the height of the water level and hence is an important parameter ultimately determining the level of light absorption and total catalyst amount."
				},
				"Additional land area": {
					"Value": {
						"type": {int,float,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "dimensionless",
					},
					"optional": False,
					"description": "Additional land area required, percentage or value > 0. Calculated as: (1 + addtional land area) * baggie area."
				},
				"Lifetime": {
					"Value": {
						"type": {int,float,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "time",
					},
					"optional": False,
					"description": "Lifetime of reactor baggies before replacement is required."
				},
			},
			"Catalyst": {
				"Cost per unit of mass": {
					"Value": {
						"type": {int,float,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "currency / mass",
					},
					"optional": False,
					"description": "Cost of catalyst per unit of mass."
				},
				"Concentration": {
					"Value": {
						"type": {int,float,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "mass / volume",
					},
					"optional": False,
					"description": "Concentration of catalyst."
				},
				"Lifetime": {
					"Value": {
						"type": {int,float,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "time",
					},
					"optional": False,
					"description": "Lifetime of catalysts before replacement is required."
				},
				"Molar weight": {
					"Value": {
						"type": {int,float,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "mass / substance",
					},
					"optional": True,
					"description": "If the molar weight of the catalyst is specified, homogeneous catalyst properties (TON, TOF etc. are calculated)."
				},
				"Molar attenuation coefficient": {
					"Value": {
						"type": {int,float,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "volume / (length * substance)",
					},
					"optional": True,
					"description": "If the molar attenuation coefficient is specified (along with the molar weight), absorbance and the fraction of absorbed light are also calculated."
				},
			},
			"Solar-to-Hydrogen Efficiency": {
				"STH": {
					"Value": {
						"type": {int, float,},
						"bounds": (0, 1),
					},
					"Unit": {
						"dimension": "dimensionless",
					},
					"optional": False,
					"description": "Solar-to-hydrogen efficiency in percentage or as a value between 0 and 1."
				},
			},
		 	"Solar Input": {
				"Hourly": {
					"Value": {
						"type": {np.ndarray,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "energy / area",
					},
					"optional": False,
					"description": "Hourly irradiation data."
				},
			},	
			"Meteorological Conditions": {
				"Temperature": {
					"Value": {
						"type": {np.ndarray},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "absolute_temperature",
					},
					"optional": False,
					"description": "Ambiant temperature, on an hourly basis."
				},	
				"Wind speed": {
					"Value": {
						"type": {np.ndarray},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "length/time",
					},
					"optional": False,
					"description": "Wind speed at 1 m above ground, on an hourly basis."
				},								
			},			
		}

		self.output_dict = {
			"Non-Depreciable Capital Costs": {
				"Land required": {
					"Value": {
						"inserted_value": "total_land_area",
						"type": {int, float,},
						"dimension": "area",
					},
					"optional": False,
					"description": "Total land area required."
				},
				"Solar collection area": {
					"Value": {
						"inserted_value": "total_solar_collection_area",
						"type": {int,float,},
						"dimension": "area",
					},
					"optional": False,
					"description": "Solar collection area"
				},
			},
			"Planned Replacement": {
				"Planned replacement catalyst": {
					"Cost_Value": {
						"inserted_value": "catalyst_cost",
						"type": {int, float,},
						"dimension": "currency",
					},
					"Frequency_Value": {
						"inserted_value": "catalyst_lifetime",
						"type": {int,float,},
						"dimension": "time",
					},
					"optional": False,
					"description": "Total cost of completely replacing the catalyst once and replacement frequency in years, identical to catalyst lifetime."
				},
				"Planned Replacement Baggie": {
					"Cost_Value": {
						"inserted_value": "baggies_cost",
						"type": {int, float,},
						"dimension": "currency",
					},
					"Frequency_Value": {
						"inserted_value": "baggie_lifetime",
						"type": {int,float,},
						"dimension": "time",
					},
					"optional": False,
					"description": "Total cost of replacing all  baggies and replacement frequency in year, identical to baggie lifetime."
				},
			},
			"Direct Capital Costs - Reactor Baggies": {
				"Baggie cost": {
					"Value": {
						"inserted_value": "baggies_cost",
						"type": {int, float,},
						"dimension": "currency",
					},
					"optional": False,
					"description": "Total baggie cost."
				},
			},
		 	"Direct Capital Costs - Photocatalyst": {
				"Catalyst cost": {
					"Value": {
						"inserted_value": "catalyst_cost",
						"type": {int, float,},
						"dimension": "currency",
					},
					"optional": False,
					"description": "Total catalyst cost."
				},
			},
			"Reactor Baggies": {
				"Number": {
					"Value": {
						"inserted_value": "baggie_number",
						"type": {int,float}, # should only be an int, but going throught the output inserter makes it a float despite the use of the .astype(int)
						"dimension": "dimensionless",
					},
					"optional": False,
					"description": "Number of individual baggies required for design H2 production capacity."
				},
			},
			"Water Volume": {
				"Volume": {
					"Value": {
						"inserted_value": "total_volume",
						"type": {int,float,},
						"dimension": "volume",
					},
					"optional": False,
					"description": "Total water volume"
				},
			},
			"Main Stream": {
				"Temperature": {
					"Value": {
						"inserted_value": "outlet_temperature",
						"type": {float,},
						"dimension": "absolute_temperature",
					},
					"optional": False,
					"description": "Mixture outlet temperature."
				},
				"Pressure": {
					"Value": {
						"inserted_value": "outlet_pressure",
						"type": {float,},
						"dimension": "pressure",
					},
					"optional": False,
					"description": "Mixture outlet pressure."
				},
				"Specific enthalpy": {
					"Value": {
						"inserted_value": "outlet_enthalpy",
						"type": {float,},
						"dimension": "energy/mass",
					},
					"optional": False,
					"description": "Mixture outlet specific enthalpy."
				},  
				"Mass fraction": {
					"Value": {
						"inserted_value": "outlet_mass_fraction",
						"type": {dict,},
						"dimension": "dimensionless",
					},
					"optional": False,
					"description": "Mixture outlet mass fraction."
				},   
				"Mass flow (hourly)": {
					"Value": {
						"inserted_value": "hourly_mass_flow",
						"type": {dict,},
						"dimension": "mass",
					},
					"optional": False,
					"description": "Mixture outlet mass flow, dictionary of years whose items are hourly arrays."
				},  			
				"Design mass flow by year": {
					"Value": {
						"inserted_value": "yearly_mass_flow",
						"type": {np.ndarray,},
						"dimension": "mass",
					},
					"optional": False,
					"description": "Mixture outlet mass per year, excluding downtime (array of years)."
				},  
				"Peak mass flowrate": {
					"Value": {
						"inserted_value": "peak_mass_flowrate",
						"type": {float,},
						"dimension": "mass/time",
					},
					"optional": False,
					"description": "Mixture outlet mass flowrate on peak production day."
				},   			 					                
			},			
		}

	def _run(self, dcf):
		self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, 'Photocatalytic_Plugin')
		
		self.H2_molecule_energy = Quantity(2*1.229, 'eV/entity')
		self.H2_molecular_weight = Quantity(2, 'g/mol')
		
		self.catalyst_lifetime = self.input_dict_resolved['Catalyst']['Lifetime']['Value']
		self.baggie_lifetime = self.input_dict_resolved['Reactor Baggies']['Lifetime']['Value']

		reactor_hourly_temperature_K = energy_balance(
											rho_kg_m3 = 1000, # water density
											thickness_m = self.input_dict_resolved['Reactor Baggies']['Filling height']['Value'].unit['m'], # only the slurry is assumed to have thermal inertia
											Cp_J_kg_K = 4.2e3, # slurry Cp. Could later come from water + catalyst mixture actual properties. 
											Irrad_in_W_m2 = self.input_dict_resolved['Solar Input']['Hourly']['Value'].unit['Wh/m2'],											
											eta_irrad = 0.6, # assumed: 60% of incident irradiation is absorbed and heats up the slurry
											lambda_soil_W_m_K = 1, # assumed
											Cp_soil_J_kg_K = 1200, # assumed
											rho_soil_kg_m3 = 1700, # assumed											
											epsilon = 0.9, # black body emissivity coefficient, assumed
											sigma_W_m2_K4 = 5.67e-8, # Stefan-Boltzmann constant
											T_air_K = self.input_dict_resolved['Meteorological Conditions']['Temperature']['Value'].unit['K'],
											wind_speed_m_s = self.input_dict_resolved['Meteorological Conditions']['Wind speed']['Value'].unit['m/s']
											)
	
		self.reactor_hourly_temperature = Quantity(reactor_hourly_temperature_K, 'K')
		plt.plot(self.reactor_hourly_temperature.unit['degC'] - self.input_dict_resolved['Meteorological Conditions']['Temperature']['Value'].unit['degC'])
		plt.show()					
		print('max temperature °C ', np.max(self.reactor_hourly_temperature.unit['degC']))
		abs_diff = np.abs(self.reactor_hourly_temperature.unit['degC'] - self.input_dict_resolved['Meteorological Conditions']['Temperature']['Value'].unit['degC'])
		#print('min temperature difference °C ', np.min(abs_diff))
		print('max temperature difference °C ', np.max(abs_diff))
	

		self.hydrogen_production()
		self.baggie_cost()
		self.catalyst_cost()
		self.land_area()
		self.catalyst_activity()
		self.outlet_flow_properties()

		
		output_inserter_function(self.output_dict, self, dcf, 'Photocatalytic_Plugin') 

	def hydrogen_production(self):
		'''Calculation of hydrogen produced per hour and per year, per baggie (in kg).
		'''
		hourly_mol_H2_per_m2 = (self.input_dict_resolved['Solar Input']['Hourly']['Value'].unit['Wh/m2']
								* self.input_dict_resolved['Solar-to-Hydrogen Efficiency']['STH']['Value'].unit['-'] 
								/ self.H2_molecule_energy.unit['Wh/mol'])

		self.hourly_H2_mass_production_per_surface = Quantity(hourly_mol_H2_per_m2 * self.H2_molecular_weight.unit['kg/mol'], 'kg/m2')

		self.mean_mol_rate_H2_per_surface = Quantity(np.sum(hourly_mol_H2_per_m2), 'mol/year/m2')		
		self.mean_H2_mass_production_rate_per_surface = Quantity(self.mean_mol_rate_H2_per_surface.unit['mol/year/m2'] * self.H2_molecular_weight.unit['kg/mol'], 'kg/year/m2')

		baggie = self.input_dict_resolved['Reactor Baggies']

		self.baggie_area = Quantity(baggie['Length']['Value'].unit['m'] * baggie['Width']['Value'].unit['m'], 'm2')

		self.yearly_averaged_mass_rate_H2_per_baggie = Quantity(self.mean_H2_mass_production_rate_per_surface.unit['kg/year/m2']
														  *
														  self.baggie_area.unit['m2'], 
														  'kg/year')

		self.peak_mol_rate_H2_per_surface = Quantity(np.amax(hourly_mol_H2_per_m2), 'mol/h/m2')


	def catalyst_activity(self):
		'''Calculation of detailed catalyst properties based on provided parameters. If "Molar Weight (g/mol)"
		is specified in "Catalyst" table properties of a homogeneous catalyst are also calculated. Furthermore,
		if "Molar Attenuation Coefficient (M^-1 cm^-1)" is also provided, the light absorption properties 
		are calculated.
		'''

		catalyst_properties = {}

		kg_catalyst_per_m2 = (self.input_dict_resolved['Reactor Baggies']['Filling height']['Value'].unit['m']
							  * self.input_dict_resolved['Catalyst']['Concentration']['Value'].unit['kg/m3'])

		self.activity_H2_rate_per_catalyst_mass = Quantity(self.peak_mol_rate_H2_per_surface.unit['mol/h/m2'] / kg_catalyst_per_m2, 'mol/h/kg')

		catalyst_properties['Peak activity'] = self.activity_H2_rate_per_catalyst_mass
		catalyst_properties['Peak H2 production'] = self.peak_mol_rate_H2_per_surface
		catalyst_properties['Catalyst Concentration (mass / area)'] = Quantity(kg_catalyst_per_m2, 'kg/m2')
		catalyst_properties['Catalyst Concentration (mass / volume)'] = self.input_dict_resolved['Catalyst']['Concentration']['Value']
	
		if 'Molar Weight' in self.input_dict_resolved['Catalyst']:

			catalyst_mol_per_L = (self.input_dict_resolved['Catalyst']['Concentration']['Value'].unit['g/liter'] 
								  / self.input_dict_resolved['Catalyst']['Molar Weight']['Value'].unit['g/mol'])

			liter_per_m2 = self.input_dict_resolved['Reactor Baggies']['Filling height']['Value'].unit['mm']

			mol_catalyst_per_m2 = liter_per_m2 * catalyst_mol_per_L

			peak_TOF_hourly = self.peak_mol_rate_H2_per_surface['mol/h/m2'] / mol_catalyst_per_m2
			average_TOF_daily = self.mean_mol_rate_H2_per_surface.unit['mol/day/m2'] / mol_catalyst_per_m2
			TON = average_TOF_daily * self.input_dict_resolved['Catalyst']['Lifetime']['Value'].unit['day']

			catalyst_properties['Homogeneous'] = {}
			catalyst_properties['Homogeneous']['Molar catalyst concentration per volume'] = Quantity(catalyst_mol_per_L, 'mol/liter')
			catalyst_properties['Homogeneous']['Molar catalyst Concentration per area'] = Quantity(mol_catalyst_per_m2, 'mol/m2')
			catalyst_properties['Homogeneous']['Peak TOF'] = Quantity(peak_TOF_hourly, '1/h')
			catalyst_properties['Homogeneous']['Mean daily TOF'] = Quantity(average_TOF_daily, '1/day')
			catalyst_properties['Homogeneous']['TON'] = Quantity(TON, '-')

			if 'Molar Attenuation Coefficient' in self.input_dict_resolved['Catalyst']:
				absorbance = (catalyst_mol_per_L 
							  * self.input_dict_resolved['Reactor Baggies']['Filling height']['Value'].unit['cm'] 
							  * self.input_dict_resolved['Catalyst']['Molar Attenuation Coefficient']['Value'].unit['liter/cm/mol'])

				catalyst_properties['Homogeneous']['Absorbance'] = Quantity(absorbance, '-')
				catalyst_properties['Homogeneous']['Absorbed light'] = Quantity(1 - 10**(-absorbance), '-')

			kg_H2_per_day_TOF_calculation = (self.catalyst_amount.unit['kg'] 
											 / self.input_dict_resolved['Catalyst']['Molar weight']['Value'].unit['kg/mol'] 
											 * average_TOF_daily * self.H2_molecular_weight.unit['kg/mol'])
			
			kg_H2_per_day_baggie_calculation = self.yearly_averaged_mass_rate_H2_per_baggie.unit['kg/day'] * self.baggie_number

			assert abs(kg_H2_per_day_TOF_calculation - kg_H2_per_day_baggie_calculation) < 1e-6, 'Difference between baggie and TOF calculation for daily H2 production: TOF: {0}, Baggie: {0}.'.format(kg_H2_per_day_TOF_calculation, kg_H2_per_day_baggie_calculation)

		self.catalyst_properties = catalyst_properties

	def baggie_cost(self):
		'''Calculation of cost per baggie, number of required baggies and total baggie cost.
		'''

		baggie = self.input_dict_resolved['Reactor Baggies']

		material_cost = (self.baggie_area.unit['m2'] 
						 * (baggie['Cost material top']['Value'].unit['USD/m2'] 
							+ baggie['Cost material bottom']['Value'].unit['USD/m2']))
		
		port_cost = (baggie['Number of ports per baggie']['Value'].unit['-'] 
					 * baggie['Cost of port']['Value'].unit['USD'])

		cost_per_baggie = (baggie['Markup factor']['Value'].unit['-'] 
						   * (material_cost + port_cost + baggie['Other costs per baggie']['Value'].unit['USD']))

		baggie_number = (self.input_dict_resolved['Technical Operating Parameters and Specifications']['Design output by year']['Value'].unit['kg'][0]  
						 / self.yearly_averaged_mass_rate_H2_per_baggie.unit['kg/year'])
		baggie_number_rounded_up = np.ceil(baggie_number).astype(int)
		
		self.baggie_number = Quantity(baggie_number_rounded_up, '-')
		self.baggies_cost = Quantity(self.baggie_number.unit['-'] * cost_per_baggie, 'USD')

	def catalyst_cost(self):
		'''Calculation of individual baggie volume, catalyst amount per baggie, total catalyst amount 
		and total catalyst cost.
		'''

		baggie = self.input_dict_resolved['Reactor Baggies']

		baggie_volume = (baggie['Length']['Value'].unit['m'] 
						 * baggie['Width']['Value'].unit['m']
						 * baggie['Filling height']['Value'].unit['m'])

		self.total_volume = Quantity(baggie_volume 
									 * self.baggie_number.unit['-'], 
									 'm3')
		
		self.catalyst_amount_per_baggie = Quantity(baggie_volume 
												   * self.input_dict_resolved['Catalyst']['Concentration']['Value'].unit['kg/m3'], 
												   'kg')
		
		self.catalyst_amount = Quantity(self.catalyst_amount_per_baggie.unit['kg'] 
										* self.baggie_number.unit['-'], 
										'kg')
		
		self.catalyst_cost = Quantity(self.catalyst_amount.unit['kg'] 
									  * self.input_dict_resolved['Catalyst']['Cost per unit of mass']['Value'].unit['USD/kg'], 
									  'USD')

	def land_area(self):
		'''Calculation of total required land area and solar collection area.
		'''

		baggie_land_area = self.baggie_number.unit['-'] * self.baggie_area.unit['m2']
		
		self.total_solar_collection_area = Quantity(baggie_land_area, 'm2')
		self.total_land_area = Quantity(baggie_land_area * 
										(1. + self.input_dict_resolved['Reactor Baggies']['Additional land area']['Value'].unit['-']), 
										'm2')

	def outlet_flow_properties(self):
		'''Establishes the thermophysical characteristics of the fluid leaving the reactor, for downstream process sizing'''

		self.outlet_temperature = Quantity(60., 'degC') # hardcoded for the moment, could become an input or even an hourly array (from energy balance) later
		self.outlet_pressure = Quantity(1.01315e5, 'Pa') # hardcoded for the moment, could become an input later

		# Assuming water vapour is saturated in the baggie, determination of the water vapour pressure
		psat = PP.Water_saturation_pressure(self.outlet_temperature)

		mol_fraction = {} # molar fraction of the gas mixture, assuming ideal gas, expressed in mol of species for a total amount of 1 mol 
		mol_fraction['H2O'] = Quantity(
								psat.unit['Pa']/self.outlet_pressure.unit['Pa'], 
								 '-') 
		# The pressure that is not due to water is due for 2/3 to H2, and for 1/3 to O2 (stoichiometry)
		mol_fraction['H2'] = Quantity(
								(2/3)*(1-mol_fraction['H2O'].unit['-']), 
								'-')
		mol_fraction['O2'] = Quantity(
								1 - mol_fraction['H2'].unit['-'] - mol_fraction['H2O'].unit['-'], 
								'-')

		_, self.outlet_mass_fraction = PP.Substance_to_mass(mol_fraction)


		smoothening_period = Quantity(1, 'day')
		self.hourly_mass_flow = {}

		# hourly_unsmoothened_output_kg should normally be a yearly dict of hourly arrays,
		# but we assume a production that is independent of the year, so there's no need to run the same calculation multiple times: a single year (year 0) is sufficient, and is the used identical to itself when generating the hourly_mass_flow dict
		hourly_unsmoothened_output_kg = (self.input_dict_resolved['Technical Operating Parameters and Specifications']['Design output by year']['Value'].unit['kg'][0] 
										*
										self.hourly_H2_mass_production_per_surface.unit['kg/m2']
										/
										self.mean_H2_mass_production_rate_per_surface.unit['kg/year/m2']
										/ 
										self.outlet_mass_fraction['H2'].unit['-']
										)
		for year in self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-']:			
			year = round(year)
			self.hourly_mass_flow[year] = Quantity(smoothened_production(hourly_unsmoothened_output_kg, round(smoothening_period.unit['h'])), 
														'kg')


		self.yearly_mass_flow = Quantity(self.input_dict_resolved['Technical Operating Parameters and Specifications']['Design output by year']['Value'].unit['kg']
									   / 
									   self.outlet_mass_fraction['H2'].unit['-']
									   ,
									   'kg')

		self.peak_mass_flowrate = Quantity(np.max(self.hourly_mass_flow[0].unit['kg']), 'kg/h')

		# specific enthalpy at the outlet of the baggie
		h = PP.Enthalpy(T = self.outlet_temperature,
						P = self.outlet_pressure, 
						amount = self.outlet_mass_fraction,
						phase = 'V', 
						composition_basis = 'mass'
						)
		self.outlet_enthalpy = Quantity(h.unit['J'], 'J/kg')

@njit
def energy_balance(
        rho_kg_m3,
        thickness_m,
        Cp_J_kg_K,
		Irrad_in_W_m2,
        eta_irrad,
		lambda_soil_W_m_K,
		Cp_soil_J_kg_K,
		rho_soil_kg_m3,
        epsilon,
        sigma_W_m2_K4,
		T_air_K,
		wind_speed_m_s
	):		
	''' Energy balance performed in 0D in the slurry, per unit of horizontal surface area
	The approach consists in linearizing the equation 
	and calculating the temperature at hour h+1 from the temeprature at hour h, 
	using the closed-form (exponential) solution of the linearized equation, 
	but at each instant.
	That is: closed form based on the values at instant h serve to predict hour h+1, and the later serves in turn to assess the closed form that calculates h+2
	'''
	# Constant coefficients for Prony approximation
	prony_c = np.array([0.01587683, 0.00238143, 0.00042124,	0.00097731,	0.00583964,	0.00025026])
	prony_gamma = np.array([2.08E-04, 5.58E-06, 1.49E-07, 9.32E-07, 3.34E-05, 1.13E-08])

	Capacity_J_K = Cp_J_kg_K * rho_kg_m3 * thickness_m # Heat capacity of the slurry (per m2)
	h_wind_W_m2_K =  5.7 + 3.8*wind_speed_m_s # Heat exchange coefficient between reactor and air, based on Choi et al (2026), DOI 10.1016/j.enconman.2026.121998, probably relaying McAdams (1954), which is only true for vertical walls!
	#h_wind_W_m2_K = 7.4 + 4*wind_speed_m_s # Palyvos (2008)
	#h_wind_W_m2_K = 2.8 + 3*wind_speed_m_s # Watmuff (1977)
	effusivity_soil = (lambda_soil_W_m_K * rho_soil_kg_m3 * Cp_soil_J_kg_K)**0.5
	
	# initial conditions are not known. 
	# Therefore, we use a spin up strategy: 
	# start with an arbitrary initial guess, and iterate over a period before the actual first hour (midnight, January 1st) so that the first hour's prediction is reasonably close to reality

	# estimate of the typical characteristic time, in order to know for how many hours the spin up should be applied.

	h_wind_typical = np.mean(h_wind_W_m2_K)
	T_typical = np.mean(T_air_K) # For the moment it's just equal to T_soil, but in the general cas it might not be true

	tau_s = Capacity_J_K/(h_wind_typical + 4*epsilon*sigma_W_m2_K4*T_typical**3) # typical thermal characteristic time in seconds
	#print('characteristic time h ', tau_s/3600)
	spin_up_time_h = 8760#round (10 * tau_s / 3600) + 1 # 10* characteristic time + 1 h to ensure we always get at least one previous step from our initial estimate
	print('spin_up_time_h ', spin_up_time_h)
	# fictitious temperature estimate for initialisation
	T_spin_up = ( # initial guess based on quasi steady-state approximation, assuming the radiative linearized heat transfer coefficient is calculated at air temperature, and the bag is in thermal equilibrium with the ground
					(eta_irrad * Irrad_in_W_m2[-spin_up_time_h] + h_wind_W_m2_K[-spin_up_time_h] * T_air_K[-spin_up_time_h] + 4*epsilon*sigma_W_m2_K4*T_air_K[-spin_up_time_h]**4)
					/
					(h_wind_W_m2_K[-spin_up_time_h] + 4*epsilon*sigma_W_m2_K4*T_air_K[-spin_up_time_h]**3)
					) 
	phi_prony = np.zeros(6)
	phi_soil_W_m2 = 0
	#ground_HX = np.zeros_like(Irrad_in_W_m2)

	for i in range(1, spin_up_time_h):
		idx = i-spin_up_time_h
		# Predictor
		linear = -(h_wind_W_m2_K[idx] + 4*epsilon*sigma_W_m2_K4*T_spin_up**3) / Capacity_J_K
		offset = (eta_irrad * Irrad_in_W_m2[idx] + phi_soil_W_m2 + h_wind_W_m2_K[idx] * T_air_K[idx] + epsilon*sigma_W_m2_K4 * (3*T_spin_up**4 + T_air_K[idx]**4) ) / Capacity_J_K
		T_equilibrium = -offset/linear
		T_predicted = T_equilibrium + (T_spin_up - T_equilibrium)*math.exp(linear * 3600) 
		# Calculate flux from the ground using Prony approximation
		phi_prony_predicted = phi_prony * np.exp(-prony_gamma * 3600) + ((T_predicted - T_spin_up)/3600) * (1 - np.exp(-prony_gamma * 3600)) / prony_gamma
		phi_soil_W_m2_predicted = - effusivity_soil * np.sum(prony_c * phi_prony_predicted) / np.pi**0.5
		phi_soil_W_m2 = phi_soil_W_m2_predicted	
		# Corrector
		offset = (eta_irrad * Irrad_in_W_m2[idx] + phi_soil_W_m2 + h_wind_W_m2_K[idx] * T_air_K[idx] + epsilon*sigma_W_m2_K4 * (3*T_spin_up**4 + T_air_K[idx]**4) ) / Capacity_J_K
		T_equilibrium = -offset/linear
		T_updated = T_equilibrium + (T_spin_up - T_equilibrium)*math.exp(linear * 3600) 
		phi_prony = phi_prony * np.exp(-prony_gamma * 3600) + ((T_updated - T_spin_up)/3600) * (1 - np.exp(-prony_gamma * 3600)) / prony_gamma		
		phi_soil_W_m2	= - effusivity_soil * np.sum(prony_c * phi_prony) / np.pi**0.5
		# update of T_spin_up, i.e.: estimate the spin up temperature at instant i from the beginning of the spin up period (= instant i-spin_up_time_h from the start of the "real" period of integration)
		T_spin_up = T_updated
	# at this stage, we have T_spin_up = value at the beginning of the first time_interval_initial_temperature_K
	# the first time_interval_initial_temperature_K is the temperature at the beginning of the first interval in which the irradiation and wind speed are assumed to be constant for 1h (centered on January 1st, Midnight).
	# However, the typical temperature reactor_hourly_temperature_K during the interval is not equal to the temperature at the beginning of the interval, but to the average between the beginning and end of interval
	reactor_hourly_temperature_K = np.zeros_like(Irrad_in_W_m2)
	time_interval_initial_temperature_K = T_spin_up
	print('initial T ', T_spin_up)
	# Loop for the actual temperature over the integration period of 1 year
	for i in range(0, len(reactor_hourly_temperature_K)):
		# Predictor
		linear = -(h_wind_W_m2_K[i] + 4*epsilon*sigma_W_m2_K4*time_interval_initial_temperature_K**3) / Capacity_J_K
		offset = (eta_irrad * Irrad_in_W_m2[i] + phi_soil_W_m2 + h_wind_W_m2_K[i] * T_air_K[i] + epsilon*sigma_W_m2_K4 * (3*time_interval_initial_temperature_K**4 + T_air_K[i]**4) ) / Capacity_J_K
		T_equilibrium = -offset/linear
		time_interval_end_temperature_predicted = T_equilibrium + (time_interval_initial_temperature_K - T_equilibrium)*math.exp(linear * 3600)	
		# Calculate flux from the ground using Prony approximation
		phi_prony_predicted = phi_prony * np.exp(-prony_gamma * 3600) + ((time_interval_end_temperature_predicted - time_interval_initial_temperature_K)/3600) * (1 - np.exp(-prony_gamma * 3600)) / prony_gamma
		phi_soil_W_m2_predicted = - effusivity_soil * np.sum(prony_c * phi_prony_predicted) / np.pi**0.5	
		phi_soil_W_m2 = phi_soil_W_m2_predicted
		#ground_HX[i] = phi_soil_W_m2		
		# Corrector
		offset = (eta_irrad * Irrad_in_W_m2[i] + phi_soil_W_m2 + h_wind_W_m2_K[i] * T_air_K[i] + epsilon*sigma_W_m2_K4 * (3*time_interval_initial_temperature_K**4 + T_air_K[i]**4) ) / Capacity_J_K
		T_equilibrium = -offset/linear
		time_interval_end_temperature = T_equilibrium + (time_interval_initial_temperature_K - T_equilibrium)*math.exp(linear * 3600)	
		phi_prony = phi_prony * np.exp(-prony_gamma * 3600) + ((time_interval_end_temperature - time_interval_initial_temperature_K)/3600) * (1 - np.exp(-prony_gamma * 3600)) / prony_gamma
		phi_soil_W_m2 = - effusivity_soil * np.sum(prony_c * phi_prony) / np.pi**0.5	

		# average temperature during the interval
		reactor_hourly_temperature_K[i] = (T_equilibrium 
											+ 
											(time_interval_end_temperature-time_interval_initial_temperature_K)
											/
											math.log(
												(time_interval_end_temperature-T_equilibrium)
												/
												(time_interval_initial_temperature_K-T_equilibrium)
												)
										 )
		# for the next time step, the end of the current interval becomes the beginning of the next interval
		time_interval_initial_temperature_K = time_interval_end_temperature		
		#ground_HX[i] = h_wind_W_m2_K[i] * (T_air_K[i]-reactor_hourly_temperature_K[i])
	return reactor_hourly_temperature_K#, ground_HX