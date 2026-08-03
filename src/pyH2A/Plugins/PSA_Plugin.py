from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity

class PSA_Plugin:
	'''Simulating pressure swing adsorption (PSA) for removal of a contaminant gas
	(e.g. O2) from the hydrogen product stream and estimating PSA system cost.

	The feed gas is assumed to be a binary mixture of the contaminant gas and
	hydrogen only, i.e. the hydrogen mole fraction is always ``1 - contaminant
	mole fraction``.

	Parameters
	----------
	Technical Operating Parameters and Specifications > Plant design capacity > Value : float
		Plant design capacity, i.e. net hydrogen product delivered downstream of
		the PSA (mass of hydrogen/time).
	PSA > Contaminant mole fraction > Value : float
		Mole fraction of contaminant gas (e.g. O2) in the feed gas entering the
		PSA system. A binary feed is assumed, so the hydrogen mole fraction is
		``1 - contaminant mole fraction``.
	PSA > Contaminant molar mass > Value : float
		Molar mass of the contaminant gas (e.g. O2), used to convert its mole
		fraction into a mass flow rate.
	PSA > Recovery > Value : float
		Fraction of hydrogen entering the PSA that is recovered in the pure
		hydrogen product stream; the remainder is lost with the purge/vent
		stream together with the desorbed contaminant. Used to back-calculate
		the hydrogen feed rate required to deliver the plant design capacity.
	PSA > Adsorption time > Value : float
		Duration of the PSA adsorption step before bed regeneration is required,
		used to size the required adsorbent inventory.
	PSA > Number of beds > Value : float
		Number of adsorbent beds in the PSA system. At any time only one bed is
		adsorbing (sized to process the full feed gas flow) while the remaining
		beds cycle through regeneration (depressurization, purge,
		repressurization); total adsorbent inventory scales with the number of
		beds.
	PSA Adsorbent Parameters > Bed void fraction > Value : float
		Void fraction of the packed adsorbent bed.
	PSA Adsorbent Parameters > Bed usage fraction > Value : float
		Fraction of total bed adsorbent capacity effectively usable, accounting
		for the length of unused bed (LUB).
	PSA Adsorbent Parameters > Adsorption uptake fraction > Value : float
		Adsorbent equilibrium loading at adsorption pressure, in mass of
		contaminant gas adsorbed per mass of adsorbent.
	PSA Adsorbent Parameters > Purge fraction > Value : float
		Adsorbent residual loading remaining after the purge/regeneration step,
		in mass of contaminant gas per mass of adsorbent.
	PSA Adsorbent Parameters > Bulk density > Value : float
		Bulk density of the packed adsorbent.
	H2A Reference PSA System > Reference bed volume > Value : float
		Adsorbent bed volume of the H2A reference PSA system.
	H2A Reference PSA System > Reference cost > Value : float
		Total cost of the H2A reference PSA system.
	H2A Reference PSA System > Scaling exponent > Value : float
		Exponential scaling factor used to relate PSA cost to bed volume,
		relative to the H2A reference PSA system.

	Returns
	-------
	Direct Capital Costs - PSA System > PSA system cost > Value : float
		Total cost of the PSA system, scaled from the H2A reference PSA system
		cost based on the required adsorbent bed volume.
	PSA > Bed volume > Value : float
		Total adsorbent bed volume required across all beds, including void
		volume.
	PSA > Adsorbent mass > Value : float
		Total mass of adsorbent required across all beds.
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
				"Contaminant mole fraction": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, 1),
					},
					"Unit": {
						"dimension": "dimensionless",
					},
					"optional": False,
					"description": "Mole fraction of contaminant gas (e.g. O2) in the feed gas entering "
								   "the PSA system. A binary feed of contaminant gas and hydrogen is "
								   "assumed, so the hydrogen mole fraction is 1 - contaminant mole fraction."
				},
				"Contaminant molar mass": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "mass / substance",
					},
					"optional": False,
					"description": "Molar mass of the contaminant gas (e.g. O2), used to convert its "
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
								   "hydrogen product stream; the remainder is lost with the purge/vent "
								   "stream together with the desorbed contaminant."
				},
				"Adsorption time": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "time",
					},
					"optional": False,
					"description": "Duration of the PSA adsorption step before bed regeneration is "
								   "required, used to size the required adsorbent inventory."
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
					"description": "Number of adsorbent beds in the PSA system. At any time only one bed "
								   "is adsorbing (sized to process the full feed gas flow) while the "
								   "remaining beds cycle through regeneration; total adsorbent inventory "
								   "scales with the number of beds."
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
								   "contaminant gas adsorbed per mass of adsorbent."
				},
				"Purge fraction": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "dimensionless",
					},
					"optional": False,
					"description": "Adsorbent residual loading remaining after the purge/regeneration "
								   "step, in mass of contaminant gas per mass of adsorbent."
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
			"H2A Reference PSA System": {
				"Reference bed volume": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "volume",
					},
					"optional": False,
					"description": "Adsorbent bed volume of the H2A reference PSA system."
				},
				"Reference cost": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "currency",
					},
					"optional": False,
					"description": "Total cost of the H2A reference PSA system."
				},
				"Scaling exponent": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "dimensionless",
					},
					"optional": False,
					"description": "Exponential scaling factor used to relate PSA cost to bed volume, "
								   "relative to the H2A reference PSA system."
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
					"description": "Total cost of the PSA system, scaled from the H2A reference PSA "
								   "system cost based on the required adsorbent bed volume.",
					"optional": False,
				}
			},
			"PSA": {
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
			},
		}

	def _run(self, dcf):
		self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, 'PSA_Plugin')

		self.calculate_bed_volume()
		self.calculate_psa_cost()

		output_inserter_function(self.output_dict, self, dcf, 'PSA_Plugin')

	def calculate_bed_volume(self):
		'''Calculation of required adsorbent mass and bed volume, across all beds.

		The contaminant mass flow rate entering the PSA system is derived from
		plant hydrogen design capacity, PSA recovery and contaminant mole
		fraction. Plant design capacity is the net hydrogen product delivered
		downstream of the PSA. Since a fraction of the hydrogen entering the PSA
		is lost with the purge/vent stream, the hydrogen feed rate is scaled up
		by the recovery to obtain the actual hydrogen molar flow entering the
		PSA. A binary feed of contaminant gas and hydrogen is assumed, so the
		molar flow of contaminant gas is derived from that feed hydrogen molar
		flow via
		``contaminant_moles = H2_feed_moles * contaminant_mole_fraction / (1 - contaminant_mole_fraction)``.

		The resulting contaminant mass flow rate is used to size the adsorbent
		mass and volume of the single bed that is adsorbing at any given time
		(sized to process the full feed gas flow). Since the remaining beds are
		simultaneously cycling through regeneration, the total adsorbent mass and
		bed volume of the system are obtained by scaling the single-bed values by
		the number of beds.
		'''

		self.H2_molecular_weight = Quantity(2.016, 'g/mol')

		psa = self.input_dict_resolved['PSA']
		adsorbent = self.input_dict_resolved['PSA Adsorbent Parameters']

		design_capacity = self.input_dict_resolved['Technical Operating Parameters and Specifications']['Plant design capacity']['Value'].unit['kg/s']
		contaminant_mole_fraction = psa['Contaminant mole fraction']['Value'].unit['-']
		contaminant_molar_mass = psa['Contaminant molar mass']['Value'].unit['kg/mol']
		recovery = psa['Recovery']['Value'].unit['-']

		H2_product_molar_flow = design_capacity / self.H2_molecular_weight.unit['kg/mol']
		H2_feed_molar_flow = H2_product_molar_flow / recovery
		contaminant_molar_flow = H2_feed_molar_flow * contaminant_mole_fraction / (1 - contaminant_mole_fraction)

		self.contaminant_mass_flow = Quantity(contaminant_molar_flow * contaminant_molar_mass, 'kg/s')

		contaminant_mass_per_cycle = (self.contaminant_mass_flow.unit['kg/s']
									  * psa['Adsorption time']['Value'].unit['s'])

		working_capacity = ((adsorbent['Adsorption uptake fraction']['Value'].unit['-']
							- adsorbent['Purge fraction']['Value'].unit['-'])
						   * adsorbent['Bed usage fraction']['Value'].unit['-'])

		single_bed_adsorbent_mass = contaminant_mass_per_cycle / working_capacity
		single_bed_volume = (single_bed_adsorbent_mass / adsorbent['Bulk density']['Value'].unit['kg/m3']
							/ (1 - adsorbent['Bed void fraction']['Value'].unit['-']))

		number_of_beds = psa['Number of beds']['Value'].unit['-']

		self.adsorbent_mass = Quantity(single_bed_adsorbent_mass * number_of_beds, 'kg')
		self.bed_volume = Quantity(single_bed_volume * number_of_beds, 'm3')

	def calculate_psa_cost(self):
		'''Calculation of PSA system cost by scaling the H2A reference PSA system
		cost to the required bed volume, using an exponential scaling factor.
		'''

		reference = self.input_dict_resolved['H2A Reference PSA System']

		volume_ratio = self.bed_volume.unit['m3'] / reference['Reference bed volume']['Value'].unit['m3']
		scaling_factor = volume_ratio ** reference['Scaling exponent']['Value'].unit['-']

		self.psa_cost = Quantity(reference['Reference cost']['Value'].unit['USD'] * scaling_factor, 'USD')
