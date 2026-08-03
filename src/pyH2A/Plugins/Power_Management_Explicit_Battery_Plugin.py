from pyH2A.Utilities.input_modification import dict_to_yearly_array_power_quantity
from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
import numpy as np

class Power_Management_Explicit_Battery_Plugin:
    '''Management of electricity production and consumption.
    
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
                    "optional": True,
                    "description": "Available energy on an hourly basis, as a dictionary of years. "
                                    "If not provided, it is assumed that no energy is available."
                },
            },
            "Power Consumption": {
                "<...>": {
                    "Value": {
                        "type": {np.ndarray,float,int,},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "energy",
                    },
                    "optional": True,
                    "description": "Power consumption values for each year. Can be provided for multiple consumers, "
                                    "in which case they should be provided as separate entries under Power Consumption. "
                                    "Only the flexible consumers (i.e. the ones whose consumption can take place at any moment) must be specified"
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
                    "optional": True,
                    "description": "Unsatisfied demand of the main consumer. Dictionary of years"
                },
            },
            "Grid Electricity": {
                "Cost": {
                    "Value": {
                        "type": {float, np.ndarray, int},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "currency / energy",
                    },
                    "optional": True,
                    "description": "Cost of grid electricity. Can be provided as a single value "
                                    "or as an array with values for each year. If not provided, "
                                    "it is assumed that grid electricity is not used."
                },
            },
        }

        self.output_dict = {
            "Power Generation": {
                "Available energy (yearly)": {
                    "Value": {
                        "inserted_value": "remaining_available",
                        "type": {np.ndarray,}, 
                        "dimension": "energy",
                    },
                    "optional": True,
                    "description": "Remaining available energy, yearly basis.",
                },
            },
            "Grid Electricity": {
                "Used grid electricity (yearly)": {
                    "Value": {
                        "inserted_value": "total_unfulfilled",
                        "type": {np.ndarray,},
                        "dimension": "energy",
                    },
                    "optional": True,
                    "description": "Used grid electricity, yearly basis.",
                },
            },
            "Other Variable Operating Cost - Grid Electricity": {
                "Cost of grid electricity (yearly)": {
                    "Value": {
                        "inserted_value": "electricity_cost",
                        "type": {np.ndarray,},
                        "dimension": "currency",
                    },
                    "optional": True,
                    "description": "Cost of grid electricity, yearly basis.",
                },
            },
        }



    def _run(self, dcf):    

        self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, 'Power_Management_Explicit_Battery_Plugin')  

        if 'Power Consumption' in self.input_dict_resolved:    
            self.calculate_consumers()
            self.calculate_electricity_cost()

        output_inserter_function(self.output_dict, self, dcf, 'Power_Management_Explicit_Battery_Plugin') 

        '''
        Allocate the remaining renewable excess to secondary consumers (i.e. consumers other than the main one).

        At this point the battery has already been simulated.
        The main consumer (with non-flexible consumption) has already been supplied by direct renewable generation + battery as much as possible.

        Therefore:
        - the remaining deficit of the main consumer must be supplied from the grid.
        - the remaining renewable excess may only be used by the secondary consumers, which are assumed to be flexible;
        '''

    def calculate_consumers(self):

        try:
            available_energy_yearly = dict_to_yearly_array_power_quantity(self.input_dict_resolved['Power Generation']['Available energy (hourly)']['Value'])
        except KeyError:
            available_energy_yearly = Quantity(
                                            np.zeros_like(self.input_dict_resolved['Time']['Years']['Value']['Operation years ones'].unit['-']), 
                                            'J'
                                            )

        try:
            main_unfulfilled_yearly = dict_to_yearly_array_power_quantity(self.input_dict_resolved['Hourly Consumer Profile']['Unsatisfied demand']['Value'])
        except KeyError:
            main_unfulfilled_yearly = Quantity(
                                            np.zeros_like(available_energy_yearly.unit['J']), 
                                            'J')
            
        self.remaining_available, secondary_unfulfilled = allocate_power(self.input_dict_resolved['Power Consumption'], available_energy_yearly)

        self.total_unfulfilled = Quantity(secondary_unfulfilled.unit['J'] + main_unfulfilled_yearly.unit['J'],'J')
   

    def calculate_electricity_cost(self):

        self.electricity_cost = Quantity(self.total_unfulfilled.unit['J']
                                        * self.input_dict_resolved['Grid Electricity']['Cost']['Value'].unit['USD/J'], 
                                'USD')

    
def allocate_power(consumption, available_power):
    """
    Allocate remaining renewable electricity to secondary consumers.
    Any remaining demand is assumed to come from the grid.
    """

    remaining_available = available_power.unit['J'].copy()

    total_unfulfilled = np.zeros_like(remaining_available)

    for _, consumer in consumption.items():

        demand = consumer['Value'].unit['J']

        fulfilled = np.minimum(demand, remaining_available)

        remaining_available -= fulfilled

        total_unfulfilled += demand - fulfilled

    return Quantity(remaining_available, 'J'), Quantity(total_unfulfilled, 'J')


