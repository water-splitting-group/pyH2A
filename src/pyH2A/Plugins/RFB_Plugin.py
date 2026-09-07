import numpy as np
from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity

class RFB_Plugin:
	'''Calculation of Redox Flow Battery amount of electrolytes and their total impact, as well as the number of stack cells.
				
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
					"description": "Dictionary containing all time-related quantities."
				}, 
			},  	
			"Battery": {	
				"Power": {
					"Value": {
						"type": {float, int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "power",
					},
					"description": "Total power of the battery."
				},						
				"Gross capacity": {
					"Value": {
						"type": {float, int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "energy",
					},
					"description": "Capacity of the battery if full charge and discharge of the electrolyte were allowed."
				},						
			},
			"Battery Cell Stack": {		
				"Power per cell stack": {
					"Value": {
						"type": {float, int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "power",
					},
					"description": "Power of each stack."
				},		
				"Lifetime": {
					"Value": {
						"type": {float, int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "time",
					},
					"description": "Lifetime duration of each stack."
				},																				
			},			
			"Battery Electrolyte": {	
				"Energy density": {
					"Value": {
						"type": {float, int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "energy/mass",
					},
					"description": "Capacity per mass of electrolyte."
				},	
				"Fraction of electrolyte to replace per year": {
									"Value": {
										"type": {float, int,},
										"bounds": (0, None), # no upper bound: it is theoretically possible that the turn over frequency is higher than 1/year.
									},
									"Unit": {
										"dimension": "dimensionless",
									},
									"description": "Fraction of the electrolyte holdup that is replaced per year. The fresh electrolyte can be produced form scratch, or obtained by regeneration."
								},
				"Fraction of replaced electrolyte to produce per year": {
					"Value": {
						"type": {float, int,},
						"bounds": (0, 1), 
					},
					"Unit": {
						"dimension": "dimensionless",
					},
					"description": "Fraction of the replacement electrolyte that must be produced. The complement is regenerated"
				},
				"Electrolyte density": {
					"Value": {
						"type": {float, int,},
						"bounds": (0, None), 
					},
					"Unit": {
						"dimension": "mass/volume",
					},
					"description": "Density of the electrolytes. Used to assess the volume of electrolytes."
				},																				
			},
			"Battery Periphery": {	
				"Number of periphery items": {
					"Value": {
						"type": {float, int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "dimensionless",
					},
					"description": "Lumped system of pumps, cables, piping..."
				},
			},	
			"RFB Specific Impacts": {
				"Stack": {
					"GWP_Value": {
						"type": {int, float},
						"bounds": (0, None),
					},
					"GWP_Unit": {
						"dimension": "mass" 
					},	
					"Energy_Value": {
						"type": {int, float},
						"bounds": (0, None),
					},
					"Energy_Unit": {
						"dimension": "energy" 
					},		
					"Toxicity_Value": {
						"type": {int, float},
						"bounds": (0, None),
					},
					"Toxicity_Unit": {
						"dimension": "dimensionless" 
					},		
					"Resource_use_Value": {
						"type": {int, float},
						"bounds": (0, None),
					},
					"Resource_use_Unit": {
						"dimension": "mass" 
					},														
					"description": "Impact per stack."
				}, 
				"Electrolyte": {
					"GWP_Value": {
						"type": {int, float},
						"bounds": (0, None),
					},
					"GWP_Unit": {
						"dimension": "mass/mass" 
					},	
					"Energy_Value": {
						"type": {int, float},
						"bounds": (0, None),
					},
					"Energy_Unit": {
						"dimension": "energy/mass" 
					},		
					"Toxicity_Value": {
						"type": {int, float},
						"bounds": (0, None),
					},
					"Toxicity_Unit": {
						"dimension": "1/mass" 
					},		
					"Resource_use_Value": {
						"type": {int, float},
						"bounds": (0, None),
					},
					"Resource_use_Unit": {
						"dimension": "mass/mass" 
					},														
					"description": "Impact per mass of electrolyte."
				}, 	
				"Periphery": {
					"GWP_Value": {
						"type": {int, float},
						"bounds": (0, None),
					},
					"GWP_Unit": {
						"dimension": "mass" 
					},	
					"Energy_Value": {
						"type": {int, float},
						"bounds": (0, None),
					},
					"Energy_Unit": {
						"dimension": "energy" 
					},		
					"Toxicity_Value": {
						"type": {int, float},
						"bounds": (0, None),
					},
					"Toxicity_Unit": {
						"dimension": "dimensionless" 
					},		
					"Resource_use_Value": {
						"type": {int, float},
						"bounds": (0, None),
					},
					"Resource_use_Unit": {
						"dimension": "mass" 
					},														
					"description": "Impact per periphery item."
				}, 
				"Steel": {
					"GWP_Value": {
						"type": {int, float},
						"bounds": (0, None),
					},
					"GWP_Unit": {
						"dimension": "mass/mass" 
					},	
					"Energy_Value": {
						"type": {int, float},
						"bounds": (0, None),
					},
					"Energy_Unit": {
						"dimension": "energy/mass" 
					},		
					"Toxicity_Value": {
						"type": {int, float},
						"bounds": (0, None),
					},
					"Toxicity_Unit": {
						"dimension": "1/mass" 
					},		
					"Resource_use_Value": {
						"type": {int, float},
						"bounds": (0, None),
					},
					"Resource_use_Unit": {
						"dimension": "mass/mass" 
					},														
					"description": "Impact per mass of steel."
				}, 								
			},  					
		}

		self.output_dict = {		
			"Battery Cell Stack": {
				"Number of cell stacks": {
					"Value": {
						"inserted_value": "number_cell_stacks",
						"type": {float,},
						"dimension": "dimensionless",
					},
					"description": "Number of cell stacks to provide the required power.",
				},	
				"Number of cell stacks over lifetime": {
					"Value": {
						"inserted_value": "total_stack",
						"type": {float,},
						"dimension": "dimensionless",
					},
					"description": "Number of cell stacks needed over the lifetime of the battery, accounting for replacement.",
				},					
			},			
			"Battery Electrolyte": {
				"Initial amount": {
					"Value": {
						"inserted_value": "initial_electrolyte_amount",
						"type": {float,},
						"dimension": "mass",
					},
					"description": "Mass of electrolyte present in the battery upon startup.",
				},
				"Amount over lifetime": {
					"Value": {
						"inserted_value": "total_electrolyte",
						"type": {float,},
						"dimension": "mass",
					},
					"description": "Mass of electrolyte to produce during the entire battery lifetime.",
				},					
			},	
			"RFB Lifetime Impacts": {
				"Stack": {
					"GWP_Value": {
						"inserted_value": "total_stack_gwp",
						"type": {float,},
						"dimension": "mass",
					},
					"Energy_Value": {
						"inserted_value": "total_stack_energy",
						"type": {float,},
						"dimension": "energy",
					},		
					"Toxicity_Value": {
						"inserted_value": "total_stack_toxicity",
						"type": {float,},
						"dimension": "dimensionless",
					},		
					"Resource_use_Value": {
						"inserted_value": "total_stack_resource_use",
						"type": {float,},
						"dimension": "mass",
					},													
					"description": "Impact of the stacks for the entire the battery lifetime.",
				},
				"Electrolyte": {
					"GWP_Value": {
						"inserted_value": "total_electrolyte_gwp",
						"type": {float,},
						"dimension": "mass",
					},
					"Energy_Value": {
						"inserted_value": "total_electrolyte_energy",
						"type": {float,},
						"dimension": "energy",
					},		
					"Toxicity_Value": {
						"inserted_value": "total_electrolyte_toxicity",
						"type": {float,},
						"dimension": "dimensionless",
					},		
					"Resource_use_Value": {
						"inserted_value": "total_electrolyte_resource_use",
						"type": {float,},
						"dimension": "mass",
					},													
					"description": "Impact of the electrolyte for the entire the battery lifetime.",
				},	
				"Periphery": {
					"GWP_Value": {
						"inserted_value": "total_periphery_gwp",
						"type": {float,},
						"dimension": "mass",
					},
					"Energy_Value": {
						"inserted_value": "total_periphery_energy",
						"type": {float,},
						"dimension": "energy",
					},		
					"Toxicity_Value": {
						"inserted_value": "total_periphery_toxicity",
						"type": {float,},
						"dimension": "dimensionless",
					},		
					"Resource_use_Value": {
						"inserted_value": "total_periphery_resource_use",
						"type": {float,},
						"dimension": "mass",
					},													
					"description": "Impact of the periphery for the entire the battery lifetime.",
				},
				"Steel": {
					"GWP_Value": {
						"inserted_value": "total_steel_gwp",
						"type": {float,},
						"dimension": "mass",
					},
					"Energy_Value": {
						"inserted_value": "total_steel_energy",
						"type": {float,},
						"dimension": "energy",
					},		
					"Toxicity_Value": {
						"inserted_value": "total_steel_toxicity",
						"type": {float,},
						"dimension": "dimensionless",
					},		
					"Resource_use_Value": {
						"inserted_value": "total_steel_resource_use",
						"type": {float,},
						"dimension": "mass",
					},													
					"description": "Impact of the steel for the entire the battery lifetime.",
				},		
				"Battery": {
					"GWP_Value": {
						"inserted_value": "total_battery_gwp",
						"type": {float,},
						"dimension": "mass",
					},
					"Energy_Value": {
						"inserted_value": "total_battery_energy",
						"type": {float,},
						"dimension": "energy",
					},		
					"Toxicity_Value": {
						"inserted_value": "total_battery_toxicity",
						"type": {float,},
						"dimension": "dimensionless",
					},		
					"Resource_use_Value": {
						"inserted_value": "total_battery_resource_use",
						"type": {float,},
						"dimension": "mass",
					},													
					"description": "Impact of the battery for its entire lifetime.",
				},												
			},			
		}



	def _run(self, dcf):

		self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, 'RFB_Plugin')

		self.calculate_electrolyte()
		self.calculate_stack()
		self.calculate_periphery()
		self.calculate_impact()

		output_inserter_function(self.output_dict, self, dcf, 'RFB_Plugin') 


	def calculate_electrolyte(self):

		self.initial_electrolyte_amount = Quantity(
												self.input_dict_resolved['Battery']['Gross capacity']['Value'].unit['J']
												/
												self.input_dict_resolved['Battery Electrolyte']['Energy density']['Value'].unit['J/kg'], 
												'kg')

		# Assumption: the fraction of fresh electrolyte to inject each year is fixed
		yearly_electrolyte_needed_kg = (self.input_dict_resolved['Battery Electrolyte']['Fraction of electrolyte to replace per year']['Value'].unit['-']
										*
										self.initial_electrolyte_amount.unit['kg'])

		yearly_electrolyte_produced_kg = (yearly_electrolyte_needed_kg
										 *
										 self.input_dict_resolved['Battery Electrolyte']['Fraction of replaced electrolyte to produce per year']['Value'].unit['-'])

		self.total_electrolyte = Quantity(
												np.sum(self.input_dict_resolved['Time']['Years']['Value']['Operation years ones'].unit['-']) # this assumes that the renewal occurs continuously all along the year. 
												*																						# If we considered that the renewal occurs as a discrete refilling at the beginning of each new  year, we would need the number of years - 1 
												yearly_electrolyte_produced_kg
												+
												self.initial_electrolyte_amount.unit['kg']
												, 
												'kg')

		# The amount of steel for tanks assumes tanks of the same size as in the following paper
		# "Life cycle assessment of an industrial-scale vanadium flow battery, Blume et al (2022), DOI: 10.1111/jiec.13328"
		# but with a number of tanks proportional to the volume of electrolytes

		# Hardcoded values obtained from the article
		reference_capacity_MWh = 8
		reference_density_kg_per_m3 = 1350 # 506746 kg / 375.4 m3
		reference_tank_steel_kg = 264622
		self.total_steel = Quantity(
							reference_tank_steel_kg 
							* 
							self.input_dict_resolved['Battery']['Gross capacity']['Value'].unit['MWh']
							/
							reference_capacity_MWh
							*
							reference_density_kg_per_m3
							/
							self.input_dict_resolved['Battery Electrolyte']['Electrolyte density']['Value'].unit['kg/m3'], 
							'kg')


	def calculate_stack(self):

		self.number_cell_stacks = Quantity(
										self.input_dict_resolved['Battery']['Power']['Value'].unit['W']
										/
										self.input_dict_resolved['Battery Cell Stack']['Power per cell stack']['Value'].unit['W'], 
										'-'
										)

		self.total_stack = Quantity(
										self.number_cell_stacks.unit['-']
										*
										(np.sum(self.input_dict_resolved['Time']['Years']['Value']['Operation years ones'].unit['-'])
										//
										self.input_dict_resolved['Battery Cell Stack']['Lifetime']['Value'].unit['year']
										), 
										'-'
										)

	def calculate_periphery(self):
		''' Simply pick up the dictionary entry to generate a variable with the same standard name as the other elements'''
		self.total_periphery = self.input_dict_resolved['Battery Periphery']['Number of periphery items']['Value']


	def calculate_impact(self):
		'''Double loop generating each impact of each element, and summing up the total elments contributiuons for each impact'''

		impact_categories = {'GWP': 'kg', 'Energy': 'J', 'Resource_use': 'kg', 'Toxicity': '-'}
		for impact_name, impact_unit in impact_categories.items():
			grand_total = 0
			for subsystem_name in self.input_dict_resolved['RFB Specific Impacts']:
				subsystem_quantity = getattr(self, f"total_{subsystem_name.lower()}")
				value_key = f"{impact_name}_Value"
				impact_per_unit = self.input_dict_resolved['RFB Specific Impacts'][subsystem_name][value_key].base_value
				total_impact = subsystem_quantity.base_value * impact_per_unit
				setattr(self, f"total_{subsystem_name.lower()}_{impact_name.lower()}", Quantity(total_impact, impact_unit))
				grand_total += total_impact
			setattr(self, f"total_battery_{impact_name.lower()}", Quantity(grand_total, impact_unit))