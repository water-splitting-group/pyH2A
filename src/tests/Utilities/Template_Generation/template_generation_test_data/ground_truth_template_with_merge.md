# Construction

Parameter | Value
--- | ---
<...> | int or float

# Hourly Irradiation

Parameter | Value
--- | ---
File | str

# Irradiance Area Parameters

Parameter | Value
--- | ---
Module tilt | int or float, optional
Array azimuth | int or float
Nominal operating temperature | int or float
Mismatch derating | int or float
Dirt derating | int or float
Temperature coefficient | int or float

# Irradiation Used

Parameter | Value
--- | ---
Data | str or ndarray

# Photovoltaic

Parameter | Value
--- | ---
Nominal power | int or float
Power loss per year | int or float
Efficiency | int or float

# Technical Operating Parameters and Specifications

Parameter | Value
--- | ---
Plant design capacity | int or float, optional
Design output by year | ndarray, optional
Operating capacity factor | int or float
Fraction of output that reaches gate | float

# <...> Direct Capital Cost <...>

Parameter | Value
--- | ---
<...> | int or float, optional

# <...> Indirect Capital Cost <...>

Parameter | Value
--- | ---
<...> | int or float, optional

# Non-Depreciable Capital Costs

Parameter | Value
--- | ---
Cost of land | int or float

# <...> Other Non-Depreciable Capital Cost <...>

Parameter | Value
--- | ---
<...> | int or float, optional

# Planned Replacement

Parameter | Frequency_Value | Cost_Value
--- | --- | ---
<...> | int or float, optional | int or float, optional

# <...> Unplanned Replacement <...>

Parameter | Value
--- | ---
<...> | int or float, optional

# Fixed Operating Costs

Parameter | Value
--- | ---
Staff | int or float
Hourly labor cost | int or float

# <...> Other Fixed Operating Cost <...>

Parameter | Value
--- | ---
<...> | int or float, optional

# Utilities

Parameter | Cost_Value | Usage_Value | Price_Conversion_Factor_Value
--- | --- | --- | ---
<...> | int or float or str or ndarray, optional | int or float, optional | int or float, optional

# <...> Other Variable Operating Cost <...>

Parameter | Value
--- | ---
<...> | int or float or ndarray, optional

# Monte_Carlo_Analysis

Parameter | Value
--- | ---
Samples | int
Target Price Range ($) | str
Output File | str, optional
Input File | str, optional

# Parameters - Monte_Carlo_Analysis

Parameter | Name | Type | Values | File Index
--- | --- | --- | --- | ---
<...> | str | str | str | int, optional

# Input files to merge

Parameter | Value
--- | ---
Default TEA | pyH2A.Config~Defaults_TEA.md

# Workflow

Parameter | Position
--- | ---
Hourly_Irradiation_Plugin | 201
Photovoltaic_Plugin | 202