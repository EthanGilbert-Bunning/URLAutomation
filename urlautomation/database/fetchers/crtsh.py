"""@package urlautomation.database.fetchers.crtsh
This module contains the implementation datafetcher for crt.sh.
"""

from urlautomation.database.datafetcher import DataFetcher
from urlautomation.database.types import Domain, SSLCertificate, SSLCertificateIdentity

from typing import Union, Dict, List, Any
from collections import defaultdict
from datetime import datetime

import requests
import json


class CrtshDataFetcher(DataFetcher):
    """This class is responsible for fetching data from crt.sh.
    It inherits from the DataFetcher class and implements the fetch_data method.
    """

    def _deduplicate_results(
        self, results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Deduplicate the results based on serial number and issuer CA ID."""
        seen = set()
        deduplicated_results = []
        for result in results:
            key = (result["serial_number"], result["issuer_ca_id"])
            if key not in seen:
                seen.add(key)
                deduplicated_results.append(result)
        return deduplicated_results

    def fetch_data(self, domains: Union[str, List[str]], **kwargs) -> None:
        domains = domains if isinstance(domains, list) else [domains]
        responses = []

        # First, fetch the data for the requested domains from crt.sh
        if kwargs.get("simulate", False):
            for domain in domains:
                with open(f"testdata/crtsh_{domain}.json", "r") as f:
                    response_json = json.load(f)
                responses.extend(self._deduplicate_results(response_json))
        else:
            for domain in domains:
                request_params = {
                    "q": f"%{domain}%",
                    "output": "json",
                }
                response = requests.get("https://crt.sh", params=request_params)
                response.raise_for_status()
                response_json = response.json()
                if kwargs.get("dump", False):
                    try:
                        with open(f"crtsh_{domain}.json", "w") as f:
                            json.dump(response_json, f, indent=2)
                    except:
                        self._logger.exception(f"Failed to dump response for {domain}")
                        self._logger.info(f"{response_json}")

                responses.extend(self._deduplicate_results(response_json))

        cached_domains = {}
        cached_certs = {}
        cert_stat = defaultdict(int)

        # Process responses, add new records to the database
        with self._database as session:
            for response in responses:
                for name_value in response["name_value"].splitlines():
                    if name_value.startswith("*."):
                        continue

                    # Fetch or create domain
                    domain = cached_domains.get(name_value)
                    if domain is None:
                        domain = (
                            session.query(Domain)
                            .filter_by(domain_name=name_value)
                            .first()
                        )
                        if domain is None:
                            self._logger.debug(
                                f"Creating new domain {name_value} in the database."
                            )
                            domain = Domain(domain_name=name_value)
                            session.add(domain)
                        cached_domains[name_value] = domain

                    cert_key = (response["serial_number"], response["issuer_ca_id"])
                    ssl_cert = cached_certs.get(cert_key)

                    if ssl_cert is None:
                        ssl_cert = (
                            session.query(SSLCertificate)
                            .filter_by(
                                serial_number=response["serial_number"],
                                issuer_ca_id=response["issuer_ca_id"],
                            )
                            .first()
                        )

                    if ssl_cert:
                        # Ensure the certificate identity is associated with the domain
                        identity = (
                            session.query(SSLCertificateIdentity)
                            .filter_by(
                                certificate_id=ssl_cert.certificate_id,
                                identity=name_value,
                            )
                            .first()
                        )

                        if identity is None:
                            identity = SSLCertificateIdentity(
                                identity=name_value, certificate=ssl_cert
                            )
                            session.add(identity)

                        if domain not in identity.domains:
                            identity.domains.append(domain)

                        continue
                    else:
                        # Create new SSL certificate
                        ssl_cert = SSLCertificate(
                            issuer_ca_id=response["issuer_ca_id"],
                            issuer_name=response["issuer_name"],
                            entry_timestamp=datetime.fromisoformat(
                                response["entry_timestamp"]
                            ),
                            not_before=datetime.fromisoformat(response["not_before"]),
                            not_after=datetime.fromisoformat(response["not_after"]),
                            serial_number=response["serial_number"],
                        )

                        session.add(ssl_cert)
                        session.commit()

                        identity = SSLCertificateIdentity(
                            identity=name_value, certificate=ssl_cert
                        )
                        identity.domains.append(domain)

                        session.add(identity)

                        # Cache certificate to prevent future redundant queries
                        cached_certs[cert_key] = ssl_cert

                    cert_stat[name_value] += 1

            # Log new certificates added per domain
            for name_value, count in cert_stat.items():
                self._logger.info(
                    f"Found {count} new certificates for domain {name_value}."
                )
