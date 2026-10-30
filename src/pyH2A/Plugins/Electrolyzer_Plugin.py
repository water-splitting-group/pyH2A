from pyH2A.Utilities.input_modification import hourly_to_daily_power, smoothened_production, moving_average
from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Physical_Properties.Physical_properties import Physical_properties as PP
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
import numpy as np

class Electrolyzer_Plugin:
    '''Simulation of hydrogen production using electrolysis.
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
            "Technical Operating Parameters and Specifications": {		
                "Operating capacity factor": { 
                    "Value": {
                        "type": {float, int},
                        "bounds": (0, 1),
                    },
                    "Unit": {
                        "dimension": "dimensionless",
                    },
                    "optional": False,
                    "description": "Operating capacity factor value between 0 and 1."
                },  						
            },            
            "Electrolyzer": {
                "Nominal power": {
                    "Value": {
                        "type": {int,float,},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "power",
                    },
                    "optional": False,
                    "description": "Nominal power of electrolyzer."
                },
                "Unit nominal power": {
                    "Value": {
                        "type": {int,float,},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "power",
                    },
                    "optional": True,
                    "description": "Nominal power of one electrolyzer unit, used to calculate the number of electrolyzers and stacks."
                },
                "Power requirement increase per year": {
                    "Value": {
                        "type": {int,float,},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "dimensionless",
                    },
                    "optional": False,
                    "description": "Electrolyzer power requirement increase per year due to stack degradation.\
                            Percentage or value > 0. Increase calculated as: (1 + increase per year) ^ year."
                },
                "Minimum capacity": {
                    "Value": {
                        "type": {int,float,},
                        "bounds": (0, 1),
                    },
                    "Unit": {
                        "dimension": "dimensionless",
                    },
                    "optional": False,
                    "description": "Minimum capacity required for electrolyzer operation. Percentage or value between 0 and 1."
                },
                "Minimum operating power coefficient": {
                    "Value": {
                        "type": {int,float,},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "dimensionless",
                    },
                    "optional": False,
                    "description": "Proportionality coefficient: electrolyzer minimum power = coefficient * energy excess. The actual minimum is curtailed by the previous Minimum capacity value. "
                },                
                "Hydrogen yield per unit energy": {
                    "Value": {
                        "type": {int,float,},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "mass / energy",
                    },
                    "optional": False,
                    "description": "Electrical conversion efficiency of electrolyzer in mass(H2)/energy(electrical)."
                },
                "Replacement time": {
                    "Value": {
                        "type": {int,float,},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "time",
                    },
                    "optional": False,
                    "description": "Operating time before stack replacement of electrolyzer is required."
                },
            },
            "Power Generation": {
                "Available energy (hourly)": {
                    "Value": {
                        "type": {dict,},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "energy",
                    },
                    "optional": False,
                    "description": "Available energy, hourly basis, dictionary of years in (energy)."
                },
            },
        }

        self.output_dict = {
            "Electrolyzer": {
                "Yearly operation data": {
                    "Year_Value": {
                        "inserted_value": "yearly_data_year",
                        "type": {np.ndarray,},
                        "dimension": "dimensionless", 
                    },                  
                    "Production_Value": {
                        "inserted_value": "yearly_data_production",
                        "type": {np.ndarray,},
                        "dimension": "mass", 
                    },  
                    "Duration_Value": {
                        "inserted_value": "yearly_data_duration",
                        "type": {np.ndarray,},
                        "dimension": "time", 
                    },                      
                    "optional": False,
                    "description": "Yearly operation data of electrolyzer: year, H2 produced, duration of operation."
                },
                "Missing required energy (hourly)": {
                    "Value": {
                        "inserted_value": "yearly_data_missing_energy",
                        "type": {dict,},
                        "dimension": "energy",
                    },
                    "optional": False,
                    "description": "Required energy (hourly) for the electrolyzer to stay above the minimum power threshold (dictionary of years)."
                },                  
                "H2 production (yearly)": {
                    "Value": {
                        "inserted_value": "yearly_h2_production",
                        "type": {np.ndarray,},
                        "dimension": "mass",
                    },
                    "optional": False,
                    "description": "Yearly hydrogen production."
                },
                "Actual stack replacement time": {
                    "Value": {
                        "inserted_value": "replacement_frequency",
                        "type": {int, float,},
                        "dimension": "time",
                    },
                    "description": "Actual stack replacement time, \
                            calculated from replacement time and operation data."
                },
                "Number of units": {
                    "Value": {
                        "inserted_value": "number_of_units",
                        "type": {int, float,},
                        "dimension": "dimensionless",
                    },
                    "optional": True,
                    "description": "Number of electrolyzer units required for the system."
                },
                "Number of stacks": {
                    "Value": {
                        "inserted_value": "number_of_stacks",
                        "type": {int, float,},
                        "dimension": "dimensionless",
                    },
                    "optional": True,
                    "description": "Number of electrolyzer stacks required for the system, whole lifetime."
                },
            },
            "Power Generation": {
                "Available energy (hourly)": {
                    "Value": {
                        "inserted_value": "yearly_data_unused_energy",
                        "type": {dict,},
                        "dimension": "energy",
                    },
                    "optional": False,
                    "description": "Available energy (hourly) after subtracting power consumed by electrolyzer (dictionary of years)."
                },
                "Available energy (daily)": {
                    "Value": {
                        "inserted_value": "yearly_data_unused_energy_daily",
                        "type": {dict,},
                        "dimension": "energy",
                    },
                    "optional": False,
                    "description": "Available energy (daily) after subtracting power consumed by electrolyzer (dictionary of years)."
                },
            },
            "Electrolyzer Water Feed": {
                "Gross yearly mass": {
                    "Value": {
                        "inserted_value": "gross_yearly_mass",
                        "type": {np.ndarray,},
                        "dimension": "mass",
                    },
                    "optional": False,
                    "description": "Mass of water to inject in the electrolyzer per year, accounting for conversion and evaporation"
                },
                "Net yearly mass": {
                    "Value": {
                        "inserted_value": "net_yearly_mass",
                        "type": {np.ndarray,},
                        "dimension": "mass",
                    },
                    "optional": False,
                    "description": "Mass of water converted into hydrogen per year"
                },				
            },	            
            "Main Stream": {
                "Temperature": {
                    "Value": {
                        "inserted_value": "outlet_temperature",
                        "type": {dict,},
                        "dimension": "absolute_temperature",
                    },
                    "optional": False,
                    "description": "Mixture outlet temperature."
                },
                "Pressure": {
                    "Value": {
                        "inserted_value": "outlet_pressure",
                        "type": {float,},
                        "dimension": "pressure",
                    },
                    "optional": False,
                    "description": "Mixture outlet pressure."
                },
                "Specific enthalpy": {
                    "Value": {
                        "inserted_value": "outlet_enthalpy",
                        "type": {dict,},
                        "dimension": "energy/mass",
                    },
                    "optional": False,
                    "description": "Mixture outlet specific enthalpy."
                },  
                "Mass fraction": {
                    "Value": {
                        "inserted_value": "outlet_mass_fraction",
                        "type": {dict,},
                        "dimension": "dimensionless",
                    },
                    "optional": False,
                    "description": "Mixture outlet mass fraction."
                },   
                "Mass flow (hourly)": {
                    "Value": {
                        "inserted_value": "hourly_mass_flow",
                        "type": {dict,},
                        "dimension": "mass",
                    },
                    "optional": False,
                    "description": "Mixture outlet mass flow, dictionary of years whose items are hourly arrays."
                },  					 					                
            },	            
        }

    def _run(self, dcf):
        self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, 'Electrolyzer_Plugin')

        self.calculate_H2_production()
        self.outlet_flow_properties()
        self.water_consumption()
        (self.replacement_frequency, 
        self.number_of_replacements) = calculate_stack_replacement(self.yearly_data_duration, 
                                        self.input_dict_resolved['Electrolyzer']['Replacement time']['Value'].unit['h'])

        if 'Unit nominal power' in self.input_dict_resolved['Electrolyzer']:
            (self.number_of_units, 
            self.number_of_stacks) = calculate_number_of_units(self.input_dict_resolved['Electrolyzer']['Unit nominal power']['Value'],
                                    self.input_dict_resolved['Electrolyzer']['Nominal power']['Value'],
                                    self.number_of_replacements)

        output_inserter_function(self.output_dict, self, dcf, 'Electrolyzer_Plugin') 

    def calculate_H2_production(self):
        '''Using hourly power generation data and electrolyzer parameters,
        H2 production is calculated.
        '''

        energy_generation_yearly_data = self.input_dict_resolved['Power Generation']['Available energy (hourly)']['Value']

        yearly_data_year = []
        yearly_data_production = []
        yearly_data_duration = []
        yearly_data_missing_energy = {}
        yearly_data_unused_energy = {}
        yearly_data_unused_energy_daily = {}
        self.hourly_h2_production = {}

        for year in self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-']:
            year = round(year)
            energy_generation_J = energy_generation_yearly_data[year].unit['J']

            electrolyzer_power_demand, power_increase_ratio = calculate_electrolyzer_power_demand(
                            self.input_dict_resolved['Electrolyzer']['Power requirement increase per year']['Value'].unit['-'],
                            self.input_dict_resolved['Electrolyzer']['Nominal power']['Value'].unit['W'],
                            year) # returns: power (Watt), dimensionless

            electrolyzer_energy_demand_J = 3600*electrolyzer_power_demand # integrate the power over 1 hour, since we ultimately think in terms of energy involved in each 1-hour slot
            electrolyzer_energy_demand_J *= np.ones(len(energy_generation_J))

            # Energy that exceeds the power demand remains available
            unused_energy_J = np.zeros_like(energy_generation_J)
            is_overproducing = energy_generation_J > electrolyzer_energy_demand_J
            unused_energy_J[is_overproducing] = energy_generation_J[is_overproducing] - electrolyzer_energy_demand_J[is_overproducing]
            yearly_data_unused_energy[year] = Quantity(unused_energy_J, 'J')
            yearly_data_unused_energy_daily[year] = Quantity(hourly_to_daily_power(unused_energy_J), 'J')            

            # Energy that is missing to maintain the electrolyzer above its minimum operating threshold will have to be provided by the battery
            missing_energy = np.zeros_like(energy_generation_J)
            averaging_overproduction_period = Quantity(1, 'day')
            moving_averaged_unused_energy_J = moving_average(unused_energy_J, round(averaging_overproduction_period.unit['h']))
            minimum_hourly_energy_J = self.input_dict_resolved['Electrolyzer']['Minimum operating power coefficient']['Value'].unit['-'] * moving_averaged_unused_energy_J 
            minimum_hourly_energy_J = np.clip(minimum_hourly_energy_J, self.input_dict_resolved['Electrolyzer']['Minimum capacity']['Value'].unit['-'] * electrolyzer_energy_demand_J, electrolyzer_energy_demand_J)
            is_underproducing = energy_generation_J < minimum_hourly_energy_J
            missing_energy[is_underproducing] = minimum_hourly_energy_J[is_underproducing] - energy_generation_J[is_underproducing]
            yearly_data_missing_energy[year] = Quantity(missing_energy, 'J')

            # The energy effectively consumed by the electrolyzer is the generated energy, 
            # saturated on the lower bound by the minimum_hourly_energy_J (the missing energy would come from the battery)
            # and on the upper bound by the electrolyzer demand (the extra energy is available for the rest of the power chain).
            electrolyzer_energy_consumption = np.clip(energy_generation_J, minimum_hourly_energy_J, electrolyzer_energy_demand_J)                  

            hours_equivalent_full_Production = np.sum(electrolyzer_energy_consumption)/electrolyzer_energy_demand_J[0] # Number of full-production hours that would be needed to obtain the actual (fluctuating) production over the year

            h2_produced = calculate_hydrogen_production(
                                electrolyzer_energy_consumption,
                                self.input_dict_resolved['Electrolyzer']['Hydrogen yield per unit energy']['Value'].unit['kg/J'],
                                power_increase_ratio) # returns an array of kg of H2 produced during each hour
            self.hourly_h2_production[year] = Quantity(h2_produced, 'kg')

            yearly_data_year.append(year)
            yearly_data_production.append(np.sum(h2_produced))
            yearly_data_duration.append(hours_equivalent_full_Production)

        self.yearly_data_year = Quantity(np.asarray(yearly_data_year), '-')
        self.yearly_data_production = Quantity(np.asarray(yearly_data_production), 'kg')
        self.yearly_data_duration = Quantity(np.asarray(yearly_data_duration), 'h')

        self.yearly_h2_production = self.yearly_data_production
        
        self.yearly_data_unused_energy = yearly_data_unused_energy
        self.yearly_data_unused_energy_daily = yearly_data_unused_energy_daily
        self.yearly_data_missing_energy = yearly_data_missing_energy


    def outlet_flow_properties(self):
        '''Establishes the thermophysical characteristics of the fluid leaving the reactor, for downstream process sizing'''

        outlet_temperature_degC = 85 # hardcoded for the moment, could become an input later
        self.outlet_temperature = {round(year): Quantity(outlet_temperature_degC *np.ones_like(self.hourly_h2_production[0].unit['kg']), 
                                        'degC') 
                                    for year in self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-']}
        
        self.outlet_pressure = Quantity(20, 'bar') # hardcoded for the moment, could become an input later

        # Assuming water vapour is saturated in the electrolyzer, determination of the water vapour pressure
        # since the temperature is constant, we only need to calculate the saturation pressure once
        psat = PP.Water_saturation_pressure(Quantity(outlet_temperature_degC, 'degC'))

        mol_fraction = {} # molar fraction of the gas mixture, assuming ideal gas, expressed in mol of species for a total amount of 1 mol 
        mol_fraction['H2O'] = Quantity(psat.unit['Pa']/self.outlet_pressure.unit['Pa'], '-')
    # The pressure that is not due to water is due to H2
        mol_fraction['H2'] = Quantity(1-mol_fraction['H2O'].unit['-'], '-')        

        _, outlet_mass_fraction = PP.Substance_to_mass(mol_fraction)

        # Converting the outlet mass fraction into a dict of arrays, then into a dict of years 
        self.outlet_mass_fraction = {'H2O': Quantity(outlet_mass_fraction['H2O'].unit['-'] 
                                                    * 
                                                    np.ones_like(self.hourly_h2_production[0].unit['kg']), 
                                                    '-'), 
                                    'H2': Quantity(outlet_mass_fraction['H2'].unit['-'] 
                                                    * 
                                                    np.ones_like(self.hourly_h2_production[0].unit['kg']), 
                                                    '-')
                                    }        
        self.outlet_mass_fraction = {round(year):self.outlet_mass_fraction for year in self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-']}

        smoothening_period = Quantity(1, 'h')
        self.hourly_mass_flow = {}

        for year in self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-']:			
            year = round(year)
            hourly_unsmoothened_output_kg = (self.hourly_h2_production[year].unit['kg']
                                            / 
                                            outlet_mass_fraction['H2'].unit['-']
                                            )            
            self.hourly_mass_flow[year] = Quantity(smoothened_production(hourly_unsmoothened_output_kg, round(smoothening_period.unit['h'])), 
                                                        'kg')
            
        # specific enthalpy at the outlet of the baggie
        h = PP.Enthalpy(T = Quantity(outlet_temperature_degC, 'degC'),
                        P = self.outlet_pressure, 
                        amount = outlet_mass_fraction,
                        phase = 'V', 
                        composition_basis = 'mass'
                        )
        
        h = Quantity(h.unit['J'] 
                    *
                    np.ones_like(self.hourly_h2_production[0].unit['kg']), 
                    'J/kg')
        self.outlet_enthalpy = {round(year):h for year in self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-']}

    def water_consumption(self):

        # Mass of water converted into hydrogen per year
        self.net_yearly_mass = Quantity(self.yearly_h2_production.unit['kg'] 
                                        *
                                        self.input_dict_resolved['Technical Operating Parameters and Specifications']['Operating capacity factor']['Value'].unit['-']
                                        *
                                        PP.MW['H2O'].unit['kg/mol']
                                        /
                                        PP.MW['H2'].unit['kg/mol'],
                                        'kg')
        
        # Mass of water to inject per year, due to conversion and evaporation 
        self.gross_yearly_mass = Quantity(1.5 # 3/2 factor becasue for each mole of H2 that leaves the electrolyzer, 0.5 mol O2 leaves as well. Each side has the same vapour fraction. So, for each water molecule leaving the system on H2 side, 0.5 water molecule leaves on O2 side
                                          *
                                          np.sum(self.hourly_mass_flow[0].unit['kg']
                                                    *
                                                    self.outlet_mass_fraction[0]['H2O'].unit['-']
                                                    )
                                        *
                                        self.input_dict_resolved['Technical Operating Parameters and Specifications']['Operating capacity factor']['Value'].unit['-']
                                        *
                                        np.ones_like(self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-'])
                                        +
                                        self.net_yearly_mass.unit['kg'],
                                        'kg')	        

def calculate_electrolyzer_power_demand(power_requirement_increase, nominal_power, year):
    '''Calculation of yearly increase in electrolyzer power demand.
    '''

    increase = (1. + power_requirement_increase) ** year
    demand = increase * nominal_power

    return demand, increase

def calculate_hydrogen_production(energy_consumption, conversion_efficiency, power_increase_ratio):
    '''Calculation of hydrogen production based on power consumption, conversion efficiency 
    and power increase.
    '''

    h2_production = energy_consumption * conversion_efficiency / power_increase_ratio

    return h2_production

def calculate_stack_replacement(operation_hours, replacement_time):
    '''Calculation of stack replacement frequency for electrolyzer.
    '''

    cumulative_running_time = np.cumsum(operation_hours.unit['h']) # operation_hours is a Quantity
    stack_usage = cumulative_running_time / replacement_time

    number_of_replacements = np.floor_divide(stack_usage[-1], 1)
    replacement_frequency = len(stack_usage) / (number_of_replacements + 1.)

    return Quantity(replacement_frequency, 'year'), Quantity(number_of_replacements, '-') # the inputs being : (hours of operation in the year, hours of operation before replacement), 
                                                # the result corresponds to the number of years between replacements

def calculate_number_of_units(unit_nominal_power, 
                            nominal_power, 
                            number_of_replacements):
    '''Calculation of number of electrolyzer BOP units and stacks.
    '''

    number_of_units = Quantity(np.ceil(nominal_power.unit['W'] 
                                    / unit_nominal_power.unit['W']), 
                            '-')
    number_of_stacks = Quantity(number_of_units.unit['-']
                                * (1 + number_of_replacements.unit['-']),
                                '-')

    return number_of_units, number_of_stacks