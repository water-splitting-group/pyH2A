import numpy as np
from pyH2A.Utilities.input_modification import insert, process_table

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
		self.dcf = dcf

		process_table(self.dcf.inp, 'Technical Operating Parameters and Specifications', 'Value')
		process_table(self.dcf.inp, 'Non-Depreciable Capital Costs', 'Value')
		process_table(self.dcf.inp, 'Fixed Operating Costs', 'Value')

		self.required_staff()

		insert(self.dcf, 'Fixed Operating Costs', 'staff', 'Value', self.staff_per_module, __name__, print_info = print_info)

	def required_staff(self):
		'''Calculation of total required staff for all plant modules, then scaling down to staff
		requirements for one module.'''

		area = self.dcf.inp['Technical Operating Parameters and Specifications']['Plant Modules']['Value'] * self.dcf.inp['Non-Depreciable Capital Costs']['Solar Collection Area (m2)']['Value']

		staff = np.ceil(area / self.dcf.inp['Fixed Operating Costs']['area']['Value']) + self.dcf.inp['Fixed Operating Costs']['supervisor']['Value']
		staff = staff * self.dcf.inp['Fixed Operating Costs']['shifts']['Value']

		self.staff_per_module = staff / self.dcf.inp['Technical Operating Parameters and Specifications']['Plant Modules']['Value']