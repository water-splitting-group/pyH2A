class H2_properties:
    '''
    This class calculates properties of pure Hydrogen
    '''

    @staticmethod
    def calc_enthalpy(T, P, m, phase):
        '''
        Calculating the enthalpy of pure H2 at the specified temperature and pressure, in the specified phase.
        Reference conditions: null enthalpy for hydrogen gas at 298.15 K

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
            Enthalpy of the mass m of H2 under the specified conditions in J   
        Cp: float 
            Constant pressure heat capacity of the mass m of H2 under the specified conditions in J       
        '''

        # thermal coefficients:
        T_ref = 298.15 # reference temperature
        linear_vapour = 6.86e3 
        quadratic_vapour = 0.46
        cubic_vapour = - 3.33e-4
        offset_liquid = - 2.65e6 # vapourization enthalpy of liquid H2
        linear_liquid = 10e3 # heat capacity of liquid
        
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
            raise ValueError("Solid H2 is not supported")
        
        H = h*m
        Cp = cp*m
        return H, Cp
    

    # Hydrogen combustion enthalpy (used to assess EROEI | equivalent hydrogen self-consumption)
    @staticmethod
    def calc_combustion_enthalpy(T, P): 
        '''
        Calculating the enthalpy of combustion of H2 at the specified temperature and pressure.

        Parameters
        ----------
        T : float 
            Temperature, Kelvins. Placeholder, as the calculation might use temeprature in the future
        P : float 
            Pressure, Pascals. Placeholder, as the calculation might use pressure in the future

        Returns
        -------
        H_mass: float 
            Mass-specific combustion enthalpy of H2 in J/kg   
        '''

        H = 142.5e6 # value under standard conditions, we can implement a correlation that depends on T, P later

        return H
  