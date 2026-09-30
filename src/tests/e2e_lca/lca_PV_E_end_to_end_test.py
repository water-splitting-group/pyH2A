import pytest

from pyH2A.run_pyH2A import pyH2A
from pyH2A.Utilities.Unit_Handler import Quantity

def test_pv_e_lca_end_to_end():
    '''Testing model PV+E H2 production system end to end with LCA calculation.
    The ground truth is based on an OpenLCA calculation using the ecoinvent 3.11 database and IPCC 2021 LCIA method. 
    The LCA calculation is based on the functional unit of 1 kg of H2 produced over the lifetime of the system. 
    The test checks that the LCA result from pyH2A matches the OpenLCA ground truth within a tight tolerance.
    '''

    TOLERANCE = 1e-9

    IMPACT_ASSESSMENT_CATEGORY  = 'Climate change: fossil - Global warming potential (GWP100)' # from ecoinvent 3.11 IPCC 2021 LCIA
    ASSUMED_H2_PRODUCTION_LIFETIME = Quantity(815238047.7775391, 'kg[H2]')
    OPENLCA_GROUND_TRUTH = Quantity(1.6637563901125195E9, 'kg[$CO_{2}$-Eq]')

    OPENLCA_GROUND_TRUTH_PER_FUNCTIONAL_UNIT = Quantity(OPENLCA_GROUND_TRUTH.unit['kg[$CO_{2}$-Eq]']
                                                        / ASSUMED_H2_PRODUCTION_LIFETIME.unit['kg[H2]'],
                                                        'kg[$CO_{2}$-Eq] / kg[H2]')
    # Ground truth value is around 2.04 kg[CO2-eq]/kg[H2]

    result = pyH2A(
        'src/tests/e2e_lca/data/PV_E/PV_E_TEA_LCA.md',
        'src/tests/e2e_lca/data/PV_E/'
    )

    lca_result = result.base_case.inp['Dependent Variables'][IMPACT_ASSESSMENT_CATEGORY]['Value']

    assert lca_result.unit['kg[$CO_{2}$-Eq] / kg[H2]'] == pytest.approx(
        OPENLCA_GROUND_TRUTH_PER_FUNCTIONAL_UNIT.unit['kg[$CO_{2}$-Eq] / kg[H2]'],
        rel = TOLERANCE)


    # import pprint as pp

    # print('PV area:                              ', result.base_case.inp['Photovoltaic']['Module area']['Value'])
    # print('Electrolyzer number of BOP:           ', result.base_case.inp['Electrolyzer']['Number of units']['Value'])
    # print('Electrolyzer number of stacks:        ', result.base_case.inp['Electrolyzer']['Number of stacks']['Value'])
    # print('Reverse Osmosis number of devices:    ', result.base_case.inp['Reverse Osmosis']['Number of devices']['Value'])
    # print('Lifetime battery mass:                ', result.base_case.inp['Battery']['Lifetime battery mass']['Value'])

    # print('H2 production                         ', result.base_case.inp['Technical Operating Parameters and Specifications']['Total output at gate']['Value'])

    # pp.pprint(result.base_case.inp['Dependent Variables'])

    # lca_plugin = result.base_case.plugs['LCA_Plugin']

    # scaling_vector = lca_plugin.scaling_vector
    # print(scaling_vector)


if __name__ == "__main__":
    test_pv_e_lca_end_to_end()
