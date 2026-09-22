# Input files to merge

Name | Value
--- | ---
Defaults | pyH2A.Config~Defaults_LCA.md

# Workflow

Name | Position | Comment
--- | --- | ---
Hourly_Irradiation_Plugin | 110 | Hourly irradiation for PV array
Photovoltaic_Plugin | 120 | Electricity generation and module area of PV array
Electrolyzer_Plugin | 130 | H2 production, electricity consumption and number of stacks
Reverse_Osmosis_Plugin | 140 | Purified water production and number of RO devices

# Display Parameters

Name | Value
--- | ---
Name | PV + E LCA
Color | darkblue

# Construction

Name | Value | Unit
--- | --- | ---
Capital spent in 1st year of construction | 100% | -

# Hourly Irradiation

Name | Value | Comment
--- | --- | ---
File | pyH2A.Lookup_Tables.Hourly_Irradiation_Data~tmy_34.859_-116.889_2006_2015.csv | Location: Dagget, CA, USA

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
Design output by year | {Electrolyzer > H2 production (yearly) > Value, kg} | kg[H2] | Hydrogen production by electrolyzer is considered as design output by year
Operating capacity factor | 100% | - | Set to 100%, operating capacity factor is considered during modelling of electrolyzer operation
Fraction of output that reaches gate | 100% | -

# Electrolyzer

Name | Value | Unit | Comment
--- | --- | --- | ---
Nominal power | 5,500 | kW | Production of ca. 1 t of H2 per day, same as PV_E_Base_test.md
Power requirement increase per year | 0.3% | - | Based on Chang 2020
Minimum capacity | 10% | - | Based on Chang 2020, minimum capacity for electrolyzer to operate
Hydrogen yield per unit energy | 0.0185 | kg/kWh | Based on Chang 2020
Replacement time | 80,000 | h | Based on Chang 2020, operating time after which electrolyzer stacks have to be replaced
Unit nominal power | 500 | kW | Nominal power of one electrolyzer unit (with one stack), used to calculate the number of stacks

# Photovoltaic

Name | Value | Path | Unit | Comment
--- | --- | --- | --- | ---
Nominal power | 1.5 | {Electrolyzer > Nominal power > Value, kW} | kW | Optimal PV oversize ratio, same as Chang 2020
Power loss per year | 0.5% | None | - | Based on Chang 2020
Efficiency | 22% | None | - | Only used for area calculation

# Reverse Osmosis

Name | Value | Unit | Comment
--- | --- | --- | ---
Power demand | 2.71 | kWh/m3 | Based on Hausmann 2021 and Kim 2008, kWh per m3 of sea water
Average operating time fraction | 0.16666666666666666 | - | Assumption that reverse osmosis runs for 4 h/day, relevant for scaling of reverse osmosis plant
Recovery rate | 40% | - | Fraction of fresh water obtained from given volume of sea water, based Palmer 2021 and Terlouw 2022
Device throughput | 1 | m3/h | Sea water throughput of one reverse osmosis device, used to calculate the number of devices

# Life Cycle Assessment

Name | Value | Comment
--- | --- | ---
Matrix Folder | src/tests/plugins/lca_data/matrix_folders/pve_unit_test | openLCA matrix export of the PV-E ground truth product system
UUID of product | 66b8a6b0-7b7a-4d2c-95d3-d82951c58a35 | H2 Production

# LCA - PV-E Components

Name | Value | Unit | UUID | Comment
--- | --- | --- | --- | ---
PV Electricity Generation | {Electrolyzer > Electricity consumption (yearly) > Value, MJ} | MJ | bc18dc79-2b51-455d-9fec-decf6b2693de | Electricity consumed by electrolyzer, summed over plant life
Electrolyzer Manufacturing | {Electrolyzer > Number of stacks over plant life > Value, item} | item | 4397d5db-7fea-4916-af17-b72fa72fc02a | Initial electrolyzer stacks and their replacements
Reverse Osmosis | {Reverse Osmosis > Purified water production (yearly) > Value, kg} | kg | 1659c3a5-5c6b-4f29-b746-e12119144b7b | Purified water for electrolysis, summed over plant life
