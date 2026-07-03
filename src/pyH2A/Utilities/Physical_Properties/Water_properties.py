class Water_properties:
    '''
    This class calculates properties of pure water
    '''

    @staticmethod
    def calc_enthalpy(T, P, m, phase):
        '''
        Calculating the enthalpy of pure water at the specified temperature and pressure, in the specified phase.
        Reference conditions: Standard formation enthalpy for liquid water at 298.15 K.
        Polynomial expressions obtained by interpolation of tabulated data

        Parameters
        ----------
        T : float 
            Temperature, Kelvins
        P : float 
            Pressure, Pascals. Placeholder, as some correlations might use pressure for some species in the future
        m : float 
            Mass of water, kg 
        phase : str
            S, L or V 
        Returns
        -------
        H: float 
            Enthalpy of the mass m of water under the specified conditions in J   
        Cp: float 
            Constant pressure heat capacity of the mass m of water under the specified conditions in J                   
        '''

        # thermal coefficients:
        T_ref = 298.15 # reference temperature
        std_H_formation = -15860e3 # Standard formation enthalpy of liquid water at 25°C, J/kg 
        offset_vapour = 2443e3 # vapourization enthalpy at 25°C, since the reference is liquid at 298.15 K
        linear_vapour = -2.36e3 + 1.864e3 # dependency of the vapourization enthalpy + dependency of the vapour itself
        quadratic_vapour = 0.23
        cubic_vapour = - 5e-5
        linear_liquid = 4.18e3 # heat capacity of liquid
        offset_solid = -385.79e3 # freezing enthalpy
        linear_solid = 2098 # heat capacity of ice
        

        # Calculation of the mass-specific enthalpy and heat capacity
        if phase == 'V':
            h = std_H_formation + offset_vapour + linear_vapour*(T-T_ref) + quadratic_vapour*(T**2-T_ref**2) + cubic_vapour*(T**3-T_ref**3)
            cp = linear_vapour + quadratic_vapour*2*T + cubic_vapour*3*T**2

        elif phase == 'L':
            h = std_H_formation + linear_liquid*(T-T_ref)
            cp = linear_liquid
            
        else: # ice
            h = std_H_formation + offset_solid + linear_solid * (T-T_ref)
            cp = linear_solid
        
        H = h*m
        Cp = cp*m
        return H, Cp

    def calc_psat(T):
        '''
        Using Antoine equation for water-vapour equilibrium:
        log10(P_sat) = A - B/(C+T)
        This equation is widely used, but the exact value of parameters A, B and C depends on the source.
        We rely on NIST SRD 69 Antoine constants 
        https://webbook.nist.gov/cgi/cbook.cgi?ID=C7732185&Mask=4&Type=ANTOINE#ANTOINE
        
        Parameters
        ----------
        T : float 
            Temperature, Kelvins
        Returns
        -------
        psat: float 
            Pure water saturation pressure, bars
        '''

        if T < 273.:
            raise ValueError("Water vapour saturation pressure not available for T < 273 K")
        elif T < 303.:
            A, B, C = 5.40221, 1838.675, -31.737
        elif T < 333.:
            A, B, C = 5.20389, 1733.926, -39.485
        elif T < 363.:
            A, B, C = 5.0768, 1659.793, -45.854
        elif T < 373.:
            A, B, C = 5.08354, 1663.125, -45.622
        elif T < 379.:
            raise ValueError("Water vapour saturation pressure not available for 373 < T < 379 K")
        elif T < 573.15:
            A, B, C = 3.55959, 643.748, -198.043
        else:
            raise ValueError("Water vapour saturation pressure not available for T > 573 K")

        psat = 10**(A - B / (C + T))
        
        return psat    
    