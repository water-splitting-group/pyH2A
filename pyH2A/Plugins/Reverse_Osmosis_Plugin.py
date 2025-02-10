import numpy as np
from pyH2A.Utilities.input_modification import insert

class Reverse_Osmosis_Plugin:
    def __init__(
            self, 
            dcf: dict,  # Dictionary containing input data
            print_info: bool  # Flag to control output verbosity
            ) -> None:
        """
        Initializes the Reverse Osmosis Plugin.

        Parameters:
        dcf (dict): Dictionary containing input data.
        print_info (bool): Flag to print processing information.
        """
        self.dcf: dict = dcf  # Store input data dictionary
        self.calculate_osmosis_power_demand()
        self.setup_inserts(print_info)

    def calculate_osmosis_power_demand(self) -> None:
        """
        Computes the annual reverse osmosis power demand and water usage metrics.
        """
        MOLAR_RATIO_WATER: float = 18.01528 / 2.016  # Molar ratio of water to hydrogen

        # Calculate fresh water demand based on hydrogen production
        mass_fresh_water_demand: np.ndarray = (
            self.dcf.inp['LCA Parameters Photovoltaic']['H2 produced (kg)']['Value'] * MOLAR_RATIO_WATER
        )  # Fresh water demand in kg

        volume_fresh_water_demand: np.ndarray = mass_fresh_water_demand / 997  # Convert to cubic meters
        self.total_volume_of_fresh_water: float = np.sum(volume_fresh_water_demand)  # Total fresh water used

        # Calculate sea water demand considering the recovery rate
        volume_sea_water_demand: np.ndarray = (
            volume_fresh_water_demand / self.dcf.inp['Reverse Osmosis']['Recovery Rate']['Value']
        )  # Sea water demand in cubic meters

        self.total_volume_of_sea_water: float = np.sum(volume_sea_water_demand)  # Total sea water demand

        # Calculate reverse osmosis power demand
        self.anual_reverse_osmosis_power_demand: np.ndarray = (
            self.dcf.inp['Reverse Osmosis']['Power Demand (kWh/m3)']['Value'] * volume_sea_water_demand
        )  # Power demand for reverse osmosis in kWh

        # Calculate mass of brine produced as a byproduct
        mass_brine: np.ndarray = mass_fresh_water_demand * 0.035  # Brine mass in kg (assuming 3.5% of fresh water mass)
        self.total_mass_brine: float = np.sum(mass_brine)  # Total brine mass

    def setup_inserts(
            self, 
            print_info: bool  # Flag to control output verbosity
            ) -> None:
        """
        Inserts calculated values into the data structure for further processing.

        Parameters:
        print_info (bool): Flag to print inserted values.
        """
        inserts: list[tuple[str, str, float | np.ndarray]] = [  # List of values to be inserted
            ('Technical Operating Parameters and Specifications', 'Reverse Osmosis Anual Power Demand (kWh)', self.anual_reverse_osmosis_power_demand),
            ('LCA Parameters Photovoltaic', 'Sea water demand (m3)', self.total_volume_of_sea_water),
            ('LCA Parameters Photovoltaic', 'Mass of brine (kg)', self.total_mass_brine),
            ('LCA Parameters Photovoltaic', 'Amount of fresh water (m3)', self.total_volume_of_fresh_water)
        ]

        # Insert values into the data structure
        for category, name, value in inserts:
            insert(self.dcf, category, name, 'Value', value, __name__, print_info=print_info)
