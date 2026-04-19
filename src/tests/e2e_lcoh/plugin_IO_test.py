import numpy as np

from pyH2A.run_pyH2A import pyH2A
from pyH2A.Utilities.Unit_Handler.quantity import Quantity

from tests.Utilities.check_dicts_for_testing import check_dicts


def test_plugin_IO():

    result = pyH2A('src/tests/end_to_end/PV_E_Plugin_IO.md', 
                   'src/tests/end_to_end/')
    
    expected_plugin_a_input = {
        'Power': {
            'Former Value': 10,
            'Path': 'Photovoltaic > Nominal Power (kW) > Value',
            'Processed': 'Yes',
            'Unit': 'kW',
            'Value': 82500.0
        }
    }

    expected_plugin_a_output = {
        'Energy': {
            'Processed': 'Yes',
            'Value': Quantity(np.array([5.94e+12, 5.94e+12, 5.94e+12]), 'J')
        }
    }

    expected_plugin_b_input = {
        'Mass': {
            'Comment': 'Value "2" is in unit kg/J, multiplying by "Plugin A Output > Energy > Value" (which is dimension energy, used in basic unit "J") gives kg',
            'Former Value': 2,
            'Path': 'Plugin A Output > Energy > Value',
            'Processed': 'Yes',
            'Unit': 'kg',
            'Value': np.array([1.188e+13, 1.188e+13, 1.188e+13])
        }
    }

    expected_plugin_b_output = {
        'Energy density': {
            'Processed': 'Yes',
            'Value': Quantity(np.array([0.5, 0.5, 0.5]), 'J / kg')
        }
    }

    check_dicts(result.base_case.inp['Plugin A Input'], expected_plugin_a_input)
    check_dicts(result.base_case.inp['Plugin A Output'], expected_plugin_a_output)
    check_dicts(result.base_case.inp['Plugin B Input'], expected_plugin_b_input)
    check_dicts(result.base_case.inp['Plugin B Output'], expected_plugin_b_output)
    
if __name__ == '__main__':
    test_plugin_IO()
