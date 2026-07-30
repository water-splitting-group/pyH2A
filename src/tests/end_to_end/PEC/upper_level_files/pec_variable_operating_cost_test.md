# Input files to merge

Name | Value
--- | ---
File A | src/tests/end_to_end/PEC_Base_test.md
Default TEA | pyH2A.Config~Defaults_TEA.md

# Technical Operating Parameters and Specifications

Name | Value | Path | Unit | Comment
--- | --- | --- | --- | --- 
Operating capacity factor | 30% | None | - | (0.33× the reference value.)

# Utilities

Name | Usage_Value | Usage_Path | Usage_Unit | Cost_Value | Cost_Path | Cost_Unit | Price_Conversion_Factor_Value | Price_Conversion_Factor_Unit | Comment 
--- | --- | --- | --- | --- | --- | --- | --- | --- 
Industrial electricity | 1.26 | None | 1/kg | pyH2A.Lookup_Tables.Utility_Cost~Industrial_Electricity_AEO_2017_Reference_Case.csv | None | USD | 0.0036 | - | Electricity usage based on Pinaud 2013 (7.88× the reference value.)
Process water | 2.569 | None | 1/kg | 0.0025749510945008 | None | USD | 2. | - | Seawater reverse osmosis cost ca. 0.6 USD/m3 (equal to ca. 0.0023 USD/gal), based on Kibria 2021 and Driess 2021. (1.08× the reference value.)