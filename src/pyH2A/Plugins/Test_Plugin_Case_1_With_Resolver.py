from pyH2A.Utilities.IO import input_resolver_function

input_dict_tables_2_3 = {
    "My Second Table": {
        "Variable_2": {
            "Value": {"type": {float, int}, "bounds": (0, None)},
            "Unit": {"dimension": "mass"},
            "description": "Issue 108 Value",
        }
    },
    "My Third Table": {
        "Variable_3": {
            "Value": {"type": {float, int}, "bounds": (0, None)},
            "Unit": {"dimension": "mass"},
            "description": "Issue 108 Value",
        }
    },
}


input_dict_table_1 = {
    "My Table": {
        "Variable": {
            "Value": {"type": {float, int}, "bounds": (0, None)},
            "Unit": {"dimension": "mass"},
            "description": "Issue 108 Variable 1",
        },
        "Variable_1": {
            "Value": {"type": {float, int}, "bounds": (0, None)},
            "Unit": {"dimension": "area"},
            "description": "Issue 108 Variable 2",
        },
    }
}


input_dict_tables_4_5 = {
    "My Fourth Table": {
        "Variable_4": {
            "Value": {"type": {float, int}, "bounds": (0, None)},
            "Unit": {"dimension": "mass"},
            "description": "Issue 108 Value",
        }
    },
    "My Fifth Table": {
        "Variable_5": {
            "Value": {"type": {float, int}, "bounds": (0, None)},
            "Unit": {"dimension": "mass"},
            "description": "Issue 108 Value",
        }
    },
}


class Test_Plugin_Case_1_With_Resolver:

    def __init__(self, dcf, print_info):

        # Case 1: resolve tables 2 and 3 before table 1
        self.tables_2_3 = input_resolver_function(
            input_dict_tables_2_3,
            dcf,
            __name__,
        )

        # Case 2: resolve table 1 after tables 2 and 3
        self.table_1 = input_resolver_function(
            input_dict_table_1,
            dcf,
            __name__,
        )

        # Case 3: resolve tables 4 and 5 after table 1
        self.tables_4_5 = input_resolver_function(
            input_dict_tables_4_5,
            dcf,
            __name__,
        )

        self.inp = {
            "tables_2_3": self.tables_2_3,
            "table_1": self.table_1,
            "tables_4_5": self.tables_4_5,
        }
