class O2_properties:
    '''
    This class calculates properties of pure Oxygen
    '''

    @staticmethod
    def calc_enthalpy(T, P, m, phase):
        '''
        Calculating the enthalpy of pure O2 at the specified temperature and pressure, in the specified phase.
        Reference conditions: null enthalpy for oxygen gas at 298.15 K

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
            Enthalpy of the mass m of O2 under the specified conditions in J   
        Cp: float 
            Constant pressure heat capacity of the mass m of O2 under the specified conditions in J       
        '''

        # thermal coefficients:
        T_ref = 298.15 # reference temperature
        linear_vapour = 9.453e2 
        quadratic_vapour = 3.207
        cubic_vapour = - 1.37e-3
        offset_liquid = - 6.17e5# vapourization enthalpy of liquid O2
        linear_liquid = 1.67e3 # heat capacity of liquid
        
        # Calculation of the mass-specific enthalpy
        if phase == 'V':
            h = linear_vapour*(T-T_ref) + quadratic_vapour*(T**2-T_ref**2) + cubic_vapour*(T**3-T_ref**3)
            cp = linear_vapour + quadratic_vapour*2*T + cubic_vapour*3*T**2

        elif phase == 'L': # liquid H2 might be needed if a plant includes liquiefaction at some point
            # this relation is valid at 1 Atm only
            # it should be considered as a placeholder rather than an actual correlation we will use
            h = offset_liquid + linear_liquid*(T-20.37)
            cp = linear_liquid
            
        else: 
            raise ValueError("Solid O2 is not supported")
        
        H = h*m
        Cp = cp*m
        return H, Cp
    

  