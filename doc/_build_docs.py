from src.pyH2A.Plugins.Battery_Plugin import Battery_Plugin
from src.pyH2A.Utilities.docstring_generation import generate_plugin_docstring

# generating docs for plugins
generate_plugin_docstring(Battery_Plugin, """Simulation of electricity storage using a battery. 
                          Simulation assumes that battery is charged and completely discharged every day. 
                          (no electricity storage across days, only one discharge per day, not multiple ones)""")
