Multiple_Modules_Plugin
=======================

The Multiple_Modules plugin determines the number of staff required to operate a plant made of multiple modules.

Equations
---------

The total solar collection area across all plant modules is:

.. math::

   A_{\mathrm{total}}
   =
   N_{\mathrm{modules}}
   \cdot
   A_{\mathrm{solar,module}}

The number of operating staff required for one shift is calculated as:

.. math::

   N_{\mathrm{staff,shift}}
   =
   \left\lceil
   \frac{
   A_{\mathrm{total}}
   }{
   A_{\mathrm{staff}}
   }
   \right\rceil
   +
   N_{\mathrm{supervisors}}

where :math:`\lceil \cdot \rceil` denotes rounding upward to the nearest integer.

The total number of 8-hour equivalent staff across all shifts is:

.. math::

   N_{\mathrm{staff,total}}
   =
   N_{\mathrm{staff,shift}}
   \cdot
   N_{\mathrm{shifts}}

The resulting number of staff required per plant module is:

.. math::

   N_{\mathrm{staff,module}}
   =
   \frac{
   N_{\mathrm{staff,total}}
   }{
   N_{\mathrm{modules}}
   }


Notation
~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 45 20

   * - Symbol
     - Description
     - Dimension

   * - :math:`N_{\mathrm{modules}}`
     - Number of plant modules considered in the calculation
     - dimensionless

   * - :math:`A_{\mathrm{solar,module}}`
     - Solar collection area for one plant module
     - area

   * - :math:`A_{\mathrm{total}}`
     - Total solar collection area across all plant modules
     - area

   * - :math:`A_{\mathrm{staff}}`
     - Solar collection area that can be covered by one staffer
     - area

   * - :math:`N_{\mathrm{supervisors}}`
     - Number of supervisors per shift
     - dimensionless

   * - :math:`N_{\mathrm{staff,shift}}`
     - Number of staff required for one 8-hour shift
     - dimensionless

   * - :math:`N_{\mathrm{shifts}}`
     - Number of 8-hour shifts
     - dimensionless

   * - :math:`N_{\mathrm{staff,total}}`
     - Total number of 8-hour equivalent staff across all shifts
     - dimensionless

   * - :math:`N_{\mathrm{staff,module}}`
     - Number of 8-hour equivalent staff required per plant module
     - dimensionless

Implementation
--------------

.. automodule:: pyH2A.Plugins.Multiple_Modules_Plugin
    :members: