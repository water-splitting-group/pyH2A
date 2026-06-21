# Workflow

Name | Type | Position | Description
--- | --- | --- | ---
Production_Plugin | plugin | 100 | Computes plant output
production | function | 200 | core function to process yearly plant output
Capital_Cost_Plugin | plugin | 300 | Calculation of direct, indirect and non-depreciable capital costs
initial_equity_depreciable_capital | function | 400 | core function to process depreciable capital costs
non_depreciable_capital_costs | function | 500 | core function to process non-depreciable capital costs
Replacement_Plugin | plugin | 600 | Calculation of replacement costs
replacement_costs | function | 700 | core function to process replacement costs
Labor_Operating_Cost_Plugin | plugin | 800 | Calculation of labor operating costs
Other_Fixed_Operating_Cost_Plugin | plugin | 900 | Calculation of other fixed operating costs
fixed_operating_costs | function | 1000 | core function to process fixed operating costs
Variable_Operating_Cost_Plugin | plugin | 1100 | Calculation of variable operating costs, including utilities
variable_operating_costs | function | 1200 | core function to process variable operating costs

# Financial Input Values

Name | Full Name | Value
--- | --- | ---
ref year | Reference year | 2016
startup year | Assumed start-up year | 2020
basis year | Basis year | 2016
current year capital costs | Current year for capital costs | 2016
startup time | Start-up Time (years) | 1
plant life | Plant life (years) | 20
depreciation length | Depreciation Schedule Length (years) | 20
depreciation type | Depreciation Type | MACRS
equity | % Equity Financing | 40%
interest | Interest rate on debt (%) | 3.7%
debt | Debt period | Constant
startup cost fixed | % of Fixed Operating Costs During Start-up | 100%
startup revenues | % of Revenues During Start-up | 75%
startup cost variable | % of Variable Operating Costs During Start-up | 75%
decommissioning | Decommissioning costs (% of depreciable capital investment) | 10%
salvage | Salvage value (% of total capital investment) | 10%
inflation | Inflation rate (%) | 1.9%
irr | After-tax Real IRR (%) | 8.0%
state tax | State Taxes (%) | 6.0%
federal tax | Federal Taxes (%) | 21.0%
working capital | Working Capital (% of yearly change in operating costs) | 15.0%