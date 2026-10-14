
import numpy as np
import numbers

from pyH2A.Utilities.Unit_Handler import Quantity
from pyH2A.Utilities.input_modification import parse_parameter, get_by_path, num
from pyH2A.Utilities.constants import (VALUE_KEY, 
									   UNIT_KEY, 
									   PATH_KEY_INPUT,
									   VALUE_SUFFIX, 
									   UNIT_SUFFIX, 
									   PATH_SUFFIX,
									   SPECIAL_BOTTOM_KEYS,
                                       CELL_DELIMITER,
                                       EMPTY_CELL_PLACEHOLDER)

def is_numerical(value):
    '''Check if a value is numerical (float, int, np.ndarray) or not. Returns True if it is numerical, False otherwise.'''

    if isinstance(value, (float, int, np.ndarray)):
         return True
    else:
         return False

def is_processed(dictionary, top_key, middle_key):
    '''Check if a middle_key has been processed or not. Returns True if it has been processed, False otherwise.'''

    processed = dictionary[top_key][middle_key].get('Processed', None)

    if processed == 'Yes':
        return True
    else:
        return False
    
def detect_path(text):
    '''Detecting if a string a is path (indicated by presence of both "{" and ">") or not.
    Example: "{Table > Entry > Bottom Key, unit}" is a path, while "Table > Entry > Bottom Key" is not a path.
    '''

    if isinstance(text, str) and '{' in text and '>' in text:
        return True
    else:
        return False

def parse_path_with_unit(text):
    '''Parsing path with the notation "{top_key > middle_key > bottom_key, unit}" '''

    text = text.strip()
    if not (text.startswith("{") and text.endswith("}")):
        raise ValueError(f"Expected a string wrapped in braces, but got '{text}' instead")

    inner = text[1:-1].strip()

    try:
        path, unit = inner.rsplit(",", 1)
    except ValueError:
        raise ValueError(f"Expected a string with a comma separating the path and unit, but got '{text}' instead")

    return path.strip(), unit.strip()

def validate_path(path,
                  top_key,
                  middle_key,
                  bottom_key): 
    '''Validating if a string is a proper path 
    Example: "{Table > Entry > Bottom Key, unit}" 
    '''

    path_alone, unit = parse_path_with_unit(path)
    parsed_path = parse_parameter(path_alone)

    if len(parsed_path) != 3:
        raise ValueError(f"Invalid path specified for '{path}' (at '{top_key} > {middle_key} > {bottom_key}'). Expected a path with three components, but got {len(parsed_path)} components instead.")

    return parsed_path, unit

def identify_bottom_keys(row_dict,
                         return_paths=False,
                         return_as_lists=False):
    '''
    Identify the bottom keys relevant for processing (value-unit pairs and standalone keys).
    This is used to decide whether a row entry should be resolved as a
    `Quantity` (value + unit) or as a plain value (for categorical strings
    or non-quantity values).

    Example
    -------
    For a row_dict like this:
    {
        'Usage_Value': 1500,
        'Usage_Unit': 'kWh/kg',
        'Usage_Path': 'some/path',
        'Cost_Value': 200,
        'Cost_Unit': 'USD/kWh/day',
        'Type': 'natural_gas'
    }

    With return_paths=True, return_as_lists=False (default nested dict):
    {
        'Usage_Value': {'Value': 'Usage_Value', 'Unit': 'Usage_Unit', 'Path': 'Usage_Path'},
        'Cost_Value': {'Cost_Value': 'Cost_Value', 'Unit': 'Cost_Unit'},
        'Type':       {'Value': 'Type'}
    }

    With return_as_lists=True (flattened, backward-compatible):
    {
        'Usage_Value': ['Usage_Value', 'Usage_Unit', 'Usage_Path'],
        'Cost_Value':  ['Cost_Value', 'Cost_Unit'],
        'Type':        ['Type']
    }
    '''
    result = {}
    processed_keys = set(SPECIAL_BOTTOM_KEYS)

    # First pass: find Value/Unit(/Path) pairs
    for key in row_dict:

        # bare Value/Unit pair (no prefix) 
        if key == VALUE_KEY and UNIT_KEY in row_dict:
            entry = {'Value': key, 'Unit': UNIT_KEY}

            if return_paths and PATH_KEY_INPUT in row_dict:
                entry['Path'] = PATH_KEY_INPUT

            result[key] = entry
            processed_keys.update(entry.values())

        # prefixed Value/Unit pairs (_Value / _Unit suffixes) 
        elif key.endswith(VALUE_SUFFIX):
            prefix    = key[:-len(VALUE_SUFFIX)]
            unit_key  = prefix + UNIT_SUFFIX
            path_key  = prefix + PATH_SUFFIX

            if unit_key in row_dict:          # only treat as a pair when unit exists
                entry = {'Value': key, 'Unit': unit_key}

                if return_paths and path_key in row_dict:
                    entry['Path'] = path_key

                result[key] = entry
                processed_keys.update(entry.values())

    # Second pass: any remaining key becomes a standalone entry
    for key in row_dict:
        if key not in processed_keys:
            result[key] = {'Value': key}

    # Optionally flatten to lists for backward compatibility
    if return_as_lists:
        return {key: list(value.values()) for key, value in result.items()}

    return result

def create_quantity_from_user_input_and_insert(dictionary, parsed_path):
	'''
	Creating quantity from user input  
	'''

	# Obtain bottom keys for the given path to identify value, unit and path keys
	# e.g. for a path like "Table > Entry > Usage_Value", identify that value is at "Usage_Value", unit is at "Usage_Unit" and path is at "Usage_Path"
	bottom_keys = identify_bottom_keys(dictionary[parsed_path[0]][parsed_path[1]], 
									   return_paths = True,
									   return_as_lists = False)

	# Getting the keys for target bottom key (e.g. "Usage_Value")
	keys = bottom_keys[parsed_path[2]]

	# Processing the value found at the path location
	value = process_input(dictionary,
					   	  parsed_path[0],
						  parsed_path[1],
						  parsed_path[2],
						  path_key = keys.get('Path', PATH_KEY_INPUT),)

	# Retrieving the unit found at the path location
	unit = dictionary[parsed_path[0]][parsed_path[1]][keys['Unit']]

	# Creating quantity object
	quantity = Quantity(value, unit)

	return quantity

def process_path(dictionary, 
                 path, 
                 top_key, 
                 middle_key, 
                 bottom_key):
    '''Return the value at a path location in the dictionary.

    The main use case is to access a Quantity object at a path location (e.g. "{Table > Entry > Bottom Key, unit}") 
    and return the value in the requested unit.

    If the value at the path location is not a Quantity object but numerical, process_input is called and a Quantity 
    object is created.

    If the value at the path location is not numerical, it is simply returned.
    
    '''
    
    # Get a valid path (validate_path throws error if it is not possible 
    # to return a parsed_path of length 3 + unit)
    parsed_path, unit = validate_path(path, 
                                      top_key, 
                                      middle_key, 
                                      bottom_key)

    # Retrieve the value at the path location using process_cell (which handles cases
    # where the value at the path location is a string that contains multiple entries or a path itself)
    target_value = process_cell(dictionary,
                                parsed_path[0], 
                                parsed_path[1], 
                                parsed_path[2],)

    # If retrieved target value is dict or str, it is returned as is (after checking that 
    # in its path it was correctly specified as dimensionless (unit "-")
    if isinstance(target_value, (dict, str)):
        assert unit == '-', f'Unexpected unit "{unit}" for non-numerical value at path "{path}" (at "{top_key} > {middle_key} > {bottom_key}"). Expected unit to be "-".'
        return target_value

    # If target value is numerical (but not a Quantity object), it is processed and a quantity object is created for further use
    elif is_numerical(target_value):
        target_value = create_quantity_from_user_input_and_insert(dictionary, parsed_path)
        
    # if it is already a quantity object, pass
    elif isinstance(target_value, Quantity):
        pass

    # if target value has an unexpected type, raise an error
    else:
        raise ValueError(f'Unexpected type (Type: {type(target_value)}) "{target_value}" at path "{path}" (at "{top_key} > {middle_key} > {bottom_key}"). Expected a str, float, int, np.ndarray, dict or Quantity')

    # Return target value in requested unit
    return target_value.unit[unit]
 
def process_multiple_entry_string(dictionary,
                                  top_key,
                                  middle_key,
                                  bottom_key,
                                  string,):
    '''Process a string that contains multiple entries separated by the CELL_DELIMITER (e.g. "{Top key > middle key > bottom key, unit} * 2") 
    and return the product of all entries. Each entry can be either a number or a path to a value in the dictionary.

    For this to work, all values must be numerical (can be multiplied)
    '''
    
    # Split string at cell delimiter (e.g. "{Top key > middle key > bottom key, unit} * 2") to separate multiple values in a cell
    entries = parse_parameter(string, delimiter = CELL_DELIMITER)

    final_value = 1.

    for entry in entries:
        # Check if string can be converted to number, if so convert it
        if isinstance(num(entry), numbers.Number):
            value = num(entry)

        # Check if string is a path, if so retrieve the value at path
        elif detect_path(entry):
            value = process_path(dictionary, 
                                 entry, 
                                 top_key, 
                                 middle_key, 
                                 bottom_key)

            # Raise error if value retrieved at path location is not numerical
            if not is_numerical(value):
                raise ValueError(f'Unexpected non-numerical value at "{top_key} > {middle_key} > {bottom_key}" retrieved at "{entry}", got Type: "{type(value)}" ({value}). Expected to retrieve a numerical value (float, int, or np.ndarray) at path location.')

        else:
            raise ValueError(f'Unexpected string "{entry}" at "{top_key} > {middle_key} > {bottom_key}". Expected a number or a path, but got neither.')
             
        final_value *= value

    return final_value

def process_cell(dictionary, 
                 top_key, 
                 middle_key, 
                 bottom_key):
    '''
    Return the value of a cell in the dictionary, processing multiple entries (A * B etc.) 
    and paths (e.g. {Table > Entry > Bottom Key, unit}) if necessary.
    '''

    try:
        cell_value = dictionary[top_key][middle_key][bottom_key]
    except KeyError:
        raise KeyError(f'Value at "{top_key} > {middle_key} > {bottom_key}" could not be retrieved.')

    # If value is already a valid type, simply return it
    if isinstance(cell_value, (float, int, np.ndarray, dict, Quantity)):
        return cell_value

    elif isinstance(cell_value, str):
        # If CELL_DELIMITER ("*") is in cell value process all entries (e.g. "{A > B > C, unit} * 2")
        if CELL_DELIMITER in cell_value:
            value = process_multiple_entry_string(dictionary,
                                                top_key,
                                                middle_key,
                                                bottom_key,
                                                cell_value)

            return value
            
        # If cell_value is path, retrieve the value at path location
        elif detect_path(cell_value):
            value = process_path(dictionary, 
                                 cell_value, 
                                 top_key, 
                                 middle_key, 
                                 bottom_key)

            return value

        # If string is neither one that contains CELLS_DELIMITER nor a path, simply return it
        else:
            return cell_value

    else:
        raise ValueError(f'Unexpected type (Type: {type(cell_value)}) "{cell_value}" at "{top_key} > {middle_key} > {bottom_key}". Expected a str, float, int, np.ndarray, dict or Quantity')

def process_input(dictionary, 
                  top_key, 
                  middle_key, 
                  bottom_key, 
                  path_key = 'Path',):
    '''Process an input by calling process_cell (which handles multiple entries and paths)
    and optionally multiplying the value with a multiplier retrieved from the path_key location (if it exists).

    If the values has changed due to the processing, the dictionary is updated with the new value and the former value 
    is stored under a new key "Former {bottom_key}".
    '''

    value = process_cell(dictionary, 
                         top_key,
                         middle_key,
                         bottom_key,)

    # If "Processed" exists, no further processing should be performed
    if is_processed(dictionary, top_key, middle_key):
        return value

    # If value is a Quantity, dict or str, it cannot be multiplied, thus no further processing is needed
    elif isinstance(value, (Quantity, dict, str)):
        pass

    # If value is numerical (float, int, np.ndarray), 
    # it can be multiplied with a multiplier retrieved from the path_key location (if it exists)
    elif is_numerical(value):
        # Try to retrieve the multiplier from the path_key, if it exists, and multiply it with the value
        try:
            multiplier = process_cell(dictionary, 
                                      top_key, 
                                      middle_key, 
                                      path_key,)

            # Multiply value with retrieved multiplier, if it is numerical
            if is_numerical(multiplier):
                value *= multiplier

            elif isinstance(multiplier, str) and multiplier in EMPTY_CELL_PLACEHOLDER:
                pass  # do nothing, multiplier is empty

            # If retrieved multiplier is not numerical nor empty, raise an error
            else:
                raise ValueError(f'Value retrieved at "{top_key} > {middle_key} > {path_key}" is not numerical (value is "{multiplier}"), cannot multiply with value at "{top_key} > {middle_key} > {bottom_key}".')

        # Pass if there is no value at "top_key > middle_key > path_key" (KeyError)
        except KeyError: 
            pass 

    else:
        raise ValueError(f'Unexpected type (Type: {type(value)}) "{value}" at "{top_key} > {middle_key} > {bottom_key}". Expected a str, float, int, np.ndarray, dict or Quantity')

    # If the value has changed, store the former value under a new key 
    # and update the original key with the new value
    if np.array_equal(value, dictionary[top_key][middle_key][bottom_key]) is False:
        former_bottom_key = 'Former ' + bottom_key 
        dictionary[top_key][middle_key][former_bottom_key] = dictionary[top_key][middle_key][bottom_key]
        dictionary[top_key][middle_key][bottom_key] = value  # setting dictionary entry to obtained value

    return value

def parse_parameter_to_array(key, 
                             delimiter = '>', 
                             path = None,
                             dictionary = None, 
                             special_values = []):
    '''parse_parameter() is applied to `key` string and result is converted to num and
    returned in ndarray. Assumes that 'key' is a string of numbers and/or special 
    values separated by `delimiter`, e.g. '1.2 ; Base'.

    Parameters
    ----------
    key : str
        String convert to array.
    delimiter : str, optional
        Delimiter used in string.
    path : array, optional
        Path for lookup in case `special_values` is triggered.        
    dictionary : dict, optional
        Dictionary used for lookup.
    special_values : list, optional
        If `key` contains an element of `special_values`, the value at `path`
        is retrieved instead of using the actual value of `key`.

    Returns
    -------
    array : ndarray
        Output as array.
    '''

    output = parse_parameter(key, 
                             delimiter = delimiter)
    array = []

    for component in output:
        # If component is in special_values (e.g. 'Base', 'Reference'), 
        # retrieve the value at path location in dictionary
        if component in special_values:
            array.append(process_cell(dictionary, 
                                      path[0], 
                                      path[1], 
                                      path[2]))

        # Else the component is expected to be a number, which is converted from string to float/int and appended to the array    
        else:
            if isinstance(num(component), numbers.Number):
                array.append(num(component))
            else:
                raise ValueError(f'Unexpected non-numerical value "{component}" in "{key}". Expected a number or a special value from {special_values}.')

    return np.asarray(array)

if __name__ == "__main__":

    test_dict = {
            'Utilities': {
                'Natural gas': {
                    'Usage_Value': 1500,
                    'Usage_Unit': 'kWh/kg',
                    'Cost_Value': 200,
                    'Cost_Unit': 'USD/kWh',
                    'Type': 'natural_gas',
                    'Comment': 'Usage of natural gas'
                },
                'Electricity': {
                    'Usage_Value': 3000,
                    'Usage_Unit': 'kWh/kg',
                    'Cost_Value': 500,
                    'Cost_Unit': 'USD/kWh',
                    'Type': 'electricity'
                },
                'Water': {
                    'Usage_Value': 2,
                    'Usage_Unit': 'J/kg',
                    'Usage_Path': '{Number of units > Bag number > Value, -}', # testing that path information is correctly passed and used
                    'Cost_Value': '{Pump - Other Variable Operating Cost - Brand A > Maintenance > Value, USD}', # testing that path information is correctly passed and used
                    'Cost_Unit': 'USD/J',
                    'Cost_Path': '{Number of units > Bag number > Value, -}', # testing that path information is correctly passed and used
                    'Type': 'water'
                }
            },        
            
            'Water Supply': {
                'Volume': {
                    'Value': 50, 
                    'Unit': 'liter', 
                    'Type': 'flexible'
                }, 
                'Purity': {
                    'Value': 0.99, 
                    'Unit': '-', 
                    'Type': 'contaminants'
                }                
            },  

            'New entry': {
                'Value': {
                    'Value': 25,
                    'Unit': 'USD'
                },
            },
            
            'Number of units': {
                'Bag number': {
                    'Value': '{New entry > Value > Value, USD} * 2', 
                    'Unit': '-',
                    'Processed': 'No',
                }
            },  

            # 'Number of units': {
            #     'Bag number': {
            #         'Value': '{Bag - Other Variable Operating Cost > Disposal > Value, MJ} * 2', 
            #         'Unit': '-',
            #         'Processed': 'No',
            #     }
            # }, 




            'Catalyst': {
                'Lifetime': {
                    'Value': 5, 
                    'Unit': 'year'
                }
            } ,
            
            'Catalyst Separation': {
                'Filtration cost': {
                    'Value': 100, 
                    'Unit': 'USD/m3'
                }
            },
            
            'Grid Electricity': {
                'Cost': {
                    'Value': 0.15, 
                    'Unit': 'USD/kWh'
                }
            },

            'Power Generation': {
                'Available Power': {
                    'Value': {
                        '2025': Quantity(np.array([400.*3600, 250.*3600, 350.*3600]), 'kJ'),
                        '2024': np.array([500., 350., 450.])
                    }, 
                    'Unit': 'kWh',                    
                    'Processed': 'Yes'
                },
                'Stored Power': {
                    'Value': {
                        '2025': 200., '2024': 250.
                    }, 
                    'Unit': 'kWh',
                    'Processed': 'Yes',
                    }
                },
                
            # the following one serves to test the situation where middle key isn't known in advance / when we want to iterate
            'Power Consumption': {
                'Any mid key': {
                    'Value': np.array([100., 120., 110.]),
                    'Type': 'on demand',
                    'Unit': 'kWh',
                    'Processed': 'Yes'
                },
                'Another mid key': {
                    'Value': np.array([50., 40., 60.]), 
                    'Type': 'flexible',
                    'Unit': 'kWh',
                    'Processed': 'Yes'
                },
            }, 
            
            # Pump and compressor: to test the "Other Variable Operating Cost" group
            'Pump - Other Variable Operating Cost - Brand A': {
                'Maintenance': {
                    'Value': 12.5, 
                    'Unit': 'USD',
                    'Processed': 'Yes',
                },
                'lubrication':  {
                    'Value': 8.2, 
                    'Unit': 'USD'
                }
            },
            
            'Compressor - Other Variable Operating Cost - Brand B': {
                'Lubrication': {
                    'Value': np.array([1.3, 1.2, 1.1]),
                    'Unit': 'USD',
                    'Processed': 'Yes'
                },
                'Electricity': {
                    'Value': 2.2, 
                    'Unit': 'USD'
                }                
            },

            'Bag - Other Variable Operating Cost': {
                'Replacement': {
                    'Value': '{Number of units > Bag number > Value, -}', 
                    'Unit': 'USD'
                },
                'Disposal': {
                    'Value': 10,
                    'Unit': 'USD',
                    'Path': '{Number of units > Bag number > Value, -}' # testing that path information is correctly passed and used
                },
                'Recycling': {
                    'Value': 10,
                    'Unit': 'USD',
                    'Path': '{Number of units > Bag number > Value, -} * {Catalyst > Lifetime > Value, year}' # testing that multiple path information is correctly passed and used
                }                     
            },

            'Electrolyzer - this input is not used': {
                'Cost': {
                    'Value': 1000, 
                    'Unit': 'USD'
                }
            },

            'Turbopump': {
                'Electricity':{
                    'Value': 500, 
                    'Unit': 'USD',
                },
            },

            'Irradiation Used': {
                'Data': {
                    'Value': 'Path/to/file.txt',
                    'Unit': 'J/m2'
                },
                'Other Data': {
                    'Value': np.array([1., 2., 3.]),
                    'Unit': 'J/m2',
                    'Processed': 'Yes',
                },
                'Only String': {
                    'Value': 'Just a string',
                },
                'Quantity object': {
                    'Value': Quantity(np.array([1., 2., 3.]), 'J/m2'),
                    'Processed': 'Yes',
                }
            },

            'Quantity Path Testing': {
                'Electrolyzer power': { 
                    'Value': Quantity(100, 'kW'),
                    'Processed': 'Yes',
                },
                'PV power': {
                    'Value': 1.5,
                    'Path': '{Quantity Path Testing > Electrolyzer power > Value, W}', # testing that path information is correctly passed and used for Quantity objects
                    'Unit': 'W',
                }
            }
    }

    # import sys
    # print(sys.getrecursionlimit())

    #print(process_input(test_dict, 'Bag - Other Variable Operating Cost', 'Recycling', 'Value', path_key = 'Path'))
    result = parse_parameter_to_array('1.2 ; Base', delimiter = ';', path = 'Quantity Path Testing > PV power > Value', dictionary = test_dict, special_values = ['Base'])
    print(result * 2)

    print(get_by_path(test_dict, ['Quantity Path Testing', 'PV power', 'Value']))