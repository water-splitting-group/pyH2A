from pyH2A.Utilities.input_modification import daily_to_yearly_power
from pyH2A.Plugins.Electrolyzer_Plugin import calculate_electrolyzer_power_demand, calculate_hydrogen_production, calculate_stack_replacement
from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
import numpy as np

input_dict = {
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
                "dimension": "mass / time"
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

output_dict = {
    "Technical Operating Parameters and Specifications": {
        "Plant design capacity": {
            "Value": {
                "inserted_value": "new_h2_production",
                "type": {float,np.ndarray, },
                "dimension": "mass / time",
            }, 
            "optional": False,
            "description": "Plant design capacity in mass flowrate of H2 calculated from installed electrolysis power capacity and hourly power generation data."
        },
    },
    "Planned Replacement": {
        "Electrolyzer stack replacement": {
            "Frequency_Value": {
                "inserted_value": "replacement_frequency",
                "type": {float,},
                "dimension": "time",
            },
            "add_processed": False,
            "insert_path": False,
            "optional": False,
            "description": "Frequency of electrolyzer stack replacements, calculated from replacement time and hourly irradiation data."
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

class Stored_Power_Electrolysis_Plugin:
    '''Simulation of hydrogen production using electrolysis.

    Parameters
    ----------
    Electrolysis Using Stored Power > Fraction of stored power used for electrolysis > Value : float
        Fraction of stored power used for electrolysis.
    Electrolyzer > Nominal power > Value : float
        Nominal power of electrolyzer.
    Electrolyzer > Power requirement increase per year > Value : float
        Electrolyzer power requirement increase per year due to stack degradation. 
        Dimensionless value > 0. Increase calculated as: (1 + increase per year) ^ year.
    Electrolyzer > Minimum capacity > Value : float
        Minimum capacity required for electrolyzer operation. Dimensionless value between 0 and 1.
    Electrolyzer > Hydrogen yield per unit energy > Value : float
        Electrical conversion efficiency of electrolyzer in (mass H2)/energy.
    Electrolyzer > Replacement time > Value : float
        Operating time in hours before stack replacement of electrolyzer is required.
    Electrolyzer > Yearly operation data > Year_Value : nd.array
        Yearly operation data of electrolyzer : year.
    Electrolyzer > Yearly operation data > Production_Value : nd.array
        Yearly operation data of electrolyzer : H2 produced during the year.
    Electrolyzer > Yearly operation data > Duration_Value : nd.array
        Yearly operation data of electrolyzer : duration of operation during the year.                
    Electrolyzer > H2 production (yearly) > Value : nd.array
        Yearly hydrogen production.
    Power Generation > Stored energy (daily) > Value : dict
        Energy stored in battery daily (dictionary of years).

    Returns
    -------
    Technical Operating Parameters and Specifications > Plant design capacity > Value : nd.array
        Plant design capacity in (mass of H2)/time calculated from installed 
        electrolysis power capacity and hourly power generation data.
    Planned Replacement > Electrolyzer stack replacement > Frequency : float
        Frequency of electrolyzer stack replacements in years, calculated from replacement time and hourly
        irradiation data.
    Power Consumption > Stored energy electrolysis (yearly) > Value : nd.array
        Electricity demand of electrolysis using stored energy per year.
    Power Consumption > Stored energy electrolysis (yearly) > Type : str
        Type of power consumer, type is 'on_demand' (only uses stored power).
    '''

    def __init__(self, dcf, print_info):
        self.input_dict_resolved = input_resolver_function(input_dict, dcf, 'Stored_Power_Electrolysis_Plugin')

        self.calculate_H2_production(dcf)
        self.on_demand = "on_demand"

        self.replacement_frequency = calculate_stack_replacement(self.operation_hours, # operation hours being for each year, the result is in years between replacement
                                                                 self.input_dict_resolved['Electrolyzer']['Replacement time']['Value'].unit['h']) 
                                                                
        output_inserter_function(output_dict, self, dcf, 'Stored_Power_Electrolysis_Plugin') 

    def calculate_H2_production(self, dcf):
        '''
        '''

        SECONDS_IN_A_YEAR = 8760*3600

        remaining_run_time_per_year_in_seconds = SECONDS_IN_A_YEAR - self.input_dict_resolved['Electrolyzer']['Yearly operation data']['Duration_Value'].unit['s']
        
        (electrolyzer_power_demand, 
               power_increase_ratio) = calculate_electrolyzer_power_demand(
                                                self.input_dict_resolved['Electrolyzer']['Power requirement increase per year']['Value'].unit['-'],
                                                self.input_dict_resolved['Electrolyzer']['Nominal power']['Value'].unit['W'],
                                                dcf.operation_years)

        maximum_consumable_energy = remaining_run_time_per_year_in_seconds * electrolyzer_power_demand # result in Joules
        
        stored_energy = {}
        for year in dcf.operation_years:
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
        self.new_h2_production = Quantity(self.new_h2_production, 'kg/year')
        
        # Updating operation hours
        additional_operation_hours = self.energy_consumption.unit['Wh'] / electrolyzer_power_demand
        self.operation_hours = Quantity(additional_operation_hours 
                                        + self.input_dict_resolved['Electrolyzer']['Yearly operation data']['Duration_Value'].unit['h'], 
                                  'h') # calculate_stack_replacement expects a Quantity as an input
