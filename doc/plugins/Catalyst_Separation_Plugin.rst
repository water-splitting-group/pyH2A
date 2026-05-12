Catalyst_Separation_Plugin
==========================

Equations
---------

The yearly fraction of water requiring catalyst separation is determined from the catalyst lifetime:

.. math::

   f_{\mathrm{filter}}
   =
   \frac{1}{t_{\mathrm{cat}}}

The yearly filtration volume is then:

.. math::

   V_{\mathrm{filter,year}}
   =
   V_{\mathrm{water}}
   \cdot
   f_{\mathrm{filter}}

The yearly catalyst separation cost is:

.. math::

   C_{\mathrm{sep,year}}
   =
   V_{\mathrm{filter,year}}
   \cdot
   c_{\mathrm{filter}}

The resulting yearly cost corresponds to:

``Other Variable Operating Cost - Catalyst Separation > Catalyst separation (yearly cost) > Value``


Notation
~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 45 25

   * - Symbol
     - Description
     - Dimension

   * - :math:`V_{\mathrm{water}}`
     - Total water volume
     - volume

   * - :math:`t_{\mathrm{cat}}`
     - Catalyst lifetime before replacement is required
     - time

   * - :math:`f_{\mathrm{filter}}`
     - Fraction of total water volume requiring filtration each year
     - 1 / time

   * - :math:`V_{\mathrm{filter,year}}`
     - Water volume filtered per year
     - volume

   * - :math:`c_{\mathrm{filter}}`
     - Filtration cost per unit volume
     - currency / volume

   * - :math:`C_{\mathrm{sep,year}}`
     - Yearly catalyst separation cost
     - currency


Implementation
--------------

.. automodule:: pyH2A.Plugins.Catalyst_Separation_Plugin
    :members: