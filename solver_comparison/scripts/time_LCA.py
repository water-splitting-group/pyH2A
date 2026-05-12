import sys
import os
import time
import importlib.util
import warnings
warnings.filterwarnings('ignore')

# Run: python solver_comparison/scripts/time_LCA.py
#      python solver_comparison/scripts/time_LCA.py pytorch
#      python solver_comparison/scripts/time_LCA.py jax
# Note for pytorch/jax: $env:KMP_DUPLICATE_LIB_OK='TRUE'

solver = sys.argv[1] if len(sys.argv) > 1 else 'pardiso'

# Navigate from solver_comparison/scripts/ up to repo root
# then into src/pyH2A/LCA/
base = os.path.dirname(os.path.abspath(__file__))
lca_dir = os.path.join(base, '..', '..', 'src', 'pyH2A', 'LCA')
lca_dir = os.path.normpath(lca_dir)

solver_files = {
    'pardiso': os.path.join(lca_dir, 'LCA_lib.py'),
    'pytorch': os.path.join(lca_dir, 'LCA_lib_pytorch.py'),
    'jax':     os.path.join(lca_dir, 'LCA_lib_jax.py'),
}

if solver not in solver_files:
    print(f'Unknown solver: {solver}. Choose: pardiso, pytorch, jax')
    sys.exit(1)

spec = importlib.util.spec_from_file_location(
    "pyH2A.LCA.LCA_lib",
    solver_files[solver]
)
mod = importlib.util.module_from_spec(spec)
sys.modules["pyH2A.LCA.LCA_lib"] = mod
spec.loader.exec_module(mod)

print(f'Solver: {solver}')
print('─' * 30)

from pyH2A.Discounted_Cash_Flow import Discounted_Cash_Flow

# Run 1 - includes startup
start = time.time()
dcf = Discounted_Cash_Flow('data/LCA/PVE.md', print_info=False)
print(f'Run 1: {time.time() - start:.3f}s')

# Run 2 - pure LCA work no startup
start = time.time()
dcf = Discounted_Cash_Flow('data/LCA/PVE.md', print_info=False)
print(f'Run 2: {time.time() - start:.3f}s')