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
				"Cell stack lifetime": {
					"Value": {
						"type": {float, int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "time",
					},
					"description": "Lifetime duration of each stack."
				},						
				"Gross capacity": {
					"Value": {
						"type": {float, int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "energy",
					},
					"description": "Design capacity of the battery, if full charge and discharge of the electrolyte were allowed."
				},		
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
									"description": "Fraction of electrolyte the holdup that is replaced per year. The fresh electrolyte can be produced form scratch, or obtained by regeneration."
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
			"Cell Stack Impact": {		
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
			"Electrolyte Impact": {		
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
			},
		}

		self.output_dict = {
			"Battery": {	
				"Number of cell stacks": {
					"Value": {
						"inserted_value": "number_cell_stacks",
						"type": {float,},
						"dimension": "dimensionless",
					},
					"description": "Number of cell stacks to provide the required power.",
					"optional": False,
				},	
				"Lifetime number of cell stacks": {
					"Value": {
						"inserted_value": "lifetime_number_cell_stacks",
						"type": {float,},
						"dimension": "dimensionless",
					},
					"description": "Number of cell stacks needed over the lifetime of the battery, accounting for replacement.",
					"optional": False,
				},												
				"Initial amount of electrolyte": {
					"Value": {
						"inserted_value": "initial_electrolyte_amount",
						"type": {float,},
						"dimension": "mass",
					},
					"description": "Mass of electrolyte present in the battery upon startup.",
					"optional": False,
				},
				"Total amount of electrolyte": {
					"Value": {
						"inserted_value": "total_electrolyte_amount",
						"type": {float,},
						"dimension": "mass",
					},
					"description": "Mass of electrolyte to produce during the entire battery lifetime.",
					"optional": False,
				},			
			},	
			"Cell Stack Impact": {
				"Total GWP": {
					"Value": {
						"inserted_value": "total_stack_gwp",
						"type": {float,},
						"dimension": "mass",
					},
					"description": "GWP associated to the stacks during the entire battery lifetime.",
					"optional": True,
				},	
				"Total energy": {
					"Value": {
						"inserted_value": "total_stack_energy",
						"type": {float,},
						"dimension": "energy",
					},
					"description": "Energy consumption associated to the stacks during the entire battery lifetime.",
					"optional": True,
				},	
				"Total toxicity": {
					"Value": {
						"inserted_value": "total_stack_toxicity",
						"type": {float,},
						"dimension": "dimensionless",
					},
					"description": "Toxicity associated to the stacks during the entire battery lifetime.",
					"optional": True,
				},	
				"Total resource use": {
					"Value": {
						"inserted_value": "total_stack_resource_use",
						"type": {float,},
						"dimension": "mass",
					},
					"description": "Resource use associated to the stacks during the entire battery lifetime.",
					"optional": True,
				},	
			},			
			"Electrolyte Impact": {
				"Total GWP": {
					"Value": {
						"inserted_value": "total_electrolyte_gwp",
						"type": {float,},
						"dimension": "mass",
					},
					"description": "GWP associated to the electolyte amount used during the entire battery lifetime.",
					"optional": True,
				},	
				"Total energy": {
					"Value": {
						"inserted_value": "total_electrolyte_energy",
						"type": {float,},
						"dimension": "energy",
					},
					"description": "Energy consumption associated to the electolyte amount used during the entire battery lifetime.",
					"optional": True,
				},	
				"Total toxicity": {
					"Value": {
						"inserted_value": "total_electrolyte_toxicity",
						"type": {float,},
						"dimension": "dimensionless",
					},
					"description": "Toxicity associated to the electolyte amount used during the entire battery lifetime.",
					"optional": True,
				},	
				"Total resource use": {
					"Value": {
						"inserted_value": "total_electrolyte_resource_use",
						"type": {float,},
						"dimension": "mass",
					},
					"description": "Resource use associated to the electolyte amount used during the entire battery lifetime.",
					"optional": True,
				},																					
			},	
			"Periphery": {
				"Amount of steel": {
					"Value": {
						"inserted_value": "amount_steel",
						"type": {float,},
						"dimension": "mass",
					},
					"description": "Mass of steel for tanks, pumps, piping, heat exchange etc.",
					"optional": True,
				},	
				"Amount of cable": {
					"Value": {
						"inserted_value": "amount_cable",
						"type": {float,},
						"dimension": "mass",
					},
					"description": "Amount of metal for cables (e.g copper or aluminium).",
					"optional": True,
				},		
			},						
		}



	def _run(self, dcf):

		self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, 'RFB_Plugin')

		self.calculate_stack_number()
		self.calculate_electrolyte_amount()
		self.calculate_impact()
		self.calculate_periphery()

		output_inserter_function(self.output_dict, self, dcf, 'RFB_Plugin') 



	def calculate_stack_number(self):

		self.number_cell_stacks = Quantity(
										self.input_dict_resolved['Battery']['Power']['Value'].unit['W']
										/
										self.input_dict_resolved['Battery']['Power per cell stack']['Value'].unit['W'], 
										'-'
										)

		self.lifetime_number_cell_stacks = Quantity(
										self.number_cell_stacks.unit['-']
										*
										(np.sum(self.input_dict_resolved['Time']['Years']['Value']['Operation years ones'].unit['-'])
										//
										self.input_dict_resolved['Battery']['Cell stack lifetime']['Value'].unit['year']
										), 
										'-'
										)

	def calculate_electrolyte_amount(self):

		self.initial_electrolyte_amount = Quantity(
												self.input_dict_resolved['Battery']['Gross capacity']['Value'].unit['J']
												/
												self.input_dict_resolved['Battery']['Energy density']['Value'].unit['J/kg'], 
												'kg')

		# Assumption: the fraction of fresh electrolyte to inject each year is fixed
		yearly_electrolyte_needed_kg = (self.input_dict_resolved['Battery']['Fraction of electrolyte to replace per year']['Value'].unit['-']
										*
										self.initial_electrolyte_amount.unit['kg'])

		yearly_electrolyte_produced_kg = (yearly_electrolyte_needed_kg
										 *
										 self.input_dict_resolved['Battery']['Fraction of replaced electrolyte to produce per year']['Value'].unit['-'])

		self.total_electrolyte_amount = Quantity(
												np.sum(self.input_dict_resolved['Time']['Years']['Value']['Operation years ones'].unit['-']) # this assumes that the renewal occurs continuously all along the year. 
												*																						# If we considered that the renewal occurs as a discrete refilling at the beginning of each new  year, we would need the number of years - 1 
												yearly_electrolyte_produced_kg
												+
												self.initial_electrolyte_amount.unit['kg']
												, 
												'kg')

	def calculate_impact(self):

		# Cell stacks
		if 'GWP per stack' in self.input_dict_resolved['Cell Stack Impact']:
			self.total_stack_gwp = Quantity(
									self.input_dict_resolved['Cell Stack Impact']['GWP per stack']['Value'].unit['kg']
									*
									self.lifetime_number_cell_stacks.unit['-'], 
									'kg'
									) 
			
		if 'Energy per stack' in self.input_dict_resolved['Cell Stack Impact']:
			self.total_stack_energy = Quantity(
									self.input_dict_resolved['Cell Stack Impact']['Energy per stack']['Value'].unit['J']
									*
									self.lifetime_number_cell_stacks.unit['-'], 
									'J'
									) 			

		if 'Toxicity per stack' in self.input_dict_resolved['Cell Stack Impact']:
			self.total_stack_toxicity = Quantity(
									self.input_dict_resolved['Cell Stack Impact']['Toxicity per stack']['Value'].unit['-']
									*
									self.lifetime_number_cell_stacks.unit['-'], 
									'-'
									) 
			
		if 'Resource use per stack' in self.input_dict_resolved['Cell Stack Impact']:
			self.total_stack_resource_use = Quantity(
									self.input_dict_resolved['Cell Stack Impact']['Resource use per stack']['Value'].unit['kg']
									*
									self.lifetime_number_cell_stacks.unit['-'], 
									'kg'
									) 

		# Electrolyte
		if 'Specific GWP' in self.input_dict_resolved['Electrolyte Impact']:
			self.total_electrolyte_gwp = Quantity(
									self.input_dict_resolved['Electrolyte Impact']['Specific GWP']['Value'].unit['kg/kg']
									*
									self.total_electrolyte_amount.unit['kg'], 
									'kg'
									) 

		if 'Energy intensity' in self.input_dict_resolved['Electrolyte Impact']:
			self.total_electrolyte_energy = Quantity(
									self.input_dict_resolved['Electrolyte Impact']['Energy intensity']['Value'].unit['J/kg']
									*
									self.total_electrolyte_amount.unit['kg'], 
									'J'
									) 			

		if 'Specific toxicity' in self.input_dict_resolved['Electrolyte Impact']:
			self.total_electrolyte_toxicity = Quantity(
									self.input_dict_resolved['Electrolyte Impact']['Specific toxicity']['Value'].unit['1/kg']
									*
									self.total_electrolyte_amount.unit['kg'], 
									'-'
									) 
			
		if 'Specific resource use' in self.input_dict_resolved['Electrolyte Impact']:
			self.total_electrolyte_resource_use = Quantity(
									self.input_dict_resolved['Electrolyte Impact']['Specific resource use']['Value'].unit['kg/kg']
									*
									self.total_electrolyte_amount.unit['kg'], 
									'kg'
									) 

	def calculate_periphery(self):
		'''Scales the amount of material for piping and tanks, pumps etc, according to the capacity or the power.
		The reference values are obtained from 
		Life cycle assessment of an industrial-scale vanadium flow battery, Blume et al (2022), DOI: 10.1111/jiec.13328 '''

		# Hardcoded values obtained from the article
		reference_power_MW = 1
		reference_capacity_MWh = 8
		reference_density_kg_per_m3 = 1350 # 506746 kg / 375.4 m3
		reference_pump_steel_kg = 12000
		reference_tank_steel_kg = 264622
		reference_cable_kg = 395
		reference_piping_steel_kg = 1145

		# The amount of steel required for a pump is not necessarily related to its power, let alone to the battery power, let alone linearly
		# The reasoning of the following formula is that the whole plant would not just have one pair of pumps, but one pair per "reference module", each "reference module" being 1 MW in power, 
		# so the number of modules, hence the number of pairs of umps and subsequent material mass would be the power of the battery divided ny the reference power (float, because this is all meant as an estimate rather than an actual discretization in modules)
		# I would recommend running a sensitivity analysis on this, hoping it would be negligeible, because this scaling approach remains fragile
		pump_steel_kg = reference_pump_steel_kg * self.input_dict_resolved['Battery']['Power']['Value'].unit['MW']/ reference_power_MW

		# The amount of steel for tanks, following the same logic, assumes tanks of the same size as the reference ones, but with a number of tanks proportional to the volume of electrolytes
		tank_steel_kg = (reference_tank_steel_kg 
				   		* 
						self.input_dict_resolved['Battery']['Gross capacity']['Value'].unit['MWh']
						/
						reference_capacity_MWh
						*
						reference_density_kg_per_m3
				   		/
					 	self.input_dict_resolved['Battery']['Electrolyte density']['Value'].unit['kg/m3'])

		piping_steel_kg = reference_piping_steel_kg # no scaling applied for the moment, would suggest sensitivity analysis

		self.amount_steel = Quantity(tank_steel_kg + pump_steel_kg + piping_steel_kg, 'kg')

		self.amount_cable = Quantity(reference_cable_kg, 'kg') # no scaling applied for the moment, would suggest sensitivity analysis