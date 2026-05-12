Battery_Plugin
==============

For each operating year :math:`y`, the battery storage model calculates the recoverable stored energy and the remaining unstored energy on a daily basis.


Equations
---------

Battery capacity degradation is first applied:

.. math::

   f_{\mathrm{cap},y} =
   \left(1 - \lambda_{\mathrm{cap}}\right)^y

.. math::

   E_{\mathrm{bat},y}^{\mathrm{avail}} =
   E_{\mathrm{bat}}^{\mathrm{design}}
   \cdot
   \left(1 - f_{\mathrm{discharge,min}}\right)
   \cdot
   f_{\mathrm{cap},y}

For each day :math:`d` of year :math:`y`, the stored energy is limited by the available energy and the available battery capacity:

.. math::

   E_{\mathrm{stored},d,y}
   =
   \min
   \left(
   E_{\mathrm{avail},d,y},
   E_{\mathrm{bat},y}^{\mathrm{avail}}
   \right)

The recoverable stored energy after round-trip efficiency losses is:

.. math::

   E_{\mathrm{recovered},d,y}
   =
   E_{\mathrm{stored},d,y}
   \cdot
   \eta_{\mathrm{rt}}


The available daily energy is updated after storage:

.. math::

   E_{\mathrm{avail},d,y}^{\mathrm{updated}}
   =
   E_{\mathrm{avail},d,y}
   -
   E_{\mathrm{stored},d,y}



Notation
~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 45 25

   * - Symbol
     - Description
     - Dimension

   * - :math:`E_{\mathrm{avail},d,y}`
     - Initial available energy for day :math:`d` in year :math:`y`
       before battery storage
       (``Power Generation > Available energy (daily) > Value`` input)
     - energy

   * - :math:`E_{\mathrm{avail},d,y}^{\mathrm{updated}}`
     - Available energy remaining after battery storage
       (``Power Generation > Available energy (daily) > Value`` output)
     - energy

   * - :math:`E_{\mathrm{bat}}^{\mathrm{design}}`
     - Battery design capacity
     - energy

   * - :math:`f_{\mathrm{discharge,min}}`
     - Lowest discharge level
     - dimensionless

   * - :math:`\lambda_{\mathrm{cap}}`
     - Capacity loss per year
     - dimensionless

   * - :math:`f_{\mathrm{cap},y}`
     - Remaining battery capacity fraction in year :math:`y`
     - dimensionless

   * - :math:`E_{\mathrm{bat},y}^{\mathrm{avail}}`
     - Available battery capacity in year :math:`y`
     - energy

   * - :math:`\eta_{\mathrm{rt}}`
     - Battery round-trip efficiency
     - dimensionless

   * - :math:`E_{\mathrm{stored},d,y}`
     - Energy stored in the battery on day :math:`d`
     - energy

   * - :math:`E_{\mathrm{recovered},d,y}`
     - Recoverable stored energy after round-trip efficiency losses
     - energy


Implementation
--------------

.. automodule:: pyH2A.Plugins.Battery_Plugin
    :members: