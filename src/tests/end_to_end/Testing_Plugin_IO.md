# Workflow

Name | Type | Position
--- | --- | ---
Test_Plugin_A | plugin | 4
Test_Plugin_B | plugin | 4

# Plugin A - Photovoltaic Input

Name | Value | Unit
--- | --- | ---
Nominal Power | 8250 | kW

# Plugin A Input

Name | Value | Path | Unit
--- | --- | --- | ---
Power | 10 | {Plugin A - Photovoltaic Input > Nominal Power > Value, kW} | kW

# Input X - Sum Testing

Name | Value | Sum Path | Unit
--- | --- | --- | ---
Compressor | 100 | None | USD
Adsorber | 500 | None | EUR

# Input Y - Sum Testing

Name | Value | Sum Path | Unit
--- | --- | --- | ---
Reactor | 20% | {Input X - Sum Testing > Summed Total > Value, USD} | USD
Pumps | 30% | {Input X - Sum Testing > Compressor > Value, USD} | USD

# Sum Testing

Name | Value | Sum Path | Unit
--- | --- | --- | ---
Other | 100 | None | USD

# Input Z - Indirect Testing

Name | Value | Path | Unit
--- | --- | --- | ---
Design | 10% | {Sum Testing > Summed Group Total > Value, USD} | USD

# Individual Table Sum

Name | Value | Path | Unit
--- | --- | --- | ---
Entry A | 1 | None | USD
Entry B | 2 | None | USD

# Plugin B Input

Name | Value | Path | Unit | Comment
--- | --- | --- | --- | ---
Mass | 2 | {Plugin A Output > Energy > Value, J}; {Individual Table Sum > Entry A > Value, USD} | kg | Value "2" is in unit kg/J, multiplying by "Plugin A Output > Energy > Value" (which is dimension energy, used in unit "J") gives kg, second path just for testing

# Plugin B - Value/Unit pairs

Name | Usage_Value | Usage_Path | Usage_Unit | Cost_Value | Cost_Unit
--- | --- | --- | --- | --- | ---
Test Input | {Plugin A Input > Power > Value, kW} | {Individual Table Sum > Entry A > Value, USD} | kW | {Individual Table Sum > Entry B > Value, EUR} | EUR

# Display Parameters

Name | Value
--- | ---
Name | PV + E
Color | darkblue

# Technical Operating Parameters and Specifications

Name | Value | Unit | Comment
--- | --- | --- | ---
Plant design capacity | 1000 | kg/day | Placeholder
Operating capacity factor | 100% | - | Placeholder
Fraction of output that reaches gate | 100% | - | Placeholder

# Construction

Name | Full Name | Value | Unit
--- | --- | --- | ---
capital perc 1st | % of capital spent in 1st year of construction | 100% | -

# Non-Depreciable Capital Costs

Name | Value | Comment
--- | --- | ---
Land required (acres) | 100 | Placeholder
Cost of land ($ per acre) | 500.0 | Same as PEC and Photocatalytic model, based on Pinaud 2013.

# Fixed Operating Costs

Name | Full Name | Value | Comment
--- | --- | --- | ---
area | Area per staff (m2) | 405,000 | Same as photocatalytic model, solar collection area that can be overseen by one staff member.
supervisor | Shift supervisor | 1 | Same as PEC and photocatalytic model, number of shift supervisors.
shifts | Shifts | 3 | Same as PEC and photocatalytic model, number of shifts per day.
hourly labor cost | Burdened labor cost, including overhead ($ per man-hr) | 50.0 | Same as PEC and photocatalytic model.
staff | Staff needed | 3 | Placeholder

# Utilities

Name | Usage per kg H2 | Usage Unit | Cost | Cost Unit | Price Conversion Factor | Comment
--- | --- | --- | --- | --- | --- | ---
Process Water | 10 | L/kg H2 | 0.0006 | $/L | 1. | Seawater reverse osmosis cost ca. 0.6 $/m3 (equal to 0.0006 $/L), based on Kibria 2021 and Driess 2021.

# Planned Replacement
