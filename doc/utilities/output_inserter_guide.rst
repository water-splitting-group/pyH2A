.. _output_inserter_guide:

=======================
Output Inserter Guide
=======================

The Output Inserter is a utility in pyH2A designed to provide a structured and verifiable way to insert output values calculated by plugins back into the `Discounted_Cash_Flow` input dictionary (`dcf.inp`).

It utilizes an `output_dict` that acts as a blueprint, describing what information should be inserted, where it should go, and ensuring that any inserted values match the required type and physical dimension.

Structure of the output_dict
============================

The `output_dict` mimics the hierarchical structure of the `dcf.inp` file. The structure is 3 levels deep: 

1. **Top Level** (Table name / Group name): E.g., ``'Power Generation'``.
2. **Middle Level** (Row name / Parameter name): E.g., ``'Stored Energy (daily)'``.
3. **Bottom Level** (Value entries & Properties): Contains the parameters for insertion, like ``'Value'``, as well as descriptive properties of the row.

Example
-------

.. code-block:: python

    output_dict = {
        'Power Generation': {
            'Stored Energy (daily)': {
                'Value': {
                    'inserted_value': 'daily_stored_power', 
                    'type': {dict},
                    'dimension': 'energy'
                },
                'optional': False,
                'add_processed': True,
                'insert_path': True,
                'path_key': 'Path',
                'description': 'Electricity stored in battery daily'
            }
        }
    }


Special Keys 
-------------

On the bottom level, alongside the actual values to be inserted, you can provide "special keys" that dictate the behavior of the row upon insertion:

* ``optional`` (bool): Whether the insertion of this row is optional. If ``True`` and the mapped attribute is missing, it will not raise an error. Defaults to ``False``.
* ``add_processed`` (bool): If ``True``, successfully inserted rows will have a ``'Processed': 'Yes'`` flag added alongside the value. Defaults to ``True``.
* ``insert_path`` (bool): If ``True``, adds a path key containing information about the origin of the inserted value. Defaults to ``True``.
* ``path_key`` (str): Customizes the key used for the path insertion. Defaults to ``'Path'``.
* ``description`` (str): Used to provide a description for the documentation or clarification within the dictionary.

Value Level Properties 
-----------------------

For any parameter key (e.g., ``'Value'``, ``'Cost_Value'``), you specify a dictionary with the following properties:

* ``inserted_value``: Essential parameter. Tells the inserter what to insert. This can be:
  * A string matching an attribute name in your plugin class (e.g. ``'daily_stored_power'``).
  * A direct ``Quantity`` object (e.g., ``Quantity(0, 'kWh')``).
  * (Other python types are supported via direct object references as long as they meet the type requirement).
* ``type``: A set of expected Python types (e.g., ``{int, float, np.ndarray}``). Used for type-checking.
* ``dimension``: A physical dimension string (e.g., ``'energy'``, ``'currency'``) to ensure the inserted ``Quantity`` matches the expected unit dimensionality.


Special Insertions
------------------

The top-level key ``special_insertions`` is ignored during the standard iteration over the output dictionary. This section can be used to hold instructions for special custom insertions that require dedicated handling outside the basic behavior (for instance, ``sum_all_tables`` across numerous groups), which are accessed manually when needed.

.. code-block:: python

    'special_insertions': {
        'sum_all_tables': {
            '<...> Direct Capital Cost <...>': {
                'Summed Total': {
                    'Value': {
                        'type': {int, float},
                    },
                    'optional': True,
                    'description': 'Summed total of direct capital costs'
                }
            }
        }
    }

Behavior of the Output Inserter
===============================

The output inserter attempts to match the keys found in the `output_dict` to the properties (attributes) on the `Plugin` class.

What CAN be inserted
--------------------

* **Plugin Attributes**: By providing a string as `inserted_value`, the inserter fetches `getattr(plugin_class, inserted_value)` (e.g., ``'daily_stored_power'`` fetches ``self.daily_stored_power``).
* **Direct Quantities**: Hardcoded ``Quantity`` objects in the dictionary directly (e.g., ``Quantity(42, 'kg')``).
* **Dictionaries**: The inserter recursively checks types inside dictionary structures if the value to be inserted is a `dict`.
* **Strings**: String parameters if the type requires it.

What CANNOT be inserted
-----------------------

* Direct numeric primitives (e.g., integer or float values like `1.5`) using ``inserted_value: 1.5``. A value must be either a string representing the class attribute name, or wrapped in a ``Quantity`` object.

Edge Cases and Common Problems
==============================

* **Missing Attributes (AttributeError)**: If ``optional=False`` and you provide a string as `inserted_value` (like ``'my_calculated_array'``) but forget to define `self.my_calculated_array` in your plugin, the insertion will fail with an AttributeError. If it's expected that a calculation might not produce this value, set ``'optional': True``.
* **Dimension Mismatch**: If you calculate a power value (``'kW'``) but the output_dict expects ``'dimension': 'energy'`` (like kWh), the inserter's `check_dimension` will throw a unit dimensionality error. Always match dimensions.
* **Invalid Type Declaration**: For values that produce nested dictionaries, you should list ``dict`` within the ``type`` set to ensure recursive validation happens properly.
* **Top-Level Dicts vs Type Checking**: Remember type checks for Python dictionaries only confirm the top-level container is a dict; it iteratively traverses the values to check their types recursively.

Other Information
=================

By default, the inserter uses `pyH2A.Utilities.input_modification.insert`, suppressing direct output chatter (``print_info=False``). Successfully inserted paths and processed tags help users trace changes to PyH2A's central data structure, making the complete execution transparent.