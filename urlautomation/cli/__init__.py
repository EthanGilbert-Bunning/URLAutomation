"""@package urlautomation.cli
Main package for the CLI of the URL Automation project.
This package contains the code for the Command Line Interface (CLI)
"""

from urlautomation.database.manager import DatabaseManager
from urlautomation.apis import crtsh

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
        # temporary
        parser.add_argument(
            "-f",
            "--fetch",
            action="store_true",
            help="Fetch SSL records from crt.sh and store them in the database",
        )
        return parser.parse_args()

    def run(self):
        """Main method to run the command line interface."""
        self._args = self.parse_args()
        with open(self._args.config, "r") as config_file:
            self._config = json.load(config_file)

        self._database = DatabaseManager(self._config["db_path"])

        if self._args.fetch:
            try:
                records = crtsh.fetch_records("corp.mediatek.com")
                self._logger.info(f"Fetched {len(records)} records from crt.sh.")
            except:
                self._logger.exception("Error fetching records from crt.sh.")

            try:
                with self._database:
                    self._database.add_ssl_records(records)
                    self._logger.info(f"Added {len(records)} records to the database.")
            except:
                self._logger.exception("Error adding records to the database.")

        try:
            with self._database:
                test = self._database.fetch_ssl_records(
                    criteria="WHERE datetime('now') BETWEEN datetime(not_before) AND datetime(not_after)"
                )
                self._logger.info(
                    f"Found {len(test)} records in with valid certificates."
                )
                for record in test:
                    self._logger.info(record)
        except:
            self._logger.exception("Error fetching records from the database.")


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
