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
        with self._database as session:
            for domain_name, responses in request_responses.items():
                domain = (
                    session.query(Domain).filter_by(domain_name=domain_name).first()
                )
                if domain is None:
                    domain = Domain(domain_name=domain_name)
                    session.add(domain)
                    # Commit to get a domain_id associated.
                    session.commit()

                domain_id = domain.domain_id

                # Create new record or update existing?
                record = session.query(DNSRecord).filter_by(domain_id=domain_id).first()
                if record is None:
                    self._logger.info(
                        f"Creating new DNS record for domain {domain_name}"
                    )
                    record = DNSRecord(domain_id=domain_id)
                    session.add(record)
                    # Commit to get a record_id associated.
                    session.commit()

                dns_stat = defaultdict(int)

                # Collect all unique organizations, IPs, and nameservers.
                organizations = set()
                ip_addresses = set()
                nameservers = set()
                for response in responses:
                    organizations.update(response["organizations"])
                    if response["type"] == "a":
                        ip_addresses.update(
                            [value["ip"] for value in response["values"]]
                        )
                    elif response["type"] == "ns":
                        nameservers.update(
                            [value["nameserver"] for value in response["values"]]
                        )

                db_organizations: Dict[str, Organization] = {
                    org.organization_name: org
                    for org in session.query(Organization)
                    .filter(Organization.organization_name.in_(organizations))
                    .all()
                }
                db_ips: Dict[str, ARecordIP] = {
                    ip.ip_address: ip
                    for ip in session.query(ARecordIP)
                    .filter(ARecordIP.ip_address.in_(ip_addresses))
                    .all()
                }
                db_nameservers: Dict[str, NSRecordNameserver] = {
                    ns.nameserver: ns
                    for ns in session.query(NSRecordNameserver)
                    .filter(NSRecordNameserver.nameserver.in_(nameservers))
                    .all()
                }

                for response in responses:
                    record_type = response["type"]
                    first_seen = datetime.strptime(response["first_seen"], "%Y-%m-%d")
                    last_seen = datetime.strptime(response["last_seen"], "%Y-%m-%d")

                    if record_type == "a":
                        record_cls = ARecordValue
                    elif record_type == "ns":
                        record_cls = NSRecordValue
                    else:
                        raise ValueError(f"Unknown record type: {record_type}")

                    sub_record = (
                        session.query(record_cls)
                        .filter_by(
                            dns_record_id=record.record_id,
                        )
                        .first()
                    )
                    if sub_record is None:
                        self._logger.info(
                            f"Creating new {record_type} record for domain {domain_name}"
                        )
                        sub_record = record_cls(
                            dns_record_id=record.record_id,
                            first_seen=first_seen,
                            last_seen=last_seen,
                        )
                        session.add(sub_record)

                    for organization in response["organizations"]:
                        if organization not in db_organizations:
                            db_org = Organization(
                                organization_name=organization,
                            )
                            session.add(db_org)
                            db_organizations[organization] = db_org
                        else:
                            db_org = db_organizations[organization]
                        if db_org not in sub_record.organizations:
                            sub_record.organizations.append(
                                db_organizations[organization]
                            )

                    if record_type == "a":
                        for ip in response["values"]:
                            ip_address = ip["ip"]
                            if ip_address not in db_ips:
                                db_ip = ARecordIP(
                                    ip_address=ip_address,
                                )
                                session.add(db_ip)
                                db_ips[ip_address] = db_ip
                            else:
                                db_ip = db_ips[ip_address]

                            if db_ip not in sub_record.ip_addresses:
                                sub_record.ip_addresses.append(db_ips[ip_address])
                                dns_stat["a"] += 1
                    elif record_type == "ns":
                        for ns in response["values"]:
                            nameserver = ns["nameserver"]
                            if nameserver not in db_nameservers:
                                db_ns = NSRecordNameserver(
                                    nameserver=nameserver,
                                )
                                session.add(db_ns)
                                db_nameservers[nameserver] = db_ns
                            else:
                                db_ns = db_nameservers[nameserver]

                            if db_ns not in sub_record.nameservers:
                                sub_record.nameservers.append(
                                    db_nameservers[nameserver]
                                )
                                dns_stat["ns"] += 1

                self._logger.info(
                    f"Discovered {dns_stat['a']} new A records and {dns_stat['ns']} NS records for domain {domain_name}"
                )
