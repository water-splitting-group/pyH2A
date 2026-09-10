'''Shared dependent-variable resolution for `Analysis` modules (`Sensitivity_Analysis`,
`Monte_Carlo_Analysis`, ...).

The tracked output is specified in the input file as a path with unit, in
"{top_key > middle_key > bottom_key, unit}" notation, and resolved against a fully
processed `Discounted_Cash_Flow` object. This makes any value reachable on `dcf.inp`
usable as a dependent variable (H2 cost, any LCA impact category, ...) without a module
having to know about it in advance.
'''

from pyH2A.Utilities.input_modification import parse_parameter, parse_path_with_unit, get_by_path

DEFAULT_DEPENDENT_VARIABLE_STRING = '{Dependent Variables > Levelized cost > Value, USD/kg}'
'''Default dependent variable (H2 cost), used as `configure_dependent_variable()`'s
`default_string` so a missing `Dependent Variable` row falls back to H2 cost.'''

def resolve_dependent_variable(dcf, dependent_variable_string):
	'''Resolve the tracked output value from a (fully processed) ``Discounted_Cash_Flow`` object.

	Parameters
	----------
	dcf : Discounted_Cash_Flow
		Fully processed ``Discounted_Cash_Flow`` object, whose ``.inp`` contains
		resolved ``Quantity`` objects.
	dependent_variable_string : str
		Path with unit, in "{top_key > middle_key > bottom_key, unit}" notation.

	Returns
	-------
	value : float
		Numeric value of the resolved ``Quantity``, in the requested unit.

	Notes
	-----
	An invalid/non-resolving path raises its natural ``KeyError``/``AttributeError``
	rather than failing silently.
	'''

	path_alone, unit = parse_path_with_unit(dependent_variable_string)
	parsed_path = parse_parameter(path_alone)
	quantity = get_by_path(dcf.inp, parsed_path)

	return quantity.unit[unit]

def configure_dependent_variable(inp, table, row_name = 'Dependent Variable',
								 default_string = None, derive_label = True):
	'''Resolve a dependent-variable string, header, unit, and label from an input-file row.

	Parameters
	----------
	inp : dict
		Full input dictionary (e.g. ``self.inp``).
	table : str
		Name of the table the row lives in (e.g. 'Monte_Carlo_Analysis'). Looked up with
		``.get()``, so a missing table is treated the same as a missing row.
	row_name : str, optional
		Name of the row within `table` (e.g. 'Dependent Variable' vs `Sensitivity_Analysis`'s
		lowercase 'Dependent variable'). Defaults to 'Dependent Variable'.
	default_string : str, optional
		Path with unit used when `row` has no 'Value'. If ``None`` (default), a missing
		'Value' raises ``KeyError``. Otherwise a warning is printed and this is used.
	derive_label : bool, optional
		If ``True`` (default), a missing 'Label' falls back to `header`. If ``False``,
		it is left as ``None``.

	Returns
	-------
	dependent_variable_string : str
		The resolved path with unit.
	header : str
		Descriptive path component, e.g. 'Levelized cost'. Paths conventionally end in
		the generic bottom key ``Value``, in which case the *second-to-last* component
		is descriptive (e.g. 'Dependent Variables > Levelized cost > Value'); some paths
		instead reach into a dict of named results below their own ``Value`` (e.g.
		'... > Results > Value > Climate change'), where the last component already is.
	unit : str
		Unit string from the path.
	label : str or None
		Resolved display label.
	'''

	row = inp.get(table, {}).get(row_name, {})

	if 'Value' not in row:
		if default_string is None:
			raise KeyError(
				"Dependent Variable row must define 'Value', a path with unit, e.g. "
				"'{Dependent Variables > Levelized cost > Value, USD/kg}'."
			)
		print("Warning: No 'Value' found for the Dependent Variable row; defaulting to "
			  "'{0}'. If you configured a custom dependent variable, check the row name "
			  "and casing.".format(default_string))
		dependent_variable_string = default_string
	else:
		dependent_variable_string = row['Value']

	path_alone, unit = parse_path_with_unit(dependent_variable_string)
	parsed_path = parse_parameter(path_alone)

	if parsed_path[-1] == 'Value' and len(parsed_path) >= 2:
		header = parsed_path[-2]
	else:
		header = parsed_path[-1]

	if derive_label:
		label = row.get('Label', header)
	else:
		label = row.get('Label')

	return dependent_variable_string, header, unit, label
