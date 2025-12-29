from pyH2A.Utilities.input_modification import insert, sum_all_tables, process_table

capital_cost_input_dict = {
	'direct_capital_costs': {
		'top_level': 'Direct Capital Cost',
		'mid_level': 'Repeatable rows',
		'lower_level': 'Value',
		'unit_key': 'unit',
	},
	'indirect_capital_costs': {
		'top_level': 'Indirect Capital Cost',
		'mid_level': 'Repeatable rows',
		'lower_level': 'Value',
		'unit_key': 'unit',
	},
	'land_cost_per_acre': {
		'top_level': 'Non-Depreciable Capital Costs',
		'mid_level': 'Cost of land ($ per acre)',
		'lower_level': 'Value',
		'unit_key': 'unit',
	},
	'land_required': {
		'top_level': 'Non-Depreciable Capital Costs',
		'mid_level': 'Land required (acres)',
		'lower_level': 'Value',
		'unit_key': 'unit',
	},
	'other_non_depreciable_capital_costs': {
		'top_level': 'Other Non-Depreciable Capital Cost',
		'mid_level': 'Repeatable rows',
		'lower_level': 'Value',
		'unit_key': 'unit',
	},
}

capital_cost_output_dict = {
	'direct_capital_total': {
		'top_level': 'Direct Capital Costs',
		'mid_level': 'Total',
		'lower_level': 'Value',
		'unit_key': 'unit',
	},
	'direct_capital_inflated': {
		'top_level': 'Direct Capital Costs',
		'mid_level': 'Inflated',
		'lower_level': 'Value',
		'unit_key': 'unit',
	},
	'indirect_capital_total': {
		'top_level': 'Indirect Capital Costs',
		'mid_level': 'Total',
		'lower_level': 'Value',
		'unit_key': 'unit',
	},
	'indirect_capital_inflated': {
		'top_level': 'Indirect Capital Costs',
		'mid_level': 'Inflated',
		'lower_level': 'Value',
		'unit_key': 'unit',
	},
	'depreciable_capital_total': {
		'top_level': 'Depreciable Capital Costs',
		'mid_level': 'Total',
		'lower_level': 'Value',
		'unit_key': 'unit',
	},
	'depreciable_capital_inflated': {
		'top_level': 'Depreciable Capital Costs',
		'mid_level': 'Inflated',
		'lower_level': 'Value',
		'unit_key': 'unit',
	},
	'non_depreciable_capital_total': {
		'top_level': 'Non-Depreciable Capital Costs',
		'mid_level': 'Total',
		'lower_level': 'Value',
		'unit_key': 'unit',
	},
	'non_depreciable_capital_inflated': {
		'top_level': 'Non-Depreciable Capital Costs',
		'mid_level': 'Inflated',
		'lower_level': 'Value',
		'unit_key': 'unit',
	},
	'total_capital_cost_total': {
		'top_level': 'Total Capital Costs',
		'mid_level': 'Total',
		'lower_level': 'Value',
		'unit_key': 'unit',
	},
	'total_capital_cost_inflated': {
		'top_level': 'Total Capital Costs',
		'mid_level': 'Inflated',
		'lower_level': 'Value',
		'unit_key': 'unit',
	},
}

from pyH2A.Utilities.input_modification import process_table, insert


def input_resolver(input_dict, dcf):
	"""
	Resolve inputs from dcf.inp using an I/O specification dictionary.
	Supports both single-row and repeatable-row inputs.
	(Value-only; unit handling is out of scope.)
	"""
	resolved = {}

	for name, spec in input_dict.items():
		top = spec['top_level']
		mid = spec['mid_level']
		low = spec['lower_level']

		process_table(dcf.inp, top, low)

		if mid.lower().startswith('repeatable'):
			values = []
			for row in dcf.inp[top].values():
				if isinstance(row, dict) and low in row:
					values.append(row[low])
			resolved[name] = values
		else:
			resolved[name] = dcf.inp[top][mid][low]

	return resolved

def output_resolver(output_dict, values, dcf, print_info):
	"""
	Insert outputs back into dcf.inp using output specification dictionary.
	"""
	for name, spec in output_dict.items():
		top = spec['top_level']
		mid = spec['mid_level']
		low = spec['lower_level']
		unit = spec.get('unit_key')

		insert(
			dcf,
			top,
			mid,
			low,
			values[name],
			__name__,
			print_info=print_info
		)

		if unit is not None:
			insert(
				dcf,
				top,
				mid,
				unit,
				unit,
				__name__,
				print_info=print_info
			)

class Capital_Cost_Plugin:
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
	['Capital_Cost_Plugin'].direct_contributions : dict
		Attribute containing cost contributions for "Direct Capital Cost" group.
	'''
	def __init__(self, dcf, print_info):

		self.direct_capital_costs(dcf, print_info)  
		direct_inflated = self.direct * dcf.combined_inflator

		insert(dcf, 'Direct Capital Costs', 'Total', 'Value', self.direct, __name__, print_info = print_info)
		insert(dcf, 'Direct Capital Costs', 'Inflated', 'Value', direct_inflated, __name__, print_info = print_info)

		self.indirect_capital_costs(dcf, print_info)

		indirect_inflated = self.indirect * dcf.combined_inflator
		depreciable = self.direct + self.indirect
		depreciable_inflated = direct_inflated + indirect_inflated
		
		insert(dcf, 'Indirect Capital Costs', 'Total', 'Value', self.indirect, __name__, print_info = print_info)
		insert(dcf, 'Indirect Capital Costs', 'Inflated', 'Value', indirect_inflated, __name__, print_info = print_info)
		
		insert(dcf, 'Depreciable Capital Costs', 'Total', 'Value', depreciable, __name__, print_info = print_info)
		insert(dcf, 'Depreciable Capital Costs', 'Inflated', 'Value', depreciable_inflated, __name__, print_info = print_info)
		
		self.non_depreciable_capital_costs(dcf, print_info)

		non_depreciable_inflated = self.non_depreciable * dcf.ci_inflator
		total = depreciable + self.non_depreciable
		total_inflated = depreciable_inflated + non_depreciable_inflated

		insert(dcf, 'Non-Depreciable Capital Costs', 'Total', 'Value', self.non_depreciable, __name__, print_info = print_info)
		insert(dcf, 'Non-Depreciable Capital Costs', 'Inflated', 'Value', non_depreciable_inflated, __name__, print_info = print_info)
		
		insert(dcf, 'Total Capital Costs', 'Total', 'Value', total, __name__, print_info = print_info)
		insert(dcf, 'Total Capital Costs', 'Inflated', 'Value', total_inflated, __name__, print_info = print_info)

	def direct_capital_costs(self, dcf, print_info):
		'''Calculation of direct capital costs by applying ``sum_all_tables()`` to "Direct Capital Cost" group.'''

		self.direct, self.direct_contributions = sum_all_tables(dcf.inp, 'Direct Capital Cost', 'Value', insert_total = True, 
																class_object = dcf, print_info = print_info, 
																return_contributions = True)

	def indirect_capital_costs(self, dcf, print_info):
		'''Calculation of indirect capital costs by applying ``sum_all_tables()`` to "Indirect Capital Cost" group.'''

		self.indirect = sum_all_tables(dcf.inp, 'Indirect Capital Cost', 'Value', insert_total = True, 
									   class_object = dcf, print_info = print_info)

	def non_depreciable_capital_costs(self, dcf, print_info):
		'''Calculation of non-depreciable capital costs by calculating cost of land and applying
		``sum_all_tables()`` to "Other Non-Depreciable Capital Cost" group.
		'''

		process_table(dcf.inp, 'Non-Depreciable Capital Costs', 'Value')

		non_depreciable = dcf.inp['Non-Depreciable Capital Costs']
		self.non_depreciable = non_depreciable['Cost of land ($ per acre)']['Value'] * non_depreciable['Land required (acres)']['Value']
		self.non_depreciable += sum_all_tables(dcf.inp, 'Other Non-Depreciable Capital Cost', 'Value', insert_total = True, class_object = dcf, print_info = print_info)

