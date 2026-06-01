import numpy as np

from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler import Quantity

input_dict = {
    'Plugin A Output': {
        'Energy': {
            'Value': {
                'type': {float, int, np.ndarray},
                'bounds': (0, None),
            },
            'Unit': {
                'dimension': 'energy'
            },
            'description': 'Energy test value'
        },
    },
    'Plugin B Input': {
        'Mass': {
            'Value': {
                'type': {float, int, np.ndarray},
                'bounds': (0, None),
            },
            'Unit': {
                'dimension': 'mass'
            },
            'description': 'Mass test data',
            'optional': True
        }
    },
    'Plugin B - Value/Unit pairs' : {
        'Test Input': {
            'Usage_Value': {
                'type': {float, int},
                'bounds': (0, None),
                'path': 'Usage_Path'
            },
            'Usage_Unit': {
                'dimension': 'power'
            },
            'Cost_Value': {
                'type': {float, int},
                'bounds': (0, None),
                'path': 'Cost_Path'
            },
            'Cost_Unit': {
                'dimension': 'currency'
            }
        }
    }
}

output_dict = {
    'Plugin B Output': {
        'Energy density': {
            'Value': {
                'inserted_value': 'energy_density',
                'type': {float, int, np.ndarray},
                'dimension': 'energy / mass'
            },
            'description': 'Energy density calculated'
        }
    }
}


class Test_Plugin_B:

    def __init__(self, dcf, print_info):

        self.inp = input_resolver_function(input_dict, dcf, __name__)

        self.method_B()

        output_inserter_function(output_dict, self, dcf, __name__)

    def method_B(self):

        mass = Quantity(200, 'g')

        mass = self.inp['Plugin B Input']['Mass']['Value']
        energy = self.inp['Plugin A Output']['Energy']['Value']

        energy_density = energy.unit['J'] / mass.unit['kg']
        self.energy_density = Quantity(energy_density, 'J / kg')


