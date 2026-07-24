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


REFERENCE_PATTERN = re.compile(r'(\w+)(?:\[([^\[\]]*)\])?')


def parse_reference(unit_str):
    """
    Split a composite unit string into its clean unit expression and a
    compact list of per-real-unit-token bracketed reference labels.

    Uses a single regex, REFERENCE_PATTERN, whose bracket group is
    optional, so one finditer pass walks through every real unit token
    in the string -- labeled or not -- while operator characters (*,
    /, (, )) are never matched at all and so never appear in the
    output.

    Parameters
    ----------
    unit_str : str
        Unit expression that may contain one or more bracketed reference
        labels attached to individual unit tokens, e.g.
        `kg[H2] / J[electricity]`. Brackets are purely descriptive and are
        not considered during unit computations.

    Returns
    -------
    clean_unit_str : str
        Unit expression with all bracketed references removed.
    reference : list
        One entry per REAL unit token only (operator tokens are never
        represented at all, not even as None), in the order those
        units appear. Each entry is that token's label, or None if it
        had no (or an empty) label. Empty if no [ is present. If any
        bracket character survives after substitution -- an unclosed
        bracket, a bracket with no unit token before it, or any other
        malformed placement -- unit_str is returned unmodified with an
        empty list, so it fails naturally downstream during unit parsing.
    """
    if '[' not in unit_str:
        return unit_str.strip(), []

    reference = [m.group(2).strip() if m.group(2) else None for m in REFERENCE_PATTERN.finditer(unit_str)]
    clean_unit_str = REFERENCE_PATTERN.sub(r'\1', unit_str).strip()

    if '[' in clean_unit_str or ']' in clean_unit_str:
        return unit_str, []

    return clean_unit_str, reference


def check_reference_match(requested_reference, stored_reference, unit_tokens):
    """
    Confirm a requested lookup's reference labels don't conflict with a
    Quantity's own stored reference labels, compact position by compact
    position.

    Only positions where the *requested* side has an actual (non-`None`)
    label are checked — the caller wasn't asking about any other position,
    so those are silently skipped regardless of what (if anything) is
    stored there.

    Parameters
    ----------
    requested_reference : list or None
        Compact, real-unit-token-aligned reference labels parsed from the
        requested lookup unit string (one entry per real unit token;
        operator positions are never represented). Empty/`None` if the
        lookup carried no labels.
    stored_reference : list or None
        Compact, real-unit-token-aligned reference labels already stored
        on the `Quantity` being looked up on (same shape as
        `requested_reference`). Empty/`None` if it was constructed
        without any.
    unit_tokens : list
        Clean, real-unit-token strings for the requested lookup, in the
        same compact order as `requested_reference` (operator tokens
        excluded, e.g. `['g', 'kg']` for `'g / kg'`), used only to name
        the mismatched token in error messages.

    Returns
    -------
    True : bool
        If every requested position either matches or had nothing stored
        to conflict with a `None` entry.

    Raises
    ------
    ValueError
        If a requested position has no corresponding stored label, or has
        a stored label that disagrees with it.
    """
    requested_reference = requested_reference or []
    stored_reference = stored_reference or []

    for i, requested_label in enumerate(requested_reference):
        if requested_label is None:
            continue

        stored_label = stored_reference[i] if i < len(stored_reference) else None

        if stored_label is None:
            raise ValueError(
                f"Reference mismatch for '{unit_tokens[i]}': requested '{requested_label}', but this "
                f"Quantity has no stored reference at this position."
            )

        if requested_label != stored_label:
            raise ValueError(
                f"Reference mismatch for '{unit_tokens[i]}': requested '{requested_label}', but stored "
                f"reference is '{stored_label}'."
            )

    return True


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
            If the requested unit has a mismatched dimension, or a
            requested reference label conflicts with this Quantity's own
            stored reference.

        """
        # 0. Reference-aware validation: strip any bracketed labels from the requested lookup key
        # before any unit math runs, and confirm they don't conflict (by position, not by unit name)
        # with this Quantity's own stored reference. Propagates as-is if it raises.
        clean_target_unit, requested_reference = parse_reference(target_unit)
        unit_tokens = [
            t.strip() for t in TOKEN_PATTERN.split(clean_target_unit)
            if t and t.strip() and t.strip() not in ('*', '/', '(', ')')
        ]
        check_reference_match(requested_reference, self._quantity.reference, unit_tokens)

        # 1. Absolute Temperature Handling Path
        if self._quantity.is_absolute_temp:
            if clean_target_unit not in ABSOLUTE_TEMPERATURE["supported_units"]:
                raise KeyError(f"Unsupported absolute temperature unit: {clean_target_unit}")

            from_base_func = ABSOLUTE_TEMPERATURE["from_base"][clean_target_unit]
            val = from_base_func(self._quantity.base_value)
            self[target_unit] = val
            return val

        # 2. Standard / Composite Units Handling Path
        target_multiplier, target_base, target_dim = parse_composite_unit(clean_target_unit)

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
    
    def __init__(self, value, unit_str, reference=None):
        '''
        Create a `Quantity` from a numeric value and unit expression.

        Parameters
        ----------
        value : float, int, or np.ndarray
            Supplied numeric value.
        unit_str : str
            Unit expression compatible with the unit handler configuration.
        reference : list, optional
            One label per real unit token in `unit_str` (excluding
            operators), e.g. `['H2', 'H2']` for `'J / kg'`. Mutually
            exclusive with bracketed labels already present in `unit_str`.

        Returns
        -------
        None : None
            The instance is initialized in-place.
        '''

        self.supplied_value = value
        clean_unit_str, self.reference = parse_reference(unit_str.strip())

        if reference is not None:
            if self.reference:
                raise ValueError(
                    "Cannot provide both bracketed labels in the unit string AND a separate "
                    "reference= argument - choose one."
                )

            raw_tokens = [t.strip() for t in TOKEN_PATTERN.split(clean_unit_str) if t and t.strip()]
            unit_token_count = len([t for t in raw_tokens if t not in ('*', '/', '(', ')')])

            if len(reference) != unit_token_count:
                raise ValueError(
                    f"reference= has {len(reference)} entries, but '{clean_unit_str}' has "
                    f"{unit_token_count} unit token(s) - lengths must match."
                )

            # reference= is already in the same compact, real-tokens-only shape parse_reference
            # itself now produces -- no expansion needed, just take a defensive copy.
            self.reference = list(reference)

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
            String form `Quantity(<base_value>, '<base_unit>')`. If
            reference labels were supplied, each labeled unit token in
            `base_unit` is reattached with its bracketed label, e.g.
            `'J / kg'` with reference list `['energy', 'H2']` becomes
            `'J[energy] / kg[H2]'`.
        """
        if self.reference:
            # self.reference is now compact (one entry per REAL unit token only, no operator
            # slots), while base_unit.split(' ') still includes operators -- walk base_unit's
            # own tokens and only advance through self.reference at non-operator positions.
            reference_iter = iter(self.reference)
            labeled_base_unit = ' '.join(
                token if token in ('*', '/', '(', ')') else (
                    f"{token}[{label}]" if (label := next(reference_iter)) else token
                )
                for token in self.base_unit.split(' ')
            )
            return f"Quantity({self.base_value}, '{labeled_base_unit}')"

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