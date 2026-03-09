class Fluid_properties:
    IG_constant = 8.314 # J/kg/K
    MW = {'H2': 2.016e-3,'O2':31.998e-3,'H2O': 18.015e-3 } # Molecular weight of usual molecules in kg / mol.
    H2_combustion_enthalpy_std = 285e3 # Joules per mol of H2 under standard conditions
    IG_heat_capacity_ratio = 1.4 # Heat capacity ratio of ideal diatomic gas

    
    
    def Enthalpy(T, P, mass_fraction, phase):
        h = {}
        if phase == 'V':
            h['H2O'] = 2.257e6 + 1.864e3*(T-298.15) + 0.23*(T**2-298.15**2) - 5e-5*(T**3-298.15**3)
            h['H2'] = 6.86e3*(T-298.15) + 0.46*(T**2-298.15**2) - 3.33e-4*(T**3-298.15**3)
            return sum(mass_fraction[species]*h[species] for species in h.keys())


        if phase == 'L':
            h['H2O'] = 4.18e3*(T-298.15)
            h['H2'] = 0 # dummy 
            return h['H2O'] 

    def water_saturation_pressure(T):
        if T < 303.15:
            A, B, C = 5.40221, 1838.675, -31.737
        elif T < 333.15:
            A, B, C = 5.20389, 1733.926, -39.485
        else:
            A, B, C = 5.0768, 1659.793, -45.854
        psat_bar = 10**(A - B / (C + T))
        return psat_bar      