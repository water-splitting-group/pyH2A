from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.Physical_Properties.Physical_properties import Physical_properties as PP
import math

input_dict = {
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

output_dict = {
    "Cooler Condenser": {
        "Heat duty": {
            "Value": {
                "inserted_value": "heat_duty",
                "type": {float,},
                "dimension": "power",
            },
            "optional": False,
            "description": "Heat exchanged in the cooler-condenser."
        },
        "Heat exchange area": {
            "Value": {
                "inserted_value": "heat_exchange_area",
                "type": {float,},
                "dimension": "area",
            },
            "optional": False,
            "description": "Heat exchange area of the cooler-condenser."
        }, 
        "Cooling water flowrate": {
            "Value": {
                "inserted_value": "coolant_flowrate",
                "type": {float,},
                "dimension": "mass/time",
            },
            "optional": False,
            "description": "Mass flowrate of the cooling water."
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
            "description": "Mixture outlet mass flowrate."
        },   					                
    },
}

class Cooler_Condenser_Plugin:
    '''Simulation of humid gas mixture cooling with condensation.
    The pressure stays constant during the compression. The other properties of the Main Stream are updated.

    Parameters
    ----------
    Cooler Condenser > Cold inlet temperature > Value : float
        Temperature of the cold fluid inlet.
    Cooler Condenser > Cold outlet temperature > Value : float
        Temperature of the cold fluid outlet.
    Cooler Condenser > Hot outlet temperature > Value : float
        Temperature of the hot fluid outlet.        
    Cooler Condenser > Heat transfer coefficient > Value : float
        Heat transfer coefficient of the exchanger 
    Cooler Condenser > Material weight per area > Value : float
        Mass of metal constituting the exchanger per heat exchange area     
	Main Stream > Temperature > Value : float
		Temperature of the gas mixture at compressor inlet
	Main Stream > Pressure > Value : float
		Pressure of the gas mixture at compressor inlet	
	Main Stream > Specific enthalpy > Value : float
		Mass-specific enthalpy of the gas mixture at compressor inlet
	Main Stream > Mass fraction > Value : dict
		Mass fraction of the gas mixture at compressor inlet			
	Main Stream > Mass flowrate > Value : float
		Mass flowrate of the gas mixture at compressor inlet	


    Returns
    -------
    Cooler Condenser > Heat duty > Value : float
        Heat exchanged in the cooler-condenser
    Cooler Condenser > Heat exchange area > Value : float
        Heat exchange area of the cooler-condenser  
    Cooler Condenser > Cooling water flowrate > Value : float
        Mass flowrate of the cooling water      
	Main Stream > Temperature > Value : float
		Temperature of the gas mixture at cooler-condenser main outlet	
	Main Stream > Specific enthalpy > Value : float
		Mass-specific enthalpy of the gas mixture at cooler-condenser main outlet	
	Main Stream > Mass fraction > Value : dict
		Mass fraction of the gas mixture at cooler-condenser main outlet	
	Main Stream > Mass flowrate > Value : float
		Mass flowrate of the gas mixture at cooler-condenser main outlet	

    '''

    def __init__(self, dcf, print_info):

        self.input_dict_resolved = input_resolver_function(input_dict, dcf, 'Cooler_Condenser_Plugin')

        self.outlet_stream_properties()
        self.cooler_condenser_sizing()

        output_inserter_function(output_dict, self, dcf, 'Cooler_Condenser_Plugin') 


    def outlet_stream_properties(self):
        '''Using inlet stream and compressor characteristics, shaft work and outlet stream porperties are calculated.
        '''

        # outlet temperature of the main stream is imposed:
        self.outlet_temperature = self.input_dict_resolved['Cooler Condenser']['Hot outlet temperature']['Value']

        # determine if the outlet reaches saturation
        _, inlet_mol_fraction = PP.Mass_to_substance(self.input_dict_resolved['Main Stream']['Mass fraction']['Value'])
        psat = PP.Water_saturation_pressure(self.outlet_temperature)

        if inlet_mol_fraction['H2O'].unit['-'] * self.input_dict_resolved['Main Stream']['Pressure']['Value'].unit['Pa'] < psat.unit['Pa']: 
            # outlet fluid doesn't reach saturation, no condensation occurs, and the outlet composition is identical to the inlet one
            self.outlet_mass_fraction = self.input_dict_resolved['Main Stream']['Mass fraction']['Value']
            self.outlet_mass_flowrate = self.input_dict_resolved['Main Stream']['Mass flowrate']['Value']

            self.condensed_water_flowrate = Quantity(0, 'kg/s')
            self.condensed_water_enthalpy = Quantity(0, 'J/kg') # dummy


            h = PP.Enthalpy(T = self.outlet_temperature,
                            P = self.input_dict_resolved['Main Stream']['Pressure']['Value'].unit['Pa'], 
                            amount = self.outlet_mass_fraction, 
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

            condensed_water_flowrate = (self.input_dict_resolved['Main Stream']['Mass flowrate']['Value'].unit['kg/s'] 
                                        * 
                                        (1-water_uncondensed_fraction) 
                                        * 
                                        self.input_dict_resolved['Main Stream']['Mass fraction']['Value']['H2O'].unit['-']
                                        )
            self.condensed_water_flowrate = Quantity(condensed_water_flowrate, 'kg/s')

            # the part of water that was condensed is excluded from the main (vapour phase) stream
            self.outlet_mass_flowrate = Quantity(self.input_dict_resolved['Main Stream']['Mass flowrate']['Value'].unit['kg/s'] - condensed_water_flowrate,
                                                'kg/s')

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


    def cooler_condenser_sizing(self):
        '''
        Calculates the thermal power transfer between the hot and the cold fluid and subsequent heat exchange area.
        Also calculates the cooling fluid flowrate andthe mass of stainless steel constituting the exchanger.
        '''

        heat_duty = (
            self.input_dict_resolved['Main Stream']['Mass flowrate']['Value'].unit['kg/s']
            *
            self.input_dict_resolved['Main Stream']['Specific enthalpy']['Value'].unit['J/kg']
            -
            (
             self.outlet_mass_flowrate.unit['kg/s'] * self.outlet_enthalpy.unit['J/kg']
             +
             self.condensed_water_flowrate.unit['kg/s'] * self.condensed_water_enthalpy.unit['J/kg']
            )

        )
        self.heat_duty = Quantity(heat_duty, 'W')           
                
        # log-mean delta temperature. This doesn't normally apply to the condensation case, but we use a unique formula for simplification purposes
        dT_1 = self.input_dict_resolved['Main Stream']['Temperature']['Value'].unit['K'] - self.input_dict_resolved['Cooler Condenser']['Cold outlet temperature']['Value'].unit['K']
        dT_2 = self.outlet_temperature.unit['K'] - self.input_dict_resolved['Cooler Condenser']['Cold inlet temperature']['Value'].unit['K']
        Delta_T_average = (
            (dT_1-dT_2)
            /
            (math.log(dT_1/dT_2))
            )

        self.heat_exchange_area = Quantity(self.heat_duty.unit['W']
                                            /
                                                (
                                                self.input_dict_resolved['Cooler Condenser']['Heat transfer coefficient']['Value'].unit['W/m2/delta_K']
                                                *
                                                Delta_T_average
                                                ), 
                                            'm2')
        

        # cooling fluid enthalpy at inlet and outlet
        inlet_coolant_h = PP.Enthalpy(T = self.input_dict_resolved['Cooler Condenser']['Cold inlet temperature']['Value'],
                        P = self.input_dict_resolved['Main Stream']['Pressure']['Value'].unit['Pa'], # dummy
                        amount = {'H2O': Quantity(1., 'kg')}, 
                        phase = 'L', 
                        composition_basis = 'mass'
                        )        
        
        outlet_coolant_h = PP.Enthalpy(T = self.input_dict_resolved['Cooler Condenser']['Cold outlet temperature']['Value'],
                        P = self.input_dict_resolved['Main Stream']['Pressure']['Value'].unit['Pa'], # dummy
                        amount = {'H2O': Quantity(1., 'kg')}, 
                        phase = 'L', 
                        composition_basis = 'mass'
                        )  

        self.coolant_flowrate = Quantity(self.heat_duty.unit['W']
                                         /
                                         (outlet_coolant_h.unit['J']-inlet_coolant_h.unit['J']), 
                                         'kg/s')

        self.material_mass = Quantity(self.input_dict_resolved['Cooler Condenser']['Material weight per area']['Value'].unit['kg/m2']
                                      *  self.heat_exchange_area.unit['m2'],
                                        'kg')



