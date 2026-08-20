import numpy as np
from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.input_modification import hourly_to_daily_power
from pyH2A.Utilities.Physical_Properties.Physical_properties import Physical_properties as PP
from pyH2A.Utilities.Unit_Handler.quantity import Quantity

class Photocatalytic_Plugin:
	'''Simulating H2 production using photocatalytic water splitting in plastic baggie reactors.

	Parameters
	----------
	Technical Operating Parameters and Specifications > Plant design capacity > Value : float
		Plant design capacity, in mass of hydrogen/time.
	Reactor Baggies > Cost material top > Value : float
		Cost of baggie top material.
	Reactor Baggies > Cost Material Bottom > Value : float
		Cost of baggie bottom material.
	Reactor Baggies > Number of ports per baggie > Value : int
		Number of ports per baggie.
	Reactor Baggies > Cost of port > Value : float
		Cost of a port.		
	Reactor Baggies > Other Costs > Value : float
		Other costs per baggie.
	Reactor Baggies > Markup factor > Value : float
		Markup factor for baggies, typically > 1.
	Reactor Baggies > Length > Value : float
		Length of single baggie in m.
	Reactor Baggies > Width > Value : float
		Width of single baggie in m.
	Reactor Baggies > Filling height > Value : float
		Height of reactor baggie in m. In this simulation this value determines the height
		of the water level and hence is an important parameter ultimately determining the
		level of light absorption and total catalyst amount.
	Reactor Baggies > Additional land area > Value : float
		Additional land area required, percentage or value > 0. 
		Calculated as: (1 + addtional land area) * baggie area.
	Reactor Baggies > Lifetime > Value : float
		Lifetime of reactor baggies in years before replacement is required.
	Catalyst > Cost per unit of mass > Value : float
		Cost per mass of catalyst.
	Catalyst > Concentration > Value : float
		Concentration of catalyst.
	Catalyst > Lifetime > Value : float
		Lifetime of catalysts before replacement is required.
	Catalyst > Molar Weight > Value : float, optional
		If the molar weight of the catalyst is specified, homogeneous catalyst
		properties (TON, TOF etc. are calculated).
	Catalyst > Molar Attenuation Coefficient > Value : float, optional
		If the molar attenuation coefficient is specified (along with the molar weight),
		absorbance and the fraction of absorbed light are also calculated.
	Solar-to-Hydrogen Efficiency > STH > Value : float
		Solar-to-hydrogen efficiency in percentage or as a value between 0 and 1.
	Solar Input > Mean solar input > Value : float
		Mean solar input power per area.
	Solar Input > Hourly > Value : ndarray
		Hourly irradiation data.

	Returns
	-------
	Non-Depreciable Capital Costs > Land required > Value : float
		Total land area required in acres.
	Non-Depreciable Capital Costs > Solar collection area > Value : float
		Solar colelction area in m2.
	Planned Replacement > Planned replacement catalyst > Cost : float
		Total cost of completely replacing the catalyst once.
	Planned Replacement > Planned replacement catalyst > Frequency : float
		Replacement frequency of catalyst in years, identical to catalyst lifetime.
	Planned Replacement > Planned replacement baggie > Cost : float
		Total cost of replacing all  baggies.
	Planned Replacement > Planned replacement baggie > Frequency : float
		Replacement frequency of baggies in year, identical to baggie lifetime.
	Direct Capital Costs - Reactor Baggies > Baggie cost > Value : float
		Total baggie cost.
	Direct Capital Costs - Photocatalyst > Catalyst cost > Value : float
		Total catalyst cost.
	Reactor Baggies > Number > Value : int
		Number of individual baggies required for design H2 production capacity.
	Water Volume > Volume > Value : float
		Total water volume.
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
				"Plant design capacity": {
					"Value": {
						"type": {int,float},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "mass/time",
					},
					"optional": False,
					"description": "Plant design capacity, in mass of hydrogen/time."
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
				"Mean solar input": {
					"Value": {
						"type": {int, float,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "power / area", 
					},
					"optional": False,
					"description": "Mean solar input."
				},
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
			"Yearly mass flow": {
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
		
		self.hydrogen_production()
		self.baggie_cost()
		self.catalyst_cost()
		self.land_area()
		self.catalyst_activity()
		self.outlet_flow_properties()

		
		output_inserter_function(self.output_dict, self, dcf, 'Photocatalytic_Plugin') 

	def hydrogen_production(self):
		'''Calculation of hydrogen produced per day per baggie (in kg).
		'''

		baggie = self.input_dict_resolved['Reactor Baggies']

		self.baggie_area = Quantity(baggie['Length']['Value'].unit['m'] * baggie['Width']['Value'].unit['m'], 'm2')
		baggie_insolation = (self.baggie_area.unit['m2'] 
							 * self.input_dict_resolved['Solar Input']['Mean solar input']['Value'].unit['W/m2'])
		mol_H2_per_baggie_per_second = (baggie_insolation 
										* self.input_dict_resolved['Solar-to-Hydrogen Efficiency']['STH']['Value'].unit['-'] 
										/ self.H2_molecule_energy.unit['J/mol'])

		self.mass_rate_H2_per_baggie = Quantity(mol_H2_per_baggie_per_second*self.H2_molecular_weight.unit['kg/mol'], 'kg/s')

	def catalyst_activity(self):
		'''Calculation of detailed catalyst properties based on provided parameters. If "Molar Weight (g/mol)"
		is specified in "Catalyst" table properties of a homogeneous catalyst are also calculated. Furthermore,
		if "Molar Attenuation Coefficient (M^-1 cm^-1)" is also provided, the light absorption properties 
		are calculated.
		'''

		catalyst_properties = {}

		peak_hourly_irradiation_per_m2 = np.amax(self.input_dict_resolved['Solar Input']['Hourly']['Value'].unit['J/m2'])
		
		peak_hourly_mol_H2_per_m2 = (peak_hourly_irradiation_per_m2
									 * self.input_dict_resolved['Solar-to-Hydrogen Efficiency']['STH']['Value'].unit['-']
									 / self.H2_molecule_energy.unit['J/mol'])

		mean_mol_rate_H2_per_surface = (self.input_dict_resolved['Solar Input']['Mean solar input']['Value'].unit['W/m2'] 
										* self.input_dict_resolved['Solar-to-Hydrogen Efficiency']['STH']['Value'].unit['-']
										/ self.H2_molecule_energy.unit['J/mol'])
		
		self.mean_mol_rate_H2_per_surface = Quantity(mean_mol_rate_H2_per_surface, 'mol/s/m2')

		kg_catalyst_per_m2 = (self.input_dict_resolved['Reactor Baggies']['Filling height']['Value'].unit['m']
							  * self.input_dict_resolved['Catalyst']['Concentration']['Value'].unit['kg/m3'])

		self.activity_H2_rate_per_catalyst_mass = Quantity(peak_hourly_mol_H2_per_m2 / kg_catalyst_per_m2, 'mol/h/kg')

		catalyst_properties['Peak activity'] = self.activity_H2_rate_per_catalyst_mass
		catalyst_properties['Peak H2 production'] = Quantity(peak_hourly_mol_H2_per_m2, 'mol/m2/h')
		catalyst_properties['Catalyst Concentration (mass / area)'] = Quantity(kg_catalyst_per_m2, 'kg/m2')
		catalyst_properties['Catalyst Concentration (mass / volume)'] = self.input_dict_resolved['Catalyst']['Concentration']['Value']
	
		if 'Molar Weight' in self.input_dict_resolved['Catalyst']:

			catalyst_mol_per_L = (self.input_dict_resolved['Catalyst']['Concentration']['Value'].unit['g/liter'] 
								  / self.input_dict_resolved['Catalyst']['Molar Weight']['Value'].unit['g/mol'])

			liter_per_m2 = self.input_dict_resolved['Reactor Baggies']['Filling height']['Value'].unit['mm']

			mol_catalyst_per_m2 = liter_per_m2 * catalyst_mol_per_L

			peak_TOF_hourly = peak_hourly_mol_H2_per_m2 / mol_catalyst_per_m2
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
			
			kg_H2_per_day_baggie_calculation = self.mass_rate_H2_per_baggie.unit['kg/day'] * self.baggie_number

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

		baggie_number = (self.input_dict_resolved['Technical Operating Parameters and Specifications']['Plant design capacity']['Value'].unit['kg/day'] 
						 / self.mass_rate_H2_per_baggie.unit['kg/day'])
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

		self.outlet_temperature = Quantity(60., 'degC') # hardcoded for the moment, could become an input later
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


		self.yearly_mass_flow = Quantity(self.input_dict_resolved['Technical Operating Parameters and Specifications']['Plant design capacity']['Value'].unit['kg/year']
								   		*	
										self.input_dict_resolved['Time']['Years']['Value']['Operation years ones'].unit['-']
									   / 
									   self.outlet_mass_fraction['H2'].unit['-']
									   ,
									   'kg')
		
		Daily_irradiation_J_per_m2 = hourly_to_daily_power(self.input_dict_resolved['Solar Input']['Hourly']['Value'].unit['J/m2'])
		Max_daily_irradiation_J_per_m2 = np.max(Daily_irradiation_J_per_m2)

		time_for_peak = Quantity(1., 's')
		self.peak_mass_flowrate = Quantity(self.yearly_mass_flow.unit['kg'][0] * time_for_peak.unit['year'] 
									 		*
											Max_daily_irradiation_J_per_m2
											/
											self.input_dict_resolved['Solar Input']['Mean solar input']['Value'].unit['W/m2'],
											'kg/day')

		# specific enthalpy at the outlet of the baggie
		h = PP.Enthalpy(T = self.outlet_temperature,
						P = self.outlet_pressure, 
						amount = self.outlet_mass_fraction,
						phase = 'V', 
						composition_basis = 'mass'
						)
		self.outlet_enthalpy = Quantity(h.unit['J'], 'J/kg')