from pyH2A.Utilities.input_modification import hourly_to_daily_power, smoothened_production
from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Physical_Properties.Physical_properties import Physical_properties as PP
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
import numpy as np

class Electrolyzer_Hourly_Plugin:
    '''Simulation of hydrogen production using electrolysis.
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
            "Electrolyzer": {
                "Nominal power": {
                    "Value": {
                        "type": {int,float,},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "power",
                    },
                    "optional": False,
                    "description": "Nominal power of electrolyzer."
                },
                "Power requirement increase per year": {
                    "Value": {
                        "type": {int,float,},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "dimensionless",
                    },
                    "optional": False,
                    "description": "Electrolyzer power requirement increase per year due to stack degradation.\
                            Percentage or value > 0. Increase calculated as: (1 + increase per year) ^ year."
                },
                "Minimum capacity": {
                    "Value": {
                        "type": {int,float,},
                        "bounds": (0, 1),
                    },
                    "Unit": {
                        "dimension": "dimensionless",
                    },
                    "optional": False,
                    "description": "Minimum capacity required for electrolyzer operation. Percentage or value between 0 and 1."
                },
                "Hydrogen yield per unit energy": {
                    "Value": {
                        "type": {int,float,},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "mass / energy",
                    },
                    "optional": False,
                    "description": "Electrical conversion efficiency of electrolyzer in mass(H2)/energy(electrical)."
                },
                "Replacement time": {
                    "Value": {
                        "type": {int,float,},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "time",
                    },
                    "optional": False,
                    "description": "Operating time before stack replacement of electrolyzer is required."
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
                    "description": "Available energy, hourly basis, dictionary of years in (energy)."
                },
            },
        }

        self.output_dict = {
            "Electrolyzer": {
                "Yearly operation data": {
                    "Year_Value": {
                        "inserted_value": "yearly_data_year",
                        "type": {np.ndarray,},
                        "dimension": "dimensionless", 
                    },                  
                    "Production_Value": {
                        "inserted_value": "yearly_data_production",
                        "type": {np.ndarray,},
                        "dimension": "mass", 
                    },  
                    "Duration_Value": {
                        "inserted_value": "yearly_data_duration",
                        "type": {np.ndarray,},
                        "dimension": "time", 
                    },                      
                    "optional": False,
                    "description": "Yearly operation data of electrolyzer: year, H2 produced, duration of operation."
                },
                "Missing required energy (hourly)": {
                    "Value": {
                        "inserted_value": "yearly_data_missing_energy",
                        "type": {dict,},
                        "dimension": "energy",
                    },
                    "optional": False,
                    "description": "Required energy (hourly) for the electrolyzer to stay above the minimum power threshold (dictionary of years)."
                },                  
                "H2 production (yearly)": {
                    "Value": {
                        "inserted_value": "h2_production",
                        "type": {np.ndarray,},
                        "dimension": "mass",
                    },
                    "optional": False,
                    "description": "Yearly hydrogen production."
                },
                "Actual stack replacement time": {
                    "Value": {
                        "inserted_value": "replacement_frequency",
                        "type": {float,},
                        "dimension": "time",
                    },
                    "description": "Actual stack replacement time, \
                            calculated from replacement time and operation data."
                },
            },
            "Power Generation": {
                "Available energy (hourly)": {
                    "Value": {
                        "inserted_value": "yearly_data_unused_energy",
                        "type": {dict,},
                        "dimension": "energy",
                    },
                    "optional": False,
                    "description": "Available energy (hourly) after subtracting power consumed by electrolyzer (dictionary of years)."
                },
                "Available energy (daily)": {
                    "Value": {
                        "inserted_value": "yearly_data_unused_energy_daily",
                        "type": {dict,},
                        "dimension": "energy",
                    },
                    "optional": False,
                    "description": "Available energy (daily) after subtracting power consumed by electrolyzer (dictionary of years)."
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
                "Mass fraction": {
                    "Value": {
                        "inserted_value": "outlet_mass_fraction",
                        "type": {dict,},
                        "dimension": "dimensionless",
                    },
                    "optional": False,
                    "description": "Mixture outlet mass fraction."
                },   
                "Mass flow (hourly)": {
                    "Value": {
                        "inserted_value": "hourly_mass_flow",
                        "type": {dict,},
                        "dimension": "mass",
                    },
                    "optional": False,
                    "description": "Mixture outlet mass flow, dictionary of years whose items are hourly arrays."
                },  			
                "Design mass flow by year": {
                    "Value": {
                        "inserted_value": "yearly_mass_flow",
                        "type": {np.ndarray,},
                        "dimension": "mass",
                    },
                    "optional": False,
                    "description": "Mixture outlet mass per year, excluding downtime (array of years)."
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
        self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, 'Electrolyzer_Hourly_Plugin')

        self.calculate_H2_production()
        self.outlet_flow_properties()
        self.replacement_frequency = calculate_stack_replacement(self.yearly_data_duration, 
                                    self.input_dict_resolved['Electrolyzer']['Replacement time']['Value'].unit['h'])

        output_inserter_function(self.output_dict, self, dcf, 'Electrolyzer_Hourly_Plugin') 

    def calculate_H2_production(self):
        '''Using hourly power generation data and electrolyzer parameters,
        H2 production is calculated.
        '''

        energy_generation_yearly_data = self.input_dict_resolved['Power Generation']['Available energy (hourly)']['Value']

        yearly_data_year = []
        yearly_data_production = []
        yearly_data_duration = []
        yearly_data_missing_energy = {}
        yearly_data_unused_energy = {}
        yearly_data_unused_energy_daily = {}
        self.hourly_h2_production = {}

        for year in self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-']:
            year = round(year)
            energy_generation = energy_generation_yearly_data[year].unit['J']

            electrolyzer_power_demand, power_increase_ratio = calculate_electrolyzer_power_demand(
                              self.input_dict_resolved['Electrolyzer']['Power requirement increase per year']['Value'].unit['-'],
                              self.input_dict_resolved['Electrolyzer']['Nominal power']['Value'].unit['W'],
                              year) # returns: power (Watt), dimensionless

            electrolyzer_energy_demand = 3600*electrolyzer_power_demand # integrate the power over 1 hour, since we ultimately think in terms of energy involved in each 1-hour slot
            electrolyzer_energy_demand *= np.ones(len(energy_generation))

            # Energy that exceeds the power demand remains available
            unused_energy = np.zeros_like(energy_generation)
            is_overproducing = energy_generation > electrolyzer_energy_demand
            unused_energy[is_overproducing] = energy_generation[is_overproducing] - electrolyzer_energy_demand[is_overproducing]
            yearly_data_unused_energy[year] = Quantity(unused_energy, 'J')
            yearly_data_unused_energy_daily[year] = Quantity(hourly_to_daily_power(unused_energy), 'J')            

            # Energy that is missing to maintain the electrolyzer above its minimum operating threshold will have to be provided by the battery
            missing_energy = np.zeros_like(energy_generation)
            threshold = self.input_dict_resolved['Electrolyzer']['Minimum capacity']['Value'].unit['-'] * electrolyzer_energy_demand
            is_underproducing = energy_generation < threshold
            missing_energy[is_underproducing] = electrolyzer_energy_demand[is_underproducing] - energy_generation[is_underproducing]
            yearly_data_missing_energy[year] = Quantity(missing_energy, 'J')

            # The energy effectively consumed by the electrolyzer is the generated energy, 
            # saturated on the lower bound by the threshold (the missing energy would come from the battery)
            # and on the upper bound by the electrolyzer demand (the extra energy is available for the rest of the power chain)
            electrolyzer_energy_consumption = np.clip(energy_generation, threshold, electrolyzer_energy_demand)

            h2_produced = calculate_hydrogen_production(
                                electrolyzer_energy_consumption,
                                self.input_dict_resolved['Electrolyzer']['Hydrogen yield per unit energy']['Value'].unit['kg/J'],
                                power_increase_ratio) # returns an array of kg of H2 produced during each hour
            self.hourly_h2_production[year] = Quantity(h2_produced, 'kg')

            yearly_data_year.append(year)
            yearly_data_production.append(np.sum(h2_produced))
            yearly_data_duration.append(8760)


        self.yearly_data_year = Quantity(np.asarray(yearly_data_year), '-')
        self.yearly_data_production = Quantity(np.asarray(yearly_data_production), 'kg')
        self.yearly_data_duration = Quantity(np.asarray(yearly_data_duration), 'h')

        self.h2_production = self.yearly_data_production
        
        self.yearly_data_unused_energy = yearly_data_unused_energy
        self.yearly_data_unused_energy_daily = yearly_data_unused_energy_daily
        self.yearly_data_missing_energy = yearly_data_missing_energy


    def outlet_flow_properties(self):
        '''Establishes the thermophysical characteristics of the fluid leaving the reactor, for downstream process sizing'''

        self.outlet_temperature = Quantity(85., 'degC') # hardcoded for the moment, could become an input later
        self.outlet_pressure = Quantity(20, 'bar') # hardcoded for the moment, could become an input later

        # Assuming water vapour is saturated in the electrolyzer, determination of the water vapour pressure
        psat = PP.Water_saturation_pressure(self.outlet_temperature)

        mol_fraction = {} # molar fraction of the gas mixture, assuming ideal gas, expressed in mol of species for a total amount of 1 mol 
        mol_fraction['H2O'] = Quantity(
                                psat.unit['Pa']/self.outlet_pressure.unit['Pa'], 
                                '-') 
        # The pressure that is not due to water is due to H2
        mol_fraction['H2'] = Quantity(
                                1-mol_fraction['H2O'].unit['-'], 
                                '-')

        _, self.outlet_mass_fraction = PP.Substance_to_mass(mol_fraction)


        smoothening_period = Quantity(1, 'h')
        self.hourly_mass_flow = {}

        for year in self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-']:			
            year = round(year)
            hourly_unsmoothened_output_kg = (self.hourly_h2_production[year].unit['kg']
                                            / 
                                            self.outlet_mass_fraction['H2'].unit['-']
                                            )            
            self.hourly_mass_flow[year] = Quantity(smoothened_production(hourly_unsmoothened_output_kg, round(smoothening_period.unit['h'])), 
                                                        'kg')

        self.yearly_mass_flow = Quantity(self.h2_production.unit['kg']
                                    / 
                                    self.outlet_mass_fraction['H2'].unit['-']
                                    ,
                                    'kg')

        self.peak_mass_flowrate = Quantity(np.max(self.hourly_mass_flow[0].unit['kg']), 'kg/h')

        # specific enthalpy at the outlet of the baggie
        h = PP.Enthalpy(T = self.outlet_temperature,
                        P = self.outlet_pressure, 
                        amount = self.outlet_mass_fraction,
                        phase = 'V', 
                        composition_basis = 'mass'
                        )
        self.outlet_enthalpy = Quantity(h.unit['J'], 'J/kg')

def calculate_electrolyzer_power_demand(power_requirement_increase, nominal_power, year):
    '''Calculation of yearly increase in electrolyzer power demand.
    '''

    increase = (1. + power_requirement_increase) ** year
    demand = increase * nominal_power

    return demand, increase

def calculate_hydrogen_production(energy_consumption, conversion_efficiency, power_increase_ratio):
    '''Calculation of hydrogen production based on power consumption, conversion efficiency 
    and power increase.
    '''

    h2_production = energy_consumption * conversion_efficiency / power_increase_ratio

    return h2_production

def calculate_stack_replacement(operation_hours, replacement_time):
    '''Calculation of stack replacement frequency for electrolyzer.
    '''

    cumulative_running_time = np.cumsum(operation_hours.unit['h']) # operation_hours is a Quantity
    stack_usage = cumulative_running_time / replacement_time

    number_of_replacements = np.floor_divide(stack_usage[-1], 1)
    replacement_frequency = len(stack_usage) / (number_of_replacements + 1.)

    return Quantity(replacement_frequency, 'year') # the inputs being : (hours of operation in the year, hours of operation before replacement), 
                                                   # the result corresponds to the number of years between replacements
