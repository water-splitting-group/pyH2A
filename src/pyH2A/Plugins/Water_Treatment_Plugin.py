from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.Physical_Properties.Physical_properties import Physical_properties as PP
import numpy as np

class Water_Treatment_Plugin:
    '''Amount of water treatment species needed for circuits that need to be protected against corrosion or biological growth.
    '''

    def __init__(self, dcf, print_info, run = True):
        self._set_up(dcf)
        if run:
            self._run(dcf)

    def _set_up(self, dcf):

        self.functional_unit = dcf.functional_unit

        self.input_dict = {                 
            "Water Treatment": {
                "Yearly water mass to treat": {
                    "Value": {
                        "type": {np.ndarray},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "mass",
                    },
                    "optional": False,
                    "description": "Mass of water to be treated each year."
                },   
                "Corrosion and scale inhibitors per water mass": {
                    "Value": {
                        "type": {int, float},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "mass/mass",
                    },
                    "optional": False,
                    "description": "Mass of corrosion and scale inhibitor species to add per mass of water to be treated."
                },  
                "Biocide per water mass": {
                    "Value": {
                        "type": {int, float},
                        "bounds": (0, None),
                    },
                    "Unit": {
                        "dimension": "mass/mass",
                    },
                    "optional": False,
                    "description": "Mass of biocide to add per mass of water to be treated."
                },                                                       
            },                                 
        }

        self.output_dict = {
            "Water_Treatment": {
                 "Yearly corrosion and scale inhibitors mass": {
                    "Value": {
                        "inserted_value": "yearly_inhibitors",
                        "type": {np.ndarray},
                        "dimension": "mass",
                    },
                    "optional": False,
                    "description": "Mass of corrosion and scale inhibitors to use every year."
                },   
                 "Total corrosion and scale inhibitors mass": {
                    "Value": {
                        "inserted_value": "total_inhibitors",
                        "type": {int, float},
                        "dimension": "mass",
                    },
                    "optional": False,
                    "description": "Total mass of corrosion and scale inhibitors to use ."
                }, 
                 "Yearly biocide mass": {
                    "Value": {
                        "inserted_value": "yearly_biocide",
                        "type": {np.ndarray},
                        "dimension": "mass",
                    },
                    "optional": False,
                    "description": "Mass of biocide to use every year."
                },   
                 "Total biocide mass": {
                    "Value": {
                        "inserted_value": "total_biocide",
                        "type": {int, float},
                        "dimension": "mass",
                    },
                    "optional": False,
                    "description": "Total mass of biocide to use ."
                },                                   
            },   
        }

    def _run(self, dcf):
        self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, 'Water_Treatment_Plugin')

        self.calculate_water_Treatment()

        output_inserter_function(self.output_dict, self, dcf, 'Water_Treatment_Plugin') 
                
    def calculate_water_Treatment(self):

        self.yearly_inhibitors = Quantity(self.input_dict_resolved['Water Treatment']['Yearly water mass to treat']['Value'].unit['kg']
                                          *
                                          self.input_dict_resolved['Water Treatment']['Corrosion and scale inhibitors per water mass']['Value'].unit['kg/kg'], 
                                          'kg')
        self.total_inhibitors = Quantity(np.sum(self.yearly_inhibitors.unit['kg']), 'kg')
        
        self.yearly_biocide = Quantity(self.input_dict_resolved['Water Treatment']['Yearly water mass to treat']['Value'].unit['kg']
                                                  *
                                                  self.input_dict_resolved['Water Treatment']['Biocide per water mass']['Value'].unit['kg/kg'], 
                                                  'kg')
        self.total_biocide = Quantity(np.sum(self.yearly_biocide.unit['kg']), 'kg')

        print('self.total_inhibitors', self.total_inhibitors)
        print('self.total_biocide', self.total_biocide)
       
    