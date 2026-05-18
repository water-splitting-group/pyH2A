import numpy as np

from pyH2A.Utilities.input_modification import sum_all_tables_quantity
from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler import Quantity

input_dict = {
    'Plugin A Input': {
        'Power': {
            'Value': {
                'type': {float, int},
                'bounds': (0, None),
            },
            'Unit': {
                'dimension': 'power'
            },
            'description': 'Power Test Value'
        }
    },
    '<...> Sum Testing <...>': {
        '<...>': {
            'Value': {
                'type': {float, int},
                'bounds': (0, None),
                'path': 'Sum Path'
            },
            'Unit': {
                'dimension': 'currency'
            },
            'optional': True,
            'description': 'Sum Test Value'
        },
        'sum_tables': {
            'mode': 'all',
            'arguments': {
                'bottom_key': 'Value',
                'middle_key_total_insertion': 'Summed Total',
                'middle_key_total_group_insertion': 'Summed Group Total',
                'middle_key_contributions_insertion': 'Contributions',
                'bottom_key_insertion': 'Value'
            }
        },
    },
    '<...> Indirect Testing <...>': {
        '<...>': {
            'Value': {
                'type': {float, int},
                'bounds': (0, None),
                'path': 'Path'
            },
            'Unit': {
                'dimension': 'currency'
            },
            'optional': True,
            'description': 'Indirect Test Value'
        },
        'sum_tables': {
            'mode': 'all',
            'arguments': {
                'bottom_key': 'Value',
                'middle_key_total_insertion': 'Summed Total',
                'middle_key_total_group_insertion': 'Summed Group Total',
                'middle_key_contributions_insertion': 'Contributions',
                'bottom_key_insertion': 'Value'
            }
        },
    },
    'Individual Table Sum': {
        '<...>': {
            'Value': {
                'type': {float, int},
                'bounds': (0, None),
                'path': 'Path'
            },
            'Unit': {
                'dimension': 'currency'
            },
            'optional': True,
            'description': 'Individual Table Sum Test Value'
        },
        'sum_tables': {
            'mode': 'single',
            'arguments': {
                'bottom_key': 'Value',
                'middle_key_total_insertion': 'Summed Total',
                'bottom_key_insertion': 'Value'
            }
        }
    }
}

output_dict = {
    'Plugin A Output': {
        'Energy': {
            'Value': {
                'inserted_value': 'energy',
                'type': {float, int, np.ndarray},
                'dimension': 'energy'
            },
            'description': 'Calculated energy'
        }
    },
    'special_insertions': {
        'sum_all_tables': {
            '<...> Sum Testing <...>': {
                'Summed Total': {
                    'Value': {
                        'type': {float, int},
                        'dimension': 'currency',
                    },
                    'description': 'Sum of table values'
                },
            },
            'Sum Testing': {
                'Summed Total': {
                    'Value': {
                        'type': {float, int},
                        'dimension': 'currency',        
                    },
                    'optional': True,
                    'description': 'Sum of table values'
                },
                'Summed Group Total': {
                    'Value': {
                        'type': {float, int},
                        'dimension': 'currency',
                    },
                    'optional': False,
                    'description': 'Sum of all values in table group "Sum Testing"'
                },
                'Contributions': {
                    'Value': {
                        'type': {dict},
                        'dimension': 'currency',
                    },
                    'description': 'Contributions to the sum'
                },
            },
            '<...> Indirect Testing <...>': {
                'Summed Total': {
                    'Value': {
                        'type': {float, int},
                        'dimension': 'currency',
                    },
                    'description': 'Sum of all values in table group "Indirect Testing"'
                }
            },
            'Indirect Testing': {
                'Summed Group Total': {
                    'Value': {
                        'type': {float, int},
                        'dimension': 'currency'
                    },
                    'description': 'Sum of all values in table group "Indirect Testing"'
                },
                'Contributions': {
                    'Value': {
                        'type': {dict},
                        'dimension': 'currency',
                    },
                    'description': 'Contributions to the sum'
                },
            },
            'Individual Table Sum': {
                'Summed Total': {
                    'Value': {
                        'type': {float, int},
                        'dimension': 'currency'
                    },
                    'description': 'Sum of all values in this table'
                }
            }
        }
    } 
}

class Test_Plugin_A:

    def __init__(self, dcf, print_info):

        self.inp = input_resolver_function(input_dict, dcf, __name__)

        self.method_A()

        output_inserter_function(output_dict, self, dcf, __name__)

    def method_A(self):

        power = self.inp['Plugin A Input']['Power']['Value']
        time = Quantity(20, 'h')

        energy = np.ones(3) * power.unit['W'] * time.unit['s']
        self.energy = Quantity(energy, 'J')
    