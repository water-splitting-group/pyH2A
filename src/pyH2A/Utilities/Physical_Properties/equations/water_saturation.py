import numpy as np
from pyH2A.Utilities.Unit_Handler.quantity import Quantity


def calc_water_saturation_pressure(T):
    """
    Calculates the saturation pressure of pure water as a function of temperature, using Antoine equation for water-vapour equilibrium:
    log10(P_sat) = A - B/(C+T)
    with Antoine constants A, B and C from NIST SRD 69 
    https://webbook.nist.gov/cgi/cbook.cgi?ID=C7732185&Mask=4&Type=ANTOINE#ANTOINE
            

    Parameters
    ----------
    T:
        Temperature.

    Returns
    -------
    psat:
        Saturation pressure.
    """

    t = np.asarray(T.unit['K'])

    if np.any(t < 273.):
        raise ValueError("Water vapour saturation pressure not available for T < 273 K")
    if np.any((t >= 373.) & (t < 379.)):
        raise ValueError("Water vapour saturation pressure not available for 373 < T < 379 K")
    if np.any(t >= 573.15):
        raise ValueError("Water vapour saturation pressure not available for T > 573 K")

    # Antoine constants (A, B, C) per temperature range
    conditions = [
        t < 303.,
        t < 333.,
        t < 363.,
        t < 373.,
        t < 573.15,
    ]
    A = np.select(conditions, [5.40221, 5.20389, 5.0768,  5.08354, 3.55959])
    B = np.select(conditions, [1838.675, 1733.926, 1659.793, 1663.125, 643.748])
    C = np.select(conditions, [-31.737, -39.485, -45.854, -45.622, -198.043])

    psat = 10 ** (A - B / (C + t))

    return Quantity(psat, 'bar')