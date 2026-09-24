'''Shared helpers for reading plugin ``input_dict``/``output_dict`` specifications.

Plugins describe their interface with nested dictionaries that are strictly
three levels deep (``top key > middle key > bottom key``). Several tools read
these dictionaries without running a model, for example the automatic
docstring generation (:mod:`pyH2A.Utilities.docstring_generation`) and the
Plugin I/O overview (:mod:`pyH2A.Utilities.io_information_generator`).

This module is the single place that knows how to traverse the
specifications, so all of these tools skip the same special keys and pair
``Value``/``Unit`` keys the same way as :mod:`pyH2A.Utilities.IO`:

* special middle keys (``sum_tables``) are skipped,
* special top-level output keys (``special_insertions``) are unwrapped so
  that the tables inside them look like regular tables,
* bottom keys are paired with
  :func:`pyH2A.Utilities.input_modification.identify_bottom_keys`.
'''

from pyH2A.Utilities.constants import (SPECIAL_MIDDLE_KEYS, OPTIONAL_KEY,
                                       VALUE_KEY, UNIT_KEY, PATH_KEY_INPUT,
                                       VALUE_SUFFIX, UNIT_SUFFIX, PATH_SUFFIX,
                                       DESCRIPTION_KEY, SPECIAL_TOP_LEVEL_KEYS,
                                       SPECIAL_KEYS_OUTPUT_INSERTER)
from pyH2A.Utilities.functional_unit import FunctionalUnit
from pyH2A.Utilities.input_modification import identify_bottom_keys, import_plugin


# Placeholder used wherever a plugin inserts the functional unit into its
DOCUMENTATION_FUNCTIONAL_UNIT = FunctionalUnit(
    unit='functional unit',
    dimension='functional unit',
    unit_SI='functional unit',
    dimension_per_time='functional unit / time',
    unit_SI_per_s='functional unit / s',
    unit_per_year='functional unit / year',
    unit_no_reference='functional unit',
    reference='functional unit',
)


class DocumentationDCF:
    '''Minimal stand-in for ``Discounted_Cash_Flow`` used to set up plugins.

    Plugins build ``input_dict`` and ``output_dict`` in ``_set_up`` and only
    need ``dcf.functional_unit`` for that. This class provides exactly that,
    so a plugin can be instantiated with ``run=False`` without an input file.

    Attributes
    ----------
    functional_unit : FunctionalUnit
        Placeholder functional unit (``DOCUMENTATION_FUNCTIONAL_UNIT``).
    '''

    def __init__(self):
        self.functional_unit = DOCUMENTATION_FUNCTIONAL_UNIT


def instantiate_plugin_for_docs(plugin):
    '''Instantiate a plugin without running it.

    Parameters
    ----------
    plugin : str or type
        Plugin class, or name of a module in ``pyH2A.Plugins`` that contains
        a class of the same name (e.g. ``'Capital_Cost_Plugin'``).

    Returns
    -------
    object
        Plugin instance whose ``input_dict`` and ``output_dict`` are set up.

    Examples
    --------
    >>> plugin = instantiate_plugin_for_docs('Time_Plugin')
    >>> 'Time' in plugin.output_dict
    True
    '''

    if isinstance(plugin, str):
        plugin = import_plugin(plugin, plugin_module=True)

    return plugin(DocumentationDCF(), print_info=False, run=False)


def _check_is_dict(value, location):
    '''Raise a ``ValueError`` if ``value`` is not a dictionary.

    Parameters
    ----------
    value : object
        Object that should be a dictionary.
    location : str
        Human readable location of ``value``, used in the error message.

    Raises
    ------
    ValueError
        If ``value`` is not a dictionary.
    '''

    if not isinstance(value, dict):
        raise ValueError(f'Expected a dictionary at {location}, '
                         f'got {type(value).__name__}.')


def iter_spec_rows(spec_dict, name='specification'):
    '''Iterate over all rows (middle keys) of a plugin specification.

    Parameters
    ----------
    spec_dict : dict
        ``input_dict`` or ``output_dict`` of a plugin.
    name : str, optional
        Name used in error messages, e.g. ``'Capital_Cost_Plugin.input_dict'``.

    Yields
    ------
    top_key : str
        Table name. For entries inside a special top-level key
        (``special_insertions > sum_all_tables > table``) this is the name of
        the inner table, so they appear like regular tables.
    middle_key : str
        Row name.
    row_dict : dict
        Row specification containing the bottom keys (``Value``, ``Unit``,
        ``optional``, ``description``, ...).

    Raises
    ------
    ValueError
        If a table or row is not a dictionary, i.e. the specification does
        not follow the ``top > middle > bottom`` structure.

    Notes
    -----
    Rows listed in ``SPECIAL_MIDDLE_KEYS`` (``sum_tables``) are skipped since
    they configure the input resolver and do not describe a variable.
    '''

    _check_is_dict(spec_dict, name)

    for top_key, table_dict in spec_dict.items():
        location = f'{name} > {top_key}'
        _check_is_dict(table_dict, location)

        if top_key in SPECIAL_TOP_LEVEL_KEYS:
            # e.g. special_insertions > sum_all_tables > <table> > <row>
            for wrapper_key, wrapped_tables in table_dict.items():
                yield from iter_spec_rows(wrapped_tables,
                                          f'{location} > {wrapper_key}')
            continue

        for middle_key, row_dict in table_dict.items():
            if middle_key in SPECIAL_MIDDLE_KEYS:
                continue

            _check_is_dict(row_dict, f'{location} > {middle_key}')

            yield top_key, middle_key, row_dict


def bottom_display_name(bottom_key):
    '''Return the name used to present a bottom key.

    Parameters
    ----------
    bottom_key : str
        Bottom key of a row, e.g. ``'Value'``, ``'Cost_Value'`` or ``'Type'``.

    Returns
    -------
    str
        ``bottom_key`` without the ``_Value`` suffix. The bare ``Value`` key
        is returned unchanged.
    '''

    if bottom_key != VALUE_KEY and bottom_key.endswith(VALUE_SUFFIX):
        return bottom_key[:-len(VALUE_SUFFIX)]

    return bottom_key


def _is_companion_key(bottom_key):
    '''Check if a bottom key only accompanies a value (unit or path key).

    Parameters
    ----------
    bottom_key : str
        Bottom key of a row.

    Returns
    -------
    bool
        ``True`` for ``Unit``, ``Path``, ``*_Unit`` and ``*_Path`` keys.
    '''

    return (bottom_key in (UNIT_KEY, PATH_KEY_INPUT)
            or bottom_key.endswith(UNIT_SUFFIX)
            or bottom_key.endswith(PATH_SUFFIX))


def iter_bottom_entries(row_dict, location='row'):
    '''Iterate over the variables described by one row.

    Parameters
    ----------
    row_dict : dict
        Row specification as yielded by :func:`iter_spec_rows`.
    location : str, optional
        Location of the row, used in error messages.

    Yields
    ------
    bottom_key : str
        Bottom key holding the value (e.g. ``'Value'`` or ``'Cost_Value'``).
    value_spec : dict
        Specification of the value (``type``, ``bounds``, ...).
    optional : bool
        Whether the value is optional. A bottom-level ``optional`` entry
        overrides the row-level one; the default is ``False``.

    Raises
    ------
    ValueError
        If the specification of a value is not a dictionary.

    Notes
    -----
    ``Unit``/``Path`` keys are paired with their value key by
    :func:`~pyH2A.Utilities.input_modification.identify_bottom_keys` and are
    not yielded separately. Row properties (``description``, ``optional``,
    ``add_processed``, ...) are skipped.
    '''

    row_optional = bool(row_dict.get(OPTIONAL_KEY, False))

    for bottom_key in identify_bottom_keys(row_dict):
        if bottom_key in SPECIAL_KEYS_OUTPUT_INSERTER or _is_companion_key(bottom_key):
            continue

        value_spec = row_dict[bottom_key]
        _check_is_dict(value_spec, f'{location} > {bottom_key}')

        optional = bool(value_spec.get(OPTIONAL_KEY, row_optional))

        yield bottom_key, value_spec, optional