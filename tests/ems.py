import numpy as np

def optimize_energy_usage_np(solar_power, P_min, P_max, battery_capacity, initial_soc, min_soc, max_soc, charge_efficiency=0.9, discharge_efficiency=0.9):
    """
    Optimized NumPy version for energy management.
    
    Parameters:
    - solar_power: NumPy array of hourly solar power generation (kW).
    - P_min: Minimum plant operating power (kW).
    - P_max: Maximum plant operating power (kW).
    - battery_capacity: Battery capacity (kWh).
    - initial_soc: Initial battery state of charge (%).
    - min_soc: Minimum SOC limit (%).
    - max_soc: Maximum SOC limit (%).
    - charge_efficiency: Charging efficiency (default 90%).
    - discharge_efficiency: Discharging efficiency (default 90%).
    
    Returns:
    - additional_used_power: Total extra power from battery (kWh).
    - unused_power: Total wasted energy (kWh).
    - additional_working_hours: Extra hours the plant could operate due to battery.
    """
    
    time_steps = len(solar_power)
    battery_soc = np.full(time_steps, initial_soc, dtype=np.float32)  # Initialize SOC array
    additional_used_power = np.zeros(time_steps, dtype=np.float32)
    unused_power = np.zeros(time_steps, dtype=np.float32)
    working_hours = np.zeros(time_steps, dtype=np.int32)

    # Compute surplus energy when solar > P_max
    surplus_energy = np.maximum(solar_power - P_max, 0)
    
    # Compute needed energy when solar < P_min
    deficit_energy = np.maximum(P_min - solar_power, 0)
    
    # Charging process (vectorized)
    battery_charge = np.minimum(surplus_energy, ((max_soc - battery_soc) / 100) * battery_capacity)
    battery_soc += (battery_charge / battery_capacity) * 100 * charge_efficiency
    unused_power += surplus_energy - battery_charge  # Remaining energy is wasted
    
    # Discharging process (vectorized)
    battery_discharge = np.minimum(deficit_energy, ((battery_soc - min_soc) / 100) * battery_capacity)
    battery_soc -= (battery_discharge / battery_capacity) * 100 / discharge_efficiency
    additional_used_power += battery_discharge
    working_hours[battery_discharge > 0] = 1  # Count extra working hours when battery helped
    
    return np.sum(additional_used_power), np.sum(unused_power), np.sum(working_hours)

# Example Usage
solar_power_data = np.loadtxt("tests/results/irradiation_data.txt") * 5000  # Load hourly solar power data (kW)
P_min = 500  # kW (minimum threshold)
P_max = 5000  # kW (maximum threshold)
battery_capacity = 4000  # kWh
initial_soc = 2  # Initial battery SOC in %
min_soc = 0  # Minimum allowed SOC %
max_soc = 100  # Maximum SOC %

# Call optimized function
additional_used_power, unused_power, additional_working_hours = optimize_energy_usage_np(
    solar_power_data, P_min, P_max, battery_capacity, initial_soc, min_soc, max_soc
)

print(f"Additional Used Power: {additional_used_power:.2f} kWh")
print(f"Unused Power: {unused_power:.2f} kWh")
print(f"Additional Working Hours: {additional_working_hours} hours")
