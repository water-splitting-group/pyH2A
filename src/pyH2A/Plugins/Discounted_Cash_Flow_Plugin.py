from functools import lru_cache

from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.input_modification import read_textfile
from pyH2A.Utilities.find_nearest import find_nearest
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
import numpy as np

input_dict = {

}

output_dict = {

}


def numpy_npv(rate, values):
	'''Calculation of net present value.
	'''

	values = np.asarray(values)
	return (values / (1+rate)**np.arange(0, len(values))).sum(axis=0)

@lru_cache(maxsize = None)
def get_idx(diagonal_number, axis0, axis1):
	'''Calculation of index for MACRS calculation.
	Uses ``lru_cache`` for repeated calculations.
	'''

	a = np.arange(0, diagonal_number)
	b = a[::-1]
	c = np.c_[a, b]

	idx = c[(c[:,0] <= axis0 - 1) & (c[:,1] <= axis1 - 1)]
	idx = (np.array(idx[:,0]), np.array(idx[:,1]))

	return idx

def MACRS_depreciation(plant_years, depreciation_length, annual_depreciable_capital):
	'''Calculation of MACRS depreciations.
	
	Parameters
	----------
	plant_years : ndarray
		Array of plant years.
	depreciation_length : int
		Depreciation length.
	annual_depreicable_capital : ndarray
		Depreciable capital by year.

	Returns 
	-------
	annual_charge : ndarray
		Charge by year.

	'''

	end_idx = len(plant_years)	

	original_macrs = read_textfile('pyH2A.Lookup_Tables~MACRS.csv', delimiter = '	')
	macrs = np.copy(original_macrs)

	macrs[1:,1:] = macrs[1:,1:]/100.
	idx_macrs = find_nearest(macrs[0][1:], depreciation_length)[0] 
	macrs_values = macrs[1:,1:][:,idx_macrs]
	macrs_values = macrs_values[macrs_values != 0]

	depreciation = np.outer(annual_depreciable_capital, macrs_values)

	charge = []
	diagonals = sum(depreciation.shape) + 1

	for i in range(1, diagonals):
		idx = get_idx(i, depreciation.shape[0], depreciation.shape[1])

		diagonal = depreciation[idx]
		charge.append(np.sum(diagonal))

	charge = np.asarray(charge)

	annual_charge = charge[:end_idx]
	annual_charge[-1] += np.sum(charge[end_idx:])

	return annual_charge


class Discounted_Cash_Flow_Plugin:
    '''Performs discounted cash flow analysis to determine levelized cost of product.

    Parameters
    ----------

    
    Returns
    -------



    '''

    def __init__(self, dcf, print_info):

        self.input_dict_resolved = input_resolver_function(input_dict, dcf, 'Discounted_Cash_Flow_Plugin')

        # ...

        output_inserter_function(output_dict, self, dcf, 'Discounted_Cash_Flow_Plugin') 

    def salvage_decommissioning(self):
        '''Calculate salvage and decommissioning costs.
        '''

        self.total_capital_inflated = self.depreciable_capital_inflation + self.non_depreciable_capital_inflated

        decommissioning = (self.depreciable_capital_inflation 
                            * self.fin['Decommissioning costs (fraction of depreciable capital investment)']['Value'])
        salvage = (self.total_capital_inflated 
                    * self.fin['Salvage value (fraction of total capital investment)']['Value'])

        self.decommissioning_costs = np.zeros_like(self.analysis_years_ones.unit['-'])
        self.decommissioning_costs[-1] = decommissioning * self.inflation_factor.unit['-'][-1]

        self.salvage_income = np.zeros_like(self.analysis_years_ones.unit['-'])
        self.salvage_income[-1] = salvage * self.inflation_factor.unit['-'][-1]

        return (numpy_npv(self.after_tax_nominal_irr, self.salvage_income), 
                numpy_npv(self.after_tax_nominal_irr, self.decommissioning_costs))

    def working_capital_reserve_calc(self):
        '''Calculate working capital reserve.
        '''

        sum_variable_fixed_operating_costs = self.variable_operating_costs + self.fixed_operating_costs

        self.working_capital_reserve = (-self.fin['Working Capital (fraction of yearly change in operating costs)']['Value'] 
                                        * np.diff(sum_variable_fixed_operating_costs))
        self.working_capital_reserve[-1] = -np.sum(self.working_capital_reserve[:-1])
        self.working_capital_reserve = np.r_[np.zeros(1), self.working_capital_reserve]

        return -numpy_npv(self.after_tax_nominal_irr, self.working_capital_reserve)

    def debt_financing(self):
        '''Calculate constant debt financing.
        '''

        self.debt_financed_capital = (self.depreciable_capital_inflation 
                                        * (1 - self.fin['Fraction equity financing']['Value']) 
                                        * self.inflation_factor.unit['-'][0])
        
        interest = self.debt_financed_capital * self.fin['Interest rate on debt']['Value']
        self.interest_per_year = self.analysis_years_ones.unit['-'] * interest

        self.principal_payment = np.zeros_like(self.analysis_years_ones.unit['-'])

        self.principal_payment[-1] = self.debt_financed_capital

        return (numpy_npv(self.after_tax_nominal_irr, self.interest_per_year), 
                numpy_npv(self.after_tax_nominal_irr, self.principal_payment))

    def depreciation_charge(self):
        '''Calculate depreciation charge.
        '''

        total_initial_depreciable_capital = self.debt_financed_capital + self.initial_depreciable_capital
        annual_depreciable_capital = np.copy(self.annual_replacement_costs)
        annual_depreciable_capital[self.start_idx] += total_initial_depreciable_capital

        self.annual_charge = MACRS_depreciation(self.plant_years_relative.unit['-'], 
                                                self.fin['Depreciation schedule Length']['Value'], 
                                                annual_depreciable_capital)		

        return numpy_npv(self.after_tax_nominal_irr, self.annual_charge)

    def h2_sales(self):
        '''Calculate H2 sales.
        '''

        self.annual_sales = self.output_per_year_at_gate.unit['kg']
        self.annual_sales[:self.start_up_time_idx] = (self.annual_sales[:self.start_up_time_idx] 
                                                        * self.fin['Fraction of revenues during start-up']['Value'])
        self.annual_sales[:self.start_idx] = 0

        return numpy_npv(self.fin['After-tax real IRR']['Value'], self.annual_sales)

    def h2_cost(self):
        '''Calculate levelized H2 cost.
        '''

        self.total_tax_rate = (self.fin['Federal taxes']['Value'] 
                                + self.fin['State taxes']['Value'] 
                                * (1. - self.fin['Federal taxes']['Value']))

        lcoe_capital_costs = (self.npv_dict['initial_equity_depreciable_capital'] 
                                + self.npv_dict['non_depreciable_capital_costs'] 
                                + self.npv_dict['replacement_costs'] 
                                + self.npv_dict['working_capital_reserve'])
        
        lcoe_depreciation = -self.npv_dict['depreciation_charge'] * self.total_tax_rate
        lcoe_principal_payment = self.npv_dict['principal_payment']
        lcoe_operating_costs = ((-self.npv_dict['salvage'] 
                                    + self.npv_dict['decommissioning'] 
                                    + self.npv_dict['fixed_operating_costs'] 
                                    + self.npv_dict['variable_operating_costs'] 
                                    + self.npv_dict['interest']) 
                                * (1. - self.total_tax_rate))
        
        lcoe_h2_sales = self.npv_dict['h2_sales'] * (1. - self.total_tax_rate)

        self.h2_cost_nominal = ((lcoe_capital_costs 
                                    + lcoe_depreciation 
                                    + lcoe_principal_payment 
                                    + lcoe_operating_costs)
                                /lcoe_h2_sales 
                                * (1. + self.fin['Inflation rate']['Value'].unit['-']) ** self.construction_time_years)
        
        self.h2_cost = self.h2_cost_nominal/self.inflation_correction.unit['-']

    def h2_revenue(self):
        '''Calculate H2 sales revenue.
        '''

        self.annual_revenue = (self.annual_sales 
                                * self.h2_cost_nominal * self.inflation_factor.unit['-'])

        return numpy_npv(self.after_tax_nominal_irr, self.annual_revenue)

    def income(self):
        '''Calculate total income.
        '''

        self.annual_pre_depreciation_income = (self.annual_revenue 
                                                + self.salvage_income 
                                                - self.decommissioning_costs 
                                                - self.fixed_operating_costs 
                                                - self.variable_operating_costs 
                                                - self.interest_per_year)
        
        self.taxable_income = self.annual_pre_depreciation_income - self.annual_charge
        self.annual_taxes = self.taxable_income * self.total_tax_rate
        self.after_tax_income = self.annual_pre_depreciation_income - self.annual_taxes

        return (numpy_npv(self.after_tax_nominal_irr, self.annual_pre_depreciation_income), 
                numpy_npv(self.after_tax_nominal_irr, self.taxable_income), 
                numpy_npv(self.after_tax_nominal_irr, self.annual_taxes), 
                numpy_npv(self.after_tax_nominal_irr, self.after_tax_income))

    def cash_flow(self):
        '''Calculate cash flow.
        '''

        pre_tax_cash_flow = (-self.annual_initial_depreciable_capital 
                                - self.annual_replacement_costs 
                                + self.working_capital_reserve 
                                - self.annual_non_depreciable_capital 
                                + self.annual_pre_depreciation_income 
                                - self.principal_payment)
        
        after_tax_post_depreciation_cash_flow = pre_tax_cash_flow - self.annual_taxes

        npv_after_tax_post_depreciation = numpy_npv(self.after_tax_nominal_irr, after_tax_post_depreciation_cash_flow)

        if abs(npv_after_tax_post_depreciation) > 1e-6:
            print('Warning: NPV of After tax post-depreciation cash flow is not 0, possible error. NPV: {0}'.format(npv_after_tax_post_depreciation))

        cummulative_cash_flow = np.cumsum(after_tax_post_depreciation_cash_flow)

        return numpy_npv(self.after_tax_nominal_irr, cummulative_cash_flow)

    def cost_contribution(self):
        '''Compile contributions to H2 cost.
        '''

        revenue = self.expenses_per_kg_H2(self.npv_dict['revenue'])

        self.contributions = {'Data': {'Initial equity depreciable capital': self.expenses_per_kg_H2(self.npv_dict['initial_equity_depreciable_capital']),
                                        'Non depreciable capital' : self.expenses_per_kg_H2(self.npv_dict['non_depreciable_capital_costs']),
                                        'Replacement costs' : self.expenses_per_kg_H2(self.npv_dict['replacement_costs']),
                                        'Salvage' : -self.expenses_per_kg_H2(self.npv_dict['salvage']),
                                        'Decommissioning' : self.expenses_per_kg_H2(self.npv_dict['decommissioning']),
                                        'Fixed operating costs' : self.expenses_per_kg_H2(self.npv_dict['fixed_operating_costs']),
                                        'Variable operating costs' : self.expenses_per_kg_H2(self.npv_dict['variable_operating_costs']),
                                        'Working capital reserve' : self.expenses_per_kg_H2(self.npv_dict['working_capital_reserve']),
                                        'Interest' : self.expenses_per_kg_H2(self.npv_dict['interest']),
                                        'Principal payment' : self.expenses_per_kg_H2(self.npv_dict['principal_payment']),
                                        'Taxes' : self.expenses_per_kg_H2(self.npv_dict['taxes'])}
                                        }

        self.contributions['Total'] = self.h2_cost
        self.contributions['Table Group'] = 'Total cost of hydrogen'

    def expenses_per_kg_H2(self, value):
        '''Calculate expenses per kg H2.
        '''

        result = (value
                    / self.npv_dict['h2_sales'] 
                    * (1. + self.fin['Inflation rate']['Value'].unit['-']) ** self.construction_time_years 
                    / self.inflation_correction.unit['-'])

        return result