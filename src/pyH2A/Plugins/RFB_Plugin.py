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
					"optional": False,
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
				"GWP per stack": {
					"Value": {
						"type": {float, int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "mass", 
					},
					"optional": True,						
					"description": "Mass of CO2 equivalent per stack produced."
				},		
				"Energy per stack": {
					"Value": {
						"type": {float, int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "energy",
					},
					"optional": True,						
					"description": "Energy consumed per stack produced."
				},	
				"Toxicity per stack": {
					"Value": {
						"type": {float, int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "dimensionless", 
					},
					"optional": True,											
					"description": "Toxicity in Comparative Toxic Unit."
				},	
				"Resource use per stack": {
					"Value": {
						"type": {float, int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "mass", 
					},
					"optional": True,			
					"description": "Resource use per stack produced."
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
				"Specific GWP": {
					"Value": {
						"type": {float, int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "mass/mass", # I didn't make it dimensionless because it's a typical case where at some point we might want to have a matrix operation where this value, and the next ones, are multiplies by the mass of product
					},
					"optional": True,						
					"description": "Mass of CO2 equivalent per mass of electrolyte produced."
				},		
				"Energy intensity": {
					"Value": {
						"type": {float, int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "energy/mass",
					},
					"optional": True,						
					"description": "Energy consumed per mass of electrolyte produced."
				},	
				"Specific toxicity": {
					"Value": {
						"type": {float, int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "1/mass", 
					},
					"optional": True,											
					"description": "Toxicity in Comparative Toxic Unit per mass of electrolyte produced."
				},	
				"Specific resource use": {
					"Value": {
						"type": {float, int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "mass/mass", # same remark as for GWP
					},
					"optional": True,			
					"description": "Resource use per mass of electrolyte produced."
				},	
				"Tank steel specific GWP": {
					"Value": {
						"type": {float, int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "mass/mass", 
					},
					"optional": True,						
					"description": "Mass of CO2 equivalent per mass of steel constituting the tanks."
				},		
				"Tank steel energy intensity": {
					"Value": {
						"type": {float, int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "energy/mass",
					},
					"optional": True,						
					"description": "Energy consumed per mass of steel."
				},	
				"Tank steel specific toxicity": {
					"Value": {
						"type": {float, int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "1/mass", 
					},
					"optional": True,											
					"description": "Toxicity in Comparative Toxic Unit per mass of steel."
				},	
				"Tank steel specific resource use": {
					"Value": {
						"type": {float, int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "mass/mass", # same remark as for GWP
					},
					"optional": True,			
					"description": "Resource use per mass of steel."
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
				"GWP per periphery item": {
					"Value": {
						"type": {float, int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "mass", 
					},
					"optional": True,						
					"description": "Mass of CO2 equivalent per periphery item."
				},		
				"Energy per periphery item": {
					"Value": {
						"type": {float, int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "energy",
					},
					"optional": True,						
					"description": "Energy consumed per periphery item."
				},	
				"Toxicity per periphery item": {
					"Value": {
						"type": {float, int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "dimensionless", 
					},
					"optional": True,											
					"description": "Toxicity in Comparative Toxic Unit."
				},	
				"Resource use per periphery item": {
					"Value": {
						"type": {float, int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "mass", 
					},
					"optional": True,			
					"description": "Resource use per periphery item."
				},	
			},			
		}

		self.output_dict = {
			"Battery": {
				"GWP over lifetime": {
					"Value": {
						"inserted_value": "total_gwp",
						"type": {float,},
						"dimension": "mass",
					},
					"description": "GWP for the entire battery system.",
				},	
				"Energy over lifetime": {
					"Value": {
						"inserted_value": "total_energy",
						"type": {float,},
						"dimension": "energy",
					},
					"description": "Energy consumption for the entire battery system.",
				},	
				"Toxicity over lifetime": {
					"Value": {
						"inserted_value": "total_toxicity",
						"type": {float,},
						"dimension": "dimensionless",
					},
					"description": "Toxicity for the entire battery system.",
				},	
				"Resource use over lifetime": {
					"Value": {
						"inserted_value": "total_resource_use",
						"type": {float,},
						"dimension": "mass",
					},
					"description": "Resource use for the entire battery system.",
				},	
			},			
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
						"inserted_value": "lifetime_number_cell_stacks",
						"type": {float,},
						"dimension": "dimensionless",
					},
					"description": "Number of cell stacks needed over the lifetime of the battery, accounting for replacement.",
				},					
				"GWP over lifetime": {
					"Value": {
						"inserted_value": "total_stack_gwp",
						"type": {float,},
						"dimension": "mass",
					},
					"description": "GWP associated to the stacks during the entire battery lifetime.",
				},	
				"Energy over lifetime": {
					"Value": {
						"inserted_value": "total_stack_energy",
						"type": {float,},
						"dimension": "energy",
					},
					"description": "Energy consumption associated to the stacks during the entire battery lifetime.",
				},	
				"Toxicity over lifetime": {
					"Value": {
						"inserted_value": "total_stack_toxicity",
						"type": {float,},
						"dimension": "dimensionless",
					},
					"description": "Toxicity associated to the stacks during the entire battery lifetime.",
				},	
				"Resource use over lifetime": {
					"Value": {
						"inserted_value": "total_stack_resource_use",
						"type": {float,},
						"dimension": "mass",
					},
					"description": "Resource use associated to the stacks during the entire battery lifetime.",
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
						"inserted_value": "total_electrolyte_amount",
						"type": {float,},
						"dimension": "mass",
					},
					"description": "Mass of electrolyte to produce during the entire battery lifetime.",
				},					
				"GWP over lifetime": {
					"Value": {
						"inserted_value": "total_electrolyte_gwp",
						"type": {float,},
						"dimension": "mass",
					},
					"description": "GWP associated to the electolyte amount used during the entire battery lifetime.",
				},	
				"Energy over lifetime": {
					"Value": {
						"inserted_value": "total_electrolyte_energy",
						"type": {float,},
						"dimension": "energy",
					},
					"description": "Energy consumption associated to the electolyte amount used during the entire battery lifetime.",
				},	
				"Toxicity over lifetime": {
					"Value": {
						"inserted_value": "total_electrolyte_toxicity",
						"type": {float,},
						"dimension": "dimensionless",
					},
					"description": "Toxicity associated to the electolyte amount used during the entire battery lifetime.",
				},	
				"Resource use over lifetime": {
					"Value": {
						"inserted_value": "total_electrolyte_resource_use",
						"type": {float,},
						"dimension": "mass",
					},
					"description": "Resource use associated to the electolyte amount used during the entire battery lifetime.",
				},	
				"Tank steel GWP": {
					"Value": {
						"inserted_value": "steel_gwp",
						"type": {float,},
						"dimension": "mass",
					},
					"description": "GWP associated to the tanks steel.",
				},	
				"Tank steel energy": {
					"Value": {
						"inserted_value": "steel_energy",
						"type": {float,},
						"dimension": "energy",
					},
					"description": "Energy consumption associated to the tanks steel.",
				},	
				"Tank steel toxicity": {
					"Value": {
						"inserted_value": "steel_toxicity",
						"type": {float,},
						"dimension": "dimensionless",
					},
					"description": "Toxicity associated to the tanks steel.",
				},	
				"Tank steel resource use": {
					"Value": {
						"inserted_value": "steel_resource_use",
						"type": {float,},
						"dimension": "mass",
					},
					"description": "Resource use associated to the tanks steel.",
				},
			},	
			"Battery Periphery": {
				"GWP over lifetime": {
					"Value": {
						"inserted_value": "total_periphery_gwp",
						"type": {float,},
						"dimension": "mass",
					},
					"description": "GWP associated to the periphery.",
				},	
				"Energy over lifetime": {
					"Value": {
						"inserted_value": "total_periphery_energy",
						"type": {float,},
						"dimension": "energy",
					},
					"description": "Energy consumption associated to the periphery.",
				},	
				"Toxicity over lifetime": {
					"Value": {
						"inserted_value": "total_periphery_toxicity",
						"type": {float,},
						"dimension": "dimensionless",
					},
					"description": "Toxicity associated to the periphery.",
				},	
				"Resource use over lifetime": {
					"Value": {
						"inserted_value": "total_periphery_resource_use",
						"type": {float,},
						"dimension": "mass",
					},
					"description": "Resource use associated to the periphery.",
				},	
			},				
		}



	def _run(self, dcf):

		self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, 'RFB_Plugin')

		self.calculate_electrolyte()
		self.calculate_stack()
		self.calculate_periphery()
		self.calculate_total_impact()

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

		self.total_electrolyte_amount = Quantity(
												np.sum(self.input_dict_resolved['Time']['Years']['Value']['Operation years ones'].unit['-']) # this assumes that the renewal occurs continuously all along the year. 
												*																						# If we considered that the renewal occurs as a discrete refilling at the beginning of each new  year, we would need the number of years - 1 
												yearly_electrolyte_produced_kg
												+
												self.initial_electrolyte_amount.unit['kg']
												, 
												'kg')

		if 'Specific GWP' in self.input_dict_resolved['Battery Electrolyte']:
			self.total_electrolyte_gwp = Quantity(
									self.input_dict_resolved['Battery Electrolyte']['Specific GWP']['Value'].unit['kg/kg']
									*
									self.total_electrolyte_amount.unit['kg'], 
									'kg'
									) 
		else:
			self.total_electrolyte_gwp = Quantity(0, 'kg')

		if 'Energy intensity' in self.input_dict_resolved['Battery Electrolyte']:
			self.total_electrolyte_energy = Quantity(
									self.input_dict_resolved['Battery Electrolyte']['Energy intensity']['Value'].unit['J/kg']
									*
									self.total_electrolyte_amount.unit['kg'], 
									'J'
									) 	
		else:
			self.total_electrolyte_energy = Quantity(0, 'J')					

		if 'Specific toxicity' in self.input_dict_resolved['Battery Electrolyte']:
			self.total_electrolyte_toxicity = Quantity(
									self.input_dict_resolved['Battery Electrolyte']['Specific toxicity']['Value'].unit['1/kg']
									*
									self.total_electrolyte_amount.unit['kg'], 
									'-'
									) 
		else:
			self.total_electrolyte_toxicity = Quantity(0, '-')			
			
		if 'Specific resource use' in self.input_dict_resolved['Battery Electrolyte']:
			self.total_electrolyte_resource_use = Quantity(
									self.input_dict_resolved['Battery Electrolyte']['Specific resource use']['Value'].unit['kg/kg']
									*
									self.total_electrolyte_amount.unit['kg'], 
									'kg'
									) 			
		else:
			self.total_electrolyte_resource_use = Quantity(0, 'kg')

		# The amount of steel for tanks assumes tanks of the same size as in the following paper
		# "Life cycle assessment of an industrial-scale vanadium flow battery, Blume et al (2022), DOI: 10.1111/jiec.13328"
		# but with a number of tanks proportional to the volume of electrolytes

		# Hardcoded values obtained from the article
		reference_capacity_MWh = 8
		reference_density_kg_per_m3 = 1350 # 506746 kg / 375.4 m3
		reference_tank_steel_kg = 264622
		tank_steel_kg = (reference_tank_steel_kg 
						* 
						self.input_dict_resolved['Battery']['Gross capacity']['Value'].unit['MWh']
						/
						reference_capacity_MWh
						*
						reference_density_kg_per_m3
						/
						self.input_dict_resolved['Battery Electrolyte']['Electrolyte density']['Value'].unit['kg/m3'])

		if 'Tank steel specific GWP' in self.input_dict_resolved['Battery Electrolyte']:
			self.steel_gwp = Quantity(
									self.input_dict_resolved['Battery Electrolyte']['Tank steel specific GWP']['Value'].unit['kg/kg']
									*
									tank_steel_kg, 
									'kg'
									) 
		else:
			self.steel_gwp = Quantity(0, 'kg')			

		if 'Tank steel energy intensity' in self.input_dict_resolved['Battery Electrolyte']:
			self.steel_energy = Quantity(
									self.input_dict_resolved['Battery Electrolyte']['Tank steel energy intensity']['Value'].unit['J/kg']
									*
									tank_steel_kg, 
									'J'
									) 	
		else:
			self.steel_energy = Quantity(0, 'J')					

		if 'Tank steel specific toxicity' in self.input_dict_resolved['Battery Electrolyte']:
			self.steel_toxicity = Quantity(
									self.input_dict_resolved['Battery Electrolyte']['Tank steel specific toxicity']['Value'].unit['1/kg']
									*
									tank_steel_kg, 
									'-'
									) 	
		else:
			self.steel_toxicity = Quantity(0, '-')				
			
		if 'Tank steel specific resource use' in self.input_dict_resolved['Battery Electrolyte']:
			self.steel_resource_use = Quantity(
									self.input_dict_resolved['Battery Electrolyte']['Tank steel specific resource use']['Value'].unit['kg/kg']
									*
									tank_steel_kg, 
									'kg'
									) 
		else:
			self.steel_resource_use = Quantity(0, 'kg')			

	def calculate_stack(self):

		self.number_cell_stacks = Quantity(
										self.input_dict_resolved['Battery']['Power']['Value'].unit['W']
										/
										self.input_dict_resolved['Battery Cell Stack']['Power per cell stack']['Value'].unit['W'], 
										'-'
										)

		self.lifetime_number_cell_stacks = Quantity(
										self.number_cell_stacks.unit['-']
										*
										(np.sum(self.input_dict_resolved['Time']['Years']['Value']['Operation years ones'].unit['-'])
										//
										self.input_dict_resolved['Battery Cell Stack']['Lifetime']['Value'].unit['year']
										), 
										'-'
										)

		if 'GWP per stack' in self.input_dict_resolved['Battery Cell Stack']:
			self.total_stack_gwp = Quantity(
									self.input_dict_resolved['Battery Cell Stack']['GWP per stack']['Value'].unit['kg']
									*
									self.lifetime_number_cell_stacks.unit['-'], 
									'kg'
									) 
		else:
			self.total_stack_gwp = Quantity(0, 'kg')			
			
		if 'Energy per stack' in self.input_dict_resolved['Battery Cell Stack']:
			self.total_stack_energy = Quantity(
									self.input_dict_resolved['Battery Cell Stack']['Energy per stack']['Value'].unit['J']
									*
									self.lifetime_number_cell_stacks.unit['-'], 
									'J'
									) 	
		else:
			self.total_stack_energy = Quantity(0, 'J')					

		if 'Toxicity per stack' in self.input_dict_resolved['Battery Cell Stack']:
			self.total_stack_toxicity = Quantity(
									self.input_dict_resolved['Battery Cell Stack']['Toxicity per stack']['Value'].unit['-']
									*
									self.lifetime_number_cell_stacks.unit['-'], 
									'-'
									) 
		else:
			self.total_stack_toxicity = Quantity(0, '-')			
			
		if 'Resource use per stack' in self.input_dict_resolved['Battery Cell Stack']:
			self.total_stack_resource_use = Quantity(
									self.input_dict_resolved['Battery Cell Stack']['Resource use per stack']['Value'].unit['kg']
									*
									self.lifetime_number_cell_stacks.unit['-'], 
									'kg'
									) 
		else:
			self.total_stack_resource_use = Quantity(0, 'kg')			

	def calculate_periphery(self):
		if 'GWP per periphery item' in self.input_dict_resolved['Battery Periphery']:
			self.total_periphery_gwp = Quantity(
									self.input_dict_resolved['Battery Periphery']['GWP per periphery item']['Value'].unit['kg']
									*
									self.input_dict_resolved['Battery Periphery']['Number of periphery items']['Value'].unit['-'], 
									'kg'
									) 
		else:
			self.total_periphery_gwp = Quantity(0, 'kg')			

		if 'Energy per periphery item' in self.input_dict_resolved['Battery Periphery']:
			self.total_periphery_energy = Quantity(
									self.input_dict_resolved['Battery Periphery']['Energy per periphery item']['Value'].unit['J']
									*
									self.input_dict_resolved['Battery Periphery']['Number of periphery items']['Value'].unit['-'], 
									'J'
									) 
		else:
			self.total_periphery_energy = Quantity(0, 'J')						

		if 'Toxicity per periphery item' in self.input_dict_resolved['Battery Periphery']:
			self.total_periphery_toxicity = Quantity(
									self.input_dict_resolved['Battery Periphery']['Toxicity per periphery item']['Value'].unit['-']
									*
									self.input_dict_resolved['Battery Periphery']['Number of periphery items']['Value'].unit['-'], 
									'-'
									) 
		else:
			self.total_periphery_toxicity = Quantity(0, '-')			
			
		if 'Resource use per periphery item' in self.input_dict_resolved['Battery Periphery']:
			self.total_periphery_resource_use = Quantity(
									self.input_dict_resolved['Battery Periphery']['Resource use per periphery item']['Value'].unit['kg']
									*
									self.input_dict_resolved['Battery Periphery']['Number of periphery items']['Value'].unit['-'], 
									'kg'
									) 
		else:
			self.total_periphery_resource_use = Quantity(0, 'kg')						


	def calculate_total_impact(self):
		self.total_gwp = Quantity(self.total_electrolyte_gwp.unit['kg']
							+ self.steel_gwp.unit['kg']
							+ self.total_stack_gwp.unit['kg']
							+ self.total_periphery_gwp.unit['kg'], 
							'kg')

		self.total_energy = Quantity(self.total_electrolyte_energy.unit['J']
							+ self.steel_energy.unit['J']
							+ self.total_stack_energy.unit['J']
							+ self.total_periphery_energy.unit['J'], 
							'J')
		
		self.total_toxicity = Quantity(self.total_electrolyte_toxicity.unit['-']
							+ self.steel_toxicity.unit['-']
							+ self.total_stack_toxicity.unit['-']
							+ self.total_periphery_toxicity.unit['-'], 
							'-')
		
		self.total_resource_use = Quantity(self.total_electrolyte_resource_use.unit['kg']
							+ self.steel_resource_use.unit['kg']
							+ self.total_stack_resource_use.unit['kg']
							+ self.total_periphery_resource_use.unit['kg'], 
							'kg')