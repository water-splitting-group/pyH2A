from pyH2A.Utilities.input_modification import daily_to_yearly_power
from pyH2A.Plugins.Electrolyzer_Plugin import calculate_electrolyzer_power_demand, calculate_hydrogen_production, calculate_stack_replacement
from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
import numpy as np
from pyH2A.Utilities.docstring_generation import generate_docstring

class Stored_Power_Electrolysis_Plugin:

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
            "Electrolysis Using Stored Power": {
                "Fraction of stored power used for electrolysis": {
                    "Value": {
                        "type": {float},
                        "bounds": (0, 1) 
                    },
                    "Unit": {
                        "dimension": "dimensionless"
                    },
                    "optional": False,
                    "description": "Fraction of stored power used for electrolysis."
                }
            },
            "Electrolyzer": {
                "Nominal power": {
                    "Value": {
                        "type": {float},
                        "bounds": (0, None)
                    },
                    "Unit": {
                        "dimension": "power"
                    },
                    "optional": False,
                    "description": "Nominal power of electrolyzer."
                },
                "Power requirement increase per year": {
                    "Value": {
                        "type": {float},
                        "bounds": (0, None)
                    },
                    "Unit": {
                        "dimension": "dimensionless"
                    },
                    "optional": False,
                    "description": "Electrolyzer power requirement increase per year due to stack degradation. Percentage or value > 0. Increase calculated as: (1 + increase per year) ^ year."
                },
                "Minimum capacity": {
                    "Value": {
                        "type": {float},
                        "bounds": (0, 1)
                    },
                    "Unit": {
                        "dimension": "dimensionless"
                    },
                    "optional": False,
                    "description": "Minimum capacity required for electrolyzer operation. Percentage or value between 0 and 1."
                },
                "Hydrogen yield per unit energy": {
                    "Value": {
                        "type": {float},
                        "bounds": (0, None)
                    },
                    "Unit": {
                        "dimension": "mass / energy"
                    },
                    "optional": False,
                    "description": "Electrical conversion efficiency of electrolyzer in mass(H2)/energy(electrical)."
                },
                "Replacement time": {
                    "Value": {
                        "type": {float},
                        "bounds": (0, None)
                    },
                    "Unit": {
                        "dimension": "time"
                    },
                    "optional": False,
                    "description": "Operating time before stack replacement of electrolyzer is required."
                },
                "Yearly operation data": {
                    "Year_Value": {
                        "type": {np.ndarray},
                        "bounds": (0, None)
                    },
                    "Year_Unit": {
                        "dimension": "dimensionless"
                    },
                    "Production_Value": {
                        "type": {np.ndarray},
                        "bounds": (0, None)
                    },
                    "Production_Unit": {
                        "dimension": "mass"
                    },   
                    "Duration_Value": {
                        "type": {np.ndarray},
                        "bounds": (0, None)
                    },
                    "Duration_Unit": {
                        "dimension": "time"
                    },                     
                    "optional": False,
                    "description": "Yearly operation data of electrolyzer: year, H2 produced and duration of operation"
                },          
                "H2 production (yearly)": {
                    "Value": {
                        "type": {np.ndarray},
                        "bounds": (0, None)
                    },
                    "Unit": {
                        "dimension": "mass"
                    },
                    "optional": False,
                    "description": "Yearly hydrogen production."
                },
            },
            "Power Generation": {
                "Stored energy (daily)": {
                    "Value": {
                        "type": {dict,},
                        "bounds": (0, None)
                    },
                    "Unit": {
                        "dimension": "energy"
                    },
                    "optional": False,
                    "description": "Energy stored in battery daily (dictionary of years)."
                }
            },
        }

        self.output_dict = {
            "Electrolyzer": {
                "Actual stack replacement time": {
                    "Value": {
                        "inserted_value": "replacement_frequency",
                        "type": {float,int},
                        "dimension": "time",
                    },
                    "description": "Actual stack replacement time, \
                            calculated from replacement time and operation data."
                },
                "H2 production (yearly)": {
                    "Value": {
                        "inserted_value": "new_h2_production",
                        "type": {np.ndarray, },
                        "dimension": "mass",
                    },
                    "optional": False,
                    "description": "Yearly hydrogen production, updated with additional hydrogen production from stored power."
                },

            },
            "Power Consumption": {
                "Stored energy electrolysis (yearly)": {
                    "Value": {
                        "inserted_value": "energy_consumption",
                        "type": {np.ndarray,},
                        "dimension": "energy",
                    },
                    "Type": {
                        "inserted_value": "on_demand",
                        "type": {str,},
                    },
                    "optional": False,
                    "description": "Electricity demand of electrolysis using stored energy per year. Type of power consumer is 'on_demand' (only uses stored power)."
                },
            },
        }
        
        summary = "Simulation of hydrogen production using electrolysis."
        
        self.__class__.__doc__ = generate_docstring(
            summary,
            self.input_dict,
            self.output_dict
        )

    def _run(self, dcf):
        self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, 'Stored_Power_Electrolysis_Plugin')

        self.calculate_H2_production()
        self.on_demand = "on_demand"

        self.replacement_frequency = calculate_stack_replacement(self.operation_hours, # operation hours being for each year, the result is in years between replacement
                                                                 self.input_dict_resolved['Electrolyzer']['Replacement time']['Value'].unit['h']) 
                                                                
        output_inserter_function(self.output_dict, self, dcf, 'Stored_Power_Electrolysis_Plugin') 

    def calculate_H2_production(self):
        '''
        '''

        SECONDS_IN_A_YEAR = 8760*3600

        remaining_run_time_per_year_in_seconds = SECONDS_IN_A_YEAR - self.input_dict_resolved['Electrolyzer']['Yearly operation data']['Duration_Value'].unit['s']
        
        (electrolyzer_power_demand, 
               power_increase_ratio) = calculate_electrolyzer_power_demand(
                                                self.input_dict_resolved['Electrolyzer']['Power requirement increase per year']['Value'].unit['-'],
                                                self.input_dict_resolved['Electrolyzer']['Nominal power']['Value'].unit['W'],
                                                self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-'])

        maximum_consumable_energy = remaining_run_time_per_year_in_seconds * electrolyzer_power_demand # result in Joules

        # Converting quantity of stored energy from daily to yearly
        stored_energy = {}
        for year in self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-']:
            stored_energy[year] = self.input_dict_resolved['Power Generation']['Stored energy (daily)']['Value'][year].unit['J']
            
        stored_energy_yearly = daily_to_yearly_power(stored_energy)

        stored_energy_yearly_available_for_use = (stored_energy_yearly 
                                            * self.input_dict_resolved['Electrolysis Using Stored Power']['Fraction of stored power used for electrolysis']['Value'].unit['-'])

        self.energy_consumption = Quantity(np.minimum(maximum_consumable_energy, 
                                                      stored_energy_yearly_available_for_use), 
                                           'J')

        # Updating H2 production
        additional_h2_production = calculate_hydrogen_production(
                                                   self.energy_consumption.unit['J'], 
                                                   self.input_dict_resolved['Electrolyzer']['Hydrogen yield per unit energy']['Value'].unit['kg/J'],
                                                   power_increase_ratio)
        
        old_h2_production = self.input_dict_resolved['Electrolyzer']['H2 production (yearly)']['Value'].unit['kg']

        self.new_h2_production = old_h2_production.copy()
        self.new_h2_production[-len(additional_h2_production):] += additional_h2_production
        self.new_h2_production = Quantity(self.new_h2_production, 'kg')
        
        # Updating operation hours
        additional_operation_hours = self.energy_consumption.unit['Wh'] / electrolyzer_power_demand
        self.operation_hours = Quantity(additional_operation_hours 
                                        + self.input_dict_resolved['Electrolyzer']['Yearly operation data']['Duration_Value'].unit['h'], 
                                  'h') # calculate_stack_replacement expects a Quantity as an input
