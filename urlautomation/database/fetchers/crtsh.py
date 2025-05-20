"""@package urlautomation.database.fetchers.crtsh
This module contains the implementation datafetcher for crt.sh.
"""

from urlautomation.database.datafetcher import DataFetcher
from urlautomation.database.types import Domain, SSLCertificate, SSLCertificateIdentity

from typing import Union, Dict, List, Any
from collections import defaultdict
from datetime import datetime
from lxml import html

import requests
import json
import re


class CrtshDataFetcher(DataFetcher):
    """This class is responsible for fetching data from crt.sh.
    It inherits from the DataFetcher class and implements the fetch_data method.
    """

    CRTSH_URL = "https://crt.sh"

    @classmethod
    def _crtsh_request(cls, **kwargs: Dict[str, Any]) -> requests.Response:
        """Make a request to the crt.sh API."""
        response = requests.get(cls.CRTSH_URL, params=kwargs)
        response.raise_for_status()
        return response

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

    def _parse_certificate_data_string(self, cert_text: str) -> dict:
        cert_text = cert_text.replace("\xa0", " ")
        cert_text = re.sub(r"\s+", " ", cert_text).strip()

        parsed = {}

        # Version
        if m := re.search(r"Version: *([^\s]+)", cert_text):
            parsed["version"] = m.group(1)

        # Serial Number
        if m := re.search(r"Serial Number: *([0-9a-fA-F:]+)", cert_text):
            parsed["serial_number"] = m.group(1)

        # Initial Signature Algorithm
        if m := re.search(r"Signature Algorithm: *([a-zA-Z0-9\-]+)", cert_text):
            parsed["signature_algorithm"] = m.group(1)

        # Issuer
        issuer = {}
        if m := re.search(r"Issuer:.*?commonName *= *([^ ]+)", cert_text):
            issuer["commonName"] = m.group(1)
        if m := re.search(r"organizationName *= *([^ ]+)", cert_text):
            issuer["organizationName"] = m.group(1)
        if m := re.search(r"countryName *= *([^ ]+)", cert_text):
            issuer["countryName"] = m.group(1)
        if issuer:
            parsed["issuer"] = issuer

        # Subject
        subject = {}
        if m := re.search(r"Subject:.*?commonName *= *([^ ]+)", cert_text):
            subject["commonName"] = m.group(1)
        parsed["subject"] = subject

        # Validity
        nb = re.search(r"Not Before: *(.*?) GMT", cert_text)
        na = re.search(r"Not After *: *(.*?) GMT", cert_text)
        parsed["validity"] = {
            "not_before": nb.group(1) if nb else None,
            "not_after": na.group(1) if na else None,
        }

        # Public Key Info
        pk_info = {}
        if m := re.search(r"Public Key Algorithm: *([a-zA-Z0-9\-]+)", cert_text):
            pk_info["algorithm"] = m.group(1)
        if m := re.search(r"RSA Public-Key: *\((\d+) bit\)", cert_text):
            pk_info["key_size"] = int(m.group(1))
        if m := re.search(r"Modulus: *([0-9a-fA-F: ]+?)Exponent:", cert_text):
            pk_info["modulus"] = m.group(1).strip().replace(" ", "").replace(":", "")
        if m := re.search(r"Exponent: *(\d+)", cert_text):
            pk_info["exponent"] = int(m.group(1))
        parsed["public_key_info"] = pk_info

        # Extensions
        extensions = {}
        if m := re.search(r"X509v3 Key Usage:.*?([A-Za-z ,]+)", cert_text):
            extensions["key_usage"] = m.group(1).strip()
        if m := re.search(r"X509v3 Extended Key Usage: *([^ ]+)", cert_text):
            extensions["extended_key_usage"] = m.group(1).strip()
        if m := re.search(r"X509v3 Basic Constraints: *[^ ]* *CA:([A-Z]+)", cert_text):
            extensions["basic_constraints"] = {"CA": m.group(1) == "TRUE"}
        parsed["extensions"] = extensions

        # Subject Key Identifier
        if m := re.search(
            r"X509v3 Subject Key Identifier: *([0-9A-Fa-f:]+)", cert_text
        ):
            parsed["subject_key_identifier"] = m.group(1)

        # Authority Key Identifier
        if m := re.search(
            r"X509v3 Authority Key Identifier:.*?keyid: *([0-9A-Fa-f:]+)", cert_text
        ):
            parsed["authority_key_identifier"] = m.group(1)

        # Authority Information Access
        aia = {}
        if m := re.search(r"CA Issuers - URI:([^\s]+)", cert_text):
            aia["ca_issuers"] = m.group(1)
        if m := re.search(r"OCSP - URI:([^\s]+)", cert_text):
            aia["ocsp"] = m.group(1)
        if aia:
            parsed["authority_information_access"] = aia

        # Subject Alternative Names
        san = re.findall(r"DNS:([a-zA-Z0-9\.\-\*]+)", cert_text)
        if san:
            parsed["subject_alternative_names"] = san

        # Certificate Policies
        if m := re.search(
            r"X509v3 Certificate Policies: *Policy: *([0-9\.\-]+)", cert_text
        ):
            parsed["certificate_policies"] = m.group(1)

        # CRL Distribution Points
        if m := re.search(r"CRL Distribution Points:.*?URI:([^\s]+)", cert_text):
            parsed["crl_distribution_point"] = m.group(1)

        # CT Precertificate SCTs
        scts = []
        sct_pattern = re.compile(
            r"Signed Certificate Timestamp:.*?Version *: *(.*?) Log Name *: *(.*?) Log ID *: *([0-9A-Fa-f:]+).*?Timestamp *: *(.*?) GMT",
            re.DOTALL,
        )
        for m in sct_pattern.finditer(cert_text):
            scts.append(
                {
                    "version": m.group(1).strip(),
                    "log_name": m.group(2).strip(),
                    "log_id": m.group(3).strip(),
                    "timestamp": m.group(4).strip(),
                }
            )
        if scts:
            parsed["ct_precertificate_scts"] = scts

        # Final Signature Algorithm
        if m := re.search(
            r"Signature Algorithm: *([a-zA-Z0-9\-]+).*?([0-9a-f: ]{10,})",
            cert_text,
            re.DOTALL,
        ):
            parsed["final_signature_algorithm"] = m.group(1)
            signature_raw = m.group(2)
            signature = re.sub(r"[^0-9a-fA-F]", "", signature_raw)
            parsed["final_signature"] = signature

        return parsed

    def _fetch_and_parse_certificate_html(self, cert_id: int) -> dict:
        """Fetch and parse certificate details from the crt.sh HTML page."""
        response = self._crtsh_request(c=cert_id)
        tree = html.fromstring(response.content.decode("utf-8"))
        # Get the second <table>
        tables = tree.xpath("//table")
        if len(tables) < 2:
            return {}
        cert_table = tables[1]
        cert_data_element = cert_table.xpath(
            ".//tr[td[contains(., 'Certificate:')]]/td"
        )
        if not cert_data_element:
            return {}
        raw_text = cert_data_element[0].text_content().strip()
        return self._parse_certificate_data_string(raw_text)

    def fetch_data(self, domains: Union[str, List[str]], **kwargs) -> None:
        dump = kwargs.get("dump", False)
        simulate = kwargs.get("simulate", False)
        quick_fetch = kwargs.get("quick", False)
        domains = domains if isinstance(domains, list) else [domains]
        responses = []

        # First, fetch the data for the requested domains from crt.sh
        if simulate:
            for domain in domains:
                with open(f"testdata/crtsh_{domain}.json", "r") as f:
                    response_json = json.load(f)
                responses.extend(self._deduplicate_results(response_json))
        else:
            for domain in domains:
                response = self._crtsh_request(q=f"%{domain}%", output="json")
                response_json = response.json()
                if dump:
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
                    if (domain := cached_domains.get(name_value)) is None:
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
                    if (ssl_cert := cached_certs.get(cert_key)) is None:
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
                        parsed = None
                        if not quick_fetch:
                            cert_id = response["id"]
                            try:
                                if simulate:
                                    with open(
                                        f"testdata/crtsh_{cert_id}_parsed.json", "r"
                                    ) as f:
                                        parsed = json.load(f)
                                else:
                                    parsed = self._fetch_and_parse_certificate_html(
                                        cert_id
                                    )
                            except:
                                self._logger.warning(
                                    f"Could not get extended data for ID {cert_id}",
                                    exc_info=True,
                                )

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
                        if parsed is not None:
                            if dump:
                                with open(f"crtsh_{cert_id}_parsed.json", "w") as f:
                                    json.dump(parsed, f, indent=2)

                            ssl_cert.subject_key_identifier = parsed[
                                "subject_key_identifier"
                            ]
                            ssl_cert.authority_key_identifier = parsed[
                                "authority_key_identifier"
                            ]
                            ssl_cert.signature_algorithm = parsed[
                                "final_signature_algorithm"
                            ]
                            ssl_cert.signature = parsed["final_signature"]
                            public_key_info = parsed["public_key_info"]
                            ssl_cert.public_key_algorithm = public_key_info.get(
                                "algorithm"
                            )
                            ssl_cert.public_key_size = public_key_info.get("key_size")
                            ssl_cert.public_key_modulus = public_key_info.get("modulus")
                            ssl_cert.public_key_exponent = public_key_info.get(
                                "exponent"
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
