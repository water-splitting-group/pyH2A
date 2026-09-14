from pyH2A.Utilities.Unit_Handler.quantity import Quantity

IDEAL_GAS_CONSTANT = Quantity(8.314, 'J/(mol*delta_K)')

IDEAL_GAS_MONOATOMIC_CV = Quantity(1.5, 'J/(mol*delta_K)')
IDEAL_GAS_MONOATOMIC_CP = Quantity(2.5, 'J/(mol*delta_K)')

IDEAL_GAS_DIATOMIC_CV = Quantity(2.5, 'J/(mol*delta_K)')
IDEAL_GAS_DIATOMIC_CP = Quantity(3.5, 'J/(mol*delta_K)')

IDEAL_GAS_MONOATOMIC_HEAT_CAPACITY_RATIO = Quantity(5/3, '-')
IDEAL_GAS_DIATOMIC_HEAT_CAPACITY_RATIO = Quantity(7/5, '-')