from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.saturated_cumsum import saturated_cumsum_cycle_loss
import numpy as np
#import matplotlib.pyplot as plt


class Battery_Calculation_Plugin:
    '''Simulation of electricity storage using a battery.
    The battery charges when there is some extra available energy (production > consumer demand), the power is within the allowed range and the state of charge is below a thershold.
    The battery discharges when there is some unsatisfied demand (production < consumer demand). 
    The amounts that are not stored and that are missing to supply the customer are also calculated.      
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
            "Power Demand": {
                "Main consumer hourly unsatisfied demand": {
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
                    "optional": True,
                    "description": "Loss of capacity per year. Defaults to 0."
                },
                "Capacity loss per full charge": {
                    "Value": {
                        "type": {int, float,},
                        "bounds": (0, 1),
                    },
                    "Unit": {
                        "dimension": "dimensionless",
                    },                    
                    "optional": True,
                    "description": "Loss of capacity per equivalent full charge. Defaults to 0"
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

        self.output_dict = {
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
            "Power Demand":{
                "Main consumer hourly unsatisfied demand": {
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


    def _run(self, dcf):
        self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, 'Battery_Calculation_Plugin')

        self.calculate_power_curtailment()
        self.calculate_capacity_curtailment()
        if 'Storage capacity per battery module' in self.input_dict_resolved['Battery']:
            self.calculate_sizing()
        
        output_inserter_function(self.output_dict, self, dcf, 'Battery_Calculation_Plugin')            

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
                                                    self.input_dict_resolved['Power Demand']['Main consumer hourly unsatisfied demand']['Value'][year].unit['Wh'] 
                                                    for year in operating_years_relative
                                                ])

        curtailed_discharging_power =  np.minimum(unsatisfied_demand_full_array, self.input_dict_resolved['Battery']['Power']['Value'].unit['W'])
        unsatisfied_demand_due_to_power_curtailment = unsatisfied_demand_full_array - curtailed_discharging_power

        self.curtailed_discharging_power = Quantity(curtailed_discharging_power, 'Wh')
        self.unsatisfied_demand_due_to_power_curtailment = Quantity(unsatisfied_demand_due_to_power_curtailment, 'Wh')

    def calculate_capacity_curtailment(self):

        operating_years_relative = self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-']
        # The battery capacity evolves with years
        if 'Capacity loss per year' in self.input_dict_resolved['Battery']:
            battery_yearly_ageing_factor_calendar = 1-self.input_dict_resolved['Battery']['Capacity loss per year']['Value'].unit['-']
            battery_ageing_factor_calendar = np.repeat(battery_yearly_ageing_factor_calendar ** operating_years_relative, 8760) 
        else:
            battery_ageing_factor_calendar = np.ones_like(lower_bound_SOE_J)

        # The capacity upper and lower bounds are proprtional to the (aged) full capacity
        lower_bound_SOE_J = (battery_ageing_factor_calendar 
                             * 
                             self.input_dict_resolved['Battery']['Design capacity']['Value'].unit['J'] 
                             * 
                             self.input_dict_resolved['Battery']['Lowest discharge level']['Value'].unit['-'])


        upper_bound_SOE_J = (battery_ageing_factor_calendar 
                             * 
                             self.input_dict_resolved['Battery']['Design capacity']['Value'].unit['J'] 
                             * 
                             self.input_dict_resolved['Battery']['Highest charge level']['Value'].unit['-'])

        if 'Capacity loss per full charge' in self.input_dict_resolved['Battery']:
            # The capacity loss per full charge refers to the total capacity ; only a fraction of which is effectively usable anyway, 
            # therefore the loss of usable capacity is only a fraction 'Highest charge level' of the nominal 'Design capacity'
            ageing_per_cycle = self.input_dict_resolved['Battery']['Capacity loss per full charge']['Value'].unit['-'] * self.input_dict_resolved['Battery']['Highest charge level']['Value'].unit['-'] 
        else: 
            ageing_per_cycle = 0

        # The power that is a-priori available for charging is subject to curtailment due to the battery capacity
        # moreover, considering that the state of energy (SOE) corresponds to the part of the chargin energy that will effectively be restituted later by the battery, the power transmitted during charging is subject to the RTE
        # Concerning the discharge, the hourly unsatisfied demand of the consumer must be satisfied by the battery, which comes as a negative contribution to the requested variation
        # note that the requested_variation array is therefore either positive (there is production excess, and we're above the charging threshold), negative (there is unsatisfied demand), or null (there is overproduction, but below the threshold)

        (
        state_of_energy_J_full_array,
        hourly_energy_deficit_J_full_array,
        hourly_energy_excess_J_full_array,
        cumulated_energy_deficit_J,
        cumulated_energy_excess_J, 
        cumulated_charge_J_full_array,
        cumulated_discharge_J_full_array
        ) = saturated_cumsum_cycle_loss(
            requested_variation = self.curtailed_charging_power.unit['J'] - self.curtailed_discharging_power.unit['J'],                          
            nominal_lower_bound = lower_bound_SOE_J,                     
            nominal_upper_bound = upper_bound_SOE_J, # The upper bound varies with calendar year
            loss_per_cycle = ageing_per_cycle, # complementary ageing due to number of charges-discharges
            initial_state = upper_bound_SOE_J[0], # assuming the battery is initially fully charged
            positive_variation_yield = self.input_dict_resolved['Battery']['Round trip efficiency']['Value'].unit['-'],
            negative_variation_yield = 1.
            )

        #plt.plot(state_of_energy_J_full_array)
        #plt.show()

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
                                            cumulated_energy_excess_J
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
        
        self.total_unsatisfied_demand = Quantity(cumulated_energy_deficit_J
                                                 +
                                                 np.sum(self.unsatisfied_demand_due_to_power_curtailment.unit['J']),
                                                 'J'
                                                 )

        # The throughput is a cumulated sum of the absolute value of the state of energy variation: cumulated_charge_J_full_array + cumulated_discharge_J_full_array
        # We need to take the last value to have the total over the lifetime, and divide it by 2 to get an "equivalent charge"
        # The throughput is defined as an array rather than simply the total sum in the first place in case we would like to refine ageing models in the future, with yearly number of cycles
        self.number_charge_cycles = Quantity(
                                            (cumulated_charge_J_full_array[-1]+cumulated_discharge_J_full_array[-1])
                                            /
                                            (2*self.input_dict_resolved['Battery']['Design capacity']['Value'].unit['J']), 
                                            '-')        

        #print('number_charge_cycles ', self.number_charge_cycles.unit['-'])

    def calculate_sizing(self):
        self.number_modules = Quantity(
            self.input_dict_resolved['Battery']['Design capacity']['Value'].unit['J']
            /
            self.input_dict_resolved['Battery']['Storage capacity per battery module']['Value'].unit['J'] , 
            '-'
        )