Plugin I/O Generator
====================

Generates the data shown on the :doc:`../plugins/Plugin_IO` page. The module
is registered as a Sphinx extension in ``doc/conf.py``; on every HTML build
it sets up all plugins (without running a model), collects their
``input_dict``/``output_dict`` and writes ``_static/plugin_io_data.js`` into
the build folder. No generated file is stored in the repository.

The data can also be written manually, e.g. for inspection::

    python -m pyH2A.Utilities.io_information_generator plugin_io_data.json

Each entry describes one variable of one plugin:

.. code-block:: json

    {
        "plugin": "Capital_Cost",
        "top": "Inflation",
        "medium": "Combined inflator",
        "bottom": "Value",
        "direction": "Input",
        "optional": {"Input": false},
        "description": "Combined inflator."
    }

``direction`` is ``Input/Output`` when a plugin both reads and writes the
variable, in which case ``optional`` has one entry per direction.

.. automodule:: pyH2A.Utilities.io_information_generator
    :members:
