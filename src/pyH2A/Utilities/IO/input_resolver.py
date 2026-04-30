import pprint as pp
import numpy as np

from pyH2A.Utilities.check_functions import check_type, check_if_in_options, check_dimension, check_bounds
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.input_modification import process_input

from tests.Utilities.Input_Resolver.input_resolver_test_data import DummyDCF, input_dict, input_dict_resolved

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
    """
    Identify which bottom-level keys form value/unit pairs versus standalone values.

    This is used to decide whether a row entry should be resolved as a
    `Quantity` (value + unit) or as a plain value (for categorical strings
    or non-quantity values).

    Parameters
    ----------
    row_dict : dict
        Row specification dictionary. Keys like `Value`/`Unit` or
        `*_Value`/`*_Unit` define value-unit pairs; any remaining keys are
        treated as standalone values.

    Returns
    -------
    list[list[str]]
        Grouped keys, where each inner list is either
        `[value_key, unit_key]` or `[standalone_key]`.

    Examples
    --------
    Input
        {'Usage_Value': {...}, 'Usage_Unit': {...}, 'Type': {...}}
    Output
        [['Usage_Value', 'Usage_Unit'], ['Type']]
    """

    result = []
    # special bottom keys are directly removed from consideration
    processed_keys = set(SPECIAL_BOTTOM_KEYS)

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
    """
    Fetch the value specification and the corresponding value from `dcf_class.inp`.

    This keeps lookups centralized so errors can be reported with a
    consistent location string.

    Parameters
    ----------
    top_key : str
        Table name in `dcf_class.inp`.
    middle_key : str
        Row name in `dcf_class.inp[top_key]`.
    bottom_key : str
        Column key in `dcf_class.inp[top_key][middle_key]`.
    row_dict : dict
        Row specification dictionary used to retrieve the specification.
    dcf_class : object
        DCF-like object that provides `inp` with nested dictionaries.

    Returns
    -------
    tuple
        `(specification, retrieved_value)` where `specification` is the
        bottom-level spec from `row_dict` and `retrieved_value` is the
        value stored in `dcf_class.inp`.

    Raises
    ------
    KeyError
        If the value is missing from `dcf_class.inp` at the specified path.
    """

    specification = row_dict[bottom_key]

    try:
        retrieved_value = dcf_class.inp[top_key][middle_key][bottom_key]
    except KeyError as e:
        raise KeyError(
            f"Key {e} not found in dcf.inp at location '{top_key} > {middle_key} > {bottom_key}'") from e

    return specification, retrieved_value


def _perform_checks_on_quantity(quantity,
                                value_specification,
                                unit_specification,
                                top_key,
                                middle_key,
                                bottom_key):
    """
    Validate a `Quantity` against dimension and optional bounds rules.

    Parameters
    ----------
    quantity : Quantity
        Quantity to validate.
    value_specification : dict
        Value specification containing optional bounds.
    unit_specification : dict
        Unit specification containing required dimension metadata.
    top_key, middle_key, bottom_key : str
        Location identifiers used in error messages.

    Returns
    -------
    None
        This function mutates nothing and raises if checks fail.
    """

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
    Recursively build `Quantity` objects and validate them.

    Why this exists
    ---------------
    Inputs can be scalars, arrays, or nested dictionaries. This function
    normalizes numeric values into `Quantity` objects and validates each
    leaf so downstream code can rely on consistent types and units.

    Parameters
    ----------
    value_retrieved : float | int | np.ndarray | dict | Quantity
        Value pulled from `dcf_class.inp`.
    unit_retrieved : str | None
        Unit string (if present) from `dcf_class.inp`.
    value_specification : dict
        Specifications that include type and optional bounds.
    unit_specification : dict
        Specifications that include required dimension metadata.
    top_key, middle_key, bottom_key : str
        Location identifiers used in error messages.

    Returns
    -------
    Quantity | dict
        The same structure as `value_retrieved`, with numeric leaves
        converted to `Quantity` instances.
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

    # Existing Quantity: validate only
    elif isinstance(value_retrieved, Quantity):
        _perform_checks_on_quantity(
            value_retrieved,
            value_specification,
            unit_specification,
            top_key,
            middle_key,
            bottom_key
        )

        return value_retrieved

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

# Value-level (bottom_key) resolver functions


def value_resolver_function(top_key,
                            middle_key,
                            bottom_key,
                            row_dict,
                            dcf_class,
                            return_specification=True):
    """
    Resolve a single value and validate it against its specification.

    This runs path processing, type checks, and optional categorical
    option checks before returning the raw value or `(spec, value)`.

    Parameters
    ----------
    top_key, middle_key, bottom_key : str
        Location identifiers in `dcf_class.inp`.
    row_dict : dict
        Row specification containing the bottom-level spec.
    dcf_class : object
        DCF-like object with `inp` nested dictionaries.
    return_specification : bool, default True
        When True, return `(spec, value)`. When False, return only `value`.

    Returns
    -------
    tuple | Any
        `(specification, retrieved_value)` when `return_specification` is
        True, otherwise just the retrieved value.
    """

    # Get specific_path_key from value specifications (if not present, default to 'Path')
    specific_path_key = row_dict[bottom_key].get(PATH_KEY, 'Path')

    # Process input (resolving paths etc.)
    process_input(dcf_class.inp,
                  top_key,
                  middle_key,
                  bottom_key,
                  path_key=specific_path_key,
                  add_processed=False)

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


def value_with_unit_resolver_function(top_key,
                                      middle_key,
                                      bottom_key_group,
                                      row_dict,
                                      dcf_class):
    """
    Resolve a value that may have an associated unit into a `Quantity`.

    If the retrieved value is already a `Quantity`, it is validated and
    returned. If the value is numeric (or nested dict of numerics), it is
    combined with the unit and converted to `Quantity` objects. Strings are
    returned as-is after type validation.

    Parameters
    ----------
    top_key, middle_key : str
        Location identifiers in `dcf_class.inp`.
    bottom_key_group : list[str]
        A two-element list: `[value_key, unit_key]`.
    row_dict : dict
        Row specification dictionary.
    dcf_class : object
        DCF-like object with `inp` nested dictionaries.

    Returns
    -------
    Quantity | dict | str
        Resolved quantity (or dict of quantities) or a string value.
    """

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
    elif isinstance(value_retrieved, (int, float, np.ndarray, dict)):

        unit_specification = row_dict[bottom_key_group[1]]

        # Only try to get Unit from dcf.inp if it exists
        unit_retrieved = dcf_class.inp[top_key][middle_key].get(
            bottom_key_group[1], None)

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


# Row-level (middle_key) resolver functions
def row_resolver_function(top_key, middle_key, row_dict, dcf_class):
    """
    Resolve a single row in a table using its specification.

    This function handles optional rows, resolves each bottom-level entry,
    and marks the row as processed in `dcf_class.inp`.

    Parameters
    ----------
    top_key : str
        Table name in `dcf_class.inp`.
    middle_key : str
        Row name in the table.
    row_dict : dict
        Row specification dict describing expected values and units.
    dcf_class : object
        DCF-like object with `inp` nested dictionaries.

    Returns
    -------
    dict | None
        Resolved row dictionary, or None when the row is optional and
        missing from `dcf_class.inp`.
    """

    is_optional = row_dict.get(OPTIONAL_KEY, False)
    row_present = middle_key in dcf_class.inp[top_key]

    # Handling if row is not present in dcf_class.inp
    if row_present is False:
        if is_optional is False:  # If row is not optional and not present in dcf_class.inp, raise error
            raise KeyError(
                f"Row '{middle_key}' in table '{top_key}' is required but not found in dcf.inp")
        else:
            return None  # return None if row is not present but optional

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
                                                      return_specification=False)
            resolved_row[bottom_key_group[0]] = resolved_string

        else:
            raise ValueError(
                f"Unexpected number of keys in bottom_key_group: {bottom_key_group}")

    # Explicitly mark the middle key as Processed now that all bottom keys are handled
    dcf_class.inp[top_key][middle_key]['Processed'] = 'Yes'

    return resolved_row


def wildcard_row_resolver_function(top_key, row_dict, dcf_class):
    """
    Resolve all rows in a table using a wildcard row specification.

    Parameters
    ----------
    top_key : str
        Table name in `dcf_class.inp`.
    row_dict : dict
        Row specification applied to every row in the table.
    dcf_class : object
        DCF-like object with `inp` nested dictionaries.

    Returns
    -------
    dict
        Mapping of each row key to its resolved row dictionary.
    """

    resolved_rows = {}

    # Go through all middle keys of dcf_class.inp[top_key] and resolve rows
    for middle_key in dcf_class.inp[top_key]:
        resolved_row = row_resolver_function(
            top_key, middle_key, row_dict, dcf_class)
        resolved_rows[middle_key] = resolved_row

    return resolved_rows


# Table-level (top_key) resolver functions
def table_resolver_function(top_key, table_dict, dcf_class):
    """
    Resolve a single table (top-level key) using its row specifications.

    Supports optional tables, regular rows, and wildcard rows.

    Parameters
    ----------
    top_key : str
        Table name in `dcf_class.inp`.
    table_dict : dict
        Table specification mapping row keys to row specifications.
    dcf_class : object
        DCF-like object with `inp` nested dictionaries.

    Returns
    -------
    dict | None
        Resolved table dictionary, or None when the table is optional and
        missing from `dcf_class.inp`.
    """

    # Check if there is at least one non-optional row in table_dict
    is_required = any(not row_dict.get(OPTIONAL_KEY, False)
                      for row_dict in table_dict.values())
    table_present = top_key in dcf_class.inp

    # Handling if table is not present in dcf_class.inp
    if table_present is False:
        if is_required is True:
            # If there is at least one non-optional row
            # and top_key is not present in dcf_class.inp, raise error
            raise KeyError(
                f"Table '{top_key}' is required but not found in dcf.inp")
        else:
            return None  # return None if table is not present but all rows are optional

    resolved_table = {}

    for middle_key, row_dict in table_dict.items():
        # Check if middle_key indicates wildcard row (flexible number of rows, middle_key is only placeholder),
        # if so call wildcard row resolver function
        if WILDCARD_MARKER in middle_key:
            resolved_rows = wildcard_row_resolver_function(
                top_key, row_dict, dcf_class)
            resolved_table.update(resolved_rows)

        # If not, resolve row as normal
        else:
            resolved_row = row_resolver_function(
                top_key, middle_key, row_dict, dcf_class)

            if resolved_row is not None:
                resolved_table[middle_key] = resolved_row

    return resolved_table


def table_group_resolver_function(table_group_top_key, table_group_dict, dcf_class):
    """
    Resolve a group of tables that share a common prefix.

    The wildcard marker in `table_group_top_key` is removed to form a
    prefix used to find matching tables in `dcf_class.inp`.

    Parameters
    ----------
    table_group_top_key : str
        Table-group key containing the wildcard marker.
    table_group_dict : dict
        Table specification applied to each matched table.
    dcf_class : object
        DCF-like object with `inp` nested dictionaries.

    Returns
    -------
    dict
        Mapping of each matched table key to its resolved table data.
    """

    resolved_table_group = {}

    # Remove wildcard marker from table group key to get the actual table group name
    table_group_top_key = table_group_top_key.replace(
        WILDCARD_MARKER, "").strip()

    # Extract all tables in dcf_class.inp that belong to the table group indicated by table_group_top_key
    dcf_table_groups = {key: value for key,
                        value in dcf_class.inp.items() if table_group_top_key in key}

    for table_key in dcf_table_groups:
        # Call table resolver function for each table in the table group
        resolved_table = table_resolver_function(
            table_key, table_group_dict, dcf_class)
        resolved_table_group[table_key] = resolved_table

    return resolved_table_group


# Top level resolver function
def input_resolver_function(input_dict, dcf_class, plugin_name):
    """
    Resolve the full input specification against `dcf_class.inp`.

    This is the top-level entry point used by plugins. It dispatches to
    table-group resolvers (wildcard top keys) or regular table resolvers,
    returning a fully resolved dictionary with validated values.

    Parameters
    ----------
    input_dict : dict
        Plugin input specification. Top-level keys are tables or table
        groups; middle-level keys are rows; bottom-level keys are value and
        unit specs.
    dcf_class : object
        DCF-like object containing `inp` input data.
    plugin_name : str
        Name of the plugin used to prefix error messages.

    Returns
    -------
    dict
        Fully resolved input dictionary with `Quantity` objects where
        appropriate.
    """

    try:
        input_dict_resolved = {}

        for top_key, table_dict in input_dict.items():

            # Check if top_key indicates table group, if so call table group resolve
            if WILDCARD_MARKER in top_key:
                resolved_table_group = table_group_resolver_function(
                    top_key, table_dict, dcf_class)
                input_dict_resolved.update(resolved_table_group)
            # If not, call table resolver
            else:
                resolved_table = table_resolver_function(
                    top_key, table_dict, dcf_class)

                if resolved_table is not None:
                    input_dict_resolved[top_key] = resolved_table

        return input_dict_resolved

    # Catch exception and prepend plugin name to error message
    except Exception as error:
        error_message = error.args[0] if getattr(
            error, 'args', None) else str(error)
        raise type(error)(
            f"[Plugin: {plugin_name}] {error_message}") from error


if __name__ == "__main__":
    DummyDCF_instance = DummyDCF()

    from timeit import default_timer as timer

    start_time = timer()

    input_dict_resolved = input_resolver_function(
        input_dict, DummyDCF_instance, 'TestPlugin')

    end_time = timer()

    pp.pprint(input_dict_resolved)

    print('--------------------------------')
    print(end_time - start_time, 's passed')
