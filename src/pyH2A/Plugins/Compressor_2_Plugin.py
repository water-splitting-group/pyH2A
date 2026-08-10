from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.Physical_Properties.Physical_properties import Physical_properties as PP
from pyH2A.Utilities.Physical_Properties.data import Constants as constant
import numpy as np

input_dict = {
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

output_dict = {
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
        "Average shaft power": {
            "Value": {
                "inserted_value": "average_shaft_power",
                "type": {float,},
                "dimension": "power",
            },
            "optional": False,
            "description": "Shaft power required to drive the compressor, averaged (accounting for Operating capacity factor)."
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

class Compressor_2_Plugin:
    '''Simulation of gas mixture adiabatic compression.
    If the polytropic coefficient corresponds to the ideal case (heat capacity ratio), then the efficiency must account for both the non-ideality of the compression and the mechanical losses.
    If the non-ideality of the compression is taken into account via the polytropic coefficient (from constructor data), then the efficiency must include mechanical losses only. 
    The total mass flowrate and composition stay constant during the compression. The other properties of the Main Stream are updated.

    Parameters
    ----------
    Compressor > Compression ratio > Value : float
        Outlet pressure divided by the inlet pressure
    Compressor > Polytropic coefficient > Value : float
        Polytropic coefficient of the compression. Defaults to the heat capacity ratio if diatomic ideal gas (1.4)
    Compressor > Efficiency > Value : float
        Compression work per shaft work provided to the compressor        
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
    Compressor > Compression power > Value : float
        Power associated to the compression.
    Compressor > Shaft power > Value : float
        Shaft power to provide to run the compressor.
	Main Stream > Temperature > Value : float
		Temperature of the gas mixture at compressor outlet
	Main Stream > Pressure > Value : float
		Pressure of the gas mixture at compressor outlet	
	Main Stream > Specific enthalpy > Value : float
		Mass-specific enthalpy of the gas mixture at compressor outlet        

    '''

    def __init__(self, dcf, print_info):

        self.input_dict_resolved = input_resolver_function(input_dict, dcf, 'Compressor_2_Plugin')

        self.calculate_compression()

        output_inserter_function(output_dict, self, dcf, 'Compressor_2_Plugin') 


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

        self.average_shaft_power = Quantity(
            self.design_shaft_power.unit['W']
            *
            self.input_dict_resolved['Technical Operating Parameters and Specifications']['Operating capacity factor']['Value'].unit['-'],
                                    'W')


