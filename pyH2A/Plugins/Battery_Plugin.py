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

    def calculate_stored_power(self, unused_power):
        capacity = self.dcf.inp['Battery']['Capacity (kWh)']['Value']
        daily_unused_power = unused_power.reshape(-1, 24).sum(axis=1)
        daily_stored_power = np.minimum(daily_unused_power, capacity) * self.dcf.inp['Battery']['Round trip efficiency']['Value']
        return daily_stored_power

    def setup_inserts(self, stored_power, print_info):
        insert(self.dcf, 'Technical Operating Parameters and Specifications', 'Stored Power (kWh)', 'Value', np.sum(stored_power), __name__)
