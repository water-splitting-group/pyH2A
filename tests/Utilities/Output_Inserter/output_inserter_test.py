from pyH2A.Utilities.IO import output_inserter_function

from tests.Utilities.Output_Inserter.output_inserter_test_data import DummyDCF, DummyPlugin, output_dict, DummyDCF_after_insertion
from tests.Utilities.check_dicts_for_testing import check_dicts
import pprint as pp

def test_output_inserter():

    DummyDCF_instance = DummyDCF()
    DummyPlugin_instance = DummyPlugin(DummyDCF_instance, print_info = False)

    output_inserter_function(output_dict, 
                             DummyPlugin_instance, 
                             DummyDCF_instance, 
                             'Test_Plugin')
    
    expected = DummyDCF_after_insertion()

    check_dicts(DummyDCF_instance.inp, expected.inp)

if __name__ == "__main__":
    test_output_inserter()

