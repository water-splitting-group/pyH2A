'''Generate the data for the Plugin I/O page of the documentation.

Used as a Sphinx extension, every plugin is set up without running a model and
its ``input_dict``/``output_dict`` is written as rows (one per plugin and
variable) to ``_static/plugin_io_data.js`` of the HTML build. Any error fails
the build.
'''

import json
from pathlib import Path

import pyH2A.Plugins as plugins
from pyH2A.Utilities.plugin_specification import (instantiate_plugin_for_docs, iter_spec_rows,
                                                  iter_bottom_entries, bottom_display_name)


def _iter_variables(spec_dict, name):
    '''Yield every variable of a specification.

    Parameters
    ----------
    spec_dict : dict
        ``input_dict`` or ``output_dict`` of a plugin.
    name : str
        Name used in error messages.

    Yields
    ------
    key : tuple of str
        ``(top, medium, bottom)`` of the variable.
    optional : bool
        Whether the variable is optional.
    description : str
        Description of the row.
    '''

    for top, middle, row in iter_spec_rows(spec_dict, name):
        for bottom, _, optional in iter_bottom_entries(row):
            yield (top, middle, bottom_display_name(bottom)), optional, row.get('description', '')


def _make_row(plugin_name, key, variable):
    '''Build one output row from a collected variable.

    Parameters
    ----------
    plugin_name : str
        Name of the plugin.
    key : tuple of str
        ``(top, medium, bottom)`` of the variable.
    variable : dict
        ``optional`` (per direction) and ``description`` of the variable.

    Returns
    -------
    dict
        Row with ``plugin``, ``top``, ``medium``, ``bottom``, ``direction``,
        ``optional`` and ``description``.
    '''

    top, medium, bottom = key
    direction = '/'.join(variable['optional'])  # 'Input', 'Output' or 'Input/Output'

    return {'plugin': plugin_name, 'top': top, 'medium': medium, 'bottom': bottom,
            'direction': direction, **variable}


def collect_plugin_rows(input_dict, output_dict, plugin_name):
    '''Collect the I/O rows of one plugin.

    Parameters
    ----------
    input_dict : dict
        Input specification of the plugin.
    output_dict : dict
        Output specification of the plugin.
    plugin_name : str
        Name stored in the ``plugin`` field of every row.

    Returns
    -------
    list of dict
        One row per variable, see :func:`_make_row`. A variable that is both
        read and written gets the direction ``'Input/Output'``.
    '''

    variables = {}

    for direction, spec_dict in (('Input', input_dict), ('Output', output_dict)):
        for key, optional, description in _iter_variables(spec_dict, f'{plugin_name} {direction}'):
            variable = variables.setdefault(key, {'optional': {}, 'description': description})
            variable['optional'][direction] = optional

    return [_make_row(plugin_name, key, variable) for key, variable in variables.items()]


def collect_rows():
    '''Collect the sorted I/O rows of all plugins in ``pyH2A.Plugins``.

    Returns
    -------
    list of dict
        Rows as returned by :func:`collect_plugin_rows`.
    '''

    rows = []

    for path in sorted(Path(plugins.__file__).parent.glob('*_Plugin.py')):
        plugin = instantiate_plugin_for_docs(path.stem)
        rows += collect_plugin_rows(plugin.input_dict, plugin.output_dict,
                                    path.stem.removesuffix('_Plugin'))

    return sorted(rows, key=lambda row: (row['top'], row['medium'], row['bottom'], row['plugin']))


def _add_files(app, pagename, templatename, context, doctree):
    '''Add the Plugin I/O files only to the page containing the browser.'''

    if 'id="io-browser"' in context.get('body', ''):
        app.add_css_file('plugin_io.css')
        app.add_js_file('plugin_io_data.js')
        app.add_js_file('plugin_io.js')


def _write_data(app, exception):
    '''Write the rows to ``_static/plugin_io_data.js`` after an HTML build.'''

    if exception is None and app.builder.format == 'html':
        data = json.dumps(collect_rows())
        (Path(app.outdir) / '_static' / 'plugin_io_data.js').write_text(
            f'window.PYH2A_PLUGIN_IO_DATA = {data};\n', encoding='utf-8')


def setup(app):
    '''Register the generator as a Sphinx extension (see ``doc/conf.py``).'''

    app.connect('html-page-context', _add_files)
    app.connect('build-finished', _write_data)

    return {'parallel_read_safe': True, 'parallel_write_safe': True}