Solar_Concentrator_Plugin
=========================



Equations
---------

Solar concentration scales the active collection area and propagates into land use and capital cost.

Solar collection area
~~~~~~~~~~~~~~~~~~~~~~

The concentrated solar collection area is:

.. math::

   A_{\mathrm{solar}}
   =
   f_{\mathrm{conc}} \cdot A_{\mathrm{solar,0}}


Area per PEC element
~~~~~~~~~~~~~~~~~~~~~

The area assigned per PEC cell is:

.. math::

   A_{\mathrm{cell}}
   =
   \frac{A_{\mathrm{solar}}}{N_{\mathrm{PEC}}}


A characteristic side length is derived as:

.. math::

   L_{\mathrm{cell}} = \sqrt{A_{\mathrm{cell}}}



Spacing correction (land footprint)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Including spacing in both directions:

.. math::

   L_x = L_{\mathrm{cell}} + \frac{s_{EW}}{2}

.. math::

   L_y = L_{\mathrm{cell}} + \frac{s_{S}}{2}

where:
- :math:`s_{EW}` = east-west spacing  
- :math:`s_{S}` = south spacing  

The spaced area per element becomes:

.. math::

   A_{\mathrm{land,cell}} = L_x \cdot L_y

Total land area:

.. math::

   A_{\mathrm{land}}
   =
   N_{\mathrm{PEC}} \cdot A_{\mathrm{land,cell}}



Solar concentrator capital cost
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The total concentrator cost is:

.. math::

   C_{\mathrm{conc,tot}}
   =
   c_{\mathrm{conc}} \cdot A_{\mathrm{solar}}

where:
- :math:`c_{\mathrm{conc}}` is cost per unit area
- :math:`A_{\mathrm{solar}}` is total solar collection area



Notation
~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 45 25

   * - Symbol
     - Description
     - Dimension

   * - :math:`f_{\mathrm{conc}}`
     - Solar concentration factor
     - dimensionless

   * - :math:`A_{\mathrm{solar,0}}`
     - Unconcentrated solar collection area
       (input solar collection area)
     - area

   * - :math:`A_{\mathrm{solar}}`
     - Concentrated solar collection area
     - area

   * - :math:`N_{\mathrm{PEC}}`
     - Number of PEC cells
     - dimensionless

   * - :math:`A_{\mathrm{cell}}`
     - Area allocated per PEC cell
     - area

   * - :math:`L_{\mathrm{cell}}`
     - Characteristic linear dimension per PEC cell
     - length

   * - :math:`s_S`
     - South spacing
     - length

   * - :math:`s_{EW}`
     - East/West spacing
     - length

   * - :math:`A_{\mathrm{land}}`
     - Total land area requirement
     - area

   * - :math:`c_{\mathrm{conc}}`
     - Solar concentrator cost per area
     - currency / area

   * - :math:`C_{\mathrm{conc,tot}}`
     - Total solar concentrator capital cost
     - currency


Implementation
--------------


.. automodule:: pyH2A.Plugins.Solar_Concentrator_Plugin
    :members: