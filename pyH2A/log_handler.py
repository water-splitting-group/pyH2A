import logging
import os
from pythonjsonlogger import json

class Log_Handler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.log_entries = []

    def emit(self, record):
        log_entry = self.format(record)
        self.log_entries.append(log_entry)

    def get_log_entries(self):
        return self.log_entries

def setup_logging(log_file=None):
    """
    Configures the logging system for the entire project.
    """

    if log_file:
            log_directory = os.path.dirname(log_file)
            if not os.path.exists(log_directory):
                os.makedirs(log_directory)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    formatter = json.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s %(calculation)s %(result)s'
    )

    list_handler = Log_Handler()
    list_handler.setFormatter(formatter)
    root_logger.addHandler(list_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    return root_logger, list_handler
