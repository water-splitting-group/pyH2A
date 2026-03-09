# Workflow

Name | Type | Position
--- | --- | ---
Hourly_Irradiation_Plugin | plugin | 0
Photovoltaic_Plugin | plugin | 0
Electrolyzer_Plugin | plugin | 0
Battery_Plugin | plugin | 0
Stored_Power_Electrolysis_Plugin | plugin | 0
Reverse_Osmosis_Plugin | plugin | 2
Power_Management_Plugin | plugin | 2
Multiple_Modules_Plugin | plugin | 3

# Display Parameters

Name | Value
--- | ---
Name | PV + E
Color | darkblue

# Hourly Irradiation

Name | Value | Comment
--- | --- | ---
File | pyH2A.Lookup_Tables.Hourly_Irradiation_Data~tmy_34.859_-116.889_2006_2015.csv | Location: Dagget, CA, USA

# Irradiance Area Parameters

Name | Value | Comment
--- | --- | ---
Module Tilt (degrees) | Hourly Irradiation > Latitude > Value | Module tilt equal to latitude of location.
Array Azimuth (degrees) | 180
Nominal Operating Temperature (Celsius) | 45
Mismatch Derating | 0.98 | Based on Chang 2020.
Dirt Derating | 0.98 | Based on Chang 2020.
Temperature Coefficient (per Celsius) | -0.4% | Based on Chang 2020.

# Irradiation Used

Name | Value | Comment
--- | --- | --- 
Data | Hourly Irradiation > Horizontal Single Axis Tracking (kW) > Value | Single axis tracking based on Chang 2020.

# Technical Operating Parameters and Specifications

Name | Value | Comment
--- | --- | ---
Plant Modules | 10 | Modelling of 10 modules for calculation of staff cost to facilitate comparison with PEC and photocatalytic model.

# Construction

Name | Full Name | Value
--- | --- | ---
capital perc 1st | % of capital spent in 1st year of construction | 100%

# CAPEX Multiplier

Name | Value | Full Name
--- | --- | ---
Multiplier | 1.0 | CAPEX multiplier for every 10-fold increase of system size.

# Electrolyzer

Name | Value | Comment
--- | --- | ---
Nominal Power (kW) | 5,500.0 | Production of ca. 1 t of H2 per day to compare with PEC and photocatalytic models.
CAPEX Reference Power (kW) | 1,000.0
Power requirement increase per year | 0.3% | Based on Chang 2020
Minimum capacity | 10.0% | Based on Chang 2020, minimum capacity for electrolyzer to operate.
Conversion efficiency (kg H2/kWh) | 0.0185 | Based on Chang 2020
Replacement time (h) | 80,000.0 | Based on Chang 2020, operating time after which electrolyzer stacks have to be replaced.

# Electrolysis Using Stored Power

Name | Value | Comment
--- | --- | ---
Fraction of stored power used for electrolysis | 95% | Additional electrolysis using stored power

# Photovoltaic

Name | Value | Path | Comment
--- | --- | --- | --- 
Nominal Power (kW) | 1.5 | Electrolyzer > Nominal Power (kW) > Value | Optimal PV oversize ratio, same as Chang 2020
CAPEX Reference Power (kW) | 1,000.0
Power loss per year | 0.5% | None | Based on Chang 2020
Efficiency | 22% | None | Only used for area calculation.

# Battery

Name | Value | Comment
--- | --- | ---
Design Capacity (kWh) | 800000 | Full design capacity
Lowest discharge level | 20% | Lowest level to which battery can be discharged
Capacity loss per year | 1% | Loss of capacity per year
Round trip efficiency | 100% | For lithium ion battery

# Reverse Osmosis

Name | Value | Comment
--- | --- | --- | ---
Power Demand (kWh/m3) | 2.71 | based on Hausmann 2021 and Kim 2008 (this was chosen for a purity of < 10 ppm of disolved salts in the obtained water), kWh per m3 of sea water
Average daily operating hours | 4 | Assumption that reverse osmosis runs for 4 h/day, relevant for scaling of reverse osmosis plant
Recovery Rate | 40.0% | Fraction of fresh water obtained from given volume of sea water, based Palmer 2021 and Tewlour 2022

# Power Consumption

Name | Value | Type
--- | --- | ---
Test Consumer | 0 | on_demand

# Direct Capital Costs - Reverse Osmosis

Name | Value | Path | Comment 
--- | --- | --- | ---
Reverse Osmosis CAPEX ($ per m3/h capacity) | 6000 | Reverse Osmosis > Capacity (m3/h) > Value | Based on https://samcotech.com/much-reverse-osmosis-nanofiltration-membrane-systems-cost/, Conversion factor of 4.5 from GPM to m3/h

# Direct Capital Costs - Battery

Name | Value | Path
--- | --- | ---
Battery CAPEX ($/kWh) | 0 | Battery > Design Capacity (kWh) > Value

# Direct Capital Costs - PV

Name | Value | Path | Comment
--- | --- | --- | ---
PV CAPEX ($/kW) | 818.0 | Photovoltaic > Nominal Power (kW) > Value ; Photovoltaic > Scaling Factor > Value | Based on Chang 2020, Chiesa 2021 Middle East PV installation cost, Shah 2021.

# Direct Capital Costs - Electrolyzer

Name | Value | Path | Comment
--- | --- | --- | ---
Electrolyzer CAPEX ($/kW) | 784.0 | Electrolyzer > Nominal Power (kW) > Value ; Electrolyzer > Scaling Factor > Value | Based on Chang 2020, IRENA 2020 Green Hydrogen (PEM System CAPEX 700 - 1400 $/kg), Shah 2021.

# Non-Depreciable Capital Costs

Name | Value | Comment
--- | --- | ---
Cost of land ($ per acre) | 500.0 | Same as PEC and Photocatalytic model, based on Pinaud 2013.

# Fixed Operating Costs

Name | Full Name | Value | Comment
--- | --- | --- | ---
area | Area per staff (m2) | 405,000 | Same as photocatalytic model, solar collection area that can be overseen by one staff member.
supervisor | Shift supervisor | 1 | Same as PEC and photocatalytic model, number of shift supervisors.
shifts | Shifts | 3 | Same as PEC and photocatalytic model, number of shifts per day.
hourly labor cost | Burdened labor cost, including overhead ($ per man-hr) | 50.0 | Same as PEC and photocatalytic model.

# Other Fixed Operating Costs

Name | Value | Path | Comment
--- | --- | --- | ---
Electrolyzer OPEX (% of CAPEX) | 2% | Direct Capital Costs - Electrolyzer > Electrolyzer CAPEX ($/kW) > Value | Based on Stolten 2020, Shah 2021.
PV OPEX (% of CAPEX) | 2% | Direct Capital Costs - PV > PV CAPEX ($/kW) > Value | Based on Stolten 2020.

# Utilities

Name | Usage per kg H2 | Usage Unit | Cost | Cost Unit | Price Conversion Factor | Comment
--- | --- | --- | --- | --- | --- | ---
Process Water | 10 | L/kg H2 | 0.0006 | $/L | 1. | Seawater reverse osmosis cost ca. 0.6 $/m3 (equal to 0.0006 $/L), based on Kibria 2021 and Driess 2021.

# Grid Electricity

Name | Value
--- | ---
Cost ($/kWh) | 10000.12

# Planned Replacement

Name | Cost ($) | Path | Comment
--- | --- | --- | ---
Electrolyzer Stack Replacement | 40% | Direct Capital Costs - Electrolyzer > Electrolyzer CAPEX ($/kW) > Value | Based on Chang 2020
