"""@package urlautomation.database.manager
This module contains the implementation of the DatabaseManager class.
"""

from urlautomation.database.types import Base, Domain, Organization
from urlautomation.database.fetchers import ALL_DATAFETCHERS

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from typing import List, Tuple, Union, Optional

import os.path


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
        self._engine = create_engine(f"sqlite:///{db_path}", echo=False)
        self._Session = sessionmaker(bind=self._engine)
        self._session: Session = None
        self._datafetchers = {
            name: fetcher_cls(self) for name, fetcher_cls in ALL_DATAFETCHERS.items()
        }
        Base.metadata.create_all(self._engine)

    def _get_session(self) -> Session:
        """Returns the current session.
        @return The current session.
        """
        if self._session is None:
            self._session = self._Session()
        return self._session

    def __enter__(self) -> Session:
        self._session = self._get_session()
        return self._session

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type:
            self._session.rollback()
        else:
            self._session.commit()
        self._session.close()

    def fetch_data(
        self, fetcher: str, domains: Union[str, List[str]], **kwargs
    ) -> None:
        """Fetches data from the specified fetcher.
        @param fetcher The name of the fetcher to use.
        @param domains The domains to fetch data for.
        """
        if fetcher not in self._datafetchers:
            raise ValueError(f"Fetcher {fetcher} not found.")
        self._datafetchers[fetcher].fetch_data(domains, **kwargs)
