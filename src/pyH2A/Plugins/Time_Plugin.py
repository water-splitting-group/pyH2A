from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
import pyH2A.Utilities.find_nearest as fn
import numpy as np

input_dict = {
    "Construction": {
        "<...>": {
            "Value": {
                "type": {int, float},
                "bounds": (0, 1),
            },
            "Unit": {
                "dimension": "dimensionless",
            },
            "optional": False,
            "description": "Fraction of capital spent during each construction year."
        },
    }, 
    "Financial Input Values": {
        "Plant life": {
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
        "Assumed start-up year": {
            "Value": {
                "type": {int},
                "bounds": (0, None),
            },
            "Unit": {
                "dimension": "dimensionless",
            },
            "optional": False,
            "description": "Year the operation starts"
        },      
        "Reference year": {
            "Value": {
                "type": {int},
                "bounds": (0, None),
            },
            "Unit": {
                "dimension": "dimensionless",
            },
            "optional": False,
            "description": "Reference year for startup"
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
            "description": "Dictionary containing all the year-related variables that are needed in other plugins.",
            "optional": False,
        },   
    }
}

          
class Time_Plugin:
    '''Generation of a unique dictionary contianing all the necessary time-related arrays and values for other plugins.
    All the quantities are dimensionless, no conversion being expected, and the years play the role of indexes rather than durations.


    Parameters
    ----------
    Construction > [...] > Value : int or float
        Fraction of capital spent during each construction year. Serves to determine the duration of the construction.
    Financial Input Values > Plant life > Value : int or float
        Operating lifetime of the plant.
    Financial Input Values > Assumed start-up year > Value : int
        Year the operation starts.
    Financial Input Values > Reference year > Value : int
        Reference year for startup.        
    
    Returns
    -------
    Time > Years > Value : dict
        Dictionary containing all the year-related variables that are needed in other plugins.
        Startup time offset: the offset between the reference year and the startup year (scalar)
        Plant years relative: array of indexes representing the years involved in the plant life, 0 being the year production starts
        Operation years: Array containing the calendar years during which production takes place
        Operation years relative: array of indexes representing the years during which production takes place, 0 being the year production starts
        Start index: relative year of startup
        Operation years ones: array of ones, of length equal to the number of production years        
        Analysis years ones: array of ones, of length equal to the construciton time + the number of production years        
        Construction years ones: array of ones, of length equal to the number of construction years        

    '''

    def __init__(self, dcf, print_info):
        self.input_dict_resolved = input_resolver_function(input_dict, dcf, 'Time_Plugin')

        self.generate_time()

        output_inserter_function(output_dict,self, dcf, 'Time_Plugin')

    def generate_time(self):
        # Getting finance dict data and construction time in year (by getting length of construction table)
        finance_dict = self.input_dict_resolved['Financial Input Values']
        construction_time_years = len(self.input_dict_resolved['Construction'])

        # Converting plant life to years (int) and converting start-up year to int (for indexing purposes)
        plant_life_years = int(round(finance_dict['Plant life']['Value'].unit['year'])) 
        startup_year = int(round(finance_dict['Assumed start-up year']['Value'].unit['-']))

        # Calculating the total number of years involved in the analysis (construction + operation)
        analysis_years = construction_time_years + plant_life_years

        # Calculating the end of life year based on the startup year and plant life
        end_of_life_year = startup_year + plant_life_years 

        # Calculating the startup time offset, plant years relative, operation years, operation years relative, and start index
        startup_time_offset = Quantity(startup_year 
                                       - finance_dict['Reference year']['Value'].unit['-'], 
                              '-')
        plant_years_relative = Quantity(np.arange(-construction_time_years, 
                                                  plant_life_years), 
                               '-')
        operation_years = Quantity(np.arange(startup_year, 
                                             end_of_life_year), 
                          '-')
        operation_years_relative = Quantity(np.arange(0, 
                                                      plant_life_years), 
                                '-')
        start_idx = Quantity(fn.find_nearest(plant_years_relative.unit['-'], 0)[0], 
                             '-')

        # Arrays of ones
        operation_years_ones = Quantity(np.ones(plant_life_years), 
                               '-')
        construction_years_ones = Quantity(np.ones(construction_time_years), 
                                  '-')
        analysis_years_ones = Quantity(np.ones(analysis_years), 
                              '-')

        # generation of the final dictionary
        self.time_quantities_dict = {
             "Startup time offset" : startup_time_offset, 
             "Plant years relative" : plant_years_relative, 
             "Operation years" : operation_years,
             "Operation years relative" : operation_years_relative,
             "Start index" : start_idx,
             "Operation years ones": operation_years_ones, 
             "Analysis years ones": analysis_years_ones,
             "Construction years ones": construction_years_ones, 
        }

