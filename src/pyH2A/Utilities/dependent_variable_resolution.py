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
	the last component of its path and its unit.

	Parameters
	----------
	dependent_variable_string : str
		Path with unit, in "{top_key > middle_key > bottom_key, unit}" notation.

	Returns
	-------
	header : str
		Last component of the path (e.g. 'Levelized cost', 'Climate change'), used by
		callers as a default header/label and to build things like plot titles.
	unit : str
		Unit string from the path.
	'''

	path_alone, unit = parse_path_with_unit(dependent_variable_string)

	return parse_parameter(path_alone)[-1], unit
