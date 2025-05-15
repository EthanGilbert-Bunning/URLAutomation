"""@package urlautomation.objects.sllrecord
This module contains the definition for the SSLRecord class."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class SSLRecordDBMeta:
    """Class representing the database metadata for an SSL record."""

    ## Primary key in the table.
    certificate_id: int

    ## Link to entry in domains table.
    domain_id: int


@dataclass
class SSLRecord:
    """Class representing an SSL record."""

    ## Issuer CA ID
    issuer_ca_id: int

    ## Issuer name
    issuer_name: str

    ## Common name
    common_name: str

    ## List of names
    names: List[str]

    ## Entry timestamp
    entry_timestamp: datetime

    ## Valid not before timestamp
    not_before: datetime

    ## Valid not after timestamp
    not_after: datetime

    ## Certificate Serial number
    serial_number: str

    ## Database metadata. This will only be available when retrieved from the database.
    meta: Optional[SSLRecordDBMeta] = None

    def __str__(self):
        """String representation of the SSLRecord object."""
        return (
            f"SSLRecord("
            f"issuer_ca_id={self.issuer_ca_id}, "
            f"issuer_name='{self.issuer_name}', "
            f"common_name='{self.common_name}', "
            f"names={self.names}, "
            f"entry_timestamp={self.entry_timestamp}, "
            f"not_before={self.not_before}, "
            f"not_after={self.not_after}, "
            f"serial_number='{self.serial_number}')"
        )
