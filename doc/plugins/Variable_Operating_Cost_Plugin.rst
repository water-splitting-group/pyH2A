Variable_Operating_Cost_Plugin
==============================

This plugin computes variable operating costs, including utility costs (time-dependent) and other variable costs.
The result is expressed as a time-dependent quantity (array over plant lifetime).

Equations
---------

Utility costs
~~~~~~~~~~~~~

For each utility :math:`i`, the cost per functional unit is calculated as:

.. math::

   C_{\mathrm{util},i}^{\mathrm{FU}}
   =
   P_i
   \times
   U_i
   \times
   F_{\mathrm{conv},i}
   \times
   f_{\mathrm{inflation}}

where the utility price may be either:

- A scalar value,
- A yearly array,
- Or a time-dependent value read from an external text file.

The total utility operating cost is then:

.. math::

   C_{\mathrm{utilities}}
   =
   Q_{\mathrm{year}}
   \times
   \sum_i
   C_{\mathrm{util},i}^{\mathrm{FU}}

Other variable operating costs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Other variable operating cost contributions are summed across all tables belonging to the
``Other Variable Operating Cost`` group:

.. math::

   C_{\mathrm{other}}
   =
   f_{\mathrm{chem}}
   \times
   \sum_j
   C_{\mathrm{other},j}

Total variable operating costs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The total variable operating cost is:

.. math::

   C_{\mathrm{var,total}}
   =
   C_{\mathrm{utilities}}
   +
   C_{\mathrm{other}}

Notation
~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 50 50

   * - Symbol
     - Description
     - Dimension

   * - :math:`P_i`
     - Utility cost for utility :math:`i`
     - Currency

   * - :math:`U_i`
     - Utility usage per functional unit for utility :math:`i`
     - 1 / Functional unit dimension

   * - :math:`F_{\mathrm{conv},i}`
     - Price conversion factor for utility :math:`i`
     - Dimensionless

   * - :math:`f_{\mathrm{inflation}}`
     - Inflation correction factor
     - Dimensionless

   * - :math:`C_{\mathrm{util},i}^{\mathrm{FU}}`
     - Inflation-corrected utility cost per functional unit
     - currency / Functional unit dimension

   * - :math:`Q_{\mathrm{year}}`
     - Output per year
     - Functional unit dimension

   * - :math:`C_{\mathrm{utilities}}`
     - Total utility operating costs
     - Currency

   * - :math:`C_{\mathrm{other},j}`
     - Individual other variable operating cost contribution
     - Currency

   * - :math:`f_{\mathrm{chem}}`
     - Chemical inflator
     - Dimensionless

   * - :math:`C_{\mathrm{other}}`
     - Total other variable operating costs
     - Currency

   * - :math:`C_{\mathrm{var,total}}`
     - Total variable operating costs
     - Currency

Notes
-----

- Utility costs are evaluated **per functional unit**, then scaled by annual delivered units.
- Costs can be:
  - constant (scalar),
  - time-dependent (array),
  - or read from external files.
- Inflation correction is applied at the **unit cost level**.
- Other variable operating costs are aggregated using ``sum_all_tables()`` and scaled by the chemical inflator.

Implementation
--------------

.. automodule:: pyH2A.Plugins.Variable_Operating_Cost_Plugin
    :members: