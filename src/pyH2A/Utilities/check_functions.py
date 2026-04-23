import numpy as np
from pyH2A.Utilities.Unit_handler.quantity import Quantity

def check_type(top_key,
               middle_key,
               bottom_key,
               value, 
               expected_type):
    '''
    Check if value is of expected type. Raises TypeError if not.
    '''
    if isinstance(expected_type, set):
        expected_type = tuple(expected_type)
        
    if not isinstance(value, expected_type):
        raise TypeError(f"'{top_key} > {middle_key} > {bottom_key}' (entry: '{value}'): Expected {expected_type}, but got {type(value)}")

def check_if_in_options(top_key,
                        middle_key,
                        bottom_key,
                        value, 
                        expected_options):
    '''
    Check if value is in expected options. Raises ValueError if not.
    '''
    if value not in expected_options:
        raise ValueError(f"'{top_key} > {middle_key} > {bottom_key}' (entry: '{value}'): Expected one of {expected_options}, but got '{value}'")
    
def check_dimension(top_key,
                    middle_key,
                    bottom_key,
                    value : Quantity, 
                    expected_dimension):
    '''
    Check if value has expected dimension. Raises ValueError if not.
    '''

    if value.dimension.replace(' ', '') != expected_dimension.replace(' ', ''):
        raise ValueError(f"'{top_key} > {middle_key} > {bottom_key}' (entry: '{value}'): Expected dimension '{expected_dimension}', but got '{value.dimension}'")

def check_bounds(top_key,
                 middle_key,
                 bottom_key,
                 value : Quantity, 
                 bounds):
    '''
    Check if value is within bounds. Raises ValueError if not.
    '''

    lower_bound, upper_bound = bounds
    base_value = value.base_value
    
    if lower_bound is not None and np.any(base_value < lower_bound):
        raise ValueError(
            f"'{top_key} > {middle_key} > {bottom_key}' (entry: {value}): "
            f"Base value {base_value} is below the lower bound of {lower_bound}."
        )
    if upper_bound is not None and np.any(base_value > upper_bound):
        raise ValueError(
            f"'{top_key} > {middle_key} > {bottom_key}' (entry: {value}): "
            f"Base value {base_value} is above the upper bound of {upper_bound}."
        )

    if bounds is None:
        return
    
