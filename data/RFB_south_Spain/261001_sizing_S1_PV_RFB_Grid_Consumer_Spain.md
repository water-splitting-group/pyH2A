# Input files to merge

Name | Value
--- | ---
Default TEA | pyH2A.Config~Defaults_LCA.md

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
Battery_Calculation_Plugin | 105 |
Power_Management_Hourly_Plugin | 106 |
RFB_Plugin | 107 | 

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
Nominal power | 100 | None | MW | Optimal PV oversize ratio, same as Chang 2020
Power loss per year | 0.5% | None | - | Based on Chang 2020
Efficiency | 22% | None | - | Only used for area calculation

# Wind Turbine

Name | Value | Unit | Comment 
--- | --- | --- | --- 
Installed wind capacity | 40 | MW
Power per wind turbine | 4.5 | MW | corresponds to ecoinvent entry "wind turbine 5 MW, offshore, tower" cc8c02da-14df-351b-a03a-64f03f0e4f97
Power loss per year | 0.5% | -

# Battery

Name | Value | Unit | Comment
--- | --- | --- | ---
Gross capacity | 1000 | MWh | 
Lowest charge level | 20% | - | Lowest level to which battery can be discharged
Capacity loss per year | 0% | - | Loss of capacity per year
Capacity loss per full charge | 0% | - | loss per full charge equivalent
Round trip efficiency | 80% | - | 
Highest charge level | 80% | - | 
Power | 100 | MW | 
Charging threshold | 20% | -
Storage capacity per battery module | 150 | MWh
Areal energy capacity | 32 | kWh/m2

# Battery Cell Stack

Name | Value | Unit 
--- | --- | --- 
Power per cell stack | 100 | kW
Lifetime | 2 | year

# Battery Electrolyte

Name | Value | Unit
--- | --- | ---
Energy density | 40 | Wh/kg
Fraction of electrolyte to replace per year | 10% | -
Fraction of recyclable electrolyte | 0% | -
Electrolyte density | 1400 | kg/m3

# Battery Periphery

Name | Value | Unit
--- | --- | ---
Number of periphery items | 1 | -

# RFB Specific Impacts

Name | GWP_Value | GWP_Unit | Energy_Value | Energy_Unit | Toxicity_Value | Toxicity_Unit | Resource_use_Value | Resource_use_Unit
--- | --- | --- | --- | --- | --- | --- | --- | --- 
Stack | 10 | kg | 10 | J | 10 | - | 10 | kg
Electrolyte | 20 | kg/kg | 100 | kWh/kg | 12 | 1/kg | 2 | kg/kg
Tank | 2 | kg/kg | 6 | kWh/kg | 20 | 1/kg | 10 | kg/kg
Periphery | 10 | kg | 10 | J | 10 | - | 10 | kg

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
Matrix Folder | data/RFB_south_Spain/261001_OBD_S2
UUID of product | ae9327ad-ccc9-49e5-b9d4-9608f224cd1e

# LCA - Photovoltaics

Name | Value | Unit | UUID
--- | --- | --- | ---
PV Modules (by area) | {Photovoltaics > Module area > Value, m2} | m2 | 8f0e6658-3ffc-3c37-b92a-b2cd0b369b46

# LCA - Wind turbine

Name | Value | Unit | UUID
--- | --- | --- | ---
Wind turbine | {Wind Turbine > Number of wind turbines > Value, -} | - | 40e8d79e-5ce5-3356-a28d-b25c9654086f

# LCA - Battery

Name | Value | Unit | UUID
--- | --- | --- | ---
Cell stack | {Battery Cell Stack > Number of cell stacks over lifetime > Value, -} | - | a9e8e1e6-335a-4a4e-a3af-254a80a06f8d
Electrolyte | {Battery Electrolyte > Amount over lifetime > Value, kg} | kg | 73d7afa7-d04c-4813-9776-bdcdb8c6fbb7
Electrolyte tank | {Battery Tank > Tank material amount > Value, kg} | kg | 60fa4449-7193-41fb-a2bf-e232422c1b74
Periphery subsystem | {Battery Periphery > Number of periphery items > Value, -} | - | 7d8b2f6c-0d01-4be6-a8f3-d255110af1ad

# LCA - Grid

Name | Value | Unit | UUID
--- | --- | --- | ---
Grid electricity | {Grid Electricity > Total used grid electricity > Value, kWh} | kWh | bd2f732e-a959-3ee5-8d81-7bbf716d8c24

# Utilities

