from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.Physical_Properties.Physical_properties import Physical_properties as PP
import numpy as np

class Reverse_Osmosis_Plugin:
    '''Simulation of purified water production using reverse osmosis.
    
    Parameters
    ----------
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
            "Purified Water Yearly Demand": {
                "<...>": {
                    "Value": {
                        "type": {np.ndarray},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "mass",
                    },
                    "optional": False,
                    "description": "Yearly mass of water needed by the various units of the process."
                },        
            },
            "Reverse Osmosis": {
                "Power demand": {
                    "Value": {
                        "type": {int, float,},
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
                        "type": {int, float,},
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
                        "type": {int, float,},
                        "bounds": (0, 1),
                    },
                    "Unit": {
                        "dimension": "dimensionless",
                    },
                    "optional": False,
                    "description": "Fraction of fresh water obtained from given volume of sea water."
                },
                "Device output": {
                    "Value": {
                        "type": {int,float,},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "volume / time",
                    },
                    "optional": True,
                    "description": "Purified water output of one reverse osmosis device, used to calculate the number of devices."
                },
            },
        }

        self.output_dict = {
            "Flexible Power Demand": {
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
                "Number of devices": {
                    "Value": {
                        "inserted_value": "number_of_devices",
                        "type": {float,int,},
                        "dimension": "dimensionless",
                    },
                    "description": "Number of reverse osmosis devices required for the system, whole lifetime.",
                    "optional": True,
                },
            },
        }

    def _run(self, dcf):
        self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, 'Reverse_Osmosis_Plugin')

        self.calculate_electricity_demand()
        self.calculate_reverse_osmosis_scaling()
        self.consumption_type = "flexible"

        output_inserter_function(self.output_dict, self, dcf, 'Reverse_Osmosis_Plugin') 
                
    def calculate_electricity_demand(self):
        '''Calculation of electricity demand for reverse osmosis based on
        yearly amount of hydrogen production.
        '''

        fresh_water_demand_kg_by_year = np.zeros_like(self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-'])

        for _, demand in self.input_dict_resolved['Purified Water Yearly Demand'].items():
            fresh_water_demand_kg_by_year += demand['Value'].unit['kg']

        self.fresh_water_demand_volume_by_year = PP.Volume(T= Quantity(25, 'degC'), 
                                                  P = Quantity(1, 'bar'), 
                                                  amount = {'H2O': Quantity(fresh_water_demand_kg_by_year, 'kg')},
                                                  phase = 'L', 
                                                  composition_basis= 'mass')

        self.sea_water_demand_by_year = Quantity(self.fresh_water_demand_volume_by_year.unit['m3'] 
                                                 / self.input_dict_resolved['Reverse Osmosis']['Recovery rate']['Value'].unit['-'], 
                                        'm3')

        electricity_demand_J_by_year = (self.sea_water_demand_by_year.unit['m3'] 
                                        * self.input_dict_resolved['Reverse Osmosis']['Power demand']['Value'].unit['J/m3'])
        self.electricity_demand_by_year = Quantity(electricity_demand_J_by_year, 'J')

    def calculate_reverse_osmosis_scaling(self):
        '''
        Calculation of maximum sea water processing capacity per hour based on
        yearly sea water demand and average daily operating hours.
        '''

        maximum_yearly_sea_water_demand_m3 = max(self.sea_water_demand_by_year.unit['m3'])
        self.maximum_sea_water_processing_flowrate = Quantity(maximum_yearly_sea_water_demand_m3 
                                                              / self.input_dict_resolved['Reverse Osmosis']['Average operating time fraction']['Value'].unit['-'], 
                                                     'm3/year')

        if 'Device output' in self.input_dict_resolved['Reverse Osmosis']:
            maximum_fresh_water_processing_flowrate = Quantity(self.maximum_sea_water_processing_flowrate.unit['m3/year'] 
                                                               * self.input_dict_resolved['Reverse Osmosis']['Recovery rate']['Value'].unit['-'],
                                                      'm3/year')

            self.number_of_devices = Quantity(maximum_fresh_water_processing_flowrate.unit['m3/year'] 
                                              / self.input_dict_resolved['Reverse Osmosis']['Device output']['Value'].unit['m3/year'],
                                     '-')

        
        
