'''Utilities shared by the analysis modules (reading the dependent variable and the
analysis parameters, running the model for a set of parameter values).
'''

from __future__ import annotations

import copy
import numbers
from collections.abc import Sequence

import numpy as np

from pyH2A.Discounted_Cash_Flow import Discounted_Cash_Flow
from pyH2A.Utilities.IO.input_processing import parse_parameter_to_array
from pyH2A.Utilities.input_modification import (parse_parameter, 
                                                get_by_path,
                                                set_by_path,)

# Entries of a "Values" cell which refer to the base value of a parameter
SPECIAL_VALUES = ['Base', 'Reference']


def select_non_reference_value(reference: float,
                               values: np.ndarray) -> float:
    '''Select the first value from `values` which is not the reference value.

    Parameters
    ----------
    reference : float
        Reference (base) value.
    values : np.ndarray
        Values to select from, e.g. the lower and upper end of a parameter range.

    Returns
    -------
    float
        First entry of `values` which is not equal to `reference`.

    Raises
    ------
    ValueError
        If all entries of `values` are equal to `reference`.
    '''

    values = np.asarray(values)
    non_reference_values = values[np.invert(np.equal(values, reference))]

    if non_reference_values.size == 0:
        raise ValueError(f'All values in {values} are equal to the reference value ({reference}).')

    return float(non_reference_values[0])

def read_dependent_variable(dependent_variable_inp: dict,
                            keys: Sequence[str] = ('Path to variable', 'Variable unit')) -> dict:
    '''Read the dependent variable from the resolved "Dependent variable" table.

    Parameters
    ----------
    dependent_variable_inp : dict
        Resolved "Dependent variable" table. Only its first row is used, the row key being
        the name of the dependent variable.
    keys : Sequence[str], optional
        Columns which have to be present in the table. If "Target range" is included,
        the target range is read as well.

    Returns
    -------
    dict
        Dictionary with "Name", "Path" (list of keys pointing to the dependent variable in
        the processed input dictionary), "Unit" and, if requested, "Target range" (ndarray).

    Raises
    ------
    KeyError
        If one of `keys` is not a column of the table.
    '''

    name = list(dependent_variable_inp)[0]
    dependent_variable = dependent_variable_inp[name]

    # Check that all keys are in the dependent_variable_inp dictionary
    for key in keys:
        if key not in dependent_variable:
            raise KeyError(f"Key '{key}' not found in dependent_variable_inp dictionary.")

    path = parse_parameter(dependent_variable['Path to variable'], delimiter = '>')

    dependent_variable_dict = {'Name': name,
                               'Path': path,
                               'Unit': dependent_variable['Variable unit'],}

    if 'Target range' in keys:
        target_range = parse_parameter_to_array(dependent_variable['Target range'],
                                                delimiter = ';')
        dependent_variable_dict['Target range'] = target_range

    return dependent_variable_dict

def dependent_variable_label(dependent_variable: dict) -> str:
    '''Label of the dependent variable for plotting, in the form "Name / Unit".

    Parameters
    ----------
    dependent_variable : dict
        Dependent variable as returned by :func:`read_dependent_variable`.

    Returns
    -------
    str
        Label, e.g. "Global warming potential (GWP100) / kg[$CO_{2}$-Eq]/kg[H2]".
    '''

    return f"{dependent_variable['Name']} / {dependent_variable['Unit']}"

def process_parameters(parameters_inp: dict,
                       whole_inp: dict,
                       keys: Sequence[str] = ('Parameter path', 'Values')) -> dict:
    '''Read the analysis parameters and retrieve their base values from `whole_inp`.

    Parameters
    ----------
    parameters_inp : dict
        Resolved parameter table. Each row key is the display name of a parameter. The
        row contains the "Parameter path" (e.g. "Photovoltaic > Efficiency > Value"), the
        "Values" (entries separated by ";") and optionally the "Type" ("value" or "factor").
    whole_inp : dict
        Input dictionary of the model, used to retrieve the base values of the parameters.
    keys : Sequence[str], optional
        Columns which have to be present in `parameters_inp`.

    Returns
    -------
    dict
        Dictionary with one entry per parameter (keyed by its display name), containing
        "Parameter" (path as list), "Type", "Values" (sorted ndarray), "Reference" (base value),
        "Limit" (first entry of "Values" which is not the reference) and "Index" (position of 
        the parameter in the table).

    Raises
    ------
    KeyError
        If one of `keys` is not a column of the table.
    ValueError
        If a "Parameter path" does not have the form "Table > Row > Column" or does not point
        to a numerical value.

    Notes
    -----
    Entries in "Values" can either be numbers or one of `SPECIAL_VALUES` ("Base", "Reference"),
    which refer to the base value of the parameter in `whole_inp`. For parameters of "Type"
    "factor", the values are factors by which the base value is multiplied. Their reference is
    therefore a factor of 1, which is also what "Base" and "Reference" refer to.
    '''

    # Check that all keys are in the parameters_inp dictionary
    for key in keys:
        if key not in parameters_inp[list(parameters_inp)[0]]:
            raise KeyError(f"Key '{key}' not found in parameters_inp dictionary.")

    parameters = {}

    for counter, key in enumerate(parameters_inp):
        path = parse_parameter(parameters_inp[key]['Parameter path'], delimiter = '>')

        if len(path) != 3:
            raise ValueError(f'Parameter path "{parameters_inp[key]["Parameter path"]}" of "{key}" does not have the form "Table > Row > Column".')

        value_type = parameters_inp[key].get('Type', 'value') # Default to 'value' if 'Type' is not specified

        # Factors multiply the base value, so the base value corresponds to a factor of 1
        lookup = {path[0]: {path[1]: {path[2]: 1.}}} if value_type == 'factor' else whole_inp

        values_range = parse_parameter_to_array(parameters_inp[key]['Values'],
                                                delimiter = ';',
                                                path = path,
                                                dictionary = lookup,
                                                special_values = SPECIAL_VALUES)
        values_range = np.sort(values_range)

        reference = get_by_path(lookup, path)

        if not isinstance(reference, numbers.Real):
            raise ValueError(f'Base value of "{key}" at "{parameters_inp[key]["Parameter path"]}" is not a number ({reference}).')

        limit = select_non_reference_value(reference, values_range)
    
        parameters[key] = {'Parameter': path, 
                           'Type': value_type,
                           'Values': values_range, 
                           'Reference': reference, 
                           'Limit': limit,
                           'Index': counter,}

    return parameters

def substitute_parameters_and_run(parameters: dict,
                                  values: np.ndarray,
                                  whole_inp: dict,
                                  dependent_variable: dict) -> float:
    '''Substitute the parameters in a copy of the input dictionary with the given values,
    run the model and return the dependent variable.

    Parameters
    ----------
    parameters : dict
        Parameters as returned by :func:`process_parameters`.
    values : np.ndarray
        1D array of parameter values, ordered according to the "Index" of each parameter.
    whole_inp : dict
        Input dictionary of the model (not modified).
    dependent_variable : dict
        Dependent variable as returned by :func:`read_dependent_variable`.

    Returns
    -------
    float
        Dependent variable in the unit of `dependent_variable`.

    Notes
    -----
    Parameters of "Type" "value" replace the base value, parameters of "Type" "factor" are
    multiplied with it.
    '''

    input_dict = copy.deepcopy(whole_inp)

    for parameter in parameters.values():
        set_by_path(input_dict, 
                    parameter['Parameter'], 
                    values[parameter['Index']], 
                    value_type = parameter.get('Type', 'value')) # Default to 'value' if 'Type' is not specified

    dcf = Discounted_Cash_Flow(input_dict, print_info = False) # Run the calculation

    result = get_by_path(dcf.inp, dependent_variable['Path']) # Retrieve the dependent variable from the dcf object
    result = result.unit[dependent_variable['Unit']] # Convert result to unit of dependent variable

    return result
