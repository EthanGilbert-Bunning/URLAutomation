"""@package urlautomation.database.manager
This module contains the implementation of the DatabaseManager class.
"""

from urlautomation.database.adapters import *

import sqlite3


class DatabaseManager:
    """This class is responsible for managing the database connection and
    executing queries.
    Currently, the database engine used is SQLite, but this class is designed
    with the idea that it can be easily modified to support other engines.
    """

    def __init__(self, db_path: str):
        """Initializes the DatabaseManager with a database connection.
        @param db_path The path to the database file.
        """
        assert db_path, "Database path cannot be None or empty."
        self._connection: sqlite3.Connection = sqlite3.connect(db_path)
        self._cursor: sqlite3.Cursor = self._connection.cursor()
