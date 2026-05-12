PEC_Plugin
==========

The PEC plugin determines the number of cells, as well as various costs for photo-electrochemical hydrogen production.

Equations
---------

The area of a single PEC cell is:

.. math::

   A_{\mathrm{cell}}
   =
   L_{\mathrm{cell}}
   \cdot
   W_{\mathrm{cell}}

The solar power incident on one PEC cell is:

.. math::

   P_{\mathrm{solar,cell}}
   =
   A_{\mathrm{cell}}
   \cdot
   I_{\mathrm{solar}}

The hydrogen molar production rate per cell is:

.. math::

   \dot{n}_{\mathrm{H_2,cell}}
   =
   \frac{
   P_{\mathrm{solar,cell}}
   \cdot
   \eta_{\mathrm{STH}}
   }{
   E_{\mathrm{H_2}}
   }

The hydrogen mass production rate per cell is:

.. math::

   \dot{m}_{\mathrm{H_2,cell}}
   =
   \dot{n}_{\mathrm{H_2,cell}}
   \cdot
   M_{\mathrm{H_2}}

The hydrogen molar production rate per collection area is:

.. math::

   \dot{n}_{\mathrm{H_2,surf}}
   =
   \frac{
   \dot{n}_{\mathrm{H_2,cell}}
   }{
   A_{\mathrm{cell}}
   }

The cost of a single PEC cell is:

.. math::

   C_{\mathrm{cell}}
   =
   A_{\mathrm{cell}}
   \cdot
   c_{\mathrm{cell}}

The number of PEC cells required to satisfy the design output flowrate is:

.. math::

   N_{\mathrm{cell}}
   =
   \left\lceil
   \frac{
   \dot{m}_{\mathrm{design}}
   }{
   \dot{m}_{\mathrm{H_2,cell}}
   }
   \right\rceil

The total PEC cell cost is:

.. math::

   C_{\mathrm{PEC,total}}
   =
   N_{\mathrm{cell}}
   \cdot
   C_{\mathrm{cell}}

The total solar collection area is:

.. math::

   A_{\mathrm{solar,total}}
   =
   A_{\mathrm{cell}}
   \cdot
   N_{\mathrm{cell}}

The projected ground length occupied by one inclined PEC cell is:

.. math::

   L_{\mathrm{proj}}
   =
   L_{\mathrm{cell}}
   \cdot
   \cos(\theta_{\mathrm{cell}})

The total ground length per PEC cell row is:

.. math::

   L_{\mathrm{row}}
   =
   L_{\mathrm{proj}}
   +
   s_{\mathrm{south}}

The total ground width per PEC cell row is:

.. math::

   W_{\mathrm{row}}
   =
   W_{\mathrm{cell}}
   +
   s_{\mathrm{EW}}

The total land area requirement is:

.. math::

   A_{\mathrm{land,total}}
   =
   L_{\mathrm{row}}
   \cdot
   W_{\mathrm{row}}
   \cdot
   N_{\mathrm{cell}}

The PEC cell replacement frequency is equal to the PEC cell lifetime:

.. math::

   t_{\mathrm{replace}}
   =
   t_{\mathrm{cell}}


Notation
~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 45 45

   * - Symbol
     - Description
     - Dimension

   * - :math:`\dot{m}_{\mathrm{design}}`
     - Design output flowrate
     - mass / time

   * - :math:`c_{\mathrm{cell}}`
     - PEC cell cost per unit area
     - currency / area

   * - :math:`t_{\mathrm{cell}}`
     - PEC cell lifetime
     - time

   * - :math:`L_{\mathrm{cell}}`
     - PEC cell length
     - length

   * - :math:`W_{\mathrm{cell}}`
     - PEC cell width
     - length

   * - :math:`A_{\mathrm{cell}}`
     - Area of a single PEC cell
     - area

   * - :math:`\theta_{\mathrm{cell}}`
     - PEC cell angle from the ground
     - angle

   * - :math:`s_{\mathrm{south}}`
     - South spacing between PEC cells
     - length

   * - :math:`s_{\mathrm{EW}}`
     - East/West spacing between PEC cells
     - length

   * - :math:`\eta_{\mathrm{STH}}`
     - Solar-to-hydrogen efficiency
     - dimensionless

   * - :math:`I_{\mathrm{solar}}`
     - Mean solar input
     - power / area

   * - :math:`P_{\mathrm{solar,cell}}`
     - Solar power incident on one PEC cell
     - power

   * - :math:`E_{\mathrm{H_2}}`
     - Energy required to produce one mole of hydrogen
     - energy / amount of substance

   * - :math:`M_{\mathrm{H_2}}`
     - Molecular weight of hydrogen
     - mass / amount of substance

   * - :math:`\dot{n}_{\mathrm{H_2,cell}}`
     - Hydrogen molar production rate per PEC cell
     - amount of substance / time

   * - :math:`\dot{m}_{\mathrm{H_2,cell}}`
     - Hydrogen mass production rate per PEC cell
     - mass / time

   * - :math:`\dot{n}_{\mathrm{H_2,surf}}`
     - Hydrogen molar production rate per collection area
     - amount of substance / time / area

   * - :math:`C_{\mathrm{cell}}`
     - Cost of a single PEC cell
     - currency

   * - :math:`N_{\mathrm{cell}}`
     - Number of PEC cells required
     - dimensionless

   * - :math:`C_{\mathrm{PEC,total}}`
     - Total PEC cell cost
     - currency

   * - :math:`A_{\mathrm{solar,total}}`
     - Total solar collection area
     - area

   * - :math:`L_{\mathrm{proj}}`
     - Projected ground length of one inclined PEC cell
     - length

   * - :math:`L_{\mathrm{row}}`
     - Total ground length per PEC cell row
     - length

   * - :math:`W_{\mathrm{row}}`
     - Total ground width per PEC cell row
     - length

   * - :math:`A_{\mathrm{land,total}}`
     - Total land area requirement
     - area

   * - :math:`t_{\mathrm{replace}}`
     - PEC cell replacement frequency
     - time

Implementation
--------------

.. automodule:: pyH2A.Plugins.PEC_Plugin
    :members: