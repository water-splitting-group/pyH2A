from pyH2A.Plugins.Battery_Plugin import Battery_Plugin
from pyH2A.Plugins.Capital_Cost_Plugin import Capital_Cost_Plugin
from pyH2A.Plugins.Electrolyzer_Plugin import Electrolyzer_Plugin
from pyH2A.Plugins.Hourly_Irradiation_Plugin import Hourly_Irradiation_Plugin
from pyH2A.Plugins.Catalyst_Separation_Plugin import Catalyst_Separation_Plugin
from pyH2A.Plugins.Inflation_Plugin import Inflation_Plugin
from pyH2A.Plugins.Labor_Operating_Cost_Plugin import Labor_Operating_Cost_Plugin
from pyH2A.Plugins.Multiple_Modules_Plugin import Multiple_Modules_Plugin
from pyH2A.Plugins.Other_Fixed_Operating_Cost_Plugin import Other_Fixed_Operating_Cost_Plugin
from pyH2A.Plugins.PEC_Plugin import PEC_Plugin
from pyH2A.Plugins.Photocatalytic_Plugin import Photocatalytic_Plugin
from pyH2A.Plugins.Photovoltaic_Plugin import Photovoltaic_Plugin
from pyH2A.Plugins.Power_Management_Plugin import Power_Management_Plugin
from pyH2A.Plugins.Production_Plugin import Production_Plugin
from pyH2A.Plugins.Replacement_Plugin import Replacement_Plugin
from pyH2A.Plugins.Reverse_Osmosis_Plugin import Reverse_Osmosis_Plugin
from pyH2A.Plugins.Solar_Concentrator_Plugin import Solar_Concentrator_Plugin
from pyH2A.Plugins.Solar_Thermal_Plugin import Solar_Thermal_Plugin
from pyH2A.Plugins.Stored_Power_Electrolysis_Plugin import Stored_Power_Electrolysis_Plugin
from pyH2A.Plugins.Time_Plugin import Time_Plugin
from pyH2A.Plugins.Variable_Operating_Cost_Plugin import Variable_Operating_Cost_Plugin
from pyH2A.Utilities.docstring_generation import generate_plugin_docstring

# generating docs for plugins
generate_plugin_docstring(Battery_Plugin, """Simulation of electricity storage using a battery. 
                          Simulation assumes that battery is charged and completely discharged every day. 
                          (no electricity storage across days, only one discharge per day, not multiple ones).""")

generate_plugin_docstring(Capital_Cost_Plugin, "Calculation of Capital Cost.")
generate_plugin_docstring(Catalyst_Separation_Plugin, "Calculation of cost for catalyst separation (e.g. via nanofiltration).")
generate_plugin_docstring(Electrolyzer_Plugin, "Simulation of hydrogen production using electrolysis.")
generate_plugin_docstring(Hourly_Irradiation_Plugin, "Calculation of hourly and mean daily irradiation data with different module configurations.")
generate_plugin_docstring(Inflation_Plugin, "Generation of a the necessary inflation-related quantities for other plugins.")
generate_plugin_docstring(Labor_Operating_Cost_Plugin, "Calculation of yearly Labor operating costs.")
generate_plugin_docstring(Multiple_Modules_Plugin, """
                                Simulating mutliple plant modules which are operated together, assuming that only labor cost is reduced. 
                                Calculation of required labor to operate all modules, scaling down labor requirement to one module for subsequent calculations.""")
generate_plugin_docstring(Other_Fixed_Operating_Cost_Plugin, "Calculation of yearly fixed operating costs.")
generate_plugin_docstring(PEC_Plugin, "Simulating H2 production using photoelectrochemical water splitting.")
generate_plugin_docstring(Photocatalytic_Plugin, "Simulating H2 production using photocatalytic water splitting in plastic baggie reactors.")
generate_plugin_docstring(Photovoltaic_Plugin, "Simulation of electricity production using PV.")
generate_plugin_docstring(Power_Management_Plugin, "Management of electricity production and consumption.")
generate_plugin_docstring(Production_Plugin, "Calculation of plant output.")
generate_plugin_docstring(Replacement_Plugin, "Calculating yearly overall replacement costs based on one-time replacement costs and frequency.")
generate_plugin_docstring(Reverse_Osmosis_Plugin, "Simulation of purified water production using reverse osmosis.")
generate_plugin_docstring(Solar_Concentrator_Plugin, "Simulation of solar concentration (used in combination with PEC cells).")
generate_plugin_docstring(Solar_Thermal_Plugin, "Simulation of hydrogen production using solar thermal water splitting.")
generate_plugin_docstring(Stored_Power_Electrolysis_Plugin, "Simulation of hydrogen production using electrolysis.")
generate_plugin_docstring(Time_Plugin, """
                          Generation of a unique dictionary contianing all the necessary time-related arrays and values for other plugins.
                                      All the quantities are dimensionless, no conversion being expected, and the years play the role of indexes rather than durations.
                          """)
generate_plugin_docstring(Variable_Operating_Cost_Plugin, "Calculation of variable operating costs.")
