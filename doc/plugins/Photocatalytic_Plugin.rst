Photocatalytic_Plugin
=====================

The Photocatalytic plugin calcualtes the characteristics of a photocatalytic hydrogen production plant (number of baggies, water etc) and subsequent costs.

Equations
---------

Hydrogen production per baggie
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The area of a single reactor baggie is:

.. math::

   A_{\mathrm{baggie}}
   =
   L_{\mathrm{baggie}}
   \cdot
   W_{\mathrm{baggie}}

The mean solar power intercepted by one baggie is:

.. math::

   P_{\mathrm{solar,baggie}}
   =
   A_{\mathrm{baggie}}
   \cdot
   I_{\mathrm{solar}}

The hydrogen molar production rate per baggie is:

.. math::

   \dot{n}_{\mathrm{H_2,baggie}}
   =
   \frac{
   P_{\mathrm{solar,baggie}}
   \cdot
   \eta_{\mathrm{STH}}
   }{
   E_{\mathrm{H_2}}
   }

The hydrogen mass production rate per baggie is:

.. math::

   \dot{m}_{\mathrm{H_2,baggie}}
   =
   \dot{n}_{\mathrm{H_2,baggie}}
   \cdot
   MW_{\mathrm{H_2}}

The required number of baggies is:

.. math::

   N_{\mathrm{baggie}}
   =
   \left\lceil
   \frac{
   \dot{m}_{\mathrm{design}}
   }{
   \dot{m}_{\mathrm{H_2,baggie}}
   }
   \right\rceil



Baggie costs
~~~~~~~~~~~~

The material cost per baggie is:

.. math::

   C_{\mathrm{material,baggie}}
   =
   A_{\mathrm{baggie}}
   \cdot
   \left(
   c_{\mathrm{top}}
   +
   c_{\mathrm{bottom}}
   \right)

The port cost per baggie is:

.. math::

   C_{\mathrm{port,baggie}}
   =
   N_{\mathrm{ports}}
   \cdot
   c_{\mathrm{port}}

The total cost per baggie is:

.. math::

   C_{\mathrm{baggie,unit}}
   =
   f_{\mathrm{markup}}
   \cdot
   \left(
   C_{\mathrm{material,baggie}}
   +
   C_{\mathrm{port,baggie}}
   +
   C_{\mathrm{other,baggie}}
   \right)

The total baggie cost is:

.. math::

   C_{\mathrm{baggie,total}}
   =
   N_{\mathrm{baggie}}
   \cdot
   C_{\mathrm{baggie,unit}}



Catalyst inventory and catalyst cost
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The volume of a single baggie is:

.. math::

   V_{\mathrm{baggie}}
   =
   L_{\mathrm{baggie}}
   \cdot
   W_{\mathrm{baggie}}
   \cdot
   h_{\mathrm{fill}}

The total reactor volume is:

.. math::

   V_{\mathrm{total}}
   =
   V_{\mathrm{baggie}}
   \cdot
   N_{\mathrm{baggie}}

The catalyst mass per baggie is:

.. math::

   m_{\mathrm{cat,baggie}}
   =
   V_{\mathrm{baggie}}
   \cdot
   \rho_{\mathrm{cat}}

The total catalyst inventory is:

.. math::

   m_{\mathrm{cat,total}}
   =
   m_{\mathrm{cat,baggie}}
   \cdot
   N_{\mathrm{baggie}}

The total catalyst cost is:

.. math::

   C_{\mathrm{cat,total}}
   =
   m_{\mathrm{cat,total}}
   \cdot
   c_{\mathrm{cat}}



Land area
~~~~~~~~~

The total solar collection area is:

.. math::

   A_{\mathrm{solar}}
   =
   N_{\mathrm{baggie}}
   \cdot
   A_{\mathrm{baggie}}

The total required land area is:

.. math::

   A_{\mathrm{land}}
   =
   A_{\mathrm{solar}}
   \cdot
   \left(
   1 +
   f_{\mathrm{land,add}}
   \right)



Planned replacement quantities
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The catalyst replacement frequency is equal to the catalyst lifetime:

.. math::

   t_{\mathrm{cat,replacement}}
   =
   t_{\mathrm{cat}}

The baggie replacement frequency is equal to the baggie lifetime:

.. math::

   t_{\mathrm{baggie,replacement}}
   =
   t_{\mathrm{baggie}}

The catalyst replacement cost is:

.. math::

   C_{\mathrm{cat,replacement}}
   =
   C_{\mathrm{cat,total}}

The baggie replacement cost is:

.. math::

   C_{\mathrm{baggie,replacement}}
   =
   C_{\mathrm{baggie,total}}



Catalyst activity calculations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The peak hydrogen production per unit area is:

.. math::

   \dot{n}_{\mathrm{H_2,peak}}
   =
   \frac{
   E_{\mathrm{solar,peak}}
   \cdot
   \eta_{\mathrm{STH}}
   }{
   E_{\mathrm{H_2}}
   }

The catalyst mass per unit area is:

.. math::

   \Gamma_{\mathrm{cat}}
   =
   h_{\mathrm{fill}}
   \cdot
   \rho_{\mathrm{cat}}

The peak catalyst activity is:

.. math::

   TOF_{\mathrm{peak,mass}}
   =
   \frac{
   \dot{n}_{\mathrm{H_2,peak}}
   }{
   \Gamma_{\mathrm{cat}}
   }

The mean hydrogen production rate per unit area is:

.. math::

   \dot{n}_{\mathrm{H_2,mean}}
   =
   \frac{
   I_{\mathrm{solar}}
   \cdot
   \eta_{\mathrm{STH}}
   }{
   E_{\mathrm{H_2}}
   }



Homogeneous catalyst calculations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the catalyst molar weight is provided, the catalyst concentration per volume is:

.. math::

   C_{\mathrm{cat,molar}}
   =
   \frac{
   \rho_{\mathrm{cat}}
   }{
   MW_{\mathrm{cat}}
   }

The catalyst amount per unit area is:

.. math::

   \Gamma_{\mathrm{cat,molar}}
   =
   h_{\mathrm{fill}}
   \cdot
   C_{\mathrm{cat,molar}}

The peak turnover frequency is:

.. math::

   TOF_{\mathrm{peak}}
   =
   \frac{
   \dot{n}_{\mathrm{H_2,peak}}
   }{
   \Gamma_{\mathrm{cat,molar}}
   }

The mean daily turnover frequency is:

.. math::

   TOF_{\mathrm{mean}}
   =
   \frac{
   \dot{n}_{\mathrm{H_2,mean,daily}}
   }{
   \Gamma_{\mathrm{cat,molar}}
   }

The turnover number is:

.. math::

   TON
   =
   TOF_{\mathrm{mean}}
   \cdot
   t_{\mathrm{cat}}

If the molar attenuation coefficient is provided, the absorbance is:

.. math::

   Abs
   =
   C_{\mathrm{cat,molar}}
   \cdot
   h_{\mathrm{fill}}
   \cdot
   \varepsilon_{\mathrm{mol}}

The absorbed light fraction is:

.. math::

   f_{\mathrm{abs}}
   =
   1 - 10^{-Abs}



Notation
~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 45 25

   * - Symbol
     - Description
     - Dimension

   * - :math:`\dot{m}_{\mathrm{design}}`
     - Design output flowrate
     - mass / time

   * - :math:`L_{\mathrm{baggie}}`
     - Baggie length
     - length

   * - :math:`W_{\mathrm{baggie}}`
     - Baggie width
     - length

   * - :math:`h_{\mathrm{fill}}`
     - Baggie filling height
     - length

   * - :math:`A_{\mathrm{baggie}}`
     - Area of one reactor baggie
     - area

   * - :math:`V_{\mathrm{baggie}}`
     - Volume of one reactor baggie
     - volume

   * - :math:`I_{\mathrm{solar}}`
     - Mean solar input
     - power / area

   * - :math:`E_{\mathrm{solar,peak}}`
     - Peak hourly solar irradiation
       derived from
     - energy / area

   * - :math:`\eta_{\mathrm{STH}}`
     - Solar-to-hydrogen efficiency
     - dimensionless

   * - :math:`E_{\mathrm{H_2}}`
     - Energy required to produce one mole of hydrogen
     - energy / substance

   * - :math:`MW_{\mathrm{H_2}}`
     - Molecular weight of hydrogen
     - mass / substance

   * - :math:`\dot{n}_{\mathrm{H_2,baggie}}`
     - Hydrogen molar production rate per baggie
     - substance / time

   * - :math:`\dot{m}_{\mathrm{H_2,baggie}}`
     - Hydrogen mass production rate per baggie
     - mass / time

   * - :math:`N_{\mathrm{baggie}}`
     - Number of required reactor baggies
     - dimensionless

   * - :math:`c_{\mathrm{top}}`
     - Cost of baggie top material
     - currency / area

   * - :math:`c_{\mathrm{bottom}}`
     - Cost of baggie bottom material
     - currency / area

   * - :math:`N_{\mathrm{ports}}`
     - Number of ports per baggie
     - dimensionless

   * - :math:`c_{\mathrm{port}}`
     - Cost of one port
     - currency

   * - :math:`C_{\mathrm{other,baggie}}`
     - Other costs per baggie
     - currency

   * - :math:`f_{\mathrm{markup}}`
     - Baggie markup factor
     - dimensionless

   * - :math:`C_{\mathrm{baggie,total}}`
     - Total baggie cost
     - currency

   * - :math:`\rho_{\mathrm{cat}}`
     - Catalyst concentration
     - mass / volume

   * - :math:`m_{\mathrm{cat,total}}`
     - Total catalyst mass
     - mass

   * - :math:`c_{\mathrm{cat}}`
     - Catalyst cost per unit mass
     - currency / mass

   * - :math:`C_{\mathrm{cat,total}}`
     - Total catalyst cost
     - currency

   * - :math:`A_{\mathrm{solar}}`
     - Total solar collection area
     - area

   * - :math:`f_{\mathrm{land,add}}`
     - Additional land area factor
     - dimensionless

   * - :math:`A_{\mathrm{land}}`
     - Total required land area
     - area

   * - :math:`t_{\mathrm{cat}}`
     - Catalyst lifetime
     - time

   * - :math:`t_{\mathrm{baggie}}`
     - Baggie lifetime
     - time

   * - :math:`MW_{\mathrm{cat}}`
     - Catalyst molar weight
     - mass / substance

   * - :math:`\varepsilon_{\mathrm{mol}}`
     - Catalyst molar attenuation coefficient
     - volume / (length \* substance)

   * - :math:`Abs`
     - Catalyst absorbance
     - dimensionless

   * - :math:`f_{\mathrm{abs}}`
     - Fraction of absorbed light
     - dimensionless

Implementation
--------------

.. automodule:: pyH2A.Plugins.Photocatalytic_Plugin
    :members: