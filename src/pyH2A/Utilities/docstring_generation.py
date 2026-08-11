'''Generate NumPy-style plugin docstrings from `input_dict`/`output_dict` specs.

Plugin modules define a structured `input_dict`/`output_dict` describing every
parameter/output (type, dimension, optionality, description). This module walks
those same structures to produce documentation text, so the docstring can never
drift from the spec it describes. Intended use, from within a plugin module::

    class Some_Plugin:
        __doc__ = generate_docstring("One-line summary.", input_dict, output_dict)
'''

import textwrap

import numpy as np

from pyH2A.Utilities.input_modification import identify_bottom_keys
from pyH2A.Utilities.constants import (WILDCARD_MARKER, SPECIAL_MIDDLE_KEYS,
                                       OPTIONAL_KEY, TYPE_KEY, OPTIONS_KEY)
from pyH2A.Utilities.IO.output_inserter import special_top_level_keys, special_keys as OUTPUT_SPECIAL_KEYS

DESCRIPTION_KEY = 'description'

_TYPE_ORDER = [int, float, str, bool, dict, list, tuple, np.ndarray]
_TYPE_PROSE = {int: 'int', float: 'float', str: 'str', bool: 'bool',
              dict: 'dict', list: 'list', tuple: 'tuple', np.ndarray: 'ndarray'}

_INDENT = '    '
_WRAP_WIDTH = 88

def _type_set_to_prose(type_set):
	'''Convert a set of Python types (e.g. `{int, float}`) to canonical prose
	(e.g. `"int or float"`), using a fixed order so the result does not depend
	on set iteration order.
	'''

	ordered = [t for t in _TYPE_ORDER if t in type_set]
	ordered += [t for t in type_set if t not in _TYPE_ORDER] # fallback for unmapped types

	return ' or '.join(_TYPE_PROSE.get(t, getattr(t, '__name__', str(t))) for t in ordered)

def _join_path(top_key, middle_key, bottom_key, table_is_group):
	'''Join a table/row/column path using the same notation as the existing
	hand-written docstrings: a double arrow (`>>`) directly after a wildcard
	table-group key (`table_is_group`), a single arrow (`>`) otherwise
	(including for a wildcard row within a concrete table).
	'''

	if table_is_group:
		return f'{top_key} >> {bottom_key}'

	return f'{top_key} > {middle_key} > {bottom_key}'

def _walk_input_dict(input_dict):
	'''Walk `input_dict` and yield `(path, type_prose, optional, description)`
	for every parameter, in dict-insertion order. Skips `sum_tables` metadata
	entries; relies on `identify_bottom_keys` for Value/Unit(/Path) pairing so
	this can't disagree with how the input resolver actually resolves rows.
	'''

	entries = []

	for top_key, table_dict in input_dict.items():
		table_is_group = WILDCARD_MARKER in top_key

		for middle_key, row_dict in table_dict.items():
			if middle_key in SPECIAL_MIDDLE_KEYS:
				continue

			optional = row_dict.get(OPTIONAL_KEY, False)
			description = row_dict.get(DESCRIPTION_KEY, '')

			for group in identify_bottom_keys(row_dict, return_as_lists = True).values():
				value_key = group[0]
				value_spec = row_dict[value_key]

				if TYPE_KEY not in value_spec:
					continue

				type_prose = _type_set_to_prose(value_spec[TYPE_KEY])

				options = value_spec.get(OPTIONS_KEY)
				if options:
					type_prose += ' {{{0}}}'.format(', '.join(repr(o) for o in sorted(options)))

				path = _join_path(top_key, middle_key, value_key, table_is_group)
				entries.append((path, type_prose, optional, description))

	return entries

def _walk_output_row(top_key, middle_key, row_dict):
	'''Yield `(path, type_prose, optional, description)` for every non-metadata
	bottom key of a single output row.
	'''

	entries = []

	optional = row_dict.get(OPTIONAL_KEY, False)
	description = row_dict.get(DESCRIPTION_KEY, '')

	for bottom_key, value_spec in row_dict.items():
		if bottom_key in OUTPUT_SPECIAL_KEYS:
			continue

		type_prose = _type_set_to_prose(value_spec[TYPE_KEY])
		path = f'{top_key} > {middle_key} > {bottom_key}'
		entries.append((path, type_prose, optional, description))

	return entries

def _walk_output_dict(output_dict):
	'''Walk `output_dict` and yield `(path, type_prose, optional, description)`
	for every output, in dict-insertion order. Handles `special_insertions >
	sum_all_tables`, which holds both per-table wildcard-group results and
	per-group aggregate results, none of which are plain output rows.
	'''

	entries = []

	for top_key, table_dict in output_dict.items():
		if top_key in special_top_level_keys:
			for group_key, group_dict in table_dict.get('sum_all_tables', {}).items():
				for row_key, row_dict in group_dict.items():
					entries.extend(_walk_output_row(group_key, row_key, row_dict))
			continue

		for middle_key, row_dict in table_dict.items():
			entries.extend(_walk_output_row(top_key, middle_key, row_dict))

	return entries

def _render_entry(path, type_prose, optional, description):
	header = f'{path} : {type_prose}'
	if optional:
		header += ', optional'

	if not description:
		return header

	body = textwrap.fill(description, width = _WRAP_WIDTH,
						 initial_indent = _INDENT, subsequent_indent = _INDENT)

	return header + '\n' + body

def _render_section(title, underline_char, entries):
	if not entries:
		return []

	lines = [title, underline_char * len(title)]
	for entry in entries:
		lines.append(_render_entry(*entry))

	lines.append('')

	return lines

def generate_docstring(summary, input_dict, output_dict, notes = None):
	'''Generate a NumPy-style class docstring from a plugin's `input_dict`/
	`output_dict` specs.

	Parameters
	----------
	summary : str
		One-line (or short paragraph) summary of what the plugin does. This is
		the only part of the docstring not derived from `input_dict`/
		`output_dict`.
	input_dict : dict
		Plugin's `input_dict`, as passed to `input_resolver_function`.
	output_dict : dict
		Plugin's `output_dict`, as passed to `output_inserter_function`.
	notes : str, optional
		Freeform text for content the structured specs cannot express (e.g.
		the internal sub-keys of a dict-typed output, or plugin-instance
		attributes read directly by other modules). Rendered as a NumPy
		"Notes" section.

	Returns
	-------
	docstring : str
		Generated docstring, ready to be assigned to a plugin class's
		`__doc__`.
	'''

	lines = [textwrap.dedent(summary).strip(), '']
	lines += _render_section('Parameters', '-', _walk_input_dict(input_dict))
	lines += _render_section('Returns', '-', _walk_output_dict(output_dict))

	if notes:
		lines += ['Notes', '-----', notes.strip(), '']

	return '\n'.join(lines).rstrip() + '\n'

def generate_plugin_docstring(plugin_class, summary):

	class DocDCF:
		class functional_unit:
			dimension = 'dimensionless'   # placeholder, only used for doc generation
		unit = None

	instance = plugin_class.__new__(plugin_class)
	instance._set_up(DocDCF())

	plugin_class.__doc__ = generate_docstring(
        summary,
        instance.input_dict,
        instance.output_dict
    )