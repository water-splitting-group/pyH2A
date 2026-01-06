from Catalyst_Separation_Plugin import Catalyst_Separation_Plugin
import numpy as np

from Fixed_Operating_Cost_Plugin import Fixed_Operating_Cost_Plugin

# ---- minimal fake DCF object ----
class DummyDCF_FIXED_OPERATING_COST_PLUGIN:
    def __init__(self):
        self.labor_inflator = 1.1
        self.combined_inflator = 1.05
        self.inp = {
            'Fixed Operating Costs': {
                'staff': {'Value': 10, 'unit': 'persons'},
                'hourly labor cost': {'Value': 50.0, 'unit': '$/hr'}
            },
            'Other Fixed Operating Cost': {
                'Insurance': {'Value': 5000, 'unit': '$'},
                'Maintenance': {'Value': 10000, 'unit': '$'}
            }
        }

# ---- minimal fake DCF object ----
class DummyDCF_CATALYST_SEPARATION_PLUGIN:
    def __init__(self):
        self.inp = {
            'Water Volume': {
                'Volume (liters)': {
                    'Value': 100_000
                }
            },
            'Catalyst': {
                'Lifetime (years)': {
                    'Value': 1
                }
            },
            'Catalyst Separation': {
                'Filtration cost ($/m3)': {
                    'Value': 0.24
                }
            }
        }


# ---- run plugin directly ----
if __name__ == "__main__":
    dcf_catalyst_separation_plugin = DummyDCF_CATALYST_SEPARATION_PLUGIN()
    dcf_fixed_cost_plugin = DummyDCF_FIXED_OPERATING_COST_PLUGIN()

    print(">>> Creating Catalyst_Separation_Plugin <<<")
    plugin = Catalyst_Separation_Plugin(dcf_catalyst_separation_plugin, print_info=True)

    print("\n>>> RESULT <<<")
    print("Yearly filtration volume (m3):", plugin.yearly_filtration_volume_m3)
    print("Yearly separation cost ($):", plugin.yearly_cost)


    print(">>> Creating Fixed_Operating_Cost_Plugin <<<")
    plugin = Fixed_Operating_Cost_Plugin(dcf_fixed_cost_plugin, print_info=True)

    print("\n>>> RESULT <<<")
    print("Labor Cost - Uninflated ($):", plugin.labor_uninflated)
    print("Labor Cost - Inflated ($):", plugin.labor)
    print("Other Fixed Operating Cost ($):", plugin.other)
    print("Total Fixed Operating Cost ($):", plugin.labor + plugin.other)