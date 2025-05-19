"""@package urlautomation.cli.domain
Main package for the CLI of the URL Automation project.
This package contains the code for the Command Line Interface (CLI)
"""

from argparse import ArgumentParser
from collections import defaultdict
from typing import List, Tuple

from urlautomation.cli.subcommand import SubCommand
from urlautomation.database.types import (
    Domain,
    ARecordValue,
    ARecordIP,
    DNSRecord,
    NSRecordValue,
    NSRecordNameserver,
    a_record_ip_association,
)

from sqlalchemy.orm import aliased

import re


DOMAIN_NAME_REGEX = re.compile(r"^(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$")


class DomainCommand(SubCommand):
    """Class for handling domain commands in the CLI."""

    @classmethod
    def add_arguments(cls: "DomainCommand", parser: ArgumentParser):
        subparsers = parser.add_subparsers(dest=cls.__name__, required=True)
        fetch = subparsers.add_parser(
            "fetch",
            help="Fetch information about a domain",
        )
        fetch.add_argument(
            "--dump",
            action="store_true",
            help="Dump the results of web requests to JSON files.",
        )
        fetch.add_argument(
            "--simulate",
            action="store_true",
            help="Simulate the fetch based on hardcoded responses.",
        )
        search = subparsers.add_parser(
            "search",
            help="Search for links to a domain",
        )
        query = subparsers.add_parser(
            "query",
            help="Query information about a domain",
        )
        fetch.add_argument(
            "name",
            help="Name of the domain to fetch for",
        )
        search.add_argument(
            "name",
            help="Name of the domain to search for",
        )
        query.add_argument(
            "name",
            help="Name of the domain to query for",
        )

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

    def _fetch_domain(self):
        domain_name = self._args.name
        assert DOMAIN_NAME_REGEX.match(domain_name), "Invalid domain name provided."

        try:
            self._database.fetch_data(
                fetcher="crtsh",
                domains=domain_name,
                dump=self._args.dump,
                simulate=self._args.simulate,
            )
            self._database.fetch_data(
                fetcher="securitytrails",
                domains=domain_name,
                apikey=self._config["securitytrails_api_key"],
                dump=self._args.dump,
                simulate=self._args.simulate,
            )
        except Exception as e:
            self._logger.exception(
                f"Failed to fetch data for domain {domain_name}: {e}"
            )
            return

    def _search_domain(self):
        domain_name = self._args.name
        assert DOMAIN_NAME_REGEX.match(domain_name), "Invalid domain name provided."

        with self._database as session:
            domain = (
                session.query(Domain).filter(Domain.domain_name == domain_name).first()
            )
            if not domain:
                self._logger.info("No domain found with the name %s", domain_name)
                return

            for domain1_name, domain2_name, ip in self._find_ip_associations(
                session, domain
            ):
                self._logger.info(
                    f"LINK between {domain1_name} -> {domain2_name}, there are A records sharing the IP address {ip}"
                )

            for ns_domain_name, nameserver in self._find_nameserver_associations(
                session, domain
            ):
                self._logger.info(
                    f"LINK between {domain_name} -> {ns_domain_name}, there are NS records sharing nameserver {nameserver}"
                )

    def _query_domain(self):
        domain_name = self._args.name
        assert DOMAIN_NAME_REGEX.match(domain_name), "Invalid domain name provided."

        # Query database for SSL records associated with the domain
        with self._database as session:
            domain_records: List[Domain] = (
                session.query(Domain).filter(Domain.domain_name == domain_name).all()
            )

            for record in domain_records:
                self._logger.info("- Domain: %s", record.domain_name)
                self._logger.info("  - ID: %d", record.domain_id)

                # The DNS records associated with the domain
                self._logger.info("  - DNS Records:")
                for dns_record in record.dns_records:
                    self._logger.info("      - A Records:")
                    for a_record in dns_record.a_records:
                        self._logger.info(
                            "            - %s", a_record.a_record_value_id
                        )
                        self._logger.info(
                            "                - First seen: %s", a_record.first_seen
                        )
                        self._logger.info(
                            "                - Last seen: %s", a_record.last_seen
                        )
                        for ip_address in a_record.ip_addresses:
                            self._logger.info(
                                "                - %s", ip_address.ip_address
                            )
                    self._logger.info("      - NS Records:")
                    for ns_record in dns_record.ns_records:
                        self._logger.info(
                            "            - %s", ns_record.ns_record_value_id
                        )
                        self._logger.info(
                            "                - First seen: %s", ns_record.first_seen
                        )
                        self._logger.info(
                            "                - Last seen: %s", ns_record.last_seen
                        )
                        for nameserver in ns_record.nameservers:
                            self._logger.info(
                                "                - %s", nameserver.nameserver
                            )

                # The SSL certificates associated with the domain
                self._logger.info("  - SSL Certificates:")
                for ssl_cert in record.ssl_certificates:
                    self._logger.info("    - %s", ssl_cert.certificate_id)
                    self._logger.info("      - Issuer: %s", ssl_cert.issuer_name)
                    self._logger.info("      - Common Name: %s", ssl_cert.common_name)
                    self._logger.info("      - Valid From: %s", ssl_cert.not_before)
                    self._logger.info("      - Valid To: %s", ssl_cert.not_after)
                    self._logger.info(
                        "      - Serial Number: %s", ssl_cert.serial_number
                    )

                    # The identities associated with the SSL certificate
                    self._logger.info("      - Identities:")
                    for identity in ssl_cert.identities:
                        self._logger.info("            - %s", identity.identity)

    def execute(self, command: str):
        """Execute the command."""
        if command == "fetch":
            self._fetch_domain()
        elif command == "search":
            self._search_domain()
        elif command == "query":
            self._query_domain()
