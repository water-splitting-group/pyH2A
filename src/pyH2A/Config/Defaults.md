# Workflow

Name | Type | Position | Description
--- | --- | --- | ---
Time_Plugin | plugin | 100 | Computes time-related arrays and values
time | function | 200 | core function to process time-related values
Inflation_Plugin | plugin | 300 | Computes the various inflation factors
inflation | function | 400 | core function to process inflation factors
Production_Plugin | plugin | 500 | Computes plant output
production | function | 600 | core function to process yearly plant output
Capital_Cost_Plugin | plugin | 700 | Calculation of direct, indirect and non-depreciable capital costs
initial_equity_depreciable_capital | function | 800 | core function to process depreciable capital costs
non_depreciable_capital_costs | function | 900 | core function to process non-depreciable capital costs
Replacement_Plugin | plugin | 1000 | Calculation of replacement costs
replacement_costs | function | 1100 | core function to process replacement costs
Labor_Operating_Cost_Plugin | plugin | 1200 | Calculation of labor operating costs
Other_Fixed_Operating_Cost_Plugin | plugin | 1300 | Calculation of other fixed operating costs
fixed_operating_costs | function | 1400 | core function to process fixed operating costs
Variable_Operating_Cost_Plugin | plugin | 1500 | Calculation of variable operating costs, including utilities
variable_operating_costs | function | 1600 | core function to process variable operating costs

# Financial Input Values

Name | Value | Unit
--- | --- | ---
Reference year | 2016 | -
Assumed start-up year | 2020 | -
Basis year | 2016 | -
Current year for capital costs | 2016 | -
Start-up time | 1 | year
Plant life | 20 | year
Depreciation schedule Length | 20 | year
Depreciation type | MACRS | -
Fraction equity financing | 40% | -
Interest rate on debt | 3.7% | -
Debt period | Constant | -
Fraction of fixed operating costs during start-up | 100% | -
Fraction of variable operating costs during start-up | 75% | -
Fraction of revenues during start-up | 75% | -
Decommissioning costs (fraction of depreciable capital investment) | 10% | -
Salvage value (fraction of total capital investment) | 10% | -
Inflation rate | 1.9% | -
After-tax real IRR | 8.0% | -
State taxes | 6.0% | -
Federal taxes | 21.0% | -
Working Capital (fraction of yearly change in operating costs) | 15.0% | - 