from pyH2A.Utilities.input_modification import read_textfile
from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
import pyH2A.Utilities.find_nearest as fn
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
import numpy as np

input_dict = {
    "Financial Input Values": {
        "inflation": {
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
        "current year capital costs": {
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
        "basis year": {
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
        "ref year": {
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

output_dict = {
    "Inflation": {
        "Inflation factor full": {
            "Value": {
                "inserted_value": "inflation_factor_full",
                "type": {np.ndarray},
				"dimension": "dimensionless",                     
            },
            "optional": False,
        },                 
        "Inflation correction": {
            "Value": {
                "inserted_value": "inflation_correction",
                "type": {float},
				"dimension": "dimensionless",                     
            },
            "optional": False,
        },      
        "CEPCI inflator": {
            "Value": {
                "inserted_value": "cepci_inflator",
                "type": {float},
				"dimension": "dimensionless",                     
            },
            "optional": False,
        },  
        "CI inflator": {
            "Value": {
                "inserted_value": "ci_inflator",
                "type": {float},
				"dimension": "dimensionless",                     
            },
            "optional": False,
        }, 
        "Combined inflator": {
            "Value": {
                "inserted_value": "combined_inflator",
                "type": {float},
				"dimension": "dimensionless",                     
            },
            "optional": False,
        }, 
        "Labor inflator": {
            "Value": {
                "inserted_value": "labor_inflator",
                "type": {float},
				"dimension": "dimensionless",                     
            },
            "optional": False,
        }, 
        "Chemical inflator": {
            "Value": {
                "inserted_value": "chemical_inflator",
                "type": {float},
				"dimension": "dimensionless",                     
            },
            "optional": False,
        },                                                      
    }
}


class Inflation_Plugin:

    def __init__(self, dcf, print_info):

        self.input_dict_resolved = input_resolver_function(input_dict, dcf, 'Inflation_Plugin')

        self.inflation()

        output_inserter_function(output_dict,self,dcf,'Inflation_Plugin')

    def inflation(self):
        dictionary = self.input_dict_resolved['Financial Input Values']

        inflation_rate = 1 + dictionary['inflation']['Value'].unit['-']

        self.inflation_factor_full = Quantity(inflation_rate ** self.input_dict_resolved['Time']['Years']['Value']['Plant years relative'].unit['-'], '-')

        self.inflation_correction = Quantity(inflation_rate ** self.input_dict_resolved['Time']['Years']['Value']['Startup time offset'].unit['-'], '-')

        plant_cost = read_textfile('pyH2A.Lookup_Tables~Plant_Cost_Index.csv', 
                                    delimiter = '	')
        gdp_deflator_price = read_textfile('pyH2A.Lookup_Tables~GDP_Implicit_Deflator_Price_Index.csv', 
                                            delimiter = '	')
        labor_price = read_textfile('pyH2A.Lookup_Tables~Labor_Index.csv', 
                                        delimiter = '	')
        chemical_price = read_textfile('pyH2A.Lookup_Tables~SRI_Chemical_Price_Index.csv', 
                                        delimiter = '	')

        plant_idx = fn.find_nearest(plant_cost, [dictionary['current year capital costs']['Value'].unit['-'], 
                                                    dictionary['basis year']['Value'].unit['-']])
        gdp_idx = fn.find_nearest(gdp_deflator_price, [dictionary['ref year']['Value'].unit['-'], 
                                                        dictionary['current year capital costs']['Value'].unit['-']])
        labor_idx = fn.find_nearest(labor_price, [dictionary['ref year']['Value'].unit['-'], 
                                                    dictionary['basis year']['Value'].unit['-']])
        chemical_idx = fn.find_nearest(chemical_price, [dictionary['ref year']['Value'].unit['-'], 
                                                        dictionary['basis year']['Value'].unit['-']])

        self.cepci_inflator = Quantity(plant_cost[:,1][plant_idx[0]]/plant_cost[:,1][plant_idx[1]], '-')
        self.ci_inflator = Quantity(gdp_deflator_price[:,1][gdp_idx[0]]/gdp_deflator_price[:,1][gdp_idx[1]], '-')
        self.combined_inflator = Quantity(self.cepci_inflator.unit['-'] * self.ci_inflator.unit['-'], '-')
        self.labor_inflator = Quantity(labor_price[:,1][labor_idx[0]]/labor_price[:,1][labor_idx[1]], '-')
        self.chemical_inflator = Quantity(chemical_price[:,1][chemical_idx[0]]/chemical_price[:,1][chemical_idx[1]], '-')