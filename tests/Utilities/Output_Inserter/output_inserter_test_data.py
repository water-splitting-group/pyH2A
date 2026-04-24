from pyH2A.Utilities.Unit_handler.quantity import Quantity
import numpy as np


class DummyDCF:
    def __init__(self):
        self.inp = {
            'Power Generation': {
                'Stored Energy (daily)': {
                    'Value': 0,
                },
                'Available Energy (daily)': {
                    'Value': 100,
                },
            },
            'Untouched Parameter': {
                'Parameter': {
                    'Value': 100,
                }
            }
        }


output_dict = {
    'Power Generation': {
        'Stored Energy (daily)': {
            'Value': {
                'inserted_value': 'daily_stored_power',
                'type': {dict, },
                'dimension': 'energy'
            },
            'optional': False,
            'add_processed': True,
            'insert_path': True,
            'path_key': 'Path',
            'description': 'Electricity stored in battery daily (dictionary of years)',
        },
        'Available Energy (daily)': {
            'Value': {
                'inserted_value': Quantity(0, 'kWh'),
                'type': {int, float, np.ndarray},
                'dimension': 'energy'
            },
            'optional': False,
            'add_processed': True,
            'insert_path': True,
            'path_key': 'Path',
            'description': 'Setting available Energy (daily) to 0',
        },
        'Insertion of a string': {
            'Value': {
                'inserted_value': 'attribute_string',
                'type': {str, },
            },
            'optional': False,
            'description': 'Insertion of a string value to check that the output resolver can handle non-numeric values',

        }
    },
    'Variable Operating Costs': {
        'Water Utility Costs': {
            'Usage_Value': {
                'inserted_value': 'water_usage',
                'type': {int, float, np.ndarray},
                'dimension': 'volume'
            },
            'Cost_Value': {
                'inserted_value': 'water_cost',
                'type': {int, float, np.ndarray},
                'dimension': 'currency'
            },
            'optional': False,
            'add_processed': False,
            'insert_path': False,
            'description': 'Water usage and cost for the water utility, calculated from water demand and water cost per unit volume.'
        }
    },
    'Optional Group': {
        'Optional Parameter': {
            'Value': {
                'inserted_value': 'optional_parameter',
                'type': {int, float, np.ndarray},
                'dimension': 'dimensionless'
            },
            'optional': True,
            'add_processed': True,
            'insert_path': True,
            'path_key': 'Path',
            'description': 'An optional parameter that may or may not be inseter into dcf.inp.'
        }
    },
    'special_insertions':
        {'sum_all_tables': {
            '<...> Direct Capital Cost <...>': {
                'Summed Total': {
                    'Value': {
                        'type': {int, float},
                    },
                    'optional': True,
                    'description': 'Summed total of direct capital costs across all tables'
                },
            },
        },
    },
}


class DummyPlugin:

    def __init__(self, dcf, print_info):

        self.input_dict_resolved = {
            'Catalyst': {
                'Lifetime': {
                    'Value': Quantity(100, 's')
                }
            }
        }

        self.daily_stored_power = {
            2026: {'second_level': Quantity(500, 'kWh')}}
        self.attribute_string = 'This is a string value'
        self.water_usage = Quantity(np.array([100, 200, 300]), 'm3')
        self.water_cost = Quantity(np.array([10, 20, 30]), 'USD')
        self.optional_parameter = Quantity(42, '-')


class DummyDCF_after_insertion:
    def __init__(self):
        self.inp = {
            'Power Generation': {
                'Stored Energy (daily)': {
                    'Value': {2026: {'second_level': Quantity(500, 'kWh')}},
                    'Processed': 'Yes',
                    'Path': 'None',
                },
                'Available Energy (daily)': {
                    'Value': Quantity(0, 'kWh'),
                    'Processed': 'Yes',
                    'Path': 'None',
                },
                'Insertion of a string': {
                    'Value': 'This is a string value',
                    'Processed': 'Yes',
                },
            },
            'Untouched Parameter': {
                'Parameter': {
                    'Value': 100,
                }
            },
            'Variable Operating Costs': {
                'Water Utility Costs': {
                    'Usage_Value': Quantity(np.array([100, 200, 300]), 'm3'),
                    'Cost_Value': Quantity(np.array([10, 20, 30]), 'USD'),
                },
            },
            'Optional Group': {
                'Optional Parameter': {
                    'Value': Quantity(42, '-'),
                    'Processed': 'Yes'
                },
            }
        }
