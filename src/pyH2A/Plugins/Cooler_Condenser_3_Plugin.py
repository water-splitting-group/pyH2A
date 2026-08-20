from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Plugins.Cooler_Condenser_Plugin import outlet_stream_properties, cooler_condenser_sizing
import numpy as np


class Cooler_Condenser_3_Plugin:
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
                "Yearly mass flow": {
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
            "Cooler Condenser 3": {
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
                "Yearly mass of cooling water": {
                    "Value": {
                        "inserted_value": "yearly_coolant_mass",
                        "type": {np.ndarray,},
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
                "Yearly mass flow": {
                    "Value": {
                        "inserted_value": "yearly_mass_flow",
                        "type": {np.ndarray,},
                        "dimension": "mass",
                    },
                    "optional": False,
                    "description": "Mixture outlet mass per year, excluding operating capacity factor (array of years).."
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

        self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, 'Cooler_Condenser_3_Plugin')

        (self.outlet_temperature,
         self.outlet_mass_fraction, 
         self.yearly_mass_flow,
         self.peak_mass_flowrate,
         self.condensed_water_enthalpy, 
         self.outlet_enthalpy, 
         self.peak_condensed_water_flowrate,
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
                                    self.yearly_mass_flow, 
                                    self.peak_mass_flowrate,
                                    self.peak_condensed_water_flowrate, 
                                    self.condensed_water_enthalpy)

        output_inserter_function(self.output_dict, self, dcf, 'Cooler_Condenser_3_Plugin') 

        print('cooler 3 yearly coolant mass ', self.yearly_coolant_mass)
        print('cooler 3 steel mass', self.material_mass)
        print('cooler 3 yearly condensed water mass ', self.yearly_condensed_water_mass)
