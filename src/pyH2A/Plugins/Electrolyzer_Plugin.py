from pyH2A.Utilities.input_modification import hourly_to_daily_power
from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
import numpy as np

input_dict = {
    "Financial Input Values": {
        "Construction time": {
            "Value": {
                "type": {int,},
                "bounds": (0, 40*365*86400),
            },
            "Unit": {
                "dimension": "time",
            },
            "optional": False,
            "description": "Construction time of hydrogen production plant."
        },
    },
    "CAPEX Multiplier": {
        "Multiplier": {
            "Value": {
                "type": {float,},
                "bounds": (0, None),
            },
            "Unit": {
                "dimension": "dimensionless",
            },
            "optional": False,
            "description": "Multiplier to describe cost reduction of electrolysis CAPEX \
                            for every ten-fold increase of power relative to CAPEX reference power. \
                            Based on the multiplier the CAPEX scaling factor is calculated as: \
                            multiplier ^ (number of ten-fold increases).\
                            A value of 1 leads to no CAPEX reduction, a value < 1 enables cost reduction."
        },
    },
    "Electrolyzer": {
        "Nominal power": {
            "Value": {
                "type": {float,},
                "bounds": (0, None),
            },
            "Unit": {
                "dimension": "power",
            },
            "optional": False,
            "description": "Nominal power of electrolyzer."
        },
        "CAPEX reference power": {
            "Value": {
                "type": {float,},
                "bounds": (0, None),
            },
            "Unit": {
                "dimension": "power",
            },
            "optional": False,
            "description": "Reference power of electrolyzer for cost reduction calculation."
        },
        "Power requirement increase per year": {
            "Value": {
                "type": {float,},
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
                "type": {float,},
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
                "type": {float,},
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
                "type": {float,},
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

output_dict = {
    "Technical Operating Parameters and Specifications": {
        "Design output by year": { 
            "Value": {
                "inserted_value": "h2_production",
                "type": {np.ndarray,}, 
                "dimension": "mass",
            },
            "optional": False,
            "description": "Design output calculated from installed \
                            electrolysis power capacity and hourly power generation data."
        },
        "Operating capacity factor": {
            "Value": {
                "inserted_value": Quantity(1., '-'),
                "type": {float,},
                "dimension": "dimensionless",
            },
            "optional": False,
            "description": "Operating capacity factor is set to 1."
        },
    },
    "Electrolyzer": {
        "Scaling factor": {
            "Value": {
                "inserted_value": "electrolyzer_scaling_factor",
                "type": {float,},
                "dimension": "dimensionless",
            },
            "optional": False,
            "description": "CAPEX scaling factor for electrolyzer calculated based \
                            on CAPEX multiplier, reference and nominal power."
        },
        "Stack lifetime": {
            "Value": {
                "inserted_value": "stack_lifetime",
                "type": {float,},
                "dimension": "time",
            },
            "optional": False,
            "description": "Lifetime of electrolyzer stack replacements in years, calculated from replacement time and hourly irradiation data."
        },                
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
    },
    "Power Generation": {
        "Available energy (hourly)": {
            "Value": {
                "inserted_value": "yearly_data_unused_energy",
                "type": {dict,},
                "dimension": "energy",
            },
            "optional": False,
            "description": "Available energy (hourly) after subtracting power consumed by electrolyzer. (dictionary of years)."
        },
        "Available energy (daily)": {
            "Value": {
                "inserted_value": "yearly_data_unused_energy_daily",
                "type": {dict,},
                "dimension": "energy",
            },
            "optional": False,
            "description": "Available energy (daily) after subtracting power consumed by electrolyzer. (dictionary of years)."
        },
    },
}

class Electrolyzer_Plugin:
    '''Simulation of hydrogen production using electrolysis.

    Parameters
    ----------
    Financial Input Values > Construction time > Value : int
        Construction time of hydrogen production plant in years.
    CAPEX Multiplier > Multiplier > Value : float
        Multiplier to describe cost reduction of electrolysis CAPEX for every ten-fold
        increase of power relative to CAPEX reference power. Based on the multiplier the CAPEX
        scaling factor is calculated as: multiplier ^ (number of ten-fold increases). A value
        of 1 leads to no CAPEX reduction, a value < 1 enables cost reduction.
    Electrolyzer > Nominal power > Value : float
        Nominal power of electrolyzer.
    Electrolyzer > CAPEX reference power > Value : float
        Reference power of electrolyzer for cost reduction calculation.
    Electrolyzer > Power requirement increase per year > Value : float
        Electrolyzer power requirement increase per year due to stack degradation. 
        Dimensioless value > 0. Increase calculated as: (1 + increase per year) ^ year.
    Electrolyzer > Minimum capacity > Value : float
        Minimum capacity required for electrolyzer operation. Dimensionless value between 0 and 1.
    Electrolyzer > Hydrogen yield per unit energy > Value : float
        Electrical conversion efficiency of electrolyzer in (mass H2)/energy.
    Electrolyzer > Replacement time > Value : float
        Operating time before stack replacement of electrolyzer is required.
    Power Generation > Available energy (hourly) > Value : dict
        Available energy, hourly basis, dictionary of years.

    Returns
    -------
    Technical Operating Parameters and Specifications > Plant design capacity > Value : float
        Plant design capacity calculated from installed 
        electrolysis power capacity and hourly power generation data.
    Technical Operating Parameters and Specifications >	Operating capacity factor > Value : float
        Operating capacity factor is set to 1.
    Electrolyzer > Scaling factor > Value : float
        CAPEX scaling factor for electrolyzer calculated based on CAPEX multiplier, 
        reference and nominal power.
    Electrolyzer > Stack lifetime > Value : float
        Frequency of electrolyzer stack replacements, calculated from replacement time and hourly irradiation data.        
    Electrolyzer > Yearly operation data > Year_Value : nd.array
        Yearly operation data of electrolyzer : year.
    Electrolyzer > Yearly operation data > Production_Value : nd.array
        Yearly operation data of electrolyzer : H2 produced during the year.
    Electrolyzer > Yearly operation data > Duration_Value : nd.array
        Yearly operation data of electrolyzer : duration of operation during the year.                
    Electrolyzer > H2 production (yearly) > Value : nd.array
        Yearly hydrogen production.
    Power Generation > Available energy (hourly) > Value : dict
        Available energy (hourly) after subtracting power consumed by electrolyzer. 
        (dictionary of years).
    Power Generation > Available energy (daily) > Value : dict
        Available power (daily) after subtracting power consumed by electrolyzer.
    '''

    def __init__(self, dcf, print_info):

        self.input_dict_resolved = input_resolver_function(input_dict, dcf, 'Electrolyzer_Plugin')

        self.calculate_H2_production(dcf)
        self.stack_lifetime = calculate_stack_replacement(self.yearly_data_duration, 
                                    self.input_dict_resolved['Electrolyzer']['Replacement time']['Value'].unit['h'])
        self.calculate_scaling_factors()

        output_inserter_function(output_dict, self, dcf, 'Electrolyzer_Plugin') 

    def calculate_H2_production(self, dcf):
        '''Using hourly power generation data and electrolyzer parameters,
        H2 production is calculated.
        '''

        energy_generation_yearly_data = self.input_dict_resolved['Power Generation']['Available energy (hourly)']['Value']

        yearly_data_year = []
        yearly_data_production = []
        yearly_data_duration = []
        yearly_data_unused_energy = {}
        yearly_data_unused_energy_daily = {}

        for year in dcf.operation_years:

            energy_generation = energy_generation_yearly_data[year].unit['J']

            electrolyzer_power_demand, power_increase_ratio = calculate_electrolyzer_power_demand(
                              self.input_dict_resolved['Electrolyzer']['Power requirement increase per year']['Value'].unit['-'],
                              self.input_dict_resolved['Electrolyzer']['Nominal power']['Value'].unit['W'],
                              year) # returns: power (Watt), dimensionless

            electrolyzer_energy_demand = 3600*electrolyzer_power_demand # integrate the power over 1 hour, since we ultimately think in terms of energy involved in each 1-hour slot
            electrolyzer_energy_demand *= np.ones(len(energy_generation))
            electrolyzer_energy_consumption = np.amin(np.c_[energy_generation, electrolyzer_energy_demand], axis = 1)

            threshold = self.input_dict_resolved['Electrolyzer']['Minimum capacity']['Value'].unit['-']
            electrolyzer_capacity = electrolyzer_energy_consumption / electrolyzer_energy_demand
            electrolyzer_capacity[electrolyzer_capacity > threshold] = 1
            electrolyzer_capacity[electrolyzer_capacity <= threshold] = 0

            electrolyzer_energy_consumption *= electrolyzer_capacity

            h2_produced = calculate_hydrogen_production(
                                electrolyzer_energy_consumption,
                                self.input_dict_resolved['Electrolyzer']['Hydrogen yield per unit energy']['Value'].unit['kg/J'],
                                power_increase_ratio) # returns an array of kg of H2 produced during each hour
            
            yearly_data_year.append(year)
            yearly_data_production.append(np.sum(h2_produced))
            yearly_data_duration.append(np.sum(electrolyzer_capacity))


            # Calculation of unused energy
            unused_energy = energy_generation - electrolyzer_energy_consumption
            yearly_data_unused_energy[year] = Quantity(unused_energy, 'J')
            yearly_data_unused_energy_daily[year] = Quantity(hourly_to_daily_power(unused_energy), 'J')

        self.yearly_data_year = Quantity(np.asarray(yearly_data_year), '-')
        self.yearly_data_production = Quantity(np.asarray(yearly_data_production), 'kg')
        self.yearly_data_duration = Quantity(np.asarray(yearly_data_duration), 'h')

        self.h2_production = np.concatenate([
                                   np.zeros(dcf.inp['Financial Input Values']['Construction time']['Value']), 
                                   self.yearly_data_production.unit['kg']
                                    ])
        self.h2_production = Quantity(self.h2_production, 'kg') # needs to be expressed as a flowrate, as it ultimately serves as the plant design capacity etc
        
        self.yearly_data_unused_energy = yearly_data_unused_energy
        self.yearly_data_unused_energy_daily = yearly_data_unused_energy_daily

    def calculate_scaling_factors(self):
        '''Calculation of electrolyzer CAPEX scaling factors.
        '''

        scaling_factor = self.scaling_factor(
            self.input_dict_resolved['Electrolyzer']['Nominal power']['Value'].unit['W'],
            self.input_dict_resolved['Electrolyzer']['CAPEX reference power']['Value'].unit['W'])

        self.electrolyzer_scaling_factor = Quantity(scaling_factor, '-')
            
    def scaling_factor(self, power, reference):
        '''Calculation of CAPEX scaling factor based on nominal and reference power.
        '''
        
        number_of_tenfold_increases = np.log10(power/reference)

        return self.input_dict_resolved['CAPEX Multiplier']['Multiplier']['Value'].unit['-'] ** number_of_tenfold_increases
    
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
    stack_lifetime = len(stack_usage) / (number_of_replacements + 1.)

    return Quantity(stack_lifetime, 'year') # the inputs being : (hours of operation in the year, hours of operation before replacement), 
                                                   # the result corresponds to the number of years between replacements
