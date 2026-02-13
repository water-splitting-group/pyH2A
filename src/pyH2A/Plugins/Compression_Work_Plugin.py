import numpy as np
from pyH2A.Utilities.Energy_Conversion import Energy, kWh, eV
from pyH2A.Utilities.input_modification import insert, process_table

class Compression_Work_Plugin:
    ''' Calculating the power needed to compress a gas
    Parameters
    ----------
    Compressor train > Inlet pressure > Value : float
        Inlet pressure of the gas to be compressed (bar).
    Compressor train > Outlet pressure > Value : float
        Pressure of the compressed gas (bar).        
    Compressor train > Number of compression stages > Value : float
        Number of compressors in series to reach the final pressure (-).
    Compressor train > Inlet temperature > Value : float
        Inlet temperature of the gas to be compressed (K).
        When more than one compressor is used, the gas is assumed to be cooled back to this temperature between two compression stages.
    Compressor train > Molar flowrate > Value : float
        Molar flowrate of gas to be compressed (mol/s).         
    Compressor train > Flowrate surplus for separation > Value : float
        Extra molar flowrate of gas, due to the internal use of product for separation processes (-). Defaults to 0.
        The flowrate to compress is Molar flowrate * (1+Flowrate surplus for separation), while the flowrate from which the energy production of the plant is calcualted remains equal to Molar flowrate
    Compressor train > Polytropic coefficient > Value : float
        Polytropic coefficient of the compression (-). Optional. Defaults to 1.4.
    Compressor train > Compressor efficiency > Value : float
        Compression work per shaft work provided to the compressor (-).          
    Compressor train > Combustion to shaft efficiency > Value : float
        Actual shaft work obtained per energy obtained from combustion (-).  
    Product gas properties > Hydrogen fraction in gas > Value : float
        Molar fraction of H2 in the gas to be compressed (-).        
    Product gas properties > Hydrogen combustion enthalpy > Value : float
        Combustion enthalpy of hydrogen (J/mol). Optional. Defaults to 285E3.          

    Returns
    -------
    Compressor train > Outlet temperature > Value : float
        Outlet temperature of each compressor of the train.  
    Product gas properties > Mixture combustion enthalpy > Value : float
        Combustion enthalpy (due to hydrogen) per mole of mixture (J/mol).
    Energy self consumption > Thermodynamic compression work > Value : float
        Power associated to the pressure increase of the gas (W).                      
    Energy self consumption > Shaft work > Value : float
        Mechanical power to drive the compressors shafts (W).            
    Energy self consumption > Required combustion power > Value : float
        Power from combustion needed to provide the necessary shaft work (W).         
    Energy self consumption > Hydrogen self consumption ratio > Value : float
        Amount of hydrogen required to provide the energy for compression, per amount of compressed hydrogen (-).            
    '''
    
    def __init__(self, dcf, print_info):    
        process_table(dcf.inp, 'Compressor train', 'Value')  

        if 'Polytropic coefficient' not in dcf.inp['Compressor train']:
            self.polytropic_coefficient = 1.4 # ideal diatomic gas heat capacity ratio
            insert(dcf, 'Compressor train', 'Polytropic coefficient', 'Value', 
                self.polytropic_coefficient, __name__, print_info = print_info)
        else:
            self.polytropic_coefficient = dcf.inp['Compressor train']['Polytropic coefficient']['Value']

        if 'Hydrogen combustion enthalpy' not in dcf.inp['Product gas properties']:
            self.hydrogen_combustion_enthalpy = 285e3 # at standard conditions of temperature and pressure
            insert(dcf, 'Product gas properties', 'Hydrogen combustion enthalpy', 'Value', 
                    self.hydrogen_combustion_enthalpy, __name__, print_info = print_info)
        else:
            self.hydrogen_combustion_enthalpy = dcf.inp['Compressor train']['Polytropic coefficient']['Value']            

        self.outlet_temperature(dcf)
        self.mixture_combustion_enthalpy(dcf)
        self.thermodynamic_compression_work(dcf)
        self.shaft_work(dcf)
        self.required_combustion_power(dcf)
        self.Hydrogen_self_consumption_ratio(dcf)

        insert(dcf, 'Compressor train', 'Outlet temperature', 'Value', 
            self.outlet_temperature, __name__, print_info = print_info)        
        insert(dcf, 'Product gas properties', 'Mixture combustion enthalpy', 'Value', 
            self.combustion_enthalpy_per_mixture, __name__, print_info = print_info)
        insert(dcf, 'Energy self consumption', 'Thermodynamic compression work', 'Value', 
            self.compression_work, __name__, print_info = print_info)
        insert(dcf, 'Energy self consumption', 'Shaft work', 'Value', 
            self.shaft_work, __name__, print_info = print_info)
        insert(dcf, 'Energy self consumption', 'Required combustion power', 'Value', 
            self.required_combustion_power, __name__, print_info = print_info)
        insert(dcf, 'Energy self consumption', 'Hydrogen self consumption ratio', 'Value', 
            self.hydrogen_self_consumption_ratio, __name__, print_info = print_info)               


    def outlet_temperature(self, dcf):
        '''Calculation of the outlet temperature of the compressor.
        '''
        
        self.outlet_temperature =  dcf.inp['Compressor train']['Inlet temperature']['Value'] * (dcf.inp['Compressor train']['Outlet pressure']['Value']/dcf.inp['Compressor train']['Inlet pressure']['Value'])**((self.polytropic_coefficient-1)/(dcf.inp['Compressor train']['Number of compression stages']['Value']*self.polytropic_coefficient))
        
    def mixture_combustion_enthalpy(self, dcf):
        '''Calculation of the combustion enthalpy per mole of mixture.
        '''

        self.combustion_enthalpy_per_mixture = dcf.inp['Product gas properties']['Hydrogen fraction in gas']['Value'] * self.hydrogen_combustion_enthalpy    

    def thermodynamic_compression_work(self, dcf):
        '''Calculation of the power associated to the pressure increase of the gas.
        '''
        
        self.compression_work = (dcf.inp['Compressor train']['Outlet pressure']['Value']/dcf.inp['Compressor train']['Inlet pressure']['Value'])**((self.polytropic_coefficient-1)/(self.polytropic_coefficient*dcf.inp['Compressor train']['Number of compression stages']['Value']))-1  
        self.compression_work = self.compression_work * 8.314 * dcf.inp['Compressor train']['Number of compression stages']['Value'] * dcf.inp['Compressor train']['Molar flowrate']['Value']  # 8.314 = ideal gas constant ; could be part of a universal constant file at some point
        self.compression_work = self.compression_work * dcf.inp['Compressor train']['Inlet temperature']['Value'] 
        self.compression_work = self.compression_work / (self.polytropic_coefficient - 1)
        if 'Flowrate surplus for separation' in dcf.inp['Compressor train']:
            self.compression_work = self.compression_work * (1 + dcf.inp['Compressor train']['Flowrate surplus for separation']['Value'])       
        
    def shaft_work(self, dcf):
        '''Calculation of the mechanical power to drive the compressors shafts.
        '''
        
        self.shaft_work = self.compression_work / dcf.inp['Compressor train']['Compressor efficiency']['Value']   
        
    def required_combustion_power(self, dcf):
        '''Calculation of power from combustion needed to provide the necessary shaft work.
        '''
        
        self.required_combustion_power =  self.shaft_work / dcf.inp['Compressor train']['Combustion to shaft efficiency']['Value']          

    def Hydrogen_self_consumption_ratio(self, dcf):
        '''Calculation of the amount of hydrogen required to provide the energy for compression, per amount of compressed hydrogen.
        '''
        
        self.hydrogen_self_consumption_ratio = self.required_combustion_power / (dcf.inp['Compressor train']['Molar flowrate']['Value'] * self.combustion_enthalpy_per_mixture)