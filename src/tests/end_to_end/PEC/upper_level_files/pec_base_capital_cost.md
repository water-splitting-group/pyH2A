# Input files to merge

Name | Value
--- | ---
File A | src/tests/end_to_end/PEC/PEC_Base_test.md

# Direct Capital Costs - Water Management

Name | Value | Path | Unit | Comment 
--- | --- | --- | --- | --- 
Water pump | 215.0 | None | USD | Based on Pinaud 2013. 
Water manifold piping | 16.58 | {PEC Cells > Number > Value, -} | USD 
Water collection piping | 1.202 | {PEC Cells > Number > Value, -} | USD 
Water column collection piping | 1.5015 | {PEC Cells > Number > Value, -} | USD 
Water final collection piping | 0.531 | {PEC Cells > Number > Value, -} | USD 

# Direct Capital Costs - Gas Processing

Name | Value | Path | Unit | Comment 
--- | --- | --- | --- | --- 
Condenser | 7,198.0 | None | USD | Based on Pinaud 2013. 
Manifold piping | 12.58 | {PEC Cells > Number > Value, -} | USD 
Collection piping | 1.802 | {PEC Cells > Number > Value, -} | USD 
Column collection piping | 1.4015 | {PEC Cells > Number > Value, -} | USD 
Final collection piping | 0.531 | {PEC Cells > Number > Value, -} | USD 

# Direct Capital Costs - Control System

Name | Value | Path | Unit | Comment 
--- | --- | --- | --- | --- 
PLC | 3,100.0 | None | USD | Based on Pinaud 2013. 
Control room building | 17,627.0 | None | USD 
Control room wiring panel | 3,200.0 | None | USD 
Computer and monitor | 1,600.0 | None | USD 
Labview software | 4,399.0 | None | USD 
Hydrogen flow meter | 5,600.0 | None | USD 
Water level controllers | 60.0 | {PEC Cells > Number > Value, -} | USD 
Pressure sensors | 3.633 | {PEC Cells > Number > Value, -} | USD 
Hydrogen area sensors | 75.42 | {PEC Cells > Number > Value, -} | USD 
Instrument wiring | 0.552 | {PEC Cells > Number > Value, -} | USD 
Power wiring | 0.3256 | {PEC Cells > Number > Value, -} | USD 
Conduit | 3.959 | {PEC Cells > Number > Value, -} | USD 

# Direct Capital Costs - Installation Costs

Name | Value | Path | Unit | Comment 
--- | --- | --- | --- | --- 
Piping installation | 5.85 | {PEC Cells > Number > Value, -} | USD | Based on Pinaud 2013
Reactor installation | 24.0 | {Non-Depreciable Capital Costs > Solar collection area > Value, m2} | USD 
Pump installation | 40% | {Direct Capital Costs - Water Management > Water pump > Value, USD} | USD 
Gas processing installation | 40% | {Direct Capital Costs - Gas Processing > Summed total > Value, USD} | USD 
Control system installation | 40% | {Direct Capital Costs - Control System > Summed total > Value, USD} | USD 

# Indirect Capital Costs

Name | Value | Path | Unit | Comment 
--- | --- | --- | --- | --- 
Engineering and design | 8% | {Direct Capital Cost > Summed group total > Value, USD} | USD | Based on Pinaud 2013. 
Process contingency | 25% | {Direct Capital Cost > Summed group total > Value, USD} | USD 
Up-front permitting costs | 0.8% | {Direct Capital Cost > Summed group total > Value, USD} | USD 
Site preparation | 2% | {Direct Capital Cost > Summed group total > Value, USD} | USD 

# Non-Depreciable Capital Costs

Name | Value | Unit | Comment 
--- | --- | --- | --- 
Cost of land | 550.0 | USD/acre | Land cost based on Pinaud 2013
