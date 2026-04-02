Fixed_Operating_Cost_Plugin
===========================

This plugin computes yearly fixed operating costs, including labor costs and other fixed operating expenses.

Equations
~~~~~~~~~

Yearly labor cost (uninflated):

.. math::

   C_{\text{labor}}^{\text{uninfl}} = N_{\text{staff}} \cdot c_{\text{labor}} \cdot 2080

Yearly labor cost (inflated):

.. math::

   C_{\text{labor}} = C_{\text{labor}}^{\text{uninfl}} \cdot f_{\text{infl,labor}}


Other fixed operating costs:

.. math::

   C_{\text{fixed,other}} = \left( \sum_i C_{\text{fixed,other},i} \right) \cdot f_{\text{infl,combined}}


Total fixed operating costs:

.. math::

   C_{\text{fixed,total}} = C_{\text{labor}} + C_{\text{fixed,other}}


Notation
~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Symbol
     - Description
     - Dimension

   * - :math:`N_{\text{staff}}`
     - Number of staff  
       (``Fixed Operating Costs > staff > Value``)
     - Dimensionless

   * - :math:`c_{\text{labor}}`
     - Hourly labor cost  
       (``Fixed Operating Costs > hourly labor cost > Value``)
     - Currency / time

   * - :math:`C_{\text{labor}}^{\text{uninfl}}`
     - Yearly labor cost (before inflation)
     - Currency

   * - :math:`C_{\text{labor}}`
     - Yearly labor cost (after applying labor inflator)
     - Currency

   * - :math:`C_{\text{fixed,other},i}`
     - Individual other fixed operating cost entries  
       (from "Other Fixed Operating Cost" tables)
     - Currency

   * - :math:`C_{\text{fixed,other}}`
     - Total other fixed operating costs (after inflation)
     - Currency

   * - :math:`C_{\text{fixed,total}}`
     - Total yearly fixed operating costs
     - Currency

   * - :math:`f_{\text{infl,labor}}`
     - Labor inflation factor (``dcf.labor_inflator``)
     - Dimensionless

   * - :math:`f_{\text{infl,combined}}`
     - Combined inflation factor (``dcf.combined_inflator``)
     - Dimensionless

.. automodule:: pyH2A.Plugins.Fixed_Operating_Cost_Plugin
    :members: