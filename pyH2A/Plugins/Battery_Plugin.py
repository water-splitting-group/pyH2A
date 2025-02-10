from pyH2A.Utilities.input_modification import insert, process_table, read_textfile
import numpy as np

class Battery_Plugin:
    def __init__(self, dcf, print_info):
        self.dcf = dcf
        self.process_input_data()    

    def process_input_data(
            self,
            ) -> None:
        process_table(self.dcf.inp, 'Battery', 'Value')

    def calculate_stored_power(self):
        yearly_additional_energy = []
        yearly_additional_working_hours = []
        for plant_hourly_energy_demand_and_excess in self.dcf['Technical Operating Parameters and Specifications', 'Yearly Plant Hourly Energy Demand And Excess']['Value']:
            additional_energy = 0
            additional_working_hours = 0
            current_charge = 0
            charging = True
            for i in range()
        self.dcf.inp['Battery']['Capacity (kWh)']['Value']
        self.dcf.inp['Battery']['Round trip efficiency']['Value']

    def setup_inserts(self, stored_power, print_info):
        insert(self.dcf, 'Technical Operating Parameters and Specifications', 'Stored Power (kWh)', 'Value', np.sum(stored_power), __name__)
