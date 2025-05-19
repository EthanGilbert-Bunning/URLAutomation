"""@package urlautomation.database.fetchers.crtsh
This module contains the implementation datafetcher for crt.sh.
"""

from urlautomation.database.datafetcher import DataFetcher
from urlautomation.database.types import Domain, SSLCertificate, SSLCertificateIdentity

from typing import Union, Dict, List, Any
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
                responses.append((domain, self._deduplicate_results(response_json)))
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

                responses.append((domain, self._deduplicate_results(response_json)))

        # Process responses, add new records to the database
        with self._database as session:
            new_identities = set()
            for domain_name, response in responses:
                cert_stat = 0
                domain = (
                    session.query(Domain).filter_by(domain_name=domain_name).first()
                )
                if domain is None:
                    domain = Domain(domain_name=domain_name)
                    session.add(domain)
                    session.commit()
                domain_id = domain.domain_id

                # Fetch existing serial number / issuing authorities from the database
                existing_certs = set(
                    session.query(
                        SSLCertificate.serial_number, SSLCertificate.issuer_ca_id
                    )
                    .filter_by(domain_id=domain_id)
                    .all()
                )
                for record in response:
                    if (
                        record["serial_number"],
                        record["issuer_ca_id"],
                    ) in existing_certs:
                        # Skip if the certificate already exists in the database
                        continue

                    ssl_cert = SSLCertificate(
                        domain_id=domain_id,
                        issuer_ca_id=record["issuer_ca_id"],
                        issuer_name=record["issuer_name"],
                        common_name=record["common_name"],
                        entry_timestamp=datetime.fromisoformat(
                            record["entry_timestamp"]
                        ),
                        not_before=datetime.fromisoformat(record["not_before"]),
                        not_after=datetime.fromisoformat(record["not_after"]),
                        serial_number=record["serial_number"],
                    )
                    for identity in record["name_value"].splitlines():
                        ssl_cert.identities.append(
                            SSLCertificateIdentity(identity=identity)
                        )
                        if identity != domain_name:
                            new_identities.add(identity)
                    session.add(ssl_cert)
                    cert_stat += 1
                self._logger.info(
                    f"Discovered {cert_stat} new associated SSL certificates for {domain_name}."
                )
            for identity in (
                session.query(Domain.domain_name)
                .filter(Domain.domain_name.in_(domains))
                .all()
            ):
                new_identities.discard(identity)

            for unidentified in new_identities:
                self._logger.warning(
                    f"Found new domain {unidentified} in crt.sh, but it is not associated with any domain in the database."
                )
                self._logger.warning(
                    f"You may want to do `domain fetch {unidentified}` to add it to the database."
                )
