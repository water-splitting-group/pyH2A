import numpy as np
from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.input_modification import smoothened_production
from pyH2A.Utilities.Physical_Properties.Physical_properties import Physical_properties as PP
from pyH2A.Utilities.Unit_Handler.quantity import Quantity

class PEC_Plugin:
	'''Simulating H2 production using photoelectrochemical water splitting.
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
				"Design output by year": {
					"Value": {
						"type": {np.ndarray},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "mass",
					},
					"optional": False,
					"description": "Yearly output, ignoring the capacity factor."
				},	
                "Operating capacity factor": { 
                    "Value": {
                        "type": {float, int},
                        "bounds": (0, 1),
                    },
                    "Unit": {
                        "dimension": "dimensionless",
                    },
                    "optional": False,
                    "description": "Operating capacity factor value between 0 and 1."
                },  									
			},
			"PEC Cells": {
				"Cell cost": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "currency / area",
					},
					"optional": False,
					"description": "Cost of PEC cells per cell area."
				},
				"Lifetime": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "time",
					},
					"optional": False,
					"description": "Lifetime of PEC cells before replacement is required."
				},
				"Length": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "length",
					},
					"optional": False,
					"description": "Length of single PEC cell."
				},
				"Width": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "length",
					},
					"optional": False,
					"description": "Width of single PEC cell."
				}
			},
			"Land Area Requirement": {
				"Cell angle": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, np.pi / 2), 
					},
					"Unit": {
						"dimension": "angle",
					},
					"optional": False,
					"description": "Angle of PEC cells from the ground."
				},
				"South spacing": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "length",
					},
					"optional": False,
					"description": "South spacing of PEC cells."
				},
				"East/West spacing": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "length",
					},
					"optional": False,
					"description": "East/West Spacing of PEC cells."
				}
			},
			"Solar-to-Hydrogen Efficiency": {
				"STH": {
					"Value": {
						"type": {float,int,},
						"bounds": (0, 1),
					},
					"Unit": {
						"dimension": "dimensionless", 
					},
					"optional": False,
					"description": "Solar-to-hydrogen efficiency in percentage or as a value between 0 and 1."
				}
			},
			"Solar Input": {
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
			}
		}

		self.output_dict = {
			"Non-Depreciable Capital Costs": {
				"Land required": {
					"Value": {
						"inserted_value": "total_land_area", 
						"type": {float,int,}, 
						"dimension":"area",
		        	},
					"description": "Total land area required.",
					"optional": False,
				},
				"Solar collection area": {
					"Value": {
						"inserted_value": "total_solar_collection_area",
						"type": {float,int,},
						"dimension":"area",
					},
					"description": "Solar collection area.",
					"optional": False,
				}
			},
			"Planned Replacement": {
				"Planned replacement PEC cells": {
					"Cost_Value": {
						"inserted_value": "cell_cost",
						"type": {float,int,},
						"dimension":"currency",
					},
					"Frequency_Value": {
						"inserted_value": "cell_lifetime",
						"type": {float,int,}, 
						"dimension":"time",
					},
					"description": "Total cost of replacing all PEC cells once.",
					"optional": False,		
				}
			},
		 	"Direct Capital Costs - PEC Cells": {
				"PEC cell cost": {
					"Value": {
						"inserted_value": "cell_cost",
						"type": {float,int,}, 
						"dimension": "currency"
					},
					"description": "Total cost of all PEC cells.",
					"optional": False,
				}
			},
			"PEC Cells": {
				"Number": {
					"Value": {
						"inserted_value": "cell_number",
						"type": {float,int}, 
						"dimension":"dimensionless",
					},
					"description": "Number of individual PEC cells required for design H2 output capacity.",
					"optional": False,
				}
			},
			"PEC Water Feed": {
				"Gross yearly mass": {
					"Value": {
						"inserted_value": "gross_yearly_mass",
						"type": {np.ndarray,},
						"dimension": "mass",
					},
					"optional": False,
					"description": "Mass of water to inject in the baggies per year, accounting for conversion and evaporation"
				},
				"Net yearly mass": {
					"Value": {
						"inserted_value": "net_yearly_mass",
						"type": {np.ndarray,},
						"dimension": "mass",
					},
					"optional": False,
					"description": "Mass of water converted into hydrogen per year"
				},				
			},			
			"Main Stream": {
				"Is independent from year": {
					"Value": {
						"inserted_value": "year_independence",
						"type": {int, float,},
						"dimension": "dimensionless",
					},
					"optional": False,
					"description": "if True: all the years behave identically. Else: each year has to be solved"
				},				
				"Temperature": {
					"Value": {
						"inserted_value": "outlet_temperature",
						"type": {dict,},
						"dimension": "absolute_temperature",
					},
					"optional": False,
					"description": "Mixture outlet temperature, dictionary of years whose items are hourly arrays."
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
						"type": {dict,},
						"dimension": "energy/mass",
					},
					"optional": False,
					"description": "Mixture outlet specific enthalpy, dictionary of years whose items are hourly arrays."
				},  
				"Mass fraction": {
					"Value": {
						"inserted_value": "outlet_mass_fraction",
						"type": {dict,},
						"dimension": "dimensionless",
					},
					"optional": False,
					"description": "Mixture outlet mass fraction, dictionary of years whose items are hourly arrays."
				},   
				"Mass flow (hourly)": {
					"Value": {
						"inserted_value": "hourly_mass_flow",
						"type": {dict,},
						"dimension": "mass",
					},
					"optional": False,
					"description": "Mixture outlet mass flow, dictionary of years whose items are hourly arrays."
				},  						 					                
			},				
		}

	def _run(self, dcf):
		self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, 'PEC_Plugin')
		
		self.hydrogen_production()
		self.PEC_cost()
		self.land_area()
		self.outlet_flow_properties()
		self.water_consumption()		

		self.cell_lifetime = self.input_dict_resolved['PEC Cells']['Lifetime']['Value']

		output_inserter_function(self.output_dict, self, dcf, 'PEC_Plugin') 

	def hydrogen_production(self):
		'''Calculation of (kg of H2)/day produced by single PEC cell.
		'''

		pec = self.input_dict_resolved['PEC Cells']

		self.H2_molecule_energy = Quantity(2 * 1.229, 'eV/entity')
		self.H2_molecular_weight = Quantity(2, 'g/mol')

		hourly_mol_H2_per_m2 = (self.input_dict_resolved['Solar Input']['Hourly']['Value'].unit['J/m2'] 
									  * self.input_dict_resolved['Solar-to-Hydrogen Efficiency']['STH']['Value'].unit['-']
									  / self.H2_molecule_energy.unit['J/mol'])

		self.hourly_mol_H2_per_surface = Quantity(hourly_mol_H2_per_m2, 'mol/m2')

		self.mean_mol_rate_H2_per_surface = Quantity(np.sum(hourly_mol_H2_per_m2), 'mol/year/m2')

		self.cell_area = Quantity(pec['Length']['Value'].unit['m'] 
								* pec['Width']['Value'].unit['m'], 
								'm2')

		self.mean_mass_rate_H2_per_cell = Quantity(self.cell_area.unit['m2']
											* self.mean_mol_rate_H2_per_surface.unit['mol/year/m2'] 
											* self.H2_molecular_weight.unit['kg/mol'], 
									 		'kg/year')	

	def PEC_cost(self):
		'''Calculation of cost per cell, number of required cells and total cell cost.
		'''

		cost_per_cell = (self.cell_area.unit['m2'] 
						 * self.input_dict_resolved['PEC Cells']['Cell cost']['Value'].unit['USD/m2'])

		self.cell_number = Quantity(np.ceil(
			   							self.input_dict_resolved['Technical Operating Parameters and Specifications']['Design output by year']['Value'].unit['kg'][0] 
										/ self.mean_mass_rate_H2_per_cell.unit['kg/year']
										), 
							'-')
		
		self.cell_cost = Quantity(self.cell_number.unit['-'] 
								  * cost_per_cell, 
						'USD')

	def land_area(self):
		'''Calculation of total required land area and solar collection area.
		'''

		self.land = self.input_dict_resolved['Land Area Requirement']
		self.pec = self.input_dict_resolved['PEC Cells']

		self.total_solar_collection_area = Quantity(self.cell_area.unit['m2'] 
													* self.cell_number.unit['-'], 
										   'm2')

		cell_plan_view = self.pec['Length']['Value'].unit['m'] * np.cos(self.land['Cell angle']['Value'].unit['rad'])
		total_length = cell_plan_view + self.land['South spacing']['Value'].unit['m']	
		total_width = self.pec['Width']['Value'].unit['m'] + self.land['East/West spacing']['Value'].unit['m']

		self.total_land_area = Quantity(total_width 
										* total_length 
										* self.cell_number.unit['-'], 
								'm2')


	def outlet_flow_properties(self):
		'''Establishes the thermophysical characteristics of the fluid leaving the reactor, for downstream process sizing'''
		self.year_independence = Quantity(True, '-')
		outlet_temperature_degC = 60 # hardcoded for the moment, could become an input later		
		self.outlet_temperature = {round(year): Quantity(outlet_temperature_degC*np.ones_like(self.hourly_mol_H2_per_surface.unit['mol/m2']), # hardcoded for the moment, could become an input later
											'degC') 
									for year in self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-']}		
		
		self.outlet_pressure = Quantity(300, 'psi') # hardcoded for the moment, could become an input later

        # Assuming water vapour is saturated in the electrolyzer, determination of the water vapour pressure
        # since the temperature is constant, we only need to calculate the saturation pressure once
		psat = PP.Water_saturation_pressure(Quantity(outlet_temperature_degC, 'degC'))

		mol_fraction = {} # molar fraction of the gas mixture, assuming ideal gas, expressed in mol of species for a total amount of 1 mol 
		mol_fraction['H2O'] = Quantity(psat.unit['Pa']/self.outlet_pressure.unit['Pa'], '-')
		# The pressure that is not due to water is due to H2
		mol_fraction['H2'] = Quantity(1-mol_fraction['H2O'].unit['-'], '-')        

		_, outlet_mass_fraction = PP.Substance_to_mass(mol_fraction)

		# Converting the outlet mass fraction into a dict of arrays, then into a dict of years 
		self.outlet_mass_fraction = {'H2O': Quantity(outlet_mass_fraction['H2O'].unit['-'] 
														* 
														np.ones_like(self.hourly_mol_H2_per_surface.unit['mol/m2']), 
													'-'), 
									'H2': Quantity(outlet_mass_fraction['H2'].unit['-'] 
														* 
														np.ones_like(self.hourly_mol_H2_per_surface.unit['mol/m2']), 
													'-')
									}        
		self.outlet_mass_fraction = {round(year):self.outlet_mass_fraction for year in self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-']}

		smoothening_period = Quantity(1, 'h')
		self.hourly_mass_flow = {}

		# hourly_unsmoothened_output_kg should normally be a yearly dict of hourly arrays,
		# but we assume a production that is independent of the year, so there's no need to run the same calculation multiple times: a single year (year 0) is sufficient, and is the used identical to itself when generating the hourly_mass_flow dict
		hourly_unsmoothened_output_kg = (self.input_dict_resolved['Technical Operating Parameters and Specifications']['Design output by year']['Value'].unit['kg'][0] 
										*
										self.hourly_mol_H2_per_surface.unit['mol/m2']
										/
										self.mean_mol_rate_H2_per_surface.unit['mol/year/m2']
										/ 
										outlet_mass_fraction['H2'].unit['-']
										)
		for year in self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-']:			
			year = round(year)
			self.hourly_mass_flow[year] = Quantity(smoothened_production(hourly_unsmoothened_output_kg, round(smoothening_period.unit['h'])), 
														'kg')

        # specific enthalpy at the outlet of the baggie
		h = PP.Enthalpy(T = Quantity(outlet_temperature_degC, 'degC'),
                        P = self.outlet_pressure, 
                        amount = outlet_mass_fraction,
                        phase = 'V', 
                        composition_basis = 'mass'
                        )
	
		# specific enthalpy at the outlet of the baggie
		h = Quantity(h.unit['J'] 
                     *
                     np.ones_like(self.hourly_mol_H2_per_surface.unit['mol/m2']), 
                     'J/kg')
		self.outlet_enthalpy = {round(year):h for year in self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-']}
	

	def water_consumption(self):

		# Mass of water converted into hydrogen per year
		self.net_yearly_mass = Quantity(self.input_dict_resolved['Technical Operating Parameters and Specifications']['Design output by year']['Value'].unit['kg'][0] 
		                                *
		                                self.input_dict_resolved['Technical Operating Parameters and Specifications']['Operating capacity factor']['Value'].unit['-']
		                                *
										PP.MW['H2O'].unit['kg/mol']
		                                /
		                                PP.MW['H2'].unit['kg/mol']
										*
										np.ones_like(self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-']),
										'kg')
		# Mass of water to inject per year, due to conversion and evaporation 
		self.gross_yearly_mass = Quantity(np.sum(self.hourly_mass_flow[0].unit['kg']
		                                         *
		                                         self.outlet_mass_fraction[0]['H2O'].unit['-']
		                                         )
		                                *
		                                self.input_dict_resolved['Technical Operating Parameters and Specifications']['Operating capacity factor']['Value'].unit['-']
										*
										np.ones_like(self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-'])
										+
										self.net_yearly_mass.unit['kg'],
										'kg')			