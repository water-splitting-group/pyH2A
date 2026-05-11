Fixed_Operating_Cost_Plugin
===========================

This plugin computes yearly fixed operating costs, including labor costs and other fixed operating expenses.

Equations
---------

Labor costs
~~~~~~~~~~~

The yearly uninflated labor cost is calculated as:

.. math::

   C_{\mathrm{labor}}^{\mathrm{uninflated}}
   =
   N_{\mathrm{staff}}
   \times
   c_{\mathrm{labor,hour}}
   \times
   t_{\mathrm{work,year}}

where:

- :math:`N_{\mathrm{staff}}` is the number of staff
- :math:`c_{\mathrm{labor,hour}}` is the hourly labor cost
- :math:`t_{\mathrm{work,year}} = 2080 \ \mathrm{h}` is the assumed yearly working time per staff member

The inflated yearly labor cost is then:

.. math::

   C_{\mathrm{labor}}
   =
   C_{\mathrm{labor}}^{\mathrm{uninflated}}
   \times
   f_{\mathrm{labor}}

where:

- :math:`f_{\mathrm{labor}}` is the labor inflator

Other fixed operating costs
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Additional fixed operating costs are obtained by summing all entries belonging to the ``Other Fixed Operating Cost`` table group:

.. math::

   C_{\mathrm{other\ fixed}}
   =
   \left(
   \sum_i C_{\mathrm{other\ fixed},i}
   \right)
   \times
   f_{\mathrm{combined}}

where:

- :math:`C_{\mathrm{other\ fixed},i}` are the individual fixed operating cost contributions
- :math:`f_{\mathrm{combined}}` is the combined inflator

Total fixed operating costs
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The total yearly fixed operating cost is:

.. math::

   C_{\mathrm{fixed,total}}
   =
   C_{\mathrm{labor}}
   +
   C_{\mathrm{other\ fixed}}


Notation
~~~~~~~~

.. list-table::
   :widths: 30 50 20
   :header-rows: 1

   * - Symbol
     - Description
     - Dimension

   * - :math:`N_{\mathrm{staff}}`
     - Number of staff
     - dimensionless

   * - :math:`c_{\mathrm{labor,hour}}`
     - Hourly labor cost
     - currency / time

   * - :math:`t_{\mathrm{work,year}}`
     - Working hours in a year
     - time

   * - :math:`C_{\mathrm{labor}}^{\mathrm{uninflated}}`
     - Yearly labor cost before labor inflation
     - currency

   * - :math:`C_{\mathrm{labor}}`
     - Yearly labor cost after applying labor inflator
     - currency

   * - :math:`C_{\mathrm{other\ fixed},i}`
     - Individual other fixed operating cost contribution
     - currency

   * - :math:`C_{\mathrm{other\ fixed}}`
     - Total other fixed operating costs
     - currency

   * - :math:`C_{\mathrm{fixed,total}}`
     - Total yearly fixed operating costs
     - currency

   * - :math:`f_{\mathrm{labor}}`
     - Labor inflation factor
     - dimensionless

   * - :math:`f_{\mathrm{combined}}`
     - Combined inflation factor
     - dimensionless

.. automodule:: pyH2A.Plugins.Fixed_Operating_Cost_Plugin
    :members: