"""@package urlautomation.cli.subcommand
Main package for the CLI of the URL Automation project.
This package contains the code for the Command Line Interface (CLI)
"""

from argparse import ArgumentParser, Namespace

from urlautomation.database.manager import DatabaseManager

import logging


class SubCommand:
    """Class to represent a subcommand in the CLI."""

    @classmethod
    def add_arguments(cls: "SubCommand", parser: ArgumentParser):
        raise NotImplementedError

    def __init__(self, arguments: Namespace, config: dict, database: DatabaseManager):
        """Class constructor for DomainCommand."""
        self._args = arguments
        self._config = config
        self._database = database
        self._logger = logging.getLogger(__name__)

    def execute(self, command: str):
        """Execute the command."""
        raise NotImplementedError
