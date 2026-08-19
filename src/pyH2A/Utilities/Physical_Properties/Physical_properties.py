from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.Physical_Properties.equations.pure_species_properties_calculation import calc_volume, calc_enthalpy, calc_heat_capacity, calc_viscosity
from pyH2A.Utilities.Physical_Properties.equations.mixture_properties_calculation import calculate_ideal_mixture_property, calculate_wilke_mixture_property, calculate_Arrhenius_mixture_property, substance_to_mass, mass_to_substance
from pyH2A.Utilities.Physical_Properties.equations.water_saturation import calc_water_saturation_pressure
from pyH2A.Utilities.Physical_Properties.data.hydrogen import HYDROGEN
from pyH2A.Utilities.Physical_Properties.data.oxygen import OXYGEN
from pyH2A.Utilities.Physical_Properties.data.water import WATER

class Physical_properties:
    '''
    This class calls methods that calculate thermophysical properties of a mixture (e.g. enthalpy) using correlations derived from literature data.
    The variables are Quantity objects to make them easy to handle in plugins. 

    Supported methods: 
    - Substance_to_mass:
        converts a dictionary made of {species: molar amount} into a dictionary of mass amounts. Also returns the mass fractions.
    - Mass_to_substance: 
        converts a dictionary made of {species: mass amount} into a dictionary of molar amounts. Also returns the molar fractions.
    - Volume:
        calcualtes the volume of a mixture defined by a dictionary of amounts {species: mass or molar amount} at the specified temeprature and pressure, for the specified phase.
    - Enthalpy:
        calculates the enthalpy at constant pressure of a mixture defined by a dictionary of amounts {species: mass or molar amount} at the specified temeprature and pressure, for the specified phase.
    - Heat_capacity:
        calculates the heat capacity at constant pressure of a mixture defined by a dictionary of amounts {species: mass or molar amount} at the specified temeprature and pressure, for the specified phase.        
    - Water_saturation_pressure:
        calculates the saturation pressure of pure water steam at the specified temeprature.
    '''
    
    species_data = {
        'H2': HYDROGEN,
        'O2': OXYGEN,
        'H2O': WATER,
    }

    # Molecular weight of usual molecules. Having this value at this level enables upper-level models to call Physical_proeprties.MW directly
    MW = {
        species: data.molecular_weight
        for species, data in species_data.items()
    } 

    @staticmethod
    def Substance_to_mass(molar_amounts):
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

        mass_amount, mass_fraction = substance_to_mass(molar_amounts, Physical_properties.species_data)

        return mass_amount, mass_fraction


    @staticmethod
    def Mass_to_substance(mass_amounts):
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
        molar_amount, molar_fraction = mass_to_substance(mass_amounts, Physical_properties.species_data)
        return molar_amount, molar_fraction
    

    @staticmethod
    def Volume(T, P, amount, phase='V', composition_basis='mass'):
        '''
        Calculating the volume of individual species at the specified temperature and pressure, and returning the mixture volume using Amagat's law assuming ideal mixture.
        The calculation is based on extensive quantities to keep it general, which is standard practice in properties packages;         
        if the specific volume (per kg or per mole of mixture), or its inverse (the density) is desired, the specified "amount" in the upper level should simply be the mass | molar fraction.
        Only single-phase (S | L | V) calculation is allowed for the moment; when a mixture involves multiple phases, the upper level model must call the present method for each phase.

        Parameters
        ----------
        T : float 
            Temperature
        P : float 
            Pressure.
        amount : float 
            Mass or  of the mixture, depending on the composition basis.
        phase : str
            S, L or V 
        composition_basis : str
            mass or molar

        Returns
        -------
        Volume: float 
            Volume of the specified amount of mixture under the specified temperature and pressure
        '''

        V_total = calculate_ideal_mixture_property(
            T,
            P,
            amount,
            phase,            
            composition_basis,
            Physical_properties.species_data,
            calc_volume
        )

        return Quantity(V_total, 'm3')


    # Mixture enthalpy
    @staticmethod
    def Enthalpy(T, P, amount, phase='V', composition_basis='mass'):
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
        amount : float 
            Amount of mixture, specified in terms of mass or substance depending on the composition basis.
        phase : str
            S, L or V 
        composition_basis : str
            mass or molar

        Returns
        -------
        H_total: float 
            Enthalpy of the specified amount of mixture under the specified temperature and pressure          
        '''

        H_total = calculate_ideal_mixture_property(
            T,
            P,
            amount,
            phase,            
            composition_basis,
            Physical_properties.species_data,
            calc_enthalpy
        )

        return Quantity(H_total, 'J')
    
 
    # Mixture heat capacity
    @staticmethod
    def Heat_capacity(T, P, amount, phase='V', composition_basis='mass'):
        '''
        Calculating the heat capacity of individual species at the specified temperature and pressure, and returning the mixture heat capacity, assuming ideal mixture.
        The calculation is based on extensive quantities to keep it general, which is standard practice in properties packages; 
        if the specific heat capacity (per kg or per mole of mixture) is desired, the specified "amount" in the upper level should simply be the mass | molar fraction.
        Only single-phase (S | L | V) calculation is allowed for the moment; when a mixture involves multiple phases, the upper level model must call the present method for each phase.

        Parameters
        ----------
        T : float 
            Temperature
        P : float 
            Pressure.
        amount : float 
            Amount of mixture, specified in terms of mass or substance depending on the composition basis.
        phase : str
            S, L or V 
        composition_basis : str
            mass or molar

        Returns
        -------
        Cp_total: float 
            Constant pressure heat capacity of the specified amount of mixture under the specified temperature and pressure            
        '''

        Cp_total = calculate_ideal_mixture_property(
            T,
            P,
            amount,
            phase,            
            composition_basis,
            Physical_properties.species_data,
            calc_heat_capacity
        )

        return Quantity(Cp_total, 'J/delta_K')
    

    # Saturation pressure of pure water 
    @staticmethod
    def Water_saturation_pressure(T):
        '''
        Calculates the saturation pressure of pure water 

        Parameters
        ----------
        T : float 
            Temperature

        Returns
        -------
        Psat: float 
            Saturation pressure of water under the specified temperature 
        '''    

        Psat = calc_water_saturation_pressure(T)  

        return Psat


    # Viscosity of a gas mixture or pure liquid water 
    @staticmethod
    def Viscosity(T, P, composition, phase='V', composition_basis='mass'):
        '''
        Calculates the saturation pressure of pure water 

        Parameters
        ----------
        T : float 
            Temperature.
        P : float 
            Pressure.
        amount : float 
            Amount of mixture, specified in terms of mass or substance depending on the composition basis.
        phase : str
            S, L or V 
        composition_basis : str
            mass or molar.

        Returns
        -------
        Viscosity: float 
            Viscosity of the gas mixture or pure water 
        '''    

        if phase =='V':
            Viscosity = calculate_wilke_mixture_property(
                T,
                P,
                composition,
                phase,            
                composition_basis,
                Physical_properties.species_data,
                calc_viscosity
            )

        elif phase == 'L':
            Viscosity = calculate_Arrhenius_mixture_property( # valid for non-polar mixtures only
                T,
                P,
                composition,
                phase,            
                composition_basis,
                Physical_properties.species_data,
                calc_viscosity
            )

        else:
            raise ValueError(f"{phase} phase not supported for viscosity calculation")

        return Quantity(Viscosity, 'Pa * s')