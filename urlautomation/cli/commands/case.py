"""@package urlautomation.cli.case
Main package for the CLI of the URL Automation project.
This package contains the code for the Command Line Interface (CLI)
"""

from argparse import ArgumentParser

from urlautomation.cli.subcommand import SubCommand
from urlautomation.database.types import (
    Case,
    CaseDomain,
    Domain,
    DNSRecord,
    ARecordValue,
    NSRecordValue,
    NSRecordNameserver,
)


class CaseCommand(SubCommand):
    """Class for handling case commands in the CLI."""

    @classmethod
    def add_arguments(cls: "CaseCommand", parser: ArgumentParser):
        subparsers = parser.add_subparsers(dest=cls.__name__, required=True)

        # Create
        create = subparsers.add_parser(
            "create",
            help="Create a new case",
        )
        create.add_argument(
            "--name",
            required=True,
            help="Name of the case to create",
        )
        # Create END

        # List
        list = subparsers.add_parser(
            "list",
            help="List cases",
        )
        list.add_argument(
            "--id",
            required=False,
            help="ID of the case to list",
        )
        # List END

        # Update
        update = subparsers.add_parser(
            "update",
            help="Update an existing case",
        )
        # Update END

        # Delete
        delete = subparsers.add_parser(
            "delete",
            help="Delete a case",
        )
        # Delete END

        # Report
        report = subparsers.add_parser(
            "report",
            help="Generate a report for a case",
        )
        report.add_argument(
            "--case",
            required=True,
            help="Name of the case to report",
        )
        # Report END

        # Domains
        domains = subparsers.add_parser(
            "domains",
            help="Manage domains in a case",
        )
        domain_subparser = domains.add_subparsers(dest="domain_command", required=True)
        domains_list = domain_subparser.add_parser(
            "list",
            help="List domains in a case",
        )
        domains_list.add_argument(
            "--case",
            required=True,
            help="Name of the case to list domains from",
        )

        domains_add = domain_subparser.add_parser(
            "add",
            help="Add a domain to a case",
        )
        domains_add.add_argument(
            "--case",
            required=True,
            help="Name of the case to add a domain to",
        )
        domains_add.add_argument(
            "--domains",
            required=True,
            nargs="+",
            help="Domain name(s) to add",
        )

        domains_del = domain_subparser.add_parser(
            "delete",
            help="Delete a domain from a case",
        )
        domains_del.add_argument(
            "--case",
            required=True,
            help="Name of the case to delete a domain from",
        )
        domains_del.add_argument(
            "--domains",
            required=True,
            nargs="+",
            help="Domain name(s) to delete",
        )
        # Domains END

        # Info
        info = subparsers.add_parser(
            "info",
            help="Get information about a case",
        )
        info.add_argument(
            "--cases",
            required=True,
            nargs="+",
            help="Name of the case to get information about",
        )

    def _create_case(self):
        with self._database as session:
            # Check if the case already exists
            existing_case = (
                session.query(Case).filter_by(case_name=self._args.name).first()
            )
            if existing_case:
                self._logger.error(f"Case '{self._args.name}' already exists.")
                return

            # Create a new case
            new_case = Case(case_name=self._args.name)
            session.add(new_case)
            session.commit()

            self._logger.info(f"Case '{self._args.name}' created successfully.")

    def _list_cases(self):
        pass

    def _report_case(self):
        with self._database as session:
            domain_cases = (
                session.query(CaseDomain)
                .join(Case)
                .filter(Case.case_name == self._args.case)
                .all()
            )

            # Collect all domains involved in this case
            domains_in_case = {
                case_domain.domain.domain_name for case_domain in domain_cases
            }
            relationships = {
                # "SSL Certificate": [],
                "A Record (IP Address)": [],
                "NS Record (Name Server)": [],
            }

            print(f"\n{'='*50}\nDOMAIN RELATIONSHIP REPORT\n{'='*50}")
            print(f"\nViewing relationships for case: {self._args.case}\n")
            print(f"Search domains: {', '.join(domains_in_case)}\n")

            for case_domain in domain_cases:
                target_domain = case_domain.domain

                # Find domains sharing SSL identities
                # TODO

                # Find domains sharing A Record IPs
                dns_record = (
                    session.query(DNSRecord)
                    .filter_by(domain_id=target_domain.domain_id)
                    .first()
                )
                if dns_record:
                    for a_record in dns_record.a_records:
                        related_dns_records = (
                            self._database.get_related_records_by_a_record(
                                session, a_record
                            )
                        )
                        for related_dns_record in related_dns_records:
                            related_domain = related_dns_record.domain
                            if related_domain.domain_name != target_domain.domain_name:
                                relationships["A Record (IP Address)"].append(
                                    f"{related_domain.domain_name} shares the same A Record IP ({a_record.ip_addresses[0].ip_address}) as {target_domain.domain_name}"
                                )

                    # Find domains sharing NS Records (Name Servers)
                    for ns_record in dns_record.ns_records:
                        related_dns_records = (
                            self._database.get_related_records_by_ns_record(
                                session, ns_record
                            )
                        )
                        for related_dns_record in related_dns_records:
                            related_domain = related_dns_record.domain
                            if related_domain.domain_name != target_domain.domain_name:
                                relationships["NS Record (Name Server)"].append(
                                    f"{related_domain.domain_name} uses the same Name Server ({ns_record.nameservers[0].nameserver}) as {target_domain.domain_name}"
                                )

            # Print relationships in a grouped format
            for category, relation_list in relationships.items():
                print(f"\n{category} Relationships:")
                if relation_list:
                    for relation in relation_list:
                        print(f"- {relation}")
                else:
                    print("- None found")

            print("\n" + "=" * 50)

    def _info_case(self):
        with self._database as session:
            # Check if the case exists
            for case in self._args.cases:
                existing_case = (
                    session.query(Case).filter(Case.case_name == case).first()
                )
                if not existing_case:
                    self._logger.error(f"Case '{case}' does not exist.")
                    continue

                # Print case information
                self._logger.info(f"Case ID: {existing_case.case_id}")
                self._logger.info(f"    - Name: {existing_case.case_name}")
                self._logger.info(
                    f"    - Investigating Officer: {existing_case.investigating_officer}"
                )
                self._logger.info(f"    - Date Opened: {existing_case.date_opened}")
                self._logger.info(f"    - Date Closed: {existing_case.date_closed}")
                self._logger.info(f"    - Status: {existing_case.case_status}")
                self._logger.info(f"    - Description: {existing_case.description}")

    def _domains_command(self):
        with self._database as session:
            # Check if the case exists
            existing_case = (
                session.query(Case).filter(Case.case_name == self._args.case).first()
            )
            if not existing_case:
                self._logger.error(f"Case '{self._args.case}' does not exist.")
                return

            # Handle subcommands for domains
            if self._args.domain_command == "list":
                self._logger.info(
                    f"Listing domains for case '{existing_case.case_name}':"
                )
                domains = existing_case.domains
                for case_domain in domains:
                    domain = case_domain.domain
                    self._logger.info(f"- {domain.domain_name}")
            elif self._args.domain_command == "add":
                for domain in self._args.domains:
                    existing_domain = (
                        session.query(Domain).filter_by(domain_name=domain).first()
                    )
                    if not existing_domain:
                        self._logger.error(
                            f"Domain '{domain}' does not exist in the database."
                        )
                        continue
                    existing_case_domain = (
                        session.query(CaseDomain)
                        .filter_by(
                            case_id=existing_case.case_id,
                            domain_id=existing_domain.domain_id,
                        )
                        .first()
                    )
                    if existing_case_domain:
                        self._logger.error(
                            f"Domain '{domain}' already exists in case '{existing_case.case_name}'."
                        )
                        continue
                    new_case_domain = CaseDomain(
                        case_id=existing_case.case_id,
                        domain_id=existing_domain.domain_id,
                    )
                    session.add(new_case_domain)
                    existing_case.domains.append(new_case_domain)
                    self._logger.info(
                        f"Domain '{domain}' added to case '{existing_case.case_name}'."
                    )
                # Commit the changes to the database after adding the domains
                session.commit()
            elif self._args.domain_command == "delete":
                for domain in self._args.domains:
                    domain_to_delete = (
                        session.query(Domain).filter_by(domain_name=domain).first()
                    )
                    if not domain_to_delete:
                        self._logger.error(
                            f"Domain '{domain}' does not exist in the database."
                        )
                        continue
                    case_domain_to_delete = (
                        session.query(CaseDomain)
                        .filter_by(
                            case_id=existing_case.case_id,
                            domain_id=domain_to_delete.domain_id,
                        )
                        .first()
                    )
                    if not case_domain_to_delete:
                        self._logger.error(
                            f"Domain '{domain}' does not exist in case '{existing_case.case_name}'."
                        )
                        continue
                    session.delete(case_domain_to_delete)
                    self._logger.info(
                        f"Domain '{domain}' deleted from case '{existing_case.case_name}'."
                    )
                # Commit the changes to the database after deleting the domains
                session.commit()

    def execute(self, command: str):
        if command == "create":
            self._create_case()
        elif command == "list":
            self._list_cases()
        elif command == "report":
            self._report_case()
        elif command == "info":
            self._info_case()
        elif command == "domains":
            self._domains_command()
