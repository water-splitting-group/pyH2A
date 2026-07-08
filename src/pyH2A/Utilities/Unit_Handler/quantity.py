import re
import numpy as np

from pyH2A.Utilities.Unit_Handler.config import FLAT_MULTIPLIERS, FLAT_BASES, FLAT_DIMENSIONS, ABSOLUTE_TEMPERATURE

# Regex pattern for lenient parsing. Splits by math operators and keeps them as tokens.
# Filters out spaces and empty strings automatically based on regex logic.
TOKEN_PATTERN = re.compile(r'([*/()])|\s+')

def parse_composite_unit(unit_str):
    """
    Parse a composite unit (like 'kWh / cm2' or '(kWh * m)/m2') string into conversion multiplier, 
    resulting composite base unit, and composite dimension.

    This function expands user-facing units (e.g., `kWh / cm2` or
    `(kWh * m)/m2`) into:
    - a numerical multiplier to convert to base units,
    - a composite base-unit expression, and
    - a composite dimension expression.

    Parameters
    ----------
    unit_str : str
        Unit expression that may include `*`, `/`, and parentheses.

    Returns
    -------
    combined_multiplier : float
        Multiplier that converts `unit_str` into its composite base unit.
    combined_base_str : str
        Composite base unit expression (e.g., `J / m2`).
    combined_dim_str : str
        Composite dimension expression in the same operator layout.

    Raises
    ------
    ValueError
        If an unknown unit token is encountered or the expression cannot
        be evaluated.
    """
    tokens = TOKEN_PATTERN.split(unit_str)
    # Remove empty/whitespace tokens
    tokens = [t.strip() for t in tokens if t and t.strip()]

    multiplier_expr = []
    base_expr = []
    dim_expr = []
    
    for tok in tokens:
        if tok in ('*', '/', '(', ')'):
            multiplier_expr.append(tok)
            base_expr.append(tok)
            dim_expr.append(tok)
        elif tok.isdigit() or tok.replace('.', '', 1).isdigit():
            # Support explicit coefficients like '1/month' where 1 is the quantity component
            multiplier_expr.append(tok)
            base_expr.append(tok)
            dim_expr.append(tok)
        else:
            if tok not in FLAT_MULTIPLIERS:
                raise ValueError(f"Unknown unit encountered during parsing: '{tok}'")
            
            val = FLAT_MULTIPLIERS[tok]
            base = FLAT_BASES[tok]
            dim = FLAT_DIMENSIONS[tok]
            multiplier_expr.append(str(val))
            base_expr.append(base)
            dim_expr.append(dim)
            
    # Evaluate the multiplier using safe eval (restricting globals over a math string)
    multiplier_str = "".join(multiplier_expr)
    try:
        combined_multiplier = eval(multiplier_str, {"__builtins__": {}})
    except Exception as e:
        raise ValueError(f"Could not compute composite factor for '{unit_str}': {str(e)}")
        
    # Join with spaces to generate clean standard form (e.g. 'J / m2')
    combined_base_str = " ".join(base_expr)
    combined_dim_str = " ".join(dim_expr)
    
    return combined_multiplier, combined_base_str, combined_dim_str


def parse_reference(unit_str):
    """
    Split a unit string into its clean unit part and an optional bracketed reference label.

    Parameters
    ----------
    unit_str : str
        Unit expression that may contain a trailing bracketed reference,
        e.g. `kg[H2]`. Brackets are purely descriptive and are not
        considered during unit computations.

    Returns
    -------
    clean_unit_str : str
        Unit expression with the bracketed reference (if any) removed.
    reference : str or None
        Text found inside the brackets, or `None` if no brackets are
        present or the brackets are empty. If an opening bracket is
        found without a matching closing bracket, `unit_str` is
        returned unmodified with a `None` reference, so that it fails
        naturally downstream during unit parsing.
    """
    before, open_bracket, rest = unit_str.partition('[')

    if not open_bracket:
        return unit_str.strip(), None

    inside, close_bracket, after = rest.partition(']')

    if not close_bracket:
        return unit_str, None

    reference = inside.strip()
    clean_unit_str = (before + after).strip()

    return clean_unit_str, reference if reference else None


class UnitDictionary(dict):
    """
    A custom dictionary class designed for lazy runtime unit evaluations.
    Takes memory and performance into consideration by not calculating all unit conversions upfront.
    Guarantees that the 'base_unit' and 'supplied_unit' values are immediately present.
    """
    def __init__(self, quantity):
        """
        Create a lazy unit dictionary for a given `Quantity`.

        Parameters
        ----------
        quantity : Quantity
            Quantity instance providing base/supplied values and dimension.

        Returns
        -------
        None : None
            This initializer populates the dictionary in-place.
        """
        super().__init__()
        self._quantity = quantity
        
        # Populate guaranteed keys on init
        self[quantity.supplied_unit] = quantity.supplied_value
        self[quantity.base_unit] = quantity.base_value
        
    def __missing__(self, target_unit):
        """
        Lazily compute a unit value when dict[target_unit] is accessed.

        Parameters
        ----------
        target_unit : str
            Unit expression requested by the caller.

        Returns
        -------
        value : float or np.ndarray
            Value expressed in `target_unit`, cached in the dictionary.

        Raises
        ------
        KeyError
            If an absolute temperature conversion is requested for an
            unsupported unit.
        ValueError
            If the requested unit has a mismatched dimension.

        """
        # 1. Absolute Temperature Handling Path
        if self._quantity.is_absolute_temp:
            if target_unit not in ABSOLUTE_TEMPERATURE["supported_units"]:
                raise KeyError(f"Unsupported absolute temperature unit: {target_unit}")
                
            from_base_func = ABSOLUTE_TEMPERATURE["from_base"][target_unit]
            val = from_base_func(self._quantity.base_value)
            self[target_unit] = val
            return val
            
        # 2. Standard / Composite Units Handling Path
        target_multiplier, target_base, target_dim = parse_composite_unit(target_unit)
        
        # Verify dimension logic (light validation by stripping spaces)
        if target_dim.replace(" ", "") != self._quantity.dimension.replace(" ", ""):
            raise ValueError(
                f"Dimension mismatch: original dimension '{self._quantity.dimension}', "
                f"but requested dimension '{target_dim}' when mapping '{target_unit}'"
            )
        
        # Compute final target value seamlessly using numpy (if given) or scalar types
        val = self._quantity.base_value / target_multiplier
        self[target_unit] = val
        return val


class Quantity:
    """
    Lightweight computational replacement for Pint in pyH2A.

    The constructor parses the supplied unit into base units and a
    dimension string. Unit conversion is provided lazily through a
    `UnitDictionary` stored on `self.unit`.
    """
    __slots__ = ['supplied_value',
                 'supplied_unit',
                 'base_value',
                 'base_unit',
                 'dimension',
                 'unit',
                 'is_absolute_temp',
                 'reference']
    
    def __init__(self, value, unit_str):
        '''
        Create a `Quantity` from a numeric value and unit expression.

        Parameters
        ----------
        value : float, int, or np.ndarray
            Supplied numeric value.
        unit_str : str
            Unit expression compatible with the unit handler configuration.

        Returns
        -------
        None : None
            The instance is initialized in-place.
        '''

        self.supplied_value = value
        clean_unit_str, self.reference = parse_reference(unit_str.strip())
        self.supplied_unit = clean_unit_str
        self.is_absolute_temp = False

        # Detect hardcoded offset pathway
        if self.supplied_unit in ABSOLUTE_TEMPERATURE["supported_units"]:
            self.is_absolute_temp = True
            to_base_func = ABSOLUTE_TEMPERATURE["to_base"][self.supplied_unit]
            self.base_value = to_base_func(self.supplied_value)
            self.base_unit = ABSOLUTE_TEMPERATURE["base"]
            self.dimension = "absolute_temperature"
        else:
            # Handle multi-unit combinations (e.g. 'kWh/day' or '(J*m)/cm2')
            supplied_multiplier, base_unit_str, dim_str = parse_composite_unit(self.supplied_unit)
            self.base_value = self.supplied_value * supplied_multiplier
            self.base_unit = base_unit_str
            self.dimension = dim_str
            
        # Provide the required dictionary attribute for lazy multi-unit access
        self.unit = UnitDictionary(self)
        
    def __repr__(self):
        """
        Provide a compact representation using base units.

        Returns
        -------
        representation : str
            String form `Quantity(<base_value>, '<base_unit>')`. If a
            reference label was supplied, it is appended to the unit
            as `'<base_unit>[<reference>]'`.
        """
        if self.reference:
            return f"Quantity({self.base_value}, '{self.base_unit}[{self.reference}]')"

        return f"Quantity({self.base_value}, '{self.base_unit}')"



def test_quantity():
    """
    Run a simple, manual sanity check of quantity parsing and conversion.

    Returns
    -------
    None : None
        Prints example outputs to stdout.
    """

    array_test = np.array([[1.0, 2.0, 3.0],
                           [4.0, 5.0, 6.0]])
    #array_test = 10
    
    test_energy = Quantity(array_test, 'kWh / m2 / day')
    print(test_energy)  # Should show the original value and unit
    print(test_energy.dimension)


    # test_frequency = Quantity(1, '1 / day')
    # print(test_frequency)  # Should show the original value and unit

    test_energy = Quantity(10, 'J')
    print(test_energy.unit['eV'])  # Should convert to electronvolts

    test_dimensionless = Quantity(0.99, '-')
    print(test_dimensionless.dimension)



   # print(test_energy.unit['J / m2 / s'])  # Should convert to Joules


if __name__ == "__main__":
    test_quantity()