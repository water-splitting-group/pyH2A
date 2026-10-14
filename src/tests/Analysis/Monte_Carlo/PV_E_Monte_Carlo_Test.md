# Input files to merge

Name | Value
--- | ---
PV-E Base Model | src/tests/e2e_lca/data/PV_E/PV_E_TEA_LCA.md
Default TEA + LCA | pyH2A.Config~Defaults_TEA_LCA.md

# Dependent variable

Name | Path to variable | Variable unit | Target range | Comment
--- | --- | --- | --- | ---
Global warming potential (GWP100) | Dependent Variables > Climate change: fossil - Global warming potential (GWP100) > Value | kg[$CO_{2}$-Eq]/kg[H2] | 1.5; 1.6 | Target range provided in same units as dependent variable (kg[$CO_{2}$]/kg[H2])

# Monte_Carlo_Analysis

Name | Value | Comment
--- | --- | ---
Samples | 100 | Number of samples in Monte Carlo simulation.
Output File | src/tests/Analysis/Monte_Carlo/Monte_Carlo_Output.csv

# Parameters - Monte_Carlo_Analysis

Name | Parameter path | Type | Values | File index | Comment
--- | --- | --- | --- | --- | --- 
PV efficiency / - | Photovoltaic > Efficiency > Value | value | Base; 0.3 | 0 | Efficiency of PV panels, affects required amount of solar panels
Battery energy density / kWh/kg[battery] | Battery > Energy density > Value | value | Base; 0.25 | 1 | Energy density of batteries in kWh/kg[battery]
Electrolyzer efficiency / kg[H2]/kWh[electricity] | Electrolyzer > Hydrogen yield per unit energy > Value | value | Base; 0.22 | 2 | Efficiency of electrolyzer for the conversion of electricity to hydrogen
Reverse osmosis recovery rate / - | Reverse Osmosis > Recovery rate > Value | value | Base; 80% | 3 | Recovery rate for purified water from seawater for reverse osmosis 