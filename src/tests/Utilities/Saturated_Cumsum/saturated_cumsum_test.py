import numpy as np
import pytest
from pyH2A.Utilities.saturated_cumsum import saturated_cumsum


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "requested_variation": np.array([1.0, -2.0, 3.0]),
                "nominal_lower_bound": np.array([1.1e-2, 1.0e-2, 0.9e-2]),
                "nominal_upper_bound": np.array([2.2, 2.0, 1.8]),
                "loss_per_cycle": 0,
                "initial_state": 2.0,
                "positive_variation_yield": 0.9,
                "negative_variation_yield": 0.9,
            },
            "expected": {
                "state": np.array([2.2,  0.009999999999999787, 1.8]),
                "instant_deficit": np.array([0, 0.028999999999999693, 0.]),
                "instant_excess": np.array([0.7777777777777776 , 0, 1.0111111111111108 ]),
                "cumulated_deficit": 0.028999999999999693,
                "cumulated_excess": 1.7888888888888883,
                "cumulated_charge": np.array([0.20000000000000018 , 0.20000000000000018 , 1.9900000000000004]),
                "cumulated_discharge": np.array([0, 2.1900000000000004,2.1900000000000004]),
            },
        },
    ],
)
def test_saturated_cumsum(case):
    '''Check saturated cumulative sum calculation'''

    inp = case["input"]
    expected = case["expected"]

    (
        state,
        instant_deficit,
        instant_excess,
        cumulated_deficit,
        cumulated_excess,
        cumulated_charge,
        cumulated_discharge,
    ) = saturated_cumsum(
        inp["requested_variation"],
        inp["nominal_lower_bound"],
        inp["nominal_upper_bound"],
        inp["loss_per_cycle"],
        inp["initial_state"],
        inp["positive_variation_yield"],
        inp["negative_variation_yield"],
    )

    obtained = {
        "state": state,
        "instant_deficit": instant_deficit,
        "instant_excess": instant_excess,
        "cumulated_deficit": cumulated_deficit,
        "cumulated_excess": cumulated_excess,
        "cumulated_charge": cumulated_charge,
        "cumulated_discharge": cumulated_discharge,
    }

    for name, expected_value in expected.items():
        np.testing.assert_allclose(
            obtained[name],
            expected_value,
            rtol=1e-12,
            atol=1e-12,
        )