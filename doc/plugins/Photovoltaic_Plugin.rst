Photovoltaic_Plugin
===================


Equations
---------

Photovoltaic electricity production is calculated from time-resolved irradiation data, PV efficiency, installed capacity, and degradation effects.



Yearly degradation factor:

.. math::

   f_{\mathrm{deg},y}
   =
   \left(1 - \lambda_{\mathrm{PV}}\right)^y



Corrected irradiation (time-dependent):

.. math::

   I_{t,y}
   =
   I_t \cdot f_{\mathrm{deg},y}



Instantaneous electrical power output:

.. math::

   P_{t,y}
   =
   I_{t,y} \cdot P_{\mathrm{PV}}^{\mathrm{nom}}



Hourly energy production (1-hour resolution):

.. math::

   E_{t,y}
   =
   P_{t,y} \cdot \Delta t
   \quad (\Delta t = 1\,\mathrm{h})



Daily aggregation:

.. math::

   E_{\mathrm{day},y}
   =
   \sum_{t \in \mathrm{day}} E_{t,y}



CAPEX scaling factor:

.. math::

   n_{\mathrm{10x}}
   =
   \log_{10}\!\left(
   \frac{P_{\mathrm{PV}}^{\mathrm{nom}}}{P_{\mathrm{PV}}^{\mathrm{ref}}}
   \right)

.. math::

   f_{\mathrm{CAPEX}}
   =
   m^{\,n_{\mathrm{10x}}}



PV area requirement:

.. math::

   A_{\mathrm{PV}}
   =
   \frac{P_{\mathrm{PV}}^{\mathrm{nom}}}{\eta_{\mathrm{PV}} \cdot I_{\mathrm{peak}}}

with :math:`I_{\mathrm{peak}} = 1\,\mathrm{kW/m^2}`.



Notation
~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 45 25

   * - Symbol
     - Description
     - Dimension

   * - :math:`I_t`
     - Hourly irradiation data
     - power / area

   * - :math:`\lambda_{\mathrm{PV}}`
     - PV power loss per year
     - dimensionless

   * - :math:`f_{\mathrm{deg},y}`
     - Degradation correction factor in year :math:`y`
     - dimensionless

   * - :math:`P_{\mathrm{PV}}^{\mathrm{nom}}`
     - Nominal PV power
     - power

   * - :math:`P_{\mathrm{PV}}^{\mathrm{ref}}`
     - CAPEX reference power
     - power

   * - :math:`P_{t,y}`
     - PV power output at time :math:`t` in year :math:`y`
     - power

   * - :math:`E_{t,y}`
     - Hourly energy production
     - energy

   * - :math:`E_{\mathrm{day},y}`
     - Daily energy production
     - energy

   * - :math:`m`
     - CAPEX multiplier
     - dimensionless

   * - :math:`f_{\mathrm{CAPEX}}`
     - PV CAPEX scaling factor
     - dimensionless

   * - :math:`P_{\mathrm{PV}}^{\mathrm{nom}} / P_{\mathrm{PV}}^{\mathrm{ref}}`
     - Power scaling ratio used for CAPEX scaling
     - dimensionless

   * - :math:`\eta_{\mathrm{PV}}`
     - PV efficiency
     - dimensionless

   * - :math:`A_{\mathrm{PV}}`
     - Required PV collection area
     - area

   * - :math:`I_{\mathrm{peak}}`
     - Peak solar irradiation assumption
     - power / area

Implementation
--------------

.. automodule:: pyH2A.Plugins.Photovoltaic_Plugin
    :members: