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
    Split a composite unit string into its clean unit expression and a
    position-aligned list of per-token bracketed reference labels.

    Scans `unit_str` once, left to right, using plain string methods
    (`.find('[')` / `.find(']')`) to locate bracket segments, and reuses
    `TOKEN_PATTERN` (the same tokenizer `parse_composite_unit` itself uses)
    only on the bracket-free stretches of text between brackets. Because
    tokenizing never runs on bracket contents, a multi-word label (e.g.
    `kg[grid electricity]`) is never torn apart by whitespace-splitting.

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
        One entry per token, in the same order as `clean_unit_str`'s own
        tokens (operator tokens included as `None`). Each entry is the
        bracketed label for that token, or `None` if that token had no (or
        an empty) label. Empty if no `[` is present. If any bracket is
        malformed (unclosed, or has no unit token immediately before it),
        `unit_str` is returned unmodified with an empty list, so that it
        fails naturally downstream during unit parsing.
    """
    # Fast path: keeps bracket-free calls (the vast majority of ~122 real production call sites) cheap
    # by skipping the scan entirely when there's nothing to parse.
    if '[' not in unit_str:
        return unit_str.strip(), []

    segments = []
    pos = 0

    while True:
        open_idx = unit_str.find('[', pos)
        if open_idx == -1:
            for tok in [t.strip() for t in TOKEN_PATTERN.split(unit_str[pos:]) if t and t.strip()]:
                segments.append(('token', tok))
            break

        stretch_tokens = [t.strip() for t in TOKEN_PATTERN.split(unit_str[pos:open_idx]) if t and t.strip()]

        # Covers a bracket with nothing preceding it and a bracket attached to an operator instead of a
        # unit token — in both cases we deliberately don't guess, letting parse_composite_unit raise its
        # own clear error downstream.
        if not stretch_tokens or stretch_tokens[-1] in ('*', '/', '(', ')'):
            return unit_str, []

        for tok in stretch_tokens[:-1]:
            segments.append(('token', tok))

        close_idx = unit_str.find(']', open_idx)
        if close_idx == -1:
            return unit_str, []

        label = unit_str[open_idx + 1:close_idx].strip()
        segments.append(('labeled', stretch_tokens[-1], label if label else None))

        pos = close_idx + 1

    clean_tokens = []
    reference = []
    for segment in segments:
        if segment[0] == 'token':
            clean_tokens.append(segment[1])
            reference.append(None)
        else:
            clean_tokens.append(segment[1])
            reference.append(segment[2])

    clean_unit_str = ' '.join(clean_tokens)

    return clean_unit_str, reference


def check_reference_match(requested_reference, stored_reference, unit_tokens):
    """
    Confirm a requested lookup's reference labels don't conflict with a
    Quantity's own stored reference labels, position by position.

    Only positions where the *requested* side has an actual (non-`None`)
    label are checked — the caller wasn't asking about any other position,
    so those are silently skipped regardless of what (if anything) is
    stored there.

    Parameters
    ----------
    requested_reference : list or None
        Position-aligned reference labels parsed from the requested lookup
        unit string. Empty/`None` if the lookup carried no labels.
    stored_reference : list or None
        Position-aligned reference labels already stored on the `Quantity`
        being looked up on. Empty/`None` if it was constructed without any.
    unit_tokens : list
        Clean unit-token strings for the requested lookup, position-aligned
        with `requested_reference` (e.g. `['g', '/', 'kg']`), used only to
        name the mismatched token in error messages.

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
        unit_tokens = [t.strip() for t in TOKEN_PATTERN.split(clean_target_unit) if t and t.strip()]
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

            # Expand the compact, unit-tokens-only reference= list into the same full,
            # position-aligned form (operators included as None) that bracket-derived
            # references already use, so __repr__ and check_reference_match need no
            # special-casing for where the labels came from.
            reference_iter = iter(reference)
            self.reference = [
                None if tok in ('*', '/', '(', ')') else next(reference_iter)
                for tok in raw_tokens
            ]

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
            `'J / kg'` with reference list `['energy', None, 'H2']`
            becomes `'J[energy] / kg[H2]'`.
        """
        if self.reference:
            # base_unit can be a composite (multiple tokens) and self.reference is now a position-aligned
            # list, so each token's label is looked up by its position (via zip), not by name — this
            # correctly distinguishes repeated unit names (e.g. two 'kg' tokens) carrying different labels.
            labeled_base_unit = ' '.join(
                f"{token}[{label}]" if label else token
                for token, label in zip(self.base_unit.split(' '), self.reference)
            )
            return f"Quantity({self.base_value}, '{labeled_base_unit}')"

        return f"Quantity({self.base_value}, '{self.base_unit}')"

    @property
    def unit_labels(self):
        """
        Reference labels for real unit tokens only, with operator positions removed.

        `self.reference` has one entry per raw token from
        `self.base_unit.split(' ')`, including a `None` placeholder for
        every operator token (`*`, `/`, `(`, `)`). This property zips
        `self.base_unit.split(' ')` with `self.reference` by position and
        filters out any pair whose token is an operator, returning just
        the remaining labels (still `None` for any unlabeled real unit
        token) in order. It is not the same as a hypothetical "actual
        labels only" view either: an unlabeled unit token still
        contributes a `None` entry here — only the operator-position
        entries are dropped, not every `None`.

        Returns
        -------
        unit_labels : list
            One entry per real unit token in `self.base_unit`, in order,
            each either that token's label or `None`.
        """
        return [
            label
            for token, label in zip(self.base_unit.split(' '), self.reference)
            if token not in ('*', '/', '(', ')')
        ]



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