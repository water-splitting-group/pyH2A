import numpy as np
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.Physical_Properties.data.Constants import IDEAL_GAS_CONSTANT


def calc_enthalpy(species_data, T, P, phase):
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
        raise ValueError(f"{phase} phase not supported for enthalpy calculation")


    h = evaluate_polynomial(coefficients, T.unit['K'])

    H = Quantity(h, 'J/kg')

    return H


def calc_heat_capacity(species_data, T, P, phase):
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
        raise ValueError(f"{phase} phase not supported for heat capacity calculation")

    cp = evaluate_polynomial_derivative(coefficients, T.unit['K'])

    Cp = Quantity(cp, 'J/kg/delta_K')

    return Cp


def calc_volume(species_data, T, P, phase):
    '''
    Selects the relevant polynomial coefficients of the desired species, for the specified phase, and builds the polynomial calculation accordingly
    '''
    if phase == 'V':
        v = IDEAL_GAS_CONSTANT.unit['J/(mol*delta_K)'] * T.unit['K'] / (P.unit['Pa']*species_data.molecular_weight.unit['kg/mol'])

    elif phase == 'L':
        coefficients = species_data.liquid_volume_coefficients

        if len(coefficients) == 0:
            raise ValueError(f"{phase} phase not supported for volume calculation")

        v = evaluate_polynomial(coefficients, T.unit['degC'])

    else:
        coefficients = species_data.solid_volume_coefficients

        if len(coefficients) == 0:
            raise ValueError(f"{phase} phase not supported for volume calculation")

        v = evaluate_polynomial(coefficients, T.unit['degC'])

    return Quantity(v, 'm3/kg')


def calc_viscosity(species_data, T, P, phase):
    '''
    Calculates the viscosity of a pure gas using Sutherland's equation, or the viscosity of liquid water using a polynomial interpolation of experimental data
    '''
    if phase == 'V':
        viscosity = evaluate_sutherland(species_data.gas_viscosity_coefficients, T)

    elif phase == 'L':
        coefficients = species_data.liquid_viscosity_coefficients

        if len(coefficients) == 0:
            raise ValueError(f"{phase} phase not supported for viscosity calculation")

        viscosity = evaluate_polynomial(coefficients, T.unit['K'])

    else:
        raise ValueError(f"{phase} phase not supported for viscosity calculation")

    return Quantity(viscosity, 'Pa*s')


# Generic form of the equations that are used for properties calculation

def evaluate_polynomial(coefficients, x):
    """
    Evaluates a polynomial:
        a0 + a1*x + a2*x² + ...
    """

    value = 0.0

    for i in range(len(coefficients)):
        value += coefficients[i] * x**i

    return value


def evaluate_polynomial_derivative(coefficients, x):
    """
    Evaluates the derivative:
        a1 + 2*a2*x + 3*a3*x² + ...
    """

    value = 0.0

    for i in range(1, len(coefficients)):
        value += i * coefficients[i] * x**(i-1)

    return value


def evaluate_sutherland(coefficients, T):
    '''
    Uses Sutherland correlation to assess physical properties.
    This form is usual for gas viscosity and for thermal conductivity
    '''

    value = (coefficients['Reference value'].base_value
             *
             (T.unit['K']/coefficients['Reference temperature'].unit['K'])**1.5
             *
            (coefficients['Reference temperature'].unit['K'] + coefficients['Sutherland constant'].unit['K'])
            /
            (T.unit['K'] + coefficients['Sutherland constant'].unit['K'])
             )
    
    return value