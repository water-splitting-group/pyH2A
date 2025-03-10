from pyH2A.Utilities.input_modification import hourly_to_daily_power, insert
from pyH2A.Plugins.Plugin import Plugin
from pyH2A.DiscountedCashFlow import DiscountedCashFlow
import numpy as np
import logging

class ElectrolyzerPlugin(Plugin):
    '''Simulation of hydrogen production using electrolysis.

    Parameters
    ----------
    Financial Input Values > construction time > Value : int
        Construction time of hydrogen production plant in years.
    CAPEX Multiplier > Multiplier > Value : float
        Multiplier to describe cost reduction of electrolysis CAPEX for every ten-fold
        increase of power relative to CAPEX reference power. Based on the multiplier the CAPEX
        scaling factor is calculated as: multiplier ^ (number of ten-fold increases). A value
        of 1 leads to no CAPEX reduction, a value < 1 enables cost reduction.
    Electrolyzer > Nominal Power (kW) > Value : float
        Nominal power of electrolyzer in kW.
    Electrolyzer > CAPEX Reference Power (kW) > Value : float
        Reference power of electrolyzer in kW for cost reduction calculation.
    Electrolyzer > Power requirement increase per year > Value : float
        Electrolyzer power requirement increase per year due to stack degradation. Percentage 
        or value > 0. Increase calculated as: (1 + increase per year) ^ year.
    Electrolyzer > Minimum capacity > Value : float
        Minimum capacity required for electrolyzer operation. Percentage or value between 0 and 1.
    Electrolyzer > Conversion efficiency (kg H2/kWh) > Value : float
        Electrical conversion efficiency of electrolyzer in (kg H2)/kWh.
    Electrolyzer > Replacement time (h) > Value : float
        Operating time in hours before stack replacement of electrolyzer is required.
    Power Generation > Available Power (hourly, kWh) > Value : dict
        Available power, hourly basis, dictionary of years (in kWh).

    Returns
    -------
    Technical Operating Parameters and Specifications > Plant Design Capacity (kg of H2/day) > Value : nd.array
        Plant design capacity in (kg of H2)/day calculated from installed 
        electrolysis power capacity and hourly power generation data.
    Technical Operating Parameters and Specifications >	Operating Capacity Factor (%) > Value : float
        Operating capacity factor is set to 1 (100%).
    Planned Replacement > Electrolyzer Stack Replacement > Frequency (years) : float
        Frequency of electrolyzer stack replacements in years, calculated from replacement time and hourly
        irradiation data.
    Electrolyzer > Scaling Factor > Value : float
        CAPEX scaling factor for electrolyzer calculated based on CAPEX multiplier, 
        reference and nominal power.
    Electrolyzer > Yearly Operation Data > Value : nd.array
        Yearly operation data of electrolyzer in (year, H2 produced, electrolyzer capacity) format.
    Electrolyzer > H2 Production (yearly, kg) > Value : nd.array
        Yearly hydrogen production in kg.
    Power Generation > Available Power (hourly, kWh) > Value : dict
        Available power (hourly, kWh) after subtracting power consumed by electrolyzer. 
        (dictionary of years).
    Power Generation > Available Power (daily, kWh) > Value : dict
        Available power (daily, kWh) after subtracting power consumed by electrolyzer.
    '''

    def __init__(
            self, 
            dcf: DiscountedCashFlow
            ) -> None:
        super().__init__(dcf)

        self.logger: logging.Logger = logging.getLogger("pyH2A.Plugins.Hydrogen.ElectrolyserPlugin")
        self.logger.info("Starting ElectrolyserPlugin")

        table_keys = ['Financial Input Values', 'CAPEX Multiplier', 'Electrolyzer', 'Power Generation']
        self.process_table(table_keys)
        self.run_plugin()
        self.insert_table()

    def run_plugin(
            self
            ) -> None:
        tea = ElectrolyserPluginTEA(self)
        lca = ElectrolyserPluginLCA(self)

        tea.calculate_H2_production()
        lca.calculate_h2_production()
        tea.calculate_replacement_frequency()
        lca.calculate_production_maintenance()
        tea.calculate_scaling_factors()

class ElectrolyserPluginTEA:
    '''Handles life-cycle assessment (LCA) calculations for the electrolyser plugin.
	'''
    def __init__(
			self,
			plugin: ElectrolyzerPlugin
			) -> None:
        self.plugin: ElectrolyzerPlugin = plugin

    def calculate_H2_production(
            self
            ) -> None:
        '''Using hourly power generation data and electrolyzer parameters,
        H2 production is calculated.
        '''

        power_generation_yearly_data: dict[np.ndarray] = self.plugin.dcf.inp['Power Generation']['Available Power (hourly, kWh)']['Value']

        yearly_data: list = []
        yearly_data_unused_power: dict = {}
        yearly_data_unused_power_daily: dict = {}

        for year in self.plugin.dcf.operation_years:

            power_generation: np.ndarray = power_generation_yearly_data[year]

            (
                electrolyzer_power_demand, 
                power_increase
            ) = calculate_electrolyzer_power_demand(
                self.plugin.dcf.inp['Electrolyzer']['Power requirement increase per year']['Value'],
                self.plugin.dcf.inp['Electrolyzer']['Nominal Power (kW)']['Value'],
                year
            )

            electrolyzer_power_demand *= np.ones(len(power_generation))
            electrolyzer_power_consumption = np.amin(np.c_[power_generation, electrolyzer_power_demand], axis = 1)

            threshold = self.plugin.dcf.inp['Electrolyzer']['Minimum capacity']['Value']
            electrolyzer_capacity = electrolyzer_power_consumption / electrolyzer_power_demand
            electrolyzer_capacity[electrolyzer_capacity > threshold] = 1
            electrolyzer_capacity[electrolyzer_capacity <= threshold] = 0

            electrolyzer_power_consumption *= electrolyzer_capacity

            h2_produced = calculate_hydrogen_production(
                electrolyzer_power_consumption,
                self.plugin.dcf.inp['Electrolyzer']['Conversion efficiency (kg H2/kWh)']['Value'],
                power_increase
            )
            
            yearly_data.append([year, np.sum(h2_produced), np.sum(electrolyzer_capacity)])

            # Calculation of unused power
            unused_power = power_generation - electrolyzer_power_consumption
            yearly_data_unused_power[year] = unused_power
            yearly_data_unused_power_daily[year] = hourly_to_daily_power(unused_power)

        yearly_data: np.ndarray = np.asarray(yearly_data)
        self.plugin.operation_hours = yearly_data[:,2]
        self.plugin.h2_production = np.concatenate([
            np.zeros(self.plugin.dcf.inp['Financial Input Values']['construction time']['Value']), 
            yearly_data[:,1]
        ])

        self.plugin.insert_queue.extend([
            ('Electrolyzer','H2 Production (yearly, kg)', self.plugin.h2_production),
            ('Technical Operating Parameters and Specifications', 'Plant Design Capacity (kg of H2/day)', self.plugin.h2_production/365.),
            ('Technical Operating Parameters and Specifications', 'Operating Capacity Factor (%)', 1.),
            ('Electrolyzer', 'Yearly Operation Data', yearly_data),
            ('Power Generation', 'Available Power (hourly, kWh)', yearly_data_unused_power),
            ('Power Generation', 'Available Power (daily, kWh)', yearly_data_unused_power_daily)
        ])

    def calculate_scaling_factors(
            self
            ) -> None:
        '''Calculation of electrolyzer CAPEX scaling factors.
        '''
        electrolyzer_scaling_factor = self.scaling_factor(
            self.plugin.dcf.inp['Electrolyzer']['Nominal Power (kW)']['Value'], 
            self.plugin.dcf.inp['Electrolyzer']['CAPEX Reference Power (kW)']['Value']
        )
        self.plugin.insert_queue.append(('Electrolyzer', 'Scaling Factor', electrolyzer_scaling_factor))
        
    def scaling_factor(
            self, 
            power, 
            reference
            ) -> None:
        '''Calculation of CAPEX scaling factor based on nominal and reference power.
        '''
        number_of_tenfold_increases = np.log10(power/reference)

        return self.plugin.dcf.inp['CAPEX Multiplier']['Multiplier']['Value'] ** number_of_tenfold_increases
    
    def calculate_replacement_frequency(
            self
            ) -> None:
        '''Calculation of stack replacement frequency for electrolyzer.
        '''
        replacement_frequency, self.plugin.number_of_replacements = calculate_stack_replacement(
            self.plugin.operation_hours, 
            self.plugin.dcf.inp['Electrolyzer']['Replacement time (h)']['Value']
        )
        insert(self.plugin.dcf, 
            'Planned Replacement', 'Electrolyzer Stack Replacement', 'Frequency (years)', replacement_frequency, 
            __name__, print_info = self.plugin.dcf.print_info, add_processed = False, insert_path = False
        )

class ElectrolyserPluginLCA:

    def __init__(
            self, 
            plugin: ElectrolyzerPlugin
            ) -> None:
        self.plugin = plugin

    def calculate_production_maintenance(
            self
            ) -> None:
        production_maintenance_electrolyser = 1 + self.plugin.number_of_replacements
        self.plugin.insert_queue.append(('LCA Parameters Photovoltaic', 'Production and maintenance electrolyzer', production_maintenance_electrolyser))
    
    def calculate_h2_production(self):
        total_h2_produced = np.sum(self.plugin.h2_production)
        self.plugin.insert_queue.append(
            ('LCA Parameters Photovoltaic', 'H2 produced (kg)', total_h2_produced)
        )

def calculate_stack_replacement(
        operating_hours,
        replacement_time
        ) -> None:
    '''Calculation of stack replacement frequency for electrolyzer.
    '''
    cumulative_running_time = np.cumsum(operating_hours)
    stack_usage = cumulative_running_time / replacement_time

    number_of_replacements = np.floor_divide(stack_usage[-1], 1)
    replacement_frequency = len(stack_usage) / (number_of_replacements + 1.)
    return replacement_frequency, number_of_replacements

def calculate_hydrogen_production(
        power_consumption,
        conversion_efficiency,
        power_increase
        ) -> None:
    '''Calculation of hydrogen production based on power consumption, conversion efficiency 
    and power increase.
    '''
    h2_production = power_consumption * conversion_efficiency / power_increase

    return h2_production

def calculate_electrolyzer_power_demand(
        power_requirement_increase,
        nominal_power,
        year
        ) -> tuple[float,float]:
    '''Calculation of yearly increase in electrolyzer power demand.
    '''
    increase = (1. + power_requirement_increase) ** year
    demand = increase * nominal_power

    return demand, increase