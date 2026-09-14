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

def openLCA_to_pyH2A_unit(unit: str, return_reference: bool = False):
    '''Translate an openLCA unit string into its pyH2A equivalent.

    ``OPEN_LCA_CONFIG`` only lists the openLCA-specific spellings that pyH2A
    cannot parse as they stand (e.g. ``'Item(s)'`` or ``'kg CO2-Eq'``). Units
    that are already valid pyH2A units (e.g. ``'kg'``, ``'MJ'``, ``'kWh'``)
    are therefore absent from it and are passed through unchanged.

    Parameters
    ----------
    unit : str
        The unit string (from openLCA) to process.
    return_reference : bool, optional
        If ``True``, return the bare unit and its reference label separately,
        instead of the single string with the label in brackets. Used when the
        unit is one token of a composite unit, since
        :class:`~pyH2A.Utilities.Unit_Handler.quantity.Quantity` takes the
        labels of a composite unit as a separate ``reference`` list.

    Returns
    -------
    str or tuple of (str, str or None)
        The unit string in pyH2A format, with its reference label attached in
        brackets (e.g. ``'kg[$CO_{2}$-Eq]'``) when the unit has one. If
        ``return_reference`` is ``True``, a ``(unit, reference)`` tuple is
        returned instead, with ``reference`` set to ``None`` for units that
        carry no label. The tuple shape does not depend on whether the unit is
        listed in ``OPEN_LCA_CONFIG``, so callers can always unpack it.
    '''
    # Ensure unit is a string and remove leading/trailing whitespace
    unit = str(unit).strip()

    # If the unit is not in the OpenLCA config, use it unchanged: it is either
    # already a valid pyH2A unit, or it fails later in the unit parser, which
    # names the offending token.
    unit_dict = OPEN_LCA_CONFIG.get(unit, {'unit': unit, 'reference': None})

    # Unit and reference returned separately, for use as one token of a composite unit
    if return_reference:
        return unit_dict['unit'], unit_dict['reference']

    # If the unit has no reference, return the pyH2A unit on its own
    if unit_dict['reference'] is None:
        return unit_dict['unit']

    # If the unit has a reference, return the pyH2A unit with reference in brackets
    return f'{unit_dict["unit"]}[{unit_dict["reference"]}]'


if __name__ == "__main__":
    openlca_unit = "kg CO2-Eq"

    print(openLCA_to_pyH2A_unit(openlca_unit))  # Expected output: "kg[$CO_{2}$-Eq]"
