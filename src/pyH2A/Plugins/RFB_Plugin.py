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
				"Cost per cell stack": {
					"Value": {
						"type": {float, int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "currency",
					},
					"description": "Cost of each stack."
				},				
				"Design capacity": {
					"Value": {
						"type": {float, int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "energy",
					},
					"description": "Design capacity of the battery."
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
				"Electrolyte regeneration per year": {
					"Value": {
						"type": {float, int,},
						"bounds": (0, None), # no upper bound: it is theoretically possible that the turn over frequency is higher than 1/year.
					},
					"Unit": {
						"dimension": "dimensionless",
					},
					"description": "Fraction of electrolyte the holdup that is replaced per year."
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
				"Specific cost": {
					"Value": {
						"type": {float, int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "currency/mass", 
					},
					"optional": True,			
					"description": "Cost per mass of electrolyte produced."
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
				"Cost of cell stacks": {
					"Value": {
						"inserted_value": "cost_cell_stacks",
						"type": {float,},
						"dimension": "currency",
					},
					"description": "Total cost of the cell stacks.",
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
				"Yearly amount of replacement electrolyte": {     # defining a yearly amount to replace, as it will enable to point to that amount in the Planned Replacement table (for Replacement_Plugin), so we can assess the inflation-adjusted cost correctly
					"Value": {
						"inserted_value": "yearly_electrolyte_amount",
						"type": {float,},
						"dimension": "mass",
					},
					"description": "Mass of electrolyte needed during each operation year to maintain capacity.",
					"optional": False,
				},
				"Total amount of electrolyte": {
					"Value": {
						"inserted_value": "total_electrolyte_amount",
						"type": {float,},
						"dimension": "mass",
					},
					"description": "Mass of electrolyte needed during the entire battery lifetime.",
					"optional": False,
				},			
			},	
			"Electrolyte Impact": {
				"Total GWP": {
					"Value": {
						"inserted_value": "total_gwp",
						"type": {float,},
						"dimension": "mass",
					},
					"description": "GWP associated to the electolyte amount used during the entire battery lifetime.",
					"optional": True,
				},	
				"Total energy": {
					"Value": {
						"inserted_value": "total_energy",
						"type": {float,},
						"dimension": "energy",
					},
					"description": "Energy consumption associated to the electolyte amount used during the entire battery lifetime.",
					"optional": True,
				},	
				"Total toxicity": {
					"Value": {
						"inserted_value": "total_toxicity",
						"type": {float,},
						"dimension": "dimensionless",
					},
					"description": "Toxicity associated to the electolyte amount used during the entire battery lifetime.",
					"optional": True,
				},	
				"Total resource use": {
					"Value": {
						"inserted_value": "total_resource_use",
						"type": {float,},
						"dimension": "mass",
					},
					"description": "Resource use associated to the electolyte amount used during the entire battery lifetime.",
					"optional": True,
				},	
				"Initial cost of electrolyte": {
					"Value": {
						"inserted_value": "initial_cost",
						"type": {float,},
						"dimension": "currency",
					},
					"description": "Cost of the initial electrolyte holdup.",
					"optional": True,
				},														
				"Yearly cost of electrolyte": {
					"Value": {
						"inserted_value": "yearly_cost",
						"type": {float,},
						"dimension": "currency",
					},
					"description": "Cost of electrolyte replacement per year.",
					"optional": True,
				},																					
			},	
		}



	def _run(self, dcf):

		self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, 'RFB_Plugin')

		self.calculate_cell_number()
		self.calculate_electrolyte_amount()
		self.calculate_impact()

		output_inserter_function(self.output_dict, self, dcf, 'RFB_Plugin') 



	def calculate_cell_number(self):

		self.number_cell_stacks = Quantity(
										self.input_dict_resolved['Battery']['Power']['Value'].unit['W']
										/
										self.input_dict_resolved['Battery']['Power per cell stack']['Value'].unit['W'], 
										'-'
										)

		self.cost_cell_stacks = Quantity(
										self.number_cell_stacks.unit['-']
										*
										self.input_dict_resolved['Battery']['Cost per cell stack']['Value'].unit['USD'], 
										'USD'
										)

	def calculate_electrolyte_amount(self):

		self.initial_electrolyte_amount = Quantity(
												self.input_dict_resolved['Battery']['Design capacity']['Value'].unit['J']
												/
												self.input_dict_resolved['Battery']['Energy density']['Value'].unit['J/kg'], 
												'kg')

		# Assumption: the fraction of fresh electrolyte to inject each year is fixed
		self.yearly_electrolyte_amount = Quantity(
												self.input_dict_resolved['Battery']['Electrolyte regeneration per year']['Value'].unit['-']
												*
												self.initial_electrolyte_amount.unit['kg'], 
												'kg')

		self.total_electrolyte_amount = Quantity(
												np.sum(self.input_dict_resolved['Time']['Years']['Value']['Operation years ones'].unit['-'])
												*
												self.yearly_electrolyte_amount.unit['kg']
												+
												self.initial_electrolyte_amount.unit['kg']
												, 
												'kg')

	def calculate_impact(self):
		if 'Specific GWP' in self.input_dict_resolved['Electrolyte Impact']:
			self.total_gwp = Quantity(
									self.input_dict_resolved['Electrolyte Impact']['Specific GWP']['Value'].unit['kg/kg']
									*
									self.total_electrolyte_amount.unit['kg'], 
									'kg'
									) 
			
		if 'Energy intensity' in self.input_dict_resolved['Electrolyte Impact']:
			self.total_energy = Quantity(
									self.input_dict_resolved['Electrolyte Impact']['Energy intensity']['Value'].unit['J/kg']
									*
									self.total_electrolyte_amount.unit['kg'], 
									'J'
									) 			

		if 'Specific toxicity' in self.input_dict_resolved['Electrolyte Impact']:
			self.total_toxicity = Quantity(
									self.input_dict_resolved['Electrolyte Impact']['Specific toxicity']['Value'].unit['1/kg']
									*
									self.total_electrolyte_amount.unit['kg'], 
									'-'
									) 
			
		if 'Specific resource use' in self.input_dict_resolved['Electrolyte Impact']:
			self.total_resource_use = Quantity(
									self.input_dict_resolved['Electrolyte Impact']['Specific resource use']['Value'].unit['kg/kg']
									*
									self.total_electrolyte_amount.unit['kg'], 
									'kg'
									) 

		if'Specific cost' in self.input_dict_resolved['Electrolyte Impact']:
			self.initial_cost = Quantity(
										self.initial_electrolyte_amount.unit['kg']
										*
										self.input_dict_resolved['Electrolyte Impact']['Specific cost']['Value'].unit['USD/kg'], 
										'USD'
									)
			
			self.yearly_cost = Quantity(
										self.yearly_electrolyte_amount.unit['kg']
										*
										self.input_dict_resolved['Electrolyte Impact']['Specific cost']['Value'].unit['USD/kg'],
										'USD'
									)