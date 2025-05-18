"""@package urlautomation.database.fetchers.crtsh
This module contains the implementation datafetcher for crt.sh.
"""

from urlautomation.database.datafetcher import DataFetcher
from urlautomation.database.types import Domain, SSLCertificate, SSLCertificateIdentity

from typing import Union, Dict, List, Any
from datetime import datetime

import requests
from json import JSONDecoder

FAKE_RESPONSE = """
[
  {
    "issuer_ca_id": 157938,
    "issuer_name": "C=US, O=\\\"Cloudflare, Inc.\\\", CN=Cloudflare Inc ECC CA-3",
    "common_name": "sni.cloudflaressl.com",
    "name_value": "*.pokerkg.dev\\npokerkg.dev",
    "id": 4026157594,
    "entry_timestamp": "2021-02-03T19:22:01.355",
    "not_before": "2021-02-03T00:00:00",
    "not_after": "2022-02-02T23:59:59",
    "serial_number": "03e6d729e4e4d9e35c2bd846c9f39a8e",
    "result_count": 2
  },
  {
    "issuer_ca_id": 183267,
    "issuer_name": "C=US, O=Let's Encrypt, CN=R3",
    "common_name": "ws.pokerkg.dev",
    "name_value": "ws.pokerkg.dev",
    "id": 3888970805,
    "entry_timestamp": "2021-01-07T02:59:19.341",
    "not_before": "2021-01-07T01:59:19",
    "not_after": "2021-04-07T01:59:19",
    "serial_number": "04b2627c601e49ab6c4dce9874241b7b211c",
    "result_count": 2
  },
  {
    "issuer_ca_id": 183267,
    "issuer_name": "C=US, O=Let's Encrypt, CN=R3",
    "common_name": "ws.pokerkg.dev",
    "name_value": "ws.pokerkg.dev",
    "id": 3888970683,
    "entry_timestamp": "2021-01-07T02:59:19.201",
    "not_before": "2021-01-07T01:59:19",
    "not_after": "2021-04-07T01:59:19",
    "serial_number": "04b2627c601e49ab6c4dce9874241b7b211c",
    "result_count": 2
  },
  {
    "issuer_ca_id": 183267,
    "issuer_name": "C=US, O=Let's Encrypt, CN=R3",
    "common_name": "poker.pokerkg.dev",
    "name_value": "poker.pokerkg.dev",
    "id": 3873955663,
    "entry_timestamp": "2021-01-04T03:57:05.593",
    "not_before": "2021-01-04T02:57:04",
    "not_after": "2021-04-04T02:57:04",
    "serial_number": "03bcee288be224f8aa7eda1315356a25f63d",
    "result_count": 2
  },
  {
    "issuer_ca_id": 183267,
    "issuer_name": "C=US, O=Let's Encrypt, CN=R3",
    "common_name": "poker.pokerkg.dev",
    "name_value": "poker.pokerkg.dev",
    "id": 3873955387,
    "entry_timestamp": "2021-01-04T03:57:04.856",
    "not_before": "2021-01-04T02:57:04",
    "not_after": "2021-04-04T02:57:04",
    "serial_number": "03bcee288be224f8aa7eda1315356a25f63d",
    "result_count": 2
  },
  {
    "issuer_ca_id": 183267,
    "issuer_name": "C=US, O=Let's Encrypt, CN=R3",
    "common_name": "api.pokerkg.dev",
    "name_value": "api.pokerkg.dev",
    "id": 3867293041,
    "entry_timestamp": "2021-01-02T21:17:32.121",
    "not_before": "2021-01-02T20:17:31",
    "not_after": "2021-04-02T20:17:31",
    "serial_number": "047e4f70cb1fb6ee4205667adcf3bdb8684e",
    "result_count": 2
  },
  {
    "issuer_ca_id": 183267,
    "issuer_name": "C=US, O=Let's Encrypt, CN=R3",
    "common_name": "api.pokerkg.dev",
    "name_value": "api.pokerkg.dev",
    "id": 3867293513,
    "entry_timestamp": "2021-01-02T21:17:31.513",
    "not_before": "2021-01-02T20:17:31",
    "not_after": "2021-04-02T20:17:31",
    "serial_number": "047e4f70cb1fb6ee4205667adcf3bdb8684e",
    "result_count": 2
  },
  {
    "issuer_ca_id": 183267,
    "issuer_name": "C=US, O=Let's Encrypt, CN=R3",
    "common_name": "bo.pokerkg.dev",
    "name_value": "bo.pokerkg.dev",
    "id": 3746552942,
    "entry_timestamp": "2020-12-07T00:40:58.111",
    "not_before": "2020-12-06T23:40:57",
    "not_after": "2021-03-06T23:40:57",
    "serial_number": "039f7747357583ae5569160aca35628499c0",
    "result_count": 2
  },
  {
    "issuer_ca_id": 183267,
    "issuer_name": "C=US, O=Let's Encrypt, CN=R3",
    "common_name": "bo.pokerkg.dev",
    "name_value": "bo.pokerkg.dev",
    "id": 3746552106,
    "entry_timestamp": "2020-12-07T00:40:57.894",
    "not_before": "2020-12-06T23:40:57",
    "not_after": "2021-03-06T23:40:57",
    "serial_number": "039f7747357583ae5569160aca35628499c0",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "ws.pokerkg.dev",
    "name_value": "ws.pokerkg.dev",
    "id": 3621328921,
    "entry_timestamp": "2020-11-08T20:27:28.968",
    "not_before": "2020-11-08T19:27:28",
    "not_after": "2021-02-06T19:27:28",
    "serial_number": "04c14c8223b07f330c5b6db667eb6e2be6c3",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "ws.pokerkg.dev",
    "name_value": "ws.pokerkg.dev",
    "id": 3621328876,
    "entry_timestamp": "2020-11-08T20:27:28.787",
    "not_before": "2020-11-08T19:27:28",
    "not_after": "2021-02-06T19:27:28",
    "serial_number": "04c14c8223b07f330c5b6db667eb6e2be6c3",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "api.pokerkg.dev",
    "name_value": "api.pokerkg.dev",
    "id": 3603391615,
    "entry_timestamp": "2020-11-04T20:02:05.054",
    "not_before": "2020-11-04T19:02:04",
    "not_after": "2021-02-02T19:02:04",
    "serial_number": "04702373cc98b4e94eb5400b0e92498be8a9",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "api.pokerkg.dev",
    "name_value": "api.pokerkg.dev",
    "id": 3603392158,
    "entry_timestamp": "2020-11-04T20:02:04.928",
    "not_before": "2020-11-04T19:02:04",
    "not_after": "2021-02-02T19:02:04",
    "serial_number": "04702373cc98b4e94eb5400b0e92498be8a9",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "poker.pokerkg.dev",
    "name_value": "poker.pokerkg.dev",
    "id": 3598590999,
    "entry_timestamp": "2020-11-03T19:24:49.045",
    "not_before": "2020-11-03T18:24:48",
    "not_after": "2021-02-01T18:24:48",
    "serial_number": "04576fc1e9b4f15156b4d6f9a4e544d69ac3",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "poker.pokerkg.dev",
    "name_value": "poker.pokerkg.dev",
    "id": 3598591392,
    "entry_timestamp": "2020-11-03T19:24:48.86",
    "not_before": "2020-11-03T18:24:48",
    "not_after": "2021-02-01T18:24:48",
    "serial_number": "04576fc1e9b4f15156b4d6f9a4e544d69ac3",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "bo.pokerkg.dev",
    "name_value": "bo.pokerkg.dev",
    "id": 3482925750,
    "entry_timestamp": "2020-10-08T19:02:02.8",
    "not_before": "2020-10-08T18:02:02",
    "not_after": "2021-01-06T18:02:02",
    "serial_number": "03d694db43d4cd25c85a2b31eeb9f1a1ac56",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "bo.pokerkg.dev",
    "name_value": "bo.pokerkg.dev",
    "id": 3482922164,
    "entry_timestamp": "2020-10-08T19:02:02.54",
    "not_before": "2020-10-08T18:02:02",
    "not_after": "2021-01-06T18:02:02",
    "serial_number": "03d694db43d4cd25c85a2b31eeb9f1a1ac56",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "api.pokerkg.dev",
    "name_value": "api.pokerkg.dev",
    "id": 3341874256,
    "entry_timestamp": "2020-09-05T18:53:34.239",
    "not_before": "2020-09-05T17:53:33",
    "not_after": "2020-12-04T17:53:33",
    "serial_number": "0397289e83a3a08429d1a17772e24ede78e2",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "api.pokerkg.dev",
    "name_value": "api.pokerkg.dev",
    "id": 3341874630,
    "entry_timestamp": "2020-09-05T18:53:33.684",
    "not_before": "2020-09-05T17:53:33",
    "not_after": "2020-12-04T17:53:33",
    "serial_number": "0397289e83a3a08429d1a17772e24ede78e2",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "ws.pokerkg.dev",
    "name_value": "ws.pokerkg.dev",
    "id": 3337502395,
    "entry_timestamp": "2020-09-04T19:28:02.118",
    "not_before": "2020-09-04T18:28:01",
    "not_after": "2020-12-03T18:28:01",
    "serial_number": "0342e021d5179731ebf59d688e2b250a2c7e",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "ws.pokerkg.dev",
    "name_value": "ws.pokerkg.dev",
    "id": 3337503604,
    "entry_timestamp": "2020-09-04T19:28:01.883",
    "not_before": "2020-09-04T18:28:01",
    "not_after": "2020-12-03T18:28:01",
    "serial_number": "0342e021d5179731ebf59d688e2b250a2c7e",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "poker.pokerkg.dev",
    "name_value": "poker.pokerkg.dev",
    "id": 3337496669,
    "entry_timestamp": "2020-09-04T19:26:09.668",
    "not_before": "2020-09-04T18:26:09",
    "not_after": "2020-12-03T18:26:09",
    "serial_number": "04c70b093d937dc0a00ac22f35b9bf63cb8c",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "poker.pokerkg.dev",
    "name_value": "poker.pokerkg.dev",
    "id": 3337497168,
    "entry_timestamp": "2020-09-04T19:26:09.516",
    "not_before": "2020-09-04T18:26:09",
    "not_after": "2020-12-03T18:26:09",
    "serial_number": "04c70b093d937dc0a00ac22f35b9bf63cb8c",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "bo.pokerkg.dev",
    "name_value": "bo.pokerkg.dev",
    "id": 3214656779,
    "entry_timestamp": "2020-08-09T08:57:41.623",
    "not_before": "2020-08-09T07:57:41",
    "not_after": "2020-11-07T07:57:41",
    "serial_number": "0308d97c78c401f1eb15a08c6053fce62f1e",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "bo.pokerkg.dev",
    "name_value": "bo.pokerkg.dev",
    "id": 3210467773,
    "entry_timestamp": "2020-08-09T08:57:41.432",
    "not_before": "2020-08-09T07:57:41",
    "not_after": "2020-11-07T07:57:41",
    "serial_number": "0308d97c78c401f1eb15a08c6053fce62f1e",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "api.pokerkg.dev",
    "name_value": "api.pokerkg.dev",
    "id": 3056005335,
    "entry_timestamp": "2020-07-07T23:38:42.37",
    "not_before": "2020-07-07T22:38:41",
    "not_after": "2020-10-05T22:38:41",
    "serial_number": "048311fb1d370512eb3f8d28b1cfb020ecab",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "api.pokerkg.dev",
    "name_value": "api.pokerkg.dev",
    "id": 3056002713,
    "entry_timestamp": "2020-07-07T23:38:42.082",
    "not_before": "2020-07-07T22:38:41",
    "not_after": "2020-10-05T22:38:41",
    "serial_number": "048311fb1d370512eb3f8d28b1cfb020ecab",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "ws.pokerkg.dev",
    "name_value": "ws.pokerkg.dev",
    "id": 3051184956,
    "entry_timestamp": "2020-07-07T00:50:30.515",
    "not_before": "2020-07-06T23:50:30",
    "not_after": "2020-10-04T23:50:30",
    "serial_number": "04d8da28e6bab63b391099eb8527897b484d",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "ws.pokerkg.dev",
    "name_value": "ws.pokerkg.dev",
    "id": 3051178877,
    "entry_timestamp": "2020-07-07T00:50:30.273",
    "not_before": "2020-07-06T23:50:30",
    "not_after": "2020-10-04T23:50:30",
    "serial_number": "04d8da28e6bab63b391099eb8527897b484d",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "poker.pokerkg.dev",
    "name_value": "poker.pokerkg.dev",
    "id": 3051183677,
    "entry_timestamp": "2020-07-07T00:50:00.471",
    "not_before": "2020-07-06T23:50:00",
    "not_after": "2020-10-04T23:50:00",
    "serial_number": "0485c329f638a07e443f9e3cb84aefd42d03",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "poker.pokerkg.dev",
    "name_value": "poker.pokerkg.dev",
    "id": 3051184788,
    "entry_timestamp": "2020-07-07T00:50:00.304",
    "not_before": "2020-07-06T23:50:00",
    "not_after": "2020-10-04T23:50:00",
    "serial_number": "0485c329f638a07e443f9e3cb84aefd42d03",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "bo.pokerkg.dev",
    "name_value": "bo.pokerkg.dev",
    "id": 2951927900,
    "entry_timestamp": "2020-06-09T18:03:32.882",
    "not_before": "2020-06-09T17:03:32",
    "not_after": "2020-09-07T17:03:32",
    "serial_number": "040a3081e46561d3ba332432c8e7efc63683",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "bo.pokerkg.dev",
    "name_value": "bo.pokerkg.dev",
    "id": 2927998141,
    "entry_timestamp": "2020-06-09T18:03:32.702",
    "not_before": "2020-06-09T17:03:32",
    "not_after": "2020-09-07T17:03:32",
    "serial_number": "040a3081e46561d3ba332432c8e7efc63683",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "api.pokerkg.dev",
    "name_value": "api.pokerkg.dev",
    "id": 2846377427,
    "entry_timestamp": "2020-05-09T19:53:32.86",
    "not_before": "2020-05-09T18:53:32",
    "not_after": "2020-08-07T18:53:32",
    "serial_number": "03c35156d5ca3d3569b0c2237633c7e50afc",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "api.pokerkg.dev",
    "name_value": "api.pokerkg.dev",
    "id": 2785904335,
    "entry_timestamp": "2020-05-09T19:53:32.372",
    "not_before": "2020-05-09T18:53:32",
    "not_after": "2020-08-07T18:53:32",
    "serial_number": "03c35156d5ca3d3569b0c2237633c7e50afc",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "ws.pokerkg.dev",
    "name_value": "ws.pokerkg.dev",
    "id": 2844028760,
    "entry_timestamp": "2020-05-08T20:14:25.472",
    "not_before": "2020-05-08T19:14:25",
    "not_after": "2020-08-06T19:14:25",
    "serial_number": "039cf1431d765c9ddd068828a166e117f05b",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "ws.pokerkg.dev",
    "name_value": "ws.pokerkg.dev",
    "id": 2784067181,
    "entry_timestamp": "2020-05-08T20:14:25.241",
    "not_before": "2020-05-08T19:14:25",
    "not_after": "2020-08-06T19:14:25",
    "serial_number": "039cf1431d765c9ddd068828a166e117f05b",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "poker.pokerkg.dev",
    "name_value": "poker.pokerkg.dev",
    "id": 2844028891,
    "entry_timestamp": "2020-05-08T20:14:06.535",
    "not_before": "2020-05-08T19:14:06",
    "not_after": "2020-08-06T19:14:06",
    "serial_number": "04ca540facd7c895abceef47f2d0ea2a764a",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "poker.pokerkg.dev",
    "name_value": "poker.pokerkg.dev",
    "id": 2782062825,
    "entry_timestamp": "2020-05-08T20:14:06.309",
    "not_before": "2020-05-08T19:14:06",
    "not_after": "2020-08-06T19:14:06",
    "serial_number": "04ca540facd7c895abceef47f2d0ea2a764a",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "bo.pokerkg.dev",
    "name_value": "bo.pokerkg.dev",
    "id": 2689581671,
    "entry_timestamp": "2020-04-10T21:07:10.316",
    "not_before": "2020-04-10T20:07:10",
    "not_after": "2020-07-09T20:07:10",
    "serial_number": "031d2cac748f8ac3cb8ea4f472d0015c069f",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "bo.pokerkg.dev",
    "name_value": "bo.pokerkg.dev",
    "id": 2689582519,
    "entry_timestamp": "2020-04-10T21:07:10.145",
    "not_before": "2020-04-10T20:07:10",
    "not_after": "2020-07-09T20:07:10",
    "serial_number": "031d2cac748f8ac3cb8ea4f472d0015c069f",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "api.pokerkg.dev",
    "name_value": "api.pokerkg.dev",
    "id": 2575003393,
    "entry_timestamp": "2020-03-11T01:39:38.297",
    "not_before": "2020-03-11T00:39:38",
    "not_after": "2020-06-09T00:39:38",
    "serial_number": "038a8e4d682ca4c058f282b3fcedce90413a",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "api.pokerkg.dev",
    "name_value": "api.pokerkg.dev",
    "id": 2563671500,
    "entry_timestamp": "2020-03-11T01:39:38.174",
    "not_before": "2020-03-11T00:39:38",
    "not_after": "2020-06-09T00:39:38",
    "serial_number": "038a8e4d682ca4c058f282b3fcedce90413a",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "ws.pokerkg.dev",
    "name_value": "ws.pokerkg.dev",
    "id": 2572792732,
    "entry_timestamp": "2020-03-10T20:52:48.48",
    "not_before": "2020-03-10T19:52:48",
    "not_after": "2020-06-08T19:52:48",
    "serial_number": "0349ad0e3db382e0fa05d6a55de4f1f71ddd",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "ws.pokerkg.dev",
    "name_value": "ws.pokerkg.dev",
    "id": 2562620928,
    "entry_timestamp": "2020-03-10T20:52:48.324",
    "not_before": "2020-03-10T19:52:48",
    "not_after": "2020-06-08T19:52:48",
    "serial_number": "0349ad0e3db382e0fa05d6a55de4f1f71ddd",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "poker.pokerkg.dev",
    "name_value": "poker.pokerkg.dev",
    "id": 2572792452,
    "entry_timestamp": "2020-03-10T20:52:24.437",
    "not_before": "2020-03-10T19:52:24",
    "not_after": "2020-06-08T19:52:24",
    "serial_number": "03a8bd55d53bfdfdb411877abef947d9fe65",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "poker.pokerkg.dev",
    "name_value": "poker.pokerkg.dev",
    "id": 2562644114,
    "entry_timestamp": "2020-03-10T20:52:24.239",
    "not_before": "2020-03-10T19:52:24",
    "not_after": "2020-06-08T19:52:24",
    "serial_number": "03a8bd55d53bfdfdb411877abef947d9fe65",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "bo.pokerkg.dev",
    "name_value": "bo.pokerkg.dev",
    "id": 2447901245,
    "entry_timestamp": "2020-02-10T15:03:00.847",
    "not_before": "2020-02-10T14:03:00",
    "not_after": "2020-05-10T14:03:00",
    "serial_number": "04d4a34b134a002e7d8a4aa1d9e9ce67d83a",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "bo.pokerkg.dev",
    "name_value": "bo.pokerkg.dev",
    "id": 2438170359,
    "entry_timestamp": "2020-02-10T15:03:00.711",
    "not_before": "2020-02-10T14:03:00",
    "not_after": "2020-05-10T14:03:00",
    "serial_number": "04d4a34b134a002e7d8a4aa1d9e9ce67d83a",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "api.pokerkg.dev",
    "name_value": "api.pokerkg.dev",
    "id": 2325712657,
    "entry_timestamp": "2020-01-10T10:30:50.479",
    "not_before": "2020-01-10T09:30:50",
    "not_after": "2020-04-09T09:30:50",
    "serial_number": "0395512681e154d88eed9d37b6fe86da7c02",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "api.pokerkg.dev",
    "name_value": "api.pokerkg.dev",
    "id": 2316586612,
    "entry_timestamp": "2020-01-10T10:30:50.282",
    "not_before": "2020-01-10T09:30:50",
    "not_after": "2020-04-09T09:30:50",
    "serial_number": "0395512681e154d88eed9d37b6fe86da7c02",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "ws.pokerkg.dev",
    "name_value": "ws.pokerkg.dev",
    "id": 2292595661,
    "entry_timestamp": "2019-12-27T07:01:18.095",
    "not_before": "2019-12-27T06:01:17",
    "not_after": "2020-03-26T06:01:17",
    "serial_number": "0319c860882f5246eaafb1c40e579a6c9f05",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "ws.pokerkg.dev",
    "name_value": "ws.pokerkg.dev",
    "id": 2255432731,
    "entry_timestamp": "2019-12-27T07:01:17.86",
    "not_before": "2019-12-27T06:01:17",
    "not_after": "2020-03-26T06:01:17",
    "serial_number": "0319c860882f5246eaafb1c40e579a6c9f05",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "poker.pokerkg.dev",
    "name_value": "poker.pokerkg.dev",
    "id": 2292594118,
    "entry_timestamp": "2019-12-27T07:00:37.151",
    "not_before": "2019-12-27T06:00:36",
    "not_after": "2020-03-26T06:00:36",
    "serial_number": "0370bf264d04c2383834955968d0e7f1ab24",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "poker.pokerkg.dev",
    "name_value": "poker.pokerkg.dev",
    "id": 2251422073,
    "entry_timestamp": "2019-12-27T07:00:36.862",
    "not_before": "2019-12-27T06:00:36",
    "not_after": "2020-03-26T06:00:36",
    "serial_number": "0370bf264d04c2383834955968d0e7f1ab24",
    "result_count": 2
  }
]
"""

FAKE_RESPONSE_2 = """
[
  {
    "issuer_ca_id": 183267,
    "issuer_name": "C=US, O=Let's Encrypt, CN=R3",
    "common_name": "pokerkg.com",
    "name_value": "*.pokerkg.com\\npokerkg.com",
    "id": 4984123534,
    "entry_timestamp": "2021-08-04T19:56:27.132",
    "not_before": "2021-08-04T18:56:26",
    "not_after": "2021-11-02T18:56:24",
    "serial_number": "03da84896cc5baf008bea715fac999899af3",
    "result_count": 3
  },
  {
    "issuer_ca_id": 183267,
    "issuer_name": "C=US, O=Let's Encrypt, CN=R3",
    "common_name": "pokerkg.com",
    "name_value": "*.pokerkg.com\\npokerkg.com",
    "id": 4984123672,
    "entry_timestamp": "2021-08-04T19:56:26.796",
    "not_before": "2021-08-04T18:56:26",
    "not_after": "2021-11-02T18:56:24",
    "serial_number": "03da84896cc5baf008bea715fac999899af3",
    "result_count": 3
  },
  {
    "issuer_ca_id": 183267,
    "issuer_name": "C=US, O=Let's Encrypt, CN=R3",
    "common_name": "pokerkg.com",
    "name_value": "*.pokerkg.com\\npokerkg.com",
    "id": 4640846878,
    "entry_timestamp": "2021-06-03T17:31:32.097",
    "not_before": "2021-06-03T16:31:31",
    "not_after": "2021-09-01T16:31:31",
    "serial_number": "03ac8bad6c62a13f56aa2d12db40dc5dc72e",
    "result_count": 3
  },
  {
    "issuer_ca_id": 183267,
    "issuer_name": "C=US, O=Let's Encrypt, CN=R3",
    "common_name": "pokerkg.com",
    "name_value": "*.pokerkg.com\\npokerkg.com",
    "id": 4640849574,
    "entry_timestamp": "2021-06-03T17:31:31.876",
    "not_before": "2021-06-03T16:31:31",
    "not_after": "2021-09-01T16:31:31",
    "serial_number": "03ac8bad6c62a13f56aa2d12db40dc5dc72e",
    "result_count": 3
  },
  {
    "issuer_ca_id": 183267,
    "issuer_name": "C=US, O=Let's Encrypt, CN=R3",
    "common_name": "pokerkg.com",
    "name_value": "*.pokerkg.com\\npokerkg.com",
    "id": 4326294714,
    "entry_timestamp": "2021-04-04T17:39:04.013",
    "not_before": "2021-04-04T16:39:03",
    "not_after": "2021-07-03T16:39:03",
    "serial_number": "04f58477a14e292712903aeaf7f0f5391f01",
    "result_count": 3
  },
  {
    "issuer_ca_id": 183267,
    "issuer_name": "C=US, O=Let's Encrypt, CN=R3",
    "common_name": "pokerkg.com",
    "name_value": "*.pokerkg.com\\npokerkg.com",
    "id": 4326295205,
    "entry_timestamp": "2021-04-04T17:39:03.786",
    "not_before": "2021-04-04T16:39:03",
    "not_after": "2021-07-03T16:39:03",
    "serial_number": "04f58477a14e292712903aeaf7f0f5391f01",
    "result_count": 3
  },
  {
    "issuer_ca_id": 183267,
    "issuer_name": "C=US, O=Let's Encrypt, CN=R3",
    "common_name": "pokerkg.com",
    "name_value": "*.pokerkg.com\\npokerkg.com",
    "id": 4026190295,
    "entry_timestamp": "2021-02-03T19:30:02.158",
    "not_before": "2021-02-03T18:30:01",
    "not_after": "2021-05-04T18:30:01",
    "serial_number": "04e7137bc3b8380b62cab2022efeda857ff8",
    "result_count": 3
  },
  {
    "issuer_ca_id": 183267,
    "issuer_name": "C=US, O=Let's Encrypt, CN=R3",
    "common_name": "pokerkg.com",
    "name_value": "*.pokerkg.com\\npokerkg.com",
    "id": 4026191222,
    "entry_timestamp": "2021-02-03T19:30:02.032",
    "not_before": "2021-02-03T18:30:01",
    "not_after": "2021-05-04T18:30:01",
    "serial_number": "04e7137bc3b8380b62cab2022efeda857ff8",
    "result_count": 3
  },
  {
    "issuer_ca_id": 183267,
    "issuer_name": "C=US, O=Let's Encrypt, CN=R3",
    "common_name": "ws.pokerkg.com",
    "name_value": "ws.pokerkg.com",
    "id": 3781514955,
    "entry_timestamp": "2020-12-15T00:31:50.81",
    "not_before": "2020-12-14T23:31:50",
    "not_after": "2021-03-14T23:31:50",
    "serial_number": "033be4213f03b2b563fa5bc3fe1b012748ca",
    "result_count": 2
  },
  {
    "issuer_ca_id": 183267,
    "issuer_name": "C=US, O=Let's Encrypt, CN=R3",
    "common_name": "ws.pokerkg.com",
    "name_value": "ws.pokerkg.com",
    "id": 3781509082,
    "entry_timestamp": "2020-12-15T00:31:50.607",
    "not_before": "2020-12-14T23:31:50",
    "not_after": "2021-03-14T23:31:50",
    "serial_number": "033be4213f03b2b563fa5bc3fe1b012748ca",
    "result_count": 2
  },
  {
    "issuer_ca_id": 183267,
    "issuer_name": "C=US, O=Let's Encrypt, CN=R3",
    "common_name": "api.pokerkg.com",
    "name_value": "api.pokerkg.com",
    "id": 3781505451,
    "entry_timestamp": "2020-12-15T00:29:33.221",
    "not_before": "2020-12-14T23:29:32",
    "not_after": "2021-03-14T23:29:32",
    "serial_number": "0382c54148a1e2a08a64d6de1901c42c6c65",
    "result_count": 2
  },
  {
    "issuer_ca_id": 183267,
    "issuer_name": "C=US, O=Let's Encrypt, CN=R3",
    "common_name": "api.pokerkg.com",
    "name_value": "api.pokerkg.com",
    "id": 3781506336,
    "entry_timestamp": "2020-12-15T00:29:33.013",
    "not_before": "2020-12-14T23:29:32",
    "not_after": "2021-03-14T23:29:32",
    "serial_number": "0382c54148a1e2a08a64d6de1901c42c6c65",
    "result_count": 2
  },
  {
    "issuer_ca_id": 183267,
    "issuer_name": "C=US, O=Let's Encrypt, CN=R3",
    "common_name": "admin8sh2bote1sg.pokerkg.com",
    "name_value": "admin8sh2bote1sg.pokerkg.com",
    "id": 3781502958,
    "entry_timestamp": "2020-12-15T00:28:30.489",
    "not_before": "2020-12-14T23:28:29",
    "not_after": "2021-03-14T23:28:29",
    "serial_number": "03347257057c6573333d58984986f52b3559",
    "result_count": 2
  },
  {
    "issuer_ca_id": 183267,
    "issuer_name": "C=US, O=Let's Encrypt, CN=R3",
    "common_name": "admin8sh2bote1sg.pokerkg.com",
    "name_value": "admin8sh2bote1sg.pokerkg.com",
    "id": 3781497165,
    "entry_timestamp": "2020-12-15T00:28:29.896",
    "not_before": "2020-12-14T23:28:29",
    "not_after": "2021-03-14T23:28:29",
    "serial_number": "03347257057c6573333d58984986f52b3559",
    "result_count": 2
  },
  {
    "issuer_ca_id": 183267,
    "issuer_name": "C=US, O=Let's Encrypt, CN=R3",
    "common_name": "game.pokerkg.com",
    "name_value": "game.pokerkg.com",
    "id": 3781501702,
    "entry_timestamp": "2020-12-15T00:28:04.161",
    "not_before": "2020-12-14T23:28:03",
    "not_after": "2021-03-14T23:28:03",
    "serial_number": "048db535c578e9a05dd43d6182b134961061",
    "result_count": 2
  },
  {
    "issuer_ca_id": 183267,
    "issuer_name": "C=US, O=Let's Encrypt, CN=R3",
    "common_name": "game.pokerkg.com",
    "name_value": "game.pokerkg.com",
    "id": 3781496905,
    "entry_timestamp": "2020-12-15T00:28:03.86",
    "not_before": "2020-12-14T23:28:03",
    "not_after": "2021-03-14T23:28:03",
    "serial_number": "048db535c578e9a05dd43d6182b134961061",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "ws.pokerkg.com",
    "name_value": "ws.pokerkg.com",
    "id": 3503520391,
    "entry_timestamp": "2020-10-13T18:50:44.441",
    "not_before": "2020-10-13T17:50:44",
    "not_after": "2021-01-11T17:50:44",
    "serial_number": "03e21fa4e340a40bcdec174d09ff5e936a1c",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "ws.pokerkg.com",
    "name_value": "ws.pokerkg.com",
    "id": 3503516671,
    "entry_timestamp": "2020-10-13T18:50:44.165",
    "not_before": "2020-10-13T17:50:44",
    "not_after": "2021-01-11T17:50:44",
    "serial_number": "03e21fa4e340a40bcdec174d09ff5e936a1c",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "api.pokerkg.com",
    "name_value": "api.pokerkg.com",
    "id": 3503514856,
    "entry_timestamp": "2020-10-13T18:48:26.554",
    "not_before": "2020-10-13T17:48:26",
    "not_after": "2021-01-11T17:48:26",
    "serial_number": "0496d71becc296bf829fbb48370092f29836",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "api.pokerkg.com",
    "name_value": "api.pokerkg.com",
    "id": 3503515609,
    "entry_timestamp": "2020-10-13T18:48:26.369",
    "not_before": "2020-10-13T17:48:26",
    "not_after": "2021-01-11T17:48:26",
    "serial_number": "0496d71becc296bf829fbb48370092f29836",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "admin8sh2bote1sg.pokerkg.com",
    "name_value": "admin8sh2bote1sg.pokerkg.com",
    "id": 3503512265,
    "entry_timestamp": "2020-10-13T18:47:33.201",
    "not_before": "2020-10-13T17:47:32",
    "not_after": "2021-01-11T17:47:32",
    "serial_number": "04823dd98db9756ae9af2d0d6c26238d8ebd",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "admin8sh2bote1sg.pokerkg.com",
    "name_value": "admin8sh2bote1sg.pokerkg.com",
    "id": 3503512905,
    "entry_timestamp": "2020-10-13T18:47:33.058",
    "not_before": "2020-10-13T17:47:32",
    "not_after": "2021-01-11T17:47:32",
    "serial_number": "04823dd98db9756ae9af2d0d6c26238d8ebd",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "game.pokerkg.com",
    "name_value": "game.pokerkg.com",
    "id": 3503510475,
    "entry_timestamp": "2020-10-13T18:46:16.974",
    "not_before": "2020-10-13T17:46:16",
    "not_after": "2021-01-11T17:46:16",
    "serial_number": "041802a96a311b7885153d02c712d13fc0ce",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "game.pokerkg.com",
    "name_value": "game.pokerkg.com",
    "id": 3503505561,
    "entry_timestamp": "2020-10-13T18:46:16.355",
    "not_before": "2020-10-13T17:46:16",
    "not_after": "2021-01-11T17:46:16",
    "serial_number": "041802a96a311b7885153d02c712d13fc0ce",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "ws.pokerkg.com",
    "name_value": "ws.pokerkg.com",
    "id": 3244941773,
    "entry_timestamp": "2020-08-15T20:37:01.672",
    "not_before": "2020-08-15T19:37:01",
    "not_after": "2020-11-13T19:37:01",
    "serial_number": "04f7f6069499d8b0207eaa3a279907943bfc",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "ws.pokerkg.com",
    "name_value": "ws.pokerkg.com",
    "id": 3244941625,
    "entry_timestamp": "2020-08-15T20:37:01.523",
    "not_before": "2020-08-15T19:37:01",
    "not_after": "2020-11-13T19:37:01",
    "serial_number": "04f7f6069499d8b0207eaa3a279907943bfc",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "game.pokerkg.com",
    "name_value": "game.pokerkg.com",
    "id": 3244922874,
    "entry_timestamp": "2020-08-15T20:32:43.497",
    "not_before": "2020-08-15T19:32:43",
    "not_after": "2020-11-13T19:32:43",
    "serial_number": "04d27fe3bd8e5f91a455593de42a5e678692",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "game.pokerkg.com",
    "name_value": "game.pokerkg.com",
    "id": 3244923076,
    "entry_timestamp": "2020-08-15T20:32:43.321",
    "not_before": "2020-08-15T19:32:43",
    "not_after": "2020-11-13T19:32:43",
    "serial_number": "04d27fe3bd8e5f91a455593de42a5e678692",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "api.pokerkg.com",
    "name_value": "api.pokerkg.com",
    "id": 3244921464,
    "entry_timestamp": "2020-08-15T20:32:18.251",
    "not_before": "2020-08-15T19:32:17",
    "not_after": "2020-11-13T19:32:17",
    "serial_number": "0346eec8febbd723ab86b60f9747a7bc6699",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "api.pokerkg.com",
    "name_value": "api.pokerkg.com",
    "id": 3244922739,
    "entry_timestamp": "2020-08-15T20:32:18.03",
    "not_before": "2020-08-15T19:32:17",
    "not_after": "2020-11-13T19:32:17",
    "serial_number": "0346eec8febbd723ab86b60f9747a7bc6699",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "admin8sh2bote1sg.pokerkg.com",
    "name_value": "admin8sh2bote1sg.pokerkg.com",
    "id": 3244918068,
    "entry_timestamp": "2020-08-15T20:31:52.278",
    "not_before": "2020-08-15T19:31:51",
    "not_after": "2020-11-13T19:31:51",
    "serial_number": "0371ae7c61ed830bb72df2f4b384205d6e82",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "admin8sh2bote1sg.pokerkg.com",
    "name_value": "admin8sh2bote1sg.pokerkg.com",
    "id": 3244919373,
    "entry_timestamp": "2020-08-15T20:31:52.074",
    "not_before": "2020-08-15T19:31:51",
    "not_after": "2020-11-13T19:31:51",
    "serial_number": "0371ae7c61ed830bb72df2f4b384205d6e82",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "thapp.todaysico.com",
    "name_value": "admin8sh2bote1sg.pokerkg.com\\napi.pokerkg.com\\ngame.pokerkg.com\\nws.pokerkg.com",
    "id": 2976829706,
    "entry_timestamp": "2020-06-17T21:42:11.22",
    "not_before": "2020-06-17T20:42:10",
    "not_after": "2020-09-15T20:42:10",
    "serial_number": "0488d66bc4afb3af4bf46160e36d1194341e",
    "result_count": 4
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "thapp.todaysico.com",
    "name_value": "admin8sh2bote1sg.pokerkg.com\\napi.pokerkg.com\\ngame.pokerkg.com\\nws.pokerkg.com",
    "id": 2969985734,
    "entry_timestamp": "2020-06-17T21:42:11.078",
    "not_before": "2020-06-17T20:42:10",
    "not_after": "2020-09-15T20:42:10",
    "serial_number": "0488d66bc4afb3af4bf46160e36d1194341e",
    "result_count": 4
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "ws.pokerkg.com",
    "name_value": "ws.pokerkg.com",
    "id": 2749575173,
    "entry_timestamp": "2020-04-18T13:58:28.959",
    "not_before": "2020-04-18T12:58:28",
    "not_after": "2020-07-17T12:58:28",
    "serial_number": "049826033ef08bd336875e602655c40b01ff",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "ws.pokerkg.com",
    "name_value": "ws.pokerkg.com",
    "id": 2712965740,
    "entry_timestamp": "2020-04-18T13:58:28.82",
    "not_before": "2020-04-18T12:58:28",
    "not_after": "2020-07-17T12:58:28",
    "serial_number": "049826033ef08bd336875e602655c40b01ff",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "api.pokerkg.com",
    "name_value": "api.pokerkg.com",
    "id": 2749574974,
    "entry_timestamp": "2020-04-18T13:58:03.991",
    "not_before": "2020-04-18T12:58:03",
    "not_after": "2020-07-17T12:58:03",
    "serial_number": "0307e417836014e9858df364cbe16c8eec89",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "api.pokerkg.com",
    "name_value": "api.pokerkg.com",
    "id": 2710818068,
    "entry_timestamp": "2020-04-18T13:58:03.843",
    "not_before": "2020-04-18T12:58:03",
    "not_after": "2020-07-17T12:58:03",
    "serial_number": "0307e417836014e9858df364cbe16c8eec89",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "admin8sh2bote1sg.pokerkg.com",
    "name_value": "admin8sh2bote1sg.pokerkg.com",
    "id": 2749571609,
    "entry_timestamp": "2020-04-18T13:57:41.622",
    "not_before": "2020-04-18T12:57:41",
    "not_after": "2020-07-17T12:57:41",
    "serial_number": "041832c09da53d7b9b1a55df80968ef7fb2a",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "admin8sh2bote1sg.pokerkg.com",
    "name_value": "admin8sh2bote1sg.pokerkg.com",
    "id": 2710817530,
    "entry_timestamp": "2020-04-18T13:57:41.498",
    "not_before": "2020-04-18T12:57:41",
    "not_after": "2020-07-17T12:57:41",
    "serial_number": "041832c09da53d7b9b1a55df80968ef7fb2a",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "game.pokerkg.com",
    "name_value": "game.pokerkg.com",
    "id": 2749568105,
    "entry_timestamp": "2020-04-18T13:57:18.896",
    "not_before": "2020-04-18T12:57:18",
    "not_after": "2020-07-17T12:57:18",
    "serial_number": "04ee41ac00e9bea5e36b8ac52e001509f9c0",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "game.pokerkg.com",
    "name_value": "game.pokerkg.com",
    "id": 2711523248,
    "entry_timestamp": "2020-04-18T13:57:18.701",
    "not_before": "2020-04-18T12:57:18",
    "not_after": "2020-07-17T12:57:18",
    "serial_number": "04ee41ac00e9bea5e36b8ac52e001509f9c0",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "ws.pokerkg.com",
    "name_value": "ws.pokerkg.com",
    "id": 2485436931,
    "entry_timestamp": "2020-02-17T15:10:24.359",
    "not_before": "2020-02-17T14:10:23",
    "not_after": "2020-05-17T14:10:23",
    "serial_number": "03703949e91b2f0a76f27cff090b0729a275",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "ws.pokerkg.com",
    "name_value": "ws.pokerkg.com",
    "id": 2468007774,
    "entry_timestamp": "2020-02-17T15:10:23.811",
    "not_before": "2020-02-17T14:10:23",
    "not_after": "2020-05-17T14:10:23",
    "serial_number": "03703949e91b2f0a76f27cff090b0729a275",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "api.pokerkg.com",
    "name_value": "api.pokerkg.com",
    "id": 2485434793,
    "entry_timestamp": "2020-02-17T15:09:49.642",
    "not_before": "2020-02-17T14:09:49",
    "not_after": "2020-05-17T14:09:49",
    "serial_number": "039faf35bb2685c93db5ca727e653f8320da",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "api.pokerkg.com",
    "name_value": "api.pokerkg.com",
    "id": 2469840564,
    "entry_timestamp": "2020-02-17T15:09:49.38",
    "not_before": "2020-02-17T14:09:49",
    "not_after": "2020-05-17T14:09:49",
    "serial_number": "039faf35bb2685c93db5ca727e653f8320da",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "admin8sh2bote1sg.pokerkg.com",
    "name_value": "admin8sh2bote1sg.pokerkg.com",
    "id": 2485432439,
    "entry_timestamp": "2020-02-17T15:09:24.039",
    "not_before": "2020-02-17T14:09:23",
    "not_after": "2020-05-17T14:09:23",
    "serial_number": "0405e45b82666fffda8bd161f410eac88d4e",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "admin8sh2bote1sg.pokerkg.com",
    "name_value": "admin8sh2bote1sg.pokerkg.com",
    "id": 2468173960,
    "entry_timestamp": "2020-02-17T15:09:23.884",
    "not_before": "2020-02-17T14:09:23",
    "not_after": "2020-05-17T14:09:23",
    "serial_number": "0405e45b82666fffda8bd161f410eac88d4e",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "game.pokerkg.com",
    "name_value": "game.pokerkg.com",
    "id": 2485397678,
    "entry_timestamp": "2020-02-17T14:51:03.229",
    "not_before": "2020-02-17T13:51:02",
    "not_after": "2020-05-17T13:51:02",
    "serial_number": "04396ef85a0641de81c6ed0c7d3167b23578",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "game.pokerkg.com",
    "name_value": "game.pokerkg.com",
    "id": 2467988658,
    "entry_timestamp": "2020-02-17T14:51:03.019",
    "not_before": "2020-02-17T13:51:02",
    "not_after": "2020-05-17T13:51:02",
    "serial_number": "04396ef85a0641de81c6ed0c7d3167b23578",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "api.pokerkg.com",
    "name_value": "api.pokerkg.com",
    "id": 2485396203,
    "entry_timestamp": "2020-02-17T14:50:33.326",
    "not_before": "2020-02-17T13:50:33",
    "not_after": "2020-05-17T13:50:33",
    "serial_number": "035bbb149eabdc68045cc6ed6cc143aec115",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "api.pokerkg.com",
    "name_value": "api.pokerkg.com",
    "id": 2468164104,
    "entry_timestamp": "2020-02-17T14:50:33.082",
    "not_before": "2020-02-17T13:50:33",
    "not_after": "2020-05-17T13:50:33",
    "serial_number": "035bbb149eabdc68045cc6ed6cc143aec115",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "game.pokerkg.com",
    "name_value": "game.pokerkg.com",
    "id": 2485254253,
    "entry_timestamp": "2020-02-17T13:49:26.786",
    "not_before": "2020-02-17T12:49:26",
    "not_after": "2020-05-17T12:49:26",
    "serial_number": "03c4addf84c399b559d7f9df6668cb4f5db2",
    "result_count": 2
  },
  {
    "issuer_ca_id": 16418,
    "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
    "common_name": "game.pokerkg.com",
    "name_value": "game.pokerkg.com",
    "id": 2467864506,
    "entry_timestamp": "2020-02-17T13:49:26.495",
    "not_before": "2020-02-17T12:49:26",
    "not_after": "2020-05-17T12:49:26",
    "serial_number": "03c4addf84c399b559d7f9df6668cb4f5db2",
    "result_count": 2
  }
]
"""
DEBUG = True


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
        for domain in domains:
            if DEBUG:
                if domain == "pokerkg.dev":
                    responses.append(
                        (
                            domain,
                            self._deduplicate_results(
                                JSONDecoder().decode(FAKE_RESPONSE)
                            ),
                        )
                    )
                elif domain == "pokerkg.com":
                    responses.append(
                        (
                            domain,
                            self._deduplicate_results(
                                JSONDecoder().decode(FAKE_RESPONSE_2)
                            ),
                        )
                    )
                else:
                    raise ValueError
                break

            request_params = {
                "q": f"%{domain}%",
                "output": "json",
            }
            response = requests.get("https://crt.sh", params=request_params)
            response.raise_for_status()
            response_json = response.json()

            responses.append((domain, self._deduplicate_results(response_json)))

        # Process responses, add new records to the database
        with self._database as session:
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
                    ssl_cert.identities = [
                        SSLCertificateIdentity(identity=identity)
                        for identity in record["name_value"].splitlines()
                    ]
                    session.add(ssl_cert)
                    cert_stat += 1
                self._logger.info(
                    f"Discovered {cert_stat} new associated SSL certificates for {domain_name}."
                )
