from pyH2A.Utilities.input_modification import read_textfile
from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
import pyH2A.Utilities.find_nearest as fn
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
import numpy as np
from pyH2A.Utilities.docstring_generation import generate_docstring

class Inflation_Plugin:

    def __init__(self, dcf, print_info, run = True):
        self._set_up(dcf)
        if run:
            self._run(dcf)

    def _set_up(self, dcf):

        self.functional_unit = dcf.functional_unit

        self.input_dict = {
            "Financial Input Values": {
                "Inflation rate": {
                    "Value": {
                        "type": {int, float},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "dimensionless",
                    },
                    "optional": False,
                    "description": "inflation factor"
                },
                "Current year for capital costs": {
                    "Value": {
                        "type": {int, float},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "dimensionless",
                    },
                    "optional": False,
                    "description": "current year capital costs"
                },     
                "Basis year": {
                    "Value": {
                        "type": {int, float},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "dimensionless",
                    },
                    "optional": False,
                    "description": "basis year for inflation calculation"
                },    
                "Reference year": {
                    "Value": {
                        "type": {int, float},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "dimensionless",
                    },
                    "optional": False,
                    "description": "reference year for inflation calculation"
                },                       
            },
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
        }

        self.output_dict = {
            "Inflation": {
                "Inflation factor full": {
                    "Value": {
                        "inserted_value": "inflation_factor_full",
                        "type": {np.ndarray},
        				"dimension": "dimensionless",                     
                    },
                    "optional": False,
                    "description": "Array containing the inflation factor for each year of the plant life, including construction and production"
                },                 
                "Inflation correction": {
                    "Value": {
                        "inserted_value": "inflation_correction",
                        "type": {float},
        				"dimension": "dimensionless",                     
                    },
                    "optional": False,
                    "description":"Correction factor applied to the inflation factors, to account for the time ofset between reference year and startup year"
                },      
                "CEPCI inflator": {
                    "Value": {
                        "inserted_value": "cepci_inflator",
                        "type": {float},
        				"dimension": "dimensionless",                     
                    },
                    "optional": False,
                    "description": "CEPCI inflation factor"
                },  
                "CI inflator": {
                    "Value": {
                        "inserted_value": "ci_inflator",
                        "type": {float},
        				"dimension": "dimensionless",                     
                    },
                    "optional": False,
                    "description": "CI inflation factor"
                }, 
                "Combined inflator": {
                    "Value": {
                        "inserted_value": "combined_inflator",
                        "type": {float},
        				"dimension": "dimensionless",               
                    },
                    "optional": False,
                    "description": "Sum of CEPCI and CI inflation factors"                  
                }, 
                "Labor inflator": {
                    "Value": {
                        "inserted_value": "labor_inflator",
                        "type": {float},
        				"dimension": "dimensionless",                     
                    },
                    "optional": False,
                    "description": "Cost of labor inflation factor"                  
                }, 
                "Chemical inflator": {
                    "Value": {
                        "inserted_value": "chemical_inflator",
                        "type": {float},
        				"dimension": "dimensionless",                     
                    },
                    "optional": False,
                    "description": "Cost of chemicals inflation factor"                  
                },                                                      
            }
        }
        
        summary = "Generation of a the necessary inflation-related quantities for other plugins."
        
        self.__class__.__doc__ = generate_docstring(
            summary,
            self.input_dict,
            self.output_dict
        )

    def _run(self, dcf):
        self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, 'Inflation_Plugin')

        self.inflation()

        output_inserter_function(self.output_dict,self,dcf,'Inflation_Plugin')

    def inflation(self):
        finance_dict = self.input_dict_resolved['Financial Input Values']

        # Read in the necessary lookup tables for inflation calculations
        plant_cost = read_textfile('pyH2A.Lookup_Tables~Plant_Cost_Index.csv', 
                                    delimiter = '	')
        gdp_deflator_price = read_textfile('pyH2A.Lookup_Tables~GDP_Implicit_Deflator_Price_Index.csv', 
                                            delimiter = '	')
        labor_price = read_textfile('pyH2A.Lookup_Tables~Labor_Index.csv', 
                                        delimiter = '	')
        chemical_price = read_textfile('pyH2A.Lookup_Tables~SRI_Chemical_Price_Index.csv', 
                                        delimiter = '	')

        # Find the indices of the years in the lookup tables that are closest to the years specified in the input dictionary
        plant_idx = fn.find_nearest(plant_cost, [finance_dict['Current year for capital costs']['Value'].unit['-'], 
                                                    finance_dict['Basis year']['Value'].unit['-']])
        gdp_idx = fn.find_nearest(gdp_deflator_price, [finance_dict['Reference year']['Value'].unit['-'], 
                                                        finance_dict['Current year for capital costs']['Value'].unit['-']])
        labor_idx = fn.find_nearest(labor_price, [finance_dict['Reference year']['Value'].unit['-'], 
                                                    finance_dict['Basis year']['Value'].unit['-']])
        chemical_idx = fn.find_nearest(chemical_price, [finance_dict['Reference year']['Value'].unit['-'], 
                                                        finance_dict['Basis year']['Value'].unit['-']])

        # Calculate the inflation factor
        inflation_rate = 1 + finance_dict['Inflation rate']['Value'].unit['-']

        # Calculate the different inflation factors and create corresponding Quantity objects and attributes
        self.inflation_factor_full = Quantity(inflation_rate 
                                              ** self.input_dict_resolved['Time']['Years']['Value']['Plant years relative'].unit['-'], 
                                    '-')
        self.inflation_correction = Quantity(inflation_rate 
                                             ** self.input_dict_resolved['Time']['Years']['Value']['Startup time offset'].unit['-'], 
                                    '-')
        self.cepci_inflator = Quantity(plant_cost[:,1][plant_idx[0]]
                                       /plant_cost[:,1][plant_idx[1]], 
                              '-')
        self.ci_inflator = Quantity(gdp_deflator_price[:,1][gdp_idx[0]]
                                    /gdp_deflator_price[:,1][gdp_idx[1]], 
                           '-')
        self.combined_inflator = Quantity(self.cepci_inflator.unit['-'] 
                                          * self.ci_inflator.unit['-'], 
                                 '-')
        self.labor_inflator = Quantity(labor_price[:,1][labor_idx[0]]
                                       /labor_price[:,1][labor_idx[1]], 
                              '-')
        self.chemical_inflator = Quantity(chemical_price[:,1][chemical_idx[0]]
                                          /chemical_price[:,1][chemical_idx[1]], 
                                '-')