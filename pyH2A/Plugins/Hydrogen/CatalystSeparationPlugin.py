from pyH2A.Plugins.Plugin import Plugin
from pyH2A.DiscountedCashFlow import DiscountedCashFlow
import logging


class CatalystSeparationPlugin(Plugin):
	'''Calculation of cost for catalyst separation (e.g. via nanofiltration).

	Parameters
	----------
	Water Volume > Volume (liters) > Value : float
		Total water volume in liters.
	Catalyst > Lifetime (years) > Value : float
		Lifetime of catalysts in year before replacement is required.
	Catalyst Separation > Filtration cost ($/m3) > Value : float
		Cost of filtration in $ per m3.

	Returns
	-------
	Other Variable Operating Cost - Catalyst Separation > Catalyst Separation (yearly cost) > Value : float
		Yearly cost of catalyst seperation.
	'''

	def __init__(
			self, 
			dcf: DiscountedCashFlow
			) -> None:
		super().__init__(dcf)

		self.logger: logging.Logger = logging.getLogger("pyH2A.Plugins.Hydrogen.CatalystSeparationPlugin")
		self.logger.info("Starting CatalystSeparationPlugin")

		table_keys = ['Water Volume', 'Catalyst Separation']
		self.process_table(table_keys)
		self.run_plugin()
		self.insert_table()


	def run_plugin(
			self
			) -> None:
		tea = CatalystSeparationPluginTEA(self)
		tea.calculate_yearly_filtration_volume()
		tea.calculate_filtration_cost()


class CatalystSeparationPluginTEA:
	'''Handles life-cycle assessment (LCA) calculations for the catalyst separation plugin.
	'''
	def __init__(
			self,
			plugin: CatalystSeparationPlugin
			) -> None:
		self.plugin: CatalystSeparationPlugin = plugin

	def calculate_yearly_filtration_volume(
			self
			) -> None:
		'''Calculation of water volume that has to be filtered per year.
		'''

		fraction_to_be_filtered_yearly = 1./self.plugin.dcf.inp['Catalyst']['Lifetime (years)']['Value']

		yearly_filtration_volume_liters = self.plugin.dcf.inp['Water Volume']['Volume (liters)']['Value'] * fraction_to_be_filtered_yearly
		self.yearly_filtration_volume_m3 = yearly_filtration_volume_liters/1000.

	def calculate_filtration_cost(
			self
			) -> None:
		'''Yearly cost of water filtration to remove catalyst.
		'''

		yearly_cost = self.yearly_filtration_volume_m3 * self.plugin.dcf.inp['Catalyst Separation']['Filtration cost ($/m3)']['Value']
		self.plugin.insert_queue.append(
			('Other Variable Operating Cost - Catalyst Separation', 'Catalyst Separation (yearly cost)', yearly_cost)
		)


class CatalystSeparationPluginLCA:

    def __init__(
            self, 
            plugin: CatalystSeparationPlugin
            ) -> None:
        self.plugin: CatalystSeparationPlugin = plugin