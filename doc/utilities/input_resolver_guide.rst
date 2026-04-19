.. _input_resolver_guide:

=======================
Input Resolver Guide
=======================

The Input Resolver is a utility in pyH2A designed to provide a structured and verifiable way to extract input values from the user's input dictionary (usually ``dcf.inp``) into the plugins.

It utilizes an ``input_dict`` that acts as a blueprint, describing what information your plugin expects, where to find it, and ensuring that any retrieved values match the required type, bounds, and physical dimension.

Structure of the input_dict
===========================

The ``input_dict`` mimics the hierarchical structure of the pyH2A input file. The structure is 3 levels deep: 

1. **Top Level** (Table name / Group name): The name of the table in the input file, e.g., ``'Utilities'``.
2. **Middle Level** (Row name / Parameter name): The name of the row, e.g., ``'Electricity'``.
3. **Bottom Level** (Value entries & Specifications): Contains the parameters for extraction, like ``'Value'``, ``'Unit'``, as well as descriptive properties of the row.

Example
-------

.. code-block:: python

    input_dict = {
        'Utilities': {
            'Electricity': {
                'Usage_Value': {
                    'type': {float, int},
                    'bounds': (0, None),
                    'path': 'Usage_Path'
                },
                'Usage_Unit': {
                    'dimension': 'energy / mass'
                },
                'Type': {
                    'type': str,
                    'options': {'natural_gas', 'electricity'}
                },
                'optional': True,
                'description': 'The utility usage details.'
            }
        }
    }


Wildcards and Table Groups
--------------------------

Often, the exact name of a table or a row is flexible or unknown in advance. The indicator ``'<...>'`` (``WILDCARD_MARKER``) can be used to handle these situations:

* **Table Groups (Top Level)**: If a top key contains ``'<...>'`` (e.g., ``'<...> Other Variable Operating Cost <...>'``), it acts as a group. The resolver extracts all tables in the input that contain the string (in this case, all tables containing " Other Variable Operating Cost ").
* **Wildcard Rows (Middle Level)**: If a middle key is ``'<...>'``, the resolver iterates over *all* rows present in the referenced table in the user's input file and applies the bottom level specification to each of them.

Special Bottom Keys
-------------------

The input resolver looks for a few special keys at the bottom level that govern the entire row's behavior:

* ``optional`` (bool): Whether the parameter is optional. If ``False`` (or absent) and the row or table is not found in the user input, an error is raised.
* ``description`` (str): Used to provide a description for the documentation or clarification within the dictionary.

These keys are ignored during the actual value parsing.

Value and Unit Pairs
--------------------

The resolver automatically pairs values and units recursively within a row based on their keys:
* A direct ``'Value'`` and ``'Unit'`` pair.
* Keys ending with ``'_Value'`` and ``'_Unit'`` (e.g., ``'Usage_Value'`` paired with ``'Usage_Unit'``).

Any key not fitting these pair formats or the special bottom keys (like ``'Type'`` in the example) is treated as a standalone value.

Specifications 
--------------

For any value or unit key on the bottom level, you provide a dictionary with specifications used for verification:

* ``type`` (set or type): A set of permitted Python types for the value (e.g., ``{float, int, np.ndarray}``).
* ``bounds`` (tuple): A tuple of ``(min, max)`` values the base value must adhere to (e.g., ``(0, None)`` for strictly non-negative limits). Checked for the associated physical *base value*.
* ``options`` (set): For categorical strings, ensuring the input matches exactly one of the allowed options.
* ``dimension`` (str): Specified **only on the unit key**, verifying the physical dimension (e.g., ``'energy / mass'``, ``'currency'``, ``'dimensionless'``).
* ``path`` (str): Customizes the suffix of the key used to find a path for the value. Replaces the default ``'Path'`` (or ``'{Prefix}_Path'``).

Behavior of the Input Resolver
==============================

The resolver pipeline extracts values from the central input dictionary and transforms them based on dimensionality.

Supported Data Types
--------------------

* **Numbers and Arrays** (``float``, ``int``, ``np.ndarray``): When retrieved alongside a unit, they are automatically converted into a ``Quantity`` object representing the physical property.
* **Existing Quantities**: The system can extract predefined ``Quantity`` objects explicitly provided by plugins.
* **Strings**: For attributes requiring string selection (like ``'Type'``), they are parsed directly without unit associations.
* **Dictionaries**: Top-level dictionaries containing nested structures (often time-series or mapping sets) are recursively traversed, and terminal numerical values are individually converted into ``Quantity`` objects.

Using the resolver function
---------------------------

Usually, resolving input information is done using the top-level ``input_resolver_function``:

.. code-block:: python

    from pyH2A.Utilities.IO.input_resolver import input_resolver_function
    
    # ... inside your plugin execution ...
    resolved_inputs = input_resolver_function(
        input_dict=my_plugin_blueprint, 
        dcf_class=self.dcf, 
        plugin_name=self.name
    )

The function matches the blueprint ``my_plugin_blueprint`` against ``self.dcf.inp`` and returns a populated, structurally identical dictionary containing validated strings, dictionaries, and ``Quantity`` objects.

Edge Cases and Common Problems
==============================

Paths and Referencing
---------------------
The resolver natively supports pointing inputs toward other input components using the path definition natively implemented in pyH2A. 
* **Important Tip regarding Paths and Units**: 
  When a ``Path`` (or ``{Prefix}_Path``) references an **unprocessed** input (direct user input), the *Unit defined at the reference destination* must be the **exact same unit** as defined for the user input.
  However, if a path string references **processed** input (marked with ``'Processed': True`` in the background data), it implies the value target has already been converted into a base ``Quantity``. **Therefore, any path referencing processed parameters must explicitly use the overarching physical default BASE UNIT (e.g. `'kg'`, `'J'`, base SI variations) to avoid duplicate unit multiplication or dimension mismatch errors.** You can view ``process_input()`` in ``pyH2A.Utilities.input_modification`` for internal path behavior.

Missing Optional Modifiers
--------------------------
If a row or table is essential for your plugin computation (e.g., you explicitly expect ``resolved_inputs['Table']['Row']`` to be provided), ensure ``'optional': False`` is set in the bottom keys. Do not rely heavily on hardcoded error catches without using the system's boolean ``optional`` flag, otherwise ``KeyError`` will natively interrupt the extraction flow.
