from dataclasses import dataclass
from pyH2A.Utilities.Unit_Handler import config

@dataclass(frozen=True)
class FunctionalUnit:
    unit: str
    dimension: str
    unit_SI: str
    dimension_per_time: str
    unit_SI_per_s: str
    unit_per_year: str

def resolve_functional_unit(unit):
    '''Compute functional-unit-derived quantities (dimension, SI unit, etc.) for the
    given unit string. Pure function — no global state; call fresh wherever the
    functional unit is needed (e.g. once per Discounted_Cash_Flow_Plugin instance).
    '''
    try:
        dimension = config.FLAT_DIMENSIONS[unit]
    except KeyError:
        raise ValueError(f"Unknown unit specified for functional unit: {unit}")

    unit_SI = config.DIMENSIONS[dimension]['base']

    if dimension == 'energy':  # special case: energy per time is power
        dimension_per_time = 'power'
        unit_SI_per_s = 'W'
        unit_per_year = unit + '_per_year'
    else:
        dimension_per_time = dimension + '/time'
        unit_SI_per_s = unit_SI + '/s'
        unit_per_year = unit + '/year'

    return FunctionalUnit(unit, dimension, unit_SI, dimension_per_time, unit_SI_per_s, unit_per_year)





