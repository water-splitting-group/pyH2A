Replacement_Plugin
==================

This plugin computes yearly replacement costs over the project lifetime, combining planned periodic replacements and unplanned replacement costs.

Equations
---------

Planned replacement costs
~~~~~~~~~~~~~~~~~~~~~~~~~

For each entry :math:`i` in the ``Planned Replacement`` table, the replacement frequency is converted into an integer number of years:

.. math::

   N_{\mathrm{rep},i}
   =
   \left\lceil
   t_{\mathrm{rep},i}
   \right\rceil

where:

- :math:`t_{\mathrm{rep},i}` is the specified replacement frequency
- :math:`\lceil \cdot \rceil` denotes the ceiling function

Because replacement costs are billed annually, a correction factor is applied when the specified replacement interval is non-integer:

.. math::

   f_{\mathrm{noninteger},i}
   =
   \frac{
   N_{\mathrm{rep},i}
   }{
   t_{\mathrm{rep},i}
   }

The replacement cost applied at each replacement event is then:

.. math::

   C_{\mathrm{planned},i}
   =
   C_{\mathrm{raw},i}
   \times
   f_{\mathrm{noninteger},i}
   \times
   f_{\mathrm{combined}}

where:

- :math:`C_{\mathrm{raw},i}` is the one-time replacement cost
- :math:`f_{\mathrm{combined}}` is the combined inflator

The yearly planned replacement cost is obtained by adding the contributions of all replacement events occurring during each project year.

Unplanned replacement costs
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Unplanned replacement costs are obtained by summing all entries belonging to the ``Unplanned Replacement`` table group:

.. math::

   C_{\mathrm{unplanned}}
   =
   \sum_i C_{\mathrm{unplanned},i}

This value is added uniformly to each year of operation.

Total yearly replacement costs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The total yearly replacement cost before inflation correction is:

.. math::

   C_{\mathrm{replacement}}(y)
   =
   C_{\mathrm{planned}}(y)
   +
   C_{\mathrm{unplanned}}

where:

- :math:`C_{\mathrm{planned}}(y)` is the total planned replacement cost during year :math:`y`

The final inflated yearly replacement cost is:

.. math::

   C_{\mathrm{replacement}}^{\mathrm{inflated}}(y)
   =
   C_{\mathrm{replacement}}(y)
   \times
   f_{\mathrm{inflation\ correction}}(y)
   \times
   f_{\mathrm{inflation}}(y)

The resulting quantity is stored as an array covering the entire plant lifetime.


Notation
~~~~~~~~

.. list-table::
   :widths: 30 50 40
   :header-rows: 1

   * - Symbol
     - Description
     - Dimension

   * - :math:`t_{\mathrm{rep},i}`
     - Replacement frequency for planned replacement entry :math:`i`
     - time

   * - :math:`N_{\mathrm{rep},i}`
     - Integer replacement interval used in the calculation
     - time

   * - :math:`f_{\mathrm{noninteger},i}`
     - Non-integer replacement correction factor
     - dimensionless

   * - :math:`C_{\mathrm{raw},i}`
     - One-time replacement cost for planned replacement entry :math:`i`
     - currency

   * - :math:`C_{\mathrm{planned},i}`
     - Inflated replacement cost applied at each replacement event
     - currency

   * - :math:`C_{\mathrm{planned}}(y)`
     - Total planned replacement cost during year :math:`y`
     - currency

   * - :math:`C_{\mathrm{unplanned},i}`
     - Individual unplanned replacement contribution
     - currency

   * - :math:`C_{\mathrm{unplanned}}`
     - Total unplanned replacement cost
     - currency

   * - :math:`C_{\mathrm{replacement}}(y)`
     - Total yearly replacement cost before inflation correction
     - currency

   * - :math:`C_{\mathrm{replacement}}^{\mathrm{inflated}}(y)`
     - Total yearly inflated replacement cost
     - currency

   * - :math:`f_{\mathrm{combined}}`
     - Combined inflator
     - dimensionless

   * - :math:`f_{\mathrm{inflation\ correction}}(y)`
     - Inflation correction factor for year :math:`y`
     - dimensionless

   * - :math:`f_{\mathrm{inflation}}(y)`
     - Inflation factor for year :math:`y`
     - dimensionless

Implementation
--------------

.. automodule:: pyH2A.Plugins.Replacement_Plugin
    :members: