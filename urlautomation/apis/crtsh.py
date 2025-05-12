"""@package urlautomation.apis.crtsh
This module contains the implementations for working with crt.sh API.
"""

from urlautomation.objects import SSLRecord

from datetime import datetime
from json import JSONDecoder
from typing import List

import requests


class CrtShResponseDecoder(JSONDecoder):
    """JSONDecoder for a crt.sh API response."""

    def decode(self, s: str) -> List[SSLRecord]:
        """Decode a JSON string into a list of SSLRecord objects.
        @param s JSON string to decode"""
        data = super().decode(s)
        if not isinstance(data, list):
            raise ValueError("Expected a list of SSL records")

        # Currently, crt.sh id and result_count fields are not
        # stored, this may change if they are shown to be useful.
        return [
            SSLRecord(
                issuer_ca_id=record["issuer_ca_id"],
                issuer_name=record["issuer_name"],
                common_name=record["common_name"],
                names=record["name_value"].splitlines(),
                entry_timestamp=datetime.fromisoformat(record["entry_timestamp"]),
                not_before=datetime.fromisoformat(record["not_before"]),
                not_after=datetime.fromisoformat(record["not_after"]),
                serial_number=record["serial_number"],
            )
            for record in data
        ]


def fetch_records(query: str) -> List[SSLRecord]:
    """Fetch a list of SSLRecords from the crt.sh database.
    @param query The identity to search for.
    @return A list of SSLRecord objects."""
    request_params = {
        "q": f"%{query}%",
        "output": "json",
    }
    response = requests.get("https://crt.sh", params=request_params)
    response.raise_for_status()

    return response.json(cls=CrtShResponseDecoder)
