import pytest
import numpy as np
from pyH2A.Utilities.Unit_Handler.quantity import Quantity


class DummyDCF:
    def __init__(self):  
        self.inp = {
            'Utilities': {
                'Natural gas': {
                    'Usage_Value': 1500,
                    'Usage_Unit': 'kWh/kg',
                    'Cost_Value': 200,
                    'Cost_Unit': 'USD/kWh',
                    'Type': 'natural_gas',
                    'Comment': 'Usage of natural gas'
                },
                'Electricity': {
                    'Usage_Value': 3000,
                    'Usage_Unit': 'kWh/kg',
                    'Cost_Value': 500,
                    'Cost_Unit': 'USD/kWh',
                    'Type': 'electricity'
                },
                'Water': {
                    'Usage_Value': 2,
                    'Usage_Unit': 'J/kg',
                    'Usage_Path': 'Number of units > Bag number > Value', # testing that path information is correctly passed and used
                    'Cost_Value': 'Pump - Other Variable Operating Cost - Brand A > Maintenance > Value', # testing that path information is correctly passed and used
                    'Cost_Unit': 'USD/J',
                    'Cost_Path': 'Number of units > Bag number > Value', # testing that path information is correctly passed and used
                    'Type': 'water'
                }
            },        
            
            'Water Supply': {
                'Volume': {
                    'Value': 50, 
                    'Unit': 'liters', 
                    'Type': 'flexible'
                }, 
                'Purity': {
                    'Value': 0.99, 
                    'Unit': '-', 
                    'Type': 'contaminants'
                }                
            },  
            
            'Number of units': {
                'Bag number': {
                    'Value': 50, 
                    'Unit': '-',
                    'Processed': True,
                }
            },  
            
            'Catalyst': {
                'Lifetime': {
                    'Value': 5, 
                    'Unit': 'year'
                }
            } ,
            
            'Catalyst Separation': {
                'Filtration cost': {
                    'Value': 100, 
                    'Unit': 'USD/m3'
                }
            },
            
            'Grid Electricity': {
                'Cost': {
                    'Value': 0.15, 
                    'Unit': 'USD/kWh'
                }
            },

            'Power Generation': {
                'Available Power': {
                    'Value': {
                        '2025':Quantity(np.array([400.*3600, 250.*3600, 350.*3600]), 'kJ'), '2024':np.array([500., 350., 450.])
                    }, 
                    'Unit': 'kWh',                    
                    'Processed': True
                },
                'Stored Power': {
                    'Value': {
                        '2025': 200., '2024': 250.
                    }, 
                    'Unit': 'kWh',
                    'Processed': True,
                    }
                },
                
            # the following one serves to test the situation where middle key isn't known in advance / when we want to iterate
            'Power Consumption': {
                'Any mid key': {
                    'Value': np.array([100., 120., 110.]),
                    'Type': 'on demand',
                    'Unit': 'kWh',
                    'Processed': True
                },
                'Another mid key': {
                    'Value': np.array([50., 40., 60.]), 
                    'Type': 'flexible',
                    'Unit': 'kWh',
                    'Processed': True
                },
            }, 
            
            # Pump and compressor: to test the "Other Variable Operating Cost" group
            'Pump - Other Variable Operating Cost - Brand A': {
                'Maintenance': {
                    'Value': 12.5, 
                    'Unit': 'USD',
                    'Processed': True,
                },
                'lubrication':  {
                    'Value': 8.2, 
                    'Unit': 'USD'
                }
            },
            
            'Compressor - Other Variable Operating Cost - Brand B': {
                'Lubrication': {
                    'Value': np.array([1.3, 1.2, 1.1]),
                    'Unit': 'USD',
                    'Processed': True
                },
                'Electricity': {
                    'Value': 2.2, 
                    'Unit': 'USD'
                }                
            },

            'Bag - Other Variable Operating Cost': {
                'Replacement': {
                    'Value': 'Number of units > Bag number > Value', 
                    'Unit': 'USD'
                },
                'Disposal': {
                    'Value': 10,
                    'Unit': 'USD',
                    'Path': 'Number of units > Bag number > Value' # testing that path information is correctly passed and used
                },
                'Recycling': {
                    'Value': 10,
                    'Unit': 'USD',
                    'Path': 'Number of units > Bag number > Value; Catalyst > Lifetime > Value' # testing that multiple path information is correctly passed and used
                }                     
            },

            'Electrolyzer - this input is not used': {
                'Cost': {
                    'Value': 1000, 
                    'Unit': 'USD'
                }
            },

            'Turbopump': {
                'Electricity':{
                    'Value': 500, 
                    'Unit': 'USD',
                },
            },

            'Irradiation Used': {
                'Data': {
                    'Value': 'Path/to/file.txt',
                    'Unit': 'J/m2'
                },
                'Other Data': {
                    'Value': np.array([1., 2., 3.]),
                    'Unit': 'J/m2',
                    'Processed': True,
                },
                'Only String': {
                    'Value': 'Just a string',
                },
                'Quantity object': {
                    'Value': Quantity(np.array([1., 2., 3.]), 'J/m2'),
                    'Processed': True,
                }
            },

            'Quantity Path Testing': {
                'Electrolyzer power': { 
                    'Value': Quantity(100, 'kW'),
                    'Processed': True,
                },
                'PV power': {
                    'Value': 1.5,
                    'Path': 'Quantity Path Testing > Electrolyzer power > Value', # testing that path information is correctly passed and used for Quantity objects
                    'Unit': 'W',
                }
            }
    }

input_dict = {
    'Utilities':{
        '<...>':{
            'Usage_Value': {
                    'type': {float, int},
                    'bounds': (0, None),
                    'path': 'Usage_Path',
            },
            'Usage_Unit': {
                    'dimension': 'energy / mass'
            },
            'Cost_Value': {
                    'type': {float, int},
                    'bounds': (0, None),
                    'path': 'Cost_Path',
            },
            'Cost_Unit': {
                    'dimension': 'currency / energy'
            },
            'Type': {
                    'type': str,
                    'options': {
                        'electricity', 'natural_gas', 'water'
                    },
            },
            'optional': True,
            'description': 'The utility usage and cost details.'
        },
    },
    'Water Supply':{
        'Volume':{
            'Value': {
                    'type': {float, int},
                    'bounds': (0, None),
            },
            'Unit': {
                'dimension': 'volume'
            },    
            'Type': {
                'type': str,
                'options': {'on_demand', 'flexible'}
            },            
            'optional': False,
            'description': 'Total water volume in liters.'
        }, 
        'Purity': {
            'Value': {
                'type': {float, int},
                'bounds': (0, 1)
            },
            'Unit': {
                'dimension': 'dimensionless'
            },
            'Type': {
                'type': str,
                'options': {'total_dissolved_solids', 'contaminants'}
            },
            'optional': False,
            'description': 'The purity of water in the system.'
        }
    },
    'Number of units':{
        'Bag number':{
            'Value': {
                'type': {int,},
                'bounds': (0, None),
            },
            'Unit': {
                'dimension': 'dimensionless',
            },                    
            'optional': False,
            'description': 'Number of bags in the system.'
        },                                                        
    },
    'Catalyst':{
        'Lifetime':{
            'Value': {
                'type': {float, int},
                'bounds': (0, None),
            },
            'Unit': {
                'dimension': 'time'
            },                    
            'optional': False,
            'description': 'Catalyst lifetime in years.'
        },                                                        
    },
    'Catalyst Separation':{
        'Filtration cost':{
            'Value': {
                'type': {float, int},
                'bounds': (0, None),
            },
            'Unit': {
                'dimension': 'currency / volume'
            },                    
        'optional': False,
        'description': 'Specific Catalyst separation cost.'
        },                                                        
    },
    'Grid Electricity': {
        'Cost':{
            'Value': {
                'type': {float, int, np.ndarray},
                'bounds': (0, None),
            },
            'Unit': {
                'dimension': 'currency / energy'
            },                    
        'optional': True,
        'description': 'Stored electric energy per period.'
        },                                                        
    },
    'Power Generation':{
        'Stored Power':{
            'Value': {
                'type': {dict,},
                'bounds': (0, None),
                },
            'Unit': {
                'dimension': 'energy'
                },                    
            'optional': True,
            'description': 'Stored electric energy per period.'
        },
        'Available Power':{              
            'Value': {
                'type': {dict,}, 
                'bounds': (0, None),
                },
            'Unit': {
                'dimension': 'energy'
                },                    
            'optional': False,
            'description': 'Available electric energy per period.'
        },                                                         
    },
    'Compressor': {
        'Electricity':{
            'Value': {
                'type': {float, int},
                'bounds': (0, None),
            },
            'Unit': {
                'dimension': 'currency'
            },                    
            'optional': True,
            'description': 'Electricity cost for compressor.'
        },
    },
    'Turbopump': {
        'Electricity':{
            'Value': {
                'type': {float, int},
                'bounds': (0, None),
            },
            'Unit': {
                'dimension': 'currency'
            },                    
            'optional': False,
            'description': 'Electricity cost for turbopump.'
        },
        'Maintenance':{
            'Value': {
                'type': {float, int},
                'bounds': (0, None),
            },
            'Unit': {
                'dimension': 'currency'
            },
            'optional': True,
            'description': 'Maintenance cost for turbopump.'
        },
    },
    'Power Consumption':{
        '<...>':{   
            # Assuming all the keys that are not known in advance must follow the same schema
            'Value': {
                'type': {np.ndarray,},
                'bounds': (0, None),
                'length': 3 # expected length of the array (in practice, would be more like 365 for a value per day of the year)
            },
            'Unit': {
                'dimension': 'energy'
            },   
            'Type': {
                'type': {str,},
                'options': {
                    'on demand', 'flexible'
                },                                    
            },
            'optional': True,
            'description': 'Power consumption per consumer.'
        },                                                        
    },
    '<...> Other Variable Operating Cost <...>':{ # table group
        '<...>':{ 
            'Value': {
                'type': {float, int, np.ndarray},
                'bounds': (0, None),
            },
            'Unit': {
                'dimension': 'currency'
            },   
            'optional': True,
            'description': 'All other variable operating costs.'
            },                                                        
    },
    '<...> Table group which is not used <...>': {
        '<...>':{ 
            'Value': {
                'type': {float, int, np.ndarray},
                'bounds': (0, None),
            },
            'Unit': {
                'dimension': 'currency'
            },   
            'optional': True,
            'description': 'This table group is not used in the test, serves to check that unused groups are correctly ignored.'
        },
    },
    'Irradiation Used': {
        'Data': {
            'Value': {
                'type': {str, np.ndarray},
                'bounds': (0, None),
            },
            'Unit': {
                'dimension': 'energy / area'
            },
            'optional': False,
            'description': 'Irradiation data for PV power generation calculation.'
        },
        'Other Data': {
            'Value': {
                'type': {str, np.ndarray,},
                'bounds': (0, None),
            },
            'Unit': {
                'dimension': 'energy / area'
            },
            'optional': False,
            'description': 'Additional irradiation data for testing.'
        },
        'Only String': {
            'Value': {
                'type': {str,},
            },
            'optional': False,
            'description': 'Testing of only getting a string'
        },   
        'Quantity object': {
            'Value': {
                'type': {np.ndarray,},
                'bounds': (0, None),
                },
            'Unit': {
                'dimension': 'energy / area'
            },
            'optional': False,
            'description': 'Testing of directly getting a Quantity object'
        }
    },
    'Quantity Path Testing': {
        'Electrolyzer power': {
            'Value': {
                'type': {float, int},
                'bounds': (0, None),
            },
            'Unit': {
                'dimension': 'power'
            },
            'optional': False,
            'description': 'Power of the electrolyzer.'
        },
        'PV power': {
            'Value': {
                'type': {float, int},
                'bounds': (0, None),
            },
            'Unit': {
                'dimension': 'power'
            },
            'optional': False,
            'description': 'Power of the PV system'
        }
    }
}

# Expected resolved output
input_dict_resolved = {'Utilities':{ 
                                'Natural gas': {
                                    'Usage_Value': Quantity(5.4E9, 'J/kg'),
                                    'Cost_Value': Quantity(5.55555555555E-5, 'USD/J'),
                                    'Type': 'natural_gas'
                                },
                                'Electricity': {
                                    'Usage_Value': Quantity(10.8E9, 'J/kg'),
                                    'Cost_Value': Quantity(1.38888888888E-4, 'USD/J'),
                                    'Type': 'electricity'
                                },
                                'Water': {
                                    'Usage_Value': Quantity(100, 'J/kg'),
                                    'Cost_Value': Quantity(625.0, 'USD/J'),
                                    'Type': 'water'
                                }
                        },
                        'Water Supply':{
                                'Volume':{
                                    'Value': Quantity(5.E-2, 'm3'), 
                                    'Type': 'flexible'
                                },
                                'Purity':{
                                    'Value': Quantity(0.99, '-'), 
                                    'Type': 'contaminants'
                                },                                
                        },
                        'Number of units': {
                                'Bag number': {
                                    'Value': Quantity(50, '-')
                                },
                        },
                        'Catalyst': {
                                'Lifetime': {
                                    'Value': Quantity(1.5768E8, 's')  # 365 days in a year
                                },
                        },
                        'Catalyst Separation': {
                                'Filtration cost': {
                                    'Value': Quantity(1.E2, 'USD/m3')
                                },
                        },      
                        'Grid Electricity': {
                                'Cost': {
                                    'Value': Quantity(4.16666667e-8, 'USD/J')
                                },
                        },  
                        'Power Generation': {
                                'Available Power': {
                                    'Value': {
                                        '2025': Quantity(np.array([1.44e9, 9.0e8, 1.26e9]), 'J'), 
                                        '2024': Quantity(np.array([1.8e9, 1.26e9, 1.62e9]), 'J')
                                    },
                                },
                                'Stored Power': {
                                    'Value':{
                                        '2025': Quantity(7.2E8, 'J'),
                                        '2024': Quantity(9.E8, 'J')
                                     },
                                },                                   
                        },                                    
                        'Power Consumption': {
                                'Any mid key': {
                                    'Value': Quantity(np.array([3.6E8, 4.32E8, 3.96E8]), 'J') ,
                                    'Type': 'on demand'
                                },   
                                'Another mid key': {
                                    'Value': Quantity(np.array([1.8E8, 1.44E8, 2.16E8]), 'J') ,
                                    'Type': 'flexible'
                                },   
                        }, 
                        'Pump - Other Variable Operating Cost - Brand A': {
                                'Maintenance': {
                                    'Value': Quantity(1.25E1, 'USD')
                                },
                                'lubrication': {
                                    'Value': Quantity(8.2, 'USD')
                                }                                
                        },
                        'Compressor - Other Variable Operating Cost - Brand B': {
                                'Lubrication': {
                                    'Value': Quantity(np.array([1.3, 1.2, 1.1]), 'USD')
                                },   
                                'Electricity': {
                                    'Value': Quantity(2.2, 'USD')
                                }                                   
                        },    
                        'Bag - Other Variable Operating Cost': {
                            'Replacement': {
                                'Value': Quantity(50, 'USD')
                            },
                            'Disposal': {
                                'Value': Quantity(500, 'USD')
                            },
                            'Recycling': {
                                'Value': Quantity(2500, 'USD')
                            },
                        },
                        'Turbopump': {
                            'Electricity': {
                                'Value': Quantity(500, 'USD')
                            },
                        },
                        'Irradiation Used': {
                            'Data': {
                                'Value': 'Path/to/file.txt',
                            },
                            'Other Data': {
                                'Value': Quantity(np.array([1., 2., 3.]), 'J/m2'),
                            },
                            'Only String': {
                                'Value': 'Just a string',
                            },
                            'Quantity object': {
                                'Value': Quantity(np.array([1., 2., 3.]), 'J/m2'),
                            }
                        },
                        'Quantity Path Testing': {
                            'Electrolyzer power': {
                                'Value': Quantity(100, 'kW'),
                            },
                            'PV power': {
                                'Value': Quantity(150000, 'W'),    
                            }
                        },
    }
    





