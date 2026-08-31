import math

from scipy.constants import R as GAS_CONSTANT

from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.input_modification import read_textfile
import pyH2A.Utilities.find_nearest as fn

# Common commercial plate thicknesses (m, converted from standard imperial
# stock sizes in inches -- 3/16, 1/4, 5/16, ... 3.0 in), ascending; used to
# round up the calculated shell thickness to a standard stock size, see
# PSA_Plugin.calculate_psa.
STANDARD_PLATE_THICKNESS = [
	0.004762, 0.006350, 0.007938, 0.009525, 0.011112, 0.012700,             # 0.0015875 m steps
	0.015875, 0.019050, 0.022225, 0.025400,                                 # 0.003175 m steps
	0.028575, 0.031750, 0.034925, 0.038100, 0.041275, 0.044450, 0.047625, 0.050800,
	0.057150, 0.063500, 0.069850, 0.076200,                                 # 0.00635 m  steps
]

# Allowable stress for different materials according to ASME Sec VIII Div 1, current code 
# (3.5:1 margin on UTS). Given the operating temperature of H2/O2 separation, the plateau 
# part was considered. It should be adjusted for other applications where operating temperature 
# is higher. Used by PSA_Plugin.calculate_psa to look up the maximum allowable stress from the
# declared PSA > Material input.
ALLOWABLE_STRESS_BAR = {
	"carbon_steel": 1082,      # bar SA-285 Gr C  (UTS 55 ksi / 3.5)
	"low_alloy_steel": 1179,   # bar SA-387 Gr 11/12/22 Class 1 (UTS 60 ksi / 3.5)
	"stainless_steel_304": 1379, # bar SA-240 304 (UTS 75 ksi / 3.5)
	"stainless_steel_316": 1379, # bar SA-240 316 (UTS 75 ksi / 3.5)
}


# Typical corrosion allowance (m, converted from standard imperial inch
# values) by material -- GENERAL/CLEAN service. These are common practice
# defaults, NOT service-specific. The correct value depends on the fluid,
# temperature, chlorides, and companies' standard. Corrosion-resistant alloys
# default to 0; add margin only if the service warrants it (e.g. chlorides,
# wet acidic condensate, erosion). Used by PSA_Plugin.calculate_psa to look
# up the allowance from the declared PSA > Material input.
CORROSION_ALLOWANCE_M = {
	"carbon_steel":        0.003175,   # 1/8 in, standard general-service default
	"low_alloy_steel":     0.0015875,  # 1/16 in
	"stainless_steel_304": 0.0,        # corrosion-resistant
	"stainless_steel_316": 0.0,        # incl. 316L
}

# Calibration year of the SSLW (Seider, Seader, Lewin, and Widagdo) vessel 
# purchase-cost correlation. Used by PSA_Plugin.calculate_psa to look up
# the correlation's base CEPCI from Plant_Cost_Index.csv.
SSLW_BASE_YEAR = 2006

# Material factor (F_M) of the SSLW vessel purchase-cost correlation, by
# material. Used by PSA_Plugin.calculate_psa to look up F_M from the
# declared PSA > Material input.
MATERIAL_FACTOR = {
	"carbon_steel": 1.0,
	"low_alloy_steel": 1.2,
	"stainless_steel_304": 1.7,
	"stainless_steel_316": 2.1,
}

# Density (kg/m3) of the vessel shell, by material. Used by
# PSA_Plugin.calculate_psa to look up density from the declared
# PSA > Material input.
STEEL_DENSITY_KG_M3 = {
	"carbon_steel": 7850,
	"low_alloy_steel": 7850,
	"stainless_steel_304": 8000,
	"stainless_steel_316": 8000,
}

class PSA_Plugin:
	'''Simulating pressure swing adsorption (PSA) for removal of an adsorbate gas
	(e.g. O2) from the hydrogen product stream and estimating PSA system cost.

	The feed gas is assumed to be a binary mixture of the adsorbate gas and
	hydrogen only, i.e. the hydrogen mole fraction is always ``1 - adsorbate
	mole fraction``.

	Parameters
	----------
	Technical Operating Parameters and Specifications > Plant design capacity > Value : float
		Plant design capacity, i.e. net hydrogen product delivered downstream of
		the PSA (mass of hydrogen/time).
	PSA > Feed adsorbate mole fraction > Value : float
		Mole fraction of adsorbate gas (e.g. O2) in the feed gas entering the
		PSA system. A binary feed is assumed, so the hydrogen mole fraction is
		``1 - adsorbate mole fraction``.
	PSA > Adsorbate molar mass > Value : float
		Molar mass of the adsorbate gas (e.g. O2), used to convert its mole
		fraction into a mass flow rate.
	PSA > Recovery > Value : float
		Fraction of hydrogen entering the PSA that is recovered in the pure
		hydrogen product stream.
	PSA > Operating pressure > Value : float
		Absolute pressure of the feed gas entering the PSA bed.
	PSA > Operating temperature > Value : float
		Absolute temperature of the feed gas entering the PSA bed.
	PSA > Feed gas velocity > Value : float
		Assumed feed gas superficial velocity through the bed.
	PSA > Length to diameter ratio > Value : float
		Assumed bed length-to-diameter (L/D) ratio.
	PSA > Feed gas viscosity > Value : float
		Dynamic viscosity of the feed gas at operating conditions.
	PSA > Maximum pressure drop per length > Value : float, optional
		Maximum allowable gas-phase pressure drop per unit bed length, 
		defaults to 0.1 bar/m if not given.
	PSA > Number of beds > Value : float
		Total number of adsorbent beds in the PSA system.
	PSA > Material > Value : str, optional
		Vessel shell material (currently ``carbon_steel``,
		``low_alloy_steel``, ``stainless_steel_304``,
		``stainless_steel_316``), defaults to
		``stainless_steel_316``.
	PSA > Weld efficiency > Value : float, optional
		Weld (joint) efficiency of the vessel shell, used in the ASME
		shell-thickness formula, defaults to 0.85.
	Financial Input Values > Current year for capital costs > Value : int or float
		Year the PSA system cost should be escalated to, via the Chemical
		Engineering Plant Cost Index (CEPCI), from the SSLW correlation's
		calibration year (``SSLW_BASE_YEAR``, CEPCI ~500), see
		:meth:`calculate_psa`.
	PSA Adsorbent Parameters > Bed void fraction > Value : float
		Void fraction of the packed adsorbent bed.
	PSA Adsorbent Parameters > Bed usage fraction > Value : float
		Fraction of total bed adsorbent capacity effectively usable, accounting
		for the length of unused bed (LUB).
	PSA Adsorbent Parameters > Adsorption uptake fraction > Value : float
		Adsorbent equilibrium loading at adsorption pressure, in mass of
		adsorbate gas adsorbed per mass of adsorbent.
	PSA Adsorbent Parameters > Residual loading fraction > Value : float
		Adsorbent residual loading remaining after the purge/regeneration step,
		in mass of adsorbate gas per mass of adsorbent.
	PSA Adsorbent Parameters > Bulk density > Value : float
		Bulk density of the packed adsorbent.
	PSA Adsorbent Parameters > Adsorbent particle diameter > Value : float
		Diameter of the (e.g. zeolite 13X) adsorbent particles, used in the
		Ergun equation, see :meth:`calculate_psa`.
	PSA Adsorbent Parameters > Adsorbent cost per kg > Value : float
		Cost of the adsorbent material per unit mass, used together with
		``Adsorbent mass`` to calculate total adsorbent cost, see
		:meth:`calculate_psa`.
	PSA Adsorbent Parameters > Adsorbent replacement interval > Value : float
		Interval, in years, at which the full adsorbent charge needs
		replacing. Reported (together
		with the adsorbent cost) as a planned replacement, see
		:meth:`calculate_psa`; the actual replacement schedule and
		cost over the plant lifetime is computed downstream by
		``Replacement_Plugin``, using ``Time > Years``, not by this plugin.

	Returns
	-------
	Direct Capital Costs - PSA System > PSA system cost > Value : float
		Total PSA system cost (all beds): vessel purchase cost (Seider et
		al. vertical-vessel cost correlation, CEPCI-escalated to the
		``Current year for capital costs`` cost basis) plus the initial
		adsorbent charge cost, see :meth:`calculate_psa`.
	PSA > Vessel cost > Value : float
		Vessel purchase cost only (all beds), see :meth:`calculate_psa`.
	PSA > Adsorbent cost > Value : float
		Cost of the initial adsorbent charge (all beds): ``Adsorbent mass``
		x ``Adsorbent cost per kg``, see :meth:`calculate_psa`.
	Planned Replacement > Planned replacement PSA adsorbent > Cost_Value : float
		Total cost of replacing the full adsorbent charge once (all beds),
		identical to ``Adsorbent cost``, see :meth:`calculate_psa`.
	Planned Replacement > Planned replacement PSA adsorbent > Frequency_Value : float
		Adsorbent replacement frequency in years, identical to the declared
		``Adsorbent replacement interval``.
	PSA > Bed volume > Value : float
		Total adsorbent bed volume required across all beds, including void
		volume.
	PSA > Adsorbent mass > Value : float
		Total mass of adsorbent required across all beds.
	PSA > Adsorption time > Value : float
		Duration of the PSA adsorption step.
	PSA > Vessel steel mass > Value : float
		Total steel mass of the bed pressure vessels (cylindrical shell plus
		flat end caps), across all beds, see
		:meth:`calculate_psa`.
	PSA > Pressure drop > Value : float
		Gas-phase pressure drop across the single producing bed (Ergun
		equation), see :meth:`calculate_psa`.
	'''

	def __init__(self, dcf, print_info, run = True):
		self._set_up(dcf)
		if run:
			self._run(dcf)

	def _set_up(self, dcf):

		self.input_dict = {
			"Technical Operating Parameters and Specifications": {
				"Plant design capacity": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "mass / time",
					},
					"optional": False,
					"description": "Plant design capacity, in mass of hydrogen/time."
				},
			},
			"PSA": {
				"Feed adsorbate mole fraction": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, 1),
					},
					"Unit": {
						"dimension": "dimensionless",
					},
					"optional": False,
					"description": "Mole fraction of adsorbate gas (e.g. O2) in the feed gas entering "
								   "the PSA system. A binary feed of adsorbate gas and hydrogen is "
								   "assumed, so the hydrogen mole fraction is 1 - adsorbate mole fraction."
				},
				"Adsorbate molar mass": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "mass / substance",
					},
					"optional": False,
					"description": "Molar mass of the adsorbate gas (e.g. O2), used to convert its "
								   "mole fraction into a mass flow rate."
				},
				"Recovery": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, 1),
					},
					"Unit": {
						"dimension": "dimensionless",
					},
					"optional": False,
					"description": "Fraction of hydrogen entering the PSA that is recovered in the pure "
								   "hydrogen product stream."
				},
				"Operating pressure": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "pressure",
					},
					"optional": False,
					"description": "Absolute pressure of the feed gas entering the PSA bed, used with "
								   "Operating temperature (ideal gas law) to convert the feed's molar "
								   "flow rate into a volumetric flow rate for bed sizing."
				},
				"Operating temperature": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "absolute_temperature",
					},
					"optional": False,
					"description": "Absolute temperature of the feed gas entering the PSA bed, used with "
								   "Operating pressure (ideal gas law) to convert the feed's molar "
								   "flow rate into a volumetric flow rate for bed sizing."
				},
				"Feed gas velocity": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, 0.5),
					},
					"Unit": {
						"dimension": "length / time",
					},
					"optional": False,
					"description": "Assumed feed gas superficial velocity through the bed, used to size "
								   "bed cross-sectional area (= volumetric feed flow / velocity)."
				},
				"Length to diameter ratio": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "dimensionless",
					},
					"optional": False,
					"description": "Assumed bed length-to-diameter (L/D) ratio."
				},
				"Feed gas viscosity": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "pressure * time",
					},
					"optional": False,
					"description": "Dynamic viscosity of the feed gas at operating conditions, used "
								   "in the Ergun equation, see :meth:`calculate_psa`."
				},
				"Maximum pressure drop per length": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "pressure / length",
					},
					"optional": True,
					"description": "Maximum allowable gas-phase pressure drop per unit bed length; "
								   "a warning is printed if the calculated pressure drop per length "
								   "exceeds this, see :meth:`calculate_psa`. Defaults to "
								   "0.1 bar/m if not given."
				},
				"Number of beds": {
					"Value": {
						"type": {float,int,},
						"bounds": (1, None),
					},
					"Unit": {
						"dimension": "dimensionless",
					},
					"optional": False,
					"description": "Total number of beds in the PSA system."
				},
				"Material": {
					"Value": {
						"type": {str,},
						"options": set(ALLOWABLE_STRESS_BAR.keys()),
					},
					"optional": True,
					"description": "Vessel shell material, used to look up the maximum allowable "
								   "stress, corrosion allowance, density, and SSLW material factor "
								   "for the vessel, see :meth:`calculate_psa`. "
								   "Defaults to 'stainless_steel_316' if not given."
				},
				"Weld efficiency": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, 1),
					},
					"Unit": {
						"dimension": "dimensionless",
					},
					"optional": True,
					"description": "Weld (joint) efficiency of the vessel shell, used in the ASME "
								   "shell-thickness formula, see :meth:`calculate_psa`. "
								   "Defaults to 0.85 if not given."
				},
			},
			"PSA Adsorbent Parameters": {
				"Bed void fraction": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, 1),
					},
					"Unit": {
						"dimension": "dimensionless",
					},
					"optional": False,
					"description": "Void fraction of the packed adsorbent bed."
				},
				"Bed usage fraction": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, 1),
					},
					"Unit": {
						"dimension": "dimensionless",
					},
					"optional": False,
					"description": "Fraction of total bed adsorbent capacity effectively usable, "
								   "accounting for the length of unused bed (LUB)."
				},
				"Adsorption uptake fraction": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "dimensionless",
					},
					"optional": False,
					"description": "Adsorbent equilibrium loading at adsorption pressure, in mass of "
								   "adsorbate gas adsorbed per mass of adsorbent."
				},
				"Residual loading fraction": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "dimensionless",
					},
					"optional": False,
					"description": "Adsorbent residual loading remaining after the purge/regeneration "
								   "step"
				},
				"Bulk density": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "mass / volume",
					},
					"optional": False,
					"description": "Bulk density of the packed adsorbent."
				},
				"Adsorbent particle diameter": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "length",
					},
					"optional": False,
					"description": "Diameter of the (e.g. zeolite 13X) adsorbent particles, used in "
								   "the Ergun equation, see :meth:`calculate_psa`."
				},
				"Adsorbent cost per kg": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "currency / mass",
					},
					"optional": False,
					"description": "Cost of the adsorbent material per unit mass, used together "
								   "with Adsorbent mass to calculate total adsorbent cost, see "
								   ":meth:`calculate_psa`."
				},
				"Adsorbent replacement interval": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "time",
					},
					"optional": False,
					"description": "Interval at which the full adsorbent charge needs replacing. "
								   "Reported as a planned replacement (cost and frequency); the "
								   "actual replacement schedule/cost over the plant lifetime is "
								   "computed downstream by Replacement_Plugin, see "
								   ":meth:`calculate_psa`."
				},
			},
			"Financial Input Values": {
				"Current year for capital costs": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "dimensionless",
					},
					"optional": False,
					"description": "Year the PSA system cost should be escalated to, via the Chemical "
								   "Engineering Plant Cost Index (CEPCI), from the SSLW correlation's "
								   "calibration year (SSLW_BASE_YEAR, CEPCI ~500)."
				},
			},
		}

		self.output_dict = {
			"Direct Capital Costs - PSA System": {
				"PSA system cost": {
					"Value": {
						"inserted_value": "psa_cost",
						"type": {float,int,},
						"dimension": "currency",
					},
					"description": "Total PSA system cost (all beds): vessel purchase cost (SSLW "
								   "correlation, CEPCI-escalated) plus the initial adsorbent "
								   "charge cost.",
					"optional": False,
				}
			},
			"Planned Replacement": {
				"Planned replacement PSA adsorbent": {
					"Cost_Value": {
						"inserted_value": "adsorbent_cost",
						"type": {float,int,},
						"dimension": "currency",
					},
					"Frequency_Value": {
						"inserted_value": "adsorbent_replacement_interval",
						"type": {float,int,},
						"dimension": "time",
					},
					"description": "Total cost of replacing the full adsorbent charge once (all beds).",
					"optional": False,
				}
			},
			"PSA": {
				"Vessel cost": {
					"Value": {
						"inserted_value": "vessel_cost",
						"type": {float,int,},
						"dimension": "currency",
					},
					"description": "Vessel purchase cost only (all beds).",
					"optional": False,
				},
				"Adsorbent cost": {
					"Value": {
						"inserted_value": "adsorbent_cost",
						"type": {float,int,},
						"dimension": "currency",
					},
					"description": "Cost of the initial adsorbent charge (all beds): Adsorbent "
								   "mass x Adsorbent cost per kg.",
					"optional": False,
				},
				"Bed volume": {
					"Value": {
						"inserted_value": "bed_volume",
						"type": {float,int,},
						"dimension": "volume",
					},
					"description": "Total adsorbent bed volume required across all beds, including void volume.",
					"optional": False,
				},
				"Adsorbent mass": {
					"Value": {
						"inserted_value": "adsorbent_mass",
						"type": {float,int,},
						"dimension": "mass",
					},
					"description": "Total mass of adsorbent required across all beds.",
					"optional": False,
				},
				"Adsorption time": {
					"Value": {
						"inserted_value": "adsorption_time",
						"type": {float,int,},
						"dimension": "time",
					},
					"description": "Duration of the PSA adsorption step.",
					"optional": False,
				},
				"Vessel steel mass": {
					"Value": {
						"inserted_value": "vessel_steel_mass",
						"type": {float,int,},
						"dimension": "mass",
					},
					"description": "Total steel mass of the bed pressure vessels (cylindrical "
								   "shell plus flat end caps), across all beds.",
					"optional": False,
				},
				"Pressure drop": {
					"Value": {
						"inserted_value": "pressure_drop",
						"type": {float,int,},
						"dimension": "pressure",
					},
					"description": "Gas-phase pressure drop across the single producing bed "
								   "(Ergun equation).",
					"optional": False,
				},
			},
		}

	def _run(self, dcf):
		self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, 'PSA_Plugin')

		self.calculate_psa()

		output_inserter_function(self.output_dict, self, dcf, 'PSA_Plugin')

	def calculate_psa(self):

		self.H2_molecular_weight = Quantity(2.016, 'g/mol')

		psa = self.input_dict_resolved['PSA']
		adsorbent = self.input_dict_resolved['PSA Adsorbent Parameters']
		finance = self.input_dict_resolved['Financial Input Values']

		material = psa['Material']['Value'] if 'Material' in psa else 'stainless_steel_316'
		number_of_beds = psa['Number of beds']['Value'].unit['-']

		# Bed sizing: H2/adsorbate mass balance, ideal-gas volumetric flow, single-bed-producer geometry -> adsorbent mass, bed volume, adsorption time, gas density.
		design_capacity = self.input_dict_resolved['Technical Operating Parameters and Specifications']['Plant design capacity']['Value'].unit['kg/s']
		feed_adsorbate_mole_fraction = psa['Feed adsorbate mole fraction']['Value'].unit['-']
		adsorbate_molar_mass = psa['Adsorbate molar mass']['Value'].unit['kg/mol']
		recovery = psa['Recovery']['Value'].unit['-']

		H2_product_molar_flow = design_capacity / self.H2_molecular_weight.unit['kg/mol']
		H2_feed_molar_flow = H2_product_molar_flow / recovery
		adsorbate_molar_flow = H2_feed_molar_flow * feed_adsorbate_mole_fraction / (1 - feed_adsorbate_mole_fraction)

		self.adsorbate_mass_flow = Quantity(adsorbate_molar_flow * adsorbate_molar_mass, 'kg/s')

		# Total (hydrogen + adsorbate) feed molar flow, from the binary feed's mole fraction.
		total_feed_molar_flow = H2_feed_molar_flow / (1 - feed_adsorbate_mole_fraction)

		operating_pressure = psa['Operating pressure']['Value'].unit['Pa']
		operating_temperature = psa['Operating temperature']['Value'].unit['K']

		molar_volume = GAS_CONSTANT * operating_temperature / operating_pressure  # ideal gas law, m3/mol
		volumetric_flow = total_feed_molar_flow * molar_volume  # m3/s

		average_molar_mass = ((1 - feed_adsorbate_mole_fraction) * self.H2_molecular_weight.unit['kg/mol']
							  + feed_adsorbate_mole_fraction * adsorbate_molar_mass)
		self.gas_density = Quantity(average_molar_mass / molar_volume, 'kg/m3')

		length_to_diameter_ratio = psa['Length to diameter ratio']['Value'].unit['-']
		feed_gas_velocity = psa['Feed gas velocity']['Value'].unit['m/s']

		# Single-bed producer: the one producing bed is sized for the full plant feed flow.
		cross_sectional_area = volumetric_flow / feed_gas_velocity  # m2
		self.bed_diameter = Quantity(math.sqrt(4 * cross_sectional_area / math.pi), 'm')
		self.bed_length = Quantity(length_to_diameter_ratio * self.bed_diameter.unit['m'], 'm')
		self.single_bed_volume = Quantity(cross_sectional_area * self.bed_length.unit['m'], 'm3')

		single_bed_adsorbent_mass = (self.single_bed_volume.unit['m3']
									 * adsorbent['Bulk density']['Value'].unit['kg/m3']
									 * (1 - adsorbent['Bed void fraction']['Value'].unit['-']))

		working_capacity = ((adsorbent['Adsorption uptake fraction']['Value'].unit['-']
							- adsorbent['Residual loading fraction']['Value'].unit['-'])
						   * adsorbent['Bed usage fraction']['Value'].unit['-'])

		# Invert the mass balance (mass adsorbed per cycle = mass flow x time = adsorbent mass x working capacity).
		adsorption_time = single_bed_adsorbent_mass * working_capacity / self.adsorbate_mass_flow.unit['kg/s']
		self.adsorption_time = Quantity(adsorption_time, 's')

		self.adsorbent_mass = Quantity(single_bed_adsorbent_mass * number_of_beds, 'kg')
		self.bed_volume = Quantity(self.single_bed_volume.unit['m3'] * number_of_beds, 'm3')

		# Shell thickness (ASME + wind/dead-load + corrosion allowance, rounded to standard plate), shared by steel mass and cost.
		operating_pressure_bar = psa['Operating pressure']['Value'].unit['bar'] 

		if operating_pressure_bar <= 1.35795:  
			design_pressure = 1.70275  
		elif operating_pressure_bar <= 69.96325:  
			u = math.log(operating_pressure_bar - 1.01325)
			design_pressure = math.exp(0.39300 + 0.924524 * u + 0.0015655 * u ** 2) + 1.01325  
		else:
			design_pressure = 1.1 * operating_pressure_bar - 0.101325  

		max_allowable_stress = ALLOWABLE_STRESS_BAR[material]

		weld_efficiency = psa['Weld efficiency']['Value'].unit['-'] if 'Weld efficiency' in psa else 0.85
		corrosion = CORROSION_ALLOWANCE_M[material]

		pressure_thickness = ((design_pressure - 1.01325) * self.bed_diameter.unit['m']
							  / (2 * max_allowable_stress * weld_efficiency - 1.2 * (design_pressure - 1.01325)))  # m

		wind_thickness = (0.01517 * (self.bed_diameter.unit['m'] + 0.4572) * self.bed_length.unit['m'] ** 2
							 / (max_allowable_stress * self.bed_diameter.unit['m'] ** 2)) # m

		# The required thickness as a function of height runs from the maximum at the bottom (pressure_thickness + wind_thickness) 
		# to the minimum at the top (pressure_thickness only). The average thickness is used for steel mass and cost.
		average_thickness = pressure_thickness + wind_thickness / 2.0  # m

		thickness_before_rounding = average_thickness + corrosion  # m

		for plate in STANDARD_PLATE_THICKNESS:
			if plate >= thickness_before_rounding - 1e-12:
				thickness = plate
				break
		else:
			thickness = math.ceil(thickness_before_rounding / 0.00635) * 0.00635  # next 1/4 in above table max

		self.shell_thickness = Quantity(thickness, 'm')

		# Vessel steel mass: cylindrical shell + two flat end caps, across all beds.
		steel_density = STEEL_DENSITY_KG_M3[material]

		shell_area = math.pi * self.bed_diameter.unit['m'] * self.bed_length.unit['m']  # m2
		heads_area = 2 * (math.pi * self.bed_diameter.unit['m'] ** 2 / 4)  # m2
		single_vessel_steel_volume = (shell_area + heads_area) * thickness  # m3

		single_vessel_steel_mass = single_vessel_steel_volume * steel_density  # kg

		self.vessel_steel_mass = Quantity(single_vessel_steel_mass * number_of_beds, 'kg')

		# PSA system cost: SSLW vessel purchase-cost correlation (CEPCI-escalated) plus adsorbent cost.
		weight = (math.pi * steel_density * thickness
				 * (self.bed_diameter.unit['m'] + thickness) * (self.bed_length.unit['m'] + 0.8 * self.bed_diameter.unit['m']))  # kg
		weight_lb = Quantity(weight, 'kg').unit['lb']

		ln_w = math.log(weight_lb)

		if weight_lb <= 1_000_000:  # weight range 1: 4,200-1,000,000 lb
			empty_vessel_cost = math.exp(8.9552 - 0.2330 * ln_w + 0.04333 * ln_w ** 2)
		else:  # weight range 2: 1,000,000+-2,500,000 lb
			empty_vessel_cost = math.exp(7.2756 - 0.18255 * ln_w + 0.02297 * ln_w ** 2)

		if weight_lb < 4200 or weight_lb > 2_500_000:
			print(f"Warning: PSA vessel weight ({weight_lb:,.0f} lb) is outside the cost "
				  f"correlation's validated range (4,200-2,500,000 lb). The resulting cost is "
				  f"an extrapolation and may be unreliable.")

		bed_length_m = self.bed_length.unit['m']

		if self.bed_diameter.unit['m'] <= 3.6576 and bed_length_m <= 12.192:  # aspect range 1: D<=12 ft, L<=40 ft
			platforms_ladders_cost = 2017.0 * self.bed_diameter.unit['m'] ** 0.73960 * bed_length_m ** 0.70684
		else:  # aspect range 2: D<=24 ft, L<=170 ft
			platforms_ladders_cost = 1655.0 * self.bed_diameter.unit['m'] ** 0.63316 * bed_length_m ** 0.80161

		F_M = MATERIAL_FACTOR[material]

		single_vessel_cost_CE500 = F_M * empty_vessel_cost + platforms_ladders_cost

		# CEPCI escalation from the correlation's calibration year (SSLW_BASE_YEAR,
		# CEPCI ~500) to the shared 'Current year for capital costs', using the
		# same Plant_Cost_Index.csv lookup table and nearest-year matching as
		# Inflation_Plugin.
		plant_cost_index = read_textfile('pyH2A.Lookup_Tables~Plant_Cost_Index.csv', delimiter = '\t')
		current_year = finance['Current year for capital costs']['Value'].unit['-']
		cepci_idx = fn.find_nearest(plant_cost_index, [current_year, SSLW_BASE_YEAR])
		cepci_current = plant_cost_index[:,1][cepci_idx[0]]
		cepci_base = plant_cost_index[:,1][cepci_idx[1]]

		single_vessel_cost = single_vessel_cost_CE500 * (cepci_current / cepci_base)

		self.vessel_cost = Quantity(single_vessel_cost * number_of_beds, 'USD')

		adsorbent_cost_per_kg = adsorbent['Adsorbent cost per kg']['Value'].unit['USD/kg']
		self.adsorbent_cost = Quantity(self.adsorbent_mass.unit['kg'] * adsorbent_cost_per_kg, 'USD')

		self.adsorbent_replacement_interval = adsorbent['Adsorbent replacement interval']['Value']

		self.psa_cost = Quantity(self.vessel_cost.unit['USD'] + self.adsorbent_cost.unit['USD'], 'USD')

		# Pressure drop across the single producing bed (Ergun equation).
		viscosity = psa['Feed gas viscosity']['Value'].unit['Pa*s']
		void_fraction = adsorbent['Bed void fraction']['Value'].unit['-']
		particle_diameter = adsorbent['Adsorbent particle diameter']['Value'].unit['m']
		density = self.gas_density.unit['kg/m3']

		viscous_term = (150 * viscosity * (1 - void_fraction) ** 2
						/ (void_fraction ** 3 * particle_diameter ** 2) * feed_gas_velocity)
		inertial_term = (1.75 * density * (1 - void_fraction)
						 / (void_fraction ** 3 * particle_diameter) * feed_gas_velocity ** 2)

		pressure_drop_per_length = viscous_term + inertial_term  # Pa/m

		self.pressure_drop = Quantity(pressure_drop_per_length * self.bed_length.unit['m'], 'Pa')

		if 'Maximum pressure drop per length' in psa:
			max_pressure_drop_per_length = psa['Maximum pressure drop per length']['Value'].unit['Pa/m']
		else:
			max_pressure_drop_per_length = 10000.0  # Pa/m, 0.1 bar/m default

		if pressure_drop_per_length > max_pressure_drop_per_length:
			print(f"Warning: PSA pressure drop per unit length "
				  f"({pressure_drop_per_length / 1e5:.4f} bar/m) exceeds the maximum allowable "
				  f"({max_pressure_drop_per_length / 1e5:.4f} bar/m). Consider decreasing "
				  f"'Feed gas velocity' to reduce pressure drop.")