"""@package urlautomation.database.manager
This module contains the implementation of the DatabaseManager class.
"""

from urlautomation.database.types import (
    Base,
    Domain,
    Organization,
    DNSRecord,
    ARecordValue,
    NSRecordValue,
    NSRecordNameserver,
    ARecordIP,
)
from urlautomation.database.fetchers import ALL_DATAFETCHERS

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, aliased

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

    @staticmethod
    def _find_ip_associations(session, domain: Domain) -> List[Tuple[str, str, str]]:
        domain1 = aliased(Domain)
        domain2 = aliased(Domain)
        dns_record1 = aliased(DNSRecord)
        dns_record2 = aliased(DNSRecord)
        a_record1 = aliased(ARecordValue)
        a_record2 = aliased(ARecordValue)
        ip_address = aliased(ARecordIP)

        return (
            session.query(
                domain1.domain_name, domain2.domain_name, ip_address.ip_address
            )
            .join(dns_record1, domain1.dns_records)
            .join(a_record1, dns_record1.a_records)
            .join(ip_address, a_record1.ip_addresses)
            .join(a_record2, ip_address.a_records)
            .join(dns_record2, a_record2.dns_record)
            .join(domain2, dns_record2.domain)
            .filter(domain1.domain_id == domain.domain_id)
            .filter(domain1.domain_id != domain2.domain_id)
            .all()
        )

    @staticmethod
    def _find_nameserver_associations(session, domain: Domain) -> List[Tuple[str, str]]:
        domain1 = aliased(Domain)
        domain2 = aliased(Domain)
        dns_record1 = aliased(DNSRecord)
        dns_record2 = aliased(DNSRecord)
        ns_record1 = aliased(NSRecordValue)
        ns_record2 = aliased(NSRecordValue)
        nameserver = aliased(NSRecordNameserver)

        return (
            session.query(domain2.domain_name, nameserver.nameserver)
            .join(dns_record1, domain1.dns_records)
            .join(ns_record1, dns_record1.ns_records)
            .join(nameserver, ns_record1.nameservers)
            .join(ns_record2, nameserver.ns_records)
            .join(dns_record2, ns_record2.dns_record)
            .join(domain2, dns_record2.domain)
            .filter(domain1.domain_id == domain.domain_id)
            .filter(domain1.domain_id != domain2.domain_id)
            .all()
        )
