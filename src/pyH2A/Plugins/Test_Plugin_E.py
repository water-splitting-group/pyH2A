from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity

input_dict = {
    'GT Battery Input': {
        'Base Quantity': {
            'Value': {
                'type': {float},
                'bounds': (0, None),
            },
            'Unit': {
                'dimension': 'mass'
            },
            'description': 'Reference battery mass per smartphone'
        },
        'Scenario Factor': {
            'Value': {
                'type': {float},
                'bounds': (0, None),
            },
            'Unit': {
                'dimension': 'dimensionless'
            },
            'description': 'Scenario multiplier applied to the base battery mass'
        }
    }
}

output_dict = {
    'GT Battery Output': {
        'Battery': {
            'Value': {
                'inserted_value': 'quantity',
                'type': {float},
                'dimension': 'mass'
            },
            'description': 'Computed battery mass for the LCA GT Components table'
        }
    }
}

class Test_Plugin_E:
    '''Computes the battery mass feeding the LCA GT Components table.

    Parameters
    ----------
    GT Battery Input > Base Quantity > Value : float
        Reference battery mass per smartphone.
    GT Battery Input > Scenario Factor > Value : float
        Scenario multiplier applied to the base mass.

    Returns
    -------
    GT Battery Output > Battery > Value : float
        Base mass multiplied by the scenario factor.
    '''

    def __init__(self, dcf, print_info):
        self.inp = input_resolver_function(input_dict, dcf, __name__)

        self.calculate_quantity()

        output_inserter_function(output_dict, self, dcf, __name__)

    def calculate_quantity(self):
        table = self.inp['GT Battery Input']
        base = table['Base Quantity']['Value'].unit['kg']
        factor = table['Scenario Factor']['Value'].unit['-']

        self.quantity = Quantity(base * factor, 'kg')
