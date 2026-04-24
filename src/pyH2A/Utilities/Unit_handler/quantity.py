import re
import numpy as np

from .config import FLAT_MULTIPLIERS, FLAT_BASES, FLAT_DIMENSIONS, ABSOLUTE_TEMPERATURE

# Regex pattern for lenient parsing. Splits by math operators and keeps them as tokens.
# Filters out spaces and empty strings automatically based on regex logic.
TOKEN_PATTERN = re.compile(r'([*/()])|\s+')

def parse_composite_unit(unit_str):
    """
    Parses a composite unit string like 'kWh / cm2' or '(kWh * m)/m2'.
    Returns the conversion multiplier, the resulting composite base unit, and the composite dimension.
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


class UnitDictionary(dict):
    """
    A custom dictionary class designed for lazy runtime unit evaluations.
    Takes memory and performance into consideration by not calculating all unit conversions upfront.
    Guarantees that the 'base_unit' and 'supplied_unit' values are immediately present.
    """
    def __init__(self, quantity):
        super().__init__()
        self._quantity = quantity
        
        # Populate guaranteed keys on init
        self[quantity.supplied_unit] = quantity.supplied_value
        self[quantity.base_unit] = quantity.base_value
        
    def __missing__(self, target_unit):
        """
        Calculates requested unit value lazily when dict[target_unit] is called.
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
    Immediate parsing and instantiation with lazy unit value retrieval.
    """
    __slots__ = ['supplied_value', 'supplied_unit', 'base_value', 'base_unit', 'dimension', 'unit', 'is_absolute_temp']
    
    def __init__(self, value, unit_str):
        self.supplied_value = value
        self.supplied_unit = unit_str.strip()
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
        return f"Quantity({self.base_value}, '{self.base_unit}')"



def test_quantity():

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