from pyH2A.Utilities.input_modification import insert, sum_all_tables, process_table
import logging

class FixedOperatingCostPlugin:
	'''Calculation of yearly fixed operating costs.

	Parameters
	----------
	Fixed Operating Costs > staff > Value : float
		Number of staff, ``process_table()`` is used.
	Fixed Operating Costs > hourly labor cost > Value : float
		Hourly labor cost of staff, ``process_table()`` is used.
	[...] Other Fixed Operating Cost [...] >> Value : float
		Yearly other fixed operating costs, ``sum_all_tables()`` is used.

	Returns
	-------
	[...] Other Fixed Operating Cost [...] > Summed Total > Value : float
		Summed total for each individual table in "Other Fixed Operating Cost" group.
	Fixed Operating Costs > Labor Cost - Uninflated > Value : float
		Yearly total labor cost.
	Fixed Operating Costs > Labor Cost > Value : float
		Yearly total labor cost multiplied by labor inflator.
	Fixed Operating Costs > Total > Value : float
		Sum of total yearly labor costs and yearly other fixed operating costs.
	'''


	def __init__(self, dcf, print_info):
		self.dcf = dcf

		self.logger = logging.getLogger("pyH2A.Plugins.Finance.FixedOperatingCostPlugin")
		self.logger.info("Starting FixedOperatingCostPlugin")

		table_keys = ['Fixed Operating Costs']
		self.process_table(table_keys)

		self.labor_cost()

		inserts = [
			('Fixed Operating Costs', 'Labor Cost - Uninflated', self.labor_uninflated),
			('Fixed Operating Costs', 'Labor Cost', self.labor)
		]
		self.insert_table(inserts, print_info)

		self.other_cost(print_info)

		inserts = [
			('Fixed Operating Costs', 'Total', self.labor + self.other)
		]
		self.insert_table(inserts, print_info)

	def process_table(self, table_keys):
		'''Processes input table.
		'''
		for table_key in table_keys:
			process_table(self.dcf.inp, table_key, 'Value')
		

	def labor_cost(self):
		'''Calculation of yearly labor costs by multiplying number of staff times hourly labor cost.'''

		process_table(self.dcf.inp, 'Fixed Operating Costs', 'Value')

		self.labor_uninflated = self.dcf.inp['Fixed Operating Costs']['staff']['Value'] * self.dcf.inp['Fixed Operating Costs']['hourly labor cost']['Value'] * 2080.
		self.labor = self.labor_uninflated * self.dcf.labor_inflator 
	
	def other_cost(self, print_info):
		'''Calculation of yearly other fixed operating costs by applying ``sum_all_tables()`` 
		to "Other Fixed Operating Cost" group.'''

		self.other = sum_all_tables(self.dcf.inp, 'Other Fixed Operating Cost', 'Value', insert_total = True, class_object = self.dcf, print_info = print_info) * self.dcf.combined_inflator

	def insert_table(self, inserts, print_info):
		'''Inserts the calculated values into the DCF.
		'''
		for key, subkey, value in inserts:
			insert(self.dcf, key, subkey, 'Value', value, __name__, print_info)
			self.logger.debug(f"{key} > {subkey} > Value: {value}")