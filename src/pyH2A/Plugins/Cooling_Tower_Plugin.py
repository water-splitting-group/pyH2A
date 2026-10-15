from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
import numpy as np

class Cooling_Tower_Plugin:
    '''Simulation of cooling tower.
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
            "Cooling Tower": {
                "<...>": {
                    "Yearly_heat_duty_Value": {
                        "type": {np.ndarray},
                        "bounds": (0, None),
                    },
                    "Yearly_heat_duty_Unit": {
                        "dimension": "energy",
                    },
                    "Heat_duty_sizing_Value": {
                        "type": {int, float},
                        "bounds": (0, None),
                    },
                    "Heat_duty_sizing_Unit": {
                        "dimension": "power",
                    },
                    "Flowrate_sizing_Value": {
                        "type": {int, float},
                        "bounds": (0, None),
                    },
                    "Flowrate_sizing_Unit": {
                        "dimension": "mass/time",
                    },                    
                    "optional": False,
                    "description": "Heat duty and water flowrate to handle."
                },        
            },
            "Cooling Tower Unit": {                
                "Maximum heat duty per unit": {
                    "Value": {
                        "type": {int, float},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "power",
                    },
                    "optional": False,
                    "description": "Maximum thermal power of each cooling tower unit. Used for sizing."
                },        
                "Maximum water flowrate per unit": {
                    "Value": {
                        "type": {int, float},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "mass/time",
                    },
                    "optional": False,
                    "description": "Maximum water flowrate of each cooling tower unit. Used for sizing."
                },   
                "Ventilation power per unit": {
                    "Value": {
                        "type": {int, float},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "power",
                    },
                    "optional": False,
                    "description": "Power of the fan."
                },                                   
                "Steel mass per unit": {
                    "Value": {
                        "type": {int, float},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "mass",
                    },
                    "optional": False,
                    "description": "Mass of steel constituting a cooling tower unit."
                },                        
                "Polymer mass per unit": {
                    "Value": {
                        "type": {int, float},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "mass",
                    },
                    "optional": False,
                    "description": "Mass of PVC constituting a cooling tower unit."
                },                                        
            },     
        }

        self.output_dict = {
            "Cooling Tower": {
                "Number of units": {
                    "Value": {
                        "inserted_value": "number_units",
                        "type": {int,float}, 
                        "dimension": "dimensionless",
                    },
                    "description": "Number of required cooling towers.",
                    "optional": False,
                },
                "Hourly electricity consumption": {
                    "Value": {
                        "inserted_value": "hourly_electricity_consumption",
                        "type": {np.ndarray}, 
                        "dimension": "energy",
                    },
                    "description": "Hourly energy consuption to supply the fans. Constant, but takes the form of an array for compatibility with other plugins.",
                    "optional": False,
                }, 
                "Total electricity consumption": {
                    "Value": {
                        "inserted_value": "total_electricity_consumption",
                        "type": {int, float}, 
                        "dimension": "energy",
                    },
                    "description": "Total energy consuption to supply the fans over plant lifetime.",
                    "optional": False,
                },                 
                "Yearly water makeup": {
                    "Value": {
                        "inserted_value": "yearly_water_makeup",
                        "type": {np.ndarray}, 
                        "dimension": "mass",
                    },
                    "description": "Water makeup needed to compensate evaporation, yearly array.",
                    "optional": False,
                },                                                
                "Total water makeup": {
                    "Value": {
                        "inserted_value": "total_water_makeup",
                        "type": {int, float}, 
                        "dimension": "mass",
                    },
                    "description": "Total water makeup needed to compensate evaporation during plant lifetime.",
                    "optional": False,
                },  
                "Total steel mass": {
                    "Value": {
                        "inserted_value": "total_steel",
                        "type": {int, float}, 
                        "dimension": "mass",
                    },
                    "description": "Total mass of steel of the cooling towers.",
                    "optional": False,
                },                                                   
                "Total polymer mass": {
                    "Value": {
                        "inserted_value": "total_polymer",
                        "type": {int, float}, 
                        "dimension": "mass",
                    },
                    "description": "Total mass of polymer of the cooling towers.",
                    "optional": False,
                },                                                                                                
            },
        }

    def _run(self, dcf):
        self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, 'Cooling_Tower_Plugin')

        self.calculate_cooling_tower()

        output_inserter_function(self.output_dict, self, dcf, 'Cooling_Tower_Plugin') 
                
    def calculate_cooling_tower(self):
        '''Calculation of the number of towers needed to meet the peak cooling demand, 
            and subsequent consumptions of electricity and fresh water.
        '''

        Total_peak_heat_duty_W = 0
        Total_peak_water_flowrate_kg_s = 0
        Total_yearly_heat_duty_kJ = np.zeros_like(self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-'])

        for cooling_demand in self.input_dict_resolved['Cooling Tower'].keys():
            Total_peak_heat_duty_W += self.input_dict_resolved['Cooling Tower'][cooling_demand]['Heat_duty_sizing_Value'].unit['W']
            Total_peak_water_flowrate_kg_s += self.input_dict_resolved['Cooling Tower'][cooling_demand]['Flowrate_sizing_Value'].unit['kg/s']
            Total_yearly_heat_duty_kJ += self.input_dict_resolved['Cooling Tower'][cooling_demand]['Yearly_heat_duty_Value'].unit['kJ']



        number_of_devices_heat_duty = np.ceil(Total_peak_heat_duty_W
                                            /
                                            self.input_dict_resolved['Cooling Tower Unit']['Maximum heat duty per unit']['Value'].unit['W']
                                            ).astype(int)

        number_of_devices_water_flowrate = np.ceil(Total_peak_water_flowrate_kg_s
                                            /
                                            self.input_dict_resolved['Cooling Tower Unit']['Maximum water flowrate per unit']['Value'].unit['kg/s']
                                            ).astype(int)    

        self.number_units = Quantity(max(number_of_devices_heat_duty, number_of_devices_water_flowrate), '-')    

        # Hardcoding the reference heat of vaporization because we don't need high accuracy.
        Water_vaporization_enthalpy_kJ_kg = 2257 # value at 100°C to be conservative in terms of water requirements

        self.yearly_water_makeup = Quantity(Total_yearly_heat_duty_kJ / Water_vaporization_enthalpy_kJ_kg, 'kg')
        self.total_water_makeup = Quantity(np.sum(self.yearly_water_makeup.unit['kg']), 'kg')
        self.hourly_electricity_consumption = Quantity(self.input_dict_resolved['Cooling Tower Unit']['Ventilation power per unit']['Value'].unit['W']
                                                        *
                                                        self.number_units.unit['-']
                                                        *
                                                        self.input_dict_resolved['Time']['Years']['Value']['Operation years ones'].unit['-'], 
                                                       'Wh')
        self.total_electricity_consumption = Quantity(self.input_dict_resolved['Cooling Tower Unit']['Ventilation power per unit']['Value'].unit['W']
                                                        *
                                                        self.number_units.unit['-']
                                                        *
                                                        8760 # hours per year
                                                        *
                                                        np.sum(self.input_dict_resolved['Time']['Years']['Value']['Operation years ones'].unit['-']), 
                                                      'Wh')
        
        self.total_steel = Quantity(self.input_dict_resolved['Cooling Tower Unit']['Steel mass per unit']['Value'].unit['kg']
                                    *
                                    self.number_units.unit['-'], 
                                    'kg')
        
        self.total_polymer = Quantity(self.input_dict_resolved['Cooling Tower Unit']['Polymer mass per unit']['Value'].unit['kg']
                                    *
                                    self.number_units.unit['-'], 
                                    'kg')    
