from pyH2A.Utilities.IO import input_resolver_function
from tests.Utilities.Input_resolver.input_resolver_test_data import DummyDCF, input_dict, input_dict_resolved
from tests.Utilities.check_dicts_for_testing import check_dicts


def test_input_resolver():

    actual = input_resolver_function(input_dict, DummyDCF(), 'TestPlugin')
    check_dicts(actual, input_dict_resolved)


if __name__ == "__main__":
    test_input_resolver()
