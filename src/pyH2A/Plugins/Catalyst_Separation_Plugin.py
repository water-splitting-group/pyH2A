from pyH2A.Utilities.input_modification import insert, process_table

catalyst_separation_input_dict = {
	'total_water': {
		'top_level': 'Water Volume',
		'mid_level': 'Volume (liters)',
		'lower_level': 'Value',
		'unit_key': 'unit',
	},
	'lifetime_catalyst': {
		'top_level': 'Catalyst',
		'mid_level': 'Lifetime (years)',
		'lower_level': 'Value',
		'unit_key': 'unit',
	},
	'cost_filteration': {
		'top_level': 'Catalyst Separation',
		'mid_level': 'Filtration cost ($/m3)',
		'lower_level': 'Value',
		'unit_key': 'unit',
	}
}

catalyst_separation_output_dict = {
	'yearly_cost': {
		'top_level': 'Other Variable Operating Cost - Catalyst Separation',
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
		inputs = input_resolver(catalyst_separation_input_dict, dcf)

		self.total_water = inputs['total_water']
		self.lifetime_catalyst = inputs['lifetime_catalyst']
		self.cost_filteration = inputs['cost_filteration']

		self.calculate_yearly_filtration_volume()
		self.calculate_filtration_cost()

		output = {
			'yearly_cost': self.yearly_cost
		}

		output_resolver(catalyst_separation_output_dict, output, dcf, print_info=print_info)

	def calculate_yearly_filtration_volume(self):
		'''Calculation of water volume that has to be filtered per year.
		'''

		fraction_to_be_filtered_yearly = 1./self.lifetime_catalyst

		yearly_filtration_volume_liters = self.total_water * fraction_to_be_filtered_yearly
		self.yearly_filtration_volume_m3 = yearly_filtration_volume_liters/1000.

	def calculate_filtration_cost(self):
		'''Yearly cost of water filtration to remove catalyst.
		'''

		self.yearly_cost = self.yearly_filtration_volume_m3 * self.cost_filteration







