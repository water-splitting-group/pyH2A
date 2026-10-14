import pytest

from pyH2A.run_pyH2A import pyH2A
from pyH2A.Utilities.Unit_Handler import Quantity

def test_pv_e_monte_carlo():

    result = pyH2A(
        'src/tests/Analysis/Monte_Carlo/PV_E_Monte_Carlo_Test.md',
        'src/tests/Analysis/Monte_Carlo/'
    )

if __name__ == "__main__":
    test_pv_e_monte_carlo()