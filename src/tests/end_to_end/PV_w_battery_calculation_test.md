# Input files to merge

Name | Value
--- | ---
Default TEA | pyH2A.Config~Defaults_TEA.md

# Workflow

Name | Position 
--- | --- 
Hourly_Irradiation_Plugin | 201 |
Photovoltaic_Plugin | 202 |
Electricity_Consumer_Plugin | 203 |
Battery_Calculation_Plugin | 204 |
Power_Management_Explicit_Battery_Plugin | 302 |



# Display Parameters

Name | Value 
--- | --- 
Name | PV + E 
Color | darkblue 

# Hourly Irradiation

Name | Value | Comment 
--- | --- | --- | --- 
File | pyH2A.Lookup_Tables.Hourly_Irradiation_Data~tmy_34.859_-116.889_2006_2015.csv | Location: Dagget, CA, USA 

# Hourly Consumer Profile
Name | Value  
--- | --- | --- 
File | pyH2A.Lookup_Tables.Hourly_Consumption~Constant_consumption_10MW.csv 


# Irradiance Area Parameters

Name | Value | Unit | Comment 
--- | --- | --- | --- 
Array azimuth | 180 | deg 
Nominal operating temperature | 45 | degC 
Mismatch derating | 98% | - | Based on Chang 2020
Dirt derating | 98% | - | Based on Chang 2020
Temperature coefficient | -0.4% | 1/delta_degC | Based on Chang 2020

# Irradiation Used

Name | Value | Unit | Comment 
--- | --- | --- | --- 
Data | {Hourly Irradiation > Horizontal single axis tracking > Value, kWh/m2} | kWh/m2 | Single axis tracking based on Chang 2020

# Technical Operating Parameters and Specifications

Name | Value | Unit | Comment 
--- | --- | --- | --- 
Fraction of output that reaches gate | 100% | -
Operating capacity factor | 100% | -
Plant design capacity | 1000 | kg/day

# Construction

Name | Value | Unit 
--- | --- | --- 
Capital spent in 1st year of construction | 100% | - 


# Photovoltaic

Name | Value | Path | Unit | Comment
--- | --- | --- | --- | --- 
Nominal power | 100 | None | MW | Optimal PV oversize ratio, same as Chang 2020
Power loss per year | 0.5% | None | - | Based on Chang 2020
Efficiency | 22% | None | - | Only used for area calculation

# Battery

Name | Value | Unit | Comment
--- | --- | --- | ---
Design capacity | 3000 | MWh | Full design capacity
Lowest discharge level | 20% | - | Lowest level to which battery can be discharged
Capacity loss per year | 1% | - | Loss of capacity per year
Round trip efficiency | 80% | - | For lithium ion battery
Highest charge level | 80% | - | 
Power | 20 | MW | insufficient for a 10 MW customer at night
Charging threshold | 20% | -


# Power Consumption

Name | Value | Unit 
--- | --- | --- | ---
Test consumer | 00 | MWh 

# Direct Capital Costs - Battery

Name | Value | Path | Unit
--- | --- | --- | ---
Battery CAPEX | 0. | {Battery > Design capacity > Value, kWh} | USD

# Direct Capital Costs - PV

Name | Value | Path | Unit | Comment
--- | --- | --- | --- | ---
PV CAPEX | 818 | {Photovoltaic > Nominal power > Value, kW} | USD | Based on Chang 2020, Chiesa 2021 Middle East PV installation cost, Shah 2021

# Non-Depreciable Capital Costs

Name | Value | Unit | Comment 
--- | --- | --- | --- 
Cost of land | 500.0 | USD/acre | Same as PEC and Photocatalytic model, based on Pinaud 2013

# Fixed Operating Costs

Name | Value | Unit | Comment 
--- | --- | --- | --- 
Solar collection area per staffer | 405,000 | m2 | Same as photocatalytic model, solar collection area that can be overseen by one staff member
Number of supervisors | 1 | - | Same as PEC and photocatalytic model, number of shift supervisors
Number of 8-hour shifts | 3 | - | Same as PEC and photocatalytic model, number of shifts per day
Hourly labor cost | 50.0 | USD/h | Same as PEC and photocatalytic model,  Burdened labor cost, including overhead (USD per man-hr)

# Other Fixed Operating Costs

Name | Value | Path | Unit | Comment
--- | --- | --- | --- | --- 
PV OPEX (fraction of CAPEX) | 2% | {Direct Capital Costs - PV > PV CAPEX > Value, USD} | USD | Based on Stolten 2020

# Utilities

Name | Usage_Value | Usage_Path | Usage_Unit | Cost_Value | Cost_Path | Cost_Unit | Price_Conversion_Factor_Value | Price_Conversion_Factor_Unit | Comment
--- | --- | --- | --- | --- | --- | --- | --- | --- | ---


# Grid Electricity

Name | Value | Unit
--- | --- | ---
Cost | 10000.12 | USD/kWh


# Planned Replacement

Name | Cost_Value | Cost_Path | Cost_Unit | Frequency_Value | Frequency_Unit | Comment
--- | --- | --- | --- | ---
Stack replacement | 40% | {Direct Capital Costs - Battery > Battery CAPEX > Value, USD} | USD | 2 | year | 

# Fixed Operating Costs

Name | Value | Unit | Comment
--- | --- | --- | --- 
Staff | 7 | - | Number of staff
Hourly labor cost | 50.0  | USD/h | Burdened labor cost, including overhead