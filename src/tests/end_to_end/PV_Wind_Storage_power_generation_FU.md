# Input files to merge

Name | Value
--- | ---
Default TEA | pyH2A.Config~Defaults_TEA.md

# Functional Unit

Name | Unit | Comment
--- | --- | ---
Functional Unit | kWh | kWh of produced electricity is functional unit

# Workflow

Name | Position 
--- | --- 
Hourly_Irradiation_Plugin | 201 
Photovoltaic_Plugin | 202
Wind_Plugin | 203 
Electricity_Consumer_Plugin | 204 |
Battery_Calculation_Plugin | 205 |
Power_Management_Explicit_Battery_Plugin | 206 |
RFB_Plugin | 207 | 
Multiple_Modules_Plugin | 401 

# Technical Operating Parameters and Specifications

Name | Value | Unit | Comment 
--- | --- | --- | --- 
Design output by year | {Power Generation > Total yearly power generation > Value, kWh} | kWh | Electricity production by PV and Wind system is considered as design output by year
Operating capacity factor | 100% | - | Set to 100%
Fraction of output that reaches gate | 100% | -
Plant modules | 10 | - | Modelling of 10 modules for calculation of staff cost to facilitate comparison with PEC and photocatalytic model

# Hourly Irradiation

Name | Value | Comment 
--- | --- | --- | --- 
File | pyH2A.Lookup_Tables.Hourly_Irradiation_Data~tmy_34.859_-116.889_2006_2015.csv | Location: Dagget, CA, USA 

# Hourly Wind

Name | Value | Comment 
--- | --- | --- | --- 
File | pyH2A.Lookup_Tables.Hourly_Wind_Data~Jena.615_2005_2023.csv | Location: Jena, DE

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

# Construction

Name | Value | Unit 
--- | --- | --- 
Capital spent in 1st year of construction | 100% | - 

# Photovoltaic

Name | Value | Path | Unit | Comment
--- | --- | --- | --- | --- 
Nominal power | 30000 | None | kW | Optimal PV oversize ratio, same as Chang 2020
Power loss per year | 0.5% | None | - | Based on Chang 2020
Efficiency | 22% | None | - | Only used for area calculation

# Wind Turbine

Name | Value | Unit | Comment 
--- | --- | --- | --- 
Installed wind capacity | 60 | MW
Power per wind turbine | 4 | MW | Typical value for land-based turbines (Older ones tend to be below, new ones are higher)
Power loss per year | 0.5% | -

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
Power per cell stack | 10 | kW
Cost per cell stack | 8500 | USD 
Energy density | 40 | Wh/kg
Electrolyte regeneration per year | 0.5% | -
Storage capacity per module | 150 | MWh

# Electrolyte Impact

Name | Value | Unit
--- | --- | ---
Specific GWP | 20 | kg/kg
Energy intensity | 100 | kWh/kg
Specific toxicity | 12 | 1/kg
Specific resource use | 15 | kg/kg
Specific cost | 9 | USD/kg

# Direct Capital Costs - Power generation

Name | Value | Path | Unit | Comment
--- | --- | --- | --- | ---
PV CAPEX | 818 | {Photovoltaic > Nominal power > Value, kW} | USD | Based on Chang 2020, Chiesa 2021 Middle East PV installation cost, Shah 2021
Wind CAPEX | 1.2 | {Wind Turbine > Installed wind capacity > Value, W} | USD | Assuming 1.2 M USD per MW isntalled

# Direct Capital Costs - Storage

Name | Value | Unit | Comment
--- | --- | --- | --- | ---
Electrolyte initial holdup | {Electrolyte Impact > Initial cost of electrolyte > Value, USD} | USD | Initial amount of electrolyte 
Battery stack  | {Battery > Cost of cell stacks > Value, USD} | USD | Cost of the cell stacks

# Non-Depreciable Capital Costs

Name | Value | Unit | Comment 
--- | --- | --- | --- 
Cost of land | 500.0 | USD/acre | Same as PEC and Photocatalytic model, based on Pinaud 2013

# Fixed Operating Costs

Name | Value | Unit | Comment 
--- | --- | --- | --- 
Solar collection area per staffer | 405,000 | m2 | Same as photocatalytic model, solar collection area that can be overseen by one staff member
Wind turbines per staffer | 8 | - | 
Battery modules per staffer | 10 | - | 
Number of supervisors | 1 | - | Same as PEC and photocatalytic model, number of shift supervisors
Number of 8-hour shifts | 3 | - | Same as PEC and photocatalytic model, number of shifts per day
Hourly labor cost | 50.0 | USD/h | Same as PEC and photocatalytic model,  Burdened labor cost, including overhead (USD per man-hr)

# Planned Replacement

Name | Frequency_Value | Frequency_Unit | Cost_Value | Cost_Unit | Comment 
--- | --- | --- | --- | --- | --- 
Electrolyte replacement | 1 | year | {Electrolyte Impact > Yearly cost of electrolyte > Value, USD} | USD | the replacement of electrolyte can be continuous, but all calculations are made per year

# Grid Electricity

Name | Value | Unit
--- | --- | ---
Cost | 2.12 | USD/kWh


# Utilities

