Plugin Specification
====================

Helpers shared by the tools that read plugin ``input_dict``/``output_dict``
specifications without running a model, such as the automatic docstring
generation (:mod:`pyH2A.Utilities.docstring_generation`) and the Plugin I/O
overview (:mod:`pyH2A.Utilities.io_information_generator`). Keeping the
traversal in one place ensures that all of them skip the same special keys
and pair ``Value``/``Unit`` keys the same way as the input resolver and the
output inserter.

.. automodule:: pyH2A.Utilities.plugin_specification
    :members:
