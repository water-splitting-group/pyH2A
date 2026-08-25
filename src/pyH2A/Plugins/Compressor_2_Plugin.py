from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Plugins.Compressor_Plugin import calculate_compression
import numpy as np


class Compressor_2_Plugin:
    '''Simulation of gas mixture adiabatic compression.
    If the polytropic coefficient corresponds to the ideal case (heat capacity ratio), then the efficiency must account for both the non-ideality of the compression and the mechanical losses.
    If the non-ideality of the compression is taken into account via the polytropic coefficient (from constructor data), then the efficiency must include mechanical losses only. 
    The total mass flowrate and composition stay constant during the compression. The other properties of the Main Stream are updated. 

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
            "Compressor 2": {
                "Compression ratio": {
                    "Value": {
                        "type": {int,float,},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "dimensionless",
                    },
                    "optional": False,
                    "description": "Outlet pressure divided by inlet pressure of the compressor."
                },
                "Polytropic coefficient": {
                    "Value": {
                        "type": {int,float,},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "dimensionless",
                    },
                    "optional": True,
                    "description": "Polytropic coefficient of the compression. Defaults to the heat capacity ratio if diatomic ideal gas (1.4)"
                },
                "Efficiency": {
                    "Value": {
                        "type": {int,float,},
                        "bounds": (0, 1),
                    },
                    "Unit": {
                        "dimension": "dimensionless",
                    },
                    "optional": False,
                    "description": "Compression work per shaft work provided to the compressor."
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
                        "type": {int, float,},
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
                        "type": {int, float,},
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
                        "type": {int, float,},
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
                        "type": {int, float,},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "mass/time",
                    },
                    "optional": False,
                    "description": "Mixture outlet mass flowrate on peak production day."
                },                                           
            },
        }

        self.output_dict = {
            "Compressor 2": {
                "Peak compression power": {
                    "Value": {
                        "inserted_value": "peak_compression_power",
                        "type": {float,},
                        "dimension": "power",
                    },
                    "optional": False,
                    "description": "Power associated to the compression."
                },         
                "Peak shaft power": {
                    "Value": {
                        "inserted_value": "peak_shaft_power",
                        "type": {float,},
                        "dimension": "power",
                    },
                    "optional": False,
                    "description": "Shaft power required to drive the compressor at the plant design capacity flowrate."
                },   
                "Hourly energy requirement": {
                    "Value": {
                        "inserted_value": "hourly_shaft_energy",
                        "type": {dict,},
                        "dimension": "energy",
                    },
                    "optional": False,
                    "description": "Dictionary of years containing arrays of hourly energy needed at the shaft to drive the compressor."
                },                 
                "Yearly energy requirement": {
                    "Value": {
                        "inserted_value": "yearly_shaft_energy",
                        "type": {np.ndarray,},
                        "dimension": "energy",
                    },
                    "optional": False,
                    "description": "Energy needed at the shaft to drive the compressor (accounting for Operating capacity factor)."
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
            },
        }


    def _run(self, dcf):    

        self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, 'Compressor_2_Plugin')

        (self.outlet_temperature,
         self.outlet_pressure,
         self.outlet_enthalpy, 
         self.peak_compression_power, 
         self.peak_shaft_power, 
         self.hourly_shaft_energy,         
         self.yearly_shaft_energy
         ) = calculate_compression(self.input_dict_resolved, compressor_name = 'Compressor 2')

        output_inserter_function(self.output_dict, self, dcf, 'Compressor_2_Plugin') 

        print('compressor 2 peak_shaft_power ', self.peak_shaft_power)
        print('compressor 2 yearly_shaft_energy ', self.yearly_shaft_energy.unit['MWh'])    