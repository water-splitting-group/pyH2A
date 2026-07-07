# Input files to merge

Name | Value
--- | ---
File A | src/tests/end_to_end/Thermal/Thermal_Base_test.md

# Technical Operating Parameters and Specifications

Name | Value | Unit 
--- | --- | --- 
Operating capacity factor | 40% | - 

# Utilities

Name | Usage_Value | Usage_Path | Usage_Unit | Cost_Value | Cost_Path | Cost_Unit | Price_Conversion_Factor_Value | Price_Conversion_Factor_Unit | Comment 
--- | --- | --- | --- | --- | --- | --- | --- | --- 
Industrial electricity | 0.86 | None | 1/kg | pyH2A.Lookup_Tables.Utility_Cost~Industrial_Electricity_AEO_2017_Reference_Case.csv | None | USD | 0.0256 | - | Electricity usage based on Pinaud 2013. 
Process water | 4.369 | None | 1/kg | 0.0993749510945008 | None | USD | 2.0 | - | Seawater reverse osmosis: 4.369 gal/kg H2, at a cost of ca. 0.6 USD/m3 (equal to ca. 0.0993 USD/gal), based on Kibria 2021 and Driess 2021. 