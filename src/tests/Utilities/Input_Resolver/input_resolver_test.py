import pytest
import numpy as np

from pyH2A.Utilities.Input_Resolver.input_resolver import input_resolver_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity

from tests.Utilities.Input_Resolver.input_resolver_test_data import DummyDCF, input_dict, input_dict_resolved


def check_dicts(actual, expected, tolerance=1e-12, path=""):

    # Improve set assert message
    missing_in_act = set(expected.keys()) - set(actual.keys())
    missing_in_exp = set(actual.keys()) - set(expected.keys())
    assert set(actual.keys()) == set(expected.keys()), \
        f"Key mismatch at {path}\nMissing in actual: {missing_in_act}\nMissing in expected: {missing_in_exp}"
            
    for key in expected:
        current_path = f"{path}['{key}']"

        # Recursively check nested dictionaries
        if isinstance(expected[key], dict):
            check_dicts(actual[key], expected[key], tolerance, current_path)

        # Check Quantity objects
        elif isinstance(expected[key], Quantity):
            # Check that actual is also a Quantity and has the same base unit
            assert isinstance(actual[key], Quantity), f"Expected Quantity, got {type(actual[key])} at {current_path}"
            assert actual[key].base_unit == expected[key].base_unit, \
                f"Unit mismatch at {current_path}: {actual[key].base_unit} != {expected[key].base_unit}"

            # Check that base_values are close (using numpy for arrays, pytest.approx for scalars)
            if isinstance(expected[key].base_value, np.ndarray):
                np.testing.assert_allclose(
                    actual[key].base_value, 
                    expected[key].base_value, 
                    atol=tolerance, 
                    err_msg=f"Array value mismatch at {current_path}"
                )
            else:
                assert actual[key].base_value == pytest.approx(expected[key].base_value, abs=tolerance), \
                    f"Value mismatch at {current_path}: {actual[key].base_value} != {expected[key].base_value}"

        # Check that strings are identical        
        elif isinstance(expected[key], str):
            assert actual[key] == expected[key], f"String mismatch at {current_path}: {actual[key]} != {expected[key]}"

        else:
            raise TypeError(f"Unsupported type in expected dict for key '{key}' at {current_path}: {type(expected[key])}")


def test_input_resolver():

    actual = input_resolver_function(input_dict, DummyDCF(), 'TestPlugin')         
    check_dicts(actual, input_dict_resolved)


if __name__ == "__main__":
    test_input_resolver()