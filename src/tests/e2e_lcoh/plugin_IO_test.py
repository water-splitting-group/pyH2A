import numpy as np

from pyH2A.run_pyH2A import pyH2A
from pyH2A.Utilities.Unit_Handler.quantity import Quantity

from tests.Utilities.check_dicts_for_testing import check_dicts


def test_plugin_IO():

    result = pyH2A('src/tests/end_to_end/PV_E_Plugin_IO.md', 
                   'src/tests/end_to_end/')
        
    expected_input_x_sum_testing_dcf = {
        'Adsorber': {
              'Processed': 'Yes',
              'Sum Path': 'None',
              'Unit': 'EUR',
              'Value': 500
              },
        'Compressor': {
                'Processed': 'Yes',
                'Sum Path': 'None',
                'Unit': 'USD',
                'Value': 100
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
           'Sum Path': 'Input X - Sum Testing > Compressor > Value',
           'Unit': 'USD',
           'Value': 30.0
           },
        'Reactor': {
            'Former Value': 0.2,
            'Processed': 'Yes',
            'Sum Path': 'Input X - Sum Testing > Summed Total > Value',
            'Unit': 'USD',
            'Value': 100.0},
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
                    'Input X - Sum Testing': 500.0,
                    'Input Y - Sum Testing': 130.0,
                    'Sum Testing': 100.0
                    },
                'Table Group': 'Sum Testing',
                'Total': Quantity(730.0, 'USD')
                }
            },
        'Other': {
            'Processed': 'Yes', 
            'Sum Path': 'None', 
            'Unit': 'USD', 
            'Value': 100},
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
            'Path': 'Sum Testing > Summed Group Total > Value',
            'Processed': 'Yes',
            'Unit': 'USD',
            'Value': 73.0
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
                    'Input Z - Indirect Testing': 73.0
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
            'Value': 1},
        'Entry B': {
            'Path': 'None', 
            'Processed': 'Yes', 
            'Unit': 'USD',
            'Value': 2},
        'Summed Total': {
            'Processed': 'Yes', 
            'Value': Quantity(3.0, 'USD')
            }
        }
        
    expected_plugin_a_input_dcf = {
        'Power': {
            'Former Value': 10,
            'Path': 'Photovoltaic > Nominal Power (kW) > Value',
            'Processed': 'Yes',
            'Unit': 'kW',
            'Value': 82500.0
        }
    }

    expected_plugin_a_processed_input = {
        'Indirect Testing': {
            'Contributions': {
                'Value': {
                    'Data': {
                        'Input Z - Indirect Testing': 73.0
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
                        'Input X - Sum Testing': 500.0,
                        'Input Y - Sum Testing': 130.0,
                        'Sum Testing': 100.0
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
            }
        }

    expected_plugin_a_output = {
        'Energy': {
            'Processed': 'Yes',
            'Value': Quantity(np.array([5.94e+12, 5.94e+12, 5.94e+12]), 'J')
        }
    }

    expected_plugin_b_input_dcf = {
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
    
    check_dicts(result.base_case.inp['Input X - Sum Testing'], expected_input_x_sum_testing_dcf)
    check_dicts(result.base_case.inp['Input Y - Sum Testing'], expected_input_y_sum_testing_dcf)
    check_dicts(result.base_case.inp['Sum Testing'], expected_input_sum_testing_dcf)
    check_dicts(result.base_case.inp['Input Z - Indirect Testing'], expected_input_z_indirect_testing_dcf)
    check_dicts(result.base_case.inp['Indirect Testing'], expected_input_indirect_testing_dcf)
    check_dicts(result.base_case.inp['Individual Table Sum'], expected_individual_table_sum_dcf)

    check_dicts(result.base_case.plugs['Test_Plugin_A'].inp, expected_plugin_a_processed_input)

    check_dicts(result.base_case.inp['Plugin A Input'], expected_plugin_a_input_dcf)
    check_dicts(result.base_case.inp['Plugin A Output'], expected_plugin_a_output)
    check_dicts(result.base_case.inp['Plugin B Input'], expected_plugin_b_input_dcf)
    check_dicts(result.base_case.inp['Plugin B Output'], expected_plugin_b_output)
    
if __name__ == '__main__':
    test_plugin_IO()
