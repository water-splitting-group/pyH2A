from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
import numpy as np

input_dict = {
    "Financial Input Values": {
        "plant life": {
            "Value": {
                "type": {int, float},
                "bounds": (0, None),
            },
            "Unit": {
                "dimension": "time",
            },
            "optional": False,
            "description": "Operating lifetime of the plant."
        },
        "Construction time": {
            "Value": {
                "type": {int, float},
                "bounds": (0, None),
            },
            "Unit": {
                "dimension": "time",
            },
            "optional": False,
            "description": "Construction time of the plant."
        },
        "startup year": {
            "Value": {
                "type": {int},
                "bounds": (0, None),
            },
            "Unit": {
                "dimension": "dimensionless",
            },
            "optional": False,
            "description": "year the operation starts"
        },      
        "ref year": {
            "Value": {
                "type": {int},
                "bounds": (0, None),
            },
            "Unit": {
                "dimension": "dimensionless",
            },
            "optional": False,
            "description": "reference year for startup"
        },             
    },
}

output_dict = {
    "Time": {
        "Startup time offset": {
            "Value": {
                "inserted_value": "startup_time_offset",
                "type": {int, float},
				"dimension": "time",                     
            },
            "optional": False,
        },   
        "Years": {
            "Value": {
                "inserted_value": "years",
                "type": {np.ndarray},
				"dimension": "dimensionless",                     
            },
            "optional": False,
        },             
        "Plant years": {
            "Value": {
                "inserted_value": "plant_years",
                "type": {np.ndarray},
				"dimension": "dimensionless",                     
            },
            "optional": False,
        },
        "Operation years": {
            "Value": {
                "inserted_value": "operation_years",
                "type": {np.ndarray},
				"dimension": "dimensionless",                     
            },
            "optional": False,
        },
        "Operation years relative": {
            "Value": {
                "inserted_value": "operation_years_relative",
                "type": {np.ndarray},
				"dimension": "dimensionless",                     
            },
            "optional": False,
        },        
        "Operation years ones": {
            "Value": {
                "inserted_value": "operation_years_ones",
                "type": {np.ndarray},
				"dimension": "dimensionless",                     
            },
            "optional": False,
        },
        "Construction years ones": {
            "Value": {
                "inserted_value": "construction_years_ones",
                "type": {np.ndarray},
				"dimension": "dimensionless",                     
            },
            "optional": False,
        },
        "Total years ones": {
            "Value": {
                "inserted_value": "total_years_ones",
                "type": {np.ndarray},
				"dimension": "dimensionless",                     
            },
            "optional": False,
        },    
        "Operation years ones padded": {
            "Value": {
                "inserted_value": "operation_years_ones_padded",
                "type": {np.ndarray},
				"dimension": "dimensionless",                     
            },
            "optional": False,
        },                   
    }
}


class Time_Plugin:

    def __init__(self, dcf, print_info):

        self.input_dict_resolved = input_resolver_function(input_dict, dcf, 'Time_Plugin')

        self.generate_time()

        output_inserter_function(output_dict,self,dcf,'Time_Plugin')

    def generate_time(self):
        dictionary = self.input_dict_resolved['Financial Input Values']

        construction_time_years = int(
            round(
                dictionary['Construction time']['Value'].unit['year']
            )
        )

        plant_life_years = int(
            round(
                dictionary['plant life']['Value'].unit['year']
            )
        )

        startup_year = int(
            round(
                dictionary['startup year']['Value'].unit['-']
            )
        )

        total_years = construction_time_years + plant_life_years

        # Scalar values
   
        self.startup_time_offset = Quantity(dictionary['startup year']['Value'].unit['-'] - dictionary['ref year']['Value'].unit['-'], 'year')

        # indices

        construction_start = startup_year - construction_time_years
        end_of_life = startup_year + plant_life_years     

        self.years = Quantity(np.arange(construction_start, end_of_life), '-')

        self.plant_years = Quantity(np.arange(-construction_time_years, plant_life_years), '-')

        self.operation_years = Quantity(np.arange(startup_year, end_of_life), '-')

        self.operation_years_relative = Quantity(np.arange(0, plant_life_years), '-')

        # arrays of "ones"
        self.operation_years_ones = Quantity(np.ones(plant_life_years), '-')

        self.construction_years_ones = Quantity(np.ones(construction_time_years), '-')

        self.total_years_ones = Quantity(np.ones(total_years), '-')

        # padded array

        self.operation_years_ones_padded = Quantity(
                                                np.concatenate([
                                                    np.zeros(construction_time_years), 
                                                    np.ones(plant_life_years)
                                                ])
                                            , '-')

