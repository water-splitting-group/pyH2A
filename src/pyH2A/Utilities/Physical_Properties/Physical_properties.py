from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.Physical_Properties.data.Constants import IDEAL_GAS_CONSTANT
from pyH2A.Utilities.Physical_Properties.data.hydrogen import HYDROGEN
from pyH2A.Utilities.Physical_Properties.data.oxygen import OXYGEN
from pyH2A.Utilities.Physical_Properties.data.water import WATER
from pyH2A.Utilities.Physical_Properties.equations.properties_calculation import calc_volume, calc_enthalpy
from pyH2A.Utilities.Physical_Properties.equations.water_saturation import calc_water_saturation_pressure
#from pyH2A.Utilities.Physical_Properties.equations.combustion import calc_hydrogen_combustion_enthalpy

class Physical_properties:
    '''
    This class defines multiple constants (e.g. the ideal gas constant) as well as material properties characteristics (e.g. molecular weight).
    It also defines methods that calculate thermophysical properties of a mixture (e.g. enthalpy) using correlations derived from literature data.
    The variables are Quantity objects to make them easy to handle in plugins. 

    Supported methods: 
    - Substance_to_mass:
        converts a dictionary made of {species: molar amount} into a dictionary of mass amounts. Also returns the mass fractions.
    - Mass_to_substance: 
        converts a dictionary made of {species: mass amount} into a dictionary of molar amounts. Also returns the molar fractions.
    - Volume:
        calcualtes the volume of a mixture defined by a dictionary of amounts {species: mass or molar amount} at the specified temeprature and pressure, for the specified phase.
    - Enthalpy:
        calcualtes the enthalpy and the heat capacity at constant pressure of a mixture defined by a dictionary of amounts {species: mass or molar amount} at the specified temeprature and pressure, for the specified phase.
    - Water_saturation_pressure:
        calculates the saturation pressure of pure water steam at the specified temeprature.
    - Combustion_enthalpy:
        calculates the mass-specific combustion enthalpy of hydrogen.
    '''
    
    species_data = {
        'H2': HYDROGEN,
        'O2': OXYGEN,
        'H2O': WATER,
    }

    # Molecular weight of usual molecules. 
    MW = {
        species: data.molecular_weight
        for species, data in species_data.items()
    } 

    # Mass-based specific ideal gas constants
    specific_IG_constant = {}

    for species in MW.keys():

        specific_IG_constant[species] = Quantity(
            IDEAL_GAS_CONSTANT.unit['J/(mol*delta_K)']
            /
            MW[species].unit['kg/mol'],
            'J/(kg*delta_K)'
        )


    # Conversion of molar to mass amounts, and conversely
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

        denominator = 0
        mass_amount = {}
        mass_fraction = {}
        for species, quantity in molar_amounts.items():
            mass = (
                quantity.unit['mol']
                *
                Physical_properties.MW[species].unit['kg/mol']
            )
            denominator += mass
            mass_amount[species] = Quantity(
                mass,
                'kg'
            )

        for species in mass_amount.keys():
            mass_fraction[species] = Quantity(
                mass_amount[species].unit['kg']
                /
                denominator,
                '-'
            )

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

        denominator = 0
        molar_amount = {}
        molar_fraction = {}
        for species, quantity in mass_amounts.items():
            mol = (
                quantity.unit['kg']
                /
                Physical_properties.MW[species].unit['kg/mol']
            )
            denominator += mol
            molar_amount[species] = Quantity(
                mol,
                'mol'
            )
        for species in molar_amount.keys():

            molar_fraction[species] = Quantity(
                molar_amount[species].unit['mol']
                /
                denominator,
                '-'
            )
        return molar_amount, molar_fraction  


    # Mixture volume
    @staticmethod
    def Volume(T, P, amount, phase = 'V', composition_basis = 'mass'):
        '''
        Calculating the volume of individual species at the specified temperature and pressure, and returning the mixture volume, assuming ideal mixture.
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

        if composition_basis == 'mass':
            mass = amount
        else:
            mass, _ = Physical_properties.Substance_to_mass(amount)
        V_total = 0

        for species, quantity in mass.items():
            V_species = calc_volume(Physical_properties.species_data[species],T ,P , quantity, phase, Physical_properties.specific_IG_constant[species])
            V_total += V_species.unit['m3']

        return Quantity(V_total,'m3')


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
        Cp_total: float 
            Constant pressure heat capacity of the specified amount of mixture under the specified temperature and pressure            
        '''

        if composition_basis == 'mass':
            mass = amount
        else:
            mass, _ = Physical_properties.Substance_to_mass(amount)

        H_total = 0
        Cp_total = 0
        for species, quantity in mass.items():
            H, Cp = calc_enthalpy(Physical_properties.species_data[species], T, P, quantity, phase)
            H_total += H.unit['J']
            Cp_total += Cp.unit['J/delta_K']
        return (Quantity(H_total, 'J'), Quantity(Cp_total, 'J/delta_K'))


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
        saturation pressure: float 
            Saturation pressure of water under the specified temperature 
        '''
    @staticmethod
    def Water_saturation_pressure(T):
        return calc_water_saturation_pressure(T)  
