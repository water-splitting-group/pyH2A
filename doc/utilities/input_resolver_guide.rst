Input Resolver Guide
====================

The ``pyH2A.Utilities.Input_Resolver.input_resolver`` pipeline provides an orchestrated subsystem exclusively designed around securely validating nested configurations within pyH2A inputs. It ensures that the model information entered by the user matches the physical types, bounds, and dimensions expected by the internal simulation modules.

Overview
--------

Data in ``pyH2A`` inputs is structured hierarchically. The input resolver walks over these nested dictionaries, checks them against predefined constraints, and dynamically converts string inputs and unit definitions into mathematical ``Quantity`` objects internally. 

To understand the input resolver, it is essential to understand the hierarchical terminology used in pyH2A input structures:
1. **top_key**: The name of the table in the input file (e.g., ``# Capital Cost``).
2. **middle_key**: The row name or parameter name within a table (e.g., the entry under the ``Name`` column).
3. **bottom_key**: The specific column related to that parameter (e.g., ``Value``, ``Unit``, or ``Type``).

Basic Strategy
--------------

When pyH2A processes a module's inputs, it provides the resolver with a predefined specification dictionary matching the expected input layout. The resolver typically looks for paired keys such as:
- ``Value`` / ``Unit``
- ``_Value`` / ``_Unit`` (e.g., ``Usage_Value`` and ``Usage_Unit``)

A matched valid pair triggers physical dimensionality resolving:
1. **Retrieval**: The ``bottom_key`` specifications are fetched.
2. **Dimensionality Checks**: The provided physical unit is matched against the target specification (e.g., ensuring an energy parameter strictly receives an ``energy`` dimension).
3. **Bounds Detection**: Boundary rules (min/max validations) assert that the inputs comply strictly with physical boundaries defined locally.
4. **Quantity Creation**: A ``Quantity`` class instance is structured, carrying the base scale mapping and value.

In contrast, basic standard variables without unit definitions (e.g., a simple ``Type`` string or ``Year`` integer) are evaluated directly based on their structural requirements using predefined type checking and list-option limits.

Examples
--------

Consider an input configuration specifying utility usage, mapped via the following dictionary structure representing expected inputs from a plugin:

.. code-block:: python

    from pyH2A.Utilities.Input_resolver.input_resolver import input_resolver_function

    # Define specifications using top_key, middle_key, bottom_key logic
    specification = {
        'Utilities': {                          # top_key
            'Electricity': {                    # middle_key
                'Usage_Value': {'type': 'float', 'bounds': [0, None]}, # bottom_key 1
                'Usage_Unit': {'dimension': 'energy / mass'},          # bottom_key 2
                'Type': {'type': 'str', 'options': ['natural_gas', 'electricity']} # bottom_key 3
            }
        }
    }
    
    # Run the resolver
    # actual = input_resolver_function(specification, dcf_class_instance, 'TestPlugin')

If the pyH2A input file does not match the constraints (e.g., entering an area unit when energy is required, or a negative usage value where bound requires ``>=0``), the resolver intercepts and explicitly tells the user where the error occurred by referencing the exact ``top_key > middle_key > bottom_key`` chain.

Wildcard and Group Formatting
-----------------------------

Often, the table structure in the input file is flexible. For example, a user can provide multiple unknown utility inputs or create table groups ending in a shared modifier (like ``[...] Direct Capital Cost [...]``). 

The resolver seamlessly models this by employing the wildcard ``"<...>"`` at either the ``top_key`` or ``middle_key`` level:

.. code-block:: python

    specification = {
        'Utilities': {                          # top_key
            '<...>': {                          # middle_key (Any number of rows)
                'Usage_Value': {'type': 'float', 'bounds': [0, None]},
                'Usage_Unit': {'dimension': 'energy / mass'}
            }
        },
        '<...> Direct Capital Cost': {          # top_key (Table group placeholder)
            '<...>': {                          # middle_key (Any parameter name)
                'Value': {'type': 'float'}
            }
        }
    }

Using the ``"<...>"`` tag instructs the resolver to dynamically search the actual input dictionary and apply the validation protocol iteratively to all matching instances.

Dependencies and Best Practices
-------------------------------

1. **Explicit Constraint Mapping**: Always set proper ``bounds`` and ``dimension`` specifications within your referencing dictionaries to ensure models avoid unphysical state inputs (e.g., negative efficiencies).
2. **Wildcards**: For dynamically expanding tables, insert ``<...>`` carefully to allow iterative parsing over flexible model structures.
3. **Traceable Errors**: Keep naming schemas unified and descriptive (``Value``, ``Unit``, ``Path``). Proper prefix/suffix pairings ensure pyH2A tracks dimensionality automatically and alerts the user natively when a definition overlaps or breaks.