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
    "Technical Operating Parameters and Specifications": {
        "Output per year": {
            "Value": {
                "type": {float, np.ndarray},
                "bounds": (0, None),
            },
            "Unit": {
                "dimension": "mass",
            },
            "optional": False,
            "description": "Yearly output taking operating capacity factor into account."
        },
    },
    "Reverse Osmosis": {
        "Power demand": {
            "Value": {
                "type": {float,},
                "bounds": (0, None),
            },
            "Unit": {
                "dimension": "energy / volume",
            },
            "optional": False,
            "description": "Power demand of reverse osmosis plant of sea water in energy demand of reverse osmosis in energy / volume (of feed water)."
        },
        "Average operating time fraction": {
            "Value": {
                "type": {float,},
                "bounds": (0, 1),
            },
            "Unit": {
                "dimension": "dimensionless",
            },
            "optional": False,
            "description": "Fraction of time during which reverse osmosis plant is operating, a value of 1 (100%) is corresponding to 24/7 operation."
        },
        "Recovery rate": {
            "Value": {
                "type": {float,},
                "bounds": (0, 1),
            },
            "Unit": {
                "dimension": "dimensionless",
            },
            "optional": False,
            "description": "Fraction of fresh water obtained from given volume of sea water."
        },
    },
}

output_dict = {
    "Power Consumption": {
        "Reverse osmosis consumption (yearly)": {
            "Value": {
                "inserted_value": "electricity_demand",
                "type": {np.ndarray,}, 
                "dimension": "energy",
            },
            "Type": {
                "inserted_value": "consumption_type",
                "type": {str,},
            },
            "description": "Electricity demand of reverse osmosis plant per year.",
            "optional": False,
        },
    },
    "Reverse Osmosis": {
        "Capacity": {
            "Value": {
                "inserted_value": "maximum_sea_water_processing_flowrate",
                "type": {float,}, 
                "dimension": "volume/time",
            },
            "description": "Maximum sea water processing capacity per hour of reverse osmosis plant.",
            "optional": False,
        },
    },
}

class Reverse_Osmosis_Plugin:
    '''Simulation of purified water production using reverse osmosis.
    
    Parameters
    ----------
    Financial Input Values > Construction time > Value : int
        Construction time of hydrogen production plant in years.
	Technical Operating Parameters and Specifications > Output per year > Value : float
		Yearly output taking operating capacity factor into account.
    Reverse Osmosis > Power demand > Value : float
        Power demand of reverse osmosis plant of sea water.
    Reverse Osmosis > Average daily operating hours > Value : float
        Average daily operating hours of reverse osmosis plant, used for scaling of reverse osmosis plant.
    Reverse Osmosis > Recovery rate > Value : float
        Fraction of fresh water obtained from given volume of sea water.
  
    Returns
    -------
    Power Consumption > Reverse osmosis consumption (yearly) > Value : nd.array
        Electricity demand of reverse osmosis plant on each year.
    Power Consumption > Reverse osmosis consumption (yearly) > Type : str
        Type of power consumer, type is 'flexible', uses both stored and available power.
    Reverse Osmosis > Capacity > Value : float
        Maximum sea water processing capacity per hour of reverse osmosis plant.   
    '''


    def __init__(self, dcf, print_info):
        self.input_dict_resolved = input_resolver_function(input_dict, dcf, 'Reverse_Osmosis_Plugin')

        self.calculate_electricity_demand(dcf)
        self.calculate_reverse_osmosis_scaling()
        self.consumption_type = "flexible"

        output_inserter_function(output_dict, self, dcf, 'Reverse_Osmosis_Plugin') 
                
    def calculate_electricity_demand(self, dcf):
        '''Calculation of electricity demand for reverse osmosis based on
        yearly amount of hydrogen production.
        '''
        MOLAR_RATIO_WATER = 18.01528 / 2.016
        DENSITY_WATER_KG_PER_M3 = 997

        output_per_year_kg_H2 = self.input_dict_resolved['Technical Operating Parameters and Specifications']['Output per year']['Value'].unit['kg']

        fresh_water_demand_kg = output_per_year_kg_H2 * MOLAR_RATIO_WATER
        fresh_water_demand_m3 = fresh_water_demand_kg / DENSITY_WATER_KG_PER_M3

        self.sea_water_demand = Quantity(fresh_water_demand_m3 / self.input_dict_resolved['Reverse Osmosis']['Recovery rate']['Value'].unit['-'], 'm3')

        electricity_demand_J = self.sea_water_demand.unit['m3'] * self.input_dict_resolved['Reverse Osmosis']['Power demand']['Value'].unit['J/m3']
        self.electricity_demand = Quantity(electricity_demand_J[dcf.inp['Financial Input Values']['Construction time']['Value']:], 'J')

    def calculate_reverse_osmosis_scaling(self):
        '''
        Calculation of maximum sea water processing capacity per hour based on
        yearly sea water demand and average daily operating hours.
        '''

        HOURS_IN_A_YEAR = 365*24

        average_operating_time_fraction = self.input_dict_resolved['Reverse Osmosis']['Average operating time fraction']['Value'].unit['-']
        yearly_operating_hours = average_operating_time_fraction * HOURS_IN_A_YEAR
        
        try:
            maximum_yearly_sea_water_demand_m3 = max(self.sea_water_demand.unit['m3'])
        except TypeError:
            maximum_yearly_sea_water_demand_m3 = self.sea_water_demand.unit['m3']

        self.maximum_sea_water_processing_flowrate = Quantity(maximum_yearly_sea_water_demand_m3 / yearly_operating_hours, 'm3/h')