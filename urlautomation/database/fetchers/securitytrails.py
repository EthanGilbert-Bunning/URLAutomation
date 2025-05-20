"""@package urlautomation.database.fetchers.securitytrails
This module contains the implementation datafetcher for the SecurityTrails API.
"""

from urlautomation.database.datafetcher import DataFetcher
from urlautomation.database.types import (
    Domain,
    DNSRecord,
    ARecordIP,
    ARecordValue,
    NSRecordNameserver,
    NSRecordValue,
    Organization,
)

from typing import Union, Dict, List
from datetime import datetime
from collections import defaultdict

import json
import requests


class SecurityTrailsDataFetcher(DataFetcher):
    """This class is responsible for fetching data from the SecurityTrails API.
    It inherits from the DataFetcher class and implements the fetch_data method.
    """

    def _make_request(self, apikey: str, domain: str, record_type: str) -> List[dict]:
        """Make a request to the SecurityTrails API."""
        url = f"https://api.securitytrails.com/v1/history/{domain}/dns/{record_type}"
        headers = {
            "Content-Type": "application/json",
            "APIKEY": apikey,
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        return response.json()["records"]

    def fetch_data(self, domains: Union[str, List[str]], **kwargs) -> None:
        # Currently we only fetch A and NS records.
        request_responses = defaultdict(list)

        if isinstance(domains, str):
            domains = [domains]

        if kwargs.get("simulate", False):
            for domain in domains:
                for record_type in ["a", "ns"]:
                    with open(f"testdata/{domain}_{record_type}.json", "r") as f:
                        response_json = json.load(f)
                    request_responses[domain].extend(response_json)
        else:
            for domain in domains:
                for record_type in ["a", "ns"]:
                    response = self._make_request(kwargs["apikey"], domain, record_type)
                    if kwargs.get("dump", False):
                        try:
                            with open(f"{domain}_{record_type}.json", "w") as f:
                                json.dump(response, f, indent=4)
                        except:
                            self._logger.exception(
                                f"Failed to dump response for {domain}"
                            )
                            self._logger.info(f"{response}")
                    request_responses[domain].extend(response)

        if not request_responses:
            self._logger.warning(f"No data found for domains: {domains}")
            return

        # welcome to hell
        cached_domains = {}
        with self._database as session:
            for domain_name, responses in request_responses.items():
                # Fetch or create domain
                domain = cached_domains.get(domain_name)
                if domain is None:
                    domain = (
                        session.query(Domain).filter_by(domain_name=domain_name).first()
                    )
                    if domain is None:
                        self._logger.debug(
                            f"Creating new domain {domain_name} in the database."
                        )
                        domain = Domain(domain_name=domain_name)
                        session.add(domain)
                        session.commit()  # Get domain_id
                    cached_domains[domain_name] = domain

                domain_id = domain.domain_id

                # Create new record or update existing?
                record = session.query(DNSRecord).filter_by(domain_id=domain_id).first()
                if record is None:
                    record = DNSRecord(domain_id=domain_id)
                    session.add(record)
                    # Commit to get a record_id associated.
                    session.commit()

                dns_stat = defaultdict(int)

                for response in responses:
                    record_type = response["type"]
                    first_seen, last_seen = map(
                        lambda d: datetime.strptime(d, "%Y-%m-%d"),
                        [response["first_seen"], response["last_seen"]],
                    )

                    record_cls = (
                        ARecordValue
                        if record_type == "a"
                        else NSRecordValue if record_type == "ns" else None
                    )
                    if record_cls is None:
                        raise ValueError(f"Unknown record type: {record_type}")

                    # Fetch or create sub-record
                    sub_record = (
                        session.query(record_cls)
                        .filter_by(dns_record_id=record.record_id)
                        .first()
                    )
                    if sub_record is None:
                        sub_record = record_cls(
                            dns_record_id=record.record_id,
                            first_seen=first_seen,
                            last_seen=last_seen,
                        )
                        session.add(sub_record)

                    for organization in response["organizations"]:
                        db_org = (
                            session.query(Organization)
                            .filter_by(organization_name=organization)
                            .first()
                        )
                        if db_org is None:
                            db_org = Organization(organization_name=organization)
                            session.add(db_org)

                        if db_org not in sub_record.organizations:
                            sub_record.organizations.append(db_org)

                    if record_type == "a":
                        for ip in response["values"]:
                            ip_address = ip["ip"]
                            db_ip = (
                                session.query(ARecordIP)
                                .filter_by(ip_address=ip_address)
                                .first()
                            )
                            if db_ip is None:
                                db_ip = ARecordIP(ip_address=ip_address)
                                session.add(db_ip)

                            if db_ip not in sub_record.ip_addresses:
                                sub_record.ip_addresses.append(db_ip)
                                dns_stat["a"] += 1
                    elif record_type == "ns":
                        for ns in response["values"]:
                            nameserver = ns["nameserver"]
                            db_ns = (
                                session.query(NSRecordNameserver)
                                .filter_by(nameserver=nameserver)
                                .first()
                            )
                            if db_ns is None:
                                db_ns = NSRecordNameserver(nameserver=nameserver)
                                session.add(db_ns)

                            if db_ns not in sub_record.nameservers:
                                sub_record.nameservers.append(db_ns)
                                dns_stat["ns"] += 1

                session.commit()  # Batch commit for performance
                self._logger.info(
                    f"Discovered {dns_stat['a']} new A records and {dns_stat['ns']} NS records for domain {domain_name}"
                )
