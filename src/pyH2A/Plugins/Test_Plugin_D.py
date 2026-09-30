from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity

input_dict = {
    'GT Display Input': {
        'Base Quantity': {
            'Value': {
                'type': {float},
                'bounds': (0, None),
            },
            'Unit': {
                'dimension': 'mass'
            },
            'description': 'Reference display mass per smartphone'
        },
        'Scenario Factor': {
            'Value': {
                'type': {float},
                'bounds': (0, None),
            },
            'Unit': {
                'dimension': 'dimensionless'
            },
            'description': 'Scenario multiplier applied to the base display mass'
        }
    }
}

output_dict = {
    'GT Display Output': {
        'Display': {
            'Value': {
                'inserted_value': 'quantity',
                'type': {float},
                'dimension': 'mass'
            },
            'description': 'Computed display mass for the LCA GT Components table'
        }
    }
}

class Test_Plugin_D:
    '''Computes the display mass feeding the LCA GT Components table.

    Parameters
    ----------
    GT Display Input > Base Quantity > Value : float
        Reference display mass per smartphone.
    GT Display Input > Scenario Factor > Value : float
        Scenario multiplier applied to the base mass.

    Returns
    -------
    GT Display Output > Display > Value : float
        Base mass multiplied by the scenario factor.
    '''

    def __init__(self, dcf, print_info):
        self.inp = input_resolver_function(input_dict, dcf, __name__)

        self.calculate_quantity()

        output_inserter_function(output_dict, self, dcf, __name__)

    def calculate_quantity(self):
        table = self.inp['GT Display Input']
        base = table['Base Quantity']['Value'].unit['kg']
        factor = table['Scenario Factor']['Value'].unit['-']

        self.quantity = Quantity(base * factor, 'kg')
