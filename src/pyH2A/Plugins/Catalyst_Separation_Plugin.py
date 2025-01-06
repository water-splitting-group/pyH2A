from pyH2A.Utilities.input_modification import insert, process_table

class Catalyst_Separation_Plugin:
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

	def __init__(self, dcf, print_info):
		self.dcf = dcf

		process_table(dcf.inp, 'Water Volume', 'Value')
		process_table(dcf.inp, 'Catalyst Separation', 'Value')

		self.calculate_yearly_filtration_volume()
		self.calculate_filtration_cost()

		insert(self.dcf, 'Other Variable Operating Cost - Catalyst Separation', 
				'Catalyst Separation (yearly cost)', 'Value', self.yearly_cost,
				__name__, print_info = print_info)

	def calculate_yearly_filtration_volume(self):
		'''Calculation of water volume that has to be filtered per year.
		'''

		fraction_to_be_filtered_yearly = 1./self.dcf.inp['Catalyst']['Lifetime (years)']['Value']

		yearly_filtration_volume_liters = self.dcf.inp['Water Volume']['Volume (liters)']['Value'] * fraction_to_be_filtered_yearly
		self.yearly_filtration_volume_m3 = yearly_filtration_volume_liters/1000.

	def calculate_filtration_cost(self):
		'''Yearly cost of water filtration to remove catalyst.
		'''

		self.yearly_cost = self.yearly_filtration_volume_m3 * self.dcf.inp['Catalyst Separation']['Filtration cost ($/m3)']['Value']







