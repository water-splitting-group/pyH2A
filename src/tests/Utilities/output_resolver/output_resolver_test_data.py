import numpy as np
from pint import UnitRegistry, Quantity
import pytest

ureg = UnitRegistry()
ureg.define('USD = [currency]')


class DummyDCF:
    def __init__(self):
        # Initial state of the dict, before any insert or update: some keys of various levels already exist, we want to check if the output resolver updates / adds values correctly  
        self.inp = {
            'Utilities': {
                'Natural gas': {
                    'Usage_Value': 1500,
                    'Usage_Unit': 'kWh/kg',
                    'Cost_Value': 200,
                    'Cost_Unit': 'USD/kWh',
                    'Type': 'natural_gas', 
                    'Processed': 'Yes'
                }
            },                       
            'Power Generation': {
                'Available Energy (daily)': {
                    'Value': {
                        '2025':np.array([400., 250., 350.]), 
                        '2024':np.array([500., 350., 450.])
                    }, 
                    'Unit': 'kWh', 
                    'Processed': 'Yes'
                },
            }, 
            'Dummy left Direct Capital Cost dummy right': {
                'First cost': {
                    'Value': 750.0,
                    'Unit': 'USD', 
                    'Processed': 'Yes'
                },
                'Second cost': {
                    'Value': 250.0,
                    'Unit': 'USD', 
                    'Processed': 'Yes'
                },                
            }, 
            'Planned Replacement': {
                'Electrolyzer Stack Replacement': {
                    'Cost_Value': 0.4,
                    'Cost_Unit': 'USD',                     
                    'Path': 'Direct Capital Costs - Electrolyzer > Electrolyzer CAPEX ($/kW) > Value', 
                    'Comment': 'Based on Chang 2020'
                },               
            }, 
        }

# quantities to insert : these would be the quantities calculated by the plugin
# that is: the self.XXX variables (that would now be pint quantities)
# written here under the form of a dict for convenience
# i.e. we write here directly the dict location where the value would go to ease testing, but in the plugin these would be self.XXX quantities, not dict items
values_to_insert = {
    'Power Generation':{
        'Stored Energy (daily)':{ # new middle key to insert
            'Value': {
                np.int64(0): ureg.Quantity(np.array([0, 0, 938736, 0, 1008000]), 'J'),
                np.int64(1): ureg.Quantity(np.array([0, 0, 933840, 0, 1005480]), 'J'), 
            }
        }, 
        'Available Energy (daily)':{ # overwrite existing value
            'Value': {
                '2025':ureg.Quantity(np.array([5.4e8, 3.6e8, 7.2e8]), 'J'), 
                '2024':ureg.Quantity(np.array([1.26e9, 7.2e8, 1.08e9]), 'J') 
            }
        },         
    },

    'Dummy left Direct Capital Cost dummy right':{
        'Summed Total':{
            'Value': ureg.Quantity(1000.0, 'USD')
        }, 
    }, 

    'Direct Capital Costs':{
        'Inflated':{
            'Value': ureg.Quantity(2000.0, 'USD')
        }, 
    }, 

    'Technical Operating Parameters and Specifications':{
        'Plant daily design flowrate':{
            'Value': ureg.Quantity(np.array([0., 955.95413492, 952.47095234, 948.98391499]), 'kg/day')
        }, 
        'Scaling Ratio':{
            'Value': ureg.Quantity(1.0, 'dimensionless')
        },         
    }, 

    'Power Consumption':{
        'Reverse Osmosis Consumption (yearly)':{
            'Value': ureg.Quantity(np.array([1.3e9, 1.e9]), 'J'), 
            'Type': 'flexible'
        }, 
    }, 

    'Reactor Baggies':{
        'Number':{
            'Value': ureg.Quantity(5, 'dimensionless'), 
        }, 
    },    

    'Planned Replacement':{
        'Planned Replacement Baggie':{
            'Cost': ureg.Quantity(1000, 'USD'), 
            'Frequency': ureg.Quantity(2, 'year'), 
        }, 
        'Electrolyzer Stack Replacement':{
            'Frequency': ureg.Quantity(10, 'year'), 
        },         
    },   

}

# Output schema (output equivalent to input_dict)
output_dict = {
    'Power Generation': {
        'Stored Energy (daily)': {
            'Value': {
                'type': {dict},
            },
            'Unit': 'J', # I didn't keep a 'dimension' subkey here, I think there's no need to validate the dimension on the output side. 
                         # Actually I'm not even sure we need to keep the unit here, since it is included in the calculated pint quantity already
            'optional': False,
            'description': 'Electricity stored in battery daily (dictionary of years)'
        }, 
        'Available Energy (daily)': {
            'Value': {
                'type': {dict},
            },
            'Unit': 'J', 
            'optional': False,
            'description': 'Available Electricity, daily basis, dictionary of years - energy which has not been stored in battery'
        }        
    }, 
  
    '<...> Direct Capital Cost <...>': {
        'Summed Total': {
            'Value': {
                'type': {float},
            },
            'Unit': 'USD', 
            'optional': False,
            'description': 'Summed total for each individual table in "Direct Capital Cost" group.'
        }
    }, 

    'Direct Capital Costs': {
        'Inflated': {
            'Value': {
                'type': {float},
            },
            'Unit': 'USD', 
            'optional': False,
            'description': 'Total direct capital costs multiplied by combined inflator.'
        }
    },    

    'Technical Operating Parameters and Specifications': { 
        'Plant Design Capacity (Daily)': {# I renamed the existing Plant Design Capacity (kg of H2/day)
            'Value': {
                'type': {float, np.ndarray},
            },
            'Unit': 'kg', 
            'optional': False,
            'description': 'Plant design capacity expressed as a daily flowrate, calculated from installed electrolysis power capacity and hourly power generation data.'
        },
        'Scaling Ratio': {
            'Value': {
                'type': {float},
            },
            'Unit': 'dimensionless', 
            'optional': True,
            'description': 'Returned if New Plant Design Capacity was specified.'
        }        
    },  

    'Scaling': { # this one is optional, and we actually don't insert any value (check the ability of the output resolver to handle an optional value that is absent)
        'Capital Scaling Factor': {
            'Value': {
                'type': {float},
            },
            'Unit': 'dimensionless', 
            'optional': True,
            'description': 'Returned if scaling is active (`Scaling Ratio` or `New Plant Design Capacity (kg of H2/day)` specified).'
        }
    },

    'Power Consumption': {
        'Reverse Osmosis Consumption (yearly)': {
            'Value': {
                'type': {np.ndarray},
            },
            'Unit': 'J', 
            'Type': {
                'type': str,
                'options': {'flexible', 'on demand'} 
            },
            'optional': False,
            'description': ' Electricity demand of reverse osmosis plant per year.'
        }
    },

    'Reactor Baggies': {
        'Number': {
            'Value': {
                'type': {int},
            },
            'Unit': 'dimensionless', 
            'optional': False,
            'description': ' Number of ports per baggie.'
        }
    },    

    'Planned Replacement': {
        'Planned Replacement Baggie': {
            'Cost_Value': {
                'type': {float},
            },
            'Cost_Unit': 'USD',
            'Frequency_Value': {
                'type': {float},
            },
            'Frequency_Unit': 'year', # keeping years here, it seems more coherent              
            'optional': False,
            'description': ' Replacement frequency and cost of baggies', 
        }, 
        'Electrolyzer Stack Replacement': {
            'Frequency_Value': {
                'type': {float},
            },
            'Frequency_Unit': 'year', # keeping years here, it seems more coherent              
            'optional': False, 
            'description': 'Frequency of electrolyzer stack replacements, calculated from replacement time and hourly irradiation data', 
            'add_processed' = False,  # when add_processed and insert_path are different from the default value, the output resolver must read it from output_dict to inform the 'insert' method accordingly
            'insert_path' = False
        },            
    },       
}


# Expected final state, that is: what dcf.inp would look like after insertions
resolved_dict_expected = {
    # Values that were initially present, and have not been modified : they must still be there at the end
    'Utilities': {
        'Natural gas': {
            'Usage_Value': 1500,
            'Usage_Unit': 'kWh/kg',
            'Cost_Value': 200,
            'Cost_Unit': 'USD/kWh',
            'Type': 'natural_gas', 
            'Processed': 'Yes'
        }
    },        
    'Dummy left Direct Capital Cost dummy right': {
        'First cost': {
            'Value': 750.0,
            'Unit': 'USD', 
            'Processed': 'Yes'
        },
        'Second cost': {
            'Value': 250.0,
            'Unit': 'USD', 
            'Processed': 'Yes'
        },                
        'Summed Total': { # new mid key
            'Value': 1000.0, 
            'Unit': 'USD', 
            'Processed': 'Yes'            
        }        
    }, 
    
    'Power Generation': { # upper key existed already
        'Available Energy (daily)': { # Value that was initially present, and has been modified
            'Value': {
                '2025':np.array([5.4e8, 3.6e8, 7.2e8]), 
                '2024':np.array([1.26e9, 7.2e8, 1.08e9]) 
            }, 
            'Unit': 'J', 
            'Processed': 'Yes'            
        }, 
        'Stored Energy (daily)': { # Value that has been inserted
            'Value': {
                np.int64(0): np.array([0, 0, 938736, 0, 1008000]), 
                np.int64(1): np.array([0, 0, 933840, 0, 1005480]), 
            }, 
            'Unit': 'J', 
            'Processed': 'Yes'            
        }        
    }, 

    'Direct Capital Costs': { # upper key didn't exist in the initial dictionary
        'Inflated': {
            'Value': 2000.0, 
            'Unit': 'USD', 
            'Processed': 'Yes'            
        }
    }, 

    'Technical Operating Parameters and Specifications': { 
        'Plant Design Capacity (Daily)': {
            'Value': np.array([0., 955.95413492, 952.47095234, 948.98391499]), 
            'Unit': 'kg', 
            'Processed': 'Yes'            
        },
        'Scaling Ratio': { # inserted optional value
            'Value': 1.0, 
            'Unit': 'dimensionless',  
            'Processed': 'Yes'
        }        
    }, 

    'Power Consumption': {
        'Reverse Osmosis Consumption (yearly)': {
            'Value': np.array([1.3e9, 1.e9]),
            'Unit': 'J',
            'Type': 'flexible', 
            'Processed': 'Yes'
        }
    },       

    'Reactor Baggies': {
        'Number': {
            'Value': 5,
            'Unit': 'dimensionless',
            'Processed': 'Yes'
        }
    },   

    'Planned Replacement': {
        'Planned Replacement Baggie': {
            'Cost_Value': 1000,
            'Cost_Unit': 'USD',
            'Frequency_Value': 2,
            'Frequency_Unit': 'year',
            'Processed': 'Yes'
        }, 
        'Electrolyzer Stack Replacement': {
            'Cost_Value': 0.4,
            'Cost_Unit': 'USD',             
            'Path': 'Direct Capital Costs - Electrolyzer > Electrolyzer CAPEX ($/kW) > Value', 
            'Comment': 'Based on Chang 2020',
            'Frequency_Value': np.float64(10.0),
            'Frequency_Unit': 'year'
        },          
    },   

}


class TestOutputResolver:

    ABS_TOL = 1e-9

    def _assert_resolved_equal(self, actual, expected) -> None:
        if isinstance(expected, dict):
            actual_key_map = {str(key).casefold(): key for key in actual}
            expected_key_map = {str(key).casefold(): key for key in expected}
            assert set(actual_key_map.keys()) == set(expected_key_map.keys())

            for normalized_key, expected_key in expected_key_map.items():
                actual_key = actual_key_map[normalized_key]
                self._assert_resolved_equal(
                    actual[actual_key], expected[expected_key]
                )
            return

        elif isinstance(expected, np.ndarray):
            assert isinstance(actual, np.ndarray)
            assert np.allclose(actual, expected, atol=self.ABS_TOL)
            return

        elif isinstance(expected, float):
            assert actual == pytest.approx(expected, abs=self.ABS_TOL)
            return

        else:
            assert actual == expected
            return

    def _apply_values(self, dcf):
        """Simulate plugin behavior: we would manually specify, in the output_resolver call, in which dict location (keys) to insert a self.XXX value"""
        for top_key, mid_dict in values_to_insert.items():
            for mid_key, leaf_dict in mid_dict.items():
                for leaf_key, value_to_insert in leaf_dict.items():
                    output_resolver(
                        dcf,
                        top_key,
                        mid_key,
                        leaf_key,
                        value_to_insert,
                        output_dict
                    )

    def test_output_resolver(self):
        dcf = DummyDCF()

        # apply all insertions one by one
        self._apply_values(dcf)

        # check final state
        self._assert_resolved_equal(dcf.inp, resolved_dict_expected)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])