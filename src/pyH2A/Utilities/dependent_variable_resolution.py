'''Shared dependent-variable resolution for `Analysis` modules (`Sensitivity_Analysis`,
`Monte_Carlo_Analysis`, ...).

Replaces the previous per-module config dict approach (e.g. the removed
`Analysis/config.py > DEPENDENT_VARIABLE_CONFIG`): the tracked output is instead specified
directly in the input file as a path with unit, in "{top_key > middle_key > bottom_key, unit}"
notation, and resolved against a fully processed `Discounted_Cash_Flow` object. This makes any
value reachable on `dcf.inp` usable as a dependent variable (H2 cost, any LCA impact category,
...) without a module having to know about it in advance.
'''

from pyH2A.Utilities.input_modification import parse_parameter, parse_path_with_unit, get_by_path

def resolve_dependent_variable(dcf, dependent_variable_string):
	'''Resolve the tracked output value from a (fully processed) ``Discounted_Cash_Flow`` object.

	Parameters
	----------
	dcf : Discounted_Cash_Flow
		Fully processed ``Discounted_Cash_Flow`` object (i.e. after its workflow has run),
		whose ``.inp`` contains resolved ``Quantity`` objects.
	dependent_variable_string : str
		Path with unit, in "{top_key > middle_key > bottom_key, unit}" notation,
		identifying which value in ``dcf.inp`` to read out.

	Returns
	-------
	value : float
		Numeric value of the resolved ``Quantity``, in the requested unit.

	Notes
	-----
	No error handling is performed here: an invalid/non-resolving path is allowed to raise
	its natural ``KeyError``/``AttributeError``, rather than silently falling back to a
	default value.
	'''

	path_alone, unit = parse_path_with_unit(dependent_variable_string)
	parsed_path = parse_parameter(path_alone)
	quantity = get_by_path(dcf.inp, parsed_path)

	return quantity.unit[unit]

def split_dependent_variable_path(dependent_variable_string):
	'''Split a "{top_key > middle_key > bottom_key, unit}" dependent-variable string into
	a descriptive header for its path and its unit.

	Parameters
	----------
	dependent_variable_string : str
		Path with unit, in "{top_key > middle_key > bottom_key, unit}" notation.

	Returns
	-------
	header : str
		Descriptive component of the path (e.g. 'Levelized cost', 'Climate change'), used
		by callers as a default header/label and to build things like plot titles.
	unit : str
		Unit string from the path.

	Notes
	-----
	Most paths in pyH2A end in the generic bottom key ``Value`` (per the
	``top_key > middle_key > bottom_key`` convention used throughout input files), in which
	case the *second-to-last* path component is the descriptive one (e.g.
	'Dependent Variables > Levelized cost > Value'). Some paths instead reach into a
	dict of named results *below* their own ``Value`` key (e.g.
	'Life Cycle Assessment > Results > Value > Climate change'), in which case the last
	component is already the descriptive one. This picks whichever applies.
	'''

	path_alone, unit = parse_path_with_unit(dependent_variable_string)
	parsed_path = parse_parameter(path_alone)

	if parsed_path[-1] == 'Value' and len(parsed_path) >= 2:
		header = parsed_path[-2]
	else:
		header = parsed_path[-1]

	return header, unit

def configure_dependent_variable(row, default_string = None, derive_label = True):
	'''Resolve a dependent-variable string, header, unit, and label from an input-file row.

	Shared by `Sensitivity_Analysis.configure_dependent_variable` and
	`Monte_Carlo_Analysis.configure_dependent_variable`, which differ only in where they
	look up `row` and how they want to handle a missing `Value`/`Label` - both expressed
	here via `default_string`/`derive_label`, rather than each module re-implementing the
	same path/unit/label parsing.

	Parameters
	----------
	row : dict
		The 'Dependent Variable' (or 'Dependent variable') row itself, e.g.
		``self.inp['Monte_Carlo_Analysis']['Dependent Variable']`` or
		``self.inp['Sensitivity_Analysis'].get('Dependent variable', {})``. May optionally
		contain 'Value' and 'Label' entries.
	default_string : str, optional
		Path with unit used when `row` has no 'Value' entry. If not provided (``None``),
		a missing 'Value' raises ``KeyError`` instead.
	derive_label : bool, optional
		If ``True`` (default), a missing 'Label' falls back to ``'{header} ({unit})'``.
		If ``False``, a missing 'Label' is left as ``None``, leaving the caller free to
		apply its own fallback (e.g. a hardcoded default display string).

	Returns
	-------
	dependent_variable_string : str
		The resolved path with unit.
	header : str
		Descriptive header, see `split_dependent_variable_path`.
	unit : str
		Unit string from the path.
	label : str or None
		Resolved display label.
	'''

	if 'Value' not in row:
		if default_string is None:
			raise KeyError(
				"Dependent Variable row must define 'Value', a path with unit, e.g. "
				"'{Dependent Variables > Levelized cost > Value, USD/kg}'."
			)
		dependent_variable_string = default_string
	else:
		dependent_variable_string = row['Value']

	header, unit = split_dependent_variable_path(dependent_variable_string)

	if derive_label:
		label = row.get('Label', '{0} ({1})'.format(header, unit))
	else:
		label = row.get('Label')

	return dependent_variable_string, header, unit, label
