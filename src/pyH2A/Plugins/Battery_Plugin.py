from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
import numpy as np

input_dict = {    
    "Time": {
        "Years": {
            "Value": {
                "type": {dict,},
                "bounds": (None, None),
            },
            "Unit": {
                "dimension": "dimensionless",
            },
            "optional": False,
            "description": "Dictionary containing all time-related quantities."
        }, 
    },        
    "Power Generation": {
        "Available energy (daily)": {
            "Value": {
                "type": {dict,},
                "bounds": (0, None),
            },
            "Unit": {
                "dimension": "energy",
            },                    
            "optional": False,
            "description": " Available energy, daily basis, dictionary of years."
        },                      
    },
    
    "Battery": {
        "Design capacity": { 
            "Value": {
                "type": {int, float,},
                "bounds": (0, None),
            },
            "Unit": {
                "dimension": "energy",
            },                    
            "optional": False,
            "description": "Full design capacity of battery."
        },
        
        "Lowest discharge level": {
            "Value": {
                "type": {int, float,},
                "bounds": (0, 1),
            },
            "Unit": {
                "dimension": "dimensionless",
            },                    
            "optional": False,
            "description": "Lowest level to which battery can be discharged."
        },
        
        "Capacity loss per year": {
            "Value": {
                "type": {int, float,},
                "bounds": (0, 1),
            },
            "Unit": {
                "dimension": "dimensionless",
            },                    
            "optional": False,
            "description": "Loss of capacity per year."
        },
        
        "Round trip efficiency": {
            "Value": {
                "type": {int, float,},
                "bounds": (0, 1),
            },
            "Unit": {
                "dimension": "dimensionless",
            },                    
            "optional": False,
            "description": "Round trip efficiency of battery."
        },

        "Energy density": {
            "Value": {
                "type": {float,},
                "bounds": (0, None),
            },
            "Unit": {
                "dimension": "energy / mass",
            },
            "optional": True,
            "description": "Battery specific energy for analyses (kWh/kg)."
        },
    }
}

output_dict = {
    "Battery": {
        "Mass (kg)": {
            "Value": {
                "inserted_value": "battery_mass",
                "type": {int, float,},
                "dimension": "mass",
            },
            "description": "Installed battery mass, calculated as design capacity divided by "
                           "energy density.",
            "optional": True,
        },
    },
    "Power Generation": {
        "Stored energy (daily)": {
            "Value": {
                "inserted_value": "yearly_recovered_energy",
                "type": {dict,},
                "dimension": "energy",
            },
            "description": "Energy stored in battery daily (dictionary of years)",
            "optional": False,
        },
        "Available energy (daily)": {
            "Value": {
                "inserted_value": "yearly_unstored_energy",
                "type": {dict,},
                "dimension": "energy",
            },
            "description": "Available energy, daily basis, dictionary of years - energy which has not been stored in battery",
            "optional": False,
        },
        "Available energy (hourly)": {
            "Value": {
                "inserted_value": Quantity(0, 'J'),
                 "type": {float,},
                 "dimension": "energy",
            },
            "description": "Available energy is set to zero, since available energy is now only in daily format.",
            "optional": False,
        }
    }
}

class Battery_Plugin:
    '''Simulation of electricity storage using a battery.
    Simulation assumes that battery is charged and completely discharged every day.
    (no electricity storage across days, only one discharge per day, not multiple ones).

    Parameters
    ----------
    Time > Years > Value : dict
        Dictionary containing plant life time-related quantities
    Power Generation > Available energy (daily) > Value : dict
        Available energy, daily basis, dictionary of years.
    Battery > Design capacity > Value : float
        Full design capacity of battery.
    Battery > Lowest discharge level > Value : float
        Lowest level to which battery can be discharged. Dimensionless value between 0 and 1.
    Battery > Capacity loss per year > Value : float
        Loss of capacity per year. Dimensionless value > 0.
    Battery > Round trip efficiency > Value : float
        Round trip efficiency of battery. Dimensionless value between 0 and 1.
    Battery > Energy density > Value : float, optional
        Battery specific energy in kWh/kg. Used to calculate installed battery mass
        from design capacity.

    Returns
    -------
    Power Generation > Stored energy (daily) > Value : dict
        Energy stored in battery daily (dictionary of years).
    Power Generation > Available energy (daily) > Value : dict
        Available energy, daily basis, dictionary of years - power which
        has not been stored in battery
    Power Generation > Available energy (hourly) > Value : float
        Available energy (hourly) is set to zero, since available power is now
        only in daily format.
    Battery > Mass (kg) > Value : float
        Installed battery mass in kg, calculated as design capacity divided by
        energy density. Inserted when Life Cycle Assessment is present.
    '''

    def __init__(self, dcf, print_info, run = True):
        self._set_up(dcf)
        if run:
            self._run(dcf)

    def _set_up(self, dcf):

        self.functional_unit = dcf.functional_unit

        self.input_dict = {
            "Time": {
                "Years": {
                    "Value": {
                        "type": {dict,},
                        "bounds": (None, None),
                    },
                    "Unit": {
                        "dimension": "dimensionless",
                    },
                    "optional": False,
                    "description": "Dictionary containing all time-related quantities."
                }, 
            },        
            "Power Generation": {
                "Available energy (daily)": {
                    "Value": {
                        "type": {dict,},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "energy",
                    },                    
                    "optional": False,
                    "description": " Available energy, daily basis, dictionary of years."
                },                      
            },

            "Battery": {
                "Design capacity": { 
                    "Value": {
                        "type": {int, float,},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "energy",
                    },                    
                    "optional": False,
                    "description": "Full design capacity of battery."
                },

                "Lowest discharge level": {
                    "Value": {
                        "type": {int, float,},
                        "bounds": (0, 1),
                    },
                    "Unit": {
                        "dimension": "dimensionless",
                    },                    
                    "optional": False,
                    "description": "Lowest level to which battery can be discharged."
                },

                "Capacity loss per year": {
                    "Value": {
                        "type": {int, float,},
                        "bounds": (0, 1),
                    },
                    "Unit": {
                        "dimension": "dimensionless",
                    },                    
                    "optional": False,
                    "description": "Loss of capacity per year."
                },

                "Round trip efficiency": {
                    "Value": {
                        "type": {int, float,},
                        "bounds": (0, 1),
                    },
                    "Unit": {
                        "dimension": "dimensionless",
                    },                    
                    "optional": False,
                    "description": "Round trip efficiency of battery."
                },  
            } 
        }

        self.output_dict = {
            "Power Generation": {
                "Stored energy (daily)": {
                    "Value": {
                        "inserted_value": "yearly_recovered_energy",
                        "type": {dict,},
                        "dimension": "energy",
                    },
                    "description": "Energy stored in battery daily (dictionary of years)",
                    "optional": False,
                },
                "Available energy (daily)": {
                    "Value": {
                        "inserted_value": "yearly_unstored_energy",
                        "type": {dict,},
                        "dimension": "energy",
                    },
                    "description": "Available energy, daily basis, dictionary of years - energy which has not been stored in battery",
                    "optional": False,
                },
                "Available energy (hourly)": {
                    "Value": {
                        "inserted_value": Quantity(0, 'J'),
                         "type": {float,},
                         "dimension": "energy",
                    },
                    "description": "Available energy is set to zero, since available energy is now only in daily format.",
                    "optional": False,
                }
            }
        }

    def _run(self, dcf):
        self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, 'Battery_Plugin')

        self.calculate_electricity_storage(dcf)
        if _battery_mass_referenced_in_inp(dcf):
            self.calculate_battery_mass()

        output_inserter_function(output_dict, self, dcf, 'Battery_Plugin')

    def calculate_electricity_storage(self, dcf):
        '''Using hourly energy generation data and electrolyzer parameters,
        H2 production is calculated.
        '''
        available_energy_yearly = self.input_dict_resolved['Power Generation']['Available energy (daily)']['Value']

        self.yearly_recovered_energy = {}
        self.yearly_unstored_energy = {}

        for year in self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-']:
            daily_available_energy = available_energy_yearly[year].unit['J'] # array of floats

            capacity, capacity_decrease = self.calculate_battery_capacity(year) # floats

            capacity *= np.ones(len(daily_available_energy))
            daily_stored_energy = np.amin(np.c_[daily_available_energy, capacity], axis = 1)
            daily_recovered_energy = daily_stored_energy * self.input_dict_resolved['Battery']['Round trip efficiency']['Value'].unit['-']

            unstored_energy = daily_available_energy - daily_stored_energy

            self.yearly_recovered_energy[year] = Quantity(daily_recovered_energy, 'J')
            self.yearly_unstored_energy[year] = Quantity(unstored_energy, 'J')
 
    def calculate_battery_capacity(self, year):

        capacity_decrease = (1. - self.input_dict_resolved['Battery']['Capacity loss per year']['Value'].unit['-'] ) ** year
        nominal_capacity = self.input_dict_resolved['Battery']['Design capacity']['Value'].unit['J'] * (1. - self.input_dict_resolved['Battery']['Lowest discharge level']['Value'].unit['-'])

        capacity = nominal_capacity * capacity_decrease

        return capacity, capacity_decrease

    def calculate_battery_mass(self):
        '''Calculation of installed battery mass from design capacity and energy density.
        '''

        design_capacity_kWh = self.input_dict_resolved['Battery']['Design capacity']['Value'].unit['kWh']

        energy_density_resolved = self.input_dict_resolved['Battery'].get('Energy density')

        if energy_density_resolved is None:
            raise KeyError("Missing required input: Battery > Energy density > Value. Please add Energy density to calculate Mass (kg).")

        energy_density_kWh_per_kg = energy_density_resolved['Value'].unit['kWh/kg']

        if energy_density_kWh_per_kg == 0:
            raise ValueError("Battery energy density must be greater than zero.")

        self.battery_mass = Quantity(design_capacity_kWh / energy_density_kWh_per_kg, 'kg')


def _battery_mass_referenced_in_inp(dcf):
    '''Return True if any table's Path references battery mass.'''

    target = 'battery > mass (kg) > value'
    rows = [row for table in dcf.inp.values() for row in table.values()]
    return any(target in str(row.get('Path', '')).strip().lower() for row in rows)