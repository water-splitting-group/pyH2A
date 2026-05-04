"""
This script gives some examples for using the openLCA matrix export in Python.
You need to have NumPy and SciPy installed, e.g. via pip

  pip install -U numpy scipy

Note that all calculations in these examples are currently done with dense
matrices. Sparse matrices are converted to a dense format in these calculations.
If you want to use faster calculations for sparse matrices checkout the direct
and iterative solvers from the SciPy package:

  https://docs.scipy.org/doc/scipy/reference/sparse.linalg.html
"""

import numpy as np
from pyH2A import Discounted_Cash_Flow
from pyH2A.LCA.LCA_lib import ExportFolder, Matrix, solve 
from pyH2A.Utilities.input_modification import process_table
import pprint as pp

class LCA:
    """
        Wrapper class for performing Life Cycle Assessment (LCA) calculations
        using openLCA matrix exports within the pyH2A framework.

        The class constructs a scaling vector from pyH2A input tables,
        performs matrix-based LCA calculations, and stores impact results
        in a structured format.

        Parameters
        ----------
        matrix_folder : str
            Path to the openLCA matrix export folder containing the
            technosphere (A), intervention (B), characterization (C),
            and demand (f) matrices.
        dcf : pyH2A.Discounted_Cash_Flow
            pyH2A Discounted_Cash_Flow object containing model input tables,
            including LCA-related scaling information.

        Attributes
        ----------
        folder : ExportFolder
            Loaded openLCA export folder.
        tech_index_dict : dict
            Dictionary mapping process UUIDs to TechEntry objects.
        A : ndarray or scipy.sparse matrix
            Technosphere matrix.
        B : ndarray or scipy.sparse matrix
            Intervention (biosphere) matrix.
        C : ndarray or scipy.sparse matrix
            Characterization matrix.
        f : ndarray
            Demand vector.
        scaling_vector : ndarray
            Vector used to scale LCA processes based on pyH2A inputs.
        lca_results : dict
            Dictionary of LCA results with impact names as keys and
            dictionaries containing values and units.

        Notes
        -----
        This implementation assumes that all processes required by the
        openLCA model are explicitly scaled through pyH2A input tables.
        An error is raised if the scaling vector is incomplete.
    """
      
    def __init__(self, matrix_folder: str, dcf: Discounted_Cash_Flow):
        """
            Initializes the LCA object and performs the LCA calculation.

            Parameters
            ----------
            matrix_folder : str
                Path to the openLCA matrix export folder.
            dcf : pyH2A.Discounted_Cash_Flow
                pyH2A Discounted_Cash_Flow object containing model inputs
                used to construct the scaling vector.
        """

        self.folder = self.import_folder(matrix_folder)
        self.tech_index_dict = self.folder.tech_index()
        self.A, self.B, self.C, self.f = self.load_matrices()
        self.A_modified = None  # Will be set by update_A_matrix_with_lca_components
        self.update_A_matrix_with_lca_components(dcf)
        self.build_scaling_vector(dcf)

        self.perform_LCA()
        

    def import_folder(self, folder: str) -> ExportFolder:
        """
            Imports an openLCA matrix export folder and verifies that
            impact assessment data are available.

            Parameters
            ----------
            folder : str
                Path to the openLCA export folder.

            Returns
            -------
            ExportFolder
                Loaded openLCA export folder.

            Raises
            ------
            RuntimeError
                If the export folder does not contain impact data.
        """

        export_folder = ExportFolder(folder)

        if not export_folder.has_impacts():
            print('error: no impacts in your export')
            return
        else:
            return export_folder

    def load_matrices(self):
        """
            Loads the technosphere, intervention, characterization,
            and demand matrices from the openLCA export folder.

            Returns
            -------
            A : ndarray or scipy.sparse matrix
                Technosphere matrix.
            B : ndarray or scipy.sparse matrix
                Intervention matrix.
            C : ndarray or scipy.sparse matrix
                Characterization matrix.
            f : ndarray
                Demand vector.
        """

        A = self.folder.load(Matrix.A)
        B = self.folder.load(Matrix.B)
        C = self.folder.load(Matrix.C)
        f = self.folder.load(Matrix.f)

        return A, B, C, f

    def _get_lca_component_table_names(self, dcf):
        """Return input-table names that start with 'LCA'."""
        return [
            table_name
            for table_name in dcf.inp
            if table_name.lower().startswith('lca')
        ]
    
    def build_scaling_vector(self, dcf):
        """
            Builds the scaling vector used for the LCA calculation.

            The scaling vector is populated using pyH2A input tables
            associated with LCA processes. Unit consistency is enforced
            during population.

            Parameters
            ----------
            dcf : pyH2A.Discounted_Cash_Flow
                pyH2A Discounted_Cash_Flow object containing LCA-related
                input tables and production values.

            Raises
            ------
            ValueError
                If any entries in the scaling vector remain zero after
                processing all LCA input tables.

            Notes
            -----
            The scaling vector must be fully populated to ensure
            correct LCA results. Missing values indicate incomplete
            or inconsistent pyH2A input definitions.
        """

        self.scaling_vector = np.asarray(solve(self.A_modified, self.f)).reshape(-1)

    def update_A_matrix_with_lca_components(self, dcf):
        """
            Updates the first column of the A matrix with LCA component values.
            
            For each LCA component defined in dcf.inp with a UUID, this method
            finds the corresponding index in the technosphere matrix and updates
            the first column with the component's value. If the value is an array/list
            like yearly H2 production, the sum is used.

            Parameters
            ----------
            dcf : pyH2A.Discounted_Cash_Flow
                pyH2A Discounted_Cash_Flow object containing LCA components table.
        """

        lca_table_names = self._get_lca_component_table_names(dcf)
        if len(lca_table_names) == 0:
            raise ValueError(
                "No LCA component tables found in input. "
                "Define at least one table whose name starts with 'LCA'."
            )

        # Resolve any path-based references (e.g. "A > B > Value") into numbers.
        for lca_table_name in lca_table_names:
            process_table(dcf.inp, lca_table_name, 'Value')

        # Safely copy the A matrix (handles both dense and sparse)
        try:
                self.A_modified = self.A.copy()
        except AttributeError:
            # If no copy method, assume it's already safe or convert
                self.A_modified = np.array(self.A)

        component_counter = 0
        for lca_table_name in lca_table_names:
            lca_components = dcf.inp[lca_table_name]

            for component_name, component_data in lca_components.items():
                if 'UUID' not in component_data or 'Value' not in component_data:
                    missing_fields = [
                        key for key in ('UUID', 'Value') if key not in component_data
                    ]
                    raise ValueError(
                        f"LCA component '{component_name}' is missing required "
                        f"field(s): {missing_fields}"
                    )

                uuid = component_data['UUID']
                value = component_data['Value']

                if uuid not in self.tech_index_dict:
                    raise ValueError(
                        f"LCA component '{component_name}' has UUID '{uuid}' "
                        f"which was not found in the technosphere matrix index."
                    )

                # Get the index for this UUID
                tech_index = self.tech_index_dict[uuid].index

                # Handle array values by summing
                if isinstance(value, np.ndarray):
                    value = np.sum(value)

                # Convert list/tuple values similarly and enforce scalar float output.
                if isinstance(value, (list, tuple)):
                    value = np.sum(value)

                try:
                    value = float(value)
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        f"LCA component '{component_name}' resolved to non-numeric value: {value}"
                    ) from exc

                # Update first column (column 0) at the appropriate index.
                # The first component keeps its original sign as product; all others are negated as inputs.
                if component_counter == 0:
                    self.A_modified[tech_index, 0] = value
                else:
                    self.A_modified[tech_index, 0] = -value

                component_counter += 1

    def perform_LCA(self):
        """
            Performs the Life Cycle Impact Assessment (LCIA) calculation.

            The method computes intermediate flows and final impact
            results using the intervention and characterization matrices.
            Results are stored in the class instance.

            Notes
            -----
            Final results are stored in the attribute `lca_results`
            as a dictionary mapping impact names to values and units.
        """

        g = self.B @ self.scaling_vector
        h = self.C @ g

        # Adding real data export into LCA class instance instead of printing results
        self.lca_results = {}
        for i in self.folder.impact_index():
            self.lca_results[i.impact_name] = {
                'value': h[i.index],
                'unit': i.impact_unit
            }

        for impact_name, data in self.lca_results.items():
                print(f"{impact_name} , {data['value']:.5f} , {data['unit']}")            

def process_LCA_table(scaling_vector: np.ndarray, input_table: dict, tech_index_dict: dict):
    """
    Processes an LCA input table and populates the scaling vector.

    Each row in the input_table must have 'UUID', 'Value', and 'Unit'.
    Units are validated and converted to the reference flow units from the LCA export.

    Parameters
    ----------
    scaling_vector : numpy.ndarray
        Vector used to scale LCA processes.
    input_table : dict
        pyH2A-formatted input table containing process UUIDs,
        values, and units.
    tech_index_dict : dict
        Dictionary mapping process UUIDs to TechEntry objects

    Raises
    ------
    KeyError
        If required keys such as 'UUID', 'Value', or 'Unit' are missing.
    ValueError
        If the unit in the input table is unsupported or incompatible.
    """

    # Allowed conversions to reference units
    unit_conversion = {
        ('ton', 'kg'): 1000,
        ('kg', 'kg'): 1,
        ('m2', 'm2'): 1,
        ('kWh', 'MJ'): 3.6,
        ('MJ', 'MJ'): 1,
        ('-', 'Item(s)'): 1,
        ('Item(s)', 'Item(s)'): 1
    }

    for key in input_table:
        entry = input_table[key]

        # Required keys (raises KeyError if missing)
        uuid = entry['UUID']
        value = entry['Value']
        try:
            unit = entry['Unit']
        except KeyError:
            raise KeyError(f"'Unit' missing for process {key} in input table")

        # Reference unit from LCA export
        expected_unit = tech_index_dict[uuid].flow_unit

        # Determine conversion factor
        conversion_key = (unit, expected_unit)
        if conversion_key not in unit_conversion:
            raise ValueError(
                f"Unsupported or incompatible unit '{unit}' for process "
                f"'{tech_index_dict[uuid].process_name}' (expected '{expected_unit}')"
            )

        value_converted = value * unit_conversion[conversion_key]

        # Populate scaling vector
        tech_index = tech_index_dict[uuid].index
        scaling_vector[tech_index] = value_converted


def lcia_example():
    """
        Example function demonstrating how to perform an LCIA
        calculation using an openLCA matrix export.

        Notes
        -----
        This function is intended for demonstration and testing
        purposes and prints impact assessment results to stdout.
    """

    folder = ExportFolder('data/LCA/LCA_Test_Data')

    if not folder.has_impacts():
        print('error: no impacts in your export')
        return
    

    tech_index = folder.tech_index()
    pp.pprint(tech_index['0b61b77e-1364-404e-a16e-fb473dc1486a'].process_name)

    #pp.pprint(vars(tech_index[0]))

    # load the matrices
    A = folder.load(Matrix.A)
    B = folder.load(Matrix.B)
    C = folder.load(Matrix.C)
    f = folder.load(Matrix.f)


    # calculate the LCIA result
    scaling = solve(A, f)
    g = B @ scaling
    print(f)
    h = C @ g

    for i in folder.impact_index():
        print('%s , %.5f , %s' % (i.impact_name, h[i.index], i.impact_unit))


if __name__ == '__main__':
    lcia_example()
