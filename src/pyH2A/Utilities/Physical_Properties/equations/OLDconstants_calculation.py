from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.Physical_Properties.data.Constants import IDEAL_GAS_CONSTANT


def calculate_specific_gas_constants(species_data):

    specific_gas_constants = {}

    for species, data in species_data.items():

        specific_gas_constants[species] = Quantity(
            IDEAL_GAS_CONSTANT.unit['J/(mol*delta_K)']
            /
            data.molecular_weight.unit['kg/mol'],
            'J/(kg*delta_K)'
        )

    return specific_gas_constants