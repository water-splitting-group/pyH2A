Solar_Thermal_Plugin
====================

The plugin estimates the required land area for thermochemical hydrogen production using solar input, conversion efficiency, and production target.

Equations
---------


Solar-to-hydrogen conversion
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The molar production rate per unit area is:

.. math::

   \dot{n}_{\mathrm{H_2}}
   =
   \frac{I_{\mathrm{solar}} \cdot \eta_{\mathrm{STH}}}
   {E_{\mathrm{H_2}}}

where:

- :math:`I_{\mathrm{solar}}` is the mean solar input,
- :math:`\eta_{\mathrm{STH}}` is the solar-to-hydrogen efficiency,
- :math:`E_{\mathrm{H_2}}` is the energy required per mole of hydrogen.

Conversion to mass-based production
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The hydrogen mass production per unit area is:

.. math::

   \dot{m}_{\mathrm{H_2}}
   =
   \dot{n}_{\mathrm{H_2}} \cdot M_{\mathrm{H_2}}

where :math:`M_{\mathrm{H_2}}` is the molar mass of hydrogen.

For alternative functional units (e.g. hydrogen peroxide), a fixed stoichiometric scaling is applied:

.. math::

   \dot{m}_{\mathrm{H_2O_2}}
   =
   17 \cdot \dot{m}_{\mathrm{H_2}}

Required land area
~~~~~~~~~~~~~~~~~~

The required solar collection area is computed from the plant design output rate:

.. math::

   A_{\mathrm{req}}
   =
   \frac{\dot{m}_{\mathrm{design}}}{\dot{m}_{\mathrm{H_2}}}

The final land requirement includes an additional land area factor:

.. math::

   A_{\mathrm{total}}
   =
   A_{\mathrm{req}} \cdot (1 + f_{\mathrm{land,add}})

Notation
~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 10 50 30

   * - Symbol
     - Description
     - Dimension

   * - :math:`I_{\mathrm{solar}}`
     - Mean solar input
     - power / area

   * - :math:`\eta_{\mathrm{STH}}`
     - Solar-to-hydrogen efficiency
     - Dimensionless

   * - :math:`E_{\mathrm{H_2}}`
     - Energy per mole of hydrogen
     - energy / mole

   * - :math:`\dot{n}_{\mathrm{H_2}}`
     - Hydrogen molar production rate per area
     - mol / (area · time)

   * - :math:`M_{\mathrm{H_2}}`
     - Molar mass of hydrogen
     - kg / mol

   * - :math:`\dot{m}_{\mathrm{H_2}}`
     - Hydrogen mass production per area
     - mass / (area · time)

   * - :math:`\dot{m}_{\mathrm{H_2O_2}}`
     - Equivalent hydrogen peroxide mass rate
     - mass / (area · time)

   * - :math:`\dot{m}_{\mathrm{design}}`
     - Plant design output rate
     - mass / time

   * - :math:`A_{\mathrm{req}}`
     - Required solar collection area
     - area

   * - :math:`f_{\mathrm{land,add}}`
     - Additional land area factor
     - Dimensionless

   * - :math:`A_{\mathrm{total}}`
     - Total required land area
     - area

Implementation
--------------

.. automodule:: pyH2A.Plugins.Solar_Thermal_Plugin
    :members: