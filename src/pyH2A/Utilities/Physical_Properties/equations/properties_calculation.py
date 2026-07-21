import numpy as np
from pyH2A.Utilities.Unit_Handler.quantity import Quantity


def calc_enthalpy(species, T, P, m, phase):

    if phase == 'V':
        coefficients = species.vapour_enthalpy_coefficients

    elif phase == 'L':
        coefficients = species.liquid_enthalpy_coefficients

    else:
        coefficients = species.solid_enthalpy_coefficients


    if len(coefficients) == 0:
        raise ValueError(f"{phase} phase not supported")


    h = evaluate_polynomial(coefficients, T.unit['K'])
    cp = evaluate_polynomial_derivative(coefficients, T.unit['K'])

    H = Quantity(h * m.unit['kg'], 'J')
    Cp = Quantity(cp * m.unit['kg'], 'J/delta_K')

    return H, Cp

def calc_volume(species, T, P, m, phase, r):

    if phase == 'V':
        v = r.unit['J/(kg*delta_K)'] * T.unit['K'] / P.unit['Pa']

    elif phase == 'L':
        coefficients = species.liquid_volume_coefficients

        if len(coefficients) == 0:
            raise ValueError(f"{phase} phase not supported")

        v = evaluate_polynomial(coefficients, T.unit['degC'])

    else:
        coefficients = species.solid_volume_coefficients

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