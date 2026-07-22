import numpy as np
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.Physical_Properties.data.Constants import IDEAL_GAS_CONSTANT


def calc_enthalpy(species_data, T, P, m, phase):
    '''
    Selects the relevant polynomial coefficients of the desired species, for the specified phase, and builds the polynomial calculation accordingly
    '''

    if phase == 'V':
        coefficients = species_data.vapour_enthalpy_coefficients

    elif phase == 'L':
        coefficients = species_data.liquid_enthalpy_coefficients

    else:
        coefficients = species_data.solid_enthalpy_coefficients


    if len(coefficients) == 0:
        raise ValueError(f"{phase} phase not supported")


    h = evaluate_polynomial(coefficients, T.unit['K'])

    H = Quantity(h * m.unit['kg'], 'J')

    return H


def calc_heat_capacity(species_data, T, P, m, phase):
    '''
    Selects the relevant polynomial coefficients of the desired species, for the specified phase, and builds the polynomial calculation accordingly.
    '''

    if phase == 'V':
        coefficients = species_data.vapour_enthalpy_coefficients

    elif phase == 'L':
        coefficients = species_data.liquid_enthalpy_coefficients

    else:
        coefficients = species_data.solid_enthalpy_coefficients


    if len(coefficients) == 0:
        raise ValueError(f"{phase} phase not supported")

    cp = evaluate_polynomial_derivative(coefficients, T.unit['K'])

    Cp = Quantity(cp * m.unit['kg'], 'J/delta_K')

    return Cp


def calc_volume(species_data, T, P, m, phase):
    '''
    Selects the relevant polynomial coefficients of the desired species, for the specified phase, and builds the polynomial calculation accordingly
    '''
    if phase == 'V':
        v = IDEAL_GAS_CONSTANT.unit['J/(mol*delta_K)'] * T.unit['K'] / (P.unit['Pa']*species_data.molecular_weight.unit['kg/mol'])

    elif phase == 'L':
        coefficients = species_data.liquid_volume_coefficients

        if len(coefficients) == 0:
            raise ValueError(f"{phase} phase not supported")

        v = evaluate_polynomial(coefficients, T.unit['degC'])

    else:
        coefficients = species_data.solid_volume_coefficients

        if len(coefficients) == 0:
            raise ValueError(f"{phase} phase not supported")

        v = evaluate_polynomial(coefficients, T.unit['degC'])

    return Quantity(v * m.unit['kg'], 'm3')


def evaluate_polynomial(coefficients, T):
    """
    Evaluates a polynomial:
        a0 + a1*T + a2*T² + ...
    """

    value = 0.0

    for i in range(len(coefficients)):
        value += coefficients[i] * T**i

    return value


def evaluate_polynomial_derivative(coefficients, T):
    """
    Evaluates the derivative:
        a1 + 2*a2*T + 3*a3*T² + ...
    """

    value = 0.0

    for i in range(1, len(coefficients)):
        value += i * coefficients[i] * T**(i-1)

    return value