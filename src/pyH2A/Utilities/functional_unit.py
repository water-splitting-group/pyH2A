from pyH2A.Utilities.Unit_Handler import config

class _FunctionalUnit:
    def __getattr__(self, name):
        raise RuntimeError(
            f"Functional unit not set yet: tried to read {name!r} before "
            f"set_functional_unit() was called."
        )

FUNCTIONAL_UNIT = _FunctionalUnit()

def set_functional_unit(unit):
    """
    Sets the functional unit for the current simulation.

    Parameters
    ----------
    unit : str
        The functional unit to set.
    """

    FUNCTIONAL_UNIT.unit = unit

    try:
        FUNCTIONAL_UNIT.dimension = config.FLAT_DIMENSIONS[unit]
    except KeyError:
        raise ValueError(f"Unknown unit specified for functional unit: {unit}")

    FUNCTIONAL_UNIT.unit_SI = config.DIMENSIONS[FUNCTIONAL_UNIT.dimension]['base']

    if FUNCTIONAL_UNIT.dimension == 'energy':  # special case: energy per time is power
        FUNCTIONAL_UNIT.dimension_per_time = 'power'
        FUNCTIONAL_UNIT.unit_SI_per_s = 'W'
        FUNCTIONAL_UNIT.unit_per_year = FUNCTIONAL_UNIT.unit + '_per_year'
    else:
        FUNCTIONAL_UNIT.dimension_per_time = FUNCTIONAL_UNIT.dimension + '/time'
        FUNCTIONAL_UNIT.unit_SI_per_s = FUNCTIONAL_UNIT.unit_SI + '/s'
        FUNCTIONAL_UNIT.unit_per_year = FUNCTIONAL_UNIT.unit + '/year'











