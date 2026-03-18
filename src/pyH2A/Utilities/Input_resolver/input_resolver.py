import pprint as pp

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
LENGTH_KEY = 'length'



### Missing: applying process table ### 

### Next step: implementing modular checker functions (checking bounds, checking type, checking options, checking dimension)

def _identify_bottom_keys(row_dict):
    '''
    Identify the bottom keys relevant for processing (value-unit pairs and standalone keys)
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

def _get_specification_and_retrieved_value(top_key, middle_key, bottom_key, row_dict, dcf_class):
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


## Value-level (bottom_key) resolver functions

def value_resolver_function(top_key, middle_key, bottom_key, row_dict, dcf_class):
    pass



def value_with_unit_resolver_function(top_key, middle_key, bottom_key_group, row_dict, dcf_class):

    value_specification, value_retrieved = _get_specification_and_retrieved_value(top_key, 
                                                                                 middle_key, 
                                                                                 bottom_key_group[0], 
                                                                                 row_dict, 
                                                                                 dcf_class)
    
    print(value_retrieved)
    
    unit_specification, unit_retrieved = _get_specification_and_retrieved_value(top_key,
                                                                               middle_key,
                                                                               bottom_key_group[1],
                                                                               row_dict,
                                                                               dcf_class)


    pass


## Row-level (middle_key) resolver functions
def row_resolver_function(top_key, middle_key, row_dict, dcf_class):
    '''
    Regular row resolver function, 
    decision between resolving values with units or simply values
    '''

    bottom_keys = _identify_bottom_keys(row_dict)

    for bottom_key_group in bottom_keys:

        # Length == 2 indicated value-unit pair, so resolve value and unit together
        if len(bottom_key_group) == 2:
            resolved_value_with_unit = value_with_unit_resolver_function(top_key, middle_key, bottom_key_group, row_dict, dcf_class)
        
        # Length == 1 indicates standalone value, so resolve value only
        elif len(bottom_key_group) == 1:
            resolved_value = value_resolver_function(top_key, middle_key, bottom_key_group[0], row_dict, dcf_class)

        else:
            raise ValueError(f"Unexpected number of keys in bottom_key_group: {bottom_key_group}")

    return {}

def wildcard_row_resolver_function(top_key, row_dict, dcf_class):
    '''
    Resolver function for wildcard rows (going through all rows in dcf_class.inp[top_key])
    '''

    resolved_rows = {}
    
    # Go through all middle keys of dcf_class.inp[top_key] and resolve rows
    for middle_key in dcf_class.inp[top_key]:
        resolved_row = row_resolver_function(top_key, middle_key, row_dict, dcf_class)
        resolved_rows.update(resolved_row)
    
    return resolved_rows


## Table-level (top_key) resolver functions
def table_resolver_function(top_key, table_dict, dcf_class):
    '''
    Regular table resolver function, 
    decision between regular rows and wildcard rows 
    (indicated by WILDCARD_MARKER in middle_key)
    '''
    
    resolved_table = {}

    for middle_key, row_dict in table_dict.items():

        # Check if middle_key indicates wildcard row (flexible number of rows, middle_key is only placeholder), 
        # if so call wildcard row resolver function
        if WILDCARD_MARKER in middle_key:
            resolved_rows = wildcard_row_resolver_function(top_key, row_dict, dcf_class)
        
        # If not, resolve row as normal
        else:
            resolved_row = row_resolver_function(top_key, middle_key, row_dict, dcf_class)

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
        resolved_table_group.update(resolved_table)

    return resolved_table_group


## Top level resolver function
def input_resolver_function(input_dict, dcf_class):
    '''
    Top level resolver function, decision between table groups 
    (indicated by WILDCARD_MARKER) or regular tables 
    '''

    input_dict_resolved = {}

    for top_key, table_dict in input_dict.items():
        
        # Check if top_key indicates table group, if so call table group resolve
        if WILDCARD_MARKER in top_key:
            resolved_table_group = table_group_resolver_function(top_key, table_dict, dcf_class)
            input_dict_resolved.update(resolved_table_group)
        # If not, call table resolver
        else:
            resolved_table = table_resolver_function(top_key, table_dict, dcf_class)
            input_dict_resolved.update(resolved_table)
    
    return input_dict_resolved



if __name__ == "__main__":
    DummyDCF_instance = DummyDCF()
    input_resolver_function(input_dict, DummyDCF_instance)

