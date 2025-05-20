from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    PrimaryKeyConstraint,
    Table,
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


ssl_identity_domains = Table(
    "ssl_identity_domains",
    Base.metadata,
    Column(
        "identity_id", Integer, ForeignKey("ssl_certificates_identities.identity_id")
    ),
    Column("domain_id", Integer, ForeignKey("domains.domain_id")),
    PrimaryKeyConstraint("identity_id", "domain_id"),
)


class Domain(Base):
    __tablename__ = "domains"

    domain_id = Column(Integer, primary_key=True, autoincrement=True)
    domain_name = Column(String, unique=True)

    # Relationships
    identities = relationship(
        "SSLCertificateIdentity",
        secondary=ssl_identity_domains,
        back_populates="domains",
    )
    dns_records = relationship("DNSRecord", back_populates="domain")
    cases = relationship("CaseDomain", back_populates="domain")


class Case(Base):
    __tablename__ = "cases"

    case_id = Column(Integer, primary_key=True, autoincrement=True)
    case_name = Column(String, unique=True)
    investigating_officer = Column(String)
    date_opened = Column(DateTime)
    date_closed = Column(DateTime)
    case_status = Column(String)
    description = Column(Text)

    # Relationships
    domains = relationship("CaseDomain", back_populates="case")


class CaseDomain(Base):
    __tablename__ = "case_domains"

    case_id = Column(Integer, ForeignKey("cases.case_id"), primary_key=True)
    domain_id = Column(Integer, ForeignKey("domains.domain_id"), primary_key=True)

    # Relationships
    case = relationship("Case", back_populates="domains")
    domain = relationship("Domain", back_populates="cases")


a_record_organizations = Table(
    "a_record_organizations",
    Base.metadata,
    Column(
        "a_record_value_id", Integer, ForeignKey("a_record_values.a_record_value_id")
    ),
    Column("organization_id", Integer, ForeignKey("organizations.organization_id")),
    PrimaryKeyConstraint("a_record_value_id", "organization_id"),
)

ns_record_organizations = Table(
    "ns_record_organizations",
    Base.metadata,
    Column(
        "ns_record_value_id", Integer, ForeignKey("ns_record_values.ns_record_value_id")
    ),
    Column("organization_id", Integer, ForeignKey("organizations.organization_id")),
    PrimaryKeyConstraint("ns_record_value_id", "organization_id"),
)


class Organization(Base):
    __tablename__ = "organizations"

    organization_id = Column(Integer, primary_key=True, autoincrement=True)
    organization_name = Column(String, unique=True)

    a_records = relationship(
        "ARecordValue", secondary=a_record_organizations, back_populates="organizations"
    )
    ns_records = relationship(
        "NSRecordValue",
        secondary=ns_record_organizations,
        back_populates="organizations",
    )


class DNSRecord(Base):
    __tablename__ = "dns_records"

    record_id = Column(Integer, primary_key=True, autoincrement=True)

    # DNSRecord is unique to a domain, because there will be multiple types
    # of records for each domain.
    domain_id = Column(Integer, ForeignKey("domains.domain_id"), unique=True)

    # Relationships
    domain = relationship("Domain", back_populates="dns_records")
    a_records = relationship("ARecordValue", back_populates="dns_record")
    ns_records = relationship("NSRecordValue", back_populates="dns_record")
    # mx_records = relationship("MXRecordValue", back_populates="dns_record")


a_record_ip_association = Table(
    "a_record_ip_association",
    Base.metadata,
    Column(
        "a_record_value_id", Integer, ForeignKey("a_record_values.a_record_value_id")
    ),
    Column("ip_id", Integer, ForeignKey("a_record_ips.ip_id")),
)


class ARecordValue(Base):
    __tablename__ = "a_record_values"

    a_record_value_id = Column(Integer, primary_key=True, autoincrement=True)
    dns_record_id = Column(Integer, ForeignKey("dns_records.record_id"))
    first_seen = Column(DateTime)
    last_seen = Column(DateTime)

    dns_record = relationship("DNSRecord", back_populates="a_records")
    ip_addresses = relationship(
        "ARecordIP", secondary=a_record_ip_association, back_populates="a_records"
    )
    organizations = relationship(
        "Organization", secondary=a_record_organizations, back_populates="a_records"
    )


class ARecordIP(Base):
    __tablename__ = "a_record_ips"

    ip_id = Column(Integer, primary_key=True, autoincrement=True)
    ip_address = Column(String, unique=True)

    a_records = relationship(
        "ARecordValue", secondary=a_record_ip_association, back_populates="ip_addresses"
    )


ns_record_nameserver_association = Table(
    "ns_record_nameserver_association",
    Base.metadata,
    Column(
        "ns_record_value_id", Integer, ForeignKey("ns_record_values.ns_record_value_id")
    ),
    Column("nameserver_id", Integer, ForeignKey("ns_record_nameservers.nameserver_id")),
)


class NSRecordValue(Base):
    __tablename__ = "ns_record_values"

    ns_record_value_id = Column(Integer, primary_key=True, autoincrement=True)
    dns_record_id = Column(Integer, ForeignKey("dns_records.record_id"))
    first_seen = Column(DateTime)
    last_seen = Column(DateTime)

    dns_record = relationship("DNSRecord", back_populates="ns_records")
    nameservers = relationship(
        "NSRecordNameserver",
        secondary=ns_record_nameserver_association,
        back_populates="ns_records",
    )
    organizations = relationship(
        "Organization", secondary=ns_record_organizations, back_populates="ns_records"
    )


class NSRecordNameserver(Base):
    __tablename__ = "ns_record_nameservers"

    nameserver_id = Column(Integer, primary_key=True, autoincrement=True)
    nameserver = Column(String, unique=True)

    ns_records = relationship(
        "NSRecordValue",
        secondary=ns_record_nameserver_association,
        back_populates="nameservers",
    )


class SSLCertificate(Base):
    __tablename__ = "ssl_certificates"

    certificate_id = Column(Integer, primary_key=True, autoincrement=True)
    issuer_ca_id = Column(Integer)
    issuer_name = Column(String)
    common_name = Column(String)
    entry_timestamp = Column(DateTime)
    not_before = Column(DateTime)
    not_after = Column(DateTime)
    serial_number = Column(String)

    subject_key_identifier = Column(String)
    authority_key_identifier = Column(String)
    public_key_algorithm = Column(String)
    public_key_size = Column(Integer)
    public_key_modulus = Column(Text)  # Can be large, so use Text
    public_key_exponent = Column(Integer)
    signature_algorithm = Column(String)
    signature = Column(Text)

    # Relationships
    identities = relationship("SSLCertificateIdentity", back_populates="certificate")
    ct_log_entries = relationship("CTLogEntry", back_populates="certificate")

    # Unique constraint
    __table_args__ = (
        UniqueConstraint("serial_number", "issuer_ca_id", name="unique_ssl_serial"),
    )


class CTLogEntry(Base):
    __tablename__ = "ct_log_entries"

    ct_log_id = Column(Integer, primary_key=True, autoincrement=True)
    certificate_id = Column(Integer, ForeignKey("ssl_certificates.certificate_id"))

    version = Column(String)
    log_name = Column(String)
    log_id = Column(String)
    timestamp = Column(DateTime)

    certificate = relationship("SSLCertificate", back_populates="ct_log_entries")


class SSLCertificateIdentity(Base):
    __tablename__ = "ssl_certificates_identities"

    identity_id = Column(Integer, primary_key=True, autoincrement=True)
    certificate_id = Column(Integer, ForeignKey("ssl_certificates.certificate_id"))
    identity = Column(String)

    # Relationships
    certificate = relationship("SSLCertificate", back_populates="identities")
    domains = relationship(
        "Domain", secondary=ssl_identity_domains, back_populates="identities"
    )

    # Unique constraint
    __table_args__ = (
        UniqueConstraint("certificate_id", "identity", name="unique_identity_per_cert"),
    )
