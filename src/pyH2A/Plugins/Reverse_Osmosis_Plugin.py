from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
import numpy as np

input_dict = {
    "Technical Operating Parameters and Specifications": {
        "Design output by year": {
            "Value": {
                "type": {np.ndarray},
                "bounds": (0, None),
            },
            "Unit": {
                "dimension": "mass",
            },
            "optional": False,
            "description": "Yearly output ignoring capacity factor."
        },
		"Operating capacity factor": { 
			"Value": {
				"type": {float, int},
				"bounds": (0, 1),
            },
			"Unit": {
				"dimension": "dimensionless",
			},
			"optional": False,
			"description": "Operating capacity factor value between 0 and 1 or percentage value."
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
            "description": "Power demand of reverse osmosis plant of sea water in energy / volume (of feed water)."
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
            "description": "Fraction of time during which reverse osmosis plant is operating, "
                           "a value of 1 (100%) is corresponding to 24/7 (continuous) operation."
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
                "inserted_value": "electricity_demand_by_year",
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
                "type": {float,int,}, 
                "dimension": "volume / time",
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
	Technical Operating Parameters and Specifications > Design output by year > Value : nd.array
		Yearly output ignoring operating capacity factor.
	Technical Operating Parameters and Specifications > Operating capacity factor > Value : float, int
		Operating capacity factor value between 0 and 1 or percentage value.        
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

        output_per_year_kg_H2 = (self.input_dict_resolved['Technical Operating Parameters and Specifications']['Design output by year']['Value'].unit['kg'] 
                                 * self.input_dict_resolved['Technical Operating Parameters and Specifications']['Operating capacity factor']['Value'].unit['-'])

        fresh_water_demand_kg_by_year = output_per_year_kg_H2 * MOLAR_RATIO_WATER
        fresh_water_demand_m3_by_year = fresh_water_demand_kg_by_year / DENSITY_WATER_KG_PER_M3

        self.sea_water_demand_by_year = Quantity(fresh_water_demand_m3_by_year 
                                         / self.input_dict_resolved['Reverse Osmosis']['Recovery rate']['Value'].unit['-'], 
                                         'm3')

        # Fixing the array slicing with time plugin
        electricity_demand_J_by_year = (self.sea_water_demand_by_year.unit['m3'] 
                                        * self.input_dict_resolved['Reverse Osmosis']['Power demand']['Value'].unit['J/m3'])
        
        idx = dcf.inp['Financial Input Values']['Construction time']['Value']
        self.electricity_demand_by_year = Quantity(electricity_demand_J_by_year[idx:], 'J')

    def calculate_reverse_osmosis_scaling(self):
        '''
        Calculation of maximum sea water processing capacity per hour based on
        yearly sea water demand and average daily operating hours.
        '''

        maximum_yearly_sea_water_demand_m3 = max(self.sea_water_demand_by_year.unit['m3'])
        self.maximum_sea_water_processing_flowrate = Quantity(maximum_yearly_sea_water_demand_m3 
                                                              / self.input_dict_resolved['Reverse Osmosis']['Average operating time fraction']['Value'].unit['-'], 
                                                     'm3/year')
