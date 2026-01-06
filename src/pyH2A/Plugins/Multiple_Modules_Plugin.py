import numpy as np
from pyH2A.Utilities.input_modification import insert, process_table
import re

multiple_modules_input_dict = {
    'plant_modules': {
        'top_level': 'Technical Operating Parameters and Specifications',
        'mid_level': 'Plant Modules',
        'lower_level': 'Value',
    },
    'solar_collection_area': {
        'top_level': 'Non-Depreciable Capital Costs',
        'mid_level': 'Solar Collection Area (m2)',
        'lower_level': 'Value',
    },
    'area_per_staff': {
        'top_level': 'Fixed Operating Costs',
        'mid_level': 'area',
        'lower_level': 'Value',
    },
    'shifts': {
        'top_level': 'Fixed Operating Costs',
        'mid_level': 'shifts',
        'lower_level': 'Value',
    },
    'supervisors': {
        'top_level': 'Fixed Operating Costs',
        'mid_level': 'supervisor',
        'lower_level': 'Value',
    },
}

multiple_modules_output_dict = {
    'staff_per_module': {
        'top_level': 'Fixed Operating Costs',
        'mid_level': 'staff',
        'lower_level': 'Value',
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

class Multiple_Modules_Plugin:
	''' Simulating mutliple plant modules which are operated together, assuming that only labor cost is reduced. 
	Calculation of required labor to operate all modules, scaling down labor requirement to one module for subsequent calculations.

	Parameters
	----------
	Technical Operating Parameters and Specifications > Plant Modules > Value : float or int
		Number of plant modules considered in this calculation, ``process_table()`` is used.
	Non-Depreciable Capital Costs > Solar Collection Area (m2) > Value : float
		Solar collection area for one plant module in m2, ``process_table()`` is used.
	Fixed Operating Costs > area > Value : float
		Solar collection area in m2 that can be covered by one staffer.
	Fixed Operating Costs > shifts > Value : float or int
		Number of 8-hour shifts (typically 3 for 24h operation).
	Fixed Operating Costs > supervisor > Value : float or int
		Number of shift supervisors.

	Returns
	-------
	Fixed Operating Costs > staff > Value : float
		Number of 8-hour equivalent staff required for operating one plant module.
	''' 

	def __init__(self, dcf, print_info):
		process_table(dcf.inp, 'Technical Operating Parameters and Specifications', 'Value')
		process_table(dcf.inp, 'Non-Depreciable Capital Costs', 'Value')
		process_table(dcf.inp, 'Fixed Operating Costs', 'Value')

		self.required_staff(dcf)

		insert(dcf, 'Fixed Operating Costs', 'staff', 'Value', self.staff_per_module, __name__, print_info = print_info)

	def required_staff(self, dcf):
		'''Calculation of total required staff for all plant modules, then scaling down to staff
		requirements for one module.'''

		area = dcf.inp['Technical Operating Parameters and Specifications']['Plant Modules']['Value'] * dcf.inp['Non-Depreciable Capital Costs']['Solar Collection Area (m2)']['Value']

		staff = np.ceil(area / dcf.inp['Fixed Operating Costs']['area']['Value']) + dcf.inp['Fixed Operating Costs']['supervisor']['Value']
		staff = staff * dcf.inp['Fixed Operating Costs']['shifts']['Value']

		self.staff_per_module = staff / dcf.inp['Technical Operating Parameters and Specifications']['Plant Modules']['Value']