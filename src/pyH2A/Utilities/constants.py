# This marker indicates either a table group (when in top_key) or a wildcard row (when in middle_key). 
# It is used to indicate that the number of tables/rows is flexible and can be determined based on the content of dcf_class.inp
WILDCARD_MARKER = "<...>"

# Special middle keys 
SPECIAL_MIDDLE_KEYS = ['sum_tables']

# These keys are not considered when constructing the resolved values 
SPECIAL_BOTTOM_KEYS = ['description', 'optional']

# Sum tables key
SUM_TABLES_KEY = 'sum_tables'

# Key indicating if a value is optional or not
OPTIONAL_KEY = 'optional'

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