from pyH2A.DiscountedCashFlow import DiscountedCashFlow
from pyH2A.Utilities.input_modification import insert, process_table
import pint

class Plugin:
    def __init__(
            self, 
            dcf: DiscountedCashFlow
            ) -> None:
        self.dcf: DiscountedCashFlow = dcf
        self.insert_queue: list[tuple[str,str,pint.Quantity]] = []
        
    def process_table(
            self, 
            table_keys: list[str]
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
            insert(self.dcf, key, subkey, 'Value', value, __name__, self.dcf.print_info)
            if self.dcf.print_info:
                self.logger.debug(f"{key} > {subkey} > Value: {value}")
        self.insert_queue.clear()
