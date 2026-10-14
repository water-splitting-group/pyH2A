# Input files to merge

Name | Value
--- | ---
PV-E Base Model | src/tests/e2e_lca/data/PV_E/PV_E_TEA_LCA.md
Default TEA + LCA | pyH2A.Config~Defaults_TEA_LCA.md

# Dependent variable

Name | Path to variable | Variable unit | Comment
--- | --- | --- | --- | ---
Global warming potential (GWP100) | Dependent Variables > Climate change: fossil - Global warming potential (GWP100) > Value | kg[$CO_{2}$-Eq]/kg[H2] | Target range provided in same units as dependent variable (kg[$CO_{2}$]/kg[H2])

# Optimization_Analysis

Name | Value | Comment
--- | --- | ---
Direction | minimize | Minimizing the dependent variable
Output File | src/tests/Analysis/Optimization/Optimization_Output.txt | Text file with optimization result
Maximum iterations | 20 | Maximum number of generations, kept small to limit the run time of the test
Population size | 5 | Population has 5 x 3 parameters = 15 members
Seed | 42 | Seed of random number generator for reproducible results
Polish | False | No polishing of the best member with L-BFGS-B

# Parameters - Optimization_Analysis

Name | Parameter path | Values | Comment
--- | --- | --- | --- 
Electrolyzer nominal power / MW | Electrolyzer > Nominal power > Value | 100 ; 1000 | Sizing of electrolyzer
Photovoltaic nominal power / MW | Photovoltaic > Nominal power > Value | 500 ; 3000 | Sizing of PV system
Battery design capacitiy / MWh | Battery > Design capacity > Value | 300 ; 4000 | Sizing of battery

# Methods - Optimization_Analysis

Name | Method Name | Arguments
--- | --- | ---
Convergence plot | plot_convergence | {'show': False, 'save': True}
