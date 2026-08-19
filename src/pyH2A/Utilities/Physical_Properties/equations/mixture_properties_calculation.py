from pyH2A.Utilities.Unit_Handler.quantity import Quantity
import math


def amount_to_fraction(amounts):
    '''
    Converts extensive amounts into fractions
    
    Parameters
    ----------
    amounts : dict 
        Dictionary of species and their respective amounts, mass or molar 

    Returns
    -------
    fractions: dict 
        Dictionary of species and their respective fractions
    '''

    fractions = {}
    denominator = 0
    for species in amounts.keys():
        denominator += amounts[species].base_value

    for species in amounts.keys():

        fractions[species] = Quantity(amounts[species].base_value / denominator,'-')

    return fractions


def substance_to_mass(molar_amounts, species_data):
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

    # If the molar_amounts input has the dimension of a fraction, we want to convert it into a quantity with substance dimension
    molar_amounts = {species: Quantity(molar_amounts[species].base_value, 'mol') for species in molar_amounts.keys()}
    
    denominator = 0
    mass_amount = {}
    mass_fraction = {}

    for species, quantity in molar_amounts.items():

        mass = (
            quantity.unit['mol']
            *
            species_data[species].molecular_weight.unit['kg/mol']
        )

        denominator += mass

        mass_amount[species] = Quantity(
            mass,
            'kg'
        )

    for species in mass_amount.keys():

        mass_fraction[species] = Quantity(
            mass_amount[species].unit['kg'] / denominator,
            '-'
        )

    return mass_amount, mass_fraction



def mass_to_substance(mass_amounts, species_data):
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

    # If the mass_amounts input has the dimension of a fraction, we want to convert it into a quantity with mass dimension
    mass_amounts = {species: Quantity(mass_amounts[species].base_value, 'kg') for species in mass_amounts.keys()}

    denominator = 0
    molar_amount = {}
    molar_fraction = {}
    
    for species, quantity in mass_amounts.items():

        mol = (
            quantity.unit['kg']
            /
            species_data[species].molecular_weight.unit['kg/mol']
        )

        denominator += mol

        molar_amount[species] = Quantity(
            mol,
            'mol'
        )

    for species in molar_amount.keys():

        molar_fraction[species] = Quantity(
            molar_amount[species].unit['mol'] / denominator,
            '-'
        )

    return molar_amount, molar_fraction


def calculate_ideal_mixture_property(
        T,
        P,        
        amount,
        phase,        
        composition_basis,
        species_data,
        property_function):
    
    '''
    Calls the properties function of each individual species and calculates the properties of a mixture 
    assuming the total the total quantity is the sum of the individual species contributions (ideal mixture)
    '''

    if composition_basis == 'mass':
        mass = amount
    else:
        mass, _ = substance_to_mass(amount, species_data)

    total = 0

    for species, quantity in mass.items():

        specific_property = property_function(
            species_data[species],
            T,
            P,
            phase
        )

        total += quantity.base_value*specific_property.base_value

    return total


def calculate_wilke_mixture_property(
        T,
        P,        
        composition,
        phase,        
        composition_basis,
        species_data,
        property_function):
    
    '''
    Calls the properties function of each individual species and calculates the properties of a mixture 
    using Wilke mixture equation.
    The calculated property being intensive, the composition must be a mass fraction or a molar fraction, not a total amount
    '''

    # as a safety net, ensure that the composition that is passed is a fraction, not an extensive amount
    composition = amount_to_fraction(composition)

    if composition_basis == 'molar':
        mol_fraction = composition
    else:
        _, mol_fraction = mass_to_substance(composition, species_data)

    # Calculation of individual species property:
    pure_property = {}
    for species in mol_fraction.keys():
        pure_property[species] = property_function(
            species_data[species],
            T,
            P,
            phase
        )

    # calculation of mixture property
    mixture_property = 0

    for species_i in mol_fraction.keys():
        denominator = 0
        for species_j in mol_fraction.keys():
            pure_i = pure_property[species_i].base_value
            pure_j = pure_property[species_j].base_value

            M_i = species_data[species_i].molecular_weight.unit['kg/mol']
            M_j = species_data[species_j].molecular_weight.unit['kg/mol']

            # interaction parameter
            phi_ij = (
                    (1 + (pure_i / pure_j)**0.5 * (M_j / M_i)**0.25)**2
                    /
                    (8 * (1 + M_i / M_j))**0.5
                )

            denominator += mol_fraction[species_j].unit['-'] * phi_ij

        mixture_property += (
            mol_fraction[species_i].unit['-']
            * pure_property[species_i].base_value
            / denominator
        )

    return mixture_property


def calculate_Arrhenius_mixture_property(
        T,
        P,        
        composition,
        phase,        
        composition_basis,
        species_data,
        property_function):
    '''
    Calls the properties function of each individual species and calculates the properties of a mixture 
    using Arrhenius mixture equation.
    The calculated property being intensive, the composition must be a mass fraction or a molar fraction, not a total amount
    '''

    # as a safety net, ensure that the composition that is passed is a fraction, not an extensive amount
    composition = amount_to_fraction(composition)

    if composition_basis == 'molar':
        mol_fraction = composition
    else:
        _, mol_fraction = mass_to_substance(composition, species_data)

    # Calculation of individual species property:
    pure_property = {}
    for species in mol_fraction.keys():
        pure_property[species] = property_function(
            species_data[species],
            T,
            P,
            phase
        )

    # calculation of mixture property
    mixture_property = 0

    for species in mol_fraction.keys():  
        mixture_property += mol_fraction[species].unit['-'] * math.log(pure_property[species].base_value)

    mixture_property = math.exp(mixture_property)

    return mixture_property