from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.Physical_Properties.Physical_properties import Physical_properties as PP
import numpy as np
import math

class Cooler_Condenser_Plugin:
    '''Simulation of humid gas mixture cooling with condensation.
    The pressure stays constant during the compression. The other properties of the Main Stream are updated.
    '''
    def __init__(self, dcf, print_info, run = True, instance_suffix=None):
        self.instance_suffix = instance_suffix
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
            "Cooler Condenser@": {
                "Cold inlet temperature": {
                    "Value": {
                        "type": {int,float,},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "absolute_temperature",
                    },
                    "optional": False,
                    "description": "Temperature of the cold fluid inlet."
                },
                "Cold outlet temperature": {
                    "Value": {
                        "type": {int,float,},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "absolute_temperature",
                    },
                    "optional": False,
                    "description": "Temperature of the cold fluid outlet."
                },  
                "Hot outlet temperature": {
                    "Value": {
                        "type": {int,float,},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "absolute_temperature",
                    },
                    "optional": False,
                    "description": "Temperature of the hot fluid outlet."
                },        
                "Heat transfer coefficient": {
                    "Value": {
                        "type": {int,float,},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "power/area/temperature_diff",
                    },
                    "optional": False,
                    "description": "Heat transfer coefficient of the cooler-condenser."
                },  
                "Material weight per area": {
                    "Value": {
                        "type": {int,float,},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "mass/area",
                    },
                    "optional": False,
                    "description": "Mass of metal constituting the exchanger per heat exchange area."
                },   
            },
            "Technical Operating Parameters and Specifications": {
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
            "Main Stream": {
				"Is independent from year":  {
                    "Value": {
                        "type": {int,float,},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "dimensionless",
                    },
                    "optional": True,
                    "description": "if True: all the years behave identically. Else: each year has to be solved."
                },		                
                "Temperature": {
                    "Value": {
                        "type": {dict,},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "absolute_temperature",
                    },
                    "optional": False,
                    "description": "Mixture inlet temperature, dictionary of years whose items are hourly arrays."
                },
                "Pressure": {
                    "Value": {
                        "type": {int,float,},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "pressure",
                    },
                    "optional": False,
                    "description": "Mixture inlet pressure."
                },      
                "Specific enthalpy": {
                    "Value": {
                        "type": {dict,},
                        "bounds": (None, None),
                    },
                    "Unit": {
                        "dimension": "energy/mass",
                    },
                    "optional": False,
                    "description": "Mixture inlet specific enthalpy, dictionary of years whose items are hourly arrays."
                },   
                "Mass fraction": {
                    "Value": {
                        "type": {dict,},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "dimensionless",
                    },
                    "optional": False,
                    "description": "Mixture inlet mass fraction of each component, dictionary of years whose items are hourly arrays."
                }, 
                "Mass flow (hourly)": {
                    "Value": {
                        "type": {dict,},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "mass",
                    },
                    "optional": False,
                    "description": "Mixture outlet mass flow, dictionary of years whose items are hourly arrays."
                },                                          
            },
        }

        self.output_dict = {
            "Cooler Condenser@": {
                "Sizing heat duty": {
                    "Value": {
                        "inserted_value": "sizing_heat_duty",
                        "type": {float,},
                        "dimension": "power",
                    },
                    "optional": False,
                    "description": "Maximum thermal power exchanged in the cooler-condenser (at the plant design capacity)."
                },
                "Heat exchange area": {
                    "Value": {
                        "inserted_value": "heat_exchange_area",
                        "type": {float,},
                        "dimension": "area",
                    },
                    "optional": False,
                    "description": "Heat exchange area of the cooler-condenser, based on plant design capacity."
                }, 
                "Sizing condensed water flowrate": {
                    "Value": {
                        "inserted_value": "peak_condensed_water_flowrate",
                        "type": {float,},
                        "dimension": "mass/time",
                    },
                    "optional": False,
                    "description": "Maximum mass flowrate of the condensed water (at design capacity flowrate)."
                },   
                "Yearly mass of condensed water": {
                    "Value": {
                        "inserted_value": "yearly_condensed_water_mass",
                        "type": {np.ndarray,},
                        "dimension": "mass",
                    },
                    "optional": False,
                    "description": "Mass of the condensed water per year, accounting for operating capacity factor."
                },                     
                "Hourly mass of cooling water": {
                    "Value": {
                        "inserted_value": "hourly_coolant_mass",
                        "type": {dict,},
                        "dimension": "mass",
                    },
                    "optional": False,
                    "description": "Dictionary of years: hourly mass of the cooling water."
                },                                                   
                "Yearly mass of cooling water": {
                    "Value": {
                        "inserted_value": "yearly_coolant_mass",
                        "type": {np.ndarray,},
                        "dimension": "mass",
                    },
                    "optional": False,
                    "description": "Mass of the cooling water used per year, accounting for the operating capacity factor."
                },                                                 
                "Cooling water yearly pumping energy": {
                    "Value": {
                        "inserted_value": "yearly_pumping_energy",
                        "type": {np.ndarray,},
                        "dimension": "energy",
                    },
                    "optional": False,
                    "description": "Energy for the pumping of the cooling water used per year, accounting for the operating capacity factor."
                },                                     
            },
            "Main Stream": {
                "Temperature": {
                    "Value": {
                        "inserted_value": "outlet_temperature",
                        "type": {dict,},
                        "dimension": "absolute_temperature",
                    },
                    "optional": False,
                    "description": "Mixture outlet temperature, dictionary of years whose items are hourly arrays."
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

        plugin_name = 'Cooler_Condenser_Plugin'
        self.cooler_name = 'Cooler Condenser'
        if self.instance_suffix is not None:
            plugin_name = f'{plugin_name} @{self.instance_suffix}'
            self.cooler_name = f'{self.cooler_name} {self.instance_suffix}'
            
        self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, plugin_name)

        self.outlet_stream_properties()
        self.Energy_balance()        
        self.cooler_condenser_sizing()        

        output_inserter_function(self.output_dict, self, dcf, plugin_name) 

        #print(self.cooler_name, ' yearly coolant mass ', self.yearly_coolant_mass)
        #print(self.cooler_name, ' steel mass', self.material_mass)
        #print(self.cooler_name, ' yearly condensed water mass ', self.yearly_condensed_water_mass)
        #print(self.cooler_name, ' yearly cooling energy ', self.yearly_pumping_energy.unit['MWh'])


    def outlet_stream_properties(self):

        psat = PP.Water_saturation_pressure(self.input_dict_resolved[self.cooler_name]['Hot outlet temperature']['Value'])

        self.outlet_temperature = {}
        self.outlet_mass_fraction = {}
        self.hourly_mass_flow = {}
        self.outlet_enthalpy = {}
        self.hourly_condensed_water = {}

        if ('Is independent from year' in self.input_dict_resolved['Main Stream']) and (bool(self.input_dict_resolved['Main Stream']['Is independent from year']['Value'].unit['-']) is True):
            self.years = np.array([0])
        else: 
            self.years = self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-']        

        for year in self.years:
            year = round(year)

            self.outlet_temperature[year] = Quantity(np.full(8760, self.input_dict_resolved[self.cooler_name]['Hot outlet temperature']['Value'].unit['K']), 'K')

            _, inlet_mol_fraction = PP.Mass_to_substance(self.input_dict_resolved['Main Stream']['Mass fraction']['Value'][year])

            inlet_mol_fraction_uncondensable = 1.0 - inlet_mol_fraction['H2O'].unit['-']

            # Variables that apply to the case where the outlet is saturated
            saturation_outlet_mol_fraction_water = psat.unit['Pa'] / self.input_dict_resolved['Main Stream']['Pressure']['Value'].unit['Pa']
            outlet_mol_fraction_uncondensable = 1.0 - saturation_outlet_mol_fraction_water

            is_saturated = inlet_mol_fraction['H2O'].unit['-'] >= saturation_outlet_mol_fraction_water

            uncondensable_fraction_factor = np.where(is_saturated, 
                                                     outlet_mol_fraction_uncondensable / inlet_mol_fraction_uncondensable, 
                                                     1.0)

            outlet_mol_fraction = {species: Quantity(uncondensable_fraction_factor * inlet_mol_fraction[species].unit['-'], 
                                                    '-')
                                    for species in inlet_mol_fraction if species != 'H2O'}
            
            outlet_mol_fraction['H2O'] = Quantity(np.where(is_saturated, 
                                                           saturation_outlet_mol_fraction_water, 
                                                           inlet_mol_fraction['H2O'].unit['-']), 
                                                '-')

            _, self.outlet_mass_fraction[year] = PP.Substance_to_mass(outlet_mol_fraction)

            water_uncondensed_fraction = np.where(
                is_saturated,
                inlet_mol_fraction_uncondensable * psat.unit['Pa'] / (inlet_mol_fraction['H2O'].unit['-'] * (self.input_dict_resolved['Main Stream']['Pressure']['Value'].unit['Pa'] - psat.unit['Pa'])),
                1.0
            )

            self.hourly_condensed_water[year] = Quantity(np.where(is_saturated,
                                                        self.input_dict_resolved['Main Stream']['Mass flow (hourly)']['Value'][year].unit['kg'] 
                                                        * 
                                                        self.input_dict_resolved['Main Stream']['Mass fraction']['Value'][year]['H2O'].unit['-']
                                                        *
                                                        (1.0 - water_uncondensed_fraction),
                                                        0.0), 
                                                        'kg')

            self.hourly_mass_flow[year] = Quantity(self.input_dict_resolved['Main Stream']['Mass flow (hourly)']['Value'][year].unit['kg'] - self.hourly_condensed_water[year].unit['kg'], 'kg')

            h_out = PP.Enthalpy(T=self.input_dict_resolved[self.cooler_name]['Hot outlet temperature']['Value'], 
                                P=self.input_dict_resolved['Main Stream']['Pressure']['Value'].unit['Pa'], 
                                amount=self.outlet_mass_fraction[year], 
                                phase='V', 
                                composition_basis='mass')
            self.outlet_enthalpy[year] = Quantity(h_out.unit['J'], 'J/kg')

        # condensed water enthalpy (constant)
        h_liq = PP.Enthalpy(T=self.input_dict_resolved[self.cooler_name]['Hot outlet temperature']['Value'], 
                            P=self.input_dict_resolved['Main Stream']['Pressure']['Value'].unit['Pa'], 
                            amount={'H2O': Quantity(1., 'kg')}, 
                            phase='L', 
                            composition_basis='mass')
        self.condensed_water_enthalpy = Quantity(h_liq.unit['J'], 'J/kg')

        self.yearly_condensed_water_mass = (self.input_dict_resolved['Technical Operating Parameters and Specifications']['Operating capacity factor']['Value'].unit['-'] 
                                            * 
                                            np.array([np.sum(self.hourly_condensed_water[round(year)].unit['kg']) 
                                            for year in self.years]))

        if ('Is independent from year' in self.input_dict_resolved['Main Stream']) and (bool(self.input_dict_resolved['Main Stream']['Is independent from year']['Value'].unit['-']) is True):
            self.outlet_temperature = {round(year): self.outlet_temperature[0] for year in self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-']}
            self.outlet_mass_fraction = {round(year): self.outlet_mass_fraction[0] for year in self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-']}
            self.hourly_condensed_water = {round(year): self.hourly_condensed_water[0] for year in self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-']}
            self.hourly_mass_flow = {round(year): self.hourly_mass_flow[0] for year in self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-']}
            self.outlet_enthalpy = {round(year): self.outlet_enthalpy[0] for year in self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-']}
            self.yearly_condensed_water_mass = self.yearly_condensed_water_mass[0]*np.ones_like(self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-'])

        self.yearly_condensed_water_mass = Quantity(self.yearly_condensed_water_mass, 'kg')

    def Energy_balance(self):

        nominal_pressure_drop = Quantity(70e3, 'Pa') # hardcoded for the moment to a realistic value
        pump_efficiency = 0.7

        self.hourly_heat_duty = {}
        self.hourly_coolant_mass = {}
        self.yearly_coolant_mass = np.zeros_like(self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-'])
        self.yearly_pumping_energy = np.zeros_like(self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-'])

        for year in self.years:
            year = round(year)

            hourly_heat_duty_J = (self.input_dict_resolved['Main Stream']['Mass flow (hourly)']['Value'][year].unit['kg']
                                       *
                                      self.input_dict_resolved['Main Stream']['Specific enthalpy']['Value'][year].unit['J/kg']
                                      -
                                      self.hourly_mass_flow[year].unit['kg']
                                      *
                                      self.outlet_enthalpy[year].unit['J/kg']
                                      -
                                      self.hourly_condensed_water[year].unit['kg']
                                      *
                                      self.condensed_water_enthalpy.unit['J/kg'])


            self.hourly_heat_duty[year] = Quantity(hourly_heat_duty_J, 'J')

            h_coolant_in = PP.Enthalpy(T=self.input_dict_resolved[self.cooler_name]['Cold inlet temperature']['Value'], 
                            P=self.input_dict_resolved['Main Stream']['Pressure']['Value'].unit['Pa'], 
                            amount={'H2O': Quantity(1., 'kg')}, 
                            phase='L', 
                            composition_basis='mass')

            h_coolant_out = PP.Enthalpy(T=self.input_dict_resolved[self.cooler_name]['Cold outlet temperature']['Value'], 
                            P=self.input_dict_resolved['Main Stream']['Pressure']['Value'].unit['Pa'], 
                            amount={'H2O': Quantity(1., 'kg')}, 
                            phase='L', 
                            composition_basis='mass')            
            
            self.hourly_coolant_mass[year] = Quantity(hourly_heat_duty_J
                                                      /
                                                      (h_coolant_out.unit['J'] - h_coolant_in.unit['J']), # Enthalpy for 1 kg of water
                                                      'kg')

            self.yearly_coolant_mass[year] = np.sum(self.hourly_coolant_mass[year].unit['kg'])

            self.yearly_pumping_energy[year] = (nominal_pressure_drop.unit['Pa'] # Assuming constant rpessure drop. This is conservative, because the pressure drop decreases supra-linearly as the flowrate decreases
                                                * 
                                                np.sum(self.hourly_coolant_mass[year].unit['ton']) # Water : 1 ton ~ 1 m³, pressure drop in Pa * mass in tons = energy 
                                                / 
                                                pump_efficiency)

        if ('Is independent from year' in self.input_dict_resolved['Main Stream']) and (bool(self.input_dict_resolved['Main Stream']['Is independent from year']['Value'].unit['-']) is True):
            self.hourly_heat_duty = {round(year): self.hourly_heat_duty[0] for year in self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-']}
            self.hourly_coolant_mass = {round(year): self.hourly_coolant_mass[0] for year in self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-']}
            self.yearly_coolant_mass = self.yearly_coolant_mass[0]*np.ones_like(self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-'])
            self.yearly_pumping_energy = self.yearly_pumping_energy[0]*np.ones_like(self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-'])

        self.yearly_coolant_mass = Quantity(self.yearly_coolant_mass, 'kg')
        self.yearly_pumping_energy = Quantity(self.yearly_pumping_energy, 'J')


    def cooler_condenser_sizing(self):

        peak_mass_flowrate_kg_h = 0
        peak_condensed_water_flowrate_kg_h = 0
        peak_heat_duty_W = 0
        T_in_peak = 0

        for year in self.years:
            year = round(year)

            peak_mass_flowrate_kg_h = max(np.max(self.hourly_mass_flow[round(year)].unit['kg']), 
                                           peak_mass_flowrate_kg_h)

            peak_condensed_water_flowrate_kg_h = max(np.max(self.hourly_condensed_water[round(year)].unit['kg']), 
                                                    peak_condensed_water_flowrate_kg_h)  

            peak_heat_duty_W  = max(np.max(self.hourly_heat_duty[round(year)].unit['Wh']), 
                                                    peak_heat_duty_W)  
            
            T_in_peak  = max(np.max(self.input_dict_resolved['Main Stream']['Temperature']['Value'][year].unit['K']), 
                                                    T_in_peak)                       

        self.peak_mass_flowrate = Quantity(peak_mass_flowrate_kg_h, 'kg/h')
        self.peak_condensed_water_flowrate = Quantity(peak_condensed_water_flowrate_kg_h, 'kg/h')
        self.sizing_heat_duty = Quantity(peak_heat_duty_W, 'W')

        dT_1 = T_in_peak - self.input_dict_resolved[self.cooler_name]['Cold outlet temperature']['Value'].unit['K']
        dT_2 = self.input_dict_resolved[self.cooler_name]['Hot outlet temperature']['Value'].unit['K'] - self.input_dict_resolved[self.cooler_name]['Cold inlet temperature']['Value'].unit['K']
        Delta_T_average = (dT_1 - dT_2) / math.log(dT_1 / dT_2)

        self.heat_exchange_area = Quantity(
            self.sizing_heat_duty.unit['W'] /
            (self.input_dict_resolved[self.cooler_name]['Heat transfer coefficient']['Value'].unit['W/m2/delta_K'] * Delta_T_average),
            'm2'
        )

        self.material_mass = Quantity(
            self.input_dict_resolved[self.cooler_name]['Material weight per area']['Value'].unit['kg/m2']
            * self.heat_exchange_area.unit['m2'],
            'kg'
        )
