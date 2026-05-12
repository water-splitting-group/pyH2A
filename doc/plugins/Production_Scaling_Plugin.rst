Production_Scaling_Plugin
-------------------------

This plugin computes the delivered output and applies optional scaling relationships for plant capacity, capital costs, and labor costs.

Equations
---------

Plant scaling
~~~~~~~~~~~~~

If a new plant size is specified, the scaling ratio is:

.. math::

   R_{\mathrm{scale}} =
   \frac{\dot{Q}_{\mathrm{design,new}}}
   {\dot{Q}_{\mathrm{design}}}

Alternatively, the scaling ratio can be provided directly as an input.

The scaled design output is then:

.. math::

   \dot{Q}_{\mathrm{design,scaled}}
   =
   \dot{Q}_{\mathrm{design}}
   \times
   R_{\mathrm{scale}}

Similarly, the maximum gate output rate becomes:

.. math::

   \dot{Q}_{\mathrm{gate,max}}
   =
   \dot{Q}_{\mathrm{gate,max,0}}
   \times
   R_{\mathrm{scale}}

Capital and labor scaling factors are calculated using power-law scaling:

.. math::

   F_{\mathrm{cap}}
   =
   R_{\mathrm{scale}}^{n_{\mathrm{cap}}}

.. math::

   F_{\mathrm{labor}}
   =
   R_{\mathrm{scale}}^{n_{\mathrm{labor}}}

If no scaling is requested, the scaled quantities are equal to the original values.

Yearly output
~~~~~~~~~~~~~

The yearly production output is calculated from the scaled design output and the operating capacity factor:

.. math::

   Q_{\mathrm{year}}
   =
   \dot{Q}_{\mathrm{design,scaled}}
   \times
   f_{\mathrm{op}}

The yearly output at gate is:

.. math::

   Q_{\mathrm{year,gate}}
   =
   \dot{Q}_{\mathrm{gate,max}}
   \times
   f_{\mathrm{op}}

Notation
~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 50 50

   * - Symbol
     - Description
     - Dimension

   * - :math:`\dot{Q}_{\mathrm{design}}`
     - Plant design capacity
     - Functional unit dimension / time

   * - :math:`\dot{Q}_{\mathrm{design,new}}`
     - New plant design capacity
     - Functional unit dimension / time

   * - :math:`R_{\mathrm{scale}}`
     - Scaling ratio
     - Dimensionless

   * - :math:`\dot{Q}_{\mathrm{design,scaled}}`
     - Scaled design output rate
     - Functional unit dimension / time

   * - :math:`\dot{Q}_{\mathrm{gate,max,0}}`
     - Initial maximum output rate at gate
     - Functional unit dimension / time

   * - :math:`\dot{Q}_{\mathrm{gate,max}}`
     - Scaled maximum output rate at gate
     - Functional unit dimension / time

   * - :math:`n_{\mathrm{cap}}`
     - Capital scaling exponent
     - Dimensionless

   * - :math:`n_{\mathrm{labor}}`
     - Labor scaling exponent
     - Dimensionless

   * - :math:`F_{\mathrm{cap}}`
     - Capital scaling factor
     - Dimensionless

   * - :math:`F_{\mathrm{labor}}`
     - Labor scaling factor
     - Dimensionless

   * - :math:`f_{\mathrm{op}}`
     - Operating capacity factor
     - Dimensionless

   * - :math:`Q_{\mathrm{year}}`
     - Output per year
     - Functional unit dimension

   * - :math:`Q_{\mathrm{year,gate}}`
     - Output per year at gate
     - Functional unit dimension

Implementation
--------------     

.. automodule:: pyH2A.Plugins.Production_Scaling_Plugin
    :members: