from pyH2A.Utilities.Unit_Handler.quantity import Quantity

class O2_properties:
    '''
    This class calculates properties of pure Oxygen
    '''

    @staticmethod
    def calc_volume(T, P, m, phase, r):
        '''
        Calculating the volume of pure O2 at the specified temperature and pressure, in the specified phase.
        Liquid value established from NIST chemistry webbook SRD69 https://webbook.nist.gov/chemistry/fluid/ 

        Parameters
        ----------
        T : float 
            Temperature
        P : float 
            Pressure.
        m : float 
            Mass of O2 
        phase : str
            S, L or V 
        r : float
            Mass-based specific ideal gas constant (R/MW)

        Returns
        -------
        V: float 
            Volume of the mass m of O2 under the specified conditions  
        '''

        # Calculation of the mass-specific volume
        if phase == 'V':
            # using ideal gas law v = rT/P
            v = r.unit['J/(kg*delta_K)'] * T.unit['K'] / P.unit['Pa']

        elif phase == 'L':
            v = 0.00087 # assumed to be constant
            
        else: # ice
            raise ValueError("Solid O2 is not supported")
        
        V = v*m.unit['kg']
        return Quantity(V, 'm3')
    

    @staticmethod
    def calc_enthalpy(T, P, m, phase):
        '''
        Calculating the enthalpy of pure O2 at the specified temperature and pressure, in the specified phase.
        Polynomials established from NIST Janaf tables with reference conditions: null enthalpy for oxygen gas at 298.15 K.

        Parameters
        ----------
        T : float 
            Temperature
        P : float 
            Pressure. Placeholder, as some correlations might use pressure for some species in the future
        m : float 
            Mass of oxygen. 
        phase : str
            S, L or V 

        Returns
        -------
        H: float 
            Enthalpy of the mass m of O2 under the specified conditions   
        Cp: float 
            Constant pressure heat capacity of the mass m of O2 under the specified conditions       
        '''

        # thermal coefficients, with imposed units due to the correlation they originate from:
        T_ref = 298.15 # reference temperature, K
        linear_vapour = 9.453e2 # J/kg/K
        quadratic_vapour = 3.207 # J/kg/K2
        cubic_vapour = - 1.37e-3  # J/kg/K3
        offset_liquid = - 6.17e5 # vapourization enthalpy of liquid O2, J/kg
        linear_liquid = 1.67e3 # heat capacity of liquid, J/kg/K
        
        # Calculation of the mass-specific enthalpy
        if phase == 'V':
            h = linear_vapour*(T.unit['K']-T_ref) + quadratic_vapour*(T.unit['K']**2-T_ref**2) + cubic_vapour*(T.unit['K']**3-T_ref**3)
            cp = linear_vapour + quadratic_vapour*2*T.unit['K'] + cubic_vapour*3*T.unit['K']**2

        elif phase == 'L': # liquid H2 might be needed if a plant includes liquiefaction at some point
            # this relation is valid at 1 Atm only
            # it should be considered as a placeholder rather than an actual correlation we will use
            h = offset_liquid + linear_liquid*(T.unit['K']-20.37)
            cp = linear_liquid
            
        else: 
            raise ValueError("Solid O2 is not supported")
        
        H = h*m.unit['kg']
        Cp = cp*m.unit['kg']
        return Quantity(H, 'J'), Quantity(Cp, 'J/delta_K')
    

  