from pyH2A.Utilities.Unit_Handler import config as config

# Define the functional unit
FU = 'kWh'

# automatic determination of the functional unit dimension and its time derivatives
FD = config.FLAT_DIMENSIONS.get(FU)
FU_SI = config.DIMENSIONS[FD]["base"]

if FD == 'energy': # special case: energy per time is power
    FD_dot = 'power' # Dimension of the functional unit per time. 
    FU_dot = 'W' # functional unit per time, SI. 
    FU_per_hour = FU +'_per_h' # not used yet, maybe in the future 
    FU_per_day = FU +'_per_day' # not used yet, maybe in the future 
    FU_per_year = FU +'_per_year' # needed because we want to integrate FUs over periods of 1 year. 
    
else: # typically, when the functional unit is a mass etc, the dimension is just that of the FU / time
    FD_dot = FD +'/time'
    FU_dot = FU_SI + '/s'
    FU_per_hour = FU + '/h' 
    FU_per_day = FU + '/day'
    FU_per_year = FU + '/year'