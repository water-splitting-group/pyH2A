from pyH2A.Utilities.input_modification import insert, process_table, read_textfile
import numpy as np

class Photovoltaic_Plugin1:
    '''Simulation of photovoltaic (PV) systems.

    Parameters
    ----------
    dcf : dict
        Discounted Cash Flow (DCF) input data.
    print_info : bool
        Flag to control whether the information should be printed.

    Notes
    -----
    This class performs various calculations related to PV systems, including power generation,
    area calculation, and energy generation. It also sets up the necessary inserts for reporting
    the results.
    '''

    def __init__(
            self, 
            dcf: dict,  # Input data dictionary containing all system parameters
            print_info: bool  # Flag to control output verbosity
            ) -> None:
        # Initialize the plugin with the given data and perform calculations
        self.dcf: dict = dcf  # Store the input dictionary
        self.process_input_data()
        self.load_irradiation_data()

        self.nominal_power: float = self.dcf.inp['Photovoltaic']['Nominal Power (kW)']['Value']  # Maximum power of the PV system (kW)

        self.calculate_amount_of_PV()
        self.calculate_area()
        self.calculate_plant_energy_generation()
        self.calculate_scaling_factor()
        self.setup_inserts(print_info)

    def process_input_data(
            self
            ) -> None:
        '''Process and validate input data tables.
        '''
        process_table(self.dcf.inp, 'Irradiation Used', 'Value')
        process_table(self.dcf.inp, 'Photovoltaic', 'Value')

    def load_irradiation_data(
            self
            ) -> None:
        '''Load hourly irradiation data from a file or array.
        '''
        if isinstance(self.dcf.inp['Irradiation Used']['Data']['Value'], str):
            self.irradiation_data: np.ndarray = read_textfile(self.dcf.inp['Irradiation Used']['Data']['Value'], delimiter='	')[:, 1]  # Load irradiation data from file
        else:
            self.irradiation_data: np.ndarray = self.dcf.inp['Irradiation Used']['Data']['Value']  # Directly use provided data array

    def calculate_amount_of_PV(
            self
            ) -> None:
        '''Calculate the number of photovoltaic (PV) modules required.
        '''
        power_per_module: float = self.dcf.inp['Photovoltaic']['Power per module (kW)']['Value']  # Power output per PV module (kW)
        self.amount_of_PV_modules: int = int(np.ceil(self.nominal_power / power_per_module))  # Total number of required PV modules
        self.power_generation: float = power_per_module * self.amount_of_PV_modules * np.sum(self.irradiation_data)  # Total power generation over time

        #print("self.amount_of_PV_modules:", self.amount_of_PV_modules)

    def calculate_area(
            self
            ) -> None:
        '''Calculate the land area required for the photovoltaic (PV) system.
        '''
        peak_kW_per_m2: float = self.dcf.inp['Photovoltaic']['Efficiency']['Value'] * 1.  # Power generation per square meter
        self.area_m2: float = self.nominal_power / peak_kW_per_m2  # Required area in square meters
        self.area_acres: float = self.area_m2 * 0.000247105  # Convert area to acres

    def calculate_plant_energy_generation(
            self
            ) -> None:
        '''Calculate the yearly plant energy generation and active hours.
        '''
        min_energy_threshold: np.ndarray = self.dcf.inp['Technical Operating Parameters and Specifications']['Yearly Plant Minimum Energy Threshold (kW)']["Value"]  # Min power limits per year
        max_energy_threshold: np.ndarray = self.dcf.inp['Technical Operating Parameters and Specifications']['Yearly Plant Maximum Energy Threshold (kW)']["Value"]  # Max power limits per year
        plant_energy_generation: list[float] = []  # List to store yearly energy generation
        plant_active_hours: list[int] = []  # List to store active hours per year

        for year in self.dcf.operation_years:
            pv_loss: float = (1. - self.dcf.inp['Photovoltaic']['Power loss per year']['Value']) ** year  # Power degradation per year
            print(pv_loss, self.nominal_power, min_energy_threshold[year], max_energy_threshold[year])
            
            nominal_irradiation_data: np.ndarray = pv_loss * self.nominal_power * self.irradiation_data  # Adjusted irradiation data
            
            filtered_nominal_irradiation_data: np.ndarray = nominal_irradiation_data[
                nominal_irradiation_data > min_energy_threshold[year]
            ]  # Remove values below the minimum threshold

            excess_energy: np.ndarray = filtered_nominal_irradiation_data[
                filtered_nominal_irradiation_data >= max_energy_threshold[year]
            ]  # Identify energy exceeding the max threshold

            excess_energy: float = np.sum(excess_energy) - len(excess_energy) * max_energy_threshold[year]  # Calculate total excess energy
            plant_active_hours.append(len(filtered_nominal_irradiation_data))  # Count active hours
            plant_energy_generation.append(np.sum(filtered_nominal_irradiation_data) - excess_energy)  # Compute net energy generation
        
        self.yearly_plant_energy_generation: np.ndarray = np.array(plant_energy_generation)  # Store yearly energy generation
        self.yearly_plant_active_hours: np.ndarray = np.array(plant_active_hours)  # Store active hours per year
        print("yearly power, active:", self.yearly_plant_energy_generation, self.yearly_plant_active_hours)

    def calculate_scaling_factor(
			self
			) -> None:
        '''Calculate the scaling factor based on system size and reference power.'''
        number_of_tenfold_increases: float = np.log10(
            self.dcf.inp['Electrolyzer']['Nominal Power (kW)']['Value'] /
            self.dcf.inp['Electrolyzer']['CAPEX Reference Power (kW)']['Value']
        )  # Compute logarithmic scale factor
        self.scaling_factor: float = self.dcf.inp['CAPEX Multiplier']['Multiplier']['Value'] ** number_of_tenfold_increases  # Final scaling factor

    def setup_inserts(
            self, 
            print_info: bool  # Flag to control output verbosity
            ) -> None:
        '''Prepare and insert output values into the data structure.
        '''
        inserts: list[tuple[str, str, float | np.ndarray]] = [  # Define list of values to insert
            ('Technical Operating Parameters and Specifications', 'Power Generation (kWh)', np.sum(self.power_generation)),
            ('Technical Operating Parameters and Specifications', 'Yearly Plant Energy Generation (kWh)', self.yearly_plant_energy_generation),
            ('Technical Operating Parameters and Specifications', 'Plant Active Hours', self.yearly_plant_active_hours),
			('Photovoltaic', 'Scaling Factor', self.scaling_factor),
            ('LCA Parameters Photovoltaic', 'Amount of PV modules', self.amount_of_PV_modules),
			('Non-Depreciable Capital Costs', 'Land required (acres)', self.area_acres),
			('Non-Depreciable Capital Costs', 'Solar Collection Area (m2)', self.area_m2)
        ]
        for category, name, value in inserts:
            insert(self.dcf, category, name, 'Value', value, __name__, print_info=print_info)  # Insert values into the data structure
