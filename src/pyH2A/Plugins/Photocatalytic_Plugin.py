import numpy as np
from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity

input_dict = {
	"Technical Operating Parameters and Specifications": {
		"Design output per day": {
			"Value": {
				"type": {float,},
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": "mass",
			},
			"optional": False,
			"description": "Design output."
		},
	},
	"Reactor Baggies": {
		"Cost material top": {
			"Value": {
				"type": {float,},
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
				"type": {float,},
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
		"Other costs per baggies": {
			"Value": {
				"type": {float,},
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
				"type": {float,},
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
				"type": {float,},
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
				"type": {float,},
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
				"type": {float,},
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
				"type": {float,},
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
				"type": {float,},
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
				"type": {float,},
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
				"type": {float,},
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
				"type": {float,},
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
				"type": {float,},
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
				"type": {float,},
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": "volume / (substance * length)",
			},
			"optional": True,
			"description": "If the molar attenuation coefficient is specified (along with the molar weight), absorbance and the fraction of absorbed light are also calculated."
		},
	},
	"Solar-to-Hydrogen Efficiency": {
		"STH": {
			"Value": {
				"type": {float,},
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
				"type": {float,},
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
  
output_dict = {
	"Non-Depreciable Capital Costs": {
		"Land required": {
			"Value": {
				"inserted_value": "total_land_area",
				"type": {float,},
				"dimension": "area",
			},
			"optional": False,
			"description": "Total land area required."
		},
		"Solar Collection area": {
			"Value": {
				"inserted_value": "total_solar_collection_area",
				"type": {float,},
				"dimension": "area",
			},
			"optional": False,
			"description": "Solar collection area"
		},
	},
	"Planned Replacement": {
		"Planned replacement catalyst": {
			"Cost": {
				"inserted_value": "catalyst_cost",
				"type": {float,},
				"dimension": "currency",
			},
			"Frequency": {
				"inserted_value": "input_dict_resolved['Catalyst']['Lifetime']['Value']",
				"type": {float,},
				"dimension": "time",
			},
			"optional": False,
			"description": "Total cost of completely replacing the catalyst once and replacement frequency in years, identical to catalyst lifetime."
		},
		"Planned Replacement Baggie": {
			"Cost": {
				"inserted_value": "baggies_cost",
				"type": {float,},
				"dimension": "currency",
			},
			"Frequency": {
				"inserted_value": "input_dict_resolved['Reactor Baggies']['Lifetime']['Value']",
				"type": {float,},
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
				"type": {float,},
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
				"type": {float,},
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
				"type": {int,},
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
				"type": {float,},
				"dimension": "volume",
			},
			"optional": False,
			"description": "Total water volume"
		},
	},
}

class Photocatalytic_Plugin:
	'''Simulating H2 production using photocatalytic water splitting in plastic baggie reactors.

	Parameters
	----------
	Technical Operating Parameters and Specifications > Design Output per Day > Value : float
		Design output in (kg of H2)/day, ``process_table()`` is used.
	Reactor Baggies > Cost Material Top ($/m2) > Value : float
		Cost of baggie top material in $/m2.
	Reactor Baggies > Cost Material Bottom ($/m2) > Value : float
		Cost of baggie bottom material in $/m2.
	Reactor Baggies > Number of ports > Value : int
		Number of ports per baggie.
	Reactor Baggies > Other Costs ($) > Value : float
		Other costs per baggie.
	Reactor Baggies > Markup factor > Value : float
		Markup factor for baggies, typically > 1.
	Reactor Baggies > Length (m) > Value : float
		Length of single baggie in m.
	Reactor Baggies > Width (m) > Value : float
		Width of single baggie in m.
	Reactor Baggies > Height (m) > Value : float
		Height of reactor baggie in m. In this simulation this value determines the height
		of the water level and hence is an important parameter ultimately determining the
		level of light absorption and total catalyst amount.
	Reactor Baggies > Additional land area (%) > Value : float
		Additional land area required, percentage or value > 0. 
		Calculated as: (1 + addtional land area) * baggie area.
	Reactor Baggies > Lifetime (years) > Value : float
		Lifetime of reactor baggies in years before replacement is required.
	Catalyst > Cost per kg ($) > Value : float
		Cost per kg of catalyst.
	Catalyst > Concentration (g/L) > Value : float
		Concentration of catalyst in g/L.
	Catalyst > Lifetime (years) > Value : float
		Lifetime of catalysts in year before replacement is required.
	Catalyst > Molar Weight (g/mol) > Value : float, optional
		If the molar weight of the catalyst (in g/mol) is specified, homogeneous catalyst
		properties (TON, TOF etc. are calculated).
	Catalyst > Molar Attenuation Coefficient (M^-1 cm^-1) > Value : float, optional
		If the molar attenuation coefficient (in M^-1 cm^-1) is specified (along with the molar weight),
		absorbance and the fraction of absorbed light are also calculated.
	Solar-to-Hydrogen Efficiency > STH (%) > Value : float
		Solar-to-hydrogen efficiency in percentage or as a value between 0 and 1.
	Solar Input > Mean solar input (kWh/m2/day) > Value : float
		Mean solar input in kWh/m2/day, ``process_table()`` is used.
	Solar Input > Hourly (kWh/m2) > Value : ndarray
		Hourly irradiation data.

	Returns
	-------
	Non-Depreciable Capital Costs > Land required (acres) > Value : float
		Total land area required in acres.
	Non-Depreciable Capital Costs > Solar Collection Area (m2) > Value : float
		Solar colelction area in m2.
	Planned Replacement > Planned Replacement Catalyst > Cost ($) : float
		Total cost of completely replacing the catalyst once.
	Planned Replacement > Planned Replacement Catalyst > Frequency (years) : float
		Replacement frequency of catalyst in years, identical to catalyst lifetime.
	Planned Replacement > Planned Replacement Baggie > Cost ($) : float
		Total cost of replacing all  baggies.
	Planned Replacement > Planned Replacement Baggie > Frequency (years) : float
		Replacement frequency of baggies in year, identical to baggie lifetime.
	Direct Capital Costs - Reactor Baggies > Baggie Cost ($) > Value : float
		Total baggie cost.
	Direct Capital Costs - Photocatalyst > Catalyst Cost ($) > Value : float
		Total catalyst cost.
	Reactor Baggies > Number > Value : int
		Number of individual baggies required for design H2 production capacity.
	Catalyst > Properties > Value : dict
		Dictionary containing detailed catalyst properties calculated from provided parameters.
	['Photocatalytic_Plugin'].catalyst_properties : dict
		Attribute containing catalyst properties dictionary.
	Water Volume > Volume (liters) > Value : float
		Total water volume in liters.
	'''

	def __init__(self, dcf, print_info):
		self.input_dict_resolved = input_resolver_function(input_dict, dcf, 'Photocatalytic_Plugin')
		self.H2_molecule_energy = Quantity(2*1.229, 'eV/entity')
		self.H2_molecular_weight = Quantity(2, 'g/mol')
		self.hydrogen_production(dcf)

		self.baggie_cost(dcf)

		self.catalyst_cost(dcf)
		self.land_area(dcf)
		self.catalyst_activity(dcf)

		output_inserter_function(output_dict, self, dcf, 'Photocatalytic_Plugin') 

	def hydrogen_production(self, dcf):
		'''Calculation of hydrogen produced per day per baggie (in kg).
		'''

		baggie = self.input_dict_resolved['Reactor Baggies']

		self.baggie_area = Quantity(baggie['Length']['Value'].unit['m'] * baggie['Width']['Value'].unit['m'], 'm2')
		baggie_insolation = self.baggie_area.unit['m2'] * self.input_dict_resolved['Solar Input']['Mean solar input']['Value'].unit['W/m2']
		mol_H2_per_baggie_per_second = baggie_insolation * self.input_dict_resolved['Solar-to-Hydrogen Efficiency']['STH']['Value'].unit['-'] / self.H2_molecule_energy.unit['J/mol']

		self.mass_rate_H2_per_baggie = Quantity(mol_H2_per_baggie_per_second*self.H2_molecular_weight.unit['kg/mol'], 'kg/s')

	def catalyst_activity(self, dcf):
		'''Calculation of detailed catalyst properties based on provided parameters. If "Molar Weight (g/mol)"
		is specified in "Catalyst" table properties of a homogeneous catalyst are also calculated. Furthermore,
		if "Molar Attenuation Coefficient (M^-1 cm^-1)" is also provided, the light absorption properties 
		are calculated.
		'''

		catalyst_properties = {}

		peak_hourly_irradiation_per_m2 = np.amax(self.input_dict_resolved['Solar Input']['Hourly']['Value'].unit['J/m2'])
		
		peak_mol_H2_per_m2_per_h = peak_hourly_irradiation_per_m2 * self.input_dict_resolved['Solar-to-Hydrogen Efficiency']['STH']['Value'].unit['-'] / self.H2_molecule_energy.unit['J/mol']

		self.mean_mol_rate_H2_per_surface = Quantity(
			self.input_dict_resolved['Solar Input']['Mean solar input']['Value'].unit['W/m2'] *self.input_dict_resolved['Solar-to-Hydrogen Efficiency']['STH']['Value'] / self.H2_molecule_energy.unit['J/mol'], 
			'mol/s/m2'
		)

		kg_catalyst_per_m2 = self.input_dict_resolved['Reactor Baggies']['Height']['Value'].unit['m'] * self.input_dict_resolved['Catalyst']['Concentration']['Value'].unit['kg/m3']

		self.activity_H2_rate_per_catalyst_mass = Quantity(peak_mol_H2_per_m2_per_h / kg_catalyst_per_m2, 'mol/h/kg')

		catalyst_properties['Peak activity'] = self.activity_H2_rate_per_catalyst_mass
		catalyst_properties['Peak H2 production'] = Quantity(peak_mol_H2_per_m2_per_h, 'mol/m2/h')
		catalyst_properties['Catalyst Conc.'] = Quantity(kg_catalyst_per_m2, 'kg/m2')
		catalyst_properties['Catalyst Conc.'] = self.input_dict_resolved['Catalyst']['Concentration']['Value']
	
		if 'Molar Weight' in self.input_dict_resolved['Catalyst']:

			catalyst_mol_per_L = self.input_dict_resolved['Catalyst']['Concentration']['Value'].unit['g/liter'] / self.input_dict_resolved['Catalyst']['Molar Weight']['Value'].unit['g/mol']

			liter_per_m2 = self.input_dict_resolved['Reactor Baggies']['Height']['Value'].unit['mm']

			mol_catalyst_per_m2 = liter_per_m2 * catalyst_mol_per_L

			peak_TOF_hourly = peak_mol_H2_per_m2_per_h / mol_catalyst_per_m2
			average_TOF_daily = self.mean_mol_rate_H2_per_surface.unit['mol/day/m2'] / mol_catalyst_per_m2
			TON = average_TOF_daily * self.input_dict_resolved['Catalyst']['Lifetime']['Value'].unit['day']

			catalyst_properties['Homogeneous'] = {}
			catalyst_properties['Homogeneous']['Catalyst Conc. per vol.'] = Quantity(catalyst_mol_per_L, 'mol/liter')
			catalyst_properties['Homogeneous']['Catalyst Conc. per area'] = Quantity(mol_catalyst_per_m2, 'mol/m2')
			catalyst_properties['Homogeneous']['Peak TOF'] = Quantity(peak_TOF_hourly, '-/hour')
			catalyst_properties['Homogeneous']['Mean daily TOF'] = Quantity(average_TOF_daily, '-/day')
			catalyst_properties['Homogeneous']['TON'] = Quantity(TON, '-')

			if 'Molar Attenuation Coefficient' in self.input_dict_resolved['Catalyst']:
				absorbance = catalyst_mol_per_L * self.input_dict_resolved['Reactor Baggies']['Height']['Value'].unit['cm'] * self.input_dict_resolved['Catalyst']['Molar Attenuation Coefficient']['Value'].unit['liter/cm/mol']

				catalyst_properties['Homogeneous']['Absorbance'] = Quantity(absorbance, '-')
				catalyst_properties['Homogeneous']['Absorbed light'] = Quantity(1 - 10**(-absorbance), '-')

			kg_H2_per_day_TOF_calculation = self.catalyst_amount.unit['kg'] / self.input_dict_resolved['Catalyst']['Molar weight']['Value'].unit['kg/mol'] * average_TOF_daily * self.H2_molecular_weight.unit['kg/mol']
			kg_H2_per_day_baggie_calculation = self.mass_rate_H2_per_baggie.unit['kg/day'] * self.baggie_number

			assert abs(kg_H2_per_day_TOF_calculation - kg_H2_per_day_baggie_calculation) < 1e-6, 'Difference between baggie and TOF calculation for daily H2 production: TOF: {0}, Baggie: {0}.'.format(
					kg_H2_per_day_TOF_calculation, kg_H2_per_day_baggie_calculation)

		self.catalyst_properties = catalyst_properties

	def baggie_cost(self, dcf):
		'''Calculation of cost per baggie, number of required baggies and total baggie cost.
		'''

		baggie = self.input_dict_resolved['Reactor Baggies']

		material_cost = self.baggie_area.unit['m2'] * (baggie['Cost material top']['Value'].unit['USD/m2'] + baggie['Cost material bottom']['Value'].unit['USD/m2'])
		port_cost = baggie['Number of ports']['Value'].unit['-'] * baggie['Cost of port']['Value'].unit['USD']

		cost_per_baggie = baggie['Markup factor']['Value'].unit['-'] * (material_cost + port_cost + baggie['Other Costs']['Value'].unit['USD'])

		self.baggie_number = Quantity(np.ceil(self.input_dict_resolved['Technical Operating Parameters and Specifications']['Design output per day']['Value'].unit['kg'] / self.mass_rate_H2_per_baggie.unit['kg/day']), '-')
		self.baggies_cost = Quantity(self.baggie_number.unit['-'] * cost_per_baggie, 'USD')

	def catalyst_cost(self, dcf):
		'''Calculation of individual baggie volume, catalyst amount per baggie, total catalyst amount 
		and total catalyst cost.
		'''

		baggie = self.input_dict_resolved['Reactor Baggies']

		baggie_volume = baggie['Length']['Value'].unit['m'] * baggie['Width']['Value'].unit['m'] * baggie['Height']['Value'].unit['m']

		self.total_volume = Quantity(baggie_volume * self.baggie_number, 'm3')

		self.catalyst_amount_per_baggie = Quantity(baggie_volume * self.input_dict_resolved['Catalyst']['Concentration']['Value'].unit['kg/m3'], 'kg')
		self.catalyst_amount = Quantity(self.catalyst_amount_per_baggie.unit['kg'] * self.baggie_number.unit['-'], 'kg')

		self.catalyst_cost = Quantity(self.catalyst_amount.unit['kg'] * self.input_dict_resolved['Catalyst']['Cost per unit mass']['Value'].unit['USD/kg'], 'USD')

	def land_area(self, dcf):
		'''Calculation of total required land area and solar collection area.
		'''

		baggie_land_area = self.baggie_number.unit['-'] * self.baggie_area.unit['m2']
		self.total_land_area = Quantity(baggie_land_area * (1. + self.input_dict_resolved['Reactor Baggies']['Additional land area']['Value'].unit['-']), 'm2')

		self.total_solar_collection_area = Quantity(baggie_land_area, 'm2')
