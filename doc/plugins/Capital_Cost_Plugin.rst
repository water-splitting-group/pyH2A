Capital_Cost_Plugin
===================

This plugin computes the different components of capital costs based on grouped cost entries and applies inflation factors.

Equations
~~~~~~~~~

Direct capital costs:

.. math::

   C_{\text{direct}} = \sum_i C_{\text{direct},i}

.. math::

   C_{\text{direct}}^{\text{infl}} = C_{\text{direct}} \cdot f_{\text{infl,combined}}


Indirect capital costs:

.. math::

   C_{\text{indirect}} = \sum_j C_{\text{indirect},j}

.. math::

   C_{\text{indirect}}^{\text{infl}} = C_{\text{indirect}} \cdot f_{\text{infl,combined}}


Depreciable capital costs:

.. math::

   C_{\text{depr}} = C_{\text{direct}} + C_{\text{indirect}}

.. math::

   C_{\text{depr}}^{\text{infl}} = C_{\text{direct}}^{\text{infl}} + C_{\text{indirect}}^{\text{infl}}


Non-depreciable capital costs:

.. math::

   C_{\text{land}} = c_{\text{land}} \cdot A_{\text{land}}

.. math::

   C_{\text{non-depr}} = C_{\text{land}} + \sum_k C_{\text{other non-depr},k}

.. math::

   C_{\text{non-depr}}^{\text{infl}} = C_{\text{non-depr}} \cdot f_{\text{infl,CI}}


Total capital costs:

.. math::

   C_{\text{total}} = C_{\text{depr}} + C_{\text{non-depr}}

.. math::

   C_{\text{total}}^{\text{infl}} = C_{\text{depr}}^{\text{infl}} + C_{\text{non-depr}}^{\text{infl}}


Notation
~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Symbol
     - Description
     - Dimension

   * - :math:`C_{\text{direct}}`
     - Total direct capital costs
     - Currency

   * - :math:`C_{\text{direct},i}`
     - Individual direct capital cost entries (from "Direct Capital Cost" tables)
     - Currency

   * - :math:`C_{\text{indirect}}`
     - Total indirect capital costs
     - Currency

   * - :math:`C_{\text{indirect},j}`
     - Individual indirect capital cost entries (from "Indirect Capital Cost" tables)
     - Currency

   * - :math:`C_{\text{depr}}`
     - Total depreciable capital costs (direct + indirect)
     - Currency

   * - :math:`C_{\text{non-depr}}`
     - Total non-depreciable capital costs
     - Currency

   * - :math:`C_{\text{other non-depr},k}`
     - Individual non-depreciable cost entries (excluding land)
     - Currency

   * - :math:`C_{\text{land}}`
     - Total land cost
     - Currency

   * - :math:`c_{\text{land}}`
     - Cost of land per area  
       (``Non-Depreciable Capital Costs > Cost of land ($ per acre) > Value``)
     - Currency / area

   * - :math:`A_{\text{land}}`
     - Land required  
       (``Non-Depreciable Capital Costs > Land required (acres) > Value``)
     - Area

   * - :math:`C_{\text{total}}`
     - Total capital costs
     - Currency

   * - :math:`f_{\text{infl,combined}}`
     - Combined inflation factor (``dcf.combined_inflator``)
     - Dimensionless

   * - :math:`f_{\text{infl,CI}}`
     - Capital investment inflation factor (``dcf.ci_inflator``)
     - Dimensionless

   * - Superscript :math:`\text{infl}`
     - Indicates inflated value
     - 


Implementation
--------------

.. automodule:: pyH2A.Plugins.Capital_Cost_Plugin
    :members: