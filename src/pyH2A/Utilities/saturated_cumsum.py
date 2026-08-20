import numpy as np
from numba import njit

@njit
def saturated_cumsum(
        requested_variation,
        nominal_lower_bound,
        nominal_upper_bound,
        loss_per_cycle,
        initial_state,
        positive_variation_yield=1.0,
        negative_variation_yield=1.0,
):
    """
    Function that calculates a cumulated sum subject to lower and upper bound curtailment, in the presence of charging/discharging yields.

    Parameters
    ----------
    requested_variation : ndarray
        Variation that would be observed in the absence of curtailment and yield (e.g. available charging energy).
    nominal_lower_bound : ndarray
        Lower saturation limit.
    nominal_upper_bound : ndarray
        Upper saturation limit.
    loss_per_cycle : float
        Fraction of the initial nominal upper bound that is loss when a full charge or discharge equivalent is performed
    initial_state : float
        Initial value of the cumulated sum.
    positive_variation_yield : float
        Fraction of accepted positive variation effectively stored.
    negative_variation_yield : float
        Fraction of withdrawn state effectively delivered.

    Returns
    -------
    state : ndarray
        Saturated cumulative state.
    instant_deficit : ndarray
        Part of the requested negative variation that could not be delivered. Counted positively
    instant_excess : ndarray
        Part of the positive variation that could not be accepted.
    cumulated_deficit : float
        sum of instant_deficit
    cumulated_excess : float
        sum of instant_excess
    cumulated_charge: array
        cumulated positive variations of the state 
    cumulated_charge: array
        cumulated absolute value of the negative variations of the state         
    """

    n = len(requested_variation)

    state = np.empty(n)

    instant_deficit = np.zeros(n)
    instant_excess = np.zeros(n)
    cumulated_charge = np.zeros(n)
    cumulated_discharge = np.zeros(n)

    cumulated_deficit = 0.0
    cumulated_excess = 0.0
    ageing_factor = 1.

    current_state = initial_state

    for i in range(n):

        # Positive contribution (e.g. battery charging)
        if requested_variation[i] > 0:
            incoming = requested_variation[i]
            # Remaining capacity
            available_capacity = nominal_upper_bound[i]*ageing_factor - current_state

            # Maximum incoming amount that can actually be accepted
            accepted_increase = min(
                incoming,
                available_capacity / positive_variation_yield
            )

            # Update state
            cumulated_charge[i] = accepted_increase * positive_variation_yield  
            current_state += cumulated_charge[i]

            # Amount that could not be stored
            instant_excess[i] = incoming - accepted_increase
            cumulated_excess += instant_excess[i]

        # Negative contribution (e.g. battery discharging)
        else:
            requested_decrease =  - requested_variation[i]

            # Amount available inside the storage
            available_storage = current_state - nominal_lower_bound[i]*ageing_factor

            # Maximum amount that can be delivered
            max_deliverable = (
                available_storage * negative_variation_yield
            )

            delivered = min(requested_decrease, max_deliverable)

            # Withdraw corresponding stored amount
            cumulated_discharge[i] = delivered / negative_variation_yield
            current_state -= cumulated_discharge[i]

            # Remaining unmet demand
            instant_deficit[i] = requested_decrease - delivered
            cumulated_deficit += instant_deficit[i]

        # calculation of the new capacity factor (relative to the initial one)
        ageing_factor -= (cumulated_charge[i] + cumulated_discharge[i])*loss_per_cycle/(2*nominal_upper_bound[0])

        state[i] = current_state

    cumulated_charge = np.cumsum(cumulated_charge)
    cumulated_discharge = np.cumsum(cumulated_discharge)

    return (
        state,
        instant_deficit,
        instant_excess,
        cumulated_deficit,
        cumulated_excess,
        cumulated_charge,
        cumulated_discharge
    )