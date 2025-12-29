from pyH2A.Utilities.input_modification import insert, process_table

catalyst_separation_input_dict = {
	'total_water': {
		'top_level': 'Water Volume',
		'mid_level': 'Volume (liters)',
		'lower_level': 'Value',
		'unit_key': 'unit',
	},
	'total_water': {
		'top_level': 'Catalyst',
		'mid_level': 'Lifetime (years)',
		'lower_level': 'Value',
		'unit_key': 'unit',
	},
	'total_water': {
		'top_level': 'Catalyst Separation',
		'mid_level': 'Filtration cost ($/m3)',
		'lower_level': 'Value',
		'unit_key': 'unit',
	}
}

catalyst_separation_output_dict = {
	'yearly_cost_catalyst_separation': {
		'top_level': 'Catalyst Separation',
		'mid_level': 'Catalyst Separation (yearly cost)',
		'lower_level': 'Value',
		'unit_key': 'unit',
	}
}

def input_resolver(io_dict, dcf):
	"""
    Resolve inputs from dcf.inp using an I/O specification dictionary.
    (Value-only; unit handling is out of scope.)
    """
	resolved = {}

	for name, spec in io_dict.items():
		top = spec['top_level']
		mid = spec['mid_level']
		low = spec['lower_level']

		# Ensure tables are expanded
		process_table(dcf.inp, top, low)

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
        unit = spec.get('unit')

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
                'Unit',
                unit,
                __name__,
                print_info=print_info
            )


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
		process_table(dcf.inp, 'Water Volume', 'Value')
		process_table(dcf.inp, 'Catalyst Separation', 'Value')

		self.calculate_yearly_filtration_volume(dcf)
		self.calculate_filtration_cost(dcf)

		insert(dcf, 'Other Variable Operating Cost - Catalyst Separation', 
				'Catalyst Separation (yearly cost)', 'Value', self.yearly_cost,
				__name__, print_info = print_info)

	def calculate_yearly_filtration_volume(self, dcf):
		'''Calculation of water volume that has to be filtered per year.
		'''

		fraction_to_be_filtered_yearly = 1./dcf.inp['Catalyst']['Lifetime (years)']['Value']

		yearly_filtration_volume_liters = dcf.inp['Water Volume']['Volume (liters)']['Value'] * fraction_to_be_filtered_yearly
		self.yearly_filtration_volume_m3 = yearly_filtration_volume_liters/1000.

	def calculate_filtration_cost(self, dcf):
		'''Yearly cost of water filtration to remove catalyst.
		'''

		self.yearly_cost = self.yearly_filtration_volume_m3 * dcf.inp['Catalyst Separation']['Filtration cost ($/m3)']['Value']







