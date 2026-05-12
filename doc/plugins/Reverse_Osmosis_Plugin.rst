Reverse_Osmosis_Plugin
======================

Equations
---------

Fresh water requirement from hydrogen production
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The hydrogen output is first converted into a required freshwater mass using stoichiometry:

.. math::

   m_{\mathrm{H2O},y}
   =
   m_{\mathrm{H2},y}
   \cdot
   \frac{M_{\mathrm{H2O}}}{M_{\mathrm{H2}}}

Fresh water volume demand:

.. math::

   V_{\mathrm{fresh},y}
   =
   \frac{m_{\mathrm{H2O},y}}{\rho_{\mathrm{water}}}

Sea water demand corrected for recovery rate:

.. math::

   V_{\mathrm{sea},y}
   =
   \frac{V_{\mathrm{fresh},y}}{\eta_{\mathrm{rec}}}


Electricity demand of reverse osmosis:

.. math::

   E_{\mathrm{RO},y}
   =
   V_{\mathrm{sea},y}
   \cdot
   e_{\mathrm{RO}}

Construction delay is applied by truncating the time series:

.. math::

   E_{\mathrm{RO},y}^{\mathrm{effective}}
   =
   E_{\mathrm{RO},y}
   \big[\, t \geq t_{\mathrm{construction}} \,\big]

Maximum sea water processing flowrate:

.. math::

   \dot{V}_{\mathrm{sea}}^{\max}
   =
   \frac{\max_y(V_{\mathrm{sea},y})}{H_{\mathrm{year}} \cdot f_{\mathrm{op}}}

Notation
~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 45 25

   * - Symbol
     - Description
     - Dimension

   * - :math:`m_{\mathrm{H2},y}`
     - Hydrogen production in year y
     - mass

   * - :math:`M_{\mathrm{H2O}}, M_{\mathrm{H2}}`
     - Molar masses of water and hydrogen
     - mass/substance

   * - :math:`\rho_{\mathrm{water}}`
     - Density of water
     - mass/volume

   * - :math:`V_{\mathrm{fresh},y}`
     - Fresh water demand
     - volume

   * - :math:`\eta_{\mathrm{rec}}`
     - Reverse osmosis recovery rate
     - dimensionless

   * - :math:`V_{\mathrm{sea},y}`
     - Sea water intake volume
     - volume

   * - :math:`e_{\mathrm{RO}}`
     - Reverse osmosis energy demand per volume
     - energy/volume

   * - :math:`E_{\mathrm{RO},y}`
     - Electricity demand of RO system (before construction delay)
     - energy

   * - :math:`t_{\mathrm{construction}}`
     - Construction time
     - time

   * - :math:`f_{\mathrm{op}}`
     - Average operating time fraction
     - dimensionless

   * - :math:`H_{\mathrm{year}}`
     - Hours in a year
     - time

   * - :math:`\dot{V}_{\mathrm{sea}}^{\max}`
     - Maximum seawater processing flowrate
     - volume/time      



Implementation
--------------

.. automodule:: pyH2A.Plugins.Reverse_Osmosis_Plugin
    :members: