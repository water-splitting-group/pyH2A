import numpy as np
from typing import List
import copy

from pyH2A.Discounted_Cash_Flow import Discounted_Cash_Flow
from pyH2A.Utilities.IO.input_processing import parse_parameter_to_array
from pyH2A.Utilities.input_modification import (parse_parameter, 
												get_by_path, 
												set_by_path,)


def select_non_reference_value(reference, values):
	'''Select value from values which is not the reference one.
	'''

	idx = np.invert(np.equal(values, reference))
	return float(values[idx][0])

def read_dependent_variable(dependent_variable_inp : dict,
                            keys : List[str] = ['Path to variable', 'Variable unit']) -> dict:
    '''
    Read dependent variable information from `dependent_variable_inp` dictionary 
    and return a dictionary containing the dependent variable information.
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

def process_parameters(parameters_inp : dict,
                       whole_inp : dict,
                       keys = ['Parameter path', 'Values']) -> dict:
    '''
    Read parameters from `parameters_inp` dictionary, retrieve the corresponding values from `whole_inp` 
    and return a dictionary containing the parameter information. 

    Notes
    -----
    The ranges for each parameter are defined in `Values` column as ';' seperated entries. Entries can
    either be a number or a `special_value` such as `Base` or `Reference`. If such a `special_value`
    is specified, the base value of that parameter is retrieved from `self.inp`.
    '''

    # Check that all keys are in the parameters_inp dictionary
    for key in keys:
        if key not in parameters_inp[list(parameters_inp)[0]]:
            raise KeyError(f"Key '{key}' not found in parameters_inp dictionary.")

    parameters = {}

    for counter, key in enumerate(parameters_inp):
        path = parse_parameter(parameters_inp[key]['Parameter path'], delimiter = '>')

        values_range = parse_parameter_to_array(parameters_inp[key]['Values'],
                                                delimiter = ';',
                                                path = path,
                                                dictionary = whole_inp,
                                                special_values = ['Base', 'Reference'])
        values_range = values_range[np.argsort(values_range)]

        reference = get_by_path(whole_inp, path)
        limit = select_non_reference_value(reference, values_range)
    
        parameters[key] = {'Parameter': path, 
                           'Values': values_range, 
                           'Reference': reference, 
                           'Limit': limit,
                           'Index': counter, 
                           'Input Index': counter,}

        if 'Type' in keys:
            parameters[key]['Type'] = parameters_inp[key]['Type']

        if 'File index' in keys:
            parameters[key]['File index'] = parameters_inp[key]['File index']
        
    return parameters

def substitute_parameters_and_run(parameters : dict,
                                  values : np.ndarray,
                                  whole_inp : dict,
                                  dependent_variable : dict) -> float:
    '''
    Substitute the parameters in the input dictionary with the given values and run the calculation.

    Parameters
    ----------
    parameters : dict
        Dictionary containing the parameter information.
    values : np.ndarray
        Array of parameter values to be substituted.
    whole_inp : dict
        The original input dictionary.
    dependent_variable : dict
        Dictionary containing the path and unit of the dependent variable.

    Returns
    -------
    float
        The result of the calculation.
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

