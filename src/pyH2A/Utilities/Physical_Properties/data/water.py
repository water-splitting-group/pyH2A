from .species_data import SpeciesData
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
import numpy as np

'''
Solid volume value and coefficients for liquid volume polynomial established from NIST chemistry webbook SRD69 https://webbook.nist.gov/chemistry/fluid/ 
Coefficients for vapour enthalpy polynomials from NASA Glenn Coefficients for Calculating Thermodynamic Properties of Individual Species.
Liquid water is assumed to have a constant heat capacity.
Reference conditions: Standard formation enthalpy for liquid water at 298.15 K.
Sutherland constants are used for vapour viscosity calculation, although it is known to be less accurate for polar molecules it is frequenbtly used as a first approximation,
from Comsol documentation https://doc.comsol.com/6.3/doc/com.comsol.help.cfd/cfd_ug_fluidflow_high_mach.08.43.html
Coefficients for liquid water viscosity obtained by experimental data fitting: https://holzmann-cfd.com/community/blog-and-tools/cae-blog/thermophysical-properties-water
'''

WATER = SpeciesData(
    molecular_weight = Quantity(18.015, 'g/mol'),
    liquid_volume_coefficients = np.array([9.99806282e-04, -2.33664305e-09, 5.74608202e-09, -1.80098558e-11, 4.45840291e-14]),    
    solid_volume_coefficients = np.array([0.00109]),    
    vapour_enthalpy_coefficients = np.array([-1.399234E+07, 1.939305E+03, -4.703031E-01, 1.003900E-03, -6.337082E-07, 1.636914E-10]),
    liquid_enthalpy_coefficients = np.array([-17114900, 4.186e3]), 
    solid_enthalpy_coefficients =  np.array([-16864100, 2050.]),
    combustion_enthalpy = Quantity(0, 'J/kg'), 
    gas_viscosity_coefficients = {'Reference value': Quantity(1.12e-5, 'Pa*s'), 
                                'Reference temperature': Quantity(350, 'K'),
                                'Sutherland constant': Quantity(1064, 'K') }, 
    liquid_viscosity_coefficients = np.array([0.116947, -0.00100532, 2.90283e-6, -2.80572e-9])          
)