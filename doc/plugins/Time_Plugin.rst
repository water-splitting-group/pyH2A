Time_Plugin
===================

The ``Time_Plugin`` generates a dictionary containing the time-related quantities used throughout the calculation workflow.

All generated quantities are dimensionless. Calendar years are treated as labels or indices rather than physical durations.

Notation
---------

.. list-table:: Notation
   :widths: 25 35 
   :header-rows: 1

   * - Symbol
     - Description
   * - :math:`Y_{ref}`
     - Reference year
   * - :math:`Y_{start}`
     - Startup year
   * - :math:`t_{const}`
     - Construction time
   * - :math:`t_{life}`
     - Plant life
   * - :math:`\Delta Y`
     - Startup time offset

Generated quantities
--------------------

Startup time offset
~~~~~~~~~~~~~~~~~~~

.. math::

   \Delta Y = Y_{start} - Y_{ref}

Plant years relative
~~~~~~~~~~~~~~~~~~~~

The array of all years involved in the project, including construction years.

.. math::

   \mathrm{Plant Years Relative}
   =
   \left[
   -t_{const},
   \ldots,
   -1,
   0,
   1,
   \ldots,
   t_{life}-1
   \right]

where year 0 corresponds to the first year of operation.

Operation years
~~~~~~~~~~~~~~~

The calendar years during which production occurs.

.. math::

   \mathrm{Operation Years}
   =
   \left[
   Y_{start},
   Y_{start}+1,
   \ldots,
   Y_{start}+t_{life}-1
   \right]

Operation years relative
~~~~~~~~~~~~~~~~~~~~~~~~

The operation years expressed relative to startup.

.. math::

   \mathrm{Operation Years Relative}
   =
   \left[
   0,
   1,
   \ldots,
   t_{life}-1
   \right]

Start index
~~~~~~~~~~~

The relative year of startup.

.. math::

   \mathrm{Start index} = Y_{operation start} - Y_{construction start} 

Operation years ones
~~~~~~~~~~~~~~~~~~~~

Array of ones having the same length as the operation period.

.. math::

   \mathrm{Operation Years Ones}
   =
   \left[
   1,
   1,
   \ldots,
   1
   \right]

Analysis years ones
~~~~~~~~~~~~~~~~~~~

Array of ones having the same length as the construction and operation period.

.. math::

   \mathrm{Analysis Years Ones}
   =
   \left[
   1,
   1,
   \ldots,
   1
   \right]   

Construction years ones
~~~~~~~~~~~~~~~~~~~~~~~

Array of ones having the same length as the construction period.

.. math::

   \mathrm{Construction Years Ones}
   =
   \left[
   1,
   1,
   \ldots,
   1
   \right] 

Example
-------

Consider:

.. list-table::
   :widths: 60 40
   :header-rows: 1

   * - Parameter
     - Value
   * - Reference year
     - 2020
   * - Startup year
     - 2025
   * - Construction time
     - 2 years
   * - Plant life
     - 5 years

The plugin generates:

.. math::

   \Delta Y = 2025 - 2020 = 5

::

   Startup time offset:
   5

   Plant years relative:
   [-2, -1, 0, 1, 2, 3, 4]

   Operation years:
   [2025, 2026, 2027, 2028, 2029]

   Operation years relative:
   [0, 1, 2, 3, 4]

   Startup index:
   2

   Operation years ones:
   [1, 1, 1, 1, 1]

   Analysis years ones:
   [1, 1, 1, 1, 1, 1, 1]

   Construction years ones:
   [1, 1]   

Returned dictionary
-------------------

The plugin inserts:

::

   Time
   └── Years
       └── Value

which contains:

::

   {
       "Startup time offset": 5,
       "Plant years relative": [-2, -1, 0, 1, 2, 3, 4],
       "Operation years": [2025, 2026, 2027, 2028, 2029],
       "Operation years relative": [0, 1, 2, 3, 4],
       "Startup index": 2,
       "Operation years ones": [1, 1, 1, 1, 1], 
       "Analysis years ones": [1, 1, 1, 1, 1, 1, 1], 
       "Construction years ones": [1, 1]
   }

These quantities are subsequently used by other plugins whenever time indexing, yearly arrays, inflation corrections, or project scheduling information are required.    


.. automodule:: pyH2A.Plugins.Core.Time_Plugin
    :members: