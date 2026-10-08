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
            "Compressor@": {
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
                        "type": {dict,},
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
                        "type": {float,},
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
            },
        }

        self.output_dict = {
            "Compressor@": {      
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
                "Total energy requirement": {
                    "Value": {
                        "inserted_value": "total_shaft_energy",
                        "type": {float, int,},
                        "dimension": "energy",
                    },
                    "optional": False,
                    "description": "Total energy needed at the shaft to drive the compressor."
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
                        "type": {dict,},
                        "dimension": "energy/mass",
                    },
                    "optional": False,
                    "description": "Mixture outlet specific enthalpy."
                },                  
            },
        }


    def _run(self, dcf):    

        plugin_name = 'Compressor_Plugin'
        self.compressor_name = 'Compressor'
        if self.instance_suffix is not None:
            plugin_name = f'{plugin_name} @{self.instance_suffix}'
            self.compressor_name = f'{self.compressor_name} {self.instance_suffix}'        

        self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, plugin_name)

        self.calculate_compression()

        output_inserter_function(self.output_dict, self, dcf, plugin_name) 

        #print(self.compressor_name, ' peak_shaft_power ', self.peak_shaft_power)
        #print(self.compressor_name, ' yearly_shaft_energy ', self.yearly_shaft_energy.unit['MWh'])        


    def calculate_compression(self):
        '''Using inlet stream and compressor characteristics, shaft work and outlet stream properties are calculated.
        '''
        if 'Polytropic coefficient' in self.input_dict_resolved[self.compressor_name]:
            k = self.input_dict_resolved[self.compressor_name]['Polytropic coefficient']['Value'].unit['-']
        else:
            k = constant.IDEAL_GAS_DIATOMIC_HEAT_CAPACITY_RATIO.unit['-']

        self.outlet_pressure = Quantity(
                                        self.input_dict_resolved['Main Stream']['Pressure']['Value'].unit['Pa']
                                        * self.input_dict_resolved[self.compressor_name]['Compression ratio']['Value'].unit['-'], 
                                        'Pa')
        self.outlet_temperature = {}
        self.outlet_enthalpy = {}
        self.hourly_shaft_energy = {}
        self.yearly_shaft_energy = np.zeros_like(self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-'])
        self.peak_shaft_power = 0
        for year in self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-']:
            year = round(year)
            self.outlet_temperature[year] = Quantity(
                                            self.input_dict_resolved['Main Stream']['Temperature']['Value'][year].unit['K']
                                            * self.input_dict_resolved[self.compressor_name]['Compression ratio']['Value'].unit['-']**((k-1)/k), 
                                            'K')


            h = PP.Enthalpy(T = self.outlet_temperature[year],
                            P = self.outlet_pressure, 
                            amount = self.input_dict_resolved['Main Stream']['Mass fraction']['Value'][year], 
                            phase = 'V', 
                            composition_basis = 'mass'
                            )
            
            self.outlet_enthalpy[year] = Quantity(h.unit['J'], 'J/kg')

            hourly_compression_energy_J = (self.input_dict_resolved['Main Stream']['Mass flow (hourly)']['Value'][year].unit['kg']
                                            *
                                            (self.outlet_enthalpy[year].unit['J/kg']-self.input_dict_resolved['Main Stream']['Specific enthalpy']['Value'][year].unit['J/kg'])
                                        )

            self.hourly_shaft_energy[year] = Quantity(hourly_compression_energy_J
                                                      /
                                                      self.input_dict_resolved[self.compressor_name]['Efficiency']['Value'].unit['-'], 
                                                      'J')

            self.yearly_shaft_energy[year] = (self.input_dict_resolved['Technical Operating Parameters and Specifications']['Operating capacity factor']['Value'].unit['-']
                                                *
                                                np.sum(self.hourly_shaft_energy[year].unit['J']))

            self.peak_shaft_power = max(self.peak_shaft_power, np.max(self.hourly_shaft_energy[year].unit['Wh']))

        self.yearly_shaft_energy = Quantity(self.yearly_shaft_energy, 'J')
        self.peak_shaft_power = Quantity(self.peak_shaft_power, 'W')
        self.total_shaft_energy = Quantity(np.sum(self.yearly_shaft_energy.unit['J']), 'J')

