from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.Physical_Properties.Physical_properties import Physical_properties as PP
import numpy as np

class Pump_Plugin:
    '''Simulation of cooling tower.
    '''


    def __init__(self, dcf, print_info, run = True, instance_suffix=None):
        self.instance_suffix = instance_suffix
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
            "Pump Hourly Liquid Mass@": {
                "<...>": {
                    "Value": {
                        "type": {dict},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "mass",
                    },
                    "optional": False,
                    "description": "Mass of liquid to pump. Yearly dict of hourly arrays."
                },                       
            },                     
            "Pump@": {    
				"Is independent from year":  {
                    "Value": {
                        "type": {int,float,},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "dimensionless",
                    },
                    "optional": True,
                    "description": "if True: all the years behave identically. Else: each year has to be solved. Default: equal to the valie taken from the Main stream"
                },	                             
                "Efficiency": {
                    "Value": {
                        "type": {int, float},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "dimensionless",
                    },
                    "optional": False,
                    "description": "Electric energy needed per pumping energy."
                }, 
                "Nominal pressure drop": {
                    "Value": {
                        "type": {int, float},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "pressure",
                    },
                    "optional": False,
                    "description": "Maximum thermal power of each cooling tower unit. Used for sizing."
                },                   
                "Minimum flowrate ratio": {
                    "Value": {
                        "type": {int, float},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "dimensionless",
                    },
                    "optional": False,
                    "description": "The flowrate can't go below the nominal flowrate * the minimum power ratio."
                },                        
                "Nominal flowrate per unit": {
                    "Value": {
                        "type": {int, float},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "mass/time",
                    },
                    "optional": False,
                    "description": "Maximum flowrate allowed per pump."
                },                                   
                "Steel mass per unit": {
                    "Value": {
                        "type": {int, float},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "mass",
                    },
                    "optional": False,
                    "description": "Mass of steel constituting a pump unit."
                },                                                            
            }, 
            "Main Stream": {
				"Is independent from year":  {
                    "Value": {
                        "type": {int,float,},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "dimensionless",
                    },
                    "optional": True,
                    "description": "if True: all the years behave identically. Else: each year has to be solved."
                },
            },                
        }

        self.output_dict = {
            "Pump@": {
                 "Number of units": {
                    "Value": {
                        "inserted_value": "number_units",
                        "type": {int, float},
                        "dimension": "dimensionless",
                    },
                    "optional": False,
                    "description": "Number of pump units required to handle the desired power."
                },   
                 "Hourly pumping energy": {
                    "Value": {
                        "inserted_value": "hourly_pumping_energy",
                        "type": {dict,},
                        "dimension": "energy",
                    },
                    "optional": False,
                    "description": "Dictionary of years: hourly energy required to pump the cooling liquid."
                },                                                                                             
                "Yearly pumping energy": {
                    "Value": {
                        "inserted_value": "yearly_pumping_energy",
                        "type": {np.ndarray,},
                        "dimension": "energy",
                    },
                    "optional": False,
                    "description": "Energy for the pumping of the cooling liquid used per year, accounting for the operating capacity factor."
                },    
                "Total pumping energy": {
                    "Value": {
                        "inserted_value": "total_pumping_energy",
                        "type": {float,},
                        "dimension": "energy",
                    },
                    "optional": False,
                    "description": "Energy for the pumping of the cooling liquid used during plant lifetime."
                }, 
                "Total steel mass": {
                    "Value": {
                        "inserted_value": "total_steel",
                        "type": {int, float}, 
                        "dimension": "mass",
                    },
                    "description": "Total mass of steel of the pump.",
                    "optional": False,
                },                  
            },   
        }

    def _run(self, dcf):
        plugin_name = 'Pump_Plugin'
        self.pump_name = 'Pump'
        self.pump_hourly_mass = 'Pump Hourly Liquid Mass'
        if self.instance_suffix is not None:
            plugin_name = f'{plugin_name} @{self.instance_suffix}'
            self.pump_name = f'{self.pump_name} {self.instance_suffix}'
            self.pump_hourly_mass = f'{self.pump_hourly_mass} {self.instance_suffix}'
            
        self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, plugin_name)

        self.calculate_pump()

        output_inserter_function(self.output_dict, self, dcf, plugin_name) 
                
    def calculate_pump(self):
        '''Calculation of the number of pumps needed to meet the peak demand, 
            and subsequent consumptions of electricity.
        '''
        specific_volume = PP.Volume(T= Quantity(25, 'degC'), 
                                    P = Quantity(1, 'bar'), 
                                    amount = {'H2O': Quantity(1, 'kg')}, # water for the moment, we can handle other fluids if necesary in the future
                                    phase = 'L', 
                                    composition_basis= 'mass')
       
        hourly_coolant_mass_kg = {}        
        self.hourly_pumping_energy = {}
        self.yearly_pumping_energy = np.zeros_like(self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-'])
        maximum_hourly_flow_kg = 0

        if 'Is independent from year' in self.input_dict_resolved[self.pump_name]:
            is_independent_from_year = bool(self.input_dict_resolved[self.pump_name]['Is independent from year']['Value'].unit['-'])
        elif 'Is independent from year' in self.input_dict_resolved['Main Stream']: 
            is_independent_from_year = bool(self.input_dict_resolved['Main Stream']['Is independent from year']['Value'].unit['-'])
        else:
            is_independent_from_year = False

        if is_independent_from_year is True:
            self.years = np.array([0])
        else: 
            self.years = self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-']                  


        for year in self.years:
            year = round(year)

            hourly_coolant_mass_kg[year] = np.zeros(8760)
            for flow in self.input_dict_resolved[self.pump_hourly_mass].keys():
                hourly_coolant_mass_kg[year] += self.input_dict_resolved[self.pump_hourly_mass][flow]['Value'][year].unit['kg']
            
            maximum_hourly_flow_kg = max(np.max(hourly_coolant_mass_kg[year]), 
                                               maximum_hourly_flow_kg)

        number_units_theoretical =  maximum_hourly_flow_kg / self.input_dict_resolved[self.pump_name]['Nominal flowrate per unit']['Value'].unit['kg/h']
        self.number_units = Quantity(np.ceil(number_units_theoretical).astype(int), '-')

        minimum_hourly_flow_kg = (self.input_dict_resolved[self.pump_name]['Minimum flowrate ratio']['Value'].unit['-'] 
                                    * 
                                    self.input_dict_resolved[self.pump_name]['Nominal flowrate per unit']['Value'].unit['kg/h']
                                    *
                                    self.number_units.unit['-'])

        for year in self.years:
            year = round(year)
            actual_flowrate = np.maximum(minimum_hourly_flow_kg, hourly_coolant_mass_kg[year])
            self.hourly_pumping_energy[year] = Quantity(self.input_dict_resolved[self.pump_name]['Nominal pressure drop']['Value'].unit['Pa'] 
                                                        * 
                                                        maximum_hourly_flow_kg
                                                        *
                                                        specific_volume.unit['m3'] # per kilogram
                                                        *
                                                        (actual_flowrate 
                                                        /
                                                        maximum_hourly_flow_kg)**3
                                                        / 
                                                        self.input_dict_resolved[self.pump_name]['Efficiency']['Value'].unit['-'], 
                                                        'J')
            
            self.yearly_pumping_energy[year] = np.sum(self.hourly_pumping_energy[year].unit['J']) * self.input_dict_resolved['Technical Operating Parameters and Specifications']['Operating capacity factor']['Value'].unit['-']

        if is_independent_from_year is True:
            self.hourly_pumping_energy = {round(year): self.hourly_pumping_energy[0] for year in self.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-']}
            self.yearly_pumping_energy = self.yearly_pumping_energy[0]*self.input_dict_resolved['Time']['Years']['Value']['Operation years ones'].unit['-']

        self.total_pumping_energy = Quantity(np.sum(self.yearly_pumping_energy), 'J')
        self.yearly_pumping_energy = Quantity(self.yearly_pumping_energy, 'J')

        self.total_steel = Quantity(self.number_units.unit['-']
                                    *
                                    self.input_dict_resolved[self.pump_name]['Steel mass per unit']['Value'].unit['kg']
                                    , 
                                    'kg')

        print('self.total_pumping_energy kWh ', self.total_pumping_energy.unit['kWh'])