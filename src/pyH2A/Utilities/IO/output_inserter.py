from pyH2A.Utilities.input_modification import insert
from pyH2A.Utilities.check_functions import check_type, check_dimension
from pyH2A.Utilities.Unit_Handler.quantity import Quantity

from tests.Utilities.Output_Inserter.output_inserter_test_data import DummyDCF, DummyPlugin, output_dict

# Properties of rows (middle level)
OPTIONAL_KEY = 'optional'
ADD_PROCESSED_KEY = 'add_processed'
INSERT_PATH_KEY = 'insert_path'
PATH_KEY = 'path_key'

# key for special insertions (which are not inserted by processing the output dictionary)
special_top_level_keys = ['special_insertions']

# Special keys (not considered while iterating through middle level of output dictionary
special_keys = ['description', OPTIONAL_KEY, ADD_PROCESSED_KEY, INSERT_PATH_KEY, PATH_KEY]

# Properties of values (bottom level)
INSERTED_VALUE_KEY = 'inserted_value'
TYPE_KEY = 'type'
DIMENSION_KEY = 'dimension'

def _retrieve_value_to_be_inserted(inserted_value,
                                   plugin_class,
                                   plugin_name,
                                   top_key,
                                   middle_key,
                                   bottom_key,
                                   optional):
    '''Helper function to retrieve the value to be inserted based on the 'inserted_value' key in the output dictionary.
    '''

    # Quantity objects are returned as they are
    if isinstance(inserted_value, Quantity):
        return inserted_value

    # string indicates a class attribute, which is retrieved using getattr
    elif isinstance(inserted_value, str):
        try:
            value_to_be_inserted = getattr(plugin_class, inserted_value)
            return value_to_be_inserted

        # If attribute is not found, raise AttributeError, unless value is optional,
        # in which case return without inserting anything
        except AttributeError:
            if optional is True:
                return None
            else:
                raise AttributeError(f"Attribute '{inserted_value}' not found in plugin class"
                                     f"'{plugin_name}' for insertion into '{bottom_key} > {middle_key} > {top_key}'")

    else:
        raise TypeError(f"Inserted value for '{bottom_key} > {middle_key} > {top_key}' "
                        f"must be either a Quantity object or a string indicating a"
                        f"plugin class attribute, but got value of type '{type(inserted_value)}' instead")

def _perform_checks_on_value_to_be_inserted(value_to_be_inserted,
                                            value_dict,
                                            top_key,
                                            middle_key,
                                            bottom_key,
                                            check_type_setting = True):
    
    
    # If value_to_be_inserted is a dict, check type of the dict and 
    # then recursively perform checks on the values in the dict
    # (type check of the dict is performed only at the top level, and not for nested dicts,
    if isinstance(value_to_be_inserted, dict):

        if check_type_setting:
            check_type(top_key,
                middle_key,
                bottom_key,
                value_to_be_inserted,
                value_dict[TYPE_KEY],
                    )
        
        for _, value in value_to_be_inserted.items():
            _perform_checks_on_value_to_be_inserted(value,
                                            value_dict,
                                            top_key,
                                            middle_key,
                                            bottom_key,
                                            check_type_setting = False
                                            )

    # If value_to_be_inserted is a string or dict, check type against specificcation
    elif isinstance(value_to_be_inserted, str):

        if check_type_setting:
            check_type(top_key,
                middle_key,
                bottom_key,
                value_to_be_inserted,
                value_dict[TYPE_KEY],
                    )

    # If value_to_be_inserted is a Quantity, 
    # check type (of base_value of Quantity object) and dimension
    # against specification in value_dict
    # DIMENSION_KEY and TYPE_KEY must be present in value_dict if type includes Quantity
    elif isinstance(value_to_be_inserted, Quantity):

        if check_type_setting:
            check_type(top_key,
                    middle_key,
                    bottom_key,
                    value_to_be_inserted.base_value,
                    value_dict[TYPE_KEY],
                        )
        check_dimension(top_key,
                        middle_key,
                        bottom_key,
                        value_to_be_inserted,
                        value_dict[DIMENSION_KEY]
                        )
    
    else:
        raise TypeError(f"Value to be inserted for '{bottom_key} > {middle_key} > {top_key}'" 
                        f"is of unsupported type '{type(value_to_be_inserted)}' for checks." 
                        f"Expected type is either 'str', 'dict' or 'Quantity'.")

def insert_value(top_key : str, 
                 middle_key : str, 
                 bottom_key : str,
                 value_dict : dict,
                 row_dict : dict,
                 plugin_class,
                 dcf_class,
                 plugin_name : str,
                 ):
    
    # Extracting properties of the row, with suitable defaults values if not provided
    optional = row_dict.get(OPTIONAL_KEY, False)
    add_processed = row_dict.get(ADD_PROCESSED_KEY, True)
    insert_path = row_dict.get(INSERT_PATH_KEY, True)
    path_key = row_dict.get(PATH_KEY, 'Path')

    inserted_value = value_dict[INSERTED_VALUE_KEY]

    value_to_be_inserted = _retrieve_value_to_be_inserted(inserted_value,
                                                          plugin_class,
                                                          plugin_name,
                                                          top_key,
                                                          middle_key,
                                                          bottom_key,
                                                          optional)

    if value_to_be_inserted is None:
        return

    _perform_checks_on_value_to_be_inserted(value_to_be_inserted,
                                            value_dict,
                                            top_key,
                                            middle_key,
                                            bottom_key)

    insert(dcf_class,
           top_key,
           middle_key,
           bottom_key,
           value_to_be_inserted,
           plugin_name,
           add_processed = add_processed,
           insert_path = insert_path,
           path_key = path_key,
           print_info = False,
            )

## Top level inserter function
def output_inserter_function(output_dict, 
                             plugin_class,
                             dcf_class, 
                             plugin_name):

    try:
        # Iterating through the top level of the output dictionary
        for top_key, table_dict in output_dict.items():

            # Skipping over special insertions (which are not inserted by processing the output dictionary)
            if top_key in special_top_level_keys:
                continue

            # Iterating through the middle level of the output dictionary
            for middle_key, row_dict in table_dict.items():

                # Iterating through the bottom level of the output dictionary and inserting values
                for bottom_key, value_dict in row_dict.items():

                    # Skipping over special keys
                    if bottom_key in special_keys:
                        continue

                    insert_value(top_key,
                                middle_key,
                                bottom_key,
                                value_dict,
                                row_dict,
                                plugin_class,
                                dcf_class,
                                plugin_name,
                                )

    except Exception as error:
        error_message = error.args[0] if getattr(error, 'args', None) else str(error)
        raise type(error)(f"[Plugin: {plugin_name}] {error_message}") from error



        



if __name__ == "__main__":

    import pprint as pp

    DummyDCF_instance = DummyDCF()
    DummyPlugin_instance = DummyPlugin(DummyDCF_instance, print_info = False)

    output_inserter_function(output_dict, 
                             DummyPlugin_instance, 
                             DummyDCF_instance, 
                             'Test_Plugin')
    
    pp.pprint(DummyDCF_instance.inp)
    
    