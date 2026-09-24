docstring_generation
====================

Generates the ``Parameters`` and ``Outputs`` tables of the plugin pages from
each plugin's ``input_dict``/``output_dict``. The module is registered as a
Sphinx extension in ``doc/conf.py``: when autodoc documents a plugin class,
the plugin is set up without running a model and its generated docstring
replaces the class docstring. Plugins that do not generate a docstring keep
their hand-written one.

The specifications are read with :doc:`plugin_specification`, which is
shared with other documentation tools.

.. automodule:: pyH2A.Utilities.docstring_generation
    :members:
