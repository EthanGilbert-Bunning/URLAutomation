"""@package urlautomation.database
This module contains implementations for interacting with the database.
"""

from urlautomation.database.manager import DatabaseManager as DatabaseManager

from urlautomation.database.adapters import __adapters__, __converters__
from sqlite3 import register_adapter, register_converter

# Register our custom adapters and converters with sqlite3
# in __init__.py so that they will be implicitly available
# when the module is imported from other modules.
for adapter in __adapters__:
    register_adapter(adapter[0], adapter[1])
for converter in __converters__:
    register_converter(converter[0], converter[1])
