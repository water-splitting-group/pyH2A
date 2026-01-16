from pyH2A.Utilities.input_modification import insert, sum_all_tables, process_table

fixed_operating_cost_input_dict = {
    'staff': {
        'top_level': 'Fixed Operating Costs',
        'mid_level': 'staff',
        'lower_level': 'Value',
        'dimension': ''
    },
    'hourly_labor_cost': {
        'top_level': 'Fixed Operating Costs',
        'mid_level': 'hourly labor cost',
        'lower_level': 'Value',
        'dimension': ''
    },
    'other_fixed_operating_costs': {
        'top_level': '<...> Other Fixed Operating Cost <...>',
        'mid_level': '<...>',
        'lower_level': 'Value',
        'dimension': ''
    },
}

fixed_operating_cost_output_dict = {
    'other_fixed_operating_cost_total': {
        'top_level': '<...> Other Fixed Operating Cost <...>',
        'mid_level': 'Summed Total',
        'lower_level': 'Value',
        'dimension': ''
    },
    'labor_cost_uninflated': {
        'top_level': 'Fixed Operating Costs',
        'mid_level': 'Labor Cost - Uninflated',
        'lower_level': 'Value',
        'dimension': ''
    },
    'labor_cost_inflated': {
        'top_level': 'Fixed Operating Costs',
        'mid_level': 'Labor Cost',
        'lower_level': 'Value',
        'dimension': ''
    },
    'fixed_operating_cost_total': {
        'top_level': 'Fixed Operating Costs',
        'mid_level': 'Total',
        'lower_level': 'Value',
        'dimension': ''
    },
}

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

