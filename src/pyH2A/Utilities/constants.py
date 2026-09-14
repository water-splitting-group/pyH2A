# This marker indicates either a table group (when in top_key) or a wildcard row (when in middle_key). 
# It is used to indicate that the number of tables/rows is flexible and can be determined based on the content of dcf_class.inp
WILDCARD_MARKER = "<...>"

# Special middle keys 
SPECIAL_MIDDLE_KEYS = ['sum_tables']

# Key indicating if a value is optional or not
OPTIONAL_KEY = 'optional'

# Key for the description of a value
DESCRIPTION_KEY = 'description'

# These keys are not considered when constructing the resolved values 
SPECIAL_BOTTOM_KEYS = [DESCRIPTION_KEY, OPTIONAL_KEY]

# Sum tables key
SUM_TABLES_KEY = 'sum_tables'

# Keys for value-unit pairs 
VALUE_KEY = "Value"
UNIT_KEY = "Unit"
PATH_KEY_INPUT = "Path"
VALUE_SUFFIX = "_Value"
UNIT_SUFFIX = "_Unit"
PATH_SUFFIX = "_Path"

# Specifications (checks) for values 
TYPE_KEY = 'type'
BOUNDS_KEY = 'bounds'
DIMENSION_KEY = 'dimension'
OPTIONS_KEY = 'options'
PATH_KEY = 'path'


### Output inserter keys ####

ADD_PROCESSED_KEY = 'add_processed'
INSERT_PATH_KEY = 'insert_path'
PATH_KEY_OUTPUT = 'path_key'

# key for special insertions (which are not inserted by processing the output dictionary)
SPECIAL_TOP_LEVEL_KEYS = ['special_insertions']

# Special keys (not considered while iterating through middle level of output dictionary
SPECIAL_KEYS_OUTPUT_INSERTER = [DESCRIPTION_KEY, OPTIONAL_KEY, ADD_PROCESSED_KEY, INSERT_PATH_KEY, PATH_KEY_OUTPUT]

# Properties of values (bottom level)
INSERTED_VALUE_KEY = 'inserted_value'