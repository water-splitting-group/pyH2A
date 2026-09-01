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
                "Temperature": {
                    "Value": {
                        "type": {int,float,},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "absolute_temperature",
                    },
                    "optional": False,
                    "description": "Mixture inlet temperature."
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
                        "type": {int,float,},
                        "bounds": (None, None),
                    },
                    "Unit": {
                        "dimension": "energy/mass",
                    },
                    "optional": False,
                    "description": "Mixture inlet specific enthalpy."
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
                    "description": "Mixture inlet mass fraction of each component."
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
                "Design mass flow by year": {
                    "Value": {
                        "type": {np.ndarray,},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "mass",
                    },
                    "optional": False,
                    "description": "Mixture inlet mass per year, excluding operating capacity factor (array of years)."
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
                    "description": "Mixture inlet mass flowrate on peak production day."
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
                "Sizing cooling water flowrate": {
                    "Value": {
                        "inserted_value": "max_coolant_flowrate",
                        "type": {float,},
                        "dimension": "mass/time",
                    },
                    "optional": False,
                    "description": "Maximum mass flowrate of the cooling water (at design capacity flowrate)."
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
                "Cooling water hourly pumping energy": {
                    "Value": {
                        "inserted_value": "hourly_pumping_energy",
                        "type": {dict,},
                        "dimension": "energy",
                    },
                    "optional": False,
                    "description": "Dictionary of years: hourly energy for the pumping of the cooling water."
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
                        "type": {float,},
                        "dimension": "absolute_temperature",
                    },
                    "optional": False,
                    "description": "Mixture outlet temperature."
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
                    "description": "Mixture outlet mass per year, excluding operating capacity factor (array of years)."
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

        plugin_name = 'Cooler_Condenser_Plugin'
        self.cooler_name = 'Cooler Condenser'

        if self.instance_suffix is not None:
            plugin_name = f'{plugin_name} @{self.instance_suffix}'
            self.cooler_name = f'{self.cooler_name} {self.instance_suffix}'
            
        self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, plugin_name)

        self.outlet_stream_properties()


        self.cooler_condenser_sizing()

        self.Coolant_operation()        

        output_inserter_function(self.output_dict, self, dcf, plugin_name) 

        print(self.cooler_name, ' yearly coolant mass ', self.yearly_coolant_mass)
        print(self.cooler_name, ' steel mass', self.material_mass)
        print(self.cooler_name, ' yearly condensed water mass ', self.yearly_condensed_water_mass)
        print(self.cooler_name, ' yearly cooling energy ', self.yearly_pumping_energy.unit['MWh'])


    def outlet_stream_properties(self):
        '''Calculate the mass flowrate, composition and enthalpy at the outlet of the main stream and the eventual condensed water stream.
        '''

        # outlet temperature of the main stream is imposed:
        self.outlet_temperature = self.input_dict_resolved[self.cooler_name]['Hot outlet temperature']['Value']

        # determine if the outlet reaches saturation
        _, inlet_mol_fraction = PP.Mass_to_substance(self.input_dict_resolved['Main Stream']['Mass fraction']['Value'])
        psat = PP.Water_saturation_pressure(self.outlet_temperature)

        if inlet_mol_fraction['H2O'].unit['-'] * self.input_dict_resolved['Main Stream']['Pressure']['Value'].unit['Pa'] < psat.unit['Pa']: 
            # outlet fluid doesn't reach saturation, no condensation occurs, and the outlet composition is identical to the inlet one
            self.outlet_mass_fraction = self.input_dict_resolved['Main Stream']['Mass fraction']['Value']
            self.yearly_mass_flow = self.input_dict_resolved['Main Stream']['Design mass flow by year']['Value']
            self.hourly_mass_flow = self.input_dict_resolved['Main Stream']['Mass flow (hourly)']['Value']
            self.peak_mass_flowrate = self.input_dict_resolved['Main Stream']['Peak mass flowrate']['Value']

            self.peak_condensed_water_flowrate = Quantity(0, 'kg/s')
            self.condensed_water_enthalpy = Quantity(0, 'J/kg') # dummy


            h = PP.Enthalpy(T = outlet_temperature,
                            P = dictionary['Main Stream']['Pressure']['Value'].unit['Pa'], 
                            amount = outlet_mass_fraction, 
                            phase = 'V', 
                            composition_basis = 'mass'
                            )
            
            self.outlet_enthalpy = Quantity(h.unit['J'], 'J/kg')


            
        else:
            # part of the water was condensed. Water pressure is therefore equal to saturation pressure, and the fraction of the other species is updated accordingly
            outlet_mol_fraction_water = psat.unit['Pa']/self.input_dict_resolved['Main Stream']['Pressure']['Value'].unit['Pa']
            # inlet mole fraction is necessary to determine how outlet mole fractions are updated due to water condensation
            _, inlet_mol_fraction = PP.Mass_to_substance(self.input_dict_resolved['Main Stream']['Mass fraction']['Value'])
            # fraction of gas phase that is not due to vapour
            inlet_mol_fraction_uncondensable = 1-inlet_mol_fraction['H2O'].unit['-']
            outlet_mol_fraction_uncondensable = 1-outlet_mol_fraction_water
            uncondensable_fraction_factor = outlet_mol_fraction_uncondensable / inlet_mol_fraction_uncondensable
            outlet_mol_fraction = {species: Quantity(uncondensable_fraction_factor * inlet_mol_fraction[species].unit['-'], '-') for species in inlet_mol_fraction.keys() if species != 'H2O'}
            outlet_mol_fraction['H2O'] = Quantity(outlet_mol_fraction_water, '-')

            _, self.outlet_mass_fraction = PP.Substance_to_mass(outlet_mol_fraction) # mass fraction in the gas phase

            # fraction of water vapour at the outlet, compared to the total (liquid + vapour) water: m_vap/(m_vap+m_liq)
            water_uncondensed_fraction = (
                inlet_mol_fraction_uncondensable * psat.unit['Pa']
                /
                (inlet_mol_fraction['H2O'].unit['-'] 
                    * 
                    (self.input_dict_resolved['Main Stream']['Pressure']['Value'].unit['Pa'] - psat.unit['Pa'])
                    )
            )

            peak_condensed_water_flowrate = (self.input_dict_resolved['Main Stream']['Peak mass flowrate']['Value'].unit['kg/s'] 
                                        * 
                                        (1-water_uncondensed_fraction) 
                                        * 
                                        self.input_dict_resolved['Main Stream']['Mass fraction']['Value']['H2O'].unit['-']
                                        )
            self.peak_condensed_water_flowrate = Quantity(peak_condensed_water_flowrate, 'kg/s')

            # the part of water that was condensed is excluded from the main (vapour phase) stream
            self.peak_mass_flowrate = Quantity(self.input_dict_resolved['Main Stream']['Peak mass flowrate']['Value'].unit['kg/s'] - self.peak_condensed_water_flowrate.unit['kg/s'],
                                                'kg/s')

            self.hourly_mass_flow = {}
            for year in self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-']:
                year = round(year)
                self.hourly_mass_flow[year] = Quantity(self.peak_mass_flowrate.unit['kg/s'] 
                                * 
                                self.input_dict_resolved['Main Stream']['Mass flow (hourly)']['Value'][year].unit['kg'] 
                                / 
                                self.input_dict_resolved['Main Stream']['Peak mass flowrate']['Value'].unit['kg/s'], 
                                'kg')

            self.yearly_mass_flow = Quantity(self.peak_mass_flowrate.unit['kg/s'] 
                                * 
                                self.input_dict_resolved['Main Stream']['Design mass flow by year']['Value'].unit['kg'] 
                                / 
                                self.input_dict_resolved['Main Stream']['Peak mass flowrate']['Value'].unit['kg/s'], 
                                'kg')

            # Main stream outlet enthalpy
            h = PP.Enthalpy(T = self.outlet_temperature,
                            P = self.input_dict_resolved['Main Stream']['Pressure']['Value'].unit['Pa'], 
                            amount = self.outlet_mass_fraction, 
                            phase = 'V', 
                            composition_basis = 'mass'
                            )
            
            self.outlet_enthalpy = Quantity(h.unit['J'], 'J/kg')

            # Condensed water outlet enthalpy
            h = PP.Enthalpy(T = self.outlet_temperature,
                            P = self.input_dict_resolved['Main Stream']['Pressure']['Value'].unit['Pa'], 
                            amount = {'H2O': Quantity(1., 'kg')}, 
                            phase = 'L', 
                            composition_basis = 'mass'
                            )
                        
            self.condensed_water_enthalpy = Quantity(h.unit['J'], 'J/kg')

        
        self.yearly_condensed_water_mass = Quantity(
            self.input_dict_resolved['Technical Operating Parameters and Specifications']['Operating capacity factor']['Value'].unit['-']
            *
            self.input_dict_resolved['Main Stream']['Design mass flow by year']['Value'].unit['kg']
            *
            self.peak_condensed_water_flowrate.unit['kg/s']
            /
            self.input_dict_resolved['Main Stream']['Peak mass flowrate']['Value'].unit['kg/s'], 
            'kg')


    def cooler_condenser_sizing(self):
        '''
        Calculates the thermal power transfer between the hot and the cold fluid at peak production, and subsequent required heat exchange area.
        Also calculates the cooling fluid peak flowrate and the mass of stainless steel constituting the exchanger.
        '''

        sizing_heat_duty = (
            self.input_dict_resolved['Main Stream']['Peak mass flowrate']['Value'].unit['kg/s']
            *
            self.input_dict_resolved['Main Stream']['Specific enthalpy']['Value'].unit['J/kg']
            -
            (
                self.peak_mass_flowrate.unit['kg/s'] * self.outlet_enthalpy.unit['J/kg']
                +
                self.peak_condensed_water_flowrate.unit['kg/s'] * self.condensed_water_enthalpy.unit['J/kg']
            )

        )
        self.sizing_heat_duty = Quantity(sizing_heat_duty, 'W')           
                
        # log-mean delta temperature. This doesn't normally apply to the condensation case, but we use a unique formula for simplification purposes
        dT_1 = self.input_dict_resolved['Main Stream']['Temperature']['Value'].unit['K'] - self.input_dict_resolved[self.cooler_name]['Cold outlet temperature']['Value'].unit['K']
        dT_2 = self.outlet_temperature.unit['K'] - self.input_dict_resolved[self.cooler_name]['Cold inlet temperature']['Value'].unit['K']
        Delta_T_average = (
            (dT_1-dT_2)
            /
            (math.log(dT_1/dT_2))
            )

        self.heat_exchange_area = Quantity(self.sizing_heat_duty.unit['W']
                                            /
                                                (
                                                self.input_dict_resolved[self.cooler_name]['Heat transfer coefficient']['Value'].unit['W/m2/delta_K']
                                                *
                                                Delta_T_average
                                                ), 
                                            'm2')
        

        # cooling fluid enthalpy at inlet and outlet
        self.inlet_coolant_h = PP.Enthalpy(T = self.input_dict_resolved[self.cooler_name]['Cold inlet temperature']['Value'],
                        P = self.input_dict_resolved['Main Stream']['Pressure']['Value'].unit['Pa'], # dummy
                        amount = {'H2O': Quantity(1., 'kg')}, 
                        phase = 'L', 
                        composition_basis = 'mass'
                        )        
        
        self.outlet_coolant_h = PP.Enthalpy(T = self.input_dict_resolved[self.cooler_name]['Cold outlet temperature']['Value'],
                        P = self.input_dict_resolved['Main Stream']['Pressure']['Value'].unit['Pa'], # dummy
                        amount = {'H2O': Quantity(1., 'kg')}, 
                        phase = 'L', 
                        composition_basis = 'mass'
                        )  


        self.max_coolant_flowrate = Quantity(self.sizing_heat_duty.unit['W']
                                            /
                                            (self.outlet_coolant_h.unit['J']-self.inlet_coolant_h.unit['J']), 
                                            'kg/s')

        self.material_mass = Quantity(self.input_dict_resolved[self.cooler_name]['Material weight per area']['Value'].unit['kg/m2']
                                    *  self.heat_exchange_area.unit['m2'],
                                    'kg')

    def Coolant_operation(self):
        '''
        Calculates the hourly flowrate of coolant and the required pumping effort.
        '''
        
        nominal_pressure_drop = Quantity(70e3, 'Pa') # Pressure drop in the cooler-condenser on the cooling water side, at maximal coolant flowrate. 
                                                    # Arbitrary realistic value: 70 kPa (Thermal Design - Heat Sinks, Thermoelectrics,Heat Pipes, Compact Heat Exchangers, and Solar Cells, HoSung Lee, 2011)

        pump_efficiency = 0.7 # hardcoded for the moment, since pumping is negligible compared to compression anyway
        self.nominal_pumping_power = Quantity(nominal_pressure_drop.unit['Pa'] 
                                        * 
                                        self.max_coolant_flowrate.unit['ton/s'] # for water 1 ton ~ 1 m3, so the mass flowrate in ton/s = volume flowrate in m3/s
                                        /
                                        pump_efficiency, 
                                        'W')

        self.hourly_coolant_mass = {}
        self.hourly_pumping_energy = {}
        yearly_pumping_Wh = np.zeros_like(self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-'])
        for year in self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-']:
            year = round(year)
            self.hourly_coolant_mass[year] = Quantity(self.max_coolant_flowrate.unit['kg/year']
                                                    *
                                                    self.hourly_mass_flow[year].unit['kg']
                                                    / 
                                                    self.peak_mass_flowrate.unit['kg/year'], 
                                                    'kg')
            # The pumping power varies as the cube of the flowrate
            # However, in practice, one avoids using too low a liquid velocity, rarely below, say, half of the peak flowrate. 
            # So we consider the pumping power is always, at least, 1/2**3 the peak pumping power
            flowrate_ratio = self.hourly_coolant_mass[year].unit['kg']/self.max_coolant_flowrate.unit['kg/h'] 
            self.hourly_pumping_energy[year] = Quantity(self.nominal_pumping_power.unit['W'] 
                                                * 
                                                np.maximum(0.125, flowrate_ratio**3), 
                                                'Wh')
            yearly_pumping_Wh[year] = np.sum(self.hourly_pumping_energy[year].unit['Wh'])

        self.yearly_pumping_energy = Quantity(self.input_dict_resolved['Technical Operating Parameters and Specifications']['Operating capacity factor']['Value'].unit['-']
                                        *
                                        yearly_pumping_Wh, 'Wh')


        self.coolant_flow_yearly_kg = (self.max_coolant_flowrate.unit['kg/year']
                                        *
                                        self.yearly_mass_flow.unit['kg']
                                        / 
                                        self.peak_mass_flowrate.unit['kg/year'])
            
        self.yearly_coolant_mass = Quantity(self.input_dict_resolved['Technical Operating Parameters and Specifications']['Operating capacity factor']['Value'].unit['-']
                                            *
                                            self.coolant_flow_yearly_kg, 
                                            'kg')




