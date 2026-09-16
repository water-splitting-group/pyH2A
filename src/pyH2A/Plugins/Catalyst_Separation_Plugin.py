from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.docstring_generation import generate_docstring

class Catalyst_Separation_Plugin:

    def __init__(self, dcf, print_info, run = True):
        self._set_up(dcf)
        if run:
            self._run(dcf)

    def _set_up(self, dcf):

        self.functional_unit = dcf.functional_unit

        self.input_dict = {
            "Water Volume": {
                "Volume": {
                    "Value": {
                        "type": {int,float,},
                        "bounds": (0, None),
                    },		
                    "Unit": {
                        "dimension": "volume",
                    },	
                    "optional": False,
                    "description": "Total water volume of plant (water/catalyst mixture)."
                },
            },
            "Catalyst": {
                "Lifetime": {
                    "Value": {
                        "type": {int,float,},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "time",
                    },	
                    "optional": False,
                    "description": "Lifetime of catalysts before replacement is required."	
                },
            },
            "Catalyst Separation": {
                "Filtration cost": {
                    "Value": {
                        "type": {int,float,},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "currency / volume",
                    },	
                    "optional": False,
                    "description": "Cost of filtration in currency per volume."
                },
            },
        }

        self.output_dict = {
            "Other Variable Operating Cost - Catalyst Separation": {
                "Catalyst separation (yearly cost)": {
                    "Value": {
                        "inserted_value": "yearly_cost",
                        "type": {float,},
                        "dimension":"currency",
                    },
                    "description": "Yearly cost of catalyst seperation.",
                    "optional": False,
                },
            },
        }
        
        self.__doc__ = generate_docstring("Calculation of cost for catalyst separation (e.g. via nanofiltration).",
                                          self.input_dict, self.output_dict)
  
    def _run(self, dcf):
        self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, 'Catalyst_Separation_Plugin')

        self.calculate_yearly_filtration_volume()
        self.calculate_filtration_cost()

        output_inserter_function(self.output_dict, self, dcf, 'Catalyst_Separation_Plugin') 

    def calculate_yearly_filtration_volume(self):
        '''Calculation of water volume that has to be filtered per year.
        '''

        fraction_to_be_filtered_yearly = 1./self.input_dict_resolved['Catalyst']['Lifetime']['Value'].unit['year']

        self.yearly_filtration_volume = Quantity(self.input_dict_resolved['Water Volume']['Volume']['Value'].unit['m3'] 
                                                 * fraction_to_be_filtered_yearly, 
                                        'm3')
        

    def calculate_filtration_cost(self):
        '''Yearly cost of water filtration to remove catalyst.
        '''

        self.yearly_cost = Quantity(self.yearly_filtration_volume.unit['m3'] 
                                    * self.input_dict_resolved['Catalyst Separation']['Filtration cost']['Value'].unit['USD/m3'], 
                           'USD')







