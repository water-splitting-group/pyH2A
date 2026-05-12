Electrolyzer_Plugin
===================

Equations
---------

For each operating year :math:`y`, the electrolyzer power demand is increased to account for stack degradation:

.. math::

   f_{\mathrm{power},y}
   =
   \left(
   1 + r_{\mathrm{power}}
   \right)^y

.. math::

   P_{\mathrm{el},y}
   =
   P_{\mathrm{el}}^{\mathrm{nom}}
   \cdot
   f_{\mathrm{power},y}

The hourly electrolyzer energy demand is:

.. math::

   E_{\mathrm{el},h,y}^{\mathrm{demand}}
   =
   3600
   \cdot
   P_{\mathrm{el},y}

For each hourly timestep :math:`h`, the consumed energy is limited by the available energy:

.. math::

   E_{\mathrm{el},h,y}^{\mathrm{cons}}
   =
   \min
   \left(
   E_{\mathrm{avail},h,y},
   E_{\mathrm{el},h,y}^{\mathrm{demand}}
   \right)

The instantaneous electrolyzer capacity factor is:

.. math::

   f_{\mathrm{cap},h,y}
   =
   \frac{
   E_{\mathrm{el},h,y}^{\mathrm{cons}}
   }{
   E_{\mathrm{el},h,y}^{\mathrm{demand}}
   }

Electrolyzer operation is only allowed when the minimum operating capacity is reached:

.. math::

   \chi_{h,y}
   =
   \begin{cases}
   1 & \text{if } f_{\mathrm{cap},h,y} > f_{\mathrm{min}} \\
   0 & \text{if } f_{\mathrm{cap},h,y} \leq f_{\mathrm{min}}
   \end{cases}

The effective hourly energy consumption is therefore:

.. math::

   E_{\mathrm{el},h,y}^{\mathrm{eff}}
   =
   E_{\mathrm{el},h,y}^{\mathrm{cons}}
   \cdot
   \chi_{h,y}

The hydrogen production during each hourly timestep is:

.. math::

   m_{\mathrm{H2},h,y}
   =
   \frac{
   E_{\mathrm{el},h,y}^{\mathrm{eff}}
   \cdot
   \eta_{\mathrm{H2}}
   }{
   f_{\mathrm{power},y}
   }

The yearly hydrogen production is:

.. math::

   m_{\mathrm{H2},y}
   =
   \sum_h
   m_{\mathrm{H2},h,y}

The yearly electrolyzer operating duration is:

.. math::

   t_{\mathrm{op},y}
   =
   \sum_h
   \chi_{h,y}

The remaining unused hourly energy is:

.. math::

   E_{\mathrm{unused},h,y}
   =
   E_{\mathrm{avail},h,y}
   -
   E_{\mathrm{el},h,y}^{\mathrm{eff}}

The daily unused energy is obtained by aggregating the hourly unused energy:

.. math::

   E_{\mathrm{unused},d,y}
   =
   \sum_{h \in d}
   E_{\mathrm{unused},h,y}

The plant design capacity is constructed from yearly hydrogen production data, including construction years during which production is zero:

.. math::

   \dot{m}_{\mathrm{plant}}
   =
   \left[
   \underbrace{0,\dots,0}_{t_{\mathrm{construction}}},
   m_{\mathrm{H2},1},
   m_{\mathrm{H2},2},
   \dots
   \right]

The operating capacity factor is fixed to:

.. math::

   f_{\mathrm{op}} = 1

The cumulative electrolyzer operating time is:

.. math::

   t_{\mathrm{cum},y}
   =
   \sum_{i=1}^{y}
   t_{\mathrm{op},i}

The stack usage ratio is:

.. math::

   u_{\mathrm{stack},y}
   =
   \frac{
   t_{\mathrm{cum},y}
   }{
   t_{\mathrm{replace}}
   }

The total number of stack replacements is:

.. math::

   N_{\mathrm{replace}}
   =
   \left\lfloor
   u_{\mathrm{stack},Y}
   \right\rfloor

where :math:`Y` is the final operating year.

The replacement frequency is then calculated as:

.. math::

   t_{\mathrm{replace,freq}}
   =
   \frac{
   N_{\mathrm{years}}
   }{
   N_{\mathrm{replace}} + 1
   }

The electrolyzer CAPEX scaling factor is calculated from the number of ten-fold increases relative to the reference power:

.. math::

   N_{10}
   =
   \log_{10}
   \left(
   \frac{
   P_{\mathrm{el}}^{\mathrm{nom}}
   }{
   P_{\mathrm{ref}}
   }
   \right)

.. math::

   f_{\mathrm{CAPEX}}
   =
   M_{\mathrm{CAPEX}}^{N_{10}}



Notation
~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 45 25

   * - Symbol
     - Description
     - Dimension

   * - :math:`E_{\mathrm{avail},h,y}`
     - Available hourly energy for timestep :math:`h` in year :math:`y`
     - energy

   * - :math:`P_{\mathrm{el}}^{\mathrm{nom}}`
     - Electrolyzer nominal power
     - power

   * - :math:`P_{\mathrm{ref}}`
     - Electrolyzer CAPEX reference power
     - power

   * - :math:`r_{\mathrm{power}}`
     - Power requirement increase per year
     - dimensionless

   * - :math:`f_{\mathrm{power},y}`
     - Electrolyzer power increase ratio for year :math:`y`
     - dimensionless

   * - :math:`P_{\mathrm{el},y}`
     - Electrolyzer power demand during year :math:`y`
     - power

   * - :math:`E_{\mathrm{el},h,y}^{\mathrm{demand}}`
     - Hourly electrolyzer energy demand
     - energy

   * - :math:`E_{\mathrm{el},h,y}^{\mathrm{cons}}`
     - Hourly electrolyzer energy consumption before minimum-capacity filtering
     - energy

   * - :math:`f_{\mathrm{cap},h,y}`
     - Instantaneous electrolyzer operating capacity fraction
     - dimensionless

   * - :math:`f_{\mathrm{min}}`
     - Minimum electrolyzer operating capacity
     - dimensionless

   * - :math:`\chi_{h,y}`
     - Binary operating-state indicator
     - dimensionless

   * - :math:`E_{\mathrm{el},h,y}^{\mathrm{eff}}`
     - Effective hourly electrolyzer energy consumption
     - energy

   * - :math:`\eta_{\mathrm{H2}}`
     - Hydrogen yield per unit energy
     - mass / energy

   * - :math:`m_{\mathrm{H2},h,y}`
     - Hydrogen produced during hourly timestep :math:`h`
     - mass

   * - :math:`m_{\mathrm{H2},y}`
     - Total yearly hydrogen production
     - mass

   * - :math:`t_{\mathrm{op},y}`
     - Electrolyzer operating duration during year :math:`y`
     - time

   * - :math:`E_{\mathrm{unused},h,y}`
     - Unused hourly energy after electrolysis
     - energy

   * - :math:`E_{\mathrm{unused},d,y}`
     - Daily unused energy after electrolysis
     - energy

   * - :math:`\dot{m}_{\mathrm{plant}}`
     - Plant design capacity
     - mass / time

   * - :math:`f_{\mathrm{op}}`
     - Operating capacity factor
     - dimensionless

   * - :math:`t_{\mathrm{construction}}`
     - Construction time
     - time

   * - :math:`t_{\mathrm{cum},y}`
     - Cumulative electrolyzer operating time up to year :math:`y`
     - time

   * - :math:`t_{\mathrm{replace}}`
     - Electrolyzer stack replacement time
     - time

   * - :math:`u_{\mathrm{stack},y}`
     - Stack usage ratio
     - dimensionless

   * - :math:`N_{\mathrm{replace}}`
     - Number of stack replacements
     - dimensionless

   * - :math:`N_{\mathrm{years}}`
     - Total number of operating years
     - dimensionless

   * - :math:`t_{\mathrm{replace,freq}}`
     - Electrolyzer stack replacement frequency
     - time

   * - :math:`M_{\mathrm{CAPEX}}`
     - CAPEX multiplier
     - dimensionless

   * - :math:`N_{10}`
     - Number of ten-fold increases relative to the CAPEX reference power
     - dimensionless

   * - :math:`f_{\mathrm{CAPEX}}`
     - Electrolyzer CAPEX scaling factor
     - dimensionless

Implementation
--------------

.. automodule:: pyH2A.Plugins.Electrolyzer_Plugin
    :members: