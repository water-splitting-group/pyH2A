import cProfile
import warnings
warnings.filterwarnings('ignore')

# Run: python solver_comparison/scripts/Profile_LCA.py
# Visualise: snakeviz mc_profile.prof
# py-spy: py-spy record -o profile.svg --subprocesses -- python solver_comparison/scripts/Profile_LCA.py
# Note: Change samples in data/LCA/PVE.md before running (100 or 50000)

from pyH2A.Analysis.Monte_Carlo_Analysis import Monte_Carlo_Analysis

if __name__ == '__main__':
    cProfile.run(
        "Monte_Carlo_Analysis('data/LCA/PVE.md')",
        'mc_profile.prof'
    )
    print('Done')