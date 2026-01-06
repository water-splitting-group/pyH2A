from pyH2A.Utilities.input_modification import insert, sum_all_tables, process_table

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
		'top_level': 'Other Fixed Operating Cost',
		'mid_level': 'Repeatable rows',
		'lower_level': 'Value',
		'unit_key': 'unit',
	},
}

fixed_operating_cost_output_dict = {
	'other_fixed_operating_cost_total': {
		'top_level': 'Other Fixed Operating Cost',
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

def analyzer_input_resolver(input_dict, dcf):
    """
    Resolve inputs for analyzers from dcf.inp using an I/O dictionary.
    Handles repeatable rows.
    Returns a dictionary mapping input names to their resolved values.
    """
    resolved = {}

    for name, spec in input_dict.items():
        top = spec['top_level']
        mid = spec['mid_level']
        low = spec['lower_level']

        process_table(dcf.inp, top, low)

        if mid.lower().startswith('repeatable'):
            # Gather values from all rows under the top-level group
            values = []
            for row in dcf.inp[top].values():
                if isinstance(row, dict) and low in row:
                    values.append(row[low])
            resolved[name] = values
        else:
            resolved[name] = dcf.inp[top][mid][low]

    return resolved

def analyzer_output_resolver(output_dict, values, dcf, print_info):
    """
    Insert outputs (figures, tables, or aggregated metrics) for analyzers
    back into dcf.inp using the output specification dictionary.
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
                'Unit',
                unit,
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

    def __init__(self, dcf, print_info=True):
        self.labor_cost(dcf)
        self.other_cost(dcf, print_info)

        outputs = {
            'other_fixed_operating_cost_total': self.other,
            'labor_cost_uninflated': self.labor_uninflated,
            'labor_cost_inflated': self.labor,
            'fixed_operating_cost_total': self.labor + self.other,
        }

        analyzer_output_resolver(fixed_operating_cost_output_dict, outputs, dcf, print_info=print_info)

    def labor_cost(self, dcf):
        '''Calculation of yearly labor costs by multiplying number of staff times hourly labor cost.'''
        inputs = analyzer_input_resolver(fixed_operating_cost_input_dict, dcf)
        self.labor_uninflated = inputs['staff'] * inputs['hourly_labor_cost'] * 2080.
        self.labor = self.labor_uninflated * dcf.labor_inflator

    def other_cost(self, dcf, print_info):
        '''Calculation of yearly other fixed operating costs by applying ``sum_all_tables()`` 
        to "Other Fixed Operating Cost" group.'''
        self.other = sum_all_tables(
            dcf.inp,
            'Other Fixed Operating Cost',
            'Value',
            insert_total=True,
            class_object=dcf,
            print_info=print_info
        ) * dcf.combined_inflator
