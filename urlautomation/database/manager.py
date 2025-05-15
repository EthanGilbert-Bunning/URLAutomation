"""@package urlautomation.database.manager
This module contains the implementation of the DatabaseManager class.
"""

from urlautomation.database.adapters import *
from urlautomation.database.constants import (
    DATABASE_SETUP_SCRIPT,
    INSERT_TABLE_QUERIES,
)
from urlautomation.objects import SSLRecord, SSLRecordDBMeta

from typing import List, Tuple, Union, Optional

import sqlite3, os.path


class DatabaseManager:
    """This class is responsible for managing the database connection and
    executing queries.
    Currently, the database engine used is SQLite, but this class is designed
    with the idea that it can be easily modified to support other engines.
    """

    def __init__(self, db_path: str) -> None:
        """Initializes the DatabaseManager with a database connection.
        @param db_path The path to the database file.
        """
        self._connection: sqlite3.Connection = None
        self._cursor: sqlite3.Cursor = None
        self._path: str = db_path
        self._setup_tables = not os.path.exists(db_path)

    def require_connection(func):
        def wrapper(self, *args, **kwargs):
            if not self._connection:
                raise RuntimeError("Database connection is not established.")
            return func(self, *args, **kwargs)

        return wrapper

    def connect(self) -> None:
        """Connects to the database.
        @param path The path to the database file.
        """
        self._connection = sqlite3.connect(self._path)
        self._cursor = self._connection.cursor()

        # Enable foreign key constraints for integrity.
        # TODO: Enable this after domain record insertion / retrieval is implemented
        # and relationships can be enforced.
        # self._cursor.execute("PRAGMA foreign_keys = ON;")

        # If we've opened this database for the first time, create tables.
        if self._setup_tables:
            self.create_tables()

    @require_connection
    def close(self) -> None:
        """Closes the database connection."""
        self._connection.close()
        self._connection = None
        self._cursor = None

    @require_connection
    def create_tables(self):
        """Creates the tables in the database if they do not exist.
        This method uses the CREATE_TABLE_QUERIES class variable to create
        the tables.
        """
        self._cursor.executescript(DATABASE_SETUP_SCRIPT)
        self._connection.commit()
        self._setup_tables = False

    @require_connection
    def fetch_ssl_records(
        self, criteria: Optional[str] = None, args: Optional[Tuple] = ()
    ) -> Union[SSLRecord, List[SSLRecord]]:
        """Convenience method for fetching SSL records from the database.
        @param criteria will be appended to "SELECT * FROM ssl_certificates".
        @param *args Additional arguments to be passed to execute().
        @return A list of SSLRecord objects.
        """
        self._cursor.execute(f"SELECT * FROM ssl_certificates {criteria}", args)
        rows = self._cursor.fetchall()
        return [
            SSLRecord(
                meta=SSLRecordDBMeta(certificate_id=row[0], domain_id=row[1]),
                issuer_ca_id=row[2],
                issuer_name=row[3],
                common_name=row[4],
                names=row[5].splitlines(),
                entry_timestamp=row[6],
                not_before=row[7],
                not_after=row[8],
                serial_number=row[9],
            )
            for row in rows
        ]

    @require_connection
    def add_ssl_records(self, records: Union[SSLRecord, List[SSLRecord]]) -> None:
        """Adds SSL records to the database.
        @param records A list of SSLRecord objects.
        """
        if isinstance(records, SSLRecord):
            records = [records]

        for record in records:
            self._cursor.execute(
                INSERT_TABLE_QUERIES["ssl_certificates"],
                (
                    0,  # TODO
                    record.issuer_ca_id,
                    record.issuer_name,
                    record.common_name,
                    "\n".join(record.names),
                    record.entry_timestamp,
                    record.not_before,
                    record.not_after,
                    record.serial_number,
                ),
            )
        self._connection.commit()

    def __enter__(self):
        """Enables the use of the 'with' statement for the DatabaseManager."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Ensures that the database connection is closed when exiting the 'with' statement."""
        self.close()
