'''Generate NumPy-style plugin docstrings from ``input_dict``/``output_dict``.

A plugin calls this in ``_set_up``, so its docstring always matches its specification::

    self.__doc__ = generate_docstring("One-line summary.", self.input_dict, self.output_dict)

The module is also a Sphinx extension (see :func:`setup`) that puts the generated
docstrings on the plugin pages. Any error fails the build.
'''

import textwrap

import numpy as np

from pyH2A.Utilities.constants import TYPE_KEY, OPTIONS_KEY
from pyH2A.Utilities.plugin_specification import instantiate_plugin_for_docs, iter_spec_rows

# Type names in the order they are listed.
_TYPE_NAMES = {int: 'int', float: 'float', str: 'str', bool: 'bool',
               dict: 'dict', list: 'list', tuple: 'tuple', np.ndarray: 'ndarray'}

# numpydoc handles the same autodoc event with priority 500; the generated
# docstring must replace its result, so it runs afterwards.
AUTODOC_PRIORITY = 900


def _type_prose(types):
    '''Convert a set of types to text.

    Parameters
    ----------
    types : set of type
        Types to convert.

    Returns
    -------
    str
        Type names in a fixed order, joined by ``" or "``.

    Examples
    --------
    >>> _type_prose({float, int})
    'int or float'
    '''

    ordered = [t for t in _TYPE_NAMES if t in types] + [t for t in types if t not in _TYPE_NAMES]

    return ' or '.join(_TYPE_NAMES.get(t, getattr(t, '__name__', str(t))) for t in ordered)


def _format_cell(key, value):
    '''Convert one specification value into the text of a table cell.

    Parameters
    ----------
    key : str
        Column of the cell, e.g. ``'Value'``, ``'Unit'`` or ``'optional'``.
    value : object
        Specification value. A dict is shown as one line per entry; in the
        ``Value`` column several lines become a nested table with dividers.

    Returns
    -------
    str
        RST text of the cell.

    Examples
    --------
    >>> _format_cell('Unit', {'type': {int, float}, 'bounds': (0, None)})
    '| type: int or float\\n| bounds: (0, None)'
    '''

    if not isinstance(value, dict):
        return _type_prose(value) if key == TYPE_KEY else str(value)

    parts = []

    for subkey, subvalue in value.items():
        if subkey == TYPE_KEY:
            subvalue = _type_prose(subvalue)
        elif subkey == OPTIONS_KEY:
            subvalue = ', '.join(repr(option) for option in sorted(subvalue))
        parts.append(f'{subkey}: {subvalue}')

    if key == 'Value' and len(parts) > 1:
        return '\n'.join(['.. list-table::', '   :widths: 100', '   :class: value-divider', '']
                         + [f'   * - {part}' for part in parts])

    return '\n'.join(f'| {part}' for part in parts)


def _render_table(title, rows):
    '''Render one table as an RST ``list-table``.

    Parameters
    ----------
    title : str
        Table name (top-level key).
    rows : list of tuple
        ``(name, row_dict)`` per row (middle-level key and its specification).

    Returns
    -------
    list of str
        RST lines of the table. The columns are the keys of the rows, in the
        order in which they first appear.
    '''

    columns = list(dict.fromkeys(key for _, row in rows for key in row))
    lines = [title, '-' * len(title), '', '.. list-table::', '   :header-rows: 1',
             '   :widths: ' + ' '.join(['25'] * (len(columns) + 1)), '', '   * - Name']
    lines += [f'     - {column}' for column in columns]

    for name, row in rows:
        lines.append(f'   * - ``{name}``')

        for column in columns:
            cell = _format_cell(column, row.get(column, '')).splitlines() or ['']
            lines.append(f'     - {cell[0]}' if cell[0] else '     -')
            lines += [f'       {line}' for line in cell[1:]]

    return lines + ['']


def _render_tables(spec_dict, name):
    '''Render all tables of an ``input_dict`` or ``output_dict``.

    Parameters
    ----------
    spec_dict : dict
        Plugin specification. ``sum_tables`` is skipped and tables inside
        ``special_insertions`` are shown like regular tables.
    name : str
        Name used in error messages.

    Returns
    -------
    list of str
        RST lines of all tables.
    '''

    tables = {}

    for top, middle, row in iter_spec_rows(spec_dict, name):
        tables.setdefault(top, []).append((middle, row))

    return [line for top, rows in tables.items() for line in _render_table(top, rows)]


def generate_docstring(summary, input_dict, output_dict, notes=None):
    '''Generate a NumPy-style plugin docstring from its specifications.

    Parameters
    ----------
    summary : str
        Short description of the plugin.
    input_dict : dict
        Input specification of the plugin.
    output_dict : dict
        Output specification of the plugin.
    notes : str, optional
        Extra text, rendered as a ``Notes`` section.

    Returns
    -------
    str
        Docstring with ``Parameters`` and ``Outputs`` tables.

    Raises
    ------
    ValueError
        If a specification does not follow the ``top > middle > bottom`` structure.

    Examples
    --------
    >>> generate_docstring('Summary.', {}, {}).splitlines()[0]
    'Summary.'
    '''

    lines = [textwrap.dedent(summary).strip(), '',
             'Parameters', '----------', '', *_render_tables(input_dict, 'input_dict'),
             'Outputs', '-------', '', *_render_tables(output_dict, 'output_dict')]

    if notes:
        lines += ['Notes', '-----', '', notes.strip(), '']

    return '\n'.join(lines).rstrip() + '\n'


# -- Sphinx extension ----------------------------------------------------------

def _autodoc_process_docstring(app, what, name, obj, options, lines):
    '''Replace a plugin class docstring by the one the plugin generates.

    Handler of Sphinx's ``autodoc-process-docstring`` event. Plugins that do
    not assign ``self.__doc__`` keep their regular docstring.
    '''

    if what == 'class' and name.startswith('pyH2A.Plugins.') and name.endswith('_Plugin'):
        generated = vars(instantiate_plugin_for_docs(obj)).get('__doc__')

        if generated:
            lines[:] = generated.splitlines()


def setup(app):
    '''Register the docstring generation as a Sphinx extension (see ``doc/conf.py``).'''

    app.setup_extension('sphinx.ext.autodoc')
    app.connect('autodoc-process-docstring', _autodoc_process_docstring, priority=AUTODOC_PRIORITY)

    return {'parallel_read_safe': True, 'parallel_write_safe': True}