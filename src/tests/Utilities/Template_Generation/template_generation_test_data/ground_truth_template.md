# Functional Unit

Parameter | Unit
--- | ---
Functional Unit | str

# Input files to merge

Parameter | Value
--- | ---
<...> | str, optional

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

# Time

Parameter | Value
--- | ---
Years | dict

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

# Construction

Parameter | Value
--- | ---
<...> | int or float

# Financial Input Values

Parameter | Value
--- | ---
Fraction equity financing | int or float

# Inflation

Parameter | Value
--- | ---
Combined inflator | int or float
CI inflator | int or float
Inflation correction | int or float
Inflation factor full | ndarray

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

# Workflow

Parameter | Position
--- | ---
Hourly_Irradiation_Plugin | 201
Photovoltaic_Plugin | 202
Capital_Cost_Plugin | 400