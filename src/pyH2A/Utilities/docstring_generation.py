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

from pyH2A.Utilities.constants import (SPECIAL_MIDDLE_KEYS,
                                       TYPE_KEY, OPTIONS_KEY, BOUNDS_KEY)
from pyH2A.Utilities.IO.output_inserter import special_top_level_keys

DESCRIPTION_KEY = 'description'

_TYPE_ORDER = [int, float, str, bool, dict, list, tuple, np.ndarray]
_TYPE_PROSE = {int: 'int', float: 'float', str: 'str', bool: 'bool',
              dict: 'dict', list: 'list', tuple: 'tuple', np.ndarray: 'ndarray'}


def _type_set_to_prose(type_set):
    """Convert a set of Python types to canonical prose.

    Parameters
    ----------
    type_set : set of type
        Set of Python types to convert. Types known to this documentation
        generator are rendered using the order defined by ``_TYPE_ORDER``.

    Returns
    -------
    str
        Type names joined by ``" or "``.

    Examples
    --------
    >>> _type_set_to_prose({int, float})
    'int or float'
    >>> _type_set_to_prose({dict})
    'dict'
    """

    ordered = [t for t in _TYPE_ORDER if t in type_set]
    ordered += [t for t in type_set if t not in _TYPE_ORDER]

    return ' or '.join(
        _TYPE_PROSE.get(
            t,
            getattr(t, '__name__', str(t))
        )
        for t in ordered
    )


def _format_cell(key, value):
    """Convert a specification value into documentation text.

    Scalar values are converted directly to strings. Type sets are converted
    to canonical type prose. Nested dictionaries are expanded into separate
    lines within the same table cell.

    Parameters
    ----------
    key : str
        Specification key associated with ``value``. Special handling is
        applied to ``TYPE_KEY``, ``OPTIONS_KEY``, and ``BOUNDS_KEY``.
    value : object
        Specification value to format.

    Returns
    -------
    str
        Text representation suitable for use as an RST table cell.

    Examples
    --------
    >>> _format_cell('type', {int, float})
    'int or float'

    >>> _format_cell('optional', False)
    'False'

    >>> _format_cell(
    ...     'Value',
    ...     {'type': {int, float}, 'bounds': (0, None)}
    ... )
    '| type: int or float\\n| bounds: (0, None)'
    """

    if value is None:
        return ''

    if key == TYPE_KEY:
        return _type_set_to_prose(value)

    if isinstance(value, dict):
        parts = []

        for subkey, subvalue in value.items():

            if subkey == TYPE_KEY and isinstance(subvalue, set):
                subvalue = _type_set_to_prose(subvalue)

            elif subkey == OPTIONS_KEY and subvalue:
                subvalue = ', '.join(
                    repr(option) for option in sorted(subvalue)
                )

            elif subkey == BOUNDS_KEY and isinstance(subvalue, tuple):
                lower, upper = subvalue
                subvalue = f'({lower}, {upper})'

            parts.append(f'{subkey}: {subvalue}')

        # Use a line block so Sphinx creates real line breaks.
        return '\n'.join(f'| {part}' for part in parts)

    return str(value)


def _render_table(title, rows):
    """Render one top-level specification as an RST list-table.

    The table contains one row for each middle-level specification key.
    Columns are determined dynamically from the keys present in the rows.
    The internal ``_name`` key is used for the row name and is not rendered
    as a separate specification column.

    Parameters
    ----------
    title : str
        Title of the table, normally the top-level specification key.
    rows : list of dict
        Specification rows. Each row must contain an internal ``_name`` key
        identifying the parameter or output represented by that row.

    Returns
    -------
    list of str
        RST lines representing the table. Returns an empty list when
        ``rows`` is empty.

    Examples
    --------
    A row such as::

        {
            '_name': 'Design capacity',
            'Value': {'type': {int, float}, 'bounds': (0, None)},
            'Unit': {'dimension': 'energy'},
            'optional': False,
            'description': 'Full design capacity.'
        }

    is rendered as a table row with columns for ``Value``, ``Unit``,
    ``optional``, and ``description``.
    """

    if not rows:
        return []

    # Find every inner key used by the rows.
    # Keep the order in which keys first appear.
    columns = []

    for row_dict in rows:
        for key in row_dict:
            if key not in columns:
                columns.append(key)

    # _name is our internal helper and must never become a table column.
    columns = [
        column for column in columns
        if column != '_name'
    ]

    number_of_columns = len(columns) + 1

    lines = [
        title,
        '-' * len(title),
        '',
        '.. list-table::',
        '   :header-rows: 1',
        '   :widths: ' + ' '.join(
            ['25'] * number_of_columns
        ),
        '',
        '   * - Name',
    ]

    # Header
    for column in columns:
        lines.append(f'     - {column}')

    # Rows
    for row_dict in rows:

        name = row_dict['_name']

        lines.append(f'   * - ``{name}``')

        for column in columns:

            value = row_dict.get(column, '')
            cell = _format_cell(column, value)

            if not cell:
                lines.append('     -')
                continue

            cell_lines = cell.splitlines()

            # First line starts the table cell.
            lines.append(f'     - {cell_lines[0]}')

            # Remaining lines belong to the same cell.
            for continuation in cell_lines[1:]:
                lines.append(f'       {continuation}')

    lines.append('')

    return lines


def _render_input_tables(input_dict):
    """Render all input specifications as RST tables.

    Each top-level key in ``input_dict`` becomes a separate table. Middle-level
    keys become table rows, while the keys inside each middle-level
    specification become table columns.

    Parameters
    ----------
    input_dict : dict
        Plugin input specification. The expected structure is::

            {
                'Top level': {
                    'Parameter': {
                        'Value': ...,
                        'Unit': ...,
                        'optional': ...,
                        'description': ...
                    }
                }
            }

    Returns
    -------
    list of str
        RST lines containing all generated input tables.

    Notes
    -----
    Keys listed in ``SPECIAL_MIDDLE_KEYS`` are skipped because they represent
    internal input structures rather than normal documented parameters.
    """

    lines = []

    for top_key, table_dict in input_dict.items():
        rows = []

        for middle_key, row_dict in table_dict.items():

            if middle_key in SPECIAL_MIDDLE_KEYS:
                continue

            row = dict(row_dict)
            row['_name'] = middle_key
            rows.append(row)

        lines += _render_table(top_key, rows)

    return lines


def _render_output_tables(output_dict):
    """Render all output specifications as RST tables.

    Normal output specifications are rendered directly from their top-level
    and middle-level keys. Special output structures listed in
    ``special_top_level_keys`` are expanded through their
    ``sum_all_tables`` structure.

    Parameters
    ----------
    output_dict : dict
        Plugin output specification. Normal output structures are expected
        to follow the form::

            {
                'Top level': {
                    'Output': {
                        'Value': ...,
                        'optional': ...,
                        'description': ...
                    }
                }
            }

        Special output structures may contain::

            {
                'special_insertions': {
                    'sum_all_tables': {
                        'Group': {
                            'Output': {...}
                        }
                    }
                }
            }

    Returns
    -------
    list of str
        RST lines containing all generated output tables.
    """

    lines = []

    for top_key, table_dict in output_dict.items():

        if top_key in special_top_level_keys:

            sum_all_tables = table_dict.get('sum_all_tables', {})

            for group_key, group_dict in sum_all_tables.items():

                rows = []

                for middle_key, row_dict in group_dict.items():

                    row = dict(row_dict)
                    row['_name'] = middle_key
                    rows.append(row)

                lines += _render_table(group_key, rows)

            continue

        rows = []

        for middle_key, row_dict in table_dict.items():

            row = dict(row_dict)
            row['_name'] = middle_key
            rows.append(row)

        lines += _render_table(top_key, rows)

    return lines


def generate_docstring(summary, input_dict, output_dict, notes=None):
    """Generate a NumPy-style class docstring from plugin specifications.

    Parameters
    ----------
    summary : str
        One-line or short paragraph summarizing what the plugin does. This is
        the only part of the generated docstring that is not derived from
        ``input_dict`` or ``output_dict``.

    input_dict : dict
        Plugin input specification as passed to
        ``input_resolver_function``.

    output_dict : dict
        Plugin output specification as passed to
        ``output_inserter_function``.

    notes : str, optional
        Free-form text for information that cannot be expressed by the
        structured specifications, such as internal sub-keys of a
        dict-typed output or plugin-instance attributes read directly by
        other modules. Rendered as a NumPy-style ``Notes`` section.

    Returns
    -------
    str
        Complete generated NumPy-style docstring, ready to be assigned to a
        plugin class's ``__doc__``.
    """

    lines = [
        textwrap.dedent(summary).strip(),
        '',
    ]

    lines += [
        'Parameters',
        '----------',
        '',
    ]

    lines += _render_input_tables(input_dict)

    lines += [
        'Outputs',
        '-------',
        '',
    ]

    lines += _render_output_tables(output_dict)

    if notes:
        lines += [
            'Notes',
            '-----',
            '',
            notes.strip(),
            '',
        ]

    return '\n'.join(lines).rstrip() + '\n'