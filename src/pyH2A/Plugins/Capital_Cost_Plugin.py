from pyH2A.Utilities.input_modification import insert, sum_all_tables, process_table
import re

# ----------------------------
# Capital Cost Input/Output Dictionaries
# ----------------------------

capital_cost_input_dict = {
    'direct_capital_costs': {
        'top_level': '[...] Direct Capital Cost [...]',
        'mid_level': 'Repeatable rows',
        'lower_level': 'Value',
        'unit_key': 'unit',
    },
    'indirect_capital_costs': {
        'top_level': '[...] Indirect Capital Cost [...]',
        'mid_level': 'Repeatable rows',
        'lower_level': 'Value',
        'unit_key': 'unit',
    },
    'land_cost': {
        'top_level': 'Non-Depreciable Capital Costs',
        'mid_level': 'Cost of land ($ per acre)',
        'lower_level': 'Value',
        'unit_key': 'unit',
    },
    'land_area': {
        'top_level': 'Non-Depreciable Capital Costs',
        'mid_level': 'Land required (acres)',
        'lower_level': 'Value',
        'unit_key': 'unit',
    },
    'other_non_depreciable': {
        'top_level': '[...] Other Non-Depreciable Capital Cost [...]',
        'mid_level': 'Repeatable rows',
        'lower_level': 'Value',
        'unit_key': 'unit',
    },
}

capital_cost_output_dict = {
    'direct_capital_total': {
        'top_level': '[...] Direct Capital Cost [...]',
        'mid_level': 'Summed Total',
        'lower_level': 'Value',
        'unit_key': 'unit',
    },
    'indirect_capital_total': {
        'top_level': '[...] Indirect Capital Cost [...]',
        'mid_level': 'Summed Total',
        'lower_level': 'Value',
        'unit_key': 'unit',
    },
    'non_depreciable_total': {
        'top_level': 'Non-Depreciable Capital Costs',
        'mid_level': 'Total',
        'lower_level': 'Value',
        'unit_key': 'unit',
    },
    'depreciable_total': {
        'top_level': 'Depreciable Capital Costs',
        'mid_level': 'Total',
        'lower_level': 'Value',
        'unit_key': 'unit',
    },
    'total_capital_costs': {
        'top_level': 'Total Capital Costs',
        'mid_level': 'Total',
        'lower_level': 'Value',
        'unit_key': 'unit',
    },
}

# ----------------------------
# Resolver Functions
# ----------------------------

def capital_input_resolver(input_dict, dcf):
    resolved = {}
    for name, spec in input_dict.items():
        top_pattern = spec['top_level']
        mid = spec['mid_level']
        low = spec['lower_level']

        matched_tables = []
        for top_key in dcf.inp.keys():
            if re.search(top_pattern.replace('[...]', '.*'), top_key):
                matched_tables.append(top_key)

        values = []
        for top in matched_tables:
            process_table(dcf.inp, top, low)
            if mid.lower().startswith('repeatable'):
                for row in dcf.inp[top].values():
                    if isinstance(row, dict) and low in row:
                        values.append(row[low])
            else:
                values.append(dcf.inp[top][mid][low])

        if len(values) == 1:
            resolved[name] = values[0]
        else:
            resolved[name] = values

    return resolved


def capital_output_resolver(output_dict, values, dcf, print_info=True):
    for name, spec in output_dict.items():
        top = spec['top_level']
        mid = spec['mid_level']
        low = spec['lower_level']
        unit = spec.get('unit_key')

        insert(dcf, top, mid, low, values[name], __name__, print_info)

        if unit is not None:
            insert(dcf, top, mid, 'Unit', unit, __name__, print_info)


# ----------------------------
# Capital Cost Plugin
# ----------------------------

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

    def __init__(self, dcf, print_info=True):
        self.direct_capital_costs(dcf, print_info)
        direct_inflated = self.direct * dcf.combined_inflator

        self.indirect_capital_costs(dcf, print_info)
        indirect_inflated = self.indirect * dcf.combined_inflator

        depreciable = self.direct + self.indirect
        depreciable_inflated = direct_inflated + indirect_inflated

        self.non_depreciable_capital_costs(dcf, print_info)
        non_depreciable_inflated = self.non_depreciable * dcf.ci_inflator

        total = depreciable + self.non_depreciable
        total_inflated = depreciable_inflated + non_depreciable_inflated

        outputs = {
            'direct_capital_total': self.direct,
            'direct_capital_inflated': direct_inflated,
            'indirect_capital_total': self.indirect,
            'indirect_capital_inflated': indirect_inflated,
            'non_depreciable_total': self.non_depreciable,
            'non_depreciable_inflated': non_depreciable_inflated,
            'depreciable_total': depreciable,
            'depreciable_inflated': depreciable_inflated,
            'total_capital_costs': total,
            'total_capital_inflated': total_inflated
        }

        print(' ')
        print(' ')
        print(outputs)
        print(' ')
        print(' ')

        capital_output_resolver(capital_cost_output_dict, outputs, dcf, print_info=print_info)

    def direct_capital_costs(self, dcf, print_info=True):
        '''Calculation of direct capital costs by applying ``sum_all_tables()`` to "Direct Capital Cost" group.'''
        inputs = capital_input_resolver({'direct_capital_costs': capital_cost_input_dict['direct_capital_costs']}, dcf)
        self.direct = sum(inputs['direct_capital_costs'])
        self.direct_contributions = inputs['direct_capital_costs']

    def indirect_capital_costs(self, dcf, print_info=True):
        '''Calculation of indirect capital costs by applying ``sum_all_tables()`` to "Indirect Capital Cost" group.'''
        inputs = capital_input_resolver({'indirect_capital_costs': capital_cost_input_dict['indirect_capital_costs']}, dcf)
        self.indirect = sum(inputs['indirect_capital_costs'])

    def non_depreciable_capital_costs(self, dcf, print_info=True):
        '''Calculation of non-depreciable capital costs by calculating cost of land and applying
        ``sum_all_tables()`` to "Other Non-Depreciable Capital Cost" group.
        '''
        inputs = capital_input_resolver({
            'land_cost': capital_cost_input_dict['land_cost'],
            'land_area': capital_cost_input_dict['land_area'],
            'other_non_depreciable': capital_cost_input_dict['other_non_depreciable']
        }, dcf)

        self.non_depreciable = inputs['land_cost'] * inputs['land_area'] + sum(inputs['other_non_depreciable'])
