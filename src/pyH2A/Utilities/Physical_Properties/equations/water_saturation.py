from pyH2A.Utilities.Unit_Handler.quantity import Quantity


def calc_water_saturation_pressure(T):
    """
    Calculates the saturation pressure of pure water.

    Parameters
    ----------
    T:
        Temperature.

    Returns
    -------
    P:
        Saturation pressure.
    """

    if T.unit['K'] < 273.:

        raise ValueError(
            "Water vapour saturation pressure not available for T < 273 K"
        )

    elif T.unit['K'] < 303.:

        A, B, C = 5.40221, 1838.675, -31.737

    elif T.unit['K'] < 333.:

        A, B, C = 5.20389, 1733.926, -39.485

    elif T.unit['K'] < 363.:

        A, B, C = 5.0768, 1659.793, -45.854

    elif T.unit['K'] < 373.:

        A, B, C = 5.08354, 1663.125, -45.622

    elif T.unit['K'] < 379.:

        raise ValueError(
            "Water vapour saturation pressure not available for 373 < T < 379 K"
        )

    elif T.unit['K'] < 573.15:

        A, B, C = 3.55959, 643.748, -198.043

    else:

        raise ValueError(
            "Water vapour saturation pressure not available for T > 573 K"
        )


    psat = 10**(A - B/(C + T.unit['K']))


    return Quantity(psat,'bar')