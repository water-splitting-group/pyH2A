# Input files to merge

Name | Value
--- | ---
PV-E Base Model | src/tests/e2e_lca/data/PV_E/PV_E_TEA_LCA.md
Default TEA + LCA | pyH2A.Config~Defaults_TEA_LCA.md

# Dependent variable

Name | Path to variable | Variable unit | Comment
--- | --- | --- | --- | ---
Global warming potential (GWP100) | Dependent Variables > Climate change: fossil - Global warming potential (GWP100) > Value | kg[$CO_{2}$-Eq]/kg[H2] | Target range provided in same units as dependent variable (kg[$CO_{2}$]/kg[H2])

# Sensitivity_Analysis

Name | Parameter path | Type | Values | Comment
--- | --- | --- | --- | --- 
PV efficiency / - | Photovoltaic > Efficiency > Value | value | 18% ; 30% | Efficiency of PV panels, affects required amount of solar panels
Battery energy density / kWh/kg[battery] | Battery > Energy density > Value | factor | 0.75 ; 1.5 | Energy density of batteries in kWh/kg[battery]
Electrolyzer efficiency / kg[H2]/kWh[electricity] | Electrolyzer > Hydrogen yield per unit energy > Value | value | 0.10 ; 0.22 | Efficiency of electrolyzer for the conversion of electricity to hydrogen
Reverse osmosis recovery rate / - | Reverse Osmosis > Recovery rate > Value | value | 20% ; 80% | Recovery rate for purified water from seawater for reverse osmosis 