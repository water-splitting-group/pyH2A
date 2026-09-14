from dataclasses import dataclass
from pyH2A.Utilities.Unit_Handler import config, Quantity

@dataclass(frozen=True)
class FunctionalUnit:
    unit: str
    unit_no_reference: str
    reference: tuple
    dimension: str
    unit_SI: str
    dimension_per_time: str
    unit_SI_per_s: str
    unit_per_year: str

def resolve_functional_unit(unit):
    '''
    Compute functional-unit-derived quantities (dimension, SI unit, etc.) for the
    given unit string. Pure function — no global state; call fresh wherever the
    functional unit is needed (e.g. once per Discounted_Cash_Flow_Plugin instance).
    '''

    functional_quantity = Quantity(1, unit)

    unit_no_reference = functional_quantity.supplied_unit
    dimension = functional_quantity.dimension
    reference = functional_quantity.reference
    unit_SI = functional_quantity.base_unit_reference

    if functional_quantity.dimension == 'energy':
        dimension_per_time = 'power'
        unit_SI_per_s = 'W'
        unit_per_year = unit + '_per_year'

    else:
        dimension_per_time = functional_quantity.dimension + '/time'
        unit_SI_per_s = unit_SI + '/s'
        unit_per_year = unit + '/year'

    return FunctionalUnit(unit, 
                          unit_no_reference,reference, 
                          dimension, 
                          unit_SI, 
                          dimension_per_time, 
                          unit_SI_per_s, 
                          unit_per_year)

if __name__ == "__main__":

    unit = 'kWh[delivered]'

    functional_unit = resolve_functional_unit(unit)

    import pprint as pp 
    pp.pprint(functional_unit)




