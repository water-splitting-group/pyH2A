from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.Physical_Properties.Physical_properties import Physical_properties as PP
from pyH2A.Utilities.Physical_Properties.data import Constants as constant
import numpy as np

class Compressor_Plugin:
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

        self.input_dict = {
            "Compressor": {
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
                "Mass flowrate": {
                    "Value": {
                        "type": {int, float,},
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
            "Compressor": {
                "Compression power": {
                    "Value": {
                        "inserted_value": "compression_power",
                        "type": {float,},
                        "dimension": "power",
                    },
                    "optional": False,
                    "description": "Power associated to the compression."
                },         
                "Design shaft power": {
                    "Value": {
                        "inserted_value": "design_shaft_power",
                        "type": {float,},
                        "dimension": "power",
                    },
                    "optional": False,
                    "description": "Shaft power required to drive the compressor at the plant design capacity flowrate."
                },   
                "Yearly power requirement": {
                    "Value": {
                        "inserted_value": "yearly_shaft_power",
                        "type": {float,},
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

        self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, 'Compressor_Plugin')

        self.calculate_compression()

        output_inserter_function(self.output_dict, self, dcf, 'Compressor_Plugin') 


    def calculate_compression(self):
        '''Using inlet stream and compressor characteristics, shaft work and outlet stream properties are calculated.
        '''
        if 'Polytropic coefficient' in self.input_dict_resolved['Compressor']:
            k = self.input_dict_resolved['Compressor']['Polytropic coefficient']['Value'].unit['-']
        else:
            k = constant.IDEAL_GAS_DIATOMIC_HEAT_CAPACITY_RATIO.unit['-']

        self.outlet_temperature = Quantity(
                                        self.input_dict_resolved['Main Stream']['Temperature']['Value'].unit['K']
                                        * self.input_dict_resolved['Compressor']['Compression ratio']['Value'].unit['-']**((k-1)/k), 
                                        'K')

        self.outlet_pressure = Quantity(
                                        self.input_dict_resolved['Main Stream']['Pressure']['Value'].unit['Pa']
                                        * self.input_dict_resolved['Compressor']['Compression ratio']['Value'].unit['-'], 
                                        'Pa')

        h = PP.Enthalpy(T = self.outlet_temperature,
                        P = self.outlet_pressure, 
                        amount = self.input_dict_resolved['Main Stream']['Mass fraction']['Value'], 
                        phase = 'V', 
                        composition_basis = 'mass'
                        )
        
        self.outlet_enthalpy = Quantity(h.unit['J'], 'J/kg')

        self.compression_power = Quantity(
                                            self.input_dict_resolved['Main Stream']['Mass flowrate']['Value'].unit['kg/s']
                                            *
                                            (self.outlet_enthalpy.unit['J/kg']-self.input_dict_resolved['Main Stream']['Specific enthalpy']['Value'].unit['J/kg']), 
                                            'W'
                                        )

        self.design_shaft_power = Quantity(
                                    self.compression_power.unit['W']
                                    /
                                    (self.input_dict_resolved['Compressor']['Efficiency']['Value'].unit['-']), 
                                    'W')

        self.yearly_shaft_power = Quantity(
            self.design_shaft_power.unit['Wh_per_year']
            *
            self.input_dict_resolved['Technical Operating Parameters and Specifications']['Operating capacity factor']['Value'].unit['-'],
                                    'Wh')

        print('design_shaft_power ', self.design_shaft_power)
        print('yearly_shaft_power ', self.yearly_shaft_power)

