import numpy as np

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
    