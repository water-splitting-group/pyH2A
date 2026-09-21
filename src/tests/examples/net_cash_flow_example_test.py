import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
EXAMPLE_FILE = REPOSITORY_ROOT / 'examples' / 'net_cash_flow_PV_E_Base.py'


@pytest.fixture(scope='module')
def example():
    """Loading the net cash flow example by its file path, since the `examples` directory
    is not part of the pyH2A package."""

    spec = importlib.util.spec_from_file_location('net_cash_flow_PV_E_Base', EXAMPLE_FILE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    yield module

    del sys.modules[spec.name]


def test_net_cash_flow_example(example, tmp_path):
    """Check that the net cash flow example runs, saves a figure and returns cash flow data
    consistent with the levelized cost of hydrogen of the PV_E base case."""

    dcf = example.main(output_directory=tmp_path)

    assert (tmp_path / 'Net_Cash_Flow_Plot.png').is_file()

    cash_flow = example.read_cash_flow(dcf)

    # Cash flow arrays share their time axis with `Plant years relative`
    for key in ('net', 'cumulative', 'cumulative_discounted'):
        assert len(cash_flow[key]) == len(cash_flow['years'])

    np.testing.assert_allclose(cash_flow['cumulative'], np.cumsum(cash_flow['net']), atol=1e-6)

    # The levelized cost of product is defined by the net present value of the after-tax,
    # post-depreciation cash flow being zero
    assert cash_flow['cumulative_discounted'][-1] == pytest.approx(0.0, abs=1e-6)

    # Payback time is counted from the first year of construction
    payback_time = cash_flow['payback_time']
    idx = int(np.floor(payback_time))

    assert cash_flow['cumulative'][idx] < 0
    assert cash_flow['cumulative'][idx + 1] >= 0
