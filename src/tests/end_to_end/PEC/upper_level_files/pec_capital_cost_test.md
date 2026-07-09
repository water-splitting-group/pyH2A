# Input files to merge

Name | Value
--- | ---
File A | src/tests/end_to_end/PEC/PEC_Base_test.md

# Direct Capital Costs - Water Management

Name | Value | Path | Unit | Comment 
--- | --- | --- | --- | --- 
Water pump | 415.0 | None | USD | Based on Pinaud 2013. 
Water manifold piping | 36.58 | {PEC Cells > Number > Value, -} | USD 
Water collection piping | 3.202 | {PEC Cells > Number > Value, -} | USD 
Water column collection piping | 3.5015 | {PEC Cells > Number > Value, -} | USD 
Water final collection piping | 2.531 | {PEC Cells > Number > Value, -} | USD 

# Indirect Capital Costs

Name | Value | Path | Unit | Comment 
--- | --- | --- | --- | --- 
Engineering and design | 15% | {Direct Capital Cost > Summed group total > Value, USD} | USD | Based on Pinaud 2013. 
Process contingency | 35% | {Direct Capital Cost > Summed group total > Value, USD} | USD 
Up-front permitting costs | 1.8% | {Direct Capital Cost > Summed group total > Value, USD} | USD 
Site preparation | 5% | {Direct Capital Cost > Summed group total > Value, USD} | USD 

# Non-Depreciable Capital Costs

Name | Value | Unit | Comment 
--- | --- | --- | --- 
Cost of land | 1550.0 | USD/acre | Land cost based on Pinaud 2013
