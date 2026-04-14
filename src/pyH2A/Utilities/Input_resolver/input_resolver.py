import pprint as pp
import numpy as np

from pyH2A.Utilities.Input_resolver.check_functions import check_type, check_if_in_options, check_dimension, check_bounds
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.input_modification import process_input

from tests.Utilities.input_resolver.input_resolver_test_data import DummyDCF, input_dict, input_dict_resolved

# This marker indicates either a table group (when in top_key) or a wildcard row (when in middle_key). 
# It is used to indicate that the number of tables/rows is flexible and can be determined based on the content of dcf_class.inp
WILDCARD_MARKER = "<...>"

# These keys are not considered when constructing the resolved values 
SPECIAL_BOTTOM_KEYS = ['description', 'optional']

# Key indicating if a value is optional or not
OPTIONAL_KEY = 'optional'

# Keys for value-unit pairs 
VALUE_KEY = "Value"
UNIT_KEY = "Unit"
VALUE_SUFFIX = "_Value"
UNIT_SUFFIX = "_Unit"

# Specifications (checks) for values 
TYPE_KEY = 'type'
BOUNDS_KEY = 'bounds'
DIMENSION_KEY = 'dimension'
OPTIONS_KEY = 'options'
PATH_KEY = 'path'

def _identify_bottom_keys(row_dict):
    '''
    Identify the bottom keys relevant for processing (value-unit pairs and standalone keys)

    Example
    -------
    For a row_dict like this:

    {
        'Usage_Value': 1500,
        'Usage_Unit': 'kWh/kg',
        'Cost_Value': 200,
        'Cost_Unit': 'USD/kWh/day',
        'Type': 'natural_gas'
    }

    The function would return:

    [
        ['Usage_Value', 'Usage_Unit'],
        ['Cost_Value', 'Cost_Unit'],
        ['Type']
    ]   
    '''
    
    result = []
    processed_keys = set(SPECIAL_BOTTOM_KEYS) # special bottom keys are directly removed from consideration
    
    # First pass: find Value/Unit pairs
    for key in row_dict:

        # Check for direct Value/Unit pair
        if key == VALUE_KEY and UNIT_KEY in row_dict:
            result.append([key, UNIT_KEY])
            processed_keys.update([key, UNIT_KEY])

        # Check for Value/Unit pairs indicated by suffixes
        elif key.endswith(VALUE_SUFFIX):
            prefix = key[:-len(VALUE_SUFFIX)]
            unit_key = prefix + UNIT_SUFFIX

            if unit_key in row_dict:
                result.append([key, unit_key])
                processed_keys.update([key, unit_key])
                
    # Second pass: append any remaining standalone keys
    for key in row_dict:
        if key not in processed_keys:
            result.append([key])
            
    return result

def _get_specification_and_retrieved_value(top_key, 
                                           middle_key, 
                                           bottom_key, 
                                           row_dict,
                                           dcf_class):
    '''
    Helper function to retrieve specification and retrieved value for a given key combination
    Raises KeyError if key combination is not found in dcf_class.inp
    '''

    specification = row_dict[bottom_key]

    try:
        retrieved_value = dcf_class.inp[top_key][middle_key][bottom_key]
    except KeyError as e:
        raise KeyError(f"Key {e} not found in dcf.inp at location '{top_key} > {middle_key} > {bottom_key}'") from e

    return specification, retrieved_value

def _perform_checks_on_quantity(quantity,
                                value_specification,
                                unit_specification,
                                top_key,
                                middle_key,
                                bottom_key):
    
    # 1. Always check dimension match (DIMENSION_KEY must be present in unit_specification)
    check_dimension(top_key, 
                    middle_key, 
                    bottom_key, 
                    quantity, 
                    unit_specification[DIMENSION_KEY])
    
    # 2. Optionally check bounds (with respect to value in base unit),
    # if BOUNDS_KEY is present in value_specification 
    if BOUNDS_KEY in value_specification:
        check_bounds(top_key, 
                     middle_key, 
                     bottom_key, 
                     quantity, 
                     value_specification[BOUNDS_KEY])
    

def _create_quantity_and_validate(value_retrieved, 
                                  unit_retrieved, 
                                  value_specification, 
                                  unit_specification, 
                                  top_key, 
                                  middle_key, 
                                  bottom_key):
    """
    Recursively processes a retrieved value (float, int, np.ndarray, or dict) and its retrieved unit, 
    creates Quantity objects, checks dimensions, and validates bounds.
    Returns the parsed structure with Quantity objects at the bottom level.
    """

    # Recursively traverse nested dictionaries
    if isinstance(value_retrieved, dict):
        processed_dict = {}

        for key, value in value_retrieved.items():
            processed_dict[key] = _create_quantity_and_validate(
                value, 
                unit_retrieved, 
                value_specification, 
                unit_specification, 
                top_key, 
                middle_key, 
                bottom_key
            )
        return processed_dict

    # Upon finding numerical values, run our processing
    elif isinstance(value_retrieved, (float, int, np.ndarray)):
        # 1. Create Quantity object
        quantity = Quantity(value_retrieved, unit_retrieved)
        
        # 2. Perform dimension and bounds checks on quantity
        _perform_checks_on_quantity(quantity, 
                                    value_specification, 
                                    unit_specification, 
                                    top_key, 
                                    middle_key, 
                                    bottom_key)
                        
        # 3. Ultimately return actual quantity piece
        return quantity
    
    else:
        raise TypeError(
            f"'{top_key} > {middle_key} > {bottom_key}': "
            f"Unsupported type '{type(value_retrieved)}' when trying to resolve quantity value."
        )

## Value-level (bottom_key) resolver functions

def value_resolver_function(top_key, 
                            middle_key, 
                            bottom_key, 
                            row_dict, 
                            dcf_class,
                            return_specification = True):
    '''
    Retrieve value specification and value.
    Perform checks if retrieved value is of specified type
    (and if applicable, within specified options).
    '''

    # Retrieve value specification, check if PATH_KEY is present, setting
    # specific_path_key accordingly (if not present, default to 'Path')
    value_specification = row_dict[bottom_key]
    if PATH_KEY in value_specification:
        specific_path_key = value_specification[PATH_KEY]
    else:
        specific_path_key = 'Path'

    # Process input (resolving paths etc.)
    process_input(dcf_class.inp, 
                  top_key, 
                  middle_key,
                  bottom_key,
                  path_key = specific_path_key,
                  add_processed = False)

    value_specification, value_retrieved = _get_specification_and_retrieved_value(top_key, 
                                                                                 middle_key, 
                                                                                 bottom_key, 
                                                                                 row_dict, 
                                                                                 dcf_class)
    
    # If retrieved value is a Quantity,
    # base value is extracted for checks, but the original Quantity object is kept for return (after checks are performed)
    if isinstance(value_retrieved, Quantity):
        base_value = value_retrieved.base_value
    else:
        base_value = value_retrieved
    
    # Always check if the value is of the expected type
    # 'TYPE_KEY' must be present in value_specification
    check_type(top_key, 
               middle_key, 
               bottom_key, 
               base_value, 
               value_specification[TYPE_KEY])

    # Optionally check if the value is within expected options (for categorical values)
    if OPTIONS_KEY in value_specification:
        check_if_in_options(top_key,
                            middle_key,
                            bottom_key,
                            base_value,
                            value_specification[OPTIONS_KEY])
        
    if return_specification:
        return value_specification, value_retrieved
    else:
        return value_retrieved
            
def unit_resolver_function(top_key, 
                           middle_key, 
                           bottom_key, 
                           row_dict, 
                           dcf_class):
    '''
    Resolve unit
    '''
    
    unit_specification, unit_retrieved = _get_specification_and_retrieved_value(top_key,
                                                                               middle_key,
                                                                               bottom_key,
                                                                               row_dict,
                                                                               dcf_class)
    
    return unit_specification, unit_retrieved
     
def value_with_unit_resolver_function(top_key, 
                                      middle_key, 
                                      bottom_key_group, 
                                      row_dict, 
                                      dcf_class):
    '''
    Resolve value with unit 
    Decision between directly getting Quantity object (if retrieved value is already a Quantity) or
    creating Quantity object from retrieved value and unit (if retrieved value is numerical).
    Throws error if retrieved value is of unsupported type (not Quantity, numerical or string).
    '''

    value_specification, value_retrieved = value_resolver_function(top_key, 
                                                                   middle_key, 
                                                                   bottom_key_group[0], 
                                                                   row_dict, 
                                                                   dcf_class)
    
    # If retrieved value is already a Quantity, checks are performed based on specifications 
    # and the original Quantity object is returned 
    if isinstance(value_retrieved, Quantity):
        unit_specification = row_dict[bottom_key_group[1]]
        
        _perform_checks_on_quantity(value_retrieved,
                                    value_specification,
                                    unit_specification,
                                    top_key,
                                    middle_key,
                                    bottom_key_group[0],)
        
        return value_retrieved

    # If retrieved value is numerical, quantity object is created, 
    # checks are performed and newly created quantity object is returned
    if isinstance(value_retrieved, (int, float, np.ndarray, dict)):

        unit_specification, unit_retrieved = unit_resolver_function(top_key, 
                                                                    middle_key, 
                                                                    bottom_key_group[1], 
                                                                    row_dict, 
                                                                    dcf_class)


        # Create quantities and check them based on specifications 
        resolved_quantity = _create_quantity_and_validate(
            value_retrieved,
            unit_retrieved,
            value_specification,
            unit_specification,
            top_key,
            middle_key,
            bottom_key_group[0]
            )
        
        return resolved_quantity
    
    # If retrieved value is string, it is directly returned (after type check performed in value_resolver_function,
    # which sucessfuly confirmed that string is expected for this value)
    elif isinstance(value_retrieved, str):
        return value_retrieved
    
    # If type is something else, raise error.
    else:
        raise TypeError(
            f"'{top_key} > {middle_key} > {bottom_key_group[0]}': "
            f"Unsupported type '{type(value_retrieved)}' when trying to resolve value with unit."
        )


## Row-level (middle_key) resolver functions
def row_resolver_function(top_key, middle_key, row_dict, dcf_class):
    '''
    Regular row resolver function, 
    decision between resolving values with units or simply values
    '''

    is_optional = row_dict.get(OPTIONAL_KEY, False)
    row_present = middle_key in dcf_class.inp[top_key]

    # Handling if row is not present in dcf_class.inp
    if row_present is False:
        if is_optional is False: # If row is not optional and not present in dcf_class.inp, raise error
            raise KeyError(f"Row '{middle_key}' in table '{top_key}' is required but not found in dcf.inp")
        else: 
            return None # return None if row is not present but optional

    resolved_row = {}

    # Identify bottom keys (value-unit pairs and standalone keys) for the given row_dict
    bottom_keys = _identify_bottom_keys(row_dict)

    for bottom_key_group in bottom_keys:

        # Length == 2 indicates value-unit pair, so resolve value and unit together
        if len(bottom_key_group) == 2:
            resolved_quantity = value_with_unit_resolver_function(top_key, 
                                                                  middle_key, 
                                                                  bottom_key_group, 
                                                                  row_dict, 
                                                                  dcf_class)
            resolved_row[bottom_key_group[0]] = resolved_quantity
            
        
        # Length == 1 indicates standalone value, so resolve value only (typically triggered by non-numerical values)
        elif len(bottom_key_group) == 1:
            resolved_string = value_resolver_function(top_key, 
                                                     middle_key, 
                                                     bottom_key_group[0],
                                                     row_dict, 
                                                     dcf_class,
                                                     return_specification = False)
            resolved_row[bottom_key_group[0]] = resolved_string

        else:
            raise ValueError(f"Unexpected number of keys in bottom_key_group: {bottom_key_group}")
        
    # Explicitly mark the middle key as Processed now that all bottom keys are handled
    dcf_class.inp[top_key][middle_key]['Processed'] = 'Yes'    

    return resolved_row

def wildcard_row_resolver_function(top_key, row_dict, dcf_class):
    '''
    Resolver function for wildcard rows (going through all rows in dcf_class.inp[top_key])
    '''

    resolved_rows = {}
    
    # Go through all middle keys of dcf_class.inp[top_key] and resolve rows
    for middle_key in dcf_class.inp[top_key]:
        resolved_row = row_resolver_function(top_key, middle_key, row_dict, dcf_class)
        resolved_rows[middle_key] = resolved_row
    
    return resolved_rows


## Table-level (top_key) resolver functions
def table_resolver_function(top_key, table_dict, dcf_class):
    '''
    Regular table resolver function, 
    decision between regular rows and wildcard rows 
    (indicated by WILDCARD_MARKER in middle_key)
    '''
    
    # Check if there is at least one non-optional row in table_dict
    is_required = any(not row_dict.get(OPTIONAL_KEY, False) for row_dict in table_dict.values())
    table_present = top_key in dcf_class.inp

    # Handling if table is not present in dcf_class.inp
    if table_present is False:
        if is_required is True: 
            # If there is at least one non-optional row 
            # and top_key is not present in dcf_class.inp, raise error
            raise KeyError(f"Table '{top_key}' is required but not found in dcf.inp")
        else:
            return None # return None if table is not present but all rows are optional

    resolved_table = {}

    for middle_key, row_dict in table_dict.items():
        # Check if middle_key indicates wildcard row (flexible number of rows, middle_key is only placeholder), 
        # if so call wildcard row resolver function
        if WILDCARD_MARKER in middle_key:
            resolved_rows = wildcard_row_resolver_function(top_key, row_dict, dcf_class)
            resolved_table.update(resolved_rows)
        
        # If not, resolve row as normal
        else:
            resolved_row = row_resolver_function(top_key, middle_key, row_dict, dcf_class)

            if resolved_row is not None:
                resolved_table[middle_key] = resolved_row

    return resolved_table


def table_group_resolver_function(table_group_top_key, table_group_dict, dcf_class):
    '''
    Resolver function for table groups
    '''

    resolved_table_group = {}

    # Remove wildcard marker from table group key to get the actual table group name
    table_group_top_key = table_group_top_key.replace(WILDCARD_MARKER, "").strip()

    # Extract all tables in dcf_class.inp that belong to the table group indicated by table_group_top_key
    dcf_table_groups = {key: value for key, value in dcf_class.inp.items() if table_group_top_key in key}

    for table_key in dcf_table_groups:
        # Call table resolver function for each table in the table group
        resolved_table = table_resolver_function(table_key, table_group_dict, dcf_class)
        resolved_table_group[table_key] = resolved_table

    return resolved_table_group


## Top level resolver function
def input_resolver_function(input_dict, dcf_class, plugin_name):
    '''
    Top level resolver function, decision between table groups 
    (indicated by WILDCARD_MARKER) or regular tables 
    '''

    try:
        input_dict_resolved = {}

        for top_key, table_dict in input_dict.items():
            
            # Check if top_key indicates table group, if so call table group resolve
            if WILDCARD_MARKER in top_key:
                resolved_table_group = table_group_resolver_function(top_key, table_dict, dcf_class)
                input_dict_resolved.update(resolved_table_group)
            # If not, call table resolver
            else:
                resolved_table = table_resolver_function(top_key, table_dict, dcf_class)

                if resolved_table is not None:
                    input_dict_resolved[top_key] = resolved_table
        
        return input_dict_resolved
    
    # Catch exception and prepend plugin name to error message 
    except Exception as error:
        error_message = error.args[0] if getattr(error, 'args', None) else str(error)
        raise type(error)(f"[Plugin: {plugin_name}] {error_message}") from error


if __name__ == "__main__":
    DummyDCF_instance = DummyDCF()

    from timeit import default_timer as timer

    start_time = timer()

    input_dict_resolved = input_resolver_function(input_dict, DummyDCF_instance, 'TestPlugin')

    end_time = timer()

    pp.pprint(input_dict_resolved)

    print('--------------------------------')
    print(end_time - start_time, 's passed')


