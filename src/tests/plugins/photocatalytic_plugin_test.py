import pytest
import numpy as np
from pyH2A.Plugins.Photocatalytic_Plugin import Photocatalytic_Plugin
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.functional_unit import resolve_functional_unit


class DummyDCF:
    """DCF object for Photocatalytic_Plugin with configurable inputs."""

    def __init__(
        self,
        relative_years,
        output_by_year,
        operating_capacity_factor,
        top_cost,
        bottom_cost,
        ports,
        port_cost,
        other_costs,
        markup,
        length,
        width,
        height,
        add_land,
        baggie_lifetime,
        catalyst_cost,
        catalyst_conc,
        catalyst_lifetime,
        molar_weight,
        attenuation_coeff,
        sth,
        hourly_solar,
        T_amb,
        wind_speed
    ):

        self.functional_unit = resolve_functional_unit('kg[H2]')
        self.inp = {
            "Time": {
                "Years": {
                    "Value": {'Operation years relative': relative_years},
                    "Unit": "-"
                },               
            },                
            "Technical Operating Parameters and Specifications": {
                "Design output by year": {
                    "Value": output_by_year, 
                    "Unit":"kg"
                },
                "Operating capacity factor": {
                    "Value": operating_capacity_factor, 
                    "Unit":"-"
                },                
            },
            "Reactor Baggies": {
                "Cost material top": {
                    "Value": top_cost, 
                    "Unit":"USD/m2"},
                "Cost material bottom": {
                    "Value": bottom_cost, 
                    "Unit":"USD/m2"},
                "Number of ports per baggie": {
                    "Value": ports, 
                    "Unit":"-"},
                "Cost of port": {
                    "Value": port_cost, 
                    "Unit":"USD"},
                "Other costs per baggie": {
                    "Value": other_costs, 
                    "Unit":"USD"},
                "Markup factor": {
                    "Value": markup, 
                    "Unit":"-"},
                "Length": {
                    "Value": length, 
                    "Unit":"m"},
                "Width": {
                    "Value": width, 
                    "Unit":"m"},
                "Filling height": {
                    "Value": height, 
                    "Unit":"m"},
                "Additional land area": {
                    "Value": add_land, 
                    "Unit":"-"},
                "Lifetime": {
                    "Value": baggie_lifetime, 
                    "Unit":"year"},
            },
            "Catalyst": {
                "Cost per unit of mass": {
                    "Value": catalyst_cost, 
                    "Unit":"USD/kg"},
                "Concentration": {
                    "Value": catalyst_conc, 
                    "Unit":"g/liter"},
                "Lifetime": {
                    "Value": catalyst_lifetime, 
                    "Unit":"year"},
                "Molar Weight": {
                    "Value": molar_weight, 
                    "Unit":"g/mol"},
                "Molar attenuation coefficient": {
                    "Value": attenuation_coeff, 
                    "Unit":"liter/(cm * mol)"
                },
            },
            "Solar-to-Hydrogen Efficiency": {
                "STH": {
                    "Value": sth, 
                    "Unit":"-"
                }
            },
            "Solar Input": {
                "Hourly": {
                    "Value": hourly_solar, 
                    "Unit":"kWh/m2", 
                    "Processed": "Yes"
                },
            },
            "Meteorological Conditions": {
                "Temperature": {
                    "Value": T_amb, 
                    "Unit":"degC"
                },
                "Wind speed": {
                    "Value": wind_speed, 
                    "Unit":"m/s"
                }                
            },          
        }


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "relative_years":  np.array([0, 1]),
                "output_by_year": np.array([1000, 1000]),
                "operating_capacity_factor": 0.9,
                "top_cost": 0.54,
                "bottom_cost": 0.47,
                "ports": 12,
                "port_cost": 30.0,
                "other_costs": 610.7,
                "markup": 1.5,
                "length": 323.0,
                "width": 12.2,
                "height": 0.05,
                "add_land": 0.30,
                "baggie_lifetime": 5.0,
                "catalyst_cost": 3000.0,
                "catalyst_conc": 0.533,
                "catalyst_lifetime": 0.5,
                "molar_weight": 500.0,
                "attenuation_coeff": 8000.0,
                "sth": 0.2,
                "hourly_solar": np.array(
                    [
                        0.22916667,
                        0.22916667,
                        0.22916667,
                        0.22916667,
                        0.22916667,
                        0.22916667,
                        0,
                        0.22916667,
                        0.22916667,
                        0.22916667,
                        0.22916667,
                        0.22916667,
                        0.22916667,
                        0.22916667,
                        0.22916667,
                        0,
                        0.22916667,
                        0.22916667,
                        0.22916667,
                        0,
                        0.22916667,
                        0.22916667,
                        0.22916667,
                        0,
                    ]
                ),
                "T_amb": np.array(
                    [
                        0.,
                        25,
                        25,
                        25,
                        25,
                        25,
                        0,
                        25,
                        25,
                        25,
                        25,
                        25,
                        25,
                        25,
                        25,
                        0,
                        25,
                        25,
                        25,
                        0,
                        25,
                        25,
                        25,
                        0,
                    ]
                ),  
                "wind_speed": np.array(
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        6,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        6,
                        0,
                        0,
                        0,
                        6,
                        0,
                        0,
                        0,
                        6,
                    ]
                ),                              
            },
            "expected": {
                "total_land_area": Quantity(1480483.42,"m2"),
                "total_solar_collection_area": Quantity(1138833.4,"m2"),
                "catalyst_cost": Quantity(91049730.33,"USD"),
                "baggies_cost": Quantity(2146131.051,"USD"),
                "baggie_number": Quantity(289,"-"),
                "total_volume": Quantity(56941670,"liter"), 
                "gross_yearly_mass": Quantity(np.array([8376.66766203819, 8376.66766203819]), 'kg'), 
                "net_yearly_mass" : Quantity(np.array([8042.410714285714, 8042.410714285714]), 'kg'),
                "outlet_temperature" : {'first': Quantity(287.75878374896547, 'K'), 
                                        'last': Quantity(292.0720326729867, 'K')}, 
                "outlet_enthalpy": {'first': Quantity(-352972.9838349018, 'J/kg'), 
                                        'last': Quantity(-444705.5619094611, 'J/kg')}, 
                "outlet_mass_fraction_H2": {'first':Quantity(0.10917635780407765, '-'),
                                         'last':Quantity(0.10832496011708614, '-')
                                        }, 
                "hourly_mass_flow": {'first': Quantity(381.6455091993411, 'kg'), 
                                        'last': Quantity(384.6451143081896, 'kg')},
            },
        },
    ],
)
def test_photocatalytic_plugin_optional_catalyst(case):
    """Test Photocatalytic_Plugin using base inputs (direct names style)."""

    # Unpack inputs from case
    dcf = DummyDCF(**case["input"])

    # Run plugin
    plugin = Photocatalytic_Plugin(dcf, print_info=False)
    expected = case["expected"]

    # Tolerance (very small)
    tolerance = 1e-12

    assert plugin.total_land_area.unit["m2"] == pytest.approx(
        expected["total_land_area"].unit["m2"], 
        abs=tolerance
    )

    assert plugin.total_solar_collection_area.unit["m2"] == pytest.approx(
        expected["total_solar_collection_area"].unit["m2"], 
        abs=tolerance
    )

    assert plugin.catalyst_cost.unit["USD"] == pytest.approx(
        expected["catalyst_cost"].unit["USD"], 
        abs=tolerance
    )

    assert plugin.baggies_cost.unit["USD"] == pytest.approx(
        expected["baggies_cost"].unit["USD"], 
        abs=tolerance
    )

    assert plugin.baggie_number.unit["-"] == pytest.approx(
        expected["baggie_number"].unit["-"], 
        abs=tolerance
    )

    assert plugin.total_volume.unit["liter"] == pytest.approx(
        expected["total_volume"].unit["liter"], 
        abs=tolerance
    )

    assert plugin.gross_yearly_mass.unit["kg"] == pytest.approx(
        expected["gross_yearly_mass"].unit["kg"], 
        abs=tolerance
    )

    assert plugin.net_yearly_mass.unit["kg"] == pytest.approx(
        expected["net_yearly_mass"].unit["kg"], 
        abs=tolerance
    )    

    assert plugin.outlet_temperature[0].unit["K"][0] == pytest.approx(
        expected["outlet_temperature"]['first'].unit["K"], 
        abs=tolerance
    )        

    assert plugin.outlet_temperature[1].unit["K"][-1] == pytest.approx(
        expected["outlet_temperature"]['last'].unit["K"], 
        abs=tolerance
    )         

    assert plugin.outlet_enthalpy[0].unit["J/kg"][0] == pytest.approx(
        expected["outlet_enthalpy"]['first'].unit["J/kg"], 
        abs=tolerance
    )        

    assert plugin.outlet_enthalpy[1].unit["J/kg"][-1] == pytest.approx(
        expected["outlet_enthalpy"]['last'].unit["J/kg"], 
        abs=tolerance
    )   

    assert plugin.outlet_mass_fraction[0]['H2'].unit["-"][0] == pytest.approx(
        expected["outlet_mass_fraction_H2"]['first'].unit["-"], 
        abs=tolerance
    )        

    assert plugin.outlet_mass_fraction[1]['H2'].unit["-"][-1] == pytest.approx(
        expected["outlet_mass_fraction_H2"]['last'].unit["-"], 
        abs=tolerance
    )  

    assert plugin.hourly_mass_flow[0].unit["kg"][0] == pytest.approx(
        expected["hourly_mass_flow"]['first'].unit["kg"], 
        abs=tolerance
    )        

    assert plugin.hourly_mass_flow[1].unit["kg"][-1] == pytest.approx(
        expected["hourly_mass_flow"]['last'].unit["kg"], 
        abs=tolerance
    )                   