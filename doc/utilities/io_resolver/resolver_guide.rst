====================
Input Resolver Guide
====================

.. contents:: Table of Contents
    :depth: 2
    :local:
    :class: this-will-duplicate-information-and-it-is-still-useful-here

What is it?
===========

The ``InputResolver`` (found in
``src/pyH2A/Utilities/IO_Resolver/resolver.py``) is a utility class that
plugins use to read, validate, and convert their inputs from the central
``dcf.inp`` dictionary — the parsed representation of the user's Markdown
input file.

In short, it is the bridge between the raw text a user writes in an input
file and the clean, type-checked, unit-aware Python values a plugin needs
to do its calculations.

Why do we need it?
==================

pyH2A input files are Markdown tables. After parsing, every value in
every table is a raw Python string, integer, or float — there are no
units, no type guarantees, and no bounds checking. A plugin that reads
``dcf.inp`` directly would need to repeat this boilerplate for every
parameter it touches:

- look up the right table and row,
- handle case-insensitive key mismatches,
- convert compund units like ``"kWh/kg"`` into a proper unit-aware quantity,
- raise a helpful error message when something is missing.

``InputResolver`` encapsulates all of that. A plugin describes *what*
it expects in a plain Python dictionary (the **spec**), calls
``resolver.resolve(spec)``, and gets back a dictionary of validated,
unit-converted values.

How does dcf.inp look?
======================

After pyH2A parses an input file, ``dcf.inp`` is a nested dictionary
with three levels:

.. code-block:: text

    dcf.inp[top_key][mid_key][bottom_key]

- **top_key** — the name of the Markdown section heading
  (e.g. ``"Water Supply"``).
- **mid_key** — the value in the ``Name`` or ``Parameter`` column of
  that table (e.g. ``"Volume"``).
- **bottom_key** — the name of a column in that table row
  (e.g. ``"Value"``, ``"Unit"``, ``"Type"``).

For example, the following Markdown table:

.. code-block:: markdown

    # Water Supply

    Name | Value | Unit | Type
    --- | --- | --- | ---
    Volume | 50 | liters | flexible
    Purity | 99 | percent | contaminants

becomes:

.. code-block:: python

    dcf.inp["Water Supply"]["Volume"]["Value"]  # 50
    dcf.inp["Water Supply"]["Volume"]["Unit"]   # "liters"
    dcf.inp["Water Supply"]["Volume"]["Type"]   # "flexible"
    dcf.inp["Water Supply"]["Purity"]["Value"]  # 99
    dcf.inp["Water Supply"]["Purity"]["Unit"]   # "percent"

Writing a specification dictionary
===================================

The spec tells ``InputResolver`` where to look and what constraints to
enforce. There are three patterns you can use.

Explicit path (table → row → field)
------------------------------------

The most common pattern: name the table, the row, and the fields you
want.

.. code-block:: python

    spec = {
        "Water Supply": {             # top_key  (table name)
            "Volume": {               # mid_key  (row name)
                "Value": {            # bottom_key
                    "type": {float, int},
                    "bounds": (0, None),
                },
                "Unit": {             # paired unit column
                    "dimension": "volume",
                },
                "Type": {
                    "type": str,
                    "options": {"on_demand", "flexible"},
                },
            },
            "Purity": {
                "Value": {
                    "type": {float, int},
                    "bounds": (0, 1),
                },
                "Unit": {
                    "dimension": "dimensionless",
                },
                "Type": {
                    "type": str,
                    "options": {
                        "total_dissolved_solids", "contaminants"
                    },
                },
            },
        }
    }

Calling ``resolver.resolve(spec)`` will:

1. Find the ``"Water Supply"`` table (case-insensitive).
2. For each specified row, find the row (case-insensitive).
3. Parse ``dcf.inp`` references and apply ``process_table`` to evaluate
   any cross-references between tables.
4. Check that ``Volume`` value is a non-negative number.
5. Check that the ``Unit`` for ``Volume`` has dimension ``"volume"``.
6. Return a ``pint.Quantity`` for every ``Value`` field, already
   carrying its unit.

The returned dict mirrors the spec structure:

.. code-block:: python

    result = resolver.resolve(spec)
    result["Water Supply"]["Volume"]["Value"]
    # <Quantity(0.05, 'meter ** 3')>
    result["Water Supply"]["Purity"]["Value"]
    # <Quantity(0.99, 'dimensionless')>

Wildcard rows — all rows share the same shape
----------------------------------------------

Use ``"<...>"`` as a row key when every row in a table has the same
columns and you want all of them at once.

.. code-block:: python

    spec = {
        "Utilities": {
            "<...>": {                    # applies to every row
                "Usage_Value": {
                    "type": {float, int},
                    "bounds": (0, None),
                },
                "Usage_Unit": {
                    "dimension": "energy / mass",
                },
                "Cost_Value": {
                    "type": {float, int},
                    "bounds": (0, None),
                },
                "Cost_Unit": {
                    "dimension": "currency / energy",
                },
                "Type": {
                    "type": str,
                    "options": {"electricity", "natural_gas", "water"},
                },
            }
        }
    }

The result will contain one entry per row that was present in the table:

.. code-block:: python

    result["Utilities"]["Natural gas"]["Usage_Value"]
    # <Quantity(5.4e+09, 'joule / kilogram')>
    result["Utilities"]["Natural gas"]["Cost_Value"]
    # <Quantity(5.56e-05, 'USD / joule')>
    result["Utilities"]["Natural gas"]["Type"]
    # "natural_gas"

Note that ``Unit`` fields disappear from the output — their information
has been folded into the ``pint.Quantity`` attached to the corresponding
``Value`` field.

Wildcard tables — a pattern across multiple top-level headings
--------------------------------------------------------------

Use ``"<...>"`` (or a string containing it) as the top-level key when
the input file may contain several tables that share a common naming
convention, such as
``"Pump - Other Variable Operating Cost - Brand A"`` and
``"Compressor - Other Variable Operating Cost - Brand B"``:

.. code-block:: python

    spec = {
        "<...> Other Variable Operating Cost <...>": {
            "<...>": {
                "Value": {
                    "type": {float, np.ndarray},
                    "bounds": (0, None),
                },
                "Unit": {
                    "dimension": "currency",
                },
            }
        }
    }

Every table whose heading contains
``"Other Variable Operating Cost"`` is resolved and returned under
its full heading as the outer key.

Flat parameter spec
-------------------

For a single scalar parameter deep in the hierarchy, a flat dict with
``"top_level"``, ``"mid_level"``, and ``"bottom_level"`` keys can be
used instead of the nested form. This is convenient when you only need
one value:

.. code-block:: python

    spec = {
        "catalyst_lifetime": {
            "top_level":    "Catalyst",
            "mid_level":    "Lifetime",
            "bottom_level": "Value",
            "type": float,
            "bounds": (0, None),
        }
    }

    result = resolver.resolve(spec)
    result["catalyst_lifetime"]
    # <Quantity(1.58e+08, 'second')>

Spec fields reference
======================

Each leaf specification dict may contain any of the following keys.

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Key
     - Meaning
   * - ``type``
     - A Python type or set of types
       (e.g. ``float``, ``{float, int}``, ``str``). ``numpy`` numeric
       types are automatically included when ``float`` or ``int`` are
       specified.
   * - ``bounds``
     - ``(lower, upper)`` tuple. Either bound can be ``None`` for
       one-sided ranges. Bounds are checked *after* unit conversion,
       on the magnitude of the ``pint.Quantity``.
   * - ``dimension``
     - Physical dimension string for ``Unit`` fields
       (e.g. ``"energy / mass"``, ``"power"``, ``"dimensionless"``).
       ``InputResolver`` raises a ``ValueError`` if the user's unit
       does not match.
   * - ``options``
     - A set of allowed string values. Raises a ``ValueError`` if the
       field value is not a member.
   * - ``length``
     - Expected length for sequence values.
   * - ``optional``
     - Set to ``True`` to skip a row or field silently when it is
       absent. Without this, a missing key raises a ``KeyError``.
   * - ``description``
     - Human-readable description. Ignored during resolution; useful
       as documentation inside the spec.

Using the resolver in a plugin
===============================

The typical usage pattern inside a pyH2A plugin ``__init__`` is:

.. code-block:: python

    from pyH2A.Utilities.IO_Resolver.resolver import InputResolver

    class MyPlugin:
        def __init__(self, dcf):
            resolver = InputResolver(dcf, plugin_name="MyPlugin")

            inputs = resolver.resolve({
                "Water Supply": {
                    "Volume": {
                        "Value": {
                            "type": {float, int},
                            "bounds": (0, None),
                        },
                        "Unit": {"dimension": "volume"},
                        "Type": {
                            "type": str,
                            "options": {"on_demand", "flexible"},
                        },
                    },
                    "Purity": {
                        "Value": {
                            "type": {float, int},
                            "bounds": (0, 1),
                        },
                        "Unit": {"dimension": "dimensionless"},
                    },
                }
            })

            self.volume = (
                inputs["Water Supply"]["Volume"]["Value"]
            )
            self.purity = (
                inputs["Water Supply"]["Purity"]["Value"]
            )

Or using the convenience wrapper
:func:`~pyH2A.Utilities.IO_Resolver.resolver.input_resolver`:

.. code-block:: python

    from pyH2A.Utilities.IO_Resolver.resolver import input_resolver

    inputs = input_resolver(dcf, spec, plugin_name="MyPlugin")

Both forms are equivalent. The class form is preferred when you need to
reuse the resolver or access the ``pint.UnitRegistry`` via
``resolver.ureg``.

Error messages
==============

``InputResolver`` always includes the ``plugin_name`` and the full
``top_key > mid_key > bottom_key`` path in every error it raises, so
debugging a misconfigured input file is straightforward:

.. code-block:: text

    KeyError: "MyPlugin: Missing table 'My Parameters'."
    KeyError: "MyPlugin: Missing key 'My Parameters > Efficiency'."
    KeyError: "MyPlugin: Missing unit 'Efficiency > Unit' for 'Value'."
    TypeError: "MyPlugin: 'Efficiency > Value' expected float, got str."
    ValueError: "MyPlugin: 'Efficiency > Value' above upper bound 1."
    ValueError: "MyPlugin: Unit 'MW' dimension 'power' != 'dimensionless'."

How it works internally
========================

For reference, the resolution pipeline for a typical *explicit path*
call is:

1. ``resolve()`` inspects each key in the spec. If the spec value
   contains ``"top_level"`` / ``"mid_level"`` / ``"bottom_level"``,
   it is a **parameter spec** and routed through
   ``_resolve_param_spec``. Otherwise it is treated as a **table
   spec** and routed through ``_resolve_table``.

2. ``_resolve_table`` calls ``process_table_for_spec``, which in turn
   calls pyH2A's own ``process_table`` to evaluate any
   cross-references (``Path`` column entries) that the user wrote in
   the input file.

3. For each row in the table, ``_resolve_row`` iterates over the spec
   keys. Fields whose name contains ``"Value"`` are sent to
   ``_resolve_value_field``; pure ``Unit`` fields are skipped (they
   are consumed during value resolution); all other fields go through
   standard type/options/bounds validation via the validators module.

4. ``_resolve_value_field`` pairs the ``Value`` and ``Unit`` fields,
   optionally checks that the unit has the expected physical
   dimension, then calls ``UnitProcessor.convert_value_with_unit``
   to produce a ``pint.Quantity``. Bounds are then checked on the
   quantity's magnitude.

5. The fully resolved nested dictionary is returned to the caller.
