"""@package urlautomation.cli.case
Main package for the CLI of the URL Automation project.
This package contains the code for the Command Line Interface (CLI)
"""

from argparse import ArgumentParser

from urlautomation.cli.subcommand import SubCommand


class CaseCommand(SubCommand):
    """Class for handling case commands in the CLI."""

    @classmethod
    def add_arguments(cls: "CaseCommand", parser: ArgumentParser):
        subparsers = parser.add_subparsers(dest=cls.__name__, required=True)
        create = subparsers.add_parser(
            "create",
            help="Create a new case",
        )
        list = subparsers.add_parser(
            "list",
            help="List cases",
        )
        list.add_argument(
            "--id",
            required=False,
            help="ID of the case to list",
        )
        update = subparsers.add_parser(
            "update",
            help="Update an existing case",
        )
        delete = subparsers.add_parser(
            "delete",
            help="Delete a case",
        )

    def _create_case(self) -> int:
        pass

    def _list_cases(self):
        pass

    def execute(self, command: str):
        if command == "create":
            self._create_case()
        elif command == "list":
            self._list_cases()
