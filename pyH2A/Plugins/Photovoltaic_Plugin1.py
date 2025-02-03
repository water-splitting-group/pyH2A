from pyH2A.Utilities.input_modification import insert, process_table, read_textfile
import numpy as np

class Photovoltaic_Plugin:
    def __init__(self, dcf):
        self.dcf = dcf
        self.process_input_data()
        self.calculate_power_generation()
        self.calculate_amount_of_PV()
        self.setup_inserts()

    def process_input_data(self):
        process_table(self.dcf.inp, 'Irradiation Used', 'Value')
        process_table(self.dcf.inp, 'Photovoltaic', 'Value')

    def calculate_power_generation(self):
        irradiation_data = self.load_irradiation_data()
        #self.power_generation = data * self.dcf.inp['Photovoltaic']['Nominal Power (kW)']['Value']
        self.threshold_data = self.load_threshold_data(f"opt-capacity_ratio-{self.dcf.inp['Irradiation Used']['Data']['Value']}")
        min_threshold = self.dcf.inp['Technical Operating Parameters and Specifications']['Plant Minimum Energy Threshold (kW)']
        max_threshold = self.dcf.inp['Technical Operating Parameters and Specifications']['Plant Maximum Energy Threshold (kW)']
        module_min_threshold, module_max_threshold, module_energy_generation = self.load_power_generation_optimum(max_threshold/min_threshold)
             

    def load_irradiation_data(self):
        if isinstance(self.dcf.inp['Irradiation Used']['Data']['Value'], str):
            return read_textfile(self.dcf.inp['Irradiation Used']['Data']['Value'], delimiter='	')[:, 1]
        else:
            return self.dcf.inp['Irradiation Used']['Data']['Value']
    
    def load_threshold_data(filename):
        return np.loadtxt(filename, delimiter=",")
    
    def load_power_generation_optimum(self, target):
        pos = np.searchsorted(self.threshold_data[:,0], target)
        if pos < len(self.threshold_data) and self.threshold_data[pos, 0] == target:
            return self.threshold_data[pos]
        if pos == 0:
            element1 = self.threshold_data[0]
            element2 = self.threshold_data[1]
        elif pos == len(self.threshold_data):
            element1 = self.threshold_data[pos-2]
            element2 = self.threshold_data[pos-1]
        else:
            element1 = self.threshold_data[pos-1]
            element2 = self.threshold_data[pos]
        b_thr = (element2[1]-element1[1])/(element2[0]-element1[0])*(target-element1[0])+element1[1]
        u_thr = (element2[2]-element1[2])/(element2[0]-element1[0])*(target-element1[0])+element1[2]
        area = (element2[3]-element1[3])/(element2[0]-element1[0])*(target-element1[0])+element1[3]
        return b_thr, u_thr, area

    def calculate_amount_of_PV(self):
        self.amount_of_PV_modules = np.ceil(self.dcf.inp['Photovoltaic']['Nominal Power (kW)']['Value'] / self.dcf.inp['Photovoltaic']['Power per module (kW)']['Value'])

    def setup_inserts(self):
        insert(self.dcf, 'Technical Operating Parameters and Specifications', 'Power Generation (kWh)', 'Value', np.sum(self.power_generation), __name__)
        insert(self.dcf, 'LCA Parameters Photovoltaic', 'Amount of PV modules', 'Value', self.amount_of_PV_modules, __name__)