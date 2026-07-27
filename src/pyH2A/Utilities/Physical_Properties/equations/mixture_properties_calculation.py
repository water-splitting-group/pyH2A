from pyH2A.Utilities.Unit_Handler.quantity import Quantity


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

    # If the molar_amounts input has the dimension of a fraction, we want to convert it into a quantity with relevant dimension
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


def calculate_mixture_property(
        T,
        P,        
        amount,
        phase,        
        composition_basis,
        species_data,
        property_function):
    
    '''
    Calls the properties function of each individual species and calculates the properties of an ideal mixture
    '''

    if composition_basis == 'mass':
        # If the amount input has the dimension of a fraction, we want to convert it into a quantity with mass dimension
        mass = {species: Quantity(amount[species].base_value, 'kg') for species in amount.keys()}        
    else:
        # If the amount input has the dimension of a fraction, we want to convert it into a quantity with substance dimension
        substance = {species: Quantity(amount[species].base_value, 'mol') for species in amount.keys()}        
        mass, _ = substance_to_mass(substance, species_data)

    total = 0

    for species, quantity in mass.items():

        property_value = property_function(
            species_data[species],
            T,
            P,
            quantity,
            phase
        )

        total += property_value.base_value

    return total