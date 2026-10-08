'''Working example: net cash flow over time for the `PV_E_Base_test.md` case.

``Discounted_Cash_Flow_Plugin`` computes the cash flow of the plant for every year of the
analysis period and makes it available both as attributes of the plugin object and under
the `Cash Flow` table of ``Discounted_Cash_Flow.inp``. This example reads that data, plots
the net cash flow of each year together with the cumulative net cash flow and marks the
payback time (the point at which the cumulative net cash flow turns positive).

Run from the repository root with:

.. code-block:: bash

	python examples/net_cash_flow_PV_E_Base.py

The figure is saved to the `Example_Output` directory by default, a different output
directory can be provided as the first command line argument.

Notes
-----
`PV_E_Base_test.md` is the input file used by the end-to-end tests, its cash flow shows
three features which are worth keeping in mind when looking at the plot:

- The large outflow in the first year is the construction of the plant, which is financed
  in a single year in this input file (`Construction > Capital spent in 1st year of
  construction` is 100%).
- The outflow in year 10 of operation is the replacement of the electrolyzer stacks.
- The large outflow in the last year of operation combines the cost of the grid
  electricity required in that year, the repayment of the debt principal (constant debt
  financing repays the principal at the end of the plant life) and the decommissioning
  costs. The grid electricity dominates, because the test input file uses a deliberately
  extreme grid electricity price of 10,000 USD/kWh to make any grid electricity usage
  visible in the tests, and the declining photovoltaic output no longer covers the rising
  power demand of the electrolyzer in the final year.
'''

import sys
from pathlib import Path

import numpy as np

from pyH2A.Discounted_Cash_Flow import Discounted_Cash_Flow
from pyH2A.Utilities.output_utilities import Figure_Lean, millify

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = REPOSITORY_ROOT / 'src' / 'tests' / 'end_to_end' / 'PV_E_Base_test.md'
DEFAULT_OUTPUT_DIRECTORY = REPOSITORY_ROOT / 'Example_Output'

def read_cash_flow(dcf):
	'''Reading cash flow data from a ``Discounted_Cash_Flow`` object.

	Parameters
	----------
	dcf : Discounted_Cash_Flow
		Discounted cash flow object for which the analysis has been performed.

	Returns
	-------
	cash_flow : dict
		Dictionary containing the time axis (`years`, relative to the start of operation),
		the net cash flow of each year (`net`), the cumulative net cash flow (`cumulative`),
		the cumulative discounted net cash flow (`cumulative_discounted`) and the payback
		time (`payback_time`, counted from the first year of construction).

	Notes
	-----
	The same data is available as attributes of the plugin object, which avoids going
	through `dcf.inp`::

		plugin = dcf.plugs['Discounted_Cash_Flow_Plugin']
		plugin.annual_cash_flow.unit['USD']
		plugin.cumulative_cash_flow.unit['USD']
		plugin.payback_time.unit['year']
	'''

	cash_flow = dcf.inp['Cash Flow']

	return {'years': dcf.inp['Time']['Years']['Value']['Plant years relative'].unit['-'],
			'net': cash_flow['Annual']['Value'].unit['USD'],
			'cumulative': cash_flow['Cumulative']['Value'].unit['USD'],
			'cumulative_discounted': cash_flow['Cumulative discounted']['Value'].unit['USD'],
			'payback_time': cash_flow['Payback time']['Value'].unit['year']}

def net_cash_flow_plot(cash_flow, levelized_cost, directory, show = False):
	'''Plotting of net cash flow over time.

	Parameters
	----------
	cash_flow : dict
		Cash flow data as returned by :func:`read_cash_flow`.
	levelized_cost : Quantity
		Levelized cost of product, shown in the title of the plot.
	directory : str or Path
		Directory in which the figure is saved.
	show : bool, optional
		If True, the figure is shown.

	Returns
	-------
	figure : Figure_Lean
		``Figure_Lean`` object of the generated plot.

	Notes
	-----
	The upper panel shows the net cash flow of each individual year, the lower panel the
	cumulative net cash flow, which turns positive at the payback time. The cumulative
	discounted net cash flow is shown for comparison, it returns to zero at the end of the
	plant life, since the levelized cost of product is defined by this condition.
	'''

	figure = Figure_Lean(name = 'Net_Cash_Flow_Plot', directory = str(directory),
						 show = show, save = True, pdf = False,
						 nrows = 2, sharex = True,
						 left = 0.13, right = 0.97, top = 0.92, bottom = 0.11, hspace = 0.12,
						 fig_width = 7.5, fig_height = 6.0)

	ax_annual, ax_cumulative = figure.ax

	years = cash_flow['years']
	net = cash_flow['net']

	positive = np.where(net >= 0, net, 0.)
	negative = np.where(net < 0, net, 0.)

	ax_annual.bar(years, positive / 1e6, width = 0.7, color = 'darkseagreen', zorder = 3,
				  label = 'Net cash inflow')
	ax_annual.bar(years, negative / 1e6, width = 0.7, color = 'indianred', zorder = 3,
				  label = 'Net cash outflow')

	ax_cumulative.plot(years, cash_flow['cumulative'] / 1e6, color = 'darkblue',
					   marker = 'o', markersize = 3.5, zorder = 5,
					   label = 'Cumulative net cash flow')
	ax_cumulative.plot(years, cash_flow['cumulative_discounted'] / 1e6, color = 'darkorange',
					   linestyle = '--', zorder = 4,
					   label = 'Cumulative discounted net cash flow')

	# Payback time is counted from the first year of construction, while the x axis is
	# given relative to the start of operation.
	payback_time = cash_flow['payback_time']
	payback_position = years[0] + payback_time

	for ax in (ax_annual, ax_cumulative):
		ax.axhline(0, color = 'black', linewidth = 0.8, zorder = 2)
		ax.axvline(payback_position, color = 'grey', linestyle = ':', zorder = 2)
		ax.grid(axis = 'y', alpha = 0.3, zorder = 0)
		ax.set_ylabel('Cash flow / million USD')

	ax_annual.legend(loc = 'lower left', fontsize = 10)
	ax_cumulative.legend(loc = 'upper left', fontsize = 10)

	ax_annual.annotate(f'Payback time: {payback_time:.1f} years\n'
					   'after start of construction',
					   xy = (payback_position, 0),
					   xytext = (7, -25), textcoords = 'offset points',
					   va = 'top', ha = 'left', color = 'dimgrey', fontsize = 10)

	ax_cumulative.set_xlabel('Year relative to start of operation')
	ax_cumulative.set_xticks(years[::2])

	ax_annual.set_title('PV + electrolysis base case, levelized cost: '
						f'{levelized_cost.unit["USD/kg"]:.2f} USD per kg H$_2$')

	figure.execute()

	return figure

def main(output_directory = DEFAULT_OUTPUT_DIRECTORY, show = False):
	'''Running the discounted cash flow analysis and plotting the net cash flow.
	'''

	dcf = Discounted_Cash_Flow(str(INPUT_FILE), print_info = False)

	levelized_cost = dcf.inp['Dependent Variables']['Levelized cost']['Value']
	cash_flow = read_cash_flow(dcf)

	print(f'Levelized cost of hydrogen: {levelized_cost}')
	print(f'Payback time: {cash_flow["payback_time"]:.2f} years '
		  '(counted from the first year of construction)')
	print(f'Cumulative net cash flow at the end of the plant life: '
		  f'{millify(cash_flow["cumulative"][-1])}')
	print(f'Cumulative discounted net cash flow at the end of the plant life: '
		  f'{millify(cash_flow["cumulative_discounted"][-1])} '
		  '(zero by definition of the levelized cost)')

	output_directory = Path(output_directory)
	output_directory.mkdir(parents = True, exist_ok = True)

	net_cash_flow_plot(cash_flow, levelized_cost, output_directory, show = show)

	print(f'Plot saved to: {output_directory / "Net_Cash_Flow_Plot.png"}')

	return dcf

if __name__ == '__main__':
	if len(sys.argv) > 1:
		main(output_directory = sys.argv[1])
	else:
		main()
