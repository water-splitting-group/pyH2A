Production_Scaling_Plugin
=========================

This plugin computes plant output and optional scaling factors affecting subsequent capital and labor calculations.

Equations
~~~~~~~~~

Default definitions:

If not specified, the maximum output at gate is set equal to the plant design capacity:

.. math::

   Q_{\text{max,gate}} = Q_{\text{design}}


Scaling ratio:

If a new plant design capacity is provided:

.. math::

   R_{\text{scale}} = \frac{Q_{\text{design,new}}}{Q_{\text{design}}}


Scaled daily outputs (if scaling is active):

.. math::

   Q_{\text{design,scaled}} = Q_{\text{design}} \cdot R_{\text{scale}}

.. math::

   Q_{\text{max,gate,scaled}} = Q_{\text{max,gate}} \cdot R_{\text{scale}}


If no scaling is applied:

.. math::

   Q_{\text{design,scaled}} = Q_{\text{design}}

.. math::

   Q_{\text{max,gate,scaled}} = Q_{\text{max,gate}}


Scaling factors (if scaling is active):

.. math::

   f_{\text{scale,cap}} = R_{\text{scale}}^{\alpha_{\text{cap}}}

.. math::

   f_{\text{scale,lab}} = R_{\text{scale}}^{\alpha_{\text{lab}}}

If exponents are not specified:

.. math::

   \alpha_{\text{cap}} = 0.78

.. math::

   \alpha_{\text{lab}} = 0.25


Yearly outputs:

.. math::

   Q_{\text{year}} = Q_{\text{design,scaled}} \cdot 365 \cdot f_{\text{op}}

.. math::

   Q_{\text{year,gate}} = Q_{\text{max,gate,scaled}} \cdot 365 \cdot f_{\text{op}}


Notation
~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Symbol
     - Description
     - Dimension

   * - :math:`Q_{\text{design}}`
     - Plant design capacity  
       (``Plant Design Capacity``)
     - Mass / time

   * - :math:`Q_{\text{design,new}}`
     - New plant design capacity (for scaling)  
       (``New Plant Design Capacity``)
     - Mass / time

   * - :math:`Q_{\text{max,gate}}`
     - Maximum output at gate  
       (``Maximum Output at Gate``)
     - Mass / time

   * - :math:`Q_{\text{design,scaled}}`
     - Scaled design output per day  
       (``Design Output per Day``)
     - Mass / time

   * - :math:`Q_{\text{max,gate,scaled}}`
     - Scaled maximum gate output per day  
       (``Max Gate Output per Day``)
     - Mass / time

   * - :math:`Q_{\text{year}}`
     - Yearly hydrogen output  
       (``Output per Year``)
     - Mass

   * - :math:`Q_{\text{year,gate}}`
     - Yearly hydrogen output at gate  
       (``Output per Year at Gate``)
     - Mass

   * - :math:`f_{\text{op}}`
     - Operating capacity factor (fraction)  
       (``Operating Capacity Factor (%)``)
     - Dimensionless

   * - :math:`R_{\text{scale}}`
     - Scaling ratio  
       (``Scaling Ratio``)
     - Dimensionless

   * - :math:`f_{\text{scale,cap}}`
     - Capital scaling factor  
       (``Scaling > Capital Scaling Factor``)
     - Dimensionless

   * - :math:`f_{\text{scale,lab}}`
     - Labor scaling factor  
       (``Scaling > Labor Scaling Factor``)
     - Dimensionless

   * - :math:`\alpha_{\text{cap}}`
     - Capital scaling exponent  
       (``Capital Scaling Exponent``; default = 0.78)
     - Dimensionless

   * - :math:`\alpha_{\text{lab}}`
     - Labor scaling exponent  
       (``Labor Scaling Exponent``; default = 0.25)
     - Dimensionless

.. automodule:: pyH2A.Plugins.Production_Scaling_Plugin
    :members: