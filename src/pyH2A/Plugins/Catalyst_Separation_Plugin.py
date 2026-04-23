from pyH2A.Utilities.input_modification import insert, process_table

input_dict = {
	"Water Volume": {
		"Volume": {
			"Value": {
				"type": {float,},
				"bounds": (0, None),
			},		
			"Unit": {
				"dimension": "volume",
			},	
			"optional": False,
			"description": "Total water volume."
		},
	},
	"Catalyst": {
		"Lifetime": {
			"Value": {
				"type": {float,},
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": "time",
			},	
			"optional": False,
			"description": "Lifetime of catalysts before replacement is required."	
		},
	},
	"Catalyst Separation": {
		"Filtration cost": {
			"Value": {
				"type": {float,},
				"bounds": (0, None),
			},
			"Unit": {
				"dimension": "currency / volume",
			},	
			"optional": False,
			"description": "Cost of filtration in currency per volume."
		},
	},
}

output_dict = {
    "Other Variable Operating Cost - Catalyst Separation": {
        "Catalyst separation (yearly cost)": {
            "Value": {
                "inserted_value": "yearly_cost",
                "type": {float,},
                "dimension": "currency / time",
            },
            "description": "Yearly cost of catalyst seperation.",
            "optional": False,
        },
	},
}

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







