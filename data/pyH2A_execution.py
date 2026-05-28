from pyH2A.Utilities.input_modification import convert_input_to_dictionary
from pyH2A.run_pyH2A import pyH2A
from pyH2A.Discounted_Cash_Flow import discounted_cash_flow_function
from scipy.stats import ttest_ind
import numpy as np

np.set_printoptions(suppress=True)
import matplotlib.pyplot as plt
import pprint


def optimization_test():
    result = pyH2A("data/PV_E/Base/PV_E_Base_Optimization.md", "data/PV_E/Base")


def dcf_test():

    values = np.linspace(0.2, 3, 200)

    parameter = ["Photovoltaic", "Nominal Power (kW)", "Value"]

    results = discounted_cash_flow_function(
        "data/PV_E/Base/PV_E_Base.md", values, parameter
    )

    plt.plot(values, results)
    plt.show()


def pv_e_base():

    result = pyH2A("data/PV_E/Base/PV_E_Base.md", "data/PV_E/Base")

    pprint.pprint(result.base_case.inp["Direct Capital Costs - Reverse Osmosis"])

    # pprint.pprint(result.base_case.inp['Technical Operating Parameters and Specifications']['Output per Year']['Value'])

    # pprint.pprint(result.base_case.inp['Technical Operating Parameters and Specifications'])

    # pprint.pprint(result.meta_modules['Monte_Carlo_Analysis']['Module'].shortest_target_distance)

    # pprint.pprint(result.__dict__)

    # pprint.pprint(result.base_case.inp)

    # pprint.pprint(result.base_case.inp['Direct Capital Costs - Electrolyzer'])
    # pprint.pprint(result.base_case.inp['Planned Replacement'])


def pv_e_limit():
    result = pyH2A("data/PV_E/Limit/PV_E_Limit.md", "data/PV_E/Limit")


def pv_e_distance_time():
    result = pyH2A(
        "data/PV_E/Historical_Data/PV_E_Distance_Time.md", "data/PV_E/Historical_Data"
    )

    print(result.meta_modules["Development_Distance_Time_Analysis"]["Module"].p_linear)


def pec_base():

    result = pyH2A("data/PEC/Base/PEC_Base.md", "data/PEC/Base")
    # pprint.pprint(result.base_case.inp['Non-Depreciable Capital Costs'])
    pprint.pprint(
        result.meta_modules["Monte_Carlo_Analysis"]["Module"].shortest_target_distance
    )


def pec_limit():

    result = pyH2A("data/PEC/Limit/PEC_Limit.md", "data/PEC/Limit")

    pprint.pprint(result.base_case.plugs["PEC_Plugin"].mol_H2_per_m2_per_day * 3 / 24.0)
    pprint.pprint(result.base_case.plugs["PEC_Plugin"].mol_H2_per_m2_per_day)
    pprint.pprint(result.base_case.plugs["PEC_Plugin"].total_solar_collection_area)

    # pprint.pprint(result.base_case.inp['Direct Capital Costs - Solar Concentrator'])
    # pprint.pprint(result.base_case.inp['Non-Depreciable Capital Costs'])
    # pprint.pprint(result.base_case.inp['PEC Cells']['Number'])


def pec_limit_no_concentration():

    result = pyH2A("data/PEC/No_Conc/PEC_Limit_No_Concentration.md", "data/PEC/No_Conc")

    # pprint.pprint(result.base_case.inp['Non-Depreciable Capital Costs'])


def photocatalytic_base():
    # 225.15652501997127 $/kg

    result = pyH2A(
        "data/Photocatalytic/Base/Photocatalytic_Base.md", "data/Photocatalytic/Base"
    )

    pprint.pprint(
        result.meta_modules["Monte_Carlo_Analysis"]["Module"].shortest_target_distance
    )
    # pprint.pprint(result.base_case.plugs['Photocatalytic_Plugin'].catalyst_amount_kg)
    # pprint.pprint(result.base_case.inp['Reactor Baggies'])
    # pprint.pprint(result.base_case.inp['Direct Capital Costs - Reactor Baggies'])
    # pprint.pprint(result.base_case.inp['Direct Capital Costs - Control System']['Hydrogen Area Sensors ($ per baggie)'])

    # from pyH2A.Discounted_Cash_Flow import discounted_cash_flow_function
    # import matplotlib.pyplot as plt
    # import numpy as np
    # data_points = np.arange(100, 10000, 100)
    # results = discounted_cash_flow_function('data/Photocatalytic/Base/Photocatalytic_Base.md',
    # 										data_points,
    # 										np.array(['Reactor Baggies', 'Length (m)', 'Value']))
    # plt.plot(data_points, results, 'o-')
    # plt.show()


def photocatalytic_limit():

    result = pyH2A(
        "data/Photocatalytic/Limit/Photocatalytic_Limit.md", "data/Photocatalytic/Limit"
    )
    pprint.pprint(result.base_case.plugs["Photocatalytic_Plugin"].catalyst_properties)


def technology_comparison():
    pec = pyH2A("data/PEC/Base/PEC_Base.md", "data/PEC/Base")
    pc = pyH2A(
        "data/Photocatalytic/Base/Photocatalytic_Base.md", "data/Photocatalytic/Base"
    )
    pv_e = pyH2A("data/PV_E/Base/PV_E_Base.md", "data/PV_E/Base")

    pec_distances = pec.meta_modules["Monte_Carlo_Analysis"]["Module"].distances
    pc_distances = pc.meta_modules["Monte_Carlo_Analysis"]["Module"].distances
    pv_e_distances = pv_e.meta_modules["Monte_Carlo_Analysis"]["Module"].distances

    print(ttest_ind(pv_e_distances, pc_distances))


def test():

    from pyH2A.Utilities.Energy_Conversion import Energy, eV, J, kJmol
    from scipy import constants as con

    reaction_energy_per_kg = Energy(2 * 1.229 * con.Avogadro * (1000.0 / 2.0), eV)
    print(reaction_energy_per_kg.J / 1e6)
    print(Energy(141 * 1e6, J).kWh)
    print(Energy(285.83 * (1000.0 / 2.0) * con.Avogadro, kJmol).J)


def lca():
    result = pyH2A("src/tests/end_to_end/Thermal_Base.md", ".")
    print(result)


def case_1_without_resolver():
    from pyH2A.Utilities.input_modification import (
        convert_input_to_dictionary,
        execute_plugin,
    )
    import pprint

    inp = convert_input_to_dictionary("src/tests/variables_references/input_1.md")

    class FakeDCF:
        def __init__(self, inp):
            self.inp = inp

    dcf = FakeDCF(inp)

    plugs = {}
    execute_plugin(
        "Test_Plugin_Case_1_Without_Resolver", plugs, print_info=True, dcf=dcf
    )

    for table_name in [
        "My Table",
        "My Second Table",
        "My Third Table",
        "My Fourth Table",
        "My Fifth Table",
    ]:
        pprint.pprint({table_name: dcf.inp[table_name]})

    print("\n\n")
    print("-------END OF CASE 1 WITHOUT RESOLVER-------")


def case_1_with_resolver():
    from pyH2A.Utilities.input_modification import (
        convert_input_to_dictionary,
        execute_plugin,
    )

    class FakeDCF:
        def __init__(self, inp):
            self.inp = inp

    inp = convert_input_to_dictionary("src/tests/variables_references/input_1.md")
    dcf = FakeDCF(inp)

    plugs = {}

    execute_plugin(
        "Test_Plugin_Case_1_With_Resolver",
        plugs,
        print_info=True,
        dcf=dcf,
    )

    plugin = plugs["Test_Plugin_Case_1_With_Resolver"]

    print("\nCASE 1: Tables 2 and 3 resolved before Table 1\n")
    pprint.pprint(plugin.tables_2_3)

    print("\nCASE 2: Table 1 resolved after Tables 2 and 3\n")
    pprint.pprint(plugin.table_1)

    print("\nCASE 3: Tables 4 and 5 resolved after Table 1\n")
    pprint.pprint(plugin.tables_4_5)


def main():
    # dcf_test()
    # optimization_test()
    # pv_e_base()
    # pv_e_limit()
    # pv_e_distance_time()
    # pec_base()
    # pec_limit()
    # pec_limit_no_concentration()
    # photocatalytic_base()
    # photocatalytic_limit()
    # technology_comparison()
    # test()
    # lca()
    case_1_without_resolver()
    case_1_with_resolver()


if __name__ == "__main__":
    main()
