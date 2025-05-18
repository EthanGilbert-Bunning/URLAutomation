from typing import Union, List

import logging


class DataFetcher:
    def __init__(self, database):
        """Class constructor for DataFetcher."""
        self._database = database
        self._logger = logging.getLogger(__name__)

    def fetch_data(self, domains: Union[str, List[str]], **kwargs) -> None:
        raise NotImplementedError("Subclasses should implement this method.")
