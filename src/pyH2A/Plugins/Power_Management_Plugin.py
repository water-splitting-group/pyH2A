from pyH2A.Utilities.input_modification import daily_to_yearly_power_quantity
from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
import numpy as np
from pyH2A.Utilities.docstring_generation import generate_docstring

class Power_Management_Plugin:

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
                "Available energy (daily)": {
                    "Value": {
                        "type": {dict,},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "energy",
                    },
                    "optional": True,
                    "description": "Available energy on a daily basis, as a dictionary of years. "
                                    "If not provided, it is assumed that no energy is available."
                },
                "Stored energy (daily)": {
                    "Value": {
                        "type": {dict,},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "energy",
                    },
                    "optional": True,
                    "description": "Stored energy on a daily basis as a dictionary of years. "
                                    "If not provided, it is assumed that no stored energy is generated."
                },
            },
            "Power Consumption": {
                "<...>": {
                    "Value": {
                        "type": {np.ndarray,float,int,},
                        "bounds": (0, None),
                    },
                    "Type": {
                        "type": {str,},
                        "options": {'flexible', 'on_demand'},
                    },
                    "Unit": {
                        "dimension": "energy",
                    },
                    "optional": True,
                    "description": "Power consumption values for each year. Can be provided for multiple consumers, "
                                    "in which case they should be provided as separate entries under Power Consumption. "
                                    "The type of consumer should be specified as either 'flexible' for consumers that "
                                    "can consume both available and stored power, or 'on_demand' for consumers "
                                    "that can only consume stored power."
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
                        "inserted_value": "remaining_flexible",
                        "type": {np.ndarray,}, 
                        "dimension": "energy",
                    },
                    "optional": True,
                    "description": "Remaining available energy, yearly basis.",
                },
                "Stored energy (yearly)": {
                    "Value": {
                        "inserted_value": "remaining_stored",
                        "type": {np.ndarray,},
                        "dimension": "energy",
                    },
                    "optional": True,
                    "description": "Remaining stored energy, yearly basis.",
                },
                "Available energy (daily)": {
                    "Value": {
                        "inserted_value": Quantity(0, 'J'),
                        "type": {float,},
                        "dimension": "energy",
                    },
                    "description": "Remaining available energy, daily basis set to 0.",
                },
                "Stored energy (daily)": {
                    "Value": {
                        "inserted_value": Quantity(0, 'J'),
                        "type": {float,},
                        "dimension": "energy",
                    },
                    "description": "Remaining stored energy, daily basis set to 0.",
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
        
        summary = "Management of electricity production and consumption."
        
        self.__class__.__doc__ = generate_docstring(
            summary,
            self.input_dict,
            self.output_dict
        )

    def _run(self, dcf):
        self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, 'Power_Management_Plugin')  

        if 'Power Consumption' in self.input_dict_resolved:    
            self.calculate_consumers()
            self.calculate_electricity_cost()

        output_inserter_function(self.output_dict, self, dcf, 'Power_Management_Plugin') 
        
    def calculate_consumers(self):
        '''Negoitate available and stored power with power consumers. 
        Including fall back options if power generation (either available power or stored power
        is not available). In those cases they are set to zero. 
        '''

        try:
            flexible_available_energy_yearly = daily_to_yearly_power_quantity(
                self.input_dict_resolved['Power Generation']['Available energy (daily)']['Value'])
        except KeyError:
            flexible_available_energy_yearly = np.zeros_like(self.input_dict_resolved['Time']['Years']['Value']['Operation years ones'].unit['-'])

        try:
            stored_available_energy_yearly = daily_to_yearly_power_quantity(
                self.input_dict_resolved['Power Generation']['Stored energy (daily)']['Value'])
        except KeyError:
            stored_available_energy_yearly = np.zeros_like(self.input_dict_resolved['Time']['Years']['Value']['Operation years ones'].unit['-'])

        (self.total_unfulfilled, 
         self.remaining_flexible, 
         self.remaining_stored) = allocate_power(self.input_dict_resolved['Power Consumption'], 
                                                 flexible_available_energy_yearly, 
                                                 stored_available_energy_yearly)

    def calculate_electricity_cost(self):

        self.electricity_cost = Quantity(self.total_unfulfilled.unit['J']
                                         * self.input_dict_resolved['Grid Electricity']['Cost']['Value'].unit['USD/J'], 
                                'USD')
    
def allocate_power(consumption, flexible_power, stored_power):
    """Allocate available power to consumers based on their type."""

    # Initialize remaining power
    remaining_flexible = flexible_power.unit['J'].copy()
    remaining_stored = stored_power.unit['J'].copy()
    
    # Initialize total unfufilled demand
    total_unfulfilled = np.zeros_like(flexible_power.unit['J'])
    
    # Process on_demand consumers first (stored power only)
    for key, consumer in consumption.items():
        if consumer['Type'] == 'on_demand':

            demand = consumer['Value'].unit['J']

            remaining_stored, unfulfilled = calculate_fulfillment(demand, remaining_stored)

            total_unfulfilled += unfulfilled
        
    # Process flexible consumers (both power sources)
    for key, consumer in consumption.items():
        if consumer['Type'] == 'flexible':

            demand = consumer['Value'].unit['J']
            
            # Try flexible power first
            remaining_flexible, remaining_demand = calculate_fulfillment(demand, remaining_flexible)

            # Use stored power for remaining demand
            remaining_stored, unfulfilled = calculate_fulfillment(remaining_demand, remaining_stored)
            
            total_unfulfilled += unfulfilled

        elif consumer['Type'] == 'on_demand':
            pass
        else:
            print('Warning: Unknown power consumer type:', consumer['Type'], f',    in Power Consumption > {key} > Type')
    
    return Quantity(total_unfulfilled, 'J'), Quantity(remaining_flexible, 'J'), Quantity(remaining_stored, 'J')
        
def calculate_fulfillment(demand, remaining):
    """Calculate fulfillment of demand using stored power."""
    
    fulfilled = np.minimum(demand, remaining)

    remaining -= fulfilled
    unfulfilled = demand - fulfilled
    
    return remaining, unfulfilled

