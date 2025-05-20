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
        search = subparsers.add_parser(
            "search",
            help="Search for links to a domain",
        )
        query = subparsers.add_parser(
            "query",
            help="Query information about a domain",
        )
        list = subparsers.add_parser(
            "list",
            help="List all domains",
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
        fetch.add_argument(
            "--quick",
            action="store_true",
            help="Fetch only data that can be gathered from minimal requests (e.g. no extended info for SSL certificates).",
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

    def _fetch_domain(self):
        domain_name = self._args.name
        assert DOMAIN_NAME_REGEX.match(domain_name), "Invalid domain name provided."

        try:
            self._database.fetch_data(
                fetcher="crtsh",
                domains=domain_name,
                dump=self._args.dump,
                simulate=self._args.simulate,
                quick=self._args.quick,
            )
            self._database.fetch_data(
                fetcher="securitytrails",
                domains=domain_name,
                apikey=self._config["securitytrails_api_key"],
                dump=self._args.dump,
                simulate=self._args.simulate,
                quick=self._args.quick,
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

            for domain1_name, domain2_name, ip in self._database._find_ip_associations(
                session, domain
            ):
                self._logger.info(
                    f"LINK between {domain1_name} -> {domain2_name}, there are A records sharing the IP address {ip}"
                )

            for (
                ns_domain_name,
                nameserver,
            ) in self._database._find_nameserver_associations(session, domain):
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
                        self._logger.info("                - IP Addresses:")
                        for ip_address in a_record.ip_addresses:
                            self._logger.info(
                                "                    - %s", ip_address.ip_address
                            )
                        self._logger.info("                - Organizations:")
                        for organization in a_record.organizations:
                            self._logger.info(
                                "                    - %s",
                                organization.organization_name,
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
                        self._logger.info("                - Nameservers:")
                        for nameserver in ns_record.nameservers:
                            self._logger.info(
                                "                   - %s", nameserver.nameserver
                            )
                        self._logger.info("                - Organizations:")
                        for organization in ns_record.organizations:
                            self._logger.info(
                                "                   - %s",
                                organization.organization_name,
                            )

                    # Log identities first, then their associated SSL certificates
                    self._logger.info("  - Identities:")
                    for identity in record.identities:
                        self._logger.info("    - %s", identity.identity)

                        # Log the SSL certificate linked to this identity
                        ssl_cert = identity.certificate
                        self._logger.info("      - SSL Certificate:")
                        self._logger.info(
                            "          - Certificate ID: %s", ssl_cert.certificate_id
                        )
                        self._logger.info(
                            "          - Issuer: %s", ssl_cert.issuer_name
                        )
                        self._logger.info(
                            "          - Valid From: %s", ssl_cert.not_before
                        )
                        self._logger.info(
                            "          - Valid To: %s", ssl_cert.not_after
                        )
                        self._logger.info(
                            "          - Serial Number: %s", ssl_cert.serial_number
                        )

                        # Additional fields
                        self._logger.info(
                            "          - Subject Key Identifier: %s",
                            ssl_cert.subject_key_identifier,
                        )
                        self._logger.info(
                            "          - Authority Key Identifier: %s",
                            ssl_cert.authority_key_identifier,
                        )
                        self._logger.info(
                            "          - Public Key Algorithm: %s",
                            ssl_cert.public_key_algorithm,
                        )
                        self._logger.info(
                            "          - Public Key Size: %s",
                            ssl_cert.public_key_size,
                        )
                        self._logger.info(
                            "          - Public Key Modulus: %s",
                            ssl_cert.public_key_modulus,
                        )
                        self._logger.info(
                            "          - Public Key Exponent: %s",
                            ssl_cert.public_key_exponent,
                        )
                        self._logger.info(
                            "          - Signature Algorithm: %s",
                            ssl_cert.signature_algorithm,
                        )
                        self._logger.info(
                            "          - Signature: %s", ssl_cert.signature
                        )

                        # Log associated domains under the identity
                        self._logger.info("      - Associated Domains:")
                        for domain in identity.domains:
                            self._logger.info("          - %s", domain.domain_name)

    def _list_domains(self):
        """List all domains in the database."""
        with self._database as session:
            domains = session.query(Domain).all()
            if not domains:
                self._logger.info("No domains found in the database.")
                return

            for domain in domains:
                self._logger.info("- Domain: %s", domain.domain_name)
                self._logger.info("  - ID: %d", domain.domain_id)

    def execute(self, command: str):
        """Execute the command."""
        if command == "fetch":
            self._fetch_domain()
        elif command == "search":
            self._search_domain()
        elif command == "query":
            self._query_domain()
        elif command == "list":
            self._list_domains()
