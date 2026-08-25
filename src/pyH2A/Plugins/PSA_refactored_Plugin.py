from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity

class PSA_refactored_Plugin:
	'''Simulating pressure swing adsorption (PSA) for removal of a adsorbate gas
	'''

	def __init__(self, dcf, print_info, run = True):
		self._set_up(dcf)
		if run:
			self._run(dcf)

	def _set_up(self, dcf):

		self.functional_unit = dcf.functional_unit

		self.input_dict = {
			"Main Stream": {
							"Mass fraction": {
								"Value": {
									"type": {dict,},
									"bounds": (0, None),
								},
								"Unit": {
									"dimension": "dimensionless",
								},
								"optional": False,
								"description": "Mixture inlet mass fraction of each component."
							}, 
							"Peak mass flowrate": {
								"Value": {
									"type": {int,float,},
									"bounds": (0, None),
								},
								"Unit": {
									"dimension": "mass/time",
								},
								"optional": False,
								"description": "Mixture inlet mass flowrate."
							},    
			},			
			"PSA": {
				"Adsorbate": {
					"Value": {
						"type": {str,},
					},
					"optional": False,
					"description": "Species to adsorb"
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
					"description": "Duration of the PSA adsorption step to size the required adsorbent "
								   "inventory."
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
					"description": "Number of beds in the PSA system."
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
			"Reference PSA System": {
				"Reference bed volume": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "volume",
					},
					"optional": False,
					"description": "Adsorbent bed volume of the reference PSA system."
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
					"description": "Total cost of the reference PSA system."
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
								   "relative to the reference PSA system."
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
					"description": "Total cost of the PSA system, scaled from the reference PSA "
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

		print('adsorbent_mass', self.adsorbent_mass)
		print('bed_volume', self.bed_volume)
		print('psa_cost', self.psa_cost)

	def calculate_bed_volume(self):
		'''Calculation of required adsorbent mass and bed volume, across all beds.

		The adsorbate mass flow rate is used to size the adsorbent
		mass and volume of the single bed that is adsorbing at any given time
		(sized to process the full feed gas flow). Since the remaining beds are
		simultaneously cycling through regeneration, the total adsorbent mass and
		bed volume of the system are obtained by scaling the single-bed values by
		the number of beds.
		'''

		Adsorbate = self.input_dict_resolved['PSA']['Adsorbate']['Value']

		adsorbate_mass_flow_kg_per_s = (self.input_dict_resolved['Main Stream']['Peak mass flowrate']['Value'].unit['kg/s']
										*
										self.input_dict_resolved['Main Stream']['Mass fraction']['Value'][Adsorbate].unit['-'])

		adsorbate_kg_per_cycle_per_bed = (adsorbate_mass_flow_kg_per_s
									  * self.input_dict_resolved['PSA']['Adsorption time']['Value'].unit['s'])

		adsorbent_dict = self.input_dict_resolved['PSA Adsorbent Parameters']
		working_capacity = ((adsorbent_dict['Adsorption uptake fraction']['Value'].unit['-']
							- adsorbent_dict['Residual loading fraction']['Value'].unit['-'])
						   * adsorbent_dict['Bed usage fraction']['Value'].unit['-'])

		single_bed_adsorbent_mass_kg = adsorbate_kg_per_cycle_per_bed / working_capacity
		single_bed_volume_m3 = (single_bed_adsorbent_mass_kg / adsorbent_dict['Bulk density']['Value'].unit['kg/m3']
							/ (1 - adsorbent_dict['Bed void fraction']['Value'].unit['-']))

		number_of_beds = self.input_dict_resolved['PSA']['Number of beds']['Value'].unit['-']

		self.adsorbent_mass = Quantity(single_bed_adsorbent_mass_kg * number_of_beds, 'kg')
		self.bed_volume = Quantity(single_bed_volume_m3 * number_of_beds, 'm3')

	def calculate_psa_cost(self):
		'''Calculation of PSA system cost by scaling the reference PSA system
		cost to the required bed volume, using an exponential scaling factor.
		'''

		reference = self.input_dict_resolved['Reference PSA System']

		volume_ratio = self.bed_volume.unit['m3'] / reference['Reference bed volume']['Value'].unit['m3']
		scaling_factor = volume_ratio ** reference['Scaling exponent']['Value'].unit['-']

		self.psa_cost = Quantity(reference['Reference cost']['Value'].unit['USD'] * scaling_factor, 'USD')
