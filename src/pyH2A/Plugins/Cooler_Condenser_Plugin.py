from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.Physical_Properties.Physical_properties import Physical_properties as PP
import math

class Cooler_Condenser_Plugin:
    '''Simulation of humid gas mixture cooling with condensation.
    The pressure stays constant during the compression. The other properties of the Main Stream are updated.
    '''
    def __init__(self, dcf, print_info, run = True):
        self._set_up(dcf)
        if run:
            self._run(dcf)

    def _set_up(self, dcf):

        self.functional_unit = dcf.functional_unit   

        self.input_dict = {
            "Cooler Condenser": {
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
                "Mass flowrate": {
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
        }

        self.output_dict = {
            "Cooler Condenser": {
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
                        "inserted_value": "max_condensed_water_flowrate",
                        "type": {float,},
                        "dimension": "mass/time",
                    },
                    "optional": False,
                    "description": "Maximum mass flowrate of the condensed water (at design capacity flowrate)."
                },   
                "Yearly mass of condensed water": {
                    "Value": {
                        "inserted_value": "yearly_condensed_water_mass",
                        "type": {float,},
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
                "Yearly mass of cooling water": {
                    "Value": {
                        "inserted_value": "yearly_coolant_mass",
                        "type": {float,},
                        "dimension": "mass",
                    },
                    "optional": False,
                    "description": "Mass of the cooling water used per year, accounting for the operating capacity factor."
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
                "Mass flowrate": {
                    "Value": {
                        "inserted_value": "outlet_mass_flowrate",
                        "type": {float,},
                        "dimension": "mass/time",
                    },
                    "optional": False,
                    "description": "Mixture outlet mass flowrate, at design capacity flowrate."
                },   					                
            },
        }


    def _run(self, dcf):    

        self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, 'Cooler_Condenser_Plugin')

        (self.outlet_temperature,
         self.outlet_mass_fraction, 
         self.outlet_mass_flowrate,
         self.condensed_water_enthalpy, 
         self.outlet_enthalpy, 
         self.max_condensed_water_flowrate,
         self.yearly_condensed_water_mass
         ) = outlet_stream_properties(self.input_dict_resolved)


        (self.sizing_heat_duty,
         self.heat_exchange_area, 
         self.max_coolant_flowrate,
         self.yearly_coolant_mass,
         self.material_mass
        ) = cooler_condenser_sizing(self.input_dict_resolved, 
                                    self.outlet_temperature,
                                    self.outlet_enthalpy, 
                                    self.outlet_mass_flowrate, 
                                    self.max_condensed_water_flowrate, 
                                    self.condensed_water_enthalpy)

        output_inserter_function(self.output_dict, self, dcf, 'Cooler_Condenser_Plugin') 

        print('cooler 1 yearly_coolant_mass ', self.yearly_coolant_mass)
        print('cooler 1 material_mass', self.material_mass)
        print('cooler 1 yearly_condensed_water_mass ', self.yearly_condensed_water_mass)


def outlet_stream_properties(dictionary):
    '''Calculate the mass flowrate, composition and enthalpy at the outlet of the main stream and the eventual condensed water stream.
    '''

    # outlet temperature of the main stream is imposed:
    outlet_temperature = dictionary['Cooler Condenser']['Hot outlet temperature']['Value']

    # determine if the outlet reaches saturation
    _, inlet_mol_fraction = PP.Mass_to_substance(dictionary['Main Stream']['Mass fraction']['Value'])
    psat = PP.Water_saturation_pressure(outlet_temperature)

    if inlet_mol_fraction['H2O'].unit['-'] * dictionary['Main Stream']['Pressure']['Value'].unit['Pa'] < psat.unit['Pa']: 
        # outlet fluid doesn't reach saturation, no condensation occurs, and the outlet composition is identical to the inlet one
        outlet_mass_fraction = dictionary['Main Stream']['Mass fraction']['Value']
        outlet_mass_flowrate = dictionary['Main Stream']['Mass flowrate']['Value']

        max_condensed_water_flowrate = Quantity(0, 'kg/s')
        condensed_water_enthalpy = Quantity(0, 'J/kg') # dummy


        h = PP.Enthalpy(T = outlet_temperature,
                        P = dictionary['Main Stream']['Pressure']['Value'].unit['Pa'], 
                        amount = outlet_mass_fraction, 
                        phase = 'V', 
                        composition_basis = 'mass'
                        )
        
        outlet_enthalpy = Quantity(h.unit['J'], 'J/kg')


        
    else:
        # part of the water was condensed. Water pressure is therefore equal to saturation pressure, and the fraction of the other species is updated accordingly
        outlet_mol_fraction_water = psat.unit['Pa']/dictionary['Main Stream']['Pressure']['Value'].unit['Pa']
        # inlet mole fraction is necessary to determine how outlet mole fractions are updated due to water condensation
        _, inlet_mol_fraction = PP.Mass_to_substance(dictionary['Main Stream']['Mass fraction']['Value'])
        # fraction of gas phase that is not due to vapour
        inlet_mol_fraction_uncondensable = 1-inlet_mol_fraction['H2O'].unit['-']
        outlet_mol_fraction_uncondensable = 1-outlet_mol_fraction_water
        uncondensable_fraction_factor = outlet_mol_fraction_uncondensable / inlet_mol_fraction_uncondensable
        outlet_mol_fraction = {species: Quantity(uncondensable_fraction_factor * inlet_mol_fraction[species].unit['-'], '-') for species in inlet_mol_fraction.keys() if species != 'H2O'}
        outlet_mol_fraction['H2O'] = Quantity(outlet_mol_fraction_water, '-')

        _, outlet_mass_fraction = PP.Substance_to_mass(outlet_mol_fraction) # mass fraction in the gas phase

        # fraction of water vapour at the outlet, compared to the total (liquid + vapour) water: m_vap/(m_vap+m_liq)
        water_uncondensed_fraction = (
            inlet_mol_fraction_uncondensable * psat.unit['Pa']
            /
            (inlet_mol_fraction['H2O'].unit['-'] 
                * 
                (dictionary['Main Stream']['Pressure']['Value'].unit['Pa'] - psat.unit['Pa'])
                )
        )

        max_condensed_water_flowrate = (dictionary['Main Stream']['Mass flowrate']['Value'].unit['kg/s'] 
                                    * 
                                    (1-water_uncondensed_fraction) 
                                    * 
                                    dictionary['Main Stream']['Mass fraction']['Value']['H2O'].unit['-']
                                    )
        max_condensed_water_flowrate = Quantity(max_condensed_water_flowrate, 'kg/s')

        # the part of water that was condensed is excluded from the main (vapour phase) stream
        outlet_mass_flowrate = Quantity(dictionary['Main Stream']['Mass flowrate']['Value'].unit['kg/s'] - max_condensed_water_flowrate.unit['kg/s'],
                                            'kg/s')

        # Main stream outlet enthalpy
        h = PP.Enthalpy(T = outlet_temperature,
                        P = dictionary['Main Stream']['Pressure']['Value'].unit['Pa'], 
                        amount = outlet_mass_fraction, 
                        phase = 'V', 
                        composition_basis = 'mass'
                        )
        
        outlet_enthalpy = Quantity(h.unit['J'], 'J/kg')

        # Condensed water outlet enthalpy
        h = PP.Enthalpy(T = outlet_temperature,
                        P = dictionary['Main Stream']['Pressure']['Value'].unit['Pa'], 
                        amount = {'H2O': Quantity(1., 'kg')}, 
                        phase = 'L', 
                        composition_basis = 'mass'
                        )
                    
        condensed_water_enthalpy = Quantity(h.unit['J'], 'J/kg')

    yearly_condensed_water_mass = Quantity(
        dictionary['Technical Operating Parameters and Specifications']['Operating capacity factor']['Value'].unit['-']
        *
        max_condensed_water_flowrate.unit['kg/year'], 
        'kg'
        )

    return (outlet_temperature, 
            outlet_mass_fraction, 
            outlet_mass_flowrate, 
            condensed_water_enthalpy, 
            outlet_enthalpy,
            max_condensed_water_flowrate,
            yearly_condensed_water_mass
            )

def cooler_condenser_sizing(dictionary, outlet_temperature, outlet_enthalpy, outlet_mass_flowrate, max_condensed_water_flowrate, condensed_water_enthalpy):
    '''
    Calculates the thermal power transfer between the hot and the cold fluid and subsequent heat exchange area.
    Also calculates the cooling fluid flowrate andthe mass of stainless steel constituting the exchanger.
    '''

    sizing_heat_duty = (
        dictionary['Main Stream']['Mass flowrate']['Value'].unit['kg/s']
        *
        dictionary['Main Stream']['Specific enthalpy']['Value'].unit['J/kg']
        -
        (
            outlet_mass_flowrate.unit['kg/s'] * outlet_enthalpy.unit['J/kg']
            +
            max_condensed_water_flowrate.unit['kg/s'] * condensed_water_enthalpy.unit['J/kg']
        )

    )
    sizing_heat_duty = Quantity(sizing_heat_duty, 'W')           
            
    # log-mean delta temperature. This doesn't normally apply to the condensation case, but we use a unique formula for simplification purposes
    dT_1 = dictionary['Main Stream']['Temperature']['Value'].unit['K'] - dictionary['Cooler Condenser']['Cold outlet temperature']['Value'].unit['K']
    dT_2 = outlet_temperature.unit['K'] - dictionary['Cooler Condenser']['Cold inlet temperature']['Value'].unit['K']
    Delta_T_average = (
        (dT_1-dT_2)
        /
        (math.log(dT_1/dT_2))
        )

    heat_exchange_area = Quantity(sizing_heat_duty.unit['W']
                                        /
                                            (
                                            dictionary['Cooler Condenser']['Heat transfer coefficient']['Value'].unit['W/m2/delta_K']
                                            *
                                            Delta_T_average
                                            ), 
                                        'm2')
    

    # cooling fluid enthalpy at inlet and outlet
    inlet_coolant_h = PP.Enthalpy(T = dictionary['Cooler Condenser']['Cold inlet temperature']['Value'],
                    P = dictionary['Main Stream']['Pressure']['Value'].unit['Pa'], # dummy
                    amount = {'H2O': Quantity(1., 'kg')}, 
                    phase = 'L', 
                    composition_basis = 'mass'
                    )        
    
    outlet_coolant_h = PP.Enthalpy(T = dictionary['Cooler Condenser']['Cold outlet temperature']['Value'],
                    P = dictionary['Main Stream']['Pressure']['Value'].unit['Pa'], # dummy
                    amount = {'H2O': Quantity(1., 'kg')}, 
                    phase = 'L', 
                    composition_basis = 'mass'
                    )  


    max_coolant_flowrate = Quantity(sizing_heat_duty.unit['W']
                                        /
                                        (outlet_coolant_h.unit['J']-inlet_coolant_h.unit['J']), 
                                        'kg/s')
    
    yearly_coolant_mass = Quantity(dictionary['Technical Operating Parameters and Specifications']['Operating capacity factor']['Value'].unit['-']
                                        *
                                        max_coolant_flowrate.unit['kg/year'], 
                                        'kg')

    material_mass = Quantity(dictionary['Cooler Condenser']['Material weight per area']['Value'].unit['kg/m2']
                                    *  heat_exchange_area.unit['m2'],
                                    'kg')

    return sizing_heat_duty, heat_exchange_area, max_coolant_flowrate, yearly_coolant_mass, material_mass





