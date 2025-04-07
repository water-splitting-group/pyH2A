import sys
from pyH2A.run_pyH2A import pyH2A
from tests.test_pyh2a import test_pv_e, test_pec, test_photocatalytic_base

def update_all():
    test_pv_e()
    pyH2A('./tests/PV_E.md', './tests/Results/PV_E/', store_snapshots=True)
    
    test_pec()
    pyH2A('./tests/PEC.md', './tests/Results/PEC/', store_snapshots=True)
    
    test_photocatalytic_base()
    pyH2A('./tests/Photocatalytic.md', './tests/Results/Photocatalytic/', store_snapshots=True)

def main():
    if len(sys.argv) < 2:
        choice = input("Update all snapshots or specify (pve, pec, photocatalytic)? [all/pve/pec/photocatalytic]: ").strip().lower()
    else:
        choice = sys.argv[1].strip().lower()
    
    if choice == "all":
        update_all()
    elif choice == "pve":
        test_pv_e()
        pyH2A('./tests/PV_E.md', './tests/Results/PV_E/', store_snapshots=True)
    elif choice == "pec":
        test_pec()
        pyH2A('./tests/PEC.md', './tests/Results/PEC/', store_snapshots=True)
    elif choice == "photocatalytic":
        test_photocatalytic_base()
        pyH2A('./tests/Photocatalytic.md', './tests/Results/Photocatalytic/', store_snapshots=True)
    else:
        print("Invalid choice. Please use 'all', 'pve', 'pec', or 'photocatalytic'.")
        sys.exit(1)

if __name__ == "__main__":
    main()
