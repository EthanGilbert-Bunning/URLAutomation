"""@package urlautomation.database.constants
This module contains constants used in the database module.
"""

DATABASE_SETUP_SCRIPT = """
CREATE TABLE "cases" (
  "case_id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "case_number" VARCHAR(50) UNIQUE NOT NULL,
  "investigating_officer" VARCHAR(100),
  "date_opened" TIMESTAMP DEFAULT (CURRENT_TIMESTAMP),
  "date_closed" TIMESTAMP,
  "case_status" VARCHAR(20),
  "description" TEXT
);

CREATE TABLE "domains" (
  "domain_id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "domain_name" VARCHAR(255) UNIQUE NOT NULL,
  "first_seen" TIMESTAMP DEFAULT (CURRENT_TIMESTAMP),
  "last_seen" TIMESTAMP
);

CREATE TABLE "dns_record_types" (
  "type_id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "type_name" VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE "dns_records" (
  "record_id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "domain_id" INTEGER,
  "record_type" INTEGER,
  "first_seen" TIMESTAMP,
  "last_seen" TIMESTAMP,
  "organizations" TEXT[],
  FOREIGN KEY("domain_id") REFERENCES "domains" ("domain_id")
);

CREATE TABLE "a_record_values" (
  "a_record_value_id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "record_id" INTEGER,
  "ip_address" INET,
  "ip_count" INTEGER DEFAULT 1,
  FOREIGN KEY("record_id") REFERENCES "dns_records" ("record_id")
);

CREATE TABLE "ns_record_values" (
  "ns_record_value_id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "record_id" INTEGER,
  "name_server" VARCHAR(255),
  "nameserver_count" INTEGER DEFAULT 1,
  FOREIGN KEY("record_id") REFERENCES "dns_records" ("record_id")
);

CREATE TABLE "ssl_certificates" (
  "certificate_id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "domain_id",
  "issuer_ca_id" VARCHAR(100),
  "issuer_name" VARCHAR(255),
  "common_name" VARCHAR(255),
  "name_value" TEXT,
  "entry_timestamp" TIMESTAMP,
  "not_before" TIMESTAMP,
  "not_after" TIMESTAMP,
  "serial_number" VARCHAR(100),
  "result_count" INTEGER,
  FOREIGN KEY("domain_id") REFERENCES "domains" ("domain_id")
);"""

INSERT_TABLE_QUERIES = {
    "cases": (
        "INSERT INTO cases (case_number, investigating_officer, date_opened, date_closed, case_status, description) "
        "VALUES (?, ?, ?, ?, ?, ?)"
    ),
    "domains": (
        "INSERT INTO domains (domain_name, first_seen, last_seen) " "VALUES (?, ?, ?)"
    ),
    "dns_records": (
        "INSERT INTO dns_records (domain_id, record_type, first_seen, last_seen, organizations) "
        "VALUES (?, ?, ?, ?, ?)"
    ),
    "a_record_values": (
        "INSERT INTO a_record_values (record_id, ip_address, ip_count) "
        "VALUES (?, ?, ?)"
    ),
    "ns_record_values": (
        "INSERT INTO ns_record_values (record_id, name_server, nameserver_count) "
        "VALUES (?, ?, ?)"
    ),
    "ssl_certificates": (
        "INSERT INTO ssl_certificates (domain_id, issuer_ca_id, issuer_name, common_name, name_value, entry_timestamp, not_before, not_after, serial_number) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
    ),
}
