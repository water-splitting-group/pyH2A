from pyH2A.Utilities.IO import input_resolver_function, output_inserter_function
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.docstring_generation import generate_docstring

class Labor_Operating_Cost_Plugin:

	def __init__(self, dcf, print_info, run = True):
		self._set_up(dcf)
		if run:
			self._run(dcf)

	def _set_up(self, dcf):

		self.functional_unit = dcf.functional_unit

		self.input_dict = {
			"Inflation":{
				"Labor inflator": {
					"Value": {
						"type": {float,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "dimensionless",
					},	
					"optional": False,
					"description": "Labor inflator."
				},
			},		
			"Fixed Operating Costs": {
				"Staff": {
					"Value": {
						"type": {int,float,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "dimensionless",
					},
					"description": "Total Number of staff (full time equivalents) required for operation of the plant."
				},
				"Hourly labor cost": {
					"Value": {
						"type": {int, float,},
						"bounds": (0, None),
					},
					"Unit": {
						"dimension": "currency / time",
					},
					"description": "Hourly labor cost of staff."
				},
			},
		}

		self.output_dict = {
			"Fixed Operating Costs": {
				"Labor cost": {
					"Value": {
						"inserted_value": "labor_uninflated",
						"type": {int, float,},
						"dimension": "currency",
					},	
					"description": "Yearly total labor cost without applying labor inflator."
				},
				"Labor cost - inflated": {
					"Value": {
						"inserted_value": "labor_inflated",
						"type": {int, float,},
						"dimension": "currency",	
					},
					"description": "Yearly total labor cost after applying labor inflator."
				},
			},
		}
  
	def _run(self, dcf):
		self.input_dict_resolved = input_resolver_function(self.input_dict, dcf, 'Labor_Operating_Cost_Plugin')
		
		self.labor_uninflated, self.labor_inflated = self.labor_cost()

		output_inserter_function(self.output_dict, self, dcf, 'Labor_Operating_Cost_Plugin')  

	def labor_cost(self):
		'''Calculation of yearly labor costs by multiplying number of staff times hourly labor cost.'''

		work_hours_in_a_year = Quantity(2080, 'h') # Assuming 40 hours per week and 52 weeks per year

		labor_uninflated = Quantity(self.input_dict_resolved['Fixed Operating Costs']['Staff']['Value'].unit['-'] 
						            * self.input_dict_resolved['Fixed Operating Costs']['Hourly labor cost']['Value'].unit['USD/h']
						            * work_hours_in_a_year.unit['h'],
						   'USD')
		
		labor_inflated = Quantity(labor_uninflated.unit['USD'] 
								       * self.input_dict_resolved['Inflation']['Labor inflator']['Value'].unit['-'], 
						 'USD')
		
		return labor_uninflated, labor_inflated




