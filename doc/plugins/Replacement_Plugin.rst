Replacement_Plugin
==================

This plugin computes yearly replacement costs over the project lifetime, combining planned periodic replacements and unplanned replacement costs.

Equations
~~~~~~~~~

Planned replacement (per component):

For each component :math:`i`, with replacement frequency:

.. math::

   f_{\text{rep},i} = \left\lceil f_{\text{input},i} \right\rceil

Non-integer frequency correction:

.. math::

   \kappa_i = \frac{f_{\text{rep},i}}{f_{\text{input},i}}

Cost per replacement event:

.. math::

   C_{\text{rep},i} = C_{\text{raw},i} \cdot \kappa_i \cdot f_{\text{infl,combined}}

Replacement events occur at discrete years:

.. math::

   t \in \{f_{\text{rep},i},\; 2 f_{\text{rep},i},\; 3 f_{\text{rep},i},\; \dots\}

Yearly planned replacement cost:

.. math::

   C_{\text{planned}}(t) = \sum_i C_{\text{rep},i} \cdot \mathbf{1}_{t \in \text{schedule}_i}


Unplanned replacement:

.. math::

   C_{\text{unplanned}} = \sum_j C_{\text{unplanned},j}

This value is applied uniformly to all years:

.. math::

   C_{\text{unplanned}}(t) = C_{\text{unplanned}}


Total yearly replacement cost (before final inflation factors):

.. math::

   C_{\text{yearly}}(t) = C_{\text{planned}}(t) + C_{\text{unplanned}}(t)


Final inflated replacement cost:

.. math::

   C_{\text{replacement}}(t) = C_{\text{yearly}}(t) \cdot f_{\text{infl,correction}}(t) \cdot f_{\text{infl}}(t)


Notation
~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Symbol
     - Description
     - Dimension

   * - :math:`C_{\text{raw},i}`
     - One-time replacement cost for component :math:`i`  
       (``Planned Replacement > [...] > Cost``)
     - Currency

   * - :math:`f_{\text{input},i}`
     - Replacement frequency for component :math:`i`   
       (``Frequency``)
     - Time

   * - :math:`f_{\text{rep},i}`
     - Effective replacement interval (rounded to integer years)
     - Time

   * - :math:`\kappa_i`
     - Non-integer frequency correction factor
     - Dimensionless

   * - :math:`C_{\text{rep},i}`
     - Cost per replacement event (inflated and corrected)
     - Currency

   * - :math:`C_{\text{planned}}(t)`
     - Planned replacement cost in year :math:`t`
     - Currency

   * - :math:`C_{\text{unplanned},j}`
     - Individual unplanned replacement cost entries  
       (from "Unplanned Replacement" tables)
     - Currency

   * - :math:`C_{\text{unplanned}}`
     - Total unplanned replacement cost per year
     - Currency / time

   * - :math:`C_{\text{yearly}}(t)`
     - Total replacement cost before final inflation factors
     - Currency

   * - :math:`C_{\text{replacement}}(t)`
     - Final yearly replacement cost (after inflation adjustments)
     - Currency / time

   * - :math:`f_{\text{infl,combined}}`
     - Combined inflation factor (``dcf.combined_inflator``)
     - Dimensionless

   * - :math:`f_{\text{infl,correction}}(t)`
     - Inflation correction factor over time (``dcf.inflation_correction``)
     - Dimensionless

   * - :math:`f_{\text{infl}}(t)`
     - Time-dependent inflation factor (``dcf.inflation_factor``)
     - Dimensionless

   * - :math:`\mathbf{1}_{t \in \text{schedule}_i}`
     - Indicator function (equals 1 when a replacement occurs at year :math:`t`, 0 otherwise)
     - Dimensionless


.. automodule:: pyH2A.Plugins.Replacement_Plugin
    :members: