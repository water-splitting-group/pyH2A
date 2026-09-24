import numpy as np

from pyH2A.run_pyH2A import pyH2A
from pyH2A.Utilities.Unit_Handler.quantity import Quantity

from tests.Utilities.check_dicts_for_testing import check_dicts


def test_plugin_IO():

    result = pyH2A('src/tests/end_to_end/Testing_Plugin_IO.md', 
                   'src/tests/end_to_end/')
        
    expected_input_x_sum_testing_dcf = {
        'Adsorber': {
              'Processed': 'Yes',
              'Sum Path': 'None',
              'Unit': 'EUR',
              'Value': Quantity(500, 'EUR')
              },
        'Compressor': {
                'Processed': 'Yes',
                'Sum Path': 'None',
                'Unit': 'USD',
                'Value': Quantity(100, 'USD')
                },
        'Summed Total': {
            'Processed': 'Yes', 
            'Value': Quantity(500.0, 'USD')
            }
        }
    
    expected_input_y_sum_testing_dcf = {
        'Pumps': {
           'Former Value': 0.3,
           'Processed': 'Yes',
           'Sum Path': '{Input X - Sum Testing > Compressor > Value, USD}',
           'Unit': 'USD',
           'Value': Quantity(30.0, 'USD')
           },
        'Reactor': {
            'Former Value': 0.2,
            'Processed': 'Yes',
            'Sum Path': '{Input X - Sum Testing > Summed Total > Value, USD}',
            'Unit': 'USD',
            'Value': Quantity(100.0, 'USD')},
        'Summed Total': {
            'Processed': 'Yes', 
            'Value': Quantity(130.0, 'USD')
            }
        }
    
    expected_input_sum_testing_dcf = {
        'Contributions': {
            'Processed': 'Yes',
            'Value': {
                'Data': {
                    'Input X - Sum Testing': Quantity(500.0, 'USD'),
                    'Input Y - Sum Testing': Quantity(130.0, 'USD'),
                    'Sum Testing': Quantity(100.0, 'USD')
                    },
                'Table Group': 'Sum Testing',
                'Total': Quantity(730.0, 'USD')
                }
            },
        'Other': {
            'Processed': 'Yes', 
            'Sum Path': 'None', 
            'Unit': 'USD', 
            'Value': Quantity(100.0, 'USD')
            },
        'Summed Group Total': {
            'Processed': 'Yes', 
            'Value': Quantity(730.0, 'USD')
            },
        'Summed Total': {
            'Processed': 'Yes', 
            'Value': Quantity(100.0, 'USD')
            }
        }

    expected_input_z_indirect_testing_dcf = {
        'Design': {
            'Former Value': 0.1,
            'Path': '{Sum Testing > Summed Group Total > Value, USD}',
            'Processed': 'Yes',
            'Unit': 'USD',
            'Value': Quantity(73.0, 'USD')
            },
        'Summed Total': {
            'Processed': 'Yes', 
            'Value': Quantity(73.0, 'USD')
            }
        }
    
    expected_input_indirect_testing_dcf = {
        'Contributions': {
            'Processed': 'Yes',
            'Value': {
                'Data': {
                    'Input Z - Indirect Testing': Quantity(73.0, 'USD')
                    },
                'Table Group': 'Indirect Testing',
                'Total': Quantity(73.0, 'USD')}},
        'Summed Group Total': {
            'Processed': 'Yes', 
            'Value': Quantity(73.0, 'USD')}}
    
    expected_individual_table_sum_dcf = {
        'Entry A': {
            'Path': 'None', 
            'Processed': 'Yes', 
            'Unit': 'USD', 
            'Value': Quantity(1.0, 'USD')
            },
        'Entry B': {
            'Path': 'None', 
            'Processed': 'Yes', 
            'Unit': 'USD',
            'Value': Quantity(2.0, 'USD')
            },
        'Summed Total': {
            'Processed': 'Yes', 
            'Value': Quantity(3.0, 'USD')
            }
        }
        
    expected_plugin_a_input_dcf = {
        'Power': {
            'Former Value': 10,
            'Path': '{Plugin A - Photovoltaic Input > Nominal Power > Value, kW}',
            'Processed': 'Yes',
            'Unit': 'kW',
            'Value': Quantity(82500.0, 'kW')
        }
    }

    expected_plugin_b_input_dcf = {
        'Mass': {
            'Comment': 'Value "2" is in unit kg/J, multiplying by "Plugin A Output > Energy > Value" (which is dimension energy, used in unit "J") gives kg, second path just for testing',
            'Former Value': 2,
            'Path': '{Plugin A Output > Energy > Value, J}; {Individual Table Sum > Entry A > Value, USD}',
            'Processed': 'Yes',
            'Unit': 'kg',
            'Value': Quantity(np.array([1.188e+13, 1.188e+13, 1.188e+13]), 'kg')
        },
        'Mass per energy': {
            'Comment': 'Retrieving two different paths, one nested, one not',
            'Former Value': '{Simple Unprocessed Input - read by Plugin B > Energy density > Value, kg/J}',
            'Path': '{Layer 2 Unprocessed Input > Layer 2 Test > Usage_Value, kg/J}',
            'Processed': 'Yes',
            'Unit': 'kg/J',
            'Value': Quantity(2, 'kg/J')
        }
    }

    expected_plugin_b_value_unit_pairs_dcf = {
        'Test Input': {
            'Cost_Unit': 'EUR',
            'Cost_Value': Quantity(2.5, 'EUR'),
            'Former Cost_Value': '{Individual Table Sum > Entry B > Value, EUR}',
            'Former Usage_Value': '{Plugin A Input > Power > Value, kW}',
            'Processed': 'Yes',
            'Usage_Path': '{Individual Table Sum > Entry A > Value, USD}',
            'Usage_Unit': 'kW',
            'Usage_Value': Quantity(82500000.0, 'W')}
    }

    expected_plugin_a_processed_input = {
        'Plugin A - Photovoltaic Input': {
            'Nominal Power': {
                'Value': Quantity(8250, 'kW'),
                },
            },
        'Indirect Testing': {
            'Contributions': {
                'Value': {
                    'Data': {
                        'Input Z - Indirect Testing': Quantity(73.0, 'USD')
                        },
                    'Table Group': 'Indirect Testing',
                    'Total': Quantity(73.0, 'USD')
                    }
                },
            'Summed Group Total': {
                'Value': Quantity(73.0, 'USD')
                }
            },
        'Individual Table Sum': {
            'Entry A': {
                'Value': Quantity(1.0, 'USD')
                },
            'Entry B': {
                'Value': Quantity(2.0, 'USD')
                },
            'Summed Total': {
                'Value': Quantity(3.0, 'USD')
                }
            },
        'Input X - Sum Testing': {
            'Adsorber': {
                'Value': Quantity(400.0, 'USD')
                },
            'Compressor': {
                'Value': Quantity(100.0, 'USD')
                },
            'Summed Total': {
                'Value': Quantity(500.0, 'USD')
                }
            },
        'Input Y - Sum Testing': {
            'Pumps': {
                'Value': Quantity(30.0, 'USD')
                },
            'Reactor': {
                'Value': Quantity(100.0, 'USD')
                },
            'Summed Total': {
                'Value': Quantity(130.0, 'USD')
                }
            },
        'Input Z - Indirect Testing': {
            'Design': {
                'Value': Quantity(73.0, 'USD')
                },
            'Summed Total': {
                'Value': Quantity(73.0, 'USD')
                }
            },
        'Plugin A Input': {
            'Power': {
                'Value': Quantity(82500000.0, 'W')
                }
            },
        'Sum Testing': {
            'Contributions': {
                'Value': {
                    'Data': {
                        'Input X - Sum Testing': Quantity(500.0, 'USD'),
                        'Input Y - Sum Testing': Quantity(130.0, 'USD'),
                        'Sum Testing': Quantity(100.0, 'USD')
                        },
                    'Table Group': 'Sum Testing',
                    'Total': Quantity(730.0, 'USD')
                    }
                },
            'Summed Group Total': {
                'Value': Quantity(730.0, 'USD')
                },
            'Other': {
                'Value': Quantity(100.0, 'USD')
                },
            'Summed Total': {
                'Value': Quantity(100.0, 'USD')
                },
            },
        'Absent Table Testing': {
            'Contributions': {
                'Value': {
                    'Data': {},
                    'Table Group': 'Absent Table Testing',
                    'Total': Quantity(0.0, 'kg')
                    }
                },
            'Summed Group Total': {
                'Value': Quantity(0.0, 'kg')
                }
            }, 
        }
 
    expected_plugin_b_processed_input = {
        'Plugin A Output': {
            'Energy': {
                'Value': Quantity(np.array([5.94e+12, 5.94e+12, 5.94e+12]), 
                              'J')
            }
        },
        'Plugin B Input': {
            'Mass': {
                'Value': Quantity(np.array([1.188e+13, 1.188e+13, 1.188e+13]), 'kg')
            },
            'Mass per energy': {
                'Value': Quantity(2, 'kg/J')
            },
        },
        'Plugin B - Value/Unit pairs': {
            'Test Input': {
                'Cost_Value': Quantity(2.5, 'EUR'),
                'Usage_Value': Quantity(82500000.0, 'W')
            }
        },
    }

    expected_plugin_a_output = {
        'Energy': {
            'Processed': 'Yes',
            'Value': Quantity(np.array([5.94e+12, 5.94e+12, 5.94e+12]), 
                              'J')
        }
    }

    expected_plugin_b_output = {
        'Energy density': {
            'Processed': 'Yes',
            'Value': Quantity(np.array([0.5, 0.5, 0.5]), 'J / kg')
        }
    }
    
    # Checking different sum tables inputs which go into plugin A
    check_dicts(result.base_case.inp['Input X - Sum Testing'], expected_input_x_sum_testing_dcf)
    check_dicts(result.base_case.inp['Input Y - Sum Testing'], expected_input_y_sum_testing_dcf)
    check_dicts(result.base_case.inp['Sum Testing'], expected_input_sum_testing_dcf)
    check_dicts(result.base_case.inp['Input Z - Indirect Testing'], expected_input_z_indirect_testing_dcf)
    check_dicts(result.base_case.inp['Indirect Testing'], expected_input_indirect_testing_dcf)
    check_dicts(result.base_case.inp['Individual Table Sum'], expected_individual_table_sum_dcf)

    # Checking non sum tables inputs into plugins A and B
    check_dicts(result.base_case.inp['Plugin A Input'], expected_plugin_a_input_dcf)
    check_dicts(result.base_case.inp['Plugin B Input'], expected_plugin_b_input_dcf)
    check_dicts(result.base_case.inp['Plugin B - Value/Unit pairs'], expected_plugin_b_value_unit_pairs_dcf)

    # Checking processed input dicts passed into plugins A and B
    check_dicts(result.base_case.plugs['Testing.Test_Plugin_A'].inp, expected_plugin_a_processed_input)
    check_dicts(result.base_case.plugs['Testing.Test_Plugin_B'].inp, expected_plugin_b_processed_input)

    # Checking outputs from plugins A and B
    check_dicts(result.base_case.inp['Plugin A Output'], expected_plugin_a_output)
    check_dicts(result.base_case.inp['Plugin B Output'], expected_plugin_b_output)
    
if __name__ == '__main__':
    test_plugin_IO()
