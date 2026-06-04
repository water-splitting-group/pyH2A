Utilities Guide
===============

convert_input_to_dictionary
---------------------------

What is this method?
~~~~~~~~~~~~~~~~~~~~

``convert_input_to_dictionary`` is a utility function that reads a Markdown
input file and converts it into a nested Python dictionary used by pyH2A.
It can also merge:


Why do we need it?
~~~~~~~~~~~~~~~~~~

This function is the entry point for turning user-facing text input (md file) into a
machine-usable configuration object and merge additional input files.


How does it work?
~~~~~~~~~~~~~~~~~

At a high level, the method performs these steps:

1. Read the main (highest priority) Markdown input file and parse it into a dictionary.
2. If ``merge_default=True``, read the default input file and merge it first.
3. Let values in the main input file override default values.
4. Look for a table named ``Base input file`` in the merged dictionary.
5. For each row in that table, read the file path stored in the ``Value`` column and merge that (md) file into the current dictionary.
6. Earlier files listed in ``Base input file`` have higher priority than later files.


Method signature
~~~~~~~~~~~~~~~~

.. code-block:: python

	convert_input_to_dictionary(
		 file,
		 default='pyH2A.Config~Defaults.md',
		 merge_default=True,
	)


Parameters
~~~~~~~~~~

``file``
	Path to the main input file.

``default``
	Path to the default input file. This can be a package-style path such as ``pyH2A.Config~Defaults.md``.

``merge_default``
	If ``True``, merge defaults first, then override with main input values.


Return value
~~~~~~~~~~~~

Returns a nested ``dict`` containing all merged input data.


How to use it
~~~~~~~~~~~~~

Basic usage:

.. code-block:: python

	from pyH2A.Utilities.input_modification import convert_input_to_dictionary

	inp = convert_input_to_dictionary('data/PV_E/Base/file_name.md')


Without merging default values:

.. code-block:: python

	from pyH2A.Utilities.input_modification import convert_input_to_dictionary

	inp = convert_input_to_dictionary(
		 'data/PV_E/Base/file_name.md',
		 merge_default=False,
	)


With a custom defaults file:

.. code-block:: python

	from pyH2A.Utilities.input_modification import convert_input_to_dictionary

	inp = convert_input_to_dictionary(
		 file='data/PV_E/Base/file_name.md',
		 default='data/custom_defaults.md',
		 merge_default=True,
	)


Input file specification
~~~~~~~~~~~~~~~~~~~~~~~~

The parser expects Markdown-style tables in this pattern:

.. code-block:: text

	# Table Name

	Name | Value | Unit
	--- | --- | ---
	Temperature | 300 | K
	Pressure | 5 | bar

Key format rules:

1. Section titles are Markdown headings (``# Table Name``).
2. Each section is a table.
3. The first column becomes the middle key in the nested dictionary.
4. Remaining columns become leaf keys (for example, ``Value``, ``Unit``).


Base input file table format
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To merge additional files, include this table in your main input file:

.. code-block:: text

	# Base input file

	Name | Value
	--- | ---
	Layer 1 | ./override_level_1.md
	Layer 2 | ./override_level_2.md

Merge priority (high to low) for this example:
1. Main input file
2. ``Layer 1`` file.
3. ``Layer 2`` file.
4. Default file


Practical example
~~~~~~~~~~~~~~~~~

.. code-block:: python

	from pyH2A.Utilities.input_modification import convert_input_to_dictionary

	inp = convert_input_to_dictionary('base_input.md', merge_default=False)

	# Access parsed and merged values
	temperature = inp['Process']['Temperature']['Value']
	pressure = inp['Process']['Pressure']['Value']

	print('Temperature:', temperature)
	print('Pressure:', pressure)


When to use this method
~~~~~~~~~~~~~~~~~~~~~~~

Use ``convert_input_to_dictionary`` when:

1. You want to convert pyH2A Markdown inputs into Python Dictionaries.
2. You need default + case-specific overrides.
3. You want to manage multiple layers of input files with clear priority rules.