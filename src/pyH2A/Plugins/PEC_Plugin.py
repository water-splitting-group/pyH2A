import numpy as np
from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.input_modification import smoothened_production
from pyH2A.Utilities.Physical_Properties.Physical_properties import Physical_properties as PP
from pyH2A.Utilities.Unit_Handler.quantity import Quantity

class PEC_Plugin:
	'''Simulating H2 production using photoelectrochemical water splitting.

	Parameters
	----------
	Technical Operating Parameters and Specifications > Plant design capacity > Value : float
		Plant design capacity (mass of hydrogen/time).
	PEC Cells > Cell cost > Value : float
		Cost of PEC cells in $/m2.
	PEC Cells > Lifetime > Value : float
		Lifetime of PEC cells in years before replacement is required.
	PEC Cells > Length > Value : float
		Length of single PEC cell.
	PEC Cells > Width > Value : float
		Width of single PEC cell.
	Land Area Requirement > Cell angle > Value : float
		Angle of PEC cells from the ground.
	Land Area Requirement > South spacing > Value : float
		South spacing of PEC cells.
	Land Area Requirement > East/West spacing > Value : float
		East/West Spacing of PEC cells.
	Solar-to-Hydrogen Efficiency > STH > Value : float
		Solar-to-hydrogen efficiency in percentage or as a value between 0 and 1.
	Solar Input > Mean solar input > Value : float
		Mean solar power per surface.

	Returns
	-------
	Non-Depreciable Capital Costs > Land required > Value : float
		Total land area required.
	Non-Depreciable Capital Costs > Solar collection area > Value : float
		Solar collection area.
	Planned Replacement > Planned replacement PEC Cells > Cost_Value : float
		Total cost of replacing all PEC cells once.
	Planned Replacement > Planned replacement PEC Cells > Frequency_Value : float
		Replacement frequency of PEC cells in years, identical to PEC cell lifetime.
	Direct Capital Costs - PEC Cells > PEC cell cost > Value : float
		Total cost of all PEC cells.
	PEC Cells > Number > Value : float
		Number of individual PEC cells required for design H2 output capacity.
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
			"Main Stream": {
				"Temperature": {
					"Value": {
						"inserted_value": "outlet_temperature",
						"type": {float,},
						"dimension": "absolute_temperature",
					},
					"optional": False,
					"description": "Mixture outlet temperature."
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
						"type": {float,},
						"dimension": "energy/mass",
					},
					"optional": False,
					"description": "Mixture outlet specific enthalpy."
				},  
				"Mass fraction": {
					"Value": {
						"inserted_value": "outlet_mass_fraction",
						"type": {dict,},
						"dimension": "dimensionless",
					},
					"optional": False,
					"description": "Mixture outlet mass fraction."
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
				"Design mass flow by year": {
					"Value": {
						"inserted_value": "yearly_mass_flow",
						"type": {np.ndarray,},
						"dimension": "mass",
					},
					"optional": False,
					"description": "Mixture outlet mass per year, excluding downtime (array of years)."
				},  
				"Peak mass flowrate": {
					"Value": {
						"inserted_value": "peak_mass_flowrate",
						"type": {float,},
						"dimension": "mass/time",
					},
					"optional": False,
					"description": "Mixture outlet mass flowrate on peak production day."
				},   			 					                
			},					
		}

	def _run(self, dcf):
		self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, 'PEC_Plugin')
		
		self.hydrogen_production()
		self.PEC_cost()
		self.land_area()
		self.outlet_flow_properties()

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
			   							self.input_dict_resolved['Technical Operating Parameters and Specifications']['Plant design capacity']['Value'].unit['kg/day'] 
										/ self.mean_mass_rate_H2_per_cell.unit['kg/day']
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

		self.outlet_temperature = Quantity(60., 'degC') # hardcoded for the moment, could become an input later
		self.outlet_pressure = Quantity(300, 'psi') # hardcoded for the moment, could become an input later

		# Assuming water vapour is saturated in the baggie, determination of the water vapour pressure
		psat = PP.Water_saturation_pressure(self.outlet_temperature)

		mol_fraction = {} # molar fraction of the gas mixture, assuming ideal gas, expressed in mol of species for a total amount of 1 mol 
		mol_fraction['H2O'] = Quantity(
								psat.unit['Pa']/self.outlet_pressure.unit['Pa'], 
								 '-') 
		# The pressure that is not due to water is due to H2
		mol_fraction['H2'] = Quantity(
								1-mol_fraction['H2O'].unit['-'], 
								'-')

		_, self.outlet_mass_fraction = PP.Substance_to_mass(mol_fraction)


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
										self.outlet_mass_fraction['H2'].unit['-']
										)
		for year in self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-']:			
			year = round(year)
			self.hourly_mass_flow[year] = Quantity(smoothened_production(hourly_unsmoothened_output_kg, round(smoothening_period.unit['h'])), 
														'kg')

		self.yearly_mass_flow = Quantity(self.input_dict_resolved['Technical Operating Parameters and Specifications']['Design output by year']['Value'].unit['kg']
									   / 
									   self.outlet_mass_fraction['H2'].unit['-']
									   ,
									   'kg')

		self.peak_mass_flowrate = Quantity(np.max(self.hourly_mass_flow[0].unit['kg']), 'kg/h')

		print('self.peak_mass_flowrate', self.peak_mass_flowrate)
		print('in H2: ', self.peak_mass_flowrate.unit['kg/h']*self.outlet_mass_fraction['H2'].unit['-'])
		print('in vapour: ', self.peak_mass_flowrate.unit['kg/h']*self.outlet_mass_fraction['H2O'].unit['-'])

		# specific enthalpy at the outlet of the baggie
		h = PP.Enthalpy(T = self.outlet_temperature,
						P = self.outlet_pressure, 
						amount = self.outlet_mass_fraction,
						phase = 'V', 
						composition_basis = 'mass'
						)
		self.outlet_enthalpy = Quantity(h.unit['J'], 'J/kg')