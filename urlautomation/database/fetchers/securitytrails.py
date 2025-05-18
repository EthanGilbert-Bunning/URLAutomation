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


DEBUG = True

fake_response_a = {
    "pokerkg.com": """
{
    "endpoint": "/v1/history/pokerkg.com/dns/a",
    "pages": 1,
    "records": [
        {
            "first_seen": "2021-12-24",
            "last_seen": "2025-05-12",
            "organizations": [
                "Amazon.com, Inc."
            ],
            "type": "a",
            "values": [
                {
                    "ip": "99.83.154.118",
                    "ip_count": 0
                }
            ]
        },
        {
            "first_seen": "2019-12-26",
            "last_seen": "2021-02-04",
            "organizations": [
                "Namecheap, Inc."
            ],
            "type": "a",
            "values": [
                {
                    "ip": "192.64.119.15",
                    "ip_count": 0
                }
            ]
        },
        {
            "first_seen": "2008-11-15",
            "last_seen": "2019-12-26",
            "organizations": [
                "Amazon.com, Inc."
            ],
            "type": "a",
            "values": [
                {
                    "ip": "69.64.155.79",
                    "ip_count": 0
                }
            ]
        },
        {
            "first_seen": "2008-09-26",
            "last_seen": "2008-10-08",
            "organizations": [
                "Tucows.com Co."
            ],
            "type": "a",
            "values": [
                {
                    "ip": "216.40.33.31",
                    "ip_count": 0
                }
            ]
        },
        {
            "first_seen": "2008-09-24",
            "last_seen": "2008-09-26",
            "organizations": [
                "Tucows.com Co."
            ],
            "type": "a",
            "values": [
                {
                    "ip": "216.40.33.31",
                    "ip_count": 0
                },
                {
                    "ip": "216.40.33.251",
                    "ip_count": 0
                }
            ]
        },
        {
            "first_seen": "2008-09-20",
            "last_seen": "2008-09-23",
            "organizations": [
                "Tucows.com Co."
            ],
            "type": "a",
            "values": [
                {
                    "ip": "216.40.33.31",
                    "ip_count": 0
                },
                {
                    "ip": "216.40.33.251",
                    "ip_count": 0
                }
            ]
        },
        {
            "first_seen": "2008-09-13",
            "last_seen": "2008-09-17",
            "organizations": [
                "Tucows.com Co."
            ],
            "type": "a",
            "values": [
                {
                    "ip": "216.40.33.31",
                    "ip_count": 0
                },
                {
                    "ip": "216.40.33.251",
                    "ip_count": 0
                }
            ]
        },
        {
            "first_seen": "2008-09-08",
            "last_seen": "2008-09-10",
            "organizations": [
                "Tucows.com Co."
            ],
            "type": "a",
            "values": [
                {
                    "ip": "216.40.33.31",
                    "ip_count": 0
                },
                {
                    "ip": "216.40.33.251",
                    "ip_count": 0
                }
            ]
        },
        {
            "first_seen": "2008-09-02",
            "last_seen": "2008-09-08",
            "organizations": [
                "Tucows.com Co."
            ],
            "type": "a",
            "values": [
                {
                    "ip": "216.40.33.31",
                    "ip_count": 0
                }
            ]
        }
    ],
    "type": "a/ipv4"
}
""",
    "pokerkg.dev": """
{
    "endpoint": "/v1/history/pokerkg.dev/dns/a",
    "pages": 1,
    "records": [
        {
            "first_seen": "2021-12-24",
            "last_seen": "2022-02-04",
            "organizations": [
                "Amazon.com, Inc."
            ],
            "type": "a",
            "values": [
                {
                    "ip": "99.83.154.118",
                    "ip_count": 0
                }
            ]
        },
        {
            "first_seen": "2021-02-04",
            "last_seen": "2021-12-24",
            "organizations": [
                "Cloudflare, Inc."
            ],
            "type": "a",
            "values": [
                {
                    "ip": "172.67.189.239",
                    "ip_count": 0
                },
                {
                    "ip": "104.21.10.47",
                    "ip_count": 0
                }
            ]
        },
        {
            "first_seen": "2019-12-26",
            "last_seen": "2021-02-04",
            "organizations": [
                "Namecheap, Inc."
            ],
            "type": "a",
            "values": [
                {
                    "ip": "162.255.119.230",
                    "ip_count": 0
                }
            ]
        }
    ],
    "type": "a/ipv4"
}
""",
}

fake_response_ns = {
    "pokerkg.com": """
{
    "endpoint": "/v1/history/pokerkg.com/dns/ns",
    "pages": 1,
    "records": [
        {
            "first_seen": "2021-12-24",
            "last_seen": "2025-05-12",
            "organizations": [
                "Neustar Security Services",
                "Akamai Connected Cloud",
                "NeuStar, Inc."
            ],
            "type": "ns",
            "values": [
                {
                    "nameserver": "dns1.registrar-servers.com",
                    "nameserver_count": 0
                },
                {
                    "nameserver": "dns101.registrar-servers.com",
                    "nameserver_count": 0
                },
                {
                    "nameserver": "dns102.registrar-servers.com",
                    "nameserver_count": 0
                },
                {
                    "nameserver": "dns2.registrar-servers.com",
                    "nameserver_count": 0
                }
            ]
        },
        {
            "first_seen": "2020-12-25",
            "last_seen": "2021-12-24",
            "organizations": [
                "Neustar Security Services",
                "NeuStar, Inc."
            ],
            "type": "ns",
            "values": [
                {
                    "nameserver": "dns1.registrar-servers.com",
                    "nameserver_count": 0
                },
                {
                    "nameserver": "dns2.registrar-servers.com",
                    "nameserver_count": 0
                }
            ]
        },
        {
            "first_seen": "2019-12-26",
            "last_seen": "2020-12-25",
            "organizations": [
                "Neustar Security Services",
                "NeuStar, Inc."
            ],
            "type": "ns",
            "values": [
                {
                    "nameserver": "pdns1.registrar-servers.com",
                    "nameserver_count": 0
                },
                {
                    "nameserver": "pdns2.registrar-servers.com",
                    "nameserver_count": 0
                }
            ]
        },
        {
            "first_seen": "2008-11-15",
            "last_seen": "2019-12-26",
            "organizations": [
                "Tucows.com Co."
            ],
            "type": "ns",
            "values": [
                {
                    "nameserver": "dns1.name-services.com",
                    "nameserver_count": 0
                },
                {
                    "nameserver": "dns2.name-services.com",
                    "nameserver_count": 0
                },
                {
                    "nameserver": "dns3.name-services.com",
                    "nameserver_count": 0
                },
                {
                    "nameserver": "dns4.name-services.com",
                    "nameserver_count": 0
                },
                {
                    "nameserver": "dns5.name-services.com",
                    "nameserver_count": 0
                }
            ]
        },
        {
            "first_seen": "2008-09-02",
            "last_seen": "2008-11-15",
            "organizations": [
                "Tucows.com Co."
            ],
            "type": "ns",
            "values": [
                {
                    "nameserver": "ns1.renewyourname.net",
                    "nameserver_count": 0
                },
                {
                    "nameserver": "ns2.renewyourname.net",
                    "nameserver_count": 0
                }
            ]
        }
    ],
    "type": "ns"
}""",
    "pokerkg.dev": """
{
    "endpoint": "/v1/history/pokerkg.dev/dns/ns",
    "pages": 1,
    "records": [
        {
            "first_seen": "2021-12-24",
            "last_seen": "2022-02-04",
            "organizations": [
                "Neustar Security Services",
                "Akamai Connected Cloud",
                "NeuStar, Inc."
            ],
            "type": "ns",
            "values": [
                {
                    "nameserver": "dns1.registrar-servers.com",
                    "nameserver_count": 0
                },
                {
                    "nameserver": "dns101.registrar-servers.com",
                    "nameserver_count": 0
                },
                {
                    "nameserver": "dns102.registrar-servers.com",
                    "nameserver_count": 0
                },
                {
                    "nameserver": "dns2.registrar-servers.com",
                    "nameserver_count": 0
                }
            ]
        },
        {
            "first_seen": "2021-02-04",
            "last_seen": "2021-12-24",
            "organizations": [
                "Cloudflare, Inc."
            ],
            "type": "ns",
            "values": [
                {
                    "nameserver": "henry.ns.cloudflare.com",
                    "nameserver_count": 0
                },
                {
                    "nameserver": "jean.ns.cloudflare.com",
                    "nameserver_count": 0
                }
            ]
        },
        {
            "first_seen": "2019-12-26",
            "last_seen": "2021-02-04",
            "organizations": [
                "Neustar Security Services",
                "NeuStar, Inc."
            ],
            "type": "ns",
            "values": [
                {
                    "nameserver": "dns1.registrar-servers.com",
                    "nameserver_count": 0
                },
                {
                    "nameserver": "dns2.registrar-servers.com",
                    "nameserver_count": 0
                }
            ]
        }
    ],
    "type": "ns"
}""",
}


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

        if DEBUG:
            for domain in domains:
                response = json.loads(fake_response_a[domain])
                request_responses[domain].extend(response["records"])
                response = json.loads(fake_response_ns[domain])
                request_responses[domain].extend(response["records"])

        else:
            for domain in domains:
                for record_type in ["a", "ns"]:
                    response = self._make_request(kwargs["apikey"], domain, record_type)
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

                    if record_type == "a":
                        for ip in response["values"]:
                            ip_address = ip["ip"]
                            if ip_address not in db_ips:
                                db_ip = ARecordIP(
                                    ip_address=ip_address,
                                )
                                session.add(db_ip)
                                session.commit()
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
                                session.commit()
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
