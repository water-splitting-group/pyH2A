# Workflow

Name                      | Type   | Description                                                                 | Position |
------------------------- | ------ | --------------------------------------------------------------------------- | -------- |
Hourly_Irradiation_Plugin | plugin | Plugin to calculate solar irradiation from typical meteorological year data | 0        |
PEC_Plugin                | plugin | Plugin to model photoelectrochemical water splitting                        | 2        |
Solar_Concentrator_Plugin | plugin | Plugin to model solar concentration                                         | 2        |
Multiple_Modules_Plugin   | plugin | Modelling of module plant modules, adjustment of labor requirement          | 3        |

# Display Parameters

Name  | Value   |
----- | ------- |
Name  | PEC     |
Color | darkred |

# Technical Operating Parameters and Specifications

Name                      | Value | Unit   | Path | Full Name                                                         |
------------------------- | ----- | ------ | ---- | ----------------------------------------------------------------- |
Operating Capacity Factor | 90%   | -      |      |
Plant Design Capacity     | 1,000 | kg/day |      |
Plant Modules             | 10    | -      | None | 10 identical modules, only affects labor requirement calculation. |

# Construction

Name             | Full Name           | Value | Unit |
---------------- | ------------------- | ----- | ---- |
capital perc 1st | Fraction of Capital | 100% | -    |

# Hourly Irradiation

Name | Value                                                                         | Comment                   |
---- | ----------------------------------------------------------------------------- | ------------------------- |
File | pyH2A.Lookup*Tables.Hourly_Irradiation_Data~tmy_34.859*-116.889_2006_2015.csv | Location: Dagget, CA, USA |

# Irradiance Area Parameters

Name                          | Value | Unit      | Comment                                                                                   |
----------------------------- | ----- | --------- | ----------------------------------------------------------------------------------------- |
Module Tilt                   | 0     | degree    | Two axis tracking, module tilt and array azimuth change are not relevant.                 |
Array Azimuth                 | 0     | degree    |
Nominal Operating Temperature | 45    | celsius   | Temperature is stabilized even under solar concentration through intrinsic water cooling. |
Mismatch Derating             | 98%   | -         |
Dirt Derating                 | 98%   | -         | Values taken from Chang 2020, analogues to silicon PV.                                    |
Temperature Coefficient       | 0     | -/delta_degC | No assumed efficiency loss with higher temperature.                                       |

# Solar Input

Name             | Value                                                           | Unit       | Path                                              | Comment                                                                                                                                   |
---------------- | --------------------------------------------------------------- | ---------- | ------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
Mean solar input | Hourly Irradiation > Mean solar input two axis tracking > Value | kWh_per_day/m2 | Solar Concentrator > Concentration factor > Value | Two axis tracking irradiation from hourly irradiation multiplied by solar concentration factor to give solar input incident on PEC cells. |

# Solar-to-Hydrogen Efficiency

Name | Value | Unit | Comment                                                                                                                                                                                                                                                                          |
---- | ----- | ---- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
STH  | 14%   | -    | Reference Kistler 2020, 14% STH (Note: vapor-fed device used in reference, techno-economic analysis assumes liquid phase design, no solar concentration); alternative reference: Idriss 2020, 18% STH at 15 suns, 13% STH at 200 suns (triple junction III-V cell based system). |

# PEC Cells

Name      | Value    | Unit | Comment                                                                                                                                                                                                                                |
--------- | -------- | ---- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
Cell Cost | 21,000.0 | USD/m2 | Price of III-V solar cells as reference, approximate USD/W to USD/m2 conversion formula: Cost (USD/W) _ conversion_efficiency (%) _ 1000 W/m2 = Cost (USD/m2), Reference: Horowitz 2018 (NREL), 70 USD/W, assuming 30% efficiency = 21,000 USD/m2. |
Lifetime  | 0.33     | year | Should consider operational lifetime (irradiation for only 8 h per day), baseline 1000 h operation time (reference: Kistler 2020), 3000 h total, 0.3 years.                                                                            |
Length    | 6        | m    | Based on sizing in Pinaud 2013.                                                                                                                                                                                                        |
Width     | 0.3      | m    | Based on sizing in Pinaud 2013.                                                                                                                                                                                                        |

# Solar Concentrator

Name                 | Value | Unit | Comment                                                                                                                                                        |
-------------------- | ----- | ---- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
Concentration Factor | 50    | -    | Concentration factor increased from 10 (Pinaud 2013) to 50 due to high PEC cell cost, within range of typical parabolic trough concentrators, see Gharbi 2011. |
Cost                 | 100   | USD/m2 | 100 USD/m2 parabolic trough concentrator cost based on Filas 2018.                                                                                               |

# Land Area Requirement

Name              | Value | Unit   | Comment                               |
----------------- | ----- | ------ | ------------------------------------- |
Cell Angle        | 35    | degree | Used for total land area calculation. |
South Spacing     | 6.71  | m      |
East/West Spacing | 17.3  | m      |

# Direct Capital Costs - Water Management

Name                           | Value  | Unit | Path                       | Comment               |
------------------------------ | ------ | ---- | -------------------------- | --------------------- |
Water pump                     | 213.0  | USD    | None                       | Based on Pinaud 2013. |
Water Manifold Piping          | 11.58  | USD    | PEC Cells > Number > Value |
Water Collection Piping        | 1.502  | USD    | PEC Cells > Number > Value |
Water Column Collection Piping | 1.1015 | USD    | PEC Cells > Number > Value |
Water Final Collection Piping  | 0.231  | USD    | PEC Cells > Number > Value |

# Direct Capital Costs - Gas Processing

Name                     | Value   | Unit | Path                       | Comment               |
------------------------ | ------- | ---- | -------------------------- | --------------------- |
Condenser                | 7,098.0 | USD    | None                       | Based on Pinaud 2013. |
Manifold Piping          | 11.58   | USD    | PEC Cells > Number > Value |
Collection Piping        | 1.502   | USD    | PEC Cells > Number > Value |
Column Collection Piping | 1.1015  | USD    | PEC Cells > Number > Value |
Final Collection Piping  | 0.231   | USD    | PEC Cells > Number > Value |

# Direct Capital Costs - Control System

Name                      | Path                       | Value    | Unit | Comment               |
------------------------- | -------------------------- | -------- | ---- | --------------------- |
PLC                       | None                       | 3,000.0  | USD    | Based on Pinaud 2013. |
Control Room Building     | None                       | 17,527.0 | USD    |
Control Room Wiring Panel | None                       | 3,000.0  | USD    |
Computer and Monitor      | None                       | 1,500.0  | USD    |
Labview Software          | None                       | 4,299.0  | USD    |
Water Level Controllers   | PEC Cells > Number > Value | 50.0     | USD    |
Pressure Sensors          | PEC Cells > Number > Value | 3.333    | USD    |
Hydrogen Area Sensors     | PEC Cells > Number > Value | 73.42    | USD    |
Hydrogen Flow Meter       | None                       | 5,500.0  | USD    |
Instrument Wiring         | PEC Cells > Number > Value | 0.252    | USD    |
Power Wiring              | PEC Cells > Number > Value | 0.1256   | USD    |
Conduit                   | PEC Cells > Number > Value | 3.759    | USD    |

# Direct Capital Costs - Installation Costs

Name                        | Path                                                          | Value | Unit | Comment               |
--------------------------- | ------------------------------------------------------------- | ----- | ---- | --------------------- |
Piping Installation         | PEC Cells > Number > Value                                    | 5.65  | USD    | Based on Pinaud 2013. |
Reactor Installation        | Non-Depreciable Capital Costs > Solar collection area > Value | 22.0  | USD    |
Pump Installation           | Direct Capital Costs - Water Management > Water pump > Value  | 30%   | USD    |
Gas processing installation | Direct Capital Costs - Gas Processing > Summed total > Value  | 30%   | USD    |
Control system installation | Direct Capital Costs - Control System > Summed total > Value  | 30%   | USD    |

# Indirect Capital Costs

Name                      | Path                                 | Value | Unit | Comment               |
------------------------- | ------------------------------------ | ----- | ---- | --------------------- |
Engineering and Design    | Direct Capital Costs > Total > Value | 7%    | USD    | Based on Pinaud 2013. |
Process Contingency       | Direct Capital Costs > Total > Value | 20%   | USD    |
Up-Front Permitting Costs | Direct Capital Costs > Total > Value | 0.5%  | USD    |
Site Preparation          | Direct Capital Costs > Total > Value | 1%    | USD    |

# Non-Depreciable Capital Costs

Name         | Value | Unit   | Comment                         |
------------ | ----- | ------ | ------------------------------- |
Cost of land | 500.0 | USD/acre | Land cost based on Pinaud 2013. |

# Fixed Operating Costs

Name              | Full Name                               | Value  | Unit   | Comment                                                                                                                                                              |
----------------- | --------------------------------------- | ------ | ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
area              | Area per staff                          | 60,000 | m2     | Based on Pinaud et al. 2013, smaller area per staff compared to PV+E and photocatalytic model due to smaller size of individual units, more connections and sensors. |
supervisor        | Shift supervisor                        | 1      | -      | Number of shift supervisors.                                                                                                                                         |
shifts            | Shifts                                  | 3      | -      | Number of shifts per day.                                                                                                                                            |
hourly labor cost | Burdened labor cost, including overhead | 50.0   | USD/hour |

# Other Fixed Operating Costs

Name         | Full Name                          | Path                                       | Value  | Unit     | Comment               |
------------ | ---------------------------------- | ------------------------------------------ | ------ | -------- | --------------------- |
g&a          | G&A rate                           | Fixed Operating Costs > Labor cost > Value | 20%    | USD      | Based on Pinaud 2013. |
property tax | Property tax and insurance rate    | Total Capital Costs > Inflated > Value     | 2%     | USD      |
repairs      | Production Maintenance and Repairs | Direct Capital Costs > Total > Value       | 0.5%   | USD      |
fees         | Licensing, Permits and Fees        | None                                       | 1000.0 | USD      |

# Utilities

Name                   | Usage_Value | Usage_Unit | Cost_Value                                                                          | Cost_Unit | Price_Conversion_Factor_Value | Price_Conversion_Factor_Unit | Comment                                                                                                       |
---------------------- | ----------- | ---------- | ----------------------------------------------------------------------------------- | --------- | ----------------------------- | ---------------------------- | ------------------------------------------------------------------------------------------------------------- |
Industrial Electricity | 0.16        | kWh/kg     | pyH2A.Lookup_Tables.Utility_Cost~Industrial_Electricity_AEO_2017_Reference_Case.csv | USD/GJ      | 0.0036                        | -                            | Electricity usage based on Pinaud 2013.                                                                       |
Process Water          | 2.369       | gal/kg     | 0.0023749510945008                                                                  | USD/gal     | 1.                            | None                         | Seawater reverse osmosis cost ca. 0.6 USD/m3 (equal to ca. 0.0023 USD/gal), based on Kibria 2021 and Driess 2021. |

# Unplanned Replacement

Name                  | Full Name                                                                                         | Path                                         | Value | Unit | Comment               |
--------------------- | ------------------------------------------------------------------------------------------------- | -------------------------------------------- | ----- | ---- | --------------------- |
unplanned replacement | Total Unplanned Replacement Capital Cost Factor (fraction of total direct depreciable costs/year) | Depreciable Capital Costs > Inflated > Value | 0.5%  | USD    | Based on Pinaud 2013. |
