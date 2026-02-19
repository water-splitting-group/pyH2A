import numpy as np
from pyH2A.Utilities.Energy_Conversion import Energy, kWh, eV
from pyH2A.Utilities.input_modification import insert, process_table
from pyH2A.Utilities.Physical_Constants import Fluid_properties as FP

class Compression_Work_Plugin:
    ''' Calculating the power needed to compress a gas
    
    Parameters
    ----------
    Raw product gas > Pressure > Value : float
        Inlet pressure of the gas to be compressed (bar).
    Raw product gas > Temperature > Value : float
        Inlet temperature of the gas to be compressed (K).
        When more than one compressor is used, the gas is assumed to be cooled back to this temperature between two compression stages.        
    Raw product gas > Hydrogen molar fraction > Value : float
        Molar fraction of hydrogen in the gas to be compressed (-)
    Technical Operating Parameters and Specifications > Design Output per Day > Value : float
        Amount of hydrogen that needs to be compressed before any separation step
    Technical Operating Parameters and Specifications > Maximum Output at Gate > Value : float
        Amount of hydrogen effectively delivered after the separation step   
    Compressor train > Outlet pressure > Value : float
        Pressure of the compressed gas (bar).        
    Compressor train > Number of compression stages > Value : float
        Number of compressors in series to reach the final pressure (-).
    Compressor train > Polytropic coefficient > Value : float, optional
        Polytropic coefficient of the compression (-). Defaults to 1.4.
    Compressor train > Compressor efficiency > Value : float
        Compression work per shaft work provided to the compressor (-).          
    Compressor train > Combustion to shaft efficiency > Value : float
        Actual shaft work obtained per energy obtained from combustion (-).         
    Product gas properties > Hydrogen combustion enthalpy > Value : float, optional
        Combustion enthalpy of hydrogen (J/mol). Defaults to 285E3.          

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
    Energy self consumption > Electricity for compression > Value : float
        Mechanical power to drive the compressors shafts (W).          
    Energy self consumption > Required combustion power > Value : float
        Power from combustion needed to provide the necessary shaft work (W).         
    Energy self consumption > Hydrogen self consumption ratio > Value : float
        Amount of hydrogen required to provide the energy for compression, per amount of hydrogen produced after separation, but before the gate (-).            
    '''
    
    def __init__(self, dcf, print_info):    
        process_table(dcf.inp, 'Raw product gas', 'Value')
        process_table(dcf.inp, 'Compressor train', 'Value')
        process_table(dcf.inp, 'Product gas properties', 'Value')        

        if 'Polytropic coefficient' not in dcf.inp['Compressor train']:
            self.polytropic_coefficient = FP.IG_heat_capacity_ratio # ideal diatomic gas heat capacity ratio
            insert(dcf, 'Compressor train', 'Polytropic coefficient', 'Value', 
                self.polytropic_coefficient, __name__, print_info = print_info)
        else:
            self.polytropic_coefficient = dcf.inp['Compressor train']['Polytropic coefficient']['Value']

        if 'Hydrogen combustion enthalpy' not in dcf.inp['Product gas properties']:
            self.hydrogen_combustion_enthalpy = FP.H2_combustion_enthalpy_std
            insert(dcf, 'Product gas properties', 'Hydrogen combustion enthalpy', 'Value', 
                    self.hydrogen_combustion_enthalpy, __name__, print_info = print_info)
        else:
            self.hydrogen_combustion_enthalpy = dcf.inp['Product gas properties']['Hydrogen combustion enthalpy']['Value']            

        self.temperature_out(dcf)
        self.mixture_combustion_enthalpy(dcf)
        self.thermodynamic_compression_work(dcf)
        self.mechanical_work(dcf)
        self.combustion_to_mechanical_energy(dcf)
        self.Hydrogen_self_consumption(dcf)

        insert(dcf, 'Compressor train', 'Outlet temperature', 'Value', 
            self.outlet_temperature, __name__, print_info = print_info)        
        insert(dcf, 'Product gas properties', 'Mixture combustion enthalpy', 'Value', 
            self.combustion_enthalpy_per_mixture, __name__, print_info = print_info)
        insert(dcf, 'Energy self consumption', 'Thermodynamic compression work', 'Value', 
            self.compression_work, __name__, print_info = print_info)
        insert(dcf, 'Energy self consumption', 'Shaft work', 'Value', 
            self.shaft_work, __name__, print_info = print_info)
        insert(dcf, 'Energy self consumption', 'Electricity for compression', 'Value', 
            self.specific_compression_electricity, __name__, print_info = print_info)
        insert(dcf, 'Energy self consumption', 'Required combustion power', 'Value', 
            self.required_combustion_power, __name__, print_info = print_info)
        insert(dcf, 'Energy self consumption', 'Hydrogen self consumption ratio', 'Value', 
            self.hydrogen_self_consumption_ratio, __name__, print_info = print_info)               


    def temperature_out(self, dcf):
        '''Calculation of the outlet temperature of the compressor.
        '''
        
        self.outlet_temperature =  dcf.inp['Raw product gas']['Temperature']['Value'] * (dcf.inp['Compressor train']['Outlet pressure']['Value']/dcf.inp['Raw product gas']['Pressure']['Value'])**((self.polytropic_coefficient-1)/(dcf.inp['Compressor train']['Number of compression stages']['Value']*self.polytropic_coefficient))
        
    def mixture_combustion_enthalpy(self, dcf):
        '''Calculation of the combustion enthalpy per mole of mixture.
        '''

        self.combustion_enthalpy_per_mixture = dcf.inp['Raw product gas']['Hydrogen molar fraction']['Value'] * self.hydrogen_combustion_enthalpy    

    def thermodynamic_compression_work(self, dcf):
        '''Calculation of the power associated to the pressure increase of the gas.
        '''
        molar_flowrate_to_compress =  dcf.inp['Technical Operating Parameters and Specifications']['Design Output per Day']['Value']/(86400*FP.MW['H2']*dcf.inp['Raw product gas']['Hydrogen molar fraction']['Value']) # mol/s       
        self.compression_work = (dcf.inp['Compressor train']['Outlet pressure']['Value']/dcf.inp['Raw product gas']['Pressure']['Value'])**((self.polytropic_coefficient-1)/(self.polytropic_coefficient*dcf.inp['Compressor train']['Number of compression stages']['Value']))-1  
        self.compression_work = self.compression_work * FP.IG_constant * dcf.inp['Compressor train']['Number of compression stages']['Value'] * molar_flowrate_to_compress
        self.compression_work = self.compression_work * dcf.inp['Raw product gas']['Temperature']['Value'] 
        self.compression_work = self.compression_work / (self.polytropic_coefficient - 1)     
        
    def mechanical_work(self, dcf):
        '''Calculation of the mechanical power to drive the compressors shafts.
        '''
        
        self.shaft_work = self.compression_work / dcf.inp['Compressor train']['Compressor efficiency']['Value']   
        self.specific_compression_electricity = self.shaft_work/(3.6e6 * dcf.inp['Technical Operating Parameters and Specifications']['Maximum Output at Gate']['Value']/86400) 
        
    def combustion_to_mechanical_energy(self, dcf):
        '''Calculation of power from combustion needed to provide the necessary shaft work.
        '''
        
        self.required_combustion_power =  self.shaft_work / dcf.inp['Compressor train']['Combustion to shaft efficiency']['Value']          

    def Hydrogen_self_consumption(self, dcf):
        '''Calculation of the amount of hydrogen required to provide the energy for compression, per amount of compressed hydrogen.
        '''
        H2_molar_flowrate_at_gate = dcf.inp['Technical Operating Parameters and Specifications']['Maximum Output at Gate']['Value']/(86400*FP.MW['H2']) # mol/s       
        self.hydrogen_self_consumption_ratio = self.required_combustion_power / (H2_molar_flowrate_at_gate * self.hydrogen_combustion_enthalpy)