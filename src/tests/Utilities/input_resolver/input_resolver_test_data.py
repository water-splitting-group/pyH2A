import numpy as np
from pint import UnitRegistry

ureg = UnitRegistry()
ureg.define('USD = [currency]')


class DummyDCF:
    def __init__(self):

        self.inp = {
            'Utilities': {
                'Natural gas': {
                    'Usage_Value': 1500,
                    'Usage_Unit': 'kWh/kg',
                    'Cost_Value': 200,
                    'Cost_Unit': 'USD/kWh',
                    'Type': 'natural_gas'
                },
                'Electricity': {
                    'Usage_Value': 3000,
                    'Usage_Unit': 'kWh/kg',
                    'Cost_Value': 500,
                    'Cost_Unit': 'USD/kWh',
                    'Type': 'electricity'
                }
            },

            'Water Supply': {
                'Volume': {
                    'Value': 50,
                    'Unit': 'liters',
                    'Type': 'flexible'
                },
                'Purity': {
                    'Value': 99,
                    'Unit': 'percent',
                    'Type': 'contaminants'
                }
            },

            'Number of units': {
                'Bag number': {
                    'Value': 50,
                    'Unit': 'dimensionless'
                }
            },

            'Catalyst': {
                'Lifetime': {
                    'Value': 5,
                    'Unit': 'years'
                }
            },

            'Catalyst Separation': {
                'Filtration cost': {
                    'Value': 100,
                    'Unit': '$/m3'
                }
            },

            'Grid electricity': {
                'Cost': {
                    'Value': 0.15,
                    'Unit': '$/kWh'
                }
            },

            'Power Generation': {
                'Available Power': {
                    'Value': {
                        '2025': np.array([400., 250., 350.]), '2024': np.array([500., 350., 450.])
                    },
                    'Unit': 'kWh'
                },
                'Stored Power': {
                    'Value': {
                        '2025': 200., '2024': 250.
                    },
                    'Unit': 'kWh'
                }
            },

            # the following one serves to test the situation where middle key isn't known in advance / when we want to iterate
            'Power Consumption': {
                'Any mid key': {
                    'Value': np.array([100., 120., 110.]),
                    'Type': 'on demand',
                    'Unit': 'kWh'
                },
                'Another mid key': {
                    'Value': np.array([50., 40., 60.]),
                    'Type': 'flexible',
                    'Unit': 'kWh'
                },
            },

            # Pump and compressor: to test the "Other Variable Operating Cost" group
            'Pump - Other Variable Operating Cost - Brand A': {
                'Maintenance': {
                    'Value': 12.5,
                    'Unit': '$'
                },
                'lubrication':  {
                    'Value': 8.2,
                    'Unit': '$'
                }
            },

            'Compressor - Other Variable Operating Cost - Brand B': {
                'Lubrication': {
                    'Value': np.array([1.3, 1.2, 1.1]),
                    'Unit': '$'
                },
                'Electricity': {
                    'Value': 2.2,
                    'Unit': '$'
                }
            }

        }


input_dict = {

    'Utilities': {
        '<...>': {
            'Usage_Value': {
                'type': {float, int},
                'bounds': (0, None)
            },
            'Usage_Unit': {
                'dimension': 'energy / mass'
            },
            'Cost_Value': {
                'type': {float, int},
                'bounds': (0, None)
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

    'Water Supply': {
        'Volume': {
            'Value': {
                'type': {float, },
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

    'Number of units': {
        'Bag number': {
            'Value': {
                'type': {int, },
                'bounds': (0, None),
            },
            'Unit': {
                'dimension': 'dimensionless',
            },
            'optional': False,
            'description': 'Number of bags in the system.'
        },
    },

    'Catalyst': {
        'Lifetime': {
            'Value': {
                'type': {float, },
                'bounds': (0, None),
            },
            'Unit': {
                'dimension': 'time'
            },
            'optional': False,
            'description': 'Catalyst lifetime in years.'
        },
    },

    'Catalyst Separation': {
        'Filtration cost': {
            'Value': {
                'type': {float, },
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
        'Cost': {
            'Value': {
                'type': {float, np.ndarray},
                'bounds': (0, None),
            },
            'Unit': {
                'dimension': 'currency / energy'
            },
            'optional': True,
            'description': 'Stored electric energy per period.'
        },
    },

    'Power Generation': {
        'Stored Power': {
            'Value': {
                'type': {dict, },
                'bounds': (0, None),
            },
            'Unit': {
                'dimension': 'energy'
            },
            'optional': True,
            'description': 'Stored electric energy per period.'
        },
        'Available Power': {
            'Value': {
                'type': {dict, },
                'bounds': (0, None),
            },
            'Unit': {
                'dimension': 'energy'
            },
            'optional': False,
            'description': 'Available electric energy per period.'
        },
    },

    'Power Consumption': {
        '<...>': {
            # Assuming all the keys that are not known in advance must follow the same schema
            'Value': {
                'type': {np.ndarray, },
                'bounds': (0, None),
                # expected length of the array (in practice, would be more like 365 for a value per day of the year)
                'length': 3
            },
            'Unit': {
                'dimension': 'energy'
            },
            'Type': {
                'type': {str, },
                'options': {
                    'on demand', 'flexible'
                },
            },
            'optional': True,
            'description': 'Power consumption per consumer.'
        },
    },

    '<...> Other Variable Operating Cost <...>': {  # table group
        '<...>': {
            'Value': {
                'type': {float, np.ndarray},
                'bounds': (0, None),
                # length might not be known in advance: check its consistency only if the 'length' key is found in the input
            },
            'Unit': {
                'dimension': 'currency'
            },
            'optional': True,
            'description': 'All other variable operating costs.'
        },
    },

}


# Expected resolved output
input_dict_resolved = {'Utilities': {
    'Natural gas': {
        'Usage_Value': ureg.Quantity(5.4E9, 'J/kg'),
        'Cost_Value': ureg.Quantity(5.555555E-5, 'USD/J'),
        'Type': 'natural_gas'
    },
    'Electricity': {
        'Usage_Value': ureg.Quantity(10.8E9, 'J/kg'),
        'Cost_Value': ureg.Quantity(1.388888E-4, 'USD/J'),
        'Type': 'electricity'
    },
},
    'Water Supply': {
    'Volume': {
        'Value': ureg.Quantity(5.E-2, 'meter**3'),
        'Type': 'flexible'
    },
    'Purity': {
        'Value': ureg.Quantity(0.99, 'dimensionless'),
        'Type': 'contaminants'
    },
},
    'Number of units': {
    'Bag number': {
        'Value': ureg.Quantity(50, 'dimensionless')
    },
},
    'Catalyst': {
    'Lifetime': {
        'Value': ureg.Quantity(1.57788E8, 's')  # assuming 1 year = 365.25 days
    },
},
    'Catalyst Separation': {
    'Filtration cost': {
        'Value': ureg.Quantity(1.E2, 'USD/meter**3')
    },
},
    'Grid electricity': {
    'Cost': {
        'Value': ureg.Quantity(4.16666667e-8, 'USD/J')
    },
},
    'Power Generation': {
    'Available Power': {
        'Value': {
            '2025': ureg.Quantity(np.array([1.44e9, 9.0e8, 1.26e9]), 'J'),
            '2024': ureg.Quantity(np.array([1.8e9, 1.26e9, 1.62e9]), 'J')
        },
    },
    'Stored Power': {
        'Value': {
            '2025': ureg.Quantity(7.2E8, 'J'),
            '2024': ureg.Quantity(9.E8, 'J')
        },
    },
},
    'Power Consumption': {
    'Any mid key': {
        'Value': ureg.Quantity(np.array([3.6E8, 4.32E8, 3.96E8]), 'J'),
        'Type': 'on demand'
    },
    'Another mid key': {
        'Value': ureg.Quantity(np.array([1.8E8, 1.44E8, 2.16E8]), 'J'),
        'Type': 'flexible'
    },
},
    'Pump - Other Variable Operating Cost - Brand A': {
    'Maintenance': {
        'Value': ureg.Quantity(1.25E1, 'USD')
    },
    'lubrication': {
        'Value': ureg.Quantity(8.2, 'USD')
    }
},

    'Compressor - Other Variable Operating Cost - Brand B': {
    'lubrication': {
        'Value': ureg.Quantity(np.array([1.3, 1.2, 1.1]), 'USD')
    },
    'Electricity': {
        'Value': ureg.Quantity(2.2, 'USD')
    }
},
}

if __name__ == "__main__":
    from pyH2A.Utilities.IO_Resolver.input_resolver import InputResolver

    dcf = DummyDCF()
    resolver = InputResolver(dcf)
    resolved = resolver.resolve(input_dict)
    print(resolved)
