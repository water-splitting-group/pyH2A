from functools import lru_cache
import numpy as np

from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.input_modification import read_textfile
from pyH2A.Utilities.find_nearest import find_nearest
from pyH2A.Utilities.Unit_Handler.quantity import Quantity

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

def expand_to_analysis_years(operation_array, start_idx, analysis_years_ones):
	'''Expand an array covering only the operation years to the full analysis period
	(construction years included). Values are placed from `start_idx` onward, the
	construction years are left at zero.

	Parameters
	----------
	operation_array : ndarray
		Array covering the operation years only.
	start_idx : int
		Index of the first operation year within the full analysis period.
	analysis_years_ones : Quantity
		Array of ones, of length equal to the full analysis period (construction
		years + operation years), used to determine the shape of the output.

	Returns
	-------
	full : ndarray
		Array covering the full analysis period.
	'''

	full = np.zeros_like(analysis_years_ones.unit['-'])
	full[start_idx:] = operation_array

	return full


class Discounted_Cash_Flow_Plugin:
    '''Performs discounted cash flow analysis to determine the levelized cost of product.

    Combines capital costs, replacement costs, fixed and variable operating costs, debt
    financing, depreciation, taxes and revenues (all provided by upstream plugins through
    `dcf.inp`) into a full discounted cash flow analysis, following the H2A methodology.

    Parameters
    ----------
    Time > Years > Value : dict
        Dictionary containing all time-related quantities.
    Inflation > Inflation factor full > Value : ndarray
        Inflation factor of each year.
    Inflation > Inflation correction > Value : float
        Inflation correction accounting for startup year offset.
    Financial Input Values > Fraction equity financing > Value : float
        Fraction of depreciable capital costs financed through equity (as opposed to debt).
    Financial Input Values > Interest rate on debt > Value : float
        Interest rate charged on debt-financed depreciable capital.
    Financial Input Values > Depreciation schedule length > Value : int or float
        Length of the depreciation schedule.
    Financial Input Values > After-tax real IRR > Value : float
        After-tax real internal rate of return.
    Financial Input Values > Inflation rate > Value : float
        Inflation rate.
    Financial Input Values > Federal taxes > Value : float
        Federal tax rate.
    Financial Input Values > State taxes > Value : float
        State tax rate.
    Financial Input Values > Start-up time > Value : int or float
        Start-up time in years.
    Financial Input Values > Fraction of revenues during start-up > Value : float
        Fraction of revenues generated during start-up.
    Financial Input Values > Decommissioning costs (fraction of depreciable capital investment) > Value : float
        Decommissioning costs as a fraction of depreciable capital investment.
    Financial Input Values > Salvage value (fraction of total capital investment) > Value : float
        Salvage value as a fraction of total capital investment.
    Financial Input Values > Working Capital (fraction of yearly change in operating costs) > Value : float
        Working capital as a fraction of the yearly change in operating costs.
    Depreciable Capital Costs > Annual equity > Value : ndarray
        Equity-financed depreciable capital spent in each year of the analysis.
    Depreciable Capital Costs > Initial equity > Value : float
        Total equity-financed depreciable capital spent during construction.
    Depreciable Capital Costs > Inflation corrected > Value : float
        Depreciable capital costs, inflated and corrected for the startup year offset.
    Non-Depreciable Capital Costs > Annual > Value : ndarray
        Non-depreciable capital costs spent in each year of the analysis.
    Non-Depreciable Capital Costs > Inflation corrected > Value : float
        Non-depreciable capital costs, inflated and corrected for the startup year offset.
    Replacement > Total > Value : ndarray
        Total replacement costs for each year of the analysis.
    Fixed Operating Costs > Annual > Value : ndarray
        Total fixed operating costs for each year of the analysis.
    Variable Operating Costs > Annual > Value : ndarray
        Total variable operating costs for each year of the analysis.
    Technical Operating Parameters and Specifications > Output at gate by year > Value : ndarray
        Actual output at gate by year (operation years only).

    Returns
    -------
    Dependent Variables > Levelized cost > Value : float
        Levelized cost of product (nominal levelized cost, corrected for inflation).
    Total Cost of Product > Contributions > Value : dict
        Cost contributions (per functional unit of product) of each component of the discounted cash flow
    ['Discounted_Cash_Flow_Plugin'].product_cost : float
        Levelized cost of product (identical to the value inserted into `dcf.inp`).
    ['Discounted_Cash_Flow_Plugin'].contributions : dict
        Cost contributions (per functional unit of product) of each component of the discounted cash flow
        analysis to the levelized cost of product.
    ['Discounted_Cash_Flow_Plugin'].npv_dict : dict
        Net present value of each component of the discounted cash flow analysis.
    '''

    def __init__(self, dcf, print_info, run = True):
        self._set_up(dcf)
        if run:
            self._run(dcf)
        
    def _set_up(self, dcf):

        self.functional_unit = dcf.functional_unit

        self.input_dict = {
                    "Time": {
                        "Years": {
                            "Value": {
                                "type": {dict,},
                                "bounds": (None, None),
                            },
                            "Unit": {
                                "dimension": "dimensionless",
                            },
                            "optional": False,
                            "description": "Dictionary containing all time-related quantities."
                        },
                    },
                    "Technical Operating Parameters and Specifications": {
                        "Output at gate by year": {
                            "Value": {
                                "type": {np.ndarray,},
                                "bounds": (0, None),
                            },
                            "Unit": {
                                "dimension": self.functional_unit.dimension,
                            },
                            "optional": False,
                            "description": "Actual output at gate by year (operation years only)."
                        },
                    },
                    "Inflation": {
                        "Inflation factor full": {
                            "Value": {
                                "type": {np.ndarray,},
                                "bounds": (0, None),
                            },
                            "Unit": {
                                "dimension": "dimensionless",
                            },
                            "optional": False,
                            "description": "Inflation factor of each year."
                        },
                        "Inflation correction": {
                            "Value": {
                                "type": {int, float,},
                                "bounds": (0, None),
                            },
                            "Unit": {
                                "dimension": "dimensionless",
                            },
                            "optional": False,
                            "description": "Inflation correction accounting for startup year offset."
                        },
                    },
                    "Financial Input Values": {
                        "Fraction equity financing": {
                            "Value": {
                                "type": {int, float},
                                "bounds": (0, 1),
                            },
                            "Unit": {
                                "dimension": "dimensionless",
                            },
                            "optional": False,
                            "description": "Fraction of depreciable capital costs financed through equity (as opposed to debt)."
                        },
                        "Interest rate on debt": {
                            "Value": {
                                "type": {int, float},
                                "bounds": (0, None),
                            },
                            "Unit": {
                                "dimension": "dimensionless",
                            },
                            "optional": False,
                            "description": "Interest rate charged on debt-financed depreciable capital."
                        },
                        "Depreciation schedule length": {
                            "Value": {
                                "type": {int, float},
                                "bounds": (0, None),
                            },
                            "Unit": {
                                "dimension": "time",
                            },
                            "optional": False,
                            "description": "Length of the depreciation schedule."
                        },
                        "After-tax real IRR": {
                            "Value": {
                                "type": {int, float},
                                "bounds": (0, None),
                            },
                            "Unit": {
                                "dimension": "dimensionless",
                            },
                            "optional": False,
                            "description": "After-tax real internal rate of return."
                        },
                        "Inflation rate": {
                            "Value": {
                                "type": {int, float},
                                "bounds": (0, None),
                            },
                            "Unit": {
                                "dimension": "dimensionless",
                            },
                            "optional": False,
                            "description": "Inflation rate."
                        },
                        "Federal taxes": {
                            "Value": {
                                "type": {int, float},
                                "bounds": (0, None),
                            },
                            "Unit": {
                                "dimension": "dimensionless",
                            },
                            "optional": False,
                            "description": "Federal tax rate."
                        },
                        "State taxes": {
                            "Value": {
                                "type": {int, float},
                                "bounds": (0, None),
                            },
                            "Unit": {
                                "dimension": "dimensionless",
                            },
                            "optional": False,
                            "description": "State tax rate."
                        },
                        "Start-up time": {
                            "Value": {
                                "type": {int, float},
                                "bounds": (0, None),
                            },
                            "Unit": {
                                "dimension": "time",
                            },
                            "optional": False,
                            "description": "Start-up time in years."
                        },
                        "Fraction of revenues during start-up": {
                            "Value": {
                                "type": {int, float},
                                "bounds": (0, 1),
                            },
                            "Unit": {
                                "dimension": "dimensionless",
                            },
                            "optional": False,
                            "description": "Fraction of revenues generated during start-up."
                        },
                        "Decommissioning costs (fraction of depreciable capital investment)": {
                            "Value": {
                                "type": {int, float},
                                "bounds": (0, None),
                            },
                            "Unit": {
                                "dimension": "dimensionless",
                            },
                            "optional": False,
                            "description": "Decommissioning costs as a fraction of depreciable capital investment."
                        },
                        "Salvage value (fraction of total capital investment)": {
                            "Value": {
                                "type": {int, float},
                                "bounds": (0, 1),
                            },
                            "Unit": {
                                "dimension": "dimensionless",
                            },
                            "optional": False,
                            "description": "Salvage value as a fraction of total capital investment."
                        },
                        "Working Capital (fraction of yearly change in operating costs)": {
                            "Value": {
                                "type": {int, float},
                                "bounds": (0, None),
                            },
                            "Unit": {
                                "dimension": "dimensionless",
                            },
                            "optional": False,
                            "description": "Working capital as a fraction of the yearly change in operating costs."
                        },
                    },
                    "Depreciable Capital Costs": {
                        "Annual equity": {
                            "Value": {
                                "type": {np.ndarray,},
                                "bounds": (None, None),
                            },
                            "Unit": {
                                "dimension": "currency",
                            },
                            "optional": False,
                            "description": "Equity-financed depreciable capital spent in each year of the analysis."
                        },
                        "Initial equity": {
                            "Value": {
                                "type": {int, float},
                                "bounds": (None, None),
                            },
                            "Unit": {
                                "dimension": "currency",
                            },
                            "optional": False,
                            "description": "Total equity-financed depreciable capital spent during construction."
                        },
                        "Inflation corrected": {
                            "Value": {
                                "type": {int, float},
                                "bounds": (None, None),
                            },
                            "Unit": {
                                "dimension": "currency",
                            },
                            "optional": False,
                            "description": "Depreciable capital costs, inflated and corrected for the startup year offset."
                        },
                    },
                    "Non-Depreciable Capital Costs": {
                        "Annual": {
                            "Value": {
                                "type": {np.ndarray,},
                                "bounds": (None, None),
                            },
                            "Unit": {
                                "dimension": "currency",
                            },
                            "optional": False,
                            "description": "Non-depreciable capital costs spent in each year of the analysis."
                        },
                        "Inflation corrected": {
                            "Value": {
                                "type": {int, float},
                                "bounds": (None, None),
                            },
                            "Unit": {
                                "dimension": "currency",
                            },
                            "optional": False,
                            "description": "Non-depreciable capital costs, inflated and corrected for the startup year offset."
                        },
                    },
                    "Replacement": {
                        "Total": {
                            "Value": {
                                "type": {np.ndarray,},
                                "bounds": (None, None),
                            },
                            "Unit": {
                                "dimension": "currency",
                            },
                            "optional": False,
                            "description": "Total replacement costs for each year of the analysis."
                        },
                    },
                    "Fixed Operating Costs": {
                        "Annual": {
                            "Value": {
                                "type": {np.ndarray,},
                                "bounds": (None, None),
                            },
                            "Unit": {
                                "dimension": "currency",
                            },
                            "optional": False,
                            "description": "Total fixed operating costs for each year of the analysis."
                        },
                    },
                    "Variable Operating Costs": {
                        "Annual": {
                            "Value": {
                                "type": {np.ndarray,},
                                "bounds": (None, None),
                            },
                            "Unit": {
                                "dimension": "currency",
                            },
                            "optional": False,
                            "description": "Total variable operating costs for each year of the analysis."
                        },
                    },
                }

        self.output_dict = {
                    "Dependent Variables": {
                        "Levelized cost": {
                            "Value": {
                                "inserted_value": "product_cost",
                                "type": {int, float},
                                "dimension": f"currency / {self.functional_unit.dimension}",
                            },
                            "optional": False,
                            "description": "Levelized cost of product (nominal levelized cost, corrected for inflation)."
                        },
                        "Levelized cost contributions": {
                            'Value': {
                                'inserted_value': 'contributions',
                                'type': {dict,},
                                'dimension': f"currency / {self.functional_unit.dimension}",
                            },
                            'optional': False,
                            'description': "Cost contributions (per functional unit of product) of each component of the discounted cash flow"
                            
                        }
                    },
                }

    def _run(self, dcf):
        self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, 'Discounted_Cash_Flow_Plugin')

        self.npv_dict = {}

        self.prepare_time_and_rates()

        self.npv_dict['initial_equity_depreciable_capital'] = self.calculate_initial_equity_depreciable_capital()
        self.npv_dict['non_depreciable_capital_costs'] = self.calculate_non_depreciable_capital_costs()
        self.npv_dict['replacement_costs'] = self.calculate_replacement_costs()
        self.npv_dict['fixed_operating_costs'] = self.calculate_fixed_operating_costs()
        self.npv_dict['variable_operating_costs'] = self.calculate_variable_operating_costs()

        self.npv_dict['salvage'], self.npv_dict['decommissioning'] = self.calculate_salvage_decommissioning()
        self.npv_dict['working_capital_reserve'] = self.calculate_working_capital_reserve()
        self.npv_dict['interest'], self.npv_dict['principal_payment'] = self.calculate_debt_financing()
        self.npv_dict['depreciation_charge'] = self.calculate_depreciation_charge()
        self.npv_dict['product_sales'] = self.calculate_product_sales()
        self.calculate_product_cost()
        self.npv_dict['revenue'] = self.calculate_product_revenue()
        (self.npv_dict['pre_depreciation_income'],
            self.npv_dict['taxable_income'],
            self.npv_dict['taxes'],
            self.npv_dict['after_tax_income']) = self.calculate_income()
        self.calculate_cash_flow()
        self.calculate_cost_contribution()

        output_inserter_function(self.output_dict, self, dcf, 'Discounted_Cash_Flow_Plugin')

    def prepare_time_and_rates(self):
        '''Preparation of time-related quantities and derived discount rates required
        throughout the discounted cash flow analysis.
        '''

        time_dict = self.input_dict_resolved['Time']['Years']['Value']
        self.fin = self.input_dict_resolved['Financial Input Values']

        self.plant_years_relative = time_dict['Plant years relative']
        self.analysis_years_ones = time_dict['Analysis years ones']
        self.construction_years_ones = time_dict['Construction years ones']
        self.construction_time_years = len(self.construction_years_ones.unit['-'])
        self.start_idx = int(round(time_dict['Start index'].unit['-']))

        self.inflation_factor = self.input_dict_resolved['Inflation']['Inflation factor full']['Value']
        self.inflation_correction = self.input_dict_resolved['Inflation']['Inflation correction']['Value']

        self.after_tax_nominal_irr = ((1 + self.fin['After-tax real IRR']['Value'].unit['-'])
                                        * (1 + self.fin['Inflation rate']['Value'].unit['-']) - 1)

        self.start_up_time_idx = self.start_idx + int(round(self.fin['Start-up time']['Value'].unit['year']))

    def calculate_initial_equity_depreciable_capital(self):
        '''Calculate net present value of initial equity depreciable capital, using the
        equity-financed depreciable capital spent during construction (as calculated by
        `Capital_Cost_Plugin`).
        '''

        depreciable = self.input_dict_resolved['Depreciable Capital Costs']

        self.depreciable_capital_inflation = depreciable['Inflation corrected']['Value'].unit['USD']
        self.initial_depreciable_capital = depreciable['Initial equity']['Value'].unit['USD']
        self.annual_initial_depreciable_capital = depreciable['Annual equity']['Value'].unit['USD']

        construction_years = self.annual_initial_depreciable_capital[:self.construction_time_years]

        return numpy_npv(self.after_tax_nominal_irr, construction_years)

    def calculate_non_depreciable_capital_costs(self):
        '''Retrieve non-depreciable capital costs (as calculated by `Capital_Cost_Plugin`).
        '''

        non_depreciable = self.input_dict_resolved['Non-Depreciable Capital Costs']

        self.non_depreciable_capital_inflated = non_depreciable['Inflation corrected']['Value'].unit['USD']
        self.annual_non_depreciable_capital = non_depreciable['Annual']['Value'].unit['USD']

        return self.annual_non_depreciable_capital[0]

    def calculate_replacement_costs(self):
        '''Calculate net present value of replacement costs (as calculated by `Replacement_Plugin`).
        '''

        self.annual_replacement_costs = self.input_dict_resolved['Replacement']['Total']['Value'].unit['USD']

        return numpy_npv(self.after_tax_nominal_irr, self.annual_replacement_costs)

    def calculate_fixed_operating_costs(self):
        '''Calculate net present value of fixed operating costs (as calculated by
        `Other_Fixed_Operating_Cost_Plugin`).
        '''

        self.annual_fixed_operating_costs = self.input_dict_resolved['Fixed Operating Costs']['Annual']['Value'].unit['USD']

        return numpy_npv(self.after_tax_nominal_irr, self.annual_fixed_operating_costs)

    def calculate_variable_operating_costs(self):
        '''Calculate net present value of variable operating costs (as calculated by
        `Variable_Operating_Cost_Plugin`).
        '''

        self.annual_variable_operating_costs = self.input_dict_resolved['Variable Operating Costs']['Annual']['Value'].unit['USD']

        return numpy_npv(self.after_tax_nominal_irr, self.annual_variable_operating_costs)

    def calculate_salvage_decommissioning(self):
        '''Calculate salvage and decommissioning costs.
        '''

        self.total_capital_inflated = self.depreciable_capital_inflation + self.non_depreciable_capital_inflated

        decommissioning = (self.depreciable_capital_inflation
                            * self.fin['Decommissioning costs (fraction of depreciable capital investment)']['Value'].unit['-'])
        salvage = (self.total_capital_inflated
                    * self.fin['Salvage value (fraction of total capital investment)']['Value'].unit['-'])

        self.decommissioning_costs = np.zeros_like(self.analysis_years_ones.unit['-'])
        self.decommissioning_costs[-1] = decommissioning * self.inflation_factor.unit['-'][-1]

        self.salvage_income = np.zeros_like(self.analysis_years_ones.unit['-'])
        self.salvage_income[-1] = salvage * self.inflation_factor.unit['-'][-1]

        return (numpy_npv(self.after_tax_nominal_irr, self.salvage_income),
                numpy_npv(self.after_tax_nominal_irr, self.decommissioning_costs))

    def calculate_working_capital_reserve(self):
        '''Calculate working capital reserve.
        '''

        sum_variable_fixed_operating_costs = self.annual_variable_operating_costs + self.annual_fixed_operating_costs

        self.working_capital_reserve = (-self.fin['Working Capital (fraction of yearly change in operating costs)']['Value'].unit['-']
                                        * np.diff(sum_variable_fixed_operating_costs))
        self.working_capital_reserve[-1] = -np.sum(self.working_capital_reserve[:-1])
        self.working_capital_reserve = np.r_[np.zeros(1), self.working_capital_reserve]

        return -numpy_npv(self.after_tax_nominal_irr, self.working_capital_reserve)

    def calculate_debt_financing(self):
        '''Calculate constant debt financing.
        '''

        self.debt_financed_capital = (self.depreciable_capital_inflation
                                        * (1 - self.fin['Fraction equity financing']['Value'].unit['-'])
                                        * self.inflation_factor.unit['-'][0])

        interest = self.debt_financed_capital * self.fin['Interest rate on debt']['Value'].unit['-']
        self.interest_per_year = self.analysis_years_ones.unit['-'] * interest

        self.principal_payment = np.zeros_like(self.analysis_years_ones.unit['-'])
        self.principal_payment[-1] = self.debt_financed_capital

        return (numpy_npv(self.after_tax_nominal_irr, self.interest_per_year),
                numpy_npv(self.after_tax_nominal_irr, self.principal_payment))

    def calculate_depreciation_charge(self):
        '''Calculate depreciation charge.
        '''

        total_initial_depreciable_capital = self.debt_financed_capital + self.initial_depreciable_capital
        annual_depreciable_capital = np.copy(self.annual_replacement_costs)
        annual_depreciable_capital[self.start_idx] += total_initial_depreciable_capital

        self.annual_charge = MACRS_depreciation(self.plant_years_relative.unit['-'],
                                                self.fin['Depreciation schedule length']['Value'].unit['year'],
                                                annual_depreciable_capital)

        return numpy_npv(self.after_tax_nominal_irr, self.annual_charge)

    def calculate_product_sales(self):
        '''Calculate product sales.
        '''

        output_at_gate = self.input_dict_resolved['Technical Operating Parameters and Specifications']['Output at gate by year']['Value'].unit[self.functional_unit.unit]
        self.output_per_year_at_gate = expand_to_analysis_years(output_at_gate, self.start_idx, self.analysis_years_ones)

        self.annual_sales = self.output_per_year_at_gate
        self.annual_sales[:self.start_up_time_idx] = (self.annual_sales[:self.start_up_time_idx]
                                                        * self.fin['Fraction of revenues during start-up']['Value'].unit['-'])
        self.annual_sales[:self.start_idx] = 0

        return numpy_npv(self.fin['After-tax real IRR']['Value'].unit['-'], self.annual_sales)

    def calculate_product_cost(self):
        '''Calculate levelized product cost.
        '''

        self.total_tax_rate = (self.fin['Federal taxes']['Value'].unit['-']
                                + self.fin['State taxes']['Value'].unit['-']
                                * (1. - self.fin['Federal taxes']['Value'].unit['-']))

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

        lcoe_product_sales = self.npv_dict['product_sales'] * (1. - self.total_tax_rate)

        self.product_cost_nominal = ((lcoe_capital_costs
                                        + lcoe_depreciation
                                        + lcoe_principal_payment
                                        + lcoe_operating_costs)
                                    / lcoe_product_sales
                                    * (1. + self.fin['Inflation rate']['Value'].unit['-']) ** self.construction_time_years)

        self.product_cost = Quantity(self.product_cost_nominal 
                                        / self.inflation_correction.unit['-'], 
                            f'USD/{self.functional_unit.unit}')

    def calculate_product_revenue(self):
        '''Calculate product sales revenue.
        '''

        self.annual_revenue = (self.annual_sales
                                * self.product_cost_nominal 
                                * self.inflation_factor.unit['-'])

        return numpy_npv(self.after_tax_nominal_irr, self.annual_revenue)

    def calculate_income(self):
        '''Calculate total income.
        '''

        self.annual_pre_depreciation_income = (self.annual_revenue
                                                + self.salvage_income
                                                - self.decommissioning_costs
                                                - self.annual_fixed_operating_costs
                                                - self.annual_variable_operating_costs
                                                - self.interest_per_year)

        self.taxable_income = self.annual_pre_depreciation_income - self.annual_charge
        self.annual_taxes = self.taxable_income * self.total_tax_rate
        self.after_tax_income = self.annual_pre_depreciation_income - self.annual_taxes

        return (numpy_npv(self.after_tax_nominal_irr, self.annual_pre_depreciation_income),
                numpy_npv(self.after_tax_nominal_irr, self.taxable_income),
                numpy_npv(self.after_tax_nominal_irr, self.annual_taxes),
                numpy_npv(self.after_tax_nominal_irr, self.after_tax_income))

    def calculate_cash_flow(self):
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

    def calculate_cost_contribution(self):
        '''Compile contributions to product cost.
        '''

        revenue = self.expenses_per_functional_unit_of_product(self.npv_dict['revenue'])

        self.contributions = {'Data': {
                                'Initial equity depreciable capital': self.expenses_per_functional_unit_of_product(self.npv_dict['initial_equity_depreciable_capital']),
                                'Non depreciable capital' : self.expenses_per_functional_unit_of_product(self.npv_dict['non_depreciable_capital_costs']),
                                'Replacement costs' : self.expenses_per_functional_unit_of_product(self.npv_dict['replacement_costs']),
                                'Salvage' : self.expenses_per_functional_unit_of_product(self.npv_dict['salvage'], sign = 'negative'),
                                'Decommissioning' : self.expenses_per_functional_unit_of_product(self.npv_dict['decommissioning']),
                                'Fixed operating costs' : self.expenses_per_functional_unit_of_product(self.npv_dict['fixed_operating_costs']),
                                'Variable operating costs' : self.expenses_per_functional_unit_of_product(self.npv_dict['variable_operating_costs']),
                                'Working capital reserve' : self.expenses_per_functional_unit_of_product(self.npv_dict['working_capital_reserve']),
                                'Interest' : self.expenses_per_functional_unit_of_product(self.npv_dict['interest']),
                                'Principal payment' : self.expenses_per_functional_unit_of_product(self.npv_dict['principal_payment']),
                                'Taxes' : self.expenses_per_functional_unit_of_product(self.npv_dict['taxes'])
                                }
                            }

        self.contributions['Total'] = self.product_cost
        self.contributions['Table Group'] = 'Total Cost of Product'

    def expenses_per_functional_unit_of_product(self, 
                                                value, 
                                                sign = 'positive'):
        '''Calculate expenses per functional unit of product.
        '''

        result = (value
                    / self.npv_dict['product_sales']
                    * (1. + self.fin['Inflation rate']['Value'].unit['-']) ** self.construction_time_years
                    / self.inflation_correction.unit['-'])

        if sign == 'negative':
            result = -result

        return Quantity(result, f'USD/{self.functional_unit.unit}')
