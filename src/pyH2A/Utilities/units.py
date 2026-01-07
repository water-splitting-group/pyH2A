"""
units.py

Unit registry for pyH2A or other workflows.

Each category has:
- base_unit: canonical unit for calculations
- allowed_units: dictionary of units with description and conversion factor to base unit
"""

unit_registry = {
    'Energy': {
        'base_unit': 'MJ',
        'allowed_units': {
            'MJ':  {'description': 'Megajoules (Reference Unit)',        'conversion_to_base': 1.0},
            'J':   {'description': 'Joule',                                'conversion_to_base': 1.0e-6},
            'kJ':  {'description': 'Kilojoule',                            'conversion_to_base': 0.001},
            'kcal':{'description': 'Kilocalorie (International)',         'conversion_to_base': 0.00418},
            'kWh': {'description': 'Kilowatt hour',                       'conversion_to_base': 3.6},
            'MWh': {'description': 'Megawatt hour',                       'conversion_to_base': 3600.0},
            'GJ':  {'description': 'Gigajoules',                           'conversion_to_base': 1000.0},
            'TJ':  {'description': 'Terajoule',                            'conversion_to_base': 1.0e6},
            'PJ':  {'description': 'Petajoule',                            'conversion_to_base': 1.0e9},
            'Wh':  {'description': 'Watt hour',                            'conversion_to_base': 0.0036},
            'BTU': {'description': 'British thermal unit (International)', 'conversion_to_base': 0.00106},
            'TCE': {'description': 'Tonne coal equivalent',               'conversion_to_base': 2.93076e4},
            'TOE': {'description': 'Tonne of oil equivalent',             'conversion_to_base': 4.1868e4}
        }
    },
    'Energy_Battery': {
        'base_unit': 'kWh',
        'allowed_units': {
            'kWh':  {'description': 'Kilowatt hour (Reference Unit)',             'conversion_to_base': 1.0},
            'MJ':   {'description': 'Megajoules',                                 'conversion_to_base': 0.277778},
            'J':    {'description': 'Joule',                                       'conversion_to_base': 2.77778e-7},
            'kJ':   {'description': 'Kilojoule',                                   'conversion_to_base': 0.000277778},
            'kcal': {'description': 'Kilocalorie (International)',                'conversion_to_base': 0.001162},
            'MWh':  {'description': 'Megawatt hour',                               'conversion_to_base': 1000.0},
            'GJ':   {'description': 'Gigajoules',                                  'conversion_to_base': 277.778},
            'TJ':   {'description': 'Terajoule',                                   'conversion_to_base': 277778.0},
            'PJ':   {'description': 'Petajoule',                                   'conversion_to_base': 2.77778e8},
            'Wh':   {'description': 'Watt hour',                                   'conversion_to_base': 0.001},
            'BTU':  {'description': 'British thermal unit (International)',       'conversion_to_base': 2.94444e-4},
            'TCE':  {'description': 'Tonne coal equivalent',                       'conversion_to_base': 8139.7},
            'TOE':  {'description': 'Tonne of oil equivalent',                     'conversion_to_base': 11629.7}
        }
    },
    'Dimensionless': {
        'base_unit': '1',
        'allowed_units': {
            'fraction': {'description': 'Fraction (0–1)', 'conversion_to_base': 1.0},
            '%':        {'description': 'Percentage',     'conversion_to_base': 0.01}
        }
    }
}

def validate_unit(unit_category: str, unit: str, input_name: str = None):
    """Validate that a unit belongs to a unit category in the registry."""
    if unit_category not in unit_registry:
        raise ValueError(f"Unit category '{unit_category}' not found in unit registry.")
    if unit not in unit_registry[unit_category]['allowed_units']:
        allowed = list(unit_registry[unit_category]['allowed_units'].keys())
        msg = f"Unit '{unit}' is not allowed in category '{unit_category}'. Allowed units: {allowed}"
        if input_name:
            msg = f"Input '{input_name}': {msg}"
        raise ValueError(msg)
