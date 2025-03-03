from pyH2A.Utilities.input_modification import insert, process_table

class Plugin:
    def __init__(
            self, 
            dcf: dict, 
            print_info: bool = False
            ) -> None:
        self.dcf = dcf
        self.insert_queue = []
        self.print_info = print_info
        
    def process_table(
            self, 
            table_keys: list
            ) -> None:
        '''Processes input table.
        '''
        for table_key in table_keys:
            process_table(self.dcf.inp, table_key, 'Value')

    def insert_table(
            self
            ) -> None:
        '''Inserts the calculated values into the DCF.
        '''
        for key, subkey, value in self.insert_queue:
            insert(self.dcf, key, subkey, 'Value', value, __name__, self.print_info)
            #self.logger.debug(f"{key} > {subkey} > Value: {value}")
        self.insert_queue = []
