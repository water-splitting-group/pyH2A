Power_Management_Plugin
=======================

The power management module allocates available and stored energy to different consumers and computes unmet demand and grid electricity usage.

Equations
---------

The system manages two energy streams on a yearly basis:

- flexible (directly available) energy
- stored (battery) energy

and allocates them sequentially to power consumers.

Available and stored energy (yearly aggregation)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Daily values are aggregated to yearly values:

.. math::

   E_{\mathrm{flex},y} = \sum_{d \in y} E_{\mathrm{avail},d,y}

.. math::

   E_{\mathrm{stor},y} = \sum_{d \in y} E_{\mathrm{stor},d,y}

Power allocation
~~~~~~~~~~~~~~~~

Let the set of consumers be split into:

- on-demand consumers :math:`\mathcal{C}_{\mathrm{on}}`
- flexible consumers :math:`\mathcal{C}_{\mathrm{flex}}`

1. On-demand consumers (stored energy only)

For each year:

.. math::

   E_{\mathrm{stor},y}^{(1)} =
   E_{\mathrm{stor},y}
   -
   \sum_{c \in \mathcal{C}_{\mathrm{on}}}
   \min\left(D_{c,y}, E_{\mathrm{stor},y}\right)

Unfulfilled demand:

.. math::

   U_{\mathrm{on},y}
   =
   \sum_{c \in \mathcal{C}_{\mathrm{on}}}
   \max\left(D_{c,y} - E_{\mathrm{stor},y}, 0\right)



2. Flexible consumers

Flexible consumers first use flexible energy, then stored energy:

Flexible allocation:

.. math::

   E_{\mathrm{flex},y}^{(1)} =
   E_{\mathrm{flex},y}
   -
   \sum_{c \in \mathcal{C}_{\mathrm{flex}}}
   \min\left(D_{c,y}, E_{\mathrm{flex},y}\right)

Residual demand:

.. math::

   D_{c,y}^{\mathrm{res}} =
   \max\left(D_{c,y} - E_{\mathrm{flex},y}, 0\right)

Stored allocation:

.. math::

   E_{\mathrm{stor},y}^{(2)} =
   E_{\mathrm{stor},y}^{(1)}
   -
   \sum_{c \in \mathcal{C}_{\mathrm{flex}}}
   \min\left(D_{c,y}^{\mathrm{res}}, E_{\mathrm{stor},y}^{(1)}\right)

Unfulfilled flexible demand:

.. math::

   U_{\mathrm{flex},y}
   =
   \sum_{c \in \mathcal{C}_{\mathrm{flex}}}
   \max\left(D_{c,y}^{\mathrm{res}} - E_{\mathrm{stor},y}^{(1)}, 0\right)



3. Total unfulfilled demand

.. math::

   U_{y} = U_{\mathrm{on},y} + U_{\mathrm{flex},y}



4. Grid electricity cost

Grid electricity compensates unmet demand:

.. math::

   C_{\mathrm{grid},y}
   =
   U_{y} \cdot p_{\mathrm{grid},y}

where :math:`p_{\mathrm{grid},y}` is the electricity price.



Notation
~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 45 25

   * - Symbol
     - Description
     - Dimension

   * - :math:`E_{\mathrm{avail},d,y}`
     - Available energy (daily input stream)
     - energy

   * - :math:`E_{\mathrm{stor},d,y}`
     - Stored energy (daily input stream)
     - energy

   * - :math:`E_{\mathrm{flex},y}`
     - Yearly flexible energy availability
     - energy

   * - :math:`E_{\mathrm{stor},y}`
     - Yearly stored energy availability
     - energy

   * - :math:`D_{c,y}`
     - Energy demand of consumer :math:`c`
     - energy

   * - :math:`\mathcal{C}_{\mathrm{on}}`
     - Set of on-demand consumers
     - dimensionless

   * - :math:`\mathcal{C}_{\mathrm{flex}}`
     - Set of flexible consumers
     - dimensionless

   * - :math:`U_{y}`
     - Total unfulfilled energy demand
     - energy

   * - :math:`p_{\mathrm{grid},y}`
     - Grid electricity cost per energy unit
     - currency / energy

   * - :math:`C_{\mathrm{grid},y}`
     - Grid electricity cost
     - currency


Implementation
--------------


.. automodule:: pyH2A.Plugins.Power_Management_Plugin
    :members: