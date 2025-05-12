"""@package urlautomation.database.adapters
This module contains adapters for adapting to and converting from
various database values.
"""

import datetime


# See https://docs.python.org/3/library/sqlite3.html#sqlite3-adapter-converter-recipes
def adapt_datetime_iso(val: datetime.datetime) -> str:
    """Adapt a datetime.datetime object to timezone-naive ISO 8601 date.
    @param val The datetime.datetime object to adapt.
    """
    return val.isoformat()


def convert_datetime(val: str) -> datetime.datetime:
    """Convert ISO 8601 datetime to datetime.datetime object.
    @param val The ISO 8601 datetime string to convert.
    """
    return datetime.datetime.fromisoformat(val.decode())


__adapters__ = ((datetime.datetime, adapt_datetime_iso),)
__converters__ = (("datetime", convert_datetime),)
