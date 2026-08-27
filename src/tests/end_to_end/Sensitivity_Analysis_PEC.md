# Input files to merge

Name | Value
--- | ---
Default TEA | pyH2A.Config~Defaults_TEA.md
Base | src/tests/end_to_end/PEC_Base_test.md

# Sensitivity_Analysis

Name | Value | Label
--- | --- | ---
Dependent variable | {Dependent Variables > Levelized cost > Value, USD/kg} | Levelized Cost

# Parameters - Sensitivity_Analysis

Parameter | Name | Type | Values
--- | --- | --- | ---
PEC Cells > Cell cost > Value | PEC cell cost (USD/m2) | value | 10000; 30000
Solar-to-Hydrogen Efficiency > STH > Value | PEC solar-to-hydrogen efficiency | value | 0.10; 0.18
PEC Cells > Lifetime > Value | PEC cell lifetime (year) | value | 0.2; 1.0
Solar Concentrator > Concentration factor > Value | Concentration factor | value | 10; 100
Solar Concentrator > Cost > Value | Concentrator cost (USD/m2) | value | 50; 200
Utilities > Industrial electricity > Usage_Value | Industrial electricity usage | value | 0.08; 0.32
