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
        "Years": {
            "Value": {
                "inserted_value": "time_quantities_dict",
                "type": {dict},
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

        # Scalar values
   
        self.startup_time_offset = Quantity(startup_year - dictionary['ref year']['Value'].unit['-'], '-')

        # indices

        end_of_life = startup_year + plant_life_years     

        self.plant_years_relative = Quantity(np.arange(-construction_time_years, plant_life_years), '-')

        self.operation_years = Quantity(np.arange(startup_year, end_of_life), '-')

        self.operation_years_relative = Quantity(np.arange(0, plant_life_years), '-')

        # arrays of "ones"
        self.operation_years_ones = Quantity(np.ones(plant_life_years), '-')

        self.time_quantities_dict = {
             "Startup time offset" : self.startup_time_offset, 
             "Plant years relative" : self.plant_years_relative, 
             "Operation years" : self.operation_years,
             "Operation years relative" : self.operation_years_relative,
             "Operation years ones": self.operation_years_ones
        }

