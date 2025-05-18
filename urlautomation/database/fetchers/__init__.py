from urlautomation.database.fetchers.securitytrails import SecurityTrailsDataFetcher
from urlautomation.database.fetchers.crtsh import CrtshDataFetcher

ALL_DATAFETCHERS = {
    "crtsh": CrtshDataFetcher,
    "securitytrails": SecurityTrailsDataFetcher,
}
