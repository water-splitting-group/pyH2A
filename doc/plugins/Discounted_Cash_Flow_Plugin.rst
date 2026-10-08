Discounted_Cash_Flow_Plugin
===========================

The ``Discounted_Cash_Flow_Plugin`` combines the capital costs, replacement costs, fixed and variable operating costs, debt financing, depreciation, taxes and revenues provided by the upstream plugins into a full discounted cash flow analysis, following the H2A methodology. Its main result is the levelized cost of product, which is defined as the product price at which the net present value of the after-tax, post-depreciation cash flow is zero.

Cash flow over time
-------------------

In addition to the levelized cost of product, the plugin makes the cash flow of every year of the analysis period available. All cash flow arrays cover the construction years followed by the operation years, so they share their time axis with ``Time > Years > Value > Plant years relative``.

The data is inserted into the input dictionary under the ``Cash Flow`` table:

.. list-table::
   :widths: 35 65
   :header-rows: 1

   * - Path
     - Description
   * - ``Cash Flow > Annual pre-tax > Value``
     - Pre-tax cash flow of each year.
   * - ``Cash Flow > Annual > Value``
     - Net (after-tax, post-depreciation) cash flow of each year.
   * - ``Cash Flow > Cumulative > Value``
     - Cumulative net cash flow, turning positive at the payback time.
   * - ``Cash Flow > Annual discounted > Value``
     - Net cash flow of each year, discounted to the beginning of the analysis period using the after-tax nominal IRR.
   * - ``Cash Flow > Cumulative discounted > Value``
     - Cumulative discounted net cash flow, returning to zero at the end of the plant life.
   * - ``Cash Flow > Payback time > Value``
     - Time from the first year of construction until the cumulative net cash flow turns positive.

The same values are available as attributes of the plugin object (``annual_cash_flow``, ``cumulative_cash_flow``, ``annual_discounted_cash_flow``, ``cumulative_discounted_cash_flow``, ``pre_tax_cash_flow`` and ``payback_time``):

.. code-block:: python

   from pyH2A.Discounted_Cash_Flow import Discounted_Cash_Flow

   dcf = Discounted_Cash_Flow('PV_E_Base_test.md', print_info = False)

   years = dcf.inp['Time']['Years']['Value']['Plant years relative'].unit['-']
   net_cash_flow = dcf.inp['Cash Flow']['Annual']['Value'].unit['USD']
   cumulative_cash_flow = dcf.inp['Cash Flow']['Cumulative']['Value'].unit['USD']
   payback_time = dcf.inp['Cash Flow']['Payback time']['Value'].unit['year']

   # identical values, read directly from the plugin object
   plugin = dcf.plugs['Discounted_Cash_Flow_Plugin']
   plugin.annual_cash_flow.unit['USD']
   plugin.cumulative_cash_flow.unit['USD']
   plugin.payback_time.unit['year']

A complete example, plotting the net cash flow over time for the PV + electrolysis base case, is provided in ``examples/net_cash_flow_PV_E_Base.py``.

Payback time
------------

The payback time is obtained from the cumulative *net* (undiscounted) cash flow, by linear interpolation between the last negative and the first non-negative entry. It is counted from the first year of construction, i.e. from the first entry of the cash flow arrays. ``nan`` is returned if the cumulative net cash flow never turns positive.

The cumulative *discounted* cash flow is not suited for this purpose: it returns to zero at the end of the plant life by construction, since this is the condition defining the levelized cost of product.

.. automodule:: pyH2A.Plugins.Discounted_Cash_Flow_Plugin
    :members:
