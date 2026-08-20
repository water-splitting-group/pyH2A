from .species_data import SpeciesData
import numpy as np
from pyH2A.Utilities.Unit_Handler.quantity import Quantity

'''
Liquid volume value established from NIST chemistry webbook SRD69 https://webbook.nist.gov/chemistry/fluid/ 
Heat capacity is assumed to be constant. Reference conditions: null enthalpy for hydrogen gas at 298.15 K.
Sutherland coefficients for gas viscosity from Comsol documentation https://doc.comsol.com/6.3/doc/com.comsol.help.cfd/cfd_ug_fluidflow_high_mach.08.43.html
'''

HYDROGEN = SpeciesData(
    molecular_weight = Quantity(2.016, 'g/mol'),
    liquid_volume_coefficients = np.array([0.014]),    
    solid_volume_coefficients = np.array([]),    
    vapour_enthalpy_coefficients = np.array([-4266.5e3, 14.31e3]),
    liquid_enthalpy_coefficients = np.array([]), 
    solid_enthalpy_coefficients =  np.array([]),      
    combustion_enthalpy = Quantity(142.5e6, 'J/kg'), 
    gas_viscosity_coefficients = {'Reference value': Quantity(8.411e-6, 'Pa*s'), 
                                  'Reference temperature': Quantity(273, 'K'),
                                  'Sutherland constant': Quantity(97, 'K') }, 
    liquid_viscosity_coefficients = np.array([]) 
)