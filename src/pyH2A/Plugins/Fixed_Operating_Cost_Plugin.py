from pyH2A.Utilities.input_modification import insert, sum_all_tables, process_table
import re

fixed_operating_cost_input_dict = {
    'staff': {
        'top_level': 'Fixed Operating Costs',
        'mid_level': 'staff',
        'lower_level': 'Value',
        'unit_key': 'unit',
    },
    'hourly_labor_cost': {
        'top_level': 'Fixed Operating Costs',
        'mid_level': 'hourly labor cost',
        'lower_level': 'Value',
        'unit_key': 'unit',
    },
    'other_fixed_operating_costs': {
        'top_level': '[...] Other Fixed Operating Cost [...]',
        'mid_level': 'Repeatable rows',
        'lower_level': 'Value',
        'unit_key': 'unit',
    },
}

fixed_operating_cost_output_dict = {
    'other_fixed_operating_cost_total': {
        'top_level': '[...] Other Fixed Operating Cost [...]',
        'mid_level': 'Summed Total',
        'lower_level': 'Value',
        'unit_key': 'unit',
    },
    'labor_cost_uninflated': {
        'top_level': 'Fixed Operating Costs',
        'mid_level': 'Labor Cost - Uninflated',
        'lower_level': 'Value',
        'unit_key': 'unit',
    },
    'labor_cost_inflated': {
        'top_level': 'Fixed Operating Costs',
        'mid_level': 'Labor Cost',
        'lower_level': 'Value',
        'unit_key': 'unit',
    },
    'fixed_operating_cost_total': {
        'top_level': 'Fixed Operating Costs',
        'mid_level': 'Total',
        'lower_level': 'Value',
        'unit_key': 'unit',
    },
}

def resolve_top_levels(inp, pattern):
	core = pattern.replace('[...]', '').strip()
	return [k for k in inp if core in k]

def input_resolver(input_dict, dcf):
	"""
    Resolve inputs from dcf.inp using an I/O specification dictionary.
    (Value-only; unit handling is out of scope.)
    """
	resolved = {}

	for name, spec in input_dict.items():
		top_pattern = spec['top_level']
		mid = spec['mid_level']
		low = spec['lower_level']

		tops = resolve_top_levels(dcf.inp, top_pattern)
		collected = {}

		for top in tops:
			process_table(dcf.inp, top, low)

			if mid.lower().startswith('repeatable'):
				values = []
				for row in dcf.inp[top].values():
					if isinstance(row, dict) and low in row:
						values.append(row[low])
				collected[top] = values
			else:
				collected[top] = dcf.inp[top][mid][low]

		if len(collected) == 1:
			resolved[name] = list(collected.values())[0]
		else:
			resolved[name] = collected

	return resolved

def output_resolver(output_dict, values, dcf, print_info=True):
    for name, spec in output_dict.items():
        top_pattern = spec['top_level']
        mid = spec['mid_level']
        low = spec['lower_level']

        # Handle '[...]' tables
        if '[...]' in top_pattern:
            if isinstance(values[name], dict):
                for top, val in values[name].items():
                    insert(
                        dcf,
                        top,
                        mid,
                        low,
                        val,
                        __name__,
                        print_info=print_info
                    )
            else:
                # fallback: find matching table(s) in dcf.inp
                for top_key in dcf.inp.keys():
                    if re.search(top_pattern.replace('[...]', '.*'), top_key):
                        insert(
                            dcf,
                            top_key,
                            mid,
                            low,
                            values[name],
                            __name__,
                            print_info=print_info
                        )
        else:
            insert(
                dcf,
                top_pattern,
                mid,
                low,
                values[name],
                __name__,
                print_info=print_info
            )

class Fixed_Operating_Cost_Plugin:
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
		self.labor_cost(dcf)
		insert(dcf, 'Fixed Operating Costs', 'Labor Cost - Uninflated', 'Value', self.labor_uninflated, __name__, print_info = print_info)
		insert(dcf, 'Fixed Operating Costs', 'Labor Cost', 'Value', self.labor, __name__, print_info = print_info)

		self.other_cost(dcf, print_info)
		insert(dcf, 'Fixed Operating Costs', 'Total', 'Value', self.labor + self.other, __name__, print_info = print_info)

	def labor_cost(self, dcf):
		'''Calculation of yearly labor costs by multiplying number of staff times hourly labor cost.'''

		process_table(dcf.inp, 'Fixed Operating Costs', 'Value')

		self.labor_uninflated = dcf.inp['Fixed Operating Costs']['staff']['Value'] * dcf.inp['Fixed Operating Costs']['hourly labor cost']['Value'] * 2080.
		self.labor = self.labor_uninflated * dcf.labor_inflator 
	
	def other_cost(self, dcf, print_info):
		'''Calculation of yearly other fixed operating costs by applying ``sum_all_tables()`` 
		to "Other Fixed Operating Cost" group.'''

		self.other = sum_all_tables(dcf.inp, 'Other Fixed Operating Cost', 'Value', insert_total = True, class_object = dcf, print_info = print_info) * dcf.combined_inflator

