Stored_Power_Electrolysis_Plugin
================================

This plugin computes hydrogen production from stored-energy electrolysis, tracks annual energy consumption, and determines stack replacement frequency.

Equations
---------


Electrolyzer power demand
~~~~~~~~~~~~~~~~~~~~~~~~~~

The electrolyzer power demand increases over time due to degradation:

.. math::

   P_{\mathrm{ely}}(t)
   =
   P_{\mathrm{nom}}
   \cdot (1 + r_{\mathrm{deg}})^{t}

where the degradation factor is:

.. math::

   I_{\mathrm{deg}}(t) = (1 + r_{\mathrm{deg}})^{t}

Maximum usable energy per year
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The maximum energy that can be consumed by the electrolyzer is limited by operating time:

.. math::

   E_{\mathrm{max}}(t)
   =
   \left(T_{\mathrm{year}} - T_{\mathrm{op}}(t)\right)
   \cdot P_{\mathrm{ely}}(t)

Available stored energy
~~~~~~~~~~~~~~~~~~~~~~~

Stored energy available for electrolysis is:

.. math::

   E_{\mathrm{store,avail}}(t)
   =
   f_{\mathrm{store}} \cdot E_{\mathrm{store}}(t)

Energy consumption (actual)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Actual electrolysis energy consumption is the minimum of available storage and demand:

.. math::

   E_{\mathrm{cons}}(t)
   =
   \min \left(
   E_{\mathrm{max}}(t),
   E_{\mathrm{store,avail}}(t)
   \right)

Hydrogen production
~~~~~~~~~~~~~~~~~~~

Hydrogen production is computed from energy consumption and conversion efficiency:

.. math::

   \dot{m}_{\mathrm{H2}}(t)
   =
   \frac{E_{\mathrm{cons}}(t) \cdot \eta_{\mathrm{ely}}}
   {I_{\mathrm{deg}}(t)}

Stack replacement frequency
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The cumulative operating time determines stack replacement timing:

.. math::

   T_{\mathrm{cum}}(t) = \sum_{i \le t} T_{\mathrm{op}}(i)

.. math::

   N_{\mathrm{rep}} = \left\lfloor \frac{T_{\mathrm{cum}}(T)}{T_{\mathrm{rep}}} \right\rfloor

.. math::

   f_{\mathrm{rep}} =
   \frac{N_{\mathrm{years}}}{N_{\mathrm{rep}} + 1}

Updated annual hydrogen production
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Final hydrogen production includes degradation-adjusted additional production:

.. math::

   \dot{m}_{\mathrm{H2,new}}(t)
   =
   \dot{m}_{\mathrm{H2,old}}(t)
   +
   \Delta \dot{m}_{\mathrm{H2}}(t)

where:

.. math::

   \Delta \dot{m}_{\mathrm{H2}}(t)
   =
   \frac{E_{\mathrm{cons}}(t) \cdot \eta_{\mathrm{ely}}}
   {I_{\mathrm{deg}}(t)}



Notation
~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 50 20

   * - Symbol
     - Description
     - Dimension

   * - :math:`f_{\mathrm{store}}`
     - Fraction of stored power used for electrolysis
     - Dimensionless

   * - :math:`E_{\mathrm{store}}(t)`
     - Stored energy available per year
     - Energy

   * - :math:`E_{\mathrm{cons}}(t)`
     - Electrolysis energy consumption
     - Energy

   * - :math:`E_{\mathrm{max}}(t)`
     - Maximum consumable energy
     - Energy

   * - :math:`P_{\mathrm{ely}}(t)`
     - Electrolyzer power demand
     - Power

   * - :math:`P_{\mathrm{nom}}`
     - Nominal electrolyzer power
     - Power

   * - :math:`r_{\mathrm{deg}}`
     - Power requirement increase per year
     - Dimensionless

   * - :math:`I_{\mathrm{deg}}(t)`
     - Degradation/increase factor
     - Dimensionless

   * - :math:`\eta_{\mathrm{ely}}`
     - Hydrogen yield per unit energy
     - mass / energy

   * - :math:`\dot{m}_{\mathrm{H2}}(t)`
     - Hydrogen production rate (yearly)
     - mass / time

   * - :math:`T_{\mathrm{op}}(t)`
     - Operating time per year
     - time

   * - :math:`T_{\mathrm{rep}}`
     - Stack replacement time
     - time

   * - :math:`f_{\mathrm{rep}}`
     - Replacement frequency (years)
     - time

   * - :math:`\dot{m}_{\mathrm{H2,new}}(t)`
     - Updated hydrogen production
     - mass / time


Implementation
--------------



.. automodule:: pyH2A.Plugins.Stored_Power_Electrolysis_Plugin
    :members: