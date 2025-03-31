from pyH2A.DiscountedCashFlow import DiscountedCashFlow
from pyH2A.Plugins.Plugin import Plugin
from pyH2A.Utilities.input_modification import sum_all_tables
import logging


class CapitalCostPlugin(Plugin):
	'''
	Parameters
	----------
	[...] Direct Capital Cost [...] >> Value : float
		``sum_all_tables()`` is used.
	[...] Indirect Capital Cost [...] >> Value : float
		``sum_all_tables()`` is used.
	Non-Depreciable Capital Costs > Cost of land ($ per acre) > Value : float
		Cost of land in $ per acre, ``process_table()`` is used.
	Non-Depreciable Capital Costs > Land required (acres) > Value : float
		Total land are required in acres, ``process_table()`` is used.
	[...] Other Non-Depreciable Capital Cost [...] >> Value : float
		``sum_all_tables()`` is used.

	Returns
	-------
	[...] Direct Capital Cost [...] > Summed Total > Value : float
		Summed total for each individual table in "Direct Capital Cost" group.
	[...] Indirect Capital Cost [...] > Summed Total > Value : float
		Summed total for each individual table in "Indirect Capital Cost" group.
	[...] Other Non-Depreciable Capital Cost  [...] > Summed Total > Value : float
		Summed total for each individual table in "Other Non-Depreciable Capital Cost" group.
	Direct Capital Costs > Total > Value : float
		Total direct capital costs.
	Direct Capital Costs > Inflated > Value : float
		Total direct capital costs multiplied by combined inflator.
	Indirect Capital Costs > Total > Value : float
		Total indirect capital costs.
	Indirect Capital Costs > Inflated > Value : float
		Total indirect capital costs multiplied by combined inflator.
	Non-Depreciable Capital Costs > Total > Value : float
		Total non-depreciable capital costs.
	Non-Depreciable Capital Costs > Inflated > Value : float
		Total non-depreciable capital costs multiplied by combined inflator.
	Depreciable Capital Costs > Total > Value : float
		Sum of direct and indirect capital costs.
	Depreciable Capital Costs > Inflated > Value : float
		Sum of direct and indirect capital costs multiplied by combined inflator.
	Total Capital Costs > Total > Value : float
		Sum of depreciable and non-depreciable capital costs.
	Total Capital Costs > Inflated > Value : float
		Sum of depreicable and non-depreciable capital costs multiplied by combined inflator.
	['Finance.CapitalCostPlugin'].direct_contributions : dict
		Attribute containing cost contributions for "Direct Capital Cost" group.
	'''
	def __init__(
			self, 
			dcf: DiscountedCashFlow
			) -> None:

		super().__init__(dcf)

		self.logger = logging.getLogger("pyH2A.Plugins.Finance.CapitalCostPlugin")
		self.logger.info("Starting CapitalCostPlugin")

		table_keys = ['Non-Depreciable Capital Costs']
		self.process_table(table_keys)
		self.run_plugin()
		self.insert_table()

	def run_plugin(
			self
			) -> None:
		
		tea = CapitalCostPluginTEA(self)

		tea.direct_capital_costs()  
		self.insert_table()

		tea.indirect_capital_costs()
		tea.non_depreciable_capital_costs()
		tea.total_cost()


class CapitalCostPluginTEA:
	'''Handles life-cycle assessment (LCA) calculations for the capital cost plugin.
	'''
	def __init__(
			self,
			plugin: CapitalCostPlugin
			) -> None:
		self.plugin: CapitalCostPlugin = plugin		

	def direct_capital_costs(
			self
			) -> None:
		'''Calculation of direct capital costs by applying ``sum_all_tables()`` to "Direct Capital Cost" group.
		'''
		(self.direct, 
   		 self.direct_contributions) = sum_all_tables(self.plugin.dcf.inp, 'Direct Capital Cost', 'Value',
												  insert_total = True, class_object = self.plugin.dcf, 
												  print_info = self.plugin.dcf.print_info, return_contributions = True
												)
		self.direct_inflated = self.direct * self.plugin.dcf.combined_inflator
		self.plugin.insert_queue.extend([
			('Direct Capital Costs', 'Total', self.direct),
			('Direct Capital Costs', 'Inflated', self.direct_inflated)
		])

	def indirect_capital_costs(self):
		'''Calculation of indirect capital costs by applying ``sum_all_tables()`` to "Indirect Capital Cost" group.'''
		self.indirect = sum_all_tables(self.plugin.dcf.inp, 'Indirect Capital Cost', 'Value', insert_total = True, 
									   class_object = self.plugin.dcf, print_info = self.plugin.dcf.print_info)
		indirect_inflated = self.indirect * self.plugin.dcf.combined_inflator
		self.depreciable = self.direct + self.indirect
		self.depreciable_inflated = self.direct_inflated + indirect_inflated
		self.plugin.insert_queue.extend([
			('Indirect Capital Costs', 'Inflated', indirect_inflated),
			('Depreciable Capital Costs', 'Total', self.depreciable),
			('Depreciable Capital Costs', 'Inflated', self.depreciable_inflated)
		])

	def non_depreciable_capital_costs(
			self
			) -> None:
		'''Calculation of non-depreciable capital costs by calculating cost of land and applying
		``sum_all_tables()`` to "Other Non-Depreciable Capital Cost" group.
		'''
		non_depreciable = self.plugin.dcf.inp['Non-Depreciable Capital Costs']
		self.non_depreciable = non_depreciable['Cost of land ($ per acre)']['Value'] * non_depreciable['Land required (acres)']['Value']
		self.non_depreciable += sum_all_tables(self.plugin.dcf.inp, 'Other Non-Depreciable Capital Cost', 'Value', 
									insert_total = True, class_object = self.plugin.dcf, print_info = self.plugin.dcf.print_info)
		self.non_depreciable_inflated = self.non_depreciable * self.plugin.dcf.ci_inflator

		self.plugin.insert_queue.extend([
			('Non-Depreciable Capital Costs', 'Total', self.non_depreciable),
			('Non-Depreciable Capital Costs', 'Inflated', self.non_depreciable_inflated),
		])

	def total_cost(
			self
			) -> None:
		total = self.depreciable + self.non_depreciable
		total_inflated = self.depreciable_inflated + self.non_depreciable_inflated

		self.plugin.insert_queue.extend([
			('Total Capital Costs', 'Total', total),
			('Total Capital Costs', 'Inflated', total_inflated)
		])
