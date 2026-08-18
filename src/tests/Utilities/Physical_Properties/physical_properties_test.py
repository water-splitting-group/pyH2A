import pytest
from pyH2A.Utilities.Physical_Properties.Physical_properties import Physical_properties as PP
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from tests.Utilities.check_dicts_for_testing import check_dicts


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "temperature": Quantity(60.0, "degC"),
                "pressure": Quantity(1.013, "bar"),
                "amount": {
                    "H2O": Quantity(0.268555356, "kg"),
                    "H2": Quantity(0.081853589, "kg"),
                    "O2": Quantity(0.649591055, "kg"),
                },
                "phase": "V",
                "composition_basis": "mass",
            },
            "expected": {
                "mol": {
                    'H2O': Quantity(14.907319233971691, 'mol'), 
                    'H2': Quantity(40.60197867063492, 'mol'), 
                    'O2': Quantity(20.300989280580037, 'mol')
                },                  
                "mol_fraction": {
                    'H2O': Quantity(0.1966397937202985, '-'), 
                    'H2': Quantity(0.5355734713344887, '-'), 
                    'O2': Quantity(0.26778673494521277, '-')
                },         
                "enthalpy": Quantity(-3527830.3799919076, 'J'),           
                "cp": Quantity(2285.9011465963235, 'J / delta_K'),                 
                "volume": Quantity(2.0728531423410006, 'm3'),             
            },
        },
        {
            "input": {
                "temperature": Quantity(60.0, "degC"),
                "pressure": Quantity(1.013, "bar"),
                "amount": {
                    "H2O": Quantity(0.19663979, "mol"),
                    "H2": Quantity(0.53557347, "mol"),
                    "O2": Quantity(0.26778674, "mol"),
                },
                "phase": "V",
                "composition_basis": "molar",
            },
            "expected": {
                "mass": {
                    'H2O': Quantity(0.0035424658168500003, 'kg'), 
                    'H2': Quantity(0.00107971611552, 'kg'), 
                    'O2': Quantity(0.00856864010652, 'kg')
                },
                "mass_fraction": {
                    'H2O': Quantity(0.26855534904541073, '-'), 
                    'H2': Quantity(0.08185358822495777, '-'), 
                    'O2': Quantity(0.6495910627296315, '-')
                }, 
                "enthalpy": Quantity(-46534.9815012528, 'J'),    
                "cp": Quantity(30.152915000642132, 'J / delta_K'),  
                "volume": Quantity(0.027342636722606124, 'm3'),   
                
            },
        },
    ],
    ids=[
        "Mass basis",
        "Molar basis",
    ],
)
def test_physical_properties(case):
    """Check physical property calculations."""

    inp = case["input"]

    T = inp["temperature"]
    P = inp["pressure"]
    amount = inp["amount"]

    obtained = {}

    if inp["composition_basis"] == "mass":
        mol, mol_fraction = PP.Mass_to_substance(amount)

        obtained["mol"] = mol
        obtained["mol_fraction"] = mol_fraction

    else:
        mass, mass_fraction = PP.Substance_to_mass(amount)

        obtained["mass"] = mass
        obtained["mass_fraction"] = mass_fraction

    H = PP.Enthalpy(
        T,
        P,
        amount,
        phase=inp["phase"],
        composition_basis=inp["composition_basis"],
    )

    Cp = PP.Heat_capacity(
        T,
        P,
        amount,
        phase=inp["phase"],
        composition_basis=inp["composition_basis"],
    )    

    V = PP.Volume(
        T,
        P,
        amount,
        phase=inp["phase"],
        composition_basis=inp["composition_basis"],
    )

    obtained["enthalpy"] = H
    obtained["cp"] = Cp
    obtained["volume"] = V

    check_dicts(obtained, case["expected"])


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "temperature": Quantity(60.0, "degC"),
            },
            "expected": {
                "psat": Quantity(19930.01340356875, 'Pa'),
            },
        },
    ],
    ids=["Water saturation pressure"],
)
def test_water_saturation_pressure(case):
    """Check water saturation pressure."""

    obtained = {
        "psat": PP.Water_saturation_pressure(case["input"]["temperature"]),
    }

    check_dicts(obtained, case["expected"])

@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "temperature": Quantity(60.0, "degC"),
                "pressure": Quantity(1.013, "bar"),
                "amount": {
                    "H2O": Quantity(1.0, "kmol"),
                },
                "phase": "L",
                "composition_basis": "molar",
            },
            "expected": {
                "volume": Quantity(1.8321969454242848e1, 'liter'),
            },
        },
    ],
    ids=["Pure liquid water"],
)
def test_liquid_water_volume(case):
    """Check liquid water volume."""

    inp = case["input"]

    obtained = {
        "volume": PP.Volume(
            inp["temperature"],
            inp["pressure"],
            inp["amount"],
            phase=inp["phase"],
            composition_basis=inp["composition_basis"],
        )
    }

    check_dicts(obtained, case["expected"])