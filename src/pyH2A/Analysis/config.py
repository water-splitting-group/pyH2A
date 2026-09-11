'''Configuration for dependent variables supported by `Monte_Carlo_Analysis`.
'''

DEPENDENT_VARIABLE_CONFIG = {
	'h2_cost': {
		'header': 'cost',
		'label': 'H2 Cost ($/kg)',
		'unit': r'\$/kg($H_{2}$)',
	},
	'Climate change': {
		'header': 'climate change',
		'label': 'Climate change (kg CO2-Eq/kg H2)',
		'unit': 'kg $CO_{2}$-Eq/kg $H_{2}$',
	},
	'Cumulative energy demand': {
		'header': 'cumulative energy demand',
		'label': 'Cumulative energy demand (MJ_Eq/kg H2)',
		'unit': 'MJ_Eq/kg $H_{2}$',
	},
	'Climate change no LT - Global warming potential (GWP100) no LT': {
		'header': 'gwp100',
		'label': 'GWP100 (kg CO2-Eq/kg H2)',
		'unit': 'kg $CO_{2}$-Eq/kg $H_{2}$',
	},
}
