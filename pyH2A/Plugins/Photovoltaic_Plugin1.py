from pyH2A.Utilities.input_modification import insert, process_table, file_import, read_textfile
import numpy as np
import os

class Photovoltaic_Plugin1:
    '''Simulation of hydrogen production using photovoltaic (PV) systems.

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
            dcf, 
            print_info
            ) -> None:
        # Initialize the plugin with the given data and perform calculations
        self.dcf = dcf
        self.process_input_data()
        self.load_irradiation_data()
        self.nominal_power = self.dcf.inp['Photovoltaic']['Nominal Power (kW)']['Value']
        self.calculate_amount_of_PV()
        self.calculate_area()
        self.calculate_plant_energy_generation()
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
            self.irradiation_data = read_textfile(self.dcf.inp['Irradiation Used']['Data']['Value'], delimiter='	')[:, 1]
        else:
            self.irradiation_data = self.dcf.inp['Irradiation Used']['Data']['Value']

    def calculate_amount_of_PV(
            self
            ) -> None:
        '''Calculate the number of photovoltaic (PV) modules required.
        '''
        power_per_module = self.dcf.inp['Photovoltaic']['Power per module (kW)']['Value']
        self.amount_of_PV_modules = np.ceil(self.nominal_power / power_per_module)
        self.power_generation = power_per_module * self.amount_of_PV_modules * np.sum(self.irradiation_data)
        print("self.amount_of_PV_modules:", self.amount_of_PV_modules)

    def calculate_area(
            self
            ) -> None:
        '''Calculate the land area required for the photovoltaic (PV) system.

        This method calculates the area in square meters (m^2) required for the PV system, assuming peak efficiency of 1000 W/m2 for the solar panels.
        '''
        # Calculate land area required for PV system
        peak_kW_per_m2 = self.dcf.inp['Photovoltaic']['Efficiency']['Value'] * 1.
        self.area_m2 = self.nominal_power / peak_kW_per_m2
        self.area_acres = self.area_m2 * 0.000247105

    def calculate_plant_energy_generation(
            self
            ) -> None:
        '''Calculate the yearly plant energy generation and active hours.
        '''
        min_energy_threshold = self.dcf.inp['Technical Operating Parameters and Specifications']['Plant Minimum Energy Threshold (kW)']["Value"]
        max_energy_threshold = self.dcf.inp['Technical Operating Parameters and Specifications']['Yearly Plant Maximum Energy Threshold (kW)']["Value"]
        plant_energy_generation = []
        self.plant_active_hours = []
        for year in self.dcf.operation_years:
            pv_loss = (1. - self.dcf.inp['Photovoltaic']['Power loss per year']['Value']) ** year
            nominal_irradiation_data = pv_loss * self.nominal_power * self.irradiation_data
            filtered_nominal_irradiation_data = nominal_irradiation_data[
                (nominal_irradiation_data >= min_energy_threshold) & 
                (nominal_irradiation_data <= max_energy_threshold[year])
            ]
            self.plant_active_hours.append(len(filtered_nominal_irradiation_data))
            plant_energy_generation.append(np.sum(filtered_nominal_irradiation_data))
        self.yearly_plant_energy_generation = np.array(plant_energy_generation)

    def setup_inserts(
            self, 
            print_info
            ) -> None:
        '''Prepare and insert output values into the data structure.

        Parameters
        ----------
        print_info : bool
            Flag to control whether the information should be printed.
        '''
        inserts = [
            ('Technical Operating Parameters and Specifications', 'Power Generation (kWh)', np.sum(self.power_generation)),
            ('Technical Operating Parameters and Specifications', 'Yearly Plant Energy Generation (kWh)', self.yearly_plant_energy_generation),
            ('Technical Operating Parameters and Specifications', 'Plant Active Hours', self.plant_active_hours),
            ('LCA Parameters Photovoltaic', 'Amount of PV modules', self.amount_of_PV_modules),
			('Non-Depreciable Capital Costs', 'Land required (acres)', self.area_acres),
			('Non-Depreciable Capital Costs', 'Solar Collection Area (m2)', self.area_m2)
        ]
        for category, name, value in inserts:
            insert(self.dcf, category, name, 'Value', value, __name__, print_info=print_info)