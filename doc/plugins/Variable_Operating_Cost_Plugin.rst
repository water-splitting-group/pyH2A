Variable_Operating_Cost_Plugin
==============================

This plugin computes variable operating costs, including utility costs (time-dependent) and other variable costs.
The result is expressed as a time-dependent quantity (array over plant lifetime).

Equations
~~~~~~~~~

Utility cost per kg of hydrogen (for each utility :math:`u`):

.. math::

   c_{\text{util},u}(t) = p_u(t) \cdot f_{\text{infl}}(t) \cdot f_{\text{conv},u} \cdot \gamma_u

Total utility cost per kg of hydrogen:

.. math::

   c_{\text{util,total}}(t) = \sum_u c_{\text{util},u}(t)


Total utility cost per year:

.. math::

   C_{\text{util}}(t) = c_{\text{util,total}}(t) \cdot Q_{\text{year}}


Other variable operating costs:

.. math::

   C_{\text{var,other}} = \left( \sum_i C_{\text{var,other},i} \right) \cdot f_{\text{infl,chem}}


Total variable operating costs:

.. math::

   C_{\text{var,total}}(t) = C_{\text{util}}(t) + C_{\text{var,other}}


Notation
~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Symbol
     - Description
     - Dimension

   * - :math:`p_u(t)`
     - Cost of utility :math:`u` (possibly time-dependent, from file or scalar)  
       (``Utilities > [...] > Cost``)
     - Currency / utility amount

   * - :math:`\gamma_u`
     - Utility usage per kg of hydrogen  
       (``Utilities > [...] > Usage per kg H2``)
     - Utility amount / mass

   * - :math:`f_{\text{conv},u}`
     - Price conversion factor  
       (``Utilities > [...] > Price Conversion Factor``)
     - Dimensionless

   * - :math:`f_{\text{infl}}(t)`
     - Inflation correction factor over time (``dcf.inflation_correction``)
     - Dimensionless

   * - :math:`c_{\text{util},u}(t)`
     - Cost contribution of utility :math:`u` per kg of hydrogen
     - Currency / mass

   * - :math:`c_{\text{util,total}}(t)`
     - Total utility cost per kg of hydrogen
     - Currency / mass

   * - :math:`Q_{\text{year}}`
     - Yearly hydrogen production  
       (``Output per Year``)
     - Mass

   * - :math:`C_{\text{util}}(t)`
     - Total utility cost per year (time-dependent)
     - Currency / time

   * - :math:`C_{\text{var,other},i}`
     - Individual other variable operating cost entries  
       (from "Other Variable Operating Cost" tables)
     - Currency

   * - :math:`C_{\text{var,other}}`
     - Total other variable operating costs (after inflation)
     - Currency

   * - :math:`f_{\text{infl,chem}}`
     - Chemical inflation factor (``dcf.chemical_inflator``)
     - Dimensionless

   * - :math:`C_{\text{var,total}}(t)`
     - Total variable operating costs (time-dependent)
     - Currency


Notes
-----

- Utility costs are evaluated **per kg of hydrogen**, then scaled by annual production.
- Costs can be:
  - constant (scalar),
  - time-dependent (array),
  - or read from external files.
- Inflation correction is applied at the **unit cost level**.
- Other variable operating costs are aggregated using ``sum_all_tables()`` and scaled by the chemical inflator.

.. automodule:: pyH2A.Plugins.Variable_Operating_Cost_Plugin
    :members: