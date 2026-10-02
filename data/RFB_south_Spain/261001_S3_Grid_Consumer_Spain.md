# Input files to merge

Name | Value
--- | ---
Default LCA | pyH2A.Config~Defaults_LCA.md

# Functional Unit

Name | Unit | Comment
--- | --- | ---
Functional Unit | kWh[consumed] | kWh of consumed electricity is functional unit

# Workflow

Name | Position 
--- | --- 
Hourly_Irradiation_Plugin | 101 
Photovoltaic_Plugin | 102
Wind_Plugin | 103 
Electricity_Consumer_Plugin | 104 |
Power_Management_Hourly_Plugin | 106 |

# Technical Operating Parameters and Specifications

Name | Value | Unit | Comment 
--- | --- | --- | --- 
Design output by year | {Power Demand > Main consumer yearly consumption > Value, kWh} | kWh[consumed] | Main consumer yearly consumption
Operating capacity factor | 100% | - | Set to 100%
Fraction of output that reaches gate | 100% | -

# Hourly Irradiation

Name | Value | Comment 
--- | --- | --- 
File | src/pyH2A/Lookup_Tables/Hourly_Irradiation_Wind_Data/tmy_36.184_-5.609_2005_2023_south_Spain.csv | Location: Spain

# Hourly Wind

Name | Value | Comment 
--- | --- | --- 
File | src/pyH2A/Lookup_Tables/Hourly_Irradiation_Wind_Data/tmy_36.184_-5.609_2005_2023_south_Spain.csv | Location: Spain

# Hourly Main Consumer Profile

Name | Value  
--- | --- 
File | src/pyH2A/Lookup_Tables/Hourly_Consumption/Constant_consumption_10MW.csv

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

# Construction

Name | Value | Unit 
--- | --- | --- 
Capital spent in 1st year of construction | 100% | - 

# Photovoltaic

Name | Value | Path | Unit | Comment
--- | --- | --- | --- | --- 
Nominal power | 0 | None | MW | Optimal PV oversize ratio, same as Chang 2020
Power loss per year | 0.5% | None | - | Based on Chang 2020
Efficiency | 22% | None | - | Only used for area calculation

# Wind Turbine

Name | Value | Unit | Comment 
--- | --- | --- | --- 
Installed wind capacity | 0 | MW
Power per wind turbine | 4.5 | MW | corresponds to ecoinvent entry
Power loss per year | 0.5% | -

# Grid Electricity

Name | Value | Unit
--- | --- | ---
Cost | 2.12 | USD/kWh

# Planned Replacement

Name | Cost_Value | Cost_Path | Cost_Unit | Frequency_Value | Frequency_Unit | Comment
--- | --- | --- | --- | ---

# Life Cycle Assessment

Name | Value 
--- | ---
Matrix Folder | data/RFB_south_Spain/S3-OBD2026
UUID of product | f87dda37-f5f7-4231-87de-0cad8539dbcf

# LCA - Grid

Name | Value | Unit | UUID
--- | --- | --- | ---
Grid | {Grid Electricity > Total used grid electricity > Value, kWh} | kWh | bd2f732e-a959-3ee5-8d81-7bbf716d8c24

# Utilities

