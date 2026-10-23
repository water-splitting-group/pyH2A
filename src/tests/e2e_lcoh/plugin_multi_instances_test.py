from pyH2A.run_pyH2A import pyH2A
from pyH2A.Utilities.Unit_Handler.quantity import Quantity

from tests.Utilities.check_dicts_for_testing import check_dicts


def test_plugin_multi_instances():

    result = pyH2A('src/tests/end_to_end/Testing_Plugin_multi_instances.md', 
                   'src/tests/end_to_end/')
        
    expected_tables_names = {'Hourly Irradiation', 'Hourly Irradiation @ Baggie', 'Hourly Irradiation @ PV', 'Irradiance Area Parameters @ Baggie', 'Irradiance Area Parameters @ PV'}
    expected_file_name = 'pyH2A.Lookup_Tables.Hourly_Irradiation_Data~tmy_34.859_-116.889_2006_2015.csv'
    expected_hourly_irradiation = {
        # Inputs in the md file
        'Irradiance Area Parameters @ Baggie': {
            'Array azimuth':{ 
                'Processed': 'Yes',                
                'Value' : Quantity(0, 'deg'), 
                'Unit': 'deg'
            },                                   
        },
        'Irradiance Area Parameters @ PV': {
            'Array azimuth':{ 
                'Processed': 'Yes',                
                'Value' : Quantity(180, 'deg'),
                'Unit': 'deg'
            },                           
        }, 
        # Calculated results
        'Hourly Irradiation @ Baggie': {
            'Mean solar input no tracking':{ 
                'Processed': 'Yes',                
                'Value' : Quantity(231.52718269392295, 'W/m2')
            },     
            'Mean solar input single axis tracking':{ 
                'Processed': 'Yes',                
                'Value' : Quantity(309.9684158257135, 'W/m2')
            },   
            'Mean solar input two axis tracking':{ 
                'Processed': 'Yes',                
                'Value' : Quantity(308.52931239315075, 'W/m2')
            },                                  
        },
        'Hourly Irradiation @ PV': {
            'Mean solar input no tracking':{ 
                'Processed': 'Yes',                
                'Value' : Quantity(229.1345051339019, 'W/m2')
            },    
            'Mean solar input single axis tracking':{ 
                'Processed': 'Yes',                
                'Value' : Quantity(284.5886316476537, 'W/m2')
            },   
            'Mean solar input two axis tracking':{ 
                'Processed': 'Yes',                
                'Value' : Quantity(283.40436929914176, 'W/m2')
            },                            
        },        
    }

    # Checking that the tables found in the input dict match the expected names
    assert expected_tables_names.issubset(result.base_case.inp)

    # Checking that the HOurly irradiation table captures the name of the file
    assert result.base_case.inp['Hourly Irradiation']['File']['Value'] == expected_file_name

    # Checking that the elements found in the expected dicts are found at the corresponding places in dcf.inp. We don't chaeck the entire dict as such because it would imply to write here expected values for each hour of the year.
    for upper_key, inner_dict in expected_hourly_irradiation.items():
        for mid_key, expected_value in inner_dict.items():
            check_dicts(result.base_case.inp[upper_key][mid_key], expected_value)

    
if __name__ == '__main__':
    test_plugin_multi_instances()
