Capital_Cost_Plugin
===================

This plugin computes the different components of capital costs based on grouped cost entries and applies inflation factors.

Equations
---------

Direct capital costs
~~~~~~~~~~~~~~~~~~~~

The total direct capital cost is obtained by summing all entries belonging to the ``Direct Capital Cost`` table group:

.. math::

   C_{\mathrm{direct}} = \sum_i C_{\mathrm{direct},i}

The inflated direct capital cost is then:

.. math::

   C_{\mathrm{direct}}^{\mathrm{inflated}}
   =
   C_{\mathrm{direct}} \times f_{\mathrm{combined}}

Indirect capital costs
~~~~~~~~~~~~~~~~~~~~~~

The total indirect capital cost is obtained by summing all entries belonging to the ``Indirect Capital Cost`` table group:

.. math::

   C_{\mathrm{indirect}} = \sum_i C_{\mathrm{indirect},i}

The inflated indirect capital cost is:

.. math::

   C_{\mathrm{indirect}}^{\mathrm{inflated}}
   =
   C_{\mathrm{indirect}} \times f_{\mathrm{combined}}

Non-depreciable capital costs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The land cost contribution is calculated as:

.. math::

   C_{\mathrm{land}}
   =
   c_{\mathrm{land}}
   \times
   A_{\mathrm{land}}

where:

- :math:`c_{\mathrm{land}}` is the land cost per unit area
- :math:`A_{\mathrm{land}}` is the required land area

Additional non-depreciable contributions are summed from the ``Other Non-Depreciable Capital Cost`` table group:

.. math::

   C_{\mathrm{other\_nondep}}
   =
   \sum_i C_{\mathrm{other\_nondep},i}

The total non-depreciable capital cost is therefore:

.. math::

   C_{\mathrm{nondep}}
   =
   C_{\mathrm{land}}
   +
   C_{\mathrm{other\_nondep}}

The inflated non-depreciable capital cost is:

.. math::

   C_{\mathrm{nondep}}^{\mathrm{inflated}}
   =
   C_{\mathrm{nondep}}
   \times
   f_{\mathrm{CI}}

Depreciable and total capital costs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The depreciable capital cost is defined as:

.. math::

   C_{\mathrm{depreciable}}
   =
   C_{\mathrm{direct}}
   +
   C_{\mathrm{indirect}}

The inflated depreciable capital cost is:

.. math::

   C_{\mathrm{depreciable}}^{\mathrm{inflated}}
   =
   C_{\mathrm{direct}}^{\mathrm{inflated}}
   +
   C_{\mathrm{indirect}}^{\mathrm{inflated}}

The total capital cost is:

.. math::

   C_{\mathrm{total}}
   =
   C_{\mathrm{depreciable}}
   +
   C_{\mathrm{nondep}}

The inflated total capital cost is:

.. math::

   C_{\mathrm{total}}^{\mathrm{inflated}}
   =
   C_{\mathrm{depreciable}}^{\mathrm{inflated}}
   +
   C_{\mathrm{nondep}}^{\mathrm{inflated}}


Notation
~~~~~~~~

.. list-table::
   :widths: 30 50 20
   :header-rows: 1

   * - Symbol
     - Description
     - Dimension

   * - :math:`C_{\mathrm{direct}}`
     - Total direct capital costs
     - currency

   * - :math:`C_{\mathrm{direct},i}`
     - Individual direct capital cost contribution
     - currency

   * - :math:`C_{\mathrm{direct}}^{\mathrm{inflated}}`
     - Inflated direct capital costs
     - currency

   * - :math:`C_{\mathrm{indirect}}`
     - Total indirect capital costs
     - currency

   * - :math:`C_{\mathrm{indirect},i}`
     - Individual indirect capital cost contribution
     - currency

   * - :math:`C_{\mathrm{indirect}}^{\mathrm{inflated}}`
     - Inflated indirect capital costs
     - currency

   * - :math:`c_{\mathrm{land}}`
     - Cost of land
     - currency / area

   * - :math:`A_{\mathrm{land}}`
     - Land required
     - area

   * - :math:`C_{\mathrm{land}}`
     - Total land cost
     - currency

   * - :math:`C_{\mathrm{other\_nondep}}`
     - Sum of other non-depreciable capital cost contributions
     - currency

   * - :math:`C_{\mathrm{other\_nondep},i}`
     - Individual other non-depreciable capital cost contribution
     - currency

   * - :math:`C_{\mathrm{nondep}}`
     - Total non-depreciable capital costs
     - currency

   * - :math:`C_{\mathrm{nondep}}^{\mathrm{inflated}}`
     - Inflated non-depreciable capital costs
     - currency

   * - :math:`C_{\mathrm{depreciable}}`
     - Total depreciable capital costs
     - currency

   * - :math:`C_{\mathrm{depreciable}}^{\mathrm{inflated}}`
     - Inflated depreciable capital costs
     - currency

   * - :math:`C_{\mathrm{total}}`
     - Total capital costs
     - currency

   * - :math:`C_{\mathrm{total}}^{\mathrm{inflated}}`
     - Inflated total capital costs
     - currency

   * - :math:`f_{\mathrm{combined}}`
     - Combined inflator
     - dimensionless

   * - :math:`f_{\mathrm{CI}}`
     - Capital inflator
     - dimensionless

Implementation
--------------

.. automodule:: pyH2A.Plugins.Capital_Cost_Plugin
    :members: