Quantity (Unit Handler) Guide
=============================

The ``pyH2A.Utilities.Unit_handler.quantity`` module provides a lightweight, computationally efficient replacement for explicit external unit libraries (like Pint). It is designed specifically for pyH2A to manage multi-unit conversions gracefully, support single values and ``numpy`` arrays, and handle lazy evaluation for performance optimizations.

Core Concepts
-------------

The central component of this utility is the ``Quantity`` class. Whenever you process input that has a numerical value accompanied by a unit string (e.g., ``"kWh"``, ``"kWh / m2 / day"``), ``Quantity`` will automatically standardize the value to its base SI formulation.

Key Features:
- Immediate formulation of the core numerical value into the absolute base unit.
- Supports single scalar floats/ints or entire ``numpy`` arrays.
- Implements lazy loading for unit conversions (e.g., retrieving the value in another valid unit automatically processes the conversion when requested via ``q.unit["..."]``, avoiding precalculating all possibilities).
- Built-in rigid dimension verification constraints prevent impossible conversions.
- Full support for temperature conversions including Absolute Temperature logic natively.

Supported Data Types
--------------------

The ``Quantity`` object is designed to process both single numerical values and arrays. The ``value`` parameter accepts the following data types natively:

- ``int``: For integer scalar values.
- ``float``: For floating-point scalar values.
- ``np.ndarray``: For entire NumPy arrays, allowing efficient vectorization and broad array-based operations directly within the unit handler.

The base value (stored as ``base_value``) and any converted value arrays accessed via the unit dictionary will inherently preserve this mathematical structure, ensuring transparent compatibility with logically intensive pyH2A plugins.

Supported Dimensions and Units
------------------------------

The following table provides a complete overview of all physical dimensions strictly supported by the framework, including their defined base unit and all acceptable alternative units.

.. list-table:: Supported Dimensions and Units
   :widths: 20 15 65
   :header-rows: 1

   * - Dimension
     - Base Unit
     - Other Supported Units
   * - ``absolute_temperature``
     - K
     - degC
   * - ``energy``
     - J
     - kJ, MJ, GJ, Wh, kWh, MWh, GWh, eV, cal, kcal
   * - ``power``
     - W
     - kW, MW, GW, hp
   * - ``length``
     - m
     - mm, cm, km
   * - ``area``
     - m2
     - mm2, cm2, km2, acre, ha
   * - ``volume``
     - m3
     - mm3, cm3, L, liters, km3, mL, uL
   * - ``time``
     - s
     - minute, h, day, week, year, ms
   * - ``currency``
     - USD
     - EUR
   * - ``mass``
     - kg
     - mg, g, ton
   * - ``temperature_diff``
     - delta_K
     - delta_degC
   * - ``substance``
     - mol
     - umol, mmol
   * - ``voltage``
     - V
     - 
   * - ``current``
     - A
     - mA
   * - ``angle``
     - rad
     - deg
   * - ``pressure``
     - Pa
     - hPa, atm, bar, MPa, psi
   * - ``force``
     - N
     - kN
   * - ``frequency``
     - Hz
     - kHz, MHz, GHz
   * - ``charge``
     - C
     - mC, Ah, mAh
   * - ``resistance``
     - Ohm
     - mOhm, kOhm
   * - ``dimensionless``
     - -
     - ppm, ppb

Basic Usage
-----------

To instantiate a ``Quantity``, you simply pass the numerical value alongside its matching unit abbreviation as a string.

.. code-block:: python

    from pyH2A.Utilities.Unit_handler.quantity import Quantity
    import numpy as np

    # Scalar numerical values
    energy = Quantity(2, "kWh")
    print(energy.base_value)  # 7.2e6
    print(energy.base_unit)   # 'J'
    print(energy.dimension)   # 'energy'

    # Retrieve value in another valid dimension
    print(energy.unit["J"])   # 7200000.0
    print(energy.unit["kWh"]) # 2.0

    # Numpy array integration
    lengths = Quantity(np.array([1.0, 2.0, 3.0]), "km")
    print(lengths.base_value) # array([1000., 2000., 3000.])
    print(lengths.unit["cm"]) # array([100000., 200000., 300000.])

Composite Units
---------------

You can provide complex/composite strings containing math markers such as ``*``, ``/``, ``(``, and ``)``, which the unit handler handles automatically.

.. code-block:: python

    composite_val = Quantity(10, "(kWh * m) / m2")
    
    print(composite_val.base_unit) # '( J * m ) / m2'
    print(composite_val.dimension) # '( energy * length ) / area'

Temperature Handling
--------------------

Absolute temperature conversions (e.g., converting Celsius ``degC`` to Kelvin ``K``) are handled on a unique isolated pathway since temperature conversion incorporates offsets, which cannot be modeled by simple multiplication.

.. code-block:: python

    temp = Quantity(25, "degC")
    print(temp.base_unit) # 'K'
    print(temp.base_value) # 298.15
    print(temp.unit["degC"]) # 25.0
    
Best Practices
--------------

1. **Leverage the Unit Dictionary Lazily**: Access unit conversions through the `.unit` dictionary exclusively in context paths where you specifically know the target unit representation required by a function plugin. Because it implements lazy dictionary loading, it stores the results for reuse, keeping memory light.
   
2. **Dimension Checking Contexts**: When handling data provided by users or unverified plugins, attempt an initial `.unit["Expected"]` access or string equality check on the `.dimension` property early in execution, which inherently raises ``ValueError`` if dimensionality paths are broken (e.g., attempting length -> energy).

3. **Avoid Space formatting errors**: The strict string parsing algorithm naturally tokenizes empty whitespace strings or expressions containing varying spacings. However, to keep definitions robust, it is highly recommended to pad internal composite expression markers neatly: ``"kWh / day"`` instead of ``"kWh/day"``, though both will compile.

Internal Workings Architecture
------------------------------

For optimization, defining ``Quantity`` constructs triggers the immediate parsing via ``parse_composite_unit(unit_str)``. It identifies base unit identifiers and recursively scales and extracts the resulting unit modifier coefficient dynamically evaluated into restricted environments for safety. 

This lazy ``UnitDictionary`` overrides the standard Python native mapping logic such that when an undeclared unit is accessed (``dict[target]`` where target does not exist natively), ``__missing__`` overrides are activated. It computes dimensions, offsets, or multipliers lazily. The calculated target is then stored, so subsequent references to the exact same unit incur zero extra computational delay.
