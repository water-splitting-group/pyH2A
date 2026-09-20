# Input files to merge

Name | Value
--- | ---
Default TEA | pyH2A.Config~Defaults_TEA.md

# Display Parameters

Name | Value
--- | ---
Name | PV + E
Color | darkblue

# Workflow

Name | Position
--- |  ---
Hourly_Irradiation_Plugin @ Baggie | 001
Hourly_Irradiation_Plugin @ PV | 002

# Hourly Irradiation

Name | Value
--- | --- 
File | pyH2A.Lookup_Tables.Hourly_Irradiation_Data~tmy_34.859_-116.889_2006_2015.csv

# Irradiance Area Parameters @ Baggie

Name | Value | Unit 
--- | --- | --- | --- 
Module tilt | 0 | deg 
Array azimuth | 0 | deg 
Nominal operating temperature | 45 | degC 
Mismatch derating | 98% | - 
Dirt derating | 98% | - 
Temperature coefficient | 0 | 1/delta_degC 

# Irradiance Area Parameters @ PV

Name | Value | Unit 
--- | --- | --- | --- 
Array azimuth | 180 | deg 
Nominal operating temperature | 45 | degC 
Mismatch derating | 98% | - 
Dirt derating | 98% | - 
Temperature coefficient | -0.4% | 1/delta_degC 

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

Name | Value | Unit | Comment
--- | --- | --- | ---
Land required | 100 | acre | Placeholder
Cost of land | 500.0 | USD/acre | Same as PEC and Photocatalytic model, based on Pinaud 2013.

# Fixed Operating Costs

Name | Full Name | Value | Unit | Comment
--- | --- | --- | ---
Hourly labor cost | Burdened labor cost, including overhead ($ per man-hr) | 50.0 | USD/h | Same as PEC and photocatalytic model.
Staff | Staff needed | 3 | - |Placeholder

# Utilities

Name | Usage_Value | Usage_Unit | Cost_Value | Cost_Unit | Price_Conversion_Factor_Value | Price_Conversion_Factor_Unit | Comment
--- | --- | --- | --- | --- | --- | --- | ---
Process water | 10 | 1/kg | 0.0006 | USD | 1.0 | - | Seawater reverse osmosis cost ca. 0.6 $/m3 (equal to 0.0006 $/L), based on Kibria 2021 and Driess 2021.

# Planned Replacement
