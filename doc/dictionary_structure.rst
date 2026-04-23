.. _dictionary-structure:


Dictionary Structure and Data Flow
==================================

.. contents:: Table of Contents
   :depth: 2
   :local:
   :class: this-will-duplicate-information-and-it-is-still-useful-here
   


1. The Shared Calculation Dictionary
------------------------------------

All plugins operate on a shared Python dictionary that contains the variables used throughout the techno-economic calculation.  
Within plugins, this dictionary is accessible as ``dcf.inp``.

As the calculation progresses, this dictionary is continuously updated.  
Plugins read values from it, perform calculations, and then insert new values or update existing ones.

Because this dictionary is passed through the successive plugins, it represents the evolving state of the economic model.


2. Structure of the Dictionary
------------------------------

The dictionary used in pyH2A has three levels of keys:

.. code-block:: python

   dcf.inp['top']['mid']['bottom']

These three levels correspond conceptually to:

- a **table name** (top key)
- a **row name** (mid key)
- a **column name** (bottom key)

For example, the input file ``Thermal_base.md`` contains the table:

::

   # Technical Operating Parameters and Specifications

   Name | Value | Unit
   --- | --- | ---
   Operating Capacity Factor | 90.0% | -
   Plant Design Capacity | 1,000 | kg/day

After conversion into Python objects and processing the table, the value ``1000``  and the associated unit ``kg/day`` are stored as this dictionary keys' item:

.. code-block:: python

   dcf.inp['Technical Operating Parameters and Specifications']['Plant Design Capacity']['Value']
   dcf.inp['Technical Operating Parameters and Specifications']['Plant Design Capacity']['Unit']

Conceptually, the dictionary structure can be visualized as follows:

.. code-block:: text

   dcf.inp
   │
   ├── "Technical Operating Parameters and Specifications"   ← table (top key)
   │       │
   │       ├── "Plant Design Capacity"        ← row (mid key)
   │       │        │
   │       │        └── "Value" → 1000        ← column (bottom key)
   │       │        └── "Unit" → 'kg/day'       ← column (bottom key)   
   │       │
   │       └── "Operating Capacity Factor"
   │                │
   │                └── "Value" → 0.9
   │                └── "Unit" → '-'   
   │
   └── "Non-Depreciable Capital Costs"
   │       │
   │       └── "Land required"
   │                │
   │                └── "Value" → Quantity object, calculated by plugin
   │				
					
					
3. Dictionary Entries and the Concept of Tables
-----------------------------------------------

In pyH2A, many variables originate from tables written in the input ``.md`` files.  
During initialization, these tables are converted into the internal dictionary structure. At this stage, the tables are only converted into Python objects; their entries are processed later when plugins request them (see Section 4).

After this conversion, each entry of an input table corresponds to a position in the ``dcf.inp`` dictionary. In practice, the top-level key of the dictionary corresponds to the table name.

However, the term *table* in pyH2A should be understood more generally than just the tables appearing in the input files.

As the calculation progresses, plugins may create new entries or update existing ones using the same ``dcf.inp`` dictionary structure. These entries follow the same organization as those originating from the input tables.

Consequently, a value stored in the dictionary may originate from two sources:

1. **Tables defined in the input (.md) file**
2. **Calculations or assignments performed by plugins**

In this sense, a *table* refers to any group of entries stored under a given top-level key of the ``dcf.inp`` dictionary, regardless of whether it was originally defined in the input file or created later by a plugin.


4. Conversion of Markdown Tables
--------------------------------

Tables written in the input ``.md`` files are converted into the Python dictionary structure by the function ``convert_input_to_dictionary``.

This function is called in both the ``pyH2A`` class and the ``Discounted_Cash_Flow`` class before the plugin workflow is executed.

It is important to note that this step **does not evaluate the entries** in the tables.  
It only converts their structure into Python objects so that they can later be processed by plugins when needed.


5. Processing inputs: ``input_resolver_function`` 
-------------------------------------------------

This paragraph gives an overview of how inputs are processed in each plugin. More detailed explanations :ref:`are provided separately <input_resolver_guide>`.

When a plugin requires input data, it retrieves it from the dictionary using ``input_resolver_function``.

Each plugin file includes an ``input_dict`` dictionary containing the entry keys that are needed by the plugin (top, middle and bottom keys), as well as the characteristics of each entry (dimension, type etc).

For example, in ``Hourly_Irradiation_Plugin``, the ``input_dict`` contains, among other items:

.. code-block:: python
	"Irradiance Area Parameters": {	
      <...>,   
		"Nominal operating temperature": {
			"Value": {
				"type": {float,},
				"bounds": (250, 500),
			},
			"Unit": {
				"dimension": "temperature",
			},
			"optional": False,
			"description": "Nominal operating temperature of irradiated module."
		},   
      <...>,    
   }

which means that ``Hourly_Irradiation__Plugin`` uses, among others, the value of ``dcf.inp['Irradiance Area Parameters']['Nominal operating temperature']['Value']`` as an input.


The ``__init__`` method of the plugin typically begins by a call to ``input_resolver_function``, for example . 

.. code-block:: python

   self.input_dict_resolved = input_resolver_function(input_dict, dcf, 'Hourly_Irradiation_Plugin')

This call retrieves the items corresponding to the dictionary positions found in input_dict, and apply a succession of conversion and sanity checks (dimensionality vs. unit consistency ; conversion into a specific unit ; bounds check).   

In our example: 
 1. ``dcf.inp['Irradiance Area Parameters']['Nominal operating temperature']['Value']`` is retrieved. 
 2. A Quantity object is created from the Value and the related Unit (``dcf.inp['Irradiance Area Parameters']['Nominal operating temperature']['Unit']``). This step is bypassed if the Value is already a Quantity object.
 3. The input resolver checks if the unit of measurement is consistent with the expected dimension as per the input_dict (in the present case: temperature). If this is not the case, an error message is thrown.
 4. The input resolver checks if the value expressed in the Base unit (generally: SI unit) respects the ``bounds`` specified in input_dict. An operating temperature below 250 K or above 500 K would be unrealistic, and would therefore lead to an error message.
 5. The Quantity object is added to the local ``self.input_dict_resolved`` dictionary. The quantities present in this dictionary are the ones used within the plugin for all the calculations.
 

One important feature of pyH2A is that table entries in the input file do not necessarily contain numerical values.  
They can instead refer to other variables or paths.

For example, in ``PV_E_Base.md`` : 

::

	# Irradiance Area Parameters

	Name | Value | Unit | Comment
	--- | --- | ---
	Module Tilt | Hourly Irradiation > Latitude > Value | deg | Module tilt equal to latitude of location.

Here the entry points to another variable in the dictionary.

When Hourly_Irradiation_Plugin executes ``input_resolver_function``, the ``dcf.inp['Irradiance Area Parameters']['Module Tilt']['Value']`` entry ultimately receives the value stored at: 

.. code-block:: python

   dcf.inp[Hourly Irradiation']['Latitude']['Value']
   
In the present example, it means that the value of the module tilt is simply made equal to the latitude.




6. Value Processing and Path-Based Multiplication
-------------------------------------------------

In many cases, the numerical value appearing in a table is not the final value used in the calculation.  
pyH2A allows entries to be expressed as a **base value multiplied by another variable** stored elsewhere in the dictionary.

This is done using the optional ``Path`` column in input tables.

For example, in ``PEC_Base.md``:

::

   # Direct Capital Costs - Water Management

   Name | Value | Path | Unit | Comment
   --- | --- | --- | ---
   Water pump | 213.0 | None | USD | Based on Pinaud 2013.
   Water Manifold Piping | 11.58 | USD | PEC Cells > Number > Value |

The entry indicates that the cost of water manifold piping is **11.58 $ per cell**.  
The total cost therefore depends on the number of PEC cells defined elsewhere in the model.

When the table is processed, pyH2A retrieves the referenced value:

::

   dcf.inp['PEC Cells']['Number']['Value']

and multiplies it by the base value specified in the table:

::

   total_cost = 11.58 * dcf.inp['PEC Cells']['Number']['Value']

This multiplication is performed automatically when the table entry is processed.

  .. admonition:: Code implementation

     The multiplication is handled by the ``process_input()`` method, which is called internally by ``input_resolver_function``. If a ``Path`` column exists, the value retrieved from that path is multiplied with the entry in the ``Value`` column, and the resulting number replaces the original value in the dictionary.


7. Flexible Rows and Table Groups
---------------------------------

Some plugins interpret tables in a way that allows the user to define multiple entries without fixing their exact row structure. Two mechanisms are used for this: **flexible rows** and **table groups**.


Flexible rows
~~~~~~~~~~~~~

In some tables, the specific row names do not affect the calculation.  
The rows are simply used to list multiple contributions that will later be combined.

For example, in the ``Variable_Operating_Cost_Plugin`` the method ``other_variable_costs`` computes the sum of all entries in the table ``Other Variable Operating Cost``:

.. code-block:: python

   self.other = dcf.chemical_inflator * sum_all_tables(dcf.inp,'Other Variable Operating Cost','Value',
       insert_total = True, class_object = dcf, print_info = print_info, unit = 'USD'
   )

In this case, the individual row names inside the table do not influence the calculation.  
The user may therefore define any number of rows describing different cost components. Their values are simply summed when the plugin processes the table.


Table groups
~~~~~~~~~~~~

In some situations, several tables that share a common theme are grouped together based on their names.

A plugin may search for all tables whose top-level key contains a given string and treat them as belonging to the same group.

For example, in ``Fixed_Operating_Cost_Plugin`` the method ``other_cost`` performs the calculation:

.. code-block:: python

   self.other = sum_all_tables(dcf.inp, 'Other Fixed Operating Cost', 'Value',
       insert_total = True, class_object = dcf, print_info = print_info, unit = 'USD'
   ) * dcf.combined_inflator

Here, every table whose name contains the string ``Other Fixed Operating Cost`` is included in the calculation.

This allows users to define several tables such as:

- ``Plant A Other Fixed Operating Cost``
- ``Water Treatment Other Fixed Operating Cost``
- ``Utilities Other Fixed Operating Cost``

Each table can contain its own entries, but all their values are combined when the plugin computes the total cost.


Purpose of These Mechanisms
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Flexible rows and table groups enable to structure input files in a clear and modular way.

Users can separate different cost contributions into individual rows or tables for readability, while the plugin logic automatically aggregates them during the calculation.

8. Inserting or Updating Values: ``output_inserter_function``
-------------------------------------------------------------

This paragraph gives an overview of how each plugin makes its calculated Quantites available in the dictionary. More detailed explanations :ref:`are provided separately <output_inserter_guide>`.

After performing calculations, plugins store their results in the dictionary using the ``output_inserter_function`` call.

This method can either:

- create a **new dictionary entry**, or
- **update the value** of an existing entry.

The variable to be inserted at a given dictionary location is defined in the output_dict structure that is found in each plugin

Example: in ``Solar_Concentrator_Plugin``

- The output_dict structure contains 
.. code-block:: python
   "Non-Depreciable Capital Costs": {
      "Land required": {
         "Value": {
               "inserted_value": "total_land_area",
               "type": {float,},
               "dimension": "area",
         },
         "optional": False,
      },
      "Solar Collection Area": {
         "Value": {
               "inserted_value": "total_solar_collection_area",
               "type": {float,},
               "dimension": "area",
         },
         "optional": False,
      },      

- creating a new entry:

The variable ``self.total_land_area`` is calculated in the plugin, and the call to ``output_inserter_function(output_dict, self, dcf, 'Solar_Concentrator_Plugin')`` creates the following dictionary entry to make it equal to ``self.total_land_area``:

.. code-block:: python

   dcf.inp['Non-Depreciable Capital Costs']['Land required']['Value']


- updating an existing entry.

The plugin reads the existing values of the ``Non-Depreciable Capital Costs`` table, including the existing value of the ``Solar Collection Area`` row, as specified in the ``input_dict``:

.. code-block:: python

	"Non-Depreciable Capital Costs": {
		"Solar collection area": {
			"Value": {
				"type": {float,},
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": "area",
			},
			"optional": False,
			"description": "Total solar collection area."
		},


A new value ``self.total_solar_collection_area`` is calculated, and its value is assigned to ``dcf.inp['Non-Depreciable Capital Costs']['Solar Collection Area']['Value']``, as seen in the ``output_dict`` above.

In other words, this operation updates:

.. code-block:: python

   dcf.inp['Non-Depreciable Capital Costs']['Solar Collection Area']['Value']


9. Dependency Between Plugins
-----------------------------

When a plugin requests a value from the dictionary using ``input_resolver_function``, the corresponding entry must already exist.

This entry must therefore have been:

- defined in the input ``.md`` file, or
- inserted earlier by another plugin.

For this reason, the **execution order of plugins determines the dependency structure of the model**.  
A plugin can only rely on variables that have already been defined earlier in the workflow.

The data flow can be represented schematically as:

.. code-block:: text

        Input tables (.md)
                │
                ▼
        convert_input_to_dictionary
                │
                ▼
            dcf.inp
      (shared calculation dictionary)
                │
                ▼
        ┌────────────────────────────┐
        │         Plugin 1           │
        │ - input_resolver_function  │
        │ - calculations             │
        │ - output_resolver          │
        └────────────────────────────┘
                │
                ▼
            dcf.inp
       (with newly inserted variables)
                │
                ▼
        ┌────────────────────────────┐
        │         Plugin 2           │
        │ - input_resolver_function  │
        │ - calculations             │
        │ - output_resolver          │
        └────────────────────────────┘
                │
                ▼
            dcf.inp
                │
                ▼
               ...
                │
                ▼
        Final financial evaluation