import numpy as np
from pint import UnitRegistry, Quantity
import pytest
import unittest
from pyH2A.Utilities.input_modification output_resolver

ureg = UnitRegistry()
ureg.define('USD = [currency]')

# Output schema (output equivalent to input_dict)
output_dict = { 
    'Power Generation': {
        'Stored Energy (daily)': { # new middle key to insert
            'Value': 'self.yearly_recovered_power',
            'add_processed' : True,  # This is the default so shouldn't be needed anyway, but it doesn't harm to test the explicit specification of it
            'insert_path' : True,            
            'description': 'Electricity stored in battery daily (dictionary of years)',
            'optional': False,            
        }, 
        'Available Energy (daily)': { # overwrite existing value
            # From now on, I don't add 'add_processed' and 'insert_path' when they are true, it's the default so normally it'S unnecessary
            'Value': 'self.yearly_unstored_power', 
            'description': 'Available Electricity, daily basis, dictionary of years - energy which has not been stored in battery',
            'optional': False,            
        }        
    }, 

    '<...> Direct Capital Cost <...>': { # actually I'm confused about this one, the docstring says we insert [...] Direct Capital Cost [...] > Summed Total > Value, but I don't find such an insert. So I use it here for the test as an example anyway but in the capital cost plugin we might need to clarify it
        'Summed Total': {
            'Value': 'self.total',
            'description': 'Summed total for each individual table in "Direct Capital Cost" group.', 
            'optional': False,
        }
    }, 

    'Direct Capital Costs': {
        'Inflated': {
            'Value': 'self.direct_inflated', # this one is not normally a self.XXX, but if we don't turn it into a self.XXX I suspect it won't work
            'description': 'Total direct capital costs multiplied by combined inflator.', 
            'optional': False,            
        }
    },    

    'Technical Operating Parameters and Specifications': { 
        'Plant design flowrate': {# I renamed the existing Plant Design Capacity (kg of H2/day)
            'Value': 'self.h2_production', #originally there's a division by 365 that iswill require update in the plugin
            'description': 'Plant design capacity expressed as a daily flowrate, calculated from installed electrolysis power capacity and hourly power generation data.', 
            'optional': False,
        },
        'Scaling Ratio': { # optional
            'Value': 'self.scaling_ratio', # isn't normally a "self"
            'description': 'Returned if New Plant Design Capacity was specified.', 
            'optional': True,            
        }        
    },  

    'Scaling': { # this one is optional, and we actually don't insert any value (to check the ability of the output resolver to handle an optional value that is absent)
        'Capital Scaling Factor': {
            'Value': 'self.capital_scaling_factor',
            'description': 'Returned if scaling is active (`Scaling Ratio` or `New Plant Design Capacity (kg of H2/day)` specified).', 
            'optional': True,            
        }
    },

    'Power Consumption': {
        'Reverse Osmosis Consumption (yearly)': {
            'Value': 'self.electricity_demand',
            'Type': 'flexible', # no need to have the intermediate "options" key anymore: in the same way as we define here the inserted variables, we define directly the Type
            'description': ' Electricity demand of reverse osmosis plant per year.',      
            'optional': False,                   
        }
    },

    'Reactor Baggies': {
        'Number': {
            'Value': 'self.baggie_number',
            'description': 'Number of individual baggies required for design H2 production capacity', 
            'optional': False,            
        }
    },    

    'Planned Replacement': {
        'Planned Replacement Baggie': {
            'Cost_Value': 'self.baggies_cost',
            'Frequency_Value': 'self.baggie_frequency',
            'description': ' Replacement frequency and cost of baggies',             
            'optional': False,                
        }, 
        'Planned Replacement Catalyst': {
            'Frequency_Value': 'self.input_dict_resolved["Catalyst"]["Lifetime"]["Value"]', # interesting because in the existing version we insert something that should already be in the dictionary ('dcf.inp['Catalyst']['Lifetime']['Value']'), not a variable that results from a calculation
                                                                                # rather than picking up the value from dcf.inp (as we currently do), it's better to now pick it up from the resolved dict so we know already it's "clean"        
            'description': 'Replacement frequency of catalyst in years, identical to catalyst lifetime.', 
            'optional': False,             
        },           
        'Electrolyzer Stack Replacement': {
            'Frequency_Value': 'self.replacement_frequency',
            'description': 'Frequency of electrolyzer stack replacements, calculated from replacement time and hourly irradiation data', 
            'optional': False,             
            'add_processed' : False,  # when add_processed and insert_path are different from the default value, the output resolver must read it from output_dict to inform the 'insert' method accordingly
            'insert_path' : False
        },            
    },       
}

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
            'Catalyst': {
                'Lifetime': {
                    'Value': 0.5,
                    'Unit': 'year', 
                },
            }
        }


# we need a dummy plugin to contain the variables to insert
class DummyPlugin:

    def __init__(self, dcf, print_info):
        self.input_dict_resolved = { # sometimes we need to pick up some values from the resolved dict that exists in the plugin, that is created after the input_resolver calls
            'Catalyst': {
                'Lifetime': {
                    'Value': ureg.Quantity(1.57788E8, 's')
                }
            }
        }        
        self.yearly_recovered_power = {
            np.int64(0): ureg.Quantity(np.array([0, 0, 938736, 0, 1008000]), 'J'),
            np.int64(1): ureg.Quantity(np.array([0, 0, 933840, 0, 1005480]), 'J'),
        }

        self.yearly_unstored_power = {
            '2025': ureg.Quantity(np.array([5.4e8, 3.6e8, 7.2e8]), 'J'),
            '2024': ureg.Quantity(np.array([1.26e9, 7.2e8, 1.08e9]), 'J'),
        }

        self.total = ureg.Quantity(1000.0, 'USD')

        self.h2_production = ureg.Quantity(np.array([0., 955.95413492, 952.47095234, 948.98391499]), 'kg/day')

        self.electricity_demand = ureg.Quantity(np.array([1.3e9, 1.e9]), 'J')

        self.baggie_number = ureg.Quantity(5, 'dimensionless')

        self.baggies_cost = ureg.Quantity(1000, 'USD')

        self.baggie_frequency = ureg.Quantity(5, 'year')

        self.replacement_frequency = ureg.Quantity(10, 'year')

        # the next two ones are not normally self.XXX, but as mentioned earlier I think we need to convert them into self.XXX for the output resolver to work 
        self.direct_inflated = ureg.Quantity(2000.0, 'USD')

        self.scaling_ratio = ureg.Quantity(1.0, 'dimensionless')

        output_resolver(dcf.inp, self, output_dict) # we want to call the output_resolver once only



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
            'Value': ureg.Quantity(1000.0, 'USD'), 
            # when we insert a pint quantity, there's no need to insert a 'unit' bottom key
            'Processed': 'Yes'            
        }        
    }, 
    
    'Power Generation': { # upper key existed already
        'Available Energy (daily)': { # Value that was initially present, and has been modified
            'Value': {
                '2025':ureg.Quantity(np.array([5.4e8, 3.6e8, 7.2e8]), 'J'), 
                '2024':ureg.Quantity(np.array([1.26e9, 7.2e8, 1.08e9]), 'J') 
            }, 
            # when we discussed we said we would ignore the 'Unit' if the 'Value' is a pint ; 
            # I would advise further that when we update a value with a pint quantity, it would be good to remove the existing 'Unit' bottom key from the dict to prevent any issue and unnecessary/wrong item (I hope it should not be too complicated too implement) 
            'Processed': 'Yes'            
        }, 
        'Stored Energy (daily)': { # Value that has been inserted
            'Value': {
                np.int64(0): ureg.Quantity(np.array([0, 0, 938736, 0, 1008000]), 'J'), 
                np.int64(1): ureg.Quantity(np.array([0, 0, 933840, 0, 1005480]), 'J'), 
            }, 
            'Processed': 'Yes'            
        }        
    }, 

    'Direct Capital Costs': { # upper key didn't exist in the initial dictionary
        'Inflated': {
            'Value': ureg.Quantity(2000.0, 'USD'), 
            'Processed': 'Yes'            
        }
    }, 

    'Technical Operating Parameters and Specifications': { 
        'Plant design flowrate': {
            'Value': ureg.Quantity(np.array([0., 955.95413492, 952.47095234, 948.98391499]), 'kg/day'), 
            'Processed': 'Yes'            
        },
        'Scaling Ratio': { # inserted optional value
            'Value': ureg.Quantity(1.0, 'dimensionless'),
            'Processed': 'Yes'
        }        
    }, 

    'Power Consumption': {
        'Reverse Osmosis Consumption (yearly)': {
            'Value': ureg.Quantity(np.array([1.3e9, 1.e9]), 'J'),
            'Type': 'flexible', 
            'Processed': 'Yes'
        }
    },       

    'Reactor Baggies': {
        'Number': {
            'Value': ureg.Quantity(5, 'dimensionless'),
            'Processed': 'Yes'
        }
    },   

    'Planned Replacement': {
        'Planned Replacement Baggie': {
            'Cost_Value': ureg.Quantity(1000, 'USD'),
            'Frequency_Value': ureg.Quantity(5, 'year'),
            'Processed': 'Yes'
        }, 
        'Planned Replacement Catalyst': {
            'Frequency_Value': ureg.Quantity(1.57788E8, 's'),
            'Processed': 'Yes'
        },
        'Electrolyzer Stack Replacement': {
            'Cost_Value': 0.4,
            'Cost_Unit': 'USD',  
            'Path': 'Direct Capital Costs - Electrolyzer > Electrolyzer CAPEX ($/kW) > Value', # insert_part is False so the path stays as is
            'Comment': 'Based on Chang 2020',
            'Frequency_Value': ureg.Quantity(10, 'year'),
        },          
    }, 
    'Catalyst': {
        'Lifetime': {
            'Value': 0.5,
            'Unit': 'year', 
        },      

    }
}



class TestDummyPlugin(unittest.TestCase):
    ABS_TOL = 1e-12

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

        elif hasattr(expected, 'units') and hasattr(actual, 'units'):
            # Compare pint quantities
            assert abs(actual.magnitude - expected.magnitude) < self.ABS_TOL
            assert str(actual.units) == str(expected.units)
            return

        else:
            assert actual == expected
            return

    def test_plugin_resolves_dict_correctly(self):
        # Create dummy DCF
        dcf = DummyDCF()
        
        # Run the plugin
        plugin = DummyPlugin(dcf, print_info=False)
        
        # Compare the final dict
        self._assert_resolved_equal(dcf.inp, resolved_dict_expected)


# Run the test
if __name__ == "__main__":
    unittest.main(argv=[''], exit=False)