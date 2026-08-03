from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.saturated_cumsum import saturated_cumsum_with_yield
import numpy as np

input_dict = {    
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
    "Power Generation": {
        "Available energy (hourly)": {
            "Value": {
                "type": {dict,},
                "bounds": (0, None),
            },
            "Unit": {
                "dimension": "energy",
            },                    
            "optional": False,
            "description": " Available energy, hourly basis, dictionary of years."
        },                      
    },
    "Hourly Consumer Profile": {
        "Unsatisfied demand": {
            "Value": {
                "type": {dict,},
                "bounds": (0, None),
            },
            "Unit": {
                "dimension": "energy",
            },                    
            "optional": False,
            "description": "Energy demand that is not met by the direct supply, dictionary of years."
        },                      
    },    
    "Battery": {
        "Design capacity": { 
            "Value": {
                "type": {int, float,},
                "bounds": (0, None),
            },
            "Unit": {
                "dimension": "energy",
            },                    
            "optional": False,
            "description": "Full design capacity of battery."
        },
        "Lowest discharge level": {
            "Value": {
                "type": {int, float,},
                "bounds": (0, 1),
            },
            "Unit": {
                "dimension": "dimensionless",
            },                    
            "optional": False,
            "description": "Lowest level to which battery can be discharged."
        },
        "Capacity loss per year": {
            "Value": {
                "type": {int, float,},
                "bounds": (0, 1),
            },
            "Unit": {
                "dimension": "dimensionless",
            },                    
            "optional": False,
            "description": "Loss of capacity per year."
        },
        "Highest charge level": {
            "Value": {
                "type": {int, float,},
                "bounds": (0, 1),
            },
            "Unit": {
                "dimension": "dimensionless",
            },                    
            "optional": False,
            "description": "Highest level to which battery can be charged, relative to battery capacity."
        },         
        "Round trip efficiency": {
            "Value": {
                "type": {int, float,},
                "bounds": (0, 1),
            },
            "Unit": {
                "dimension": "dimensionless",
            },                    
            "optional": False,
            "description": "Round trip efficiency of battery."
        },  
        "Power": {
            "Value": {
                "type": {int, float,},
                "bounds": (0, None),
            },
            "Unit": {
                "dimension": "power",
            },                    
            "optional": False,
            "description": "Maximum power that can be charged or discharged at a given moment."
        },   
        "Charging threshold": {
            "Value": {
                "type": {int, float,},
                "bounds": (0, None),
            },
            "Unit": {
                "dimension": "dimensionless",
            },                    
            "optional": False,
            "description": "Fraction of the maximum power below which charging is shut down."
        },    
        "Storage capacity per battery module": {
            "Value": {
                "type": {int, float,},
                "bounds": (0, None),
            },
            "Unit": {
                "dimension": "energy",
            },                    
            "optional": True,
            "description": "Serves to calculate the number of battery modules."
        },                         
    } 
}

output_dict = {
    "Power Generation": {
        "State of energy (hourly)": {
            "Value": {
                "inserted_value": "houly_state_of_energy",
                "type": {dict,},
                "dimension": "energy",
            },
            "description": "State of energy of the battery, dictionary of years",
            "optional": False,
        },
        "Available energy (hourly)": {
            "Value": {
                "inserted_value": "hourly_unstored_energy",
                 "type": {dict,},
                 "dimension": "energy",
            },
            "description": "Excess energy that was not stored, dictionary of years",
            "optional": False,
        },
        "Total available energy": {
            "Value": {
                "inserted_value": "total_unstored_energy",
                 "type": {float,},
                 "dimension": "energy",
            },
            "description": "Total excess energy that was not stored during the plant operating years",
            "optional": False,
        },            
    },
    "Hourly Consumer Profile":{
        "Unsatisfied demand": {
            "Value": {
                "inserted_value": "hourly_unsatisfied_demand",
                 "type": {dict,},
                 "dimension": "energy",
            },
            "description": "Energy demand that is not met after the battery supply, dictionary of years.",
            "optional": False,
        },
        "Total unsatisfied demand": {
            "Value": {
                "inserted_value": "total_unsatisfied_demand",
                 "type": {float,},
                 "dimension": "energy",
            },
            "description": "Total energy demand that is not met after the battery supply during the plant operating time.",
            "optional": False,
        },        
    },
    "Battery": {  
        "Number of charge cycles": {
            "Value": {
                "inserted_value": "number_charge_cycles",
                 "type": {float,},
                 "dimension": "dimensionless",
            },
            "description": "Total energy throughput relative to the battery design capacity.",
            "optional": False,
        },              
        "Number of needed modules": {
            "Value": {
                "inserted_value": "number_modules",
                 "type": {float,int},
                 "dimension": "dimensionless",
            },
            "description": "Number of modules to provide the requested storage capacity.",
            "optional": True,
        }        
    }
}

class Battery_Calculation_Plugin:
    '''Simulation of electricity storage using a battery.
    The battery charges when there is some extra available energy (production > consumer demand), the power is within the allowed range and the state of charge is below a thershold.
    The battery discharges when there is some unsatisfied demand (production < consumer demand). 
    The amounts that are not stored and that are missing to supply the customer are also calculated.

    Parameters
    ----------
    Time > Years > Value : dict
        Dictionary containing plant life time-related quantities
    Power Generation > Available energy (hourly) > Value : dict
        Available energy, hourly basis, dictionary of years.
    Hourly Consumer Profile > Unsatisfied demand > Value : dict
        Energy demand that is not met by the direct supply, dictionary of years.  
    Battery > Design capacity > Value : float or int
        Full design capacity of battery.
    Battery > Lowest discharge level > Value : float or int
        Lowest level to which battery can be discharged, relative to battery design capacity. Dimensionless value between 0 and 1.
    Battery > Highest charge level > Value : float or int
        Highest level to which battery can be charged, relative to battery capacity. Dimensionless value between 0 and 1.        
    Battery > Capacity loss per year > Value : float or int
        Loss of capacity per year. Dimensionless value > 0.
    Battery > Round trip efficiency > Value : float or int
        Round trip efficiency of battery. Dimensionless value between 0 and 1.
    Battery > Power > Value : float or int
        Maximum power that can be charged or discharged at a given moment.
     Battery > Charging threshold > Value : float or int
        Fraction of the maximum power below which charging is shut down.       
     Battery > Storage capacity per battery module > Value : float or int, optional
        Fraction of the maximum power below which charging is shut down.    
    
    Returns
    -------
    Power Generation > State of energy (hourly) > Value : dict
        State of energy of the battery, dictionary of years.
    Power Generation > Available energy (hourly) > Value : dict
        Excess energy that was not stored, dictionary of years
    Power Generation > Total available energy > Value : float
        Total excess energy that was not stored during the plant operating years.
    Hourly Consumer Profile > Unsatisfied demand > Value : dict
        Energy demand that is not met after the battery supply, dictionary of years.
    Hourly Consumer Profile > Total unsatisfied demand > Value : float
        Total energy demand that is not met after the battery supply during the plant operating time.        
        
    Battery > Number of charge cycle > Value : float
        Total energy throughput relative to the initial design capacity.         
    Battery > Number of needed modules > Value : float or int, optional
        Number of modules to provide the requested storage capacity.         
    '''

    def __init__(self, dcf, print_info):
        self.input_dict_resolved = input_resolver_function(input_dict, dcf, 'Battery_Calculation_Plugin')

        #number_operating_years = len(self.input_dict_resolved['Time']['Years']['Value']['Operation years'].unit['-'])
        self.calculate_power_curtailment()
        self.calculate_capacity_curtailment()
        
        output_inserter_function(output_dict, self, dcf, 'Battery_Calculation_Plugin')            

    def calculate_power_curtailment(self):

        operating_years_relative = self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-']
        # in order to keep the battery state of charge consistent when changing year (in calculate_capacity_curtailment, called later), it is necessary to handle a unique array containing all the operating hours during all the years
        available_energy_Wh_full_array = np.concatenate([
                                                    self.input_dict_resolved['Power Generation']['Available energy (hourly)']['Value'][year].unit['Wh']
                                                    for year in operating_years_relative
                                                ])

        # if the power (in what, i.e. hourly energy in Wh) is below the minimum threshold, we don't charge the battery and the energy remains available
        # if the available power exceeds the power of the battery, the value is saturated, the excess energy remains available
        curtailed_charging_power = np.where(
                                                (available_energy_Wh_full_array
                                                < 
                                                self.input_dict_resolved['Battery']['Power']['Value'].unit['W'] 
                                                * 
                                                self.input_dict_resolved['Battery']['Charging threshold']['Value'].unit['-'])
                                            ,
                                                0
                                            ,
                                                np.minimum(
                                                        available_energy_Wh_full_array
                                                        , 
                                                        self.input_dict_resolved['Battery']['Power']['Value'].unit['W'])
                                            )

        # The energy that falls out of the allowed charging power will constitute a contribution that remains after the battery system
        available_energy_due_to_power_curtailment = available_energy_Wh_full_array - curtailed_charging_power

        self.curtailed_charging_power = Quantity(curtailed_charging_power, 'Wh')
        self.available_energy_due_to_power_curtailment = Quantity(available_energy_due_to_power_curtailment, 'Wh')

        # symetrically, discharge is only available within the limits of the battery power. Ideally we would allow the battery power to be sufficient to provide the entire consumption as a standalone, but in a general case this is not guaranteed
        unsatisfied_demand_full_array = np.concatenate([
                                                    self.input_dict_resolved['Hourly Consumer Profile']['Unsatisfied demand']['Value'][year].unit['Wh'] 
                                                    for year in operating_years_relative
                                                ])

        curtailed_discharging_power =  np.minimum(unsatisfied_demand_full_array, self.input_dict_resolved['Battery']['Power']['Value'].unit['W'])
        unsatisfied_demand_due_to_power_curtailment = unsatisfied_demand_full_array - curtailed_discharging_power

        self.curtailed_discharging_power = Quantity(curtailed_discharging_power, 'Wh')
        self.unsatisfied_demand_due_to_power_curtailment = Quantity(unsatisfied_demand_due_to_power_curtailment, 'Wh')

    def calculate_capacity_curtailment(self):

        operating_years_relative = self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-']
        # The lower bound of the state of energy is assumed to be constant (fraction of the initial capacity), but the curtailing function expects an array
        lower_bound_SOE_J = np.full(self.curtailed_charging_power.unit['J'].shape, 
                                  self.input_dict_resolved['Battery']['Design capacity']['Value'].unit['J'] * self.input_dict_resolved['Battery']['Lowest discharge level']['Value'].unit['-']) 

        # The battery capacity evolves with years
        battery_yearly_ageing_factor_calendar = 1-self.input_dict_resolved['Battery']['Capacity loss per year']['Value'].unit['-']
        battery_ageing_factor_calendar = np.repeat(battery_yearly_ageing_factor_calendar ** operating_years_relative, 8760) 
        upper_bound_SOE_J = (battery_ageing_factor_calendar 
                             * 
                             self.input_dict_resolved['Battery']['Design capacity']['Value'].unit['J'] 
                             * 
                             self.input_dict_resolved['Battery']['Highest charge level']['Value'].unit['-'])

        # The power that is a-priori available for charging is subject to curtailment due to the battery capacity
        # moreover, considering that the state of energy (SOE) corresponds to the part of the chargin energy that will effectively be restituted later by the battery, the power transmitted during charging is subject to the RTE
        # Concerning the discharge, the hourly unsatisfied demand of the consumer must be satisfied by the battery, which comes as a negative contribution to the requested variation
        # note that the requested_variation array is therefore either positive (there is production excess, and we're above the charging threshold), negative (there is unsatisfied demand), or null (there is overproduction, but below the threshold)

        (
        state_of_energy_J_full_array,
        hourly_energy_deficit_J_full_array,
        hourly_energy_excess_J_full_array,
        cumulated_energy_deficit_J_full_array,
        cumulated_energy_excess_J_full_array, 
        throughput_J_full_array
        ) = saturated_cumsum_with_yield(
            requested_variation = self.curtailed_charging_power.unit['J'] - self.curtailed_discharging_power.unit['J'],                          
            lower_bound = lower_bound_SOE_J,                     
            upper_bound = upper_bound_SOE_J,
            initial_state = upper_bound_SOE_J[0], # assuming the battery is initially fully charged
            positive_variation_yield = self.input_dict_resolved['Battery']['Round trip efficiency']['Value'].unit['-'],
            negative_variation_yield = 1.
            )

        self.houly_state_of_energy = {year: Quantity(
                                                    state_of_energy_J_full_array[i*8760:(i+1)*8760],
                                                    'J'
                                                    )
                                            for i, year in enumerate(operating_years_relative)
                                        }
        # The hourly energy that remains available has two origins: the energy that exceeded the power of the stack (over 1 h), and the energy that exceeded the battery capacity
        self.hourly_unstored_energy = {year: Quantity(
                                                    hourly_energy_excess_J_full_array[i*8760:(i+1)*8760] 
                                                    + 
                                                    self.available_energy_due_to_power_curtailment.unit['J'][i*8760:(i+1)*8760],
                                                    'J'
                                                    )
                                            for i, year in enumerate(operating_years_relative)
                                        }
        self.total_unstored_energy = Quantity(
                                            cumulated_energy_excess_J_full_array
                                            +
                                            np.sum(self.available_energy_due_to_power_curtailment.unit['J']),
                                            'J'
                                            )
        
        # similarly, the unsatisfied demand comes either from the fact that the battery power is insufficient to feed the consumer when production is low, and from the fact that the state of charge is insufficient to provide the missing energy
        self.hourly_unsatisfied_demand =  {year: Quantity(
                                                    hourly_energy_deficit_J_full_array[i*8760:(i+1)*8760]
                                                    +
                                                    self.unsatisfied_demand_due_to_power_curtailment.unit['J'][i*8760:(i+1)*8760],
                                                    'J'
                                                    )
                                            for i, year in enumerate(operating_years_relative)
                                        }
        
        self.total_unsatisfied_demand = Quantity(cumulated_energy_deficit_J_full_array
                                                 +
                                                 np.sum(self.unsatisfied_demand_due_to_power_curtailment.unit['J']),
                                                 'J'
                                                 )

        # The throughput is a cumulated sum of the absolute value of the state of energy variation
        # We need to take the last value to have the total over the lifetime, and divide it by 2 to get an "equivalent charge"
        # The throughput is defined as an array rather than simply the totla sum in the forst place in case we would like to refine ageing models in the future, with yearly number of cycles
        self.number_charge_cycles = Quantity(
                                            throughput_J_full_array[-1]/(2*self.input_dict_resolved['Battery']['Design capacity']['Value'].unit['J']), 
                                            '-')        
  