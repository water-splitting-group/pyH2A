from pyH2A.Utilities.Unit_Handler.quantity import Quantity


class Water_properties:
    '''
    This class calculates properties of pure water
    '''

    @staticmethod
    def calc_volume(T, P, m, phase, r):
        '''
        Calculating the volume of pure water at the specified temperature and pressure, in the specified phase.
        Polynomial for liquid established from NIST chemistry webbook SRD69 https://webbook.nist.gov/chemistry/fluid/ 

        Parameters
        ----------
        T : float 
            Temperature
        P : float 
            Pressure.
        m : float 
            Mass of water 
        phase : str
            S, L or V 
        r : float
            Mass-based specific ideal gas constant (R/MW)

        Returns
        -------
        V: float 
            Volume of the mass m of water under the specified conditions  
        '''

        # thermal coefficients, with imposed units due to the correlation they originate from:
        offset_liquid =  9.99806282e-04 # m3/kg
        linear_liquid = -2.33664305e-09 # m3/kg/degC
        quadratic_liquid =  5.74608202e-09 # m3/kg/degC^2
        cubic_liquid = -1.80098558e-11 # m3/kg/degC^3
        quartic_liquid =  4.45840291e-14 # m3/kg/degC^4

        # Calculation of the mass-specific volume
        if phase == 'V':
            # using ideal gas law v = rT/P
            v = r.unit['J/(kg*delta_K)'] * T.unit['K'] / P.unit['Pa']

        elif phase == 'L':
            v = offset_liquid + linear_liquid * T.unit['degC'] + quadratic_liquid * T.unit['degC']**2 + cubic_liquid * T.unit['degC']**3 + quartic_liquid * T.unit['degC']**4
            
        else: # ice
            v = 0.00109 # assumed to be insensitive to pressure and temperature in our range of use
        
        V = v*m.unit['kg']
        return Quantity(V, 'm3')
    
    
    @staticmethod
    def calc_enthalpy(T, P, m, phase):
        '''
        Calculating the enthalpy of pure water at the specified temperature and pressure, in the specified phase.
        Polynomials established from NIST Janaf tables with reference conditions: Standard formation enthalpy for liquid water at 298.15 K.

        Parameters
        ----------
        T : float 
            Temperature
        P : float 
            Pressure. Placeholder, as some correlations might use pressure for some species in the future
        m : float 
            Mass of water 
        phase : str
            S, L or V 

        Returns
        -------
        H: float 
            Enthalpy of the mass m of water under the specified conditions  
        Cp: float 
            Constant pressure heat capacity of the mass m of water under the specified conditions                
        '''

        # thermal coefficients, with imposed units due to the correlation they originate from:
        T_ref = 298.15 # reference temperature, K
        std_H_formation = -15860e3 # Standard formation enthalpy of liquid water at 25°C, J/kg 
        offset_vapour = 2443e3 # vapourization enthalpy at 25°C, since the reference is liquid at 298.15 K, J/kg
        linear_vapour = -2.36e3 + 1.864e3 # dependency of the vapourization enthalpy + dependency of the vapour itself, J/kg/K
        quadratic_vapour = 0.23 # J/kg/K^2
        cubic_vapour = - 5e-5 # J/kg/K^3
        linear_liquid = 4.18e3 # heat capacity of liquid, J/kg/K
        offset_solid = -385.79e3 # freezing enthalpy, J/kg
        linear_solid = 2098 # heat capacity of ice, J/kg/K
        

        # Calculation of the mass-specific enthalpy and heat capacity
        if phase == 'V':
            h = std_H_formation + offset_vapour + linear_vapour*(T.unit['K']-T_ref) + quadratic_vapour*(T.unit['K']**2-T_ref**2) + cubic_vapour*(T.unit['K']**3-T_ref**3)
            cp = linear_vapour + quadratic_vapour*2*T.unit['K'] + cubic_vapour*3*T.unit['K']**2

        elif phase == 'L':
            h = std_H_formation + linear_liquid*(T.unit['K']-T_ref)
            cp = linear_liquid
            
        else: # ice
            h = std_H_formation + offset_solid + linear_solid * (T.unit['K']-T_ref)
            cp = linear_solid
        
        H = h*m.unit['kg']
        Cp = cp*m.unit['kg']
        return Quantity(H, 'J'), Quantity(Cp, 'J/delta_K')
    
    def calc_psat(T):
        '''
        Antoine equation for water-vapour equilibrium:
        log10(P_sat) = A - B/(C+T)
        with Antoine constants A, B and C from NIST SRD 69 
        https://webbook.nist.gov/cgi/cbook.cgi?ID=C7732185&Mask=4&Type=ANTOINE#ANTOINE
        
        Parameters
        ----------
        T : float 
            Temperature

        Returns
        -------
        psat: float 
            Pure water saturation pressure
        '''

        if T.unit['K'] < 273.:
            raise ValueError("Water vapour saturation pressure not available for T < 273 K")
        elif T.unit['K'] < 303.:
            A, B, C = 5.40221, 1838.675, -31.737
        elif T.unit['K'] < 333.:
            A, B, C = 5.20389, 1733.926, -39.485
        elif T.unit['K'] < 363.:
            A, B, C = 5.0768, 1659.793, -45.854
        elif T.unit['K'] < 373.:
            A, B, C = 5.08354, 1663.125, -45.622
        elif T.unit['K'] < 379.:
            raise ValueError("Water vapour saturation pressure not available for 373 < T < 379 K")
        elif T.unit['K'] < 573.15:
            A, B, C = 3.55959, 643.748, -198.043
        else:
            raise ValueError("Water vapour saturation pressure not available for T > 573 K")

        psat = 10**(A - B / (C + T.unit['K']))
        
        return Quantity(psat, 'bar')
    