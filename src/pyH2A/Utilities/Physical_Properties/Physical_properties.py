from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.Physical_Properties import H2_properties as H2_prop
from pyH2A.Utilities.Physical_Properties import O2_properties as O2_prop
from pyH2A.Utilities.Physical_Properties import Water_properties as water_prop
import numpy as np

class Physical_properties:
    '''
    This class defines multiple constants (e.g. the ideal gas constant) as well as material properties characteristics (e.g. molecular weight).
    It also defines methods that calculate thermophysical properties of a mixture (e.g. enthalpy) using correlations derived from literature data.
    Input and oputput variables are Quantity objects to make them easy to handle in plugins. 
    Internal variables are however defined with fixed units, generally imposed by the correlations.
    '''
    
    # Universal constants

    # Ideal gas constant
    IG_constant = Quantity(8.314, 'J/(mol*delta_K)') 

    # Ideal gas molar heat capacities at constant volume and pressure
    IG_monoatomic_Cv = Quantity(1.5, 'J/(mol*delta_K)')
    IG_monoatomic_Cp = Quantity(2.5, 'J/(mol*delta_K)')
    IG_diatomic_Cv = Quantity(2.5, 'J/(mol*delta_K)')
    IG_diatomic_Cp = Quantity(3.5, 'J/(mol*delta_K)')

    # Heat capacity ratio of ideal gas
    IG_monoatomic_heat_capacity_ratio = Quantity(5/3, '-')     
    IG_diatomic_heat_capacity_ratio = Quantity(7/5, '-')    

    # Material-specific constants

    # dictionary mapping each compound to the class that contains its properties calculation methods (e.g. enthalpy)
    species_properties = {
        'H2': H2_prop.H2_properties(),
        'O2': O2_prop.O2_properties(),
        'H2O': water_prop.Water_properties(),
    }

    # Molecular weight of usual molecules. These live outside of the respective species classes as they are permanent constants.
    MW = {
        'H2': Quantity(2.016, 'g/mol'),
        'O2':Quantity(31.998, 'g/mol'),
        'H2O': Quantity(18.015, 'g/mol'), 
    } 

    # Conversion of molar to mass amounts, and conversely
    @staticmethod
    def substance_to_mass(molar_amounts):
        '''
        Convert molar amounts into mass amounts. Also returns the mass fractions

        Parameters
        ----------
        molar_amounts : dict 
            Dictionary of species and their respective molar amounts 

        Returns
        -------
        mass_amount: dict 
            Dictionary of species and their respective mass amounts 
        mass_fraction: dict 
            Dictionary of species and their respective mass fractions             
        '''       

        denominator = 0
        mass_amount = {}
        mass_fraction = {}

        for species, quantity in molar_amounts.items():
            mass_amount[species] = quantity.unit['mol'] * Physical_properties.MW[species].unit['kg/mol']
            denominator += mass_amount[species]
            mass_amount[species] = Quantity(mass_amount[species], 'kg')

        for species in molar_amounts.keys():
            mass_fraction[species] = Quantity(
                                                mass_amount[species].unit['kg']
                                                /denominator, 
                                            '-')

        return mass_amount, mass_fraction

    @staticmethod
    def mass_to_substance(mass_amounts):
        '''
        Convert mass amounts into molar amounts. Also returns the molar fractions.

        Parameters
        ----------
        mass_amounts : dict 
            Dictionary of species and their respective mass amounts 

        Returns
        -------
        molar_amount: dict 
            Dictionary of species and their respective molar amounts 
        molar_fraction: dict 
            Dictionary of species and their respective molar fractions             
        '''       

        denominator = 0
        molar_amount = {}
        molar_fraction = {}

        for species, quantity in mass_amounts.items():
            molar_amount[species] = quantity.unit['kg'] / Physical_properties.MW[species].unit['kg/mol']
            denominator += molar_amount[species]
            molar_amount[species] = Quantity(molar_amount[species], 'mol')

        for species in mass_amounts.keys():
            molar_fraction[species] = Quantity(
                                                molar_amount[species].unit['mol']
                                                /denominator, 
                                            '-')

        return molar_amount, molar_fraction    


    # Mixture enthalpy
    @staticmethod
    def Enthalpy(T, P, amount, phase = 'V', composition_basis = 'mass'):
        '''
        Calculating the enthalpy of individual species at the specified temperature and pressure, and returning the mixture enthalpy, assuming ideal mixture.
        The calculation is based on extensive quantities to keep it general, which is standard practice in properties packages; 
        if the specific enthalpy (per kg or per mole of mixture) is desired, the specified "amount" in the upper level should simply be the mass | molar fraction.
        Only single-phase (S | L | V) calculation is allowed for the moment; when a mixture involves multiple phases, the upper level model must call the present method for each phase.

        Parameters
        ----------
        T : float 
            Temperature
        P : float 
            Pressure.
        m : float 
            Mass.
        phase : str
            S, L or V 
        composition_basis : str
            mass or molar

        Returns
        -------
        H_total: float 
            Enthalpy of the specified amount of mixture under the specified temperature and pressure
        Cp_total: float 
            Constant pressure heat capacity of the specified amount of mixture under the specified temperature and pressure            
        '''

        if composition_basis == 'mass':
            mass = {}
            for species, quant in amount.items(): 
                mass[species] = amount[species]
        else:
            mass, mass_fraction = Physical_properties.substance_to_mass(amount)

        H = {}
        Cp = {}
        H_total = 0
        Cp_total = 0

        for species, quantity in mass.items():
            H[species], Cp[species] = Physical_properties.species_properties[species].calc_enthalpy(T, P, quantity, phase = phase)
            H_total += H[species].unit['J']
            Cp_total += Cp[species].unit['J/delta_K']

        return Quantity(H_total, 'J'), Quantity(Cp_total, 'J/delta_K')

    # Saturation pressure of pure water 
    @staticmethod
    def water_saturation_pressure(T):
        '''
        Calculates the saturation pressure of pure water 

        Parameters
        ----------
        T : float 
            Temperature

        Returns
        -------
        saturation pressure: float 
            Saturation pressure of water under the specified temperature 
        '''
        return water_prop.Water_properties.calc_psat(T)     
    

    # Combustion enthalpy of a hydrogen - we can extend it to a mixture in the future
    @staticmethod
    def combustion_enthalpy(T, P):
        '''
        Calculates the saturation pressure of hydrogen

        Parameters
        ----------
        T : float 
            Temperature
        P : float 
            Pressure            

        Returns
        -------
        Combustion_enthalpy: float 
            Mass-specific combustion enthalpy of hydrogen 
        '''
        return H2_prop.H2_properties.calc_combustion_enthalpy(T, P) 