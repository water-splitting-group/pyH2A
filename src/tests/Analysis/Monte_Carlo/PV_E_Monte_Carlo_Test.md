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
Samples | 50 | Number of samples in Monte Carlo simulation.
Random seed | 2026 | Seed of the random number generator, makes the sampled parameter values reproducible.
Output File | src/tests/Analysis/Monte_Carlo/Monte_Carlo_Results.npz | NumPy file in which the results are saved together with their metadata.

# Parameters - Monte_Carlo_Analysis

Name | Parameter path | Type | Values | Comment
--- | --- | --- | --- | --- 
PV efficiency / - | Photovoltaic > Efficiency > Value | value | Base; 0.3 | Efficiency of PV panels, affects required amount of solar panels
Battery energy density / kWh/kg[battery] | Battery > Energy density > Value | value | Base; 0.25 | Energy density of batteries in kWh/kg[battery]
Electrolyzer efficiency / kg[H2]/kWh[electricity] | Electrolyzer > Hydrogen yield per unit energy > Value | value | Base; 0.022 | Efficiency of electrolyzer for the conversion of electricity to hydrogen
Reverse osmosis recovery rate / - | Reverse Osmosis > Recovery rate > Value | value | Base; 80% | Recovery rate for purified water from seawater for reverse osmosis 
PV power loss per year (factor) / - | Photovoltaic > Power loss per year > Value | factor | Base; 0.5 | Factor by which the yearly power loss of the PV panels is multiplied (base: factor of 1)

# Methods - Monte_Carlo_Analysis

Name | Method Name | Arguments
--- | --- | ---
complete_histogram | plot_complete_histogram | {'save': True, 'pdf': False, 'dpi': 100}
colored_scatter | plot_colored_scatter | {'save': True, 'pdf': False, 'dpi': 100, 'grid_points': 5}
colored_scatter_3D | plot_colored_scatter_3D | {'save': True, 'pdf': False, 'dpi': 100}
distance_histogram | plot_distance_histogram | Arguments - MC Analysis - distance_histogram
distance_cost_relationship | plot_distance_cost_relationship | Arguments - MC Analysis - distance_cost
target_parameters_by_distance | plot_target_parameters_by_distance | {'save': True, 'pdf': False, 'dpi': 100}

# Arguments - MC Analysis - distance_histogram

Name | Value
--- | ---
save | True
pdf | False
dpi | 100
xlabel | True
mu_x | 0.85
mu_y | 0.6
plot_kwargs | {'fig_width': 13, 'fig_height': 3, 'left': 0.07, 'right': 0.37, 'bottom': 0.2, 'top': 0.85}
table_kwargs | {'colWidths': [1.35, 0.25, 0.12, 0.25], 'fontsize': 11}

# Arguments - MC Analysis - distance_cost

Name | Value
--- | ---
save | True
pdf | False
dpi | 100
plot_kwargs | {'fig_width': 13, 'fig_height': 5.5, 'left': 0.08, 'right': 0.45, 'bottom': 0.11, 'top': 0.95}
table_kwargs | {'xpos': 1.05, 'ypos': 0.3, 'height': 0.45, 'fontsize': 11, 'colWidths': [0.95, 0.17, 0.08, 0.17]}
