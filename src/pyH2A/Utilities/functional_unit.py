from pyH2A.Utilities.Unit_Handler import config as config

def _derived_units():
    '''
    This function detects the dimension of a unit, and creates all the necessary derived dimensions and units.
    A distinction is made between the case where the functional unit has the dimension of an energy (so its derivative is a power), and the other dimensions.
    '''
    global Functional_Dimension, Functional_Dimension_dot, Functional_Unit, Functional_Unit_SI, Functional_Unit_dot, Functional_Unit_per_year

    Functional_Dimension = config.FLAT_DIMENSIONS.get(Functional_Unit)
    Functional_Unit_SI = config.DIMENSIONS[Functional_Dimension]["base"]

    if Functional_Dimension == 'energy':  # special case: energy per time is power
        Functional_Dimension_dot = 'power'
        Functional_Unit_dot = 'W'
        Functional_Unit_per_year = Functional_Unit + '_per_year'
    else:
        Functional_Dimension_dot = Functional_Dimension + '/time'
        Functional_Unit_dot = Functional_Unit_SI + '/s'
        Functional_Unit_per_year = Functional_Unit + '/year'


def set_Functional_Unit(value):
    """Set the functional unit and compute all derived units and dimensions."""
    global Functional_Unit, Ref
    Functional_Unit = value['Unit of measurement']
    Ref = value['Reference']
    _derived_units()


