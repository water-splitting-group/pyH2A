import math

from scipy.constants import R as GAS_CONSTANT

from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity

class PSA_Plugin:
	'''Simulating pressure swing adsorption (PSA) for removal of a adsorbate gas
	(e.g. O2) from the hydrogen product stream and estimating PSA system cost.

	The feed gas is assumed to be a binary mixture of the adsorbate gas and
	hydrogen only, i.e. the hydrogen mole fraction is always ``1 - adsorbate
	mole fraction``.

	This model assumes a single-bed producer: at any given time, exactly one
	bed is in the adsorption step and is sized to process the full plant
	feed flow, while every other bed cycles through regeneration
	(depressurization, purge, repressurization). See :meth:`calculate_bed_volume`.

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
		hydrogen product stream; the remainder is lost with the purge/vent
		stream together with the desorbed adsorbate. Used to back-calculate
		the hydrogen feed rate required to deliver the plant design capacity.
	PSA > Operating pressure > Value : float
		Absolute pressure of the feed gas entering the PSA bed, used with
		``Operating temperature`` (ideal gas law) to convert the feed's molar
		flow rate into a volumetric flow rate for bed sizing.
	PSA > Operating temperature > Value : float
		Absolute temperature of the feed gas entering the PSA bed, used with
		``Operating pressure`` (ideal gas law) to convert the feed's molar
		flow rate into a volumetric flow rate for bed sizing.
	PSA > Feed gas velocity > Value : float
		Assumed feed gas superficial velocity through the bed, used to size
		bed cross-sectional area (= volumetric feed flow / velocity), see
		:meth:`calculate_bed_volume`.
	PSA > Length to diameter ratio > Value : float
		Assumed bed length-to-diameter (L/D) ratio, used together with the
		bed cross-sectional area (from feed gas velocity, see
		:meth:`calculate_bed_volume`) to fix bed geometry and back-calculate
		adsorption time.
	PSA > Number of beds > Value : float
		Total number of adsorbent beds in the PSA system. This model assumes
		a single-bed producer: only one bed is ever in the adsorption step
		at any given time (sized to process the full plant feed flow), while
		the remaining beds cycle through regeneration (depressurization,
		purge, repressurization). Total adsorbent inventory (bed volume,
		adsorbent mass) scales with the total number of beds, but the
		producing bed's own sizing and the resulting adsorption time do not.
	PSA > Steel density > Value : float
		Density of the vessel (bed shell) steel, used to convert vessel wall
		thickness and geometry into total steel mass, see
		:meth:`calculate_vessel_steel_mass`.
	PSA Costing > CEPCI base > Value : float
		Chemical Engineering Plant Cost Index for the base year that the
		Turton et al. vessel-costing correlation constants (K1, K2, K3, B1,
		B2, F_M) are regressed against, used to escalate the correlation's
		base-year cost estimate to the cost basis of ``CEPCI current``, see
		:meth:`calculate_psa_cost`.
	PSA Costing > CEPCI current > Value : float
		Chemical Engineering Plant Cost Index for the cost basis the PSA
		system cost should be expressed in, see :meth:`calculate_psa_cost`.
	PSA Costing > Adsorbent cost per kg > Value : float
		Cost of the adsorbent material per unit mass, used together with
		``Adsorbent mass`` to calculate total adsorbent cost, see
		:meth:`calculate_psa_cost`.
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

	Returns
	-------
	Direct Capital Costs - PSA System > PSA system cost > Value : float
		Total cost of the PSA system: vessel bare module cost (Turton et
		al. equipment-costing correlation, escalated from ``CEPCI base`` to
		``CEPCI current``) plus adsorbent cost (``Adsorbent mass`` x
		``Adsorbent cost per kg``), see :meth:`calculate_psa_cost`.
	PSA > Vessel cost > Value : float
		Bare module cost of the pressure vessels (all beds), from the
		Turton et al. correlation, escalated to the ``CEPCI current`` cost
		basis, see :meth:`calculate_psa_cost`.
	PSA > Adsorbent cost > Value : float
		Cost of the adsorbent (all beds): ``Adsorbent mass`` x
		``Adsorbent cost per kg``.
	PSA > Bed volume > Value : float
		Total adsorbent bed volume required across all beds, including void
		volume.
	PSA > Adsorbent mass > Value : float
		Total mass of adsorbent required across all beds.
	PSA > Adsorption time > Value : float
		Duration of the PSA adsorption step before bed regeneration is
		required.
	PSA > Vessel steel mass > Value : float
		Total steel mass of the bed pressure vessels (cylindrical shell plus
		flat end caps), across all beds, see
		:meth:`calculate_vessel_steel_mass`.
	'''

	def __init__(self, dcf, print_info, run = True):
		self._set_up(dcf)
		if run:
			self._run(dcf)

	def _set_up(self, dcf):

		self.functional_unit = dcf.functional_unit

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
					"description": "Plant design capacity, i.e. net hydrogen product delivered downstream "
								   "of the PSA, in mass of hydrogen/time."
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
						"bounds": (0, None),
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
					"description": "Assumed bed length-to-diameter (L/D) ratio, used together with the "
								   "bed cross-sectional area (from feed gas velocity) to fix bed geometry "
								   "and back-calculate adsorption time."
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
				"Steel density": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "mass / volume",
					},
					"optional": False,
					"description": "Density of the vessel (bed shell) steel, used together with "
								   "vessel wall thickness and geometry to calculate total vessel "
								   "steel mass, see :meth:`calculate_vessel_steel_mass`."
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
			},
			"PSA Costing": {
				"CEPCI base": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "dimensionless",
					},
					"optional": False,
					"description": "Chemical Engineering Plant Cost Index for the base year that the "
								   "Turton et al. vessel-costing correlation constants are regressed "
								   "against, used to escalate the correlation's base-year cost estimate."
				},
				"CEPCI current": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "dimensionless",
					},
					"optional": False,
					"description": "Chemical Engineering Plant Cost Index for the cost basis the PSA "
								   "system cost should be expressed in."
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
					"description": "Cost of the adsorbent material per unit mass, used together with "
								   "Adsorbent mass to calculate total adsorbent cost."
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
					"description": "Total cost of the PSA system: vessel bare module cost (Turton "
								   "et al. correlation, CEPCI-escalated) plus adsorbent cost.",
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
					"description": "Bare module cost of the pressure vessels (all beds), from the "
								   "Turton et al. correlation, escalated to the CEPCI current cost basis.",
					"optional": False,
				},
				"Adsorbent cost": {
					"Value": {
						"inserted_value": "adsorbent_cost",
						"type": {float,int,},
						"dimension": "currency",
					},
					"description": "Cost of the adsorbent (all beds): Adsorbent mass x Adsorbent cost per kg.",
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
					"description": "Duration of the PSA adsorption step, back-calculated from the "
								   "declared feed gas velocity and bed length-to-diameter ratio.",
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
			},
		}

	def _run(self, dcf):
		self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, 'PSA_Plugin')

		self.calculate_bed_volume()
		self.calculate_vessel_steel_mass()
		self.calculate_psa_cost()

		output_inserter_function(self.output_dict, self, dcf, 'PSA_Plugin')

	def calculate_bed_volume(self):
		'''Calculation of required adsorbent mass, bed volume, and adsorption time, across all beds.

		The adsorbate mass flow rate entering the PSA system is derived from
		plant hydrogen design capacity, PSA recovery and adsorbate mole
		fraction. Plant design capacity is the net hydrogen product delivered
		downstream of the PSA. Since a fraction of the hydrogen entering the PSA
		is lost with the purge/vent stream, the hydrogen feed rate is scaled up
		by the recovery to obtain the actual hydrogen molar flow entering the
		PSA.

		Bed geometry (cross-sectional area, diameter, length) is sized from the
		total (hydrogen + adsorbate) feed's volumetric flow rate -- obtained
		from its molar flow rate via the ideal gas law using the declared
		operating pressure and temperature -- combined with the declared feed
		gas superficial velocity (cross-sectional area = volumetric
		flow / velocity) and the declared bed length-to-diameter ratio
		(length = L/D x diameter). This geometry is independent of adsorption
		time: for a fixed cross-sectional area and velocity, any adsorption time
		is self-consistent with a proportionally sized bed length, so velocity
		alone cannot determine a unique adsorption time without also fixing the
		length-to-diameter ratio.

		This model assumes a single-bed producer: exactly one bed is in the
		adsorption step at any given time, and that bed alone is sized to
		process the full plant feed flow (see :meth:`_set_up`/class
		docstring). With bed volume fixed by that geometry, the required
		adsorbent mass of the producing bed follows from the bed's bulk
		density and void fraction. Adsorption time is then back-calculated
		from that adsorbent mass, the (full) adsorbate mass flow rate, and
		the adsorbent's working capacity, by inverting the mass balance
		(mass adsorbed per cycle = adsorbate mass flow rate x adsorption
		time = adsorbent mass x working capacity). Every bed in the system
		-- whether currently producing or cycling through regeneration -- is
		physically identical, so the total adsorbent mass and bed volume of
		the system are obtained by scaling the single-bed values by the
		total number of beds.
		'''

		self.H2_molecular_weight = Quantity(2.016, 'g/mol')

		psa = self.input_dict_resolved['PSA']
		adsorbent = self.input_dict_resolved['PSA Adsorbent Parameters']

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

		length_to_diameter_ratio = psa['Length to diameter ratio']['Value'].unit['-']
		feed_gas_velocity = psa['Feed gas velocity']['Value'].unit['m/s']

		# Single-bed producer: the one producing bed is sized for the full plant feed flow.
		cross_sectional_area = volumetric_flow / feed_gas_velocity  # m2
		diameter = math.sqrt(4 * cross_sectional_area / math.pi)  # m
		length = length_to_diameter_ratio * diameter  # m
		single_bed_volume = cross_sectional_area * length  # m3

		self.bed_diameter = Quantity(diameter, 'm')
		self.bed_length = Quantity(length, 'm')
		self.single_bed_volume = Quantity(single_bed_volume, 'm3')

		single_bed_adsorbent_mass = (single_bed_volume
									 * adsorbent['Bulk density']['Value'].unit['kg/m3']
									 * (1 - adsorbent['Bed void fraction']['Value'].unit['-']))

		working_capacity = ((adsorbent['Adsorption uptake fraction']['Value'].unit['-']
							- adsorbent['Residual loading fraction']['Value'].unit['-'])
						   * adsorbent['Bed usage fraction']['Value'].unit['-'])

		# Invert the mass balance (mass adsorbed per cycle = mass flow x time = adsorbent mass x working capacity).
		adsorption_time_s = single_bed_adsorbent_mass * working_capacity / self.adsorbate_mass_flow.unit['kg/s']
		self.adsorption_time = Quantity(adsorption_time_s, 's')

		number_of_beds = psa['Number of beds']['Value'].unit['-']

		self.adsorbent_mass = Quantity(single_bed_adsorbent_mass * number_of_beds, 'kg')
		self.bed_volume = Quantity(single_bed_volume * number_of_beds, 'm3')

	def calculate_vessel_steel_mass(self):
		'''Calculation of pressure vessel (bed shell) steel mass, across all beds.

		Wall thickness of a single bed's pressure vessel is calculated from
		the thin-wall (hoop stress) pressure vessel formula,
		``t = P x D / (2 x S)``, using the declared operating pressure, the
		bed diameter (from :meth:`calculate_bed_volume`), and a fixed
		allowable stress of 115 MPa (ASME SA-240 316L austenitic stainless
		steel at near-ambient temperature). 316L is used rather than carbon
		steel because the process gas here is an oxygen-bearing mixture:
		carbon steel is prone to ignition in oxygen-enriched atmospheres
		(particle-impact and adiabatic-compression ignition), whereas 316L
		has a substantially higher autoignition resistance and is a standard
		material choice for oxygen service (see CGA G-4.4 / ASTM G88).
		Steel volume of a single vessel is
		approximated as the cylindrical shell wall (circumference x length x
		thickness) plus two flat circular end caps of the same thickness,
		converted to mass via the declared steel density. Since every bed in
		the system needs its own vessel, the total steel mass scales with
		the total number of beds.
		'''

		self.allowable_stress = Quantity(115.0, 'MPa')

		psa = self.input_dict_resolved['PSA']

		operating_pressure = psa['Operating pressure']['Value'].unit['Pa']
		steel_density = psa['Steel density']['Value'].unit['kg/m3']
		diameter = self.bed_diameter.unit['m']
		length = self.bed_length.unit['m']

		wall_thickness = (operating_pressure * diameter) / (2 * self.allowable_stress.unit['Pa'])  # m

		shell_area = math.pi * diameter * length  # m2
		heads_area = 2 * (math.pi * diameter ** 2 / 4)  # m2
		single_vessel_steel_volume = (shell_area + heads_area) * wall_thickness  # m3

		single_vessel_steel_mass = single_vessel_steel_volume * steel_density  # kg

		number_of_beds = psa['Number of beds']['Value'].unit['-']

		self.vessel_steel_mass = Quantity(single_vessel_steel_mass * number_of_beds, 'kg')

	def calculate_psa_cost(self):
		'''Calculation of PSA system cost: vessel bare module cost (Turton et
		al. equipment-costing correlation) plus adsorbent cost.

		Vessel purchased cost follows the Turton et al. correlation for a
		process vessel, ``C_P = 10^(K1 + K2 x LC + K3 x LC^2)`` where
		``LC = log10(single-bed volume in m3)``, with K1, K2, K3 fixed
		regression constants for the vertical process vessel equipment
		category (see :class:`PSA_Plugin` docstring). This is corrected to a
		bare module cost via ``C_BM = C_P x (B1 + B2 x F_M x F_P)``, where
		B1, B2 are fixed bare-module constants, F_M = 3.1 is the material
		factor for stainless steel (consistent with the 316L vessel material
		chosen in :meth:`calculate_vessel_steel_mass` for oxygen service),
		and F_P is a pressure correction factor. F_P requires *gauge*
		pressure, so the declared (absolute) operating pressure is converted
		by subtracting standard atmospheric pressure (1.01325 bar); per the
		Turton correlation's convention, F_P is floored at 1.0 (it is not
		allowed to reduce cost below the ambient-pressure base case). The
		bare module cost of one vessel is multiplied by the total number of
		beds (one vessel per bed) for the total vessel cost at the
		correlation's base-year cost basis, then escalated to the declared
		``CEPCI current`` basis via the ratio to ``CEPCI base``.

		Adsorbent cost is simply ``Adsorbent mass x Adsorbent cost per kg``
		(no CEPCI escalation, since this is a direct current-cost input, not
		a historically-correlated estimate). Total PSA system cost is the
		sum of vessel and adsorbent cost.
		'''

		# Turton et al. correlation constants for a vertical process vessel;
		# F_M corresponds to stainless steel construction.
		K1, K2, K3 = 3.4974, 0.4485, 0.1074
		B1, B2 = 2.25, 1.82
		F_M = 3.1

		psa = self.input_dict_resolved['PSA']
		costing = self.input_dict_resolved['PSA Costing']

		LC = math.log10(self.single_bed_volume.unit['m3'])
		C_P = 10 ** (K1 + K2 * LC + K3 * LC ** 2)

		# F_P needs gauge pressure; Operating pressure is declared as absolute.
		operating_pressure_barg = psa['Operating pressure']['Value'].unit['bar'] - 1.01325
		diameter = self.bed_diameter.unit['m']

		F_P = ((operating_pressure_barg * diameter) / (2 * (850 - 0.6 * operating_pressure_barg)) + 0.00315) / 0.0063
		F_P = max(F_P, 1.0)  # Turton convention: F_P cannot reduce cost below the ambient-pressure base case.

		C_BM = C_P * (B1 + B2 * F_M * F_P)

		number_of_beds = psa['Number of beds']['Value'].unit['-']
		vessel_cost_base_year = number_of_beds * C_BM

		cepci_base = costing['CEPCI base']['Value'].unit['-']
		cepci_current = costing['CEPCI current']['Value'].unit['-']

		self.vessel_cost = Quantity(vessel_cost_base_year * (cepci_current / cepci_base), 'USD')

		adsorbent_cost_per_kg = costing['Adsorbent cost per kg']['Value'].unit['USD/kg']
		self.adsorbent_cost = Quantity(self.adsorbent_mass.unit['kg'] * adsorbent_cost_per_kg, 'USD')

		self.psa_cost = Quantity(self.vessel_cost.unit['USD'] + self.adsorbent_cost.unit['USD'], 'USD')
