OPEN_LCA_CONFIG = { 
        'Item(s)': {
                'dimension': 'dimensionless',
                'unit': 'Items',
                'reference': None
                },
        't': {
                'dimension': 'mass',
                'unit': 'ton',
                'reference': None
                },
        'CTUe': {
                'dimension': 'dimensionless',
                'unit': '-',
                'reference': "CTUe"
                },
        'CTUh': {
                'dimension': 'dimensionless',
                'unit': '-',
                'reference': "CTUh"
                },
        'dimensionless': {
                'dimension': 'dimensionless',
                'unit': '-',
                'reference': None
                },
        'disease incidence': {
                'dimension': 'dimensionless',
                'unit': '-',
                'reference': 'disease incidence'
                },
        'kBq U235-Eq': {
                'dimension': 'radioactivity',
                'unit': 'kBq',
                'reference': 'U235-Eq'
                },
        'kg CFC-11-Eq': {
                'dimension': 'mass',
                'unit': 'kg',
                'reference': 'CFC-11-Eq'
                },
        'kg CO2-Eq': {
                'dimension': 'mass',
                'unit': 'kg',
                'reference': '$CO_{2}$-Eq'
                },
        'kg SO2-Eq': {
                'dimension': 'mass',
                'unit': 'kg',
                'reference': 'SO2-Eq'
                },
        'kg CO2-eq': {
                'dimension': 'mass',
                'unit': 'kg',
                'reference': '$CO_{2}$-Eq'
                },
        'kg SO2-eq': {
                'dimension': 'mass',
                'unit': 'kg',
                'reference': 'SO2-eq'
                },
        'kg N-Eq': {
                'dimension': 'mass',
                'unit': 'kg',
                'reference': 'N-Eq'
                },
        'kg NMVOC-Eq': {
                'dimension': 'mass',
                'unit': 'kg',
                'reference': 'NMVOC-Eq'
                },
        'kg P-Eq': {
                'dimension': 'mass',
                'unit': 'kg',
                'reference': 'P-Eq'
                },
        'kg Sb-Eq': {
                'dimension': 'mass',
                'unit': 'kg',
                'reference': 'Sb-Eq'
                },
        'm3 world Eq deprived': {
                'dimension': 'volume',
                'unit': 'm3',
                'reference': 'world Eq deprived'
                },
        'MJ, net calorific value': {
                'dimension': 'energy',
                'unit': 'MJ',
                'reference': 'net calorific value'
                },
        'MJ-Eq': {
                'dimension': 'energy',
                'unit': 'MJ',
                'reference': 'Eq'
                },
        'mol H+-Eq': {
                'dimension': 'substance',
                'unit': 'mol',
                'reference': 'H+-Eq'
                },
        'mol N-Eq': {
                'dimension': 'substance',
                'unit': 'mol',
                'reference': 'N-Eq'
                },
        }

def openLCA_to_pyH2A_unit(unit: str, return_reference: bool = False) -> str:
    '''

    Parameters
    ----------
    unit : str
        The unit string (from OpenLCA) to process.

    Returns
    -------
    str
        The unit string in pyH2A format
    '''
    # Ensure unit is a string and remove leading/trailing whitespace and convert to lowercase
    unit = str(unit).strip() #.lower()  

    # If the unit is not in the OpenLCA config, return it unchanged
    if unit not in OPEN_LCA_CONFIG:
        return unit

    unit_dict = OPEN_LCA_CONFIG[unit]

    # If the unit has no reference, return the pyH2A unit
    if unit_dict['reference'] is None:
        return unit_dict['unit']

    # If the unit has a reference, return the pyH2A unit with reference in brackets
    elif return_reference:
        return unit_dict["unit"], unit_dict["reference"]

    else:
        return f'{unit_dict["unit"]}[{unit_dict["reference"]}]'



if __name__ == "__main__":
    openlca_unit = "kg CO2-Eq"

    print(openLCA_to_pyH2A_unit(openlca_unit))  # Expected output: "kg[CO2-Eq]"
