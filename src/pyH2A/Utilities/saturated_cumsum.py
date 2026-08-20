import numpy as np
from numba import njit

@njit
def saturated_cumsum(raw_variations, 
                     lower_bound,                     
                     upper_bound,
                     initial_state,
                     ):
    '''
    Function that calculates a cumulated sum subject to lower and upper bound curtailment.
    Parameters
    ----------
    raw_variations: array
        variations whose cumulated sum is calculated
    lower_bound: array
        value below which the cumulated sum is not allowed to go.         
    upper_bound: array
        value above which the cumulated sum is not allowed to go.     
    initial_state: float
        starting vlaue of the cumulated sum.        

    Returns
    -------
    cumsum: array
        saturated cumulated sum
    instant_deficit: array
        part of the raw_variations that would lead below the lower threshold in the absence of curtailment. Counted positively
    instant_excess: array
        part of the raw_variations that would lead above the upper threshold in the absence of curtailment.
    cumulated_deficit: float
        sum of instant_deficit.
    cumulated_excess: float
        sum of instant_excess.
    '''
    cumsum = np.empty_like(raw_variations)
    instant_deficit = np.zeros_like(raw_variations)
    instant_excess = np.zeros_like(raw_variations)
    cumulated_deficit = 0
    cumulated_excess = 0
    sum = initial_state
    for i in range(raw_variations.size):
        sum += raw_variations[i]
        if sum > upper_bound[i]:
            instant_excess[i] = sum-upper_bound[i]
            cumulated_excess += instant_excess[i]
            sum = upper_bound[i]
        elif sum < lower_bound[i]:
            instant_deficit[i] = lower_bound[i]-sum # counting positively the missing amounts
            cumulated_deficit += instant_deficit[i] 
            sum = lower_bound[i]
        cumsum[i] = sum
    return cumsum, instant_deficit, instant_excess, cumulated_deficit, cumulated_excess

@njit
def saturated_cumsum_calendar_loss(
        requested_variation,
        lower_bound,
        upper_bound,
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
    lower_bound : ndarray
        Lower saturation limit.
    upper_bound : ndarray
        Upper saturation limit.
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
    throughput: array
        cumulated absolute value of the state variation
    """

    n = len(requested_variation)

    state = np.empty(n)

    instant_deficit = np.zeros(n)
    instant_excess = np.zeros(n)
    cumulated_charge = np.zeros(n)
    cumulated_discharge = np.zeros(n)

    cumulated_deficit = 0.0
    cumulated_excess = 0.0

    current_state = initial_state

    for i in range(n):

        # Positive contribution (e.g. battery charging)
        if requested_variation[i] > 0:
            incoming = requested_variation[i]
            # Remaining capacity
            available_capacity = upper_bound[i] - current_state

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
            available_storage = current_state - lower_bound[i]

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

@njit
def saturated_cumsum_cycle_loss(
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
    upper_bound : ndarray
        Upper saturation limit.
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
    throughput: array
        cumulated absolute value of the state variation
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