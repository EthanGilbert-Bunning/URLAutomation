"""@package urlautomation.cli
Main package for the CLI of the URL Automation project.
This package contains the code for the Command Line Interface (CLI)
"""

from urlautomation.cli.commands import ALL_SUBCOMMANDS
from urlautomation.database.manager import DatabaseManager

from argparse import ArgumentParser, Namespace

import logging
import json


class CommandLine:
    def __init__(self):
        """Class constructor for CommandLine."""
        self._args: Namespace = None
        self._config: dict = None
        self._database: DatabaseManager = None
        self._logger = logging.getLogger(__name__)

    def parse_args(self):
        """Parse command line arguments."""
        parser = ArgumentParser(description="URL Automation CLI")
        parser.add_argument(
            "-c",
            "--config",
            type=str,
            default="config.json",
            help="Path to the configuration file",
        )
        subparsers = parser.add_subparsers(dest="command", required=True)

        for subcommand, subcommand_class in ALL_SUBCOMMANDS.items():
            subparser = subparsers.add_parser(subcommand, help=subcommand_class.__doc__)
            subcommand_class.add_arguments(subparser)

        return parser.parse_args()

    def run(self):
        """Main method to run the command line interface."""
        self._args = self.parse_args()
        with open(self._args.config, "r") as config_file:
            self._config = json.load(config_file)

        self._database = DatabaseManager(self._config["db_path"])

        command_class = ALL_SUBCOMMANDS[self._args.command]
        command = getattr(self._args, command_class.__name__, None)
        command_instance = command_class(self._args, self._config, self._database)

        try:
            command_instance.execute(command)
        except Exception as e:
            self._logger.exception(e)
            exit(1)


def main():
    """Convenience function to construct a
    CommandLine object and call run().
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    CommandLine().run()
