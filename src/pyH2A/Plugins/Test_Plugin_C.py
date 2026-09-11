from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity

input_dict = {
    'GT Circuit Board Input': {
        'Base Quantity': {
            'Value': {
                'type': {float},
                'bounds': (0, None),
            },
            'Unit': {
                'dimension': 'dimensionless'
            },
            'description': 'Reference circuit board quantity per smartphone'
        },
        'Scenario Factor': {
            'Value': {
                'type': {float},
                'bounds': (0, None),
            },
            'Unit': {
                'dimension': 'dimensionless'
            },
            'description': 'Scenario multiplier applied to the base circuit board quantity'
        }
    }
}

output_dict = {
    'GT Circuit Board Output': {
        'Circuit Board': {
            'Value': {
                'inserted_value': 'quantity',
                'type': {float},
                'dimension': 'dimensionless'
            },
            'description': 'Computed circuit board quantity for the LCA GT Components table'
        }
    }
}

class Test_Plugin_C:
    '''Computes the circuit board quantity feeding the LCA GT Components table.

    Parameters
    ----------
    GT Circuit Board Input > Base Quantity > Value : float
        Reference circuit board quantity per smartphone.
    GT Circuit Board Input > Scenario Factor > Value : float
        Scenario multiplier applied to the base quantity.

    Returns
    -------
    GT Circuit Board Output > Circuit Board > Value : float
        Base quantity multiplied by the scenario factor.
    '''

    def __init__(self, dcf, print_info):
        self.inp = input_resolver_function(input_dict, dcf, __name__)

        self.calculate_quantity()

        output_inserter_function(output_dict, self, dcf, __name__)

    def calculate_quantity(self):
        table = self.inp['GT Circuit Board Input']
        base = table['Base Quantity']['Value'].unit['-']
        factor = table['Scenario Factor']['Value'].unit['-']

        self.quantity = Quantity(base * factor, '-')
