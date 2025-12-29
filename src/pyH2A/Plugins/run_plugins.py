from Catalyst_Separation_Plugin import Catalyst_Separation_Plugin
import numpy as np

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

    print(">>> Creating Catalyst_Separation_Plugin <<<")
    plugin = Catalyst_Separation_Plugin(dcf_catalyst_separation_plugin, print_info=True)

    print("\n>>> RESULT <<<")
    print("Yearly filtration volume (m3):", plugin.yearly_filtration_volume_m3)
    print("Yearly separation cost ($):", plugin.yearly_cost)