import numpy as np

from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler import Quantity

class Test_Plugin_B:

    def __init__(self, dcf, print_info, run = True):
        self._set_up(dcf)
        if run:
            self._run(dcf)

    def _set_up(self, dcf):

        self.functional_unit = dcf.functional_unit

        self.input_dict = {
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
                },
                'Mass per energy': {
                    'Value': {
                        'type': {float, int},
                        'bounds': (0, None),
                    },
                    'Unit': {
                        'dimension': 'mass / energy'
                    },
                    'description': 'Mass per energy test data',
                    'optional': False
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

        self.output_dict = {
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

    def _run(self, dcf):
        self.inp = input_resolver_function(self.input_dict, dcf, __name__)

        self.method_B()

        output_inserter_function(self.output_dict, self, dcf, __name__)

    def method_B(self):

        mass = Quantity(200, 'g')

        mass = self.inp['Plugin B Input']['Mass']['Value']
        energy = self.inp['Plugin A Output']['Energy']['Value']

        energy_density = energy.unit['J'] / mass.unit['kg']
        self.energy_density = Quantity(energy_density, 'J / kg')


