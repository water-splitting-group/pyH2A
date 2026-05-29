from pyH2A.Utilities.Unit_Handler import config as config

def _derived_units():
    global FD, FU_SI, FD_dot, FU_dot, FU_per_hour, FU_per_day, FU_per_year, FU

    FD = config.FLAT_DIMENSIONS.get(FU)
    FU_SI = config.DIMENSIONS[FD]["base"]

    if FD == 'energy':  # special case: energy per time is power
        FD_dot = 'power'
        FU_dot = 'W'
        FU_per_hour = FU + '_per_h'
        FU_per_day = FU + '_per_day'
        FU_per_year = FU + '_per_year'
    else:
        FD_dot = FD + '/time'
        FU_dot = FU_SI + '/s'
        FU_per_hour = FU + '/h'
        FU_per_day = FU + '/day'
        FU_per_year = FU + '/year'


def set_FU(value):
    """Set the functional unit and compute all derived units and dimensions."""
    global FU, Ref
    FU = value['Unit of measurement']
    Ref = value['Reference']
    _derived_units()


