from pyH2A.Utilities.input_modification import process_table


class Test_Plugin_Case_1_Without_Resolver:

    def __init__(self, dcf, print_info):
        process_table(dcf.inp, "My Table", "Value")
        process_table(dcf.inp, "My Second Table", "Value")
        process_table(dcf.inp, "My Third Table", "Value")
        process_table(dcf.inp, "My Fourth Table", "Value")
        process_table(dcf.inp, "My Fifth Table", "Value")
