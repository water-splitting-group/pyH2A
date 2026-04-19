"""
Handling of inputs and outputs for pyH2A plugins.
"""

from .input_resolver import input_resolver_function
from .output_inserter import output_inserter_function

__all__ = [
    'input_resolver_function', 
    'output_inserter_function'
]