from __future__ import annotations

import unittest

from _support import RecordingOpener
from fxmacrodata_data import FXMacroDataClient, FXMacroDataError, known_at, to_csv, vintage_rows

SERIES_PATH = "/v1/announcements/usd/policy_rate"


def _page(rows, offset, total, has_more, next_offset=None, **extra):
    body = {"currency": "USD", "indicator": "policy_rate", "data": rows,
            "pagination": {"limit": 100, "offset": offset, "returned_count": len(rows),
                           "total_count": total, "has_more": has_more, "next_offset": next_offset}}
    body.update(extra)
    return 200, body


def _row(day, val, stamp, status="confirmed"):
    return {"date": day, "val": val, "announcement_datetime": stamp,
            "publication_time_status": status, "publication_time_precision": "minute"}


class ClientRequestTests(unittest.TestCase):
    def test_key_goes_in_header_never_in_url(self):
        opener = RecordingOpener({SERIES_PATH: _page([], 0, 0, False)})
        FXMacroDataClient(api_key="fixture-key", opener=opener).series("USD", "policy_rate")
        call = opener.calls[0]
        self.assertEqual(call["headers"]["X-API-Key"], "fixture-key")
        self.assertNotIn("fixture-key", call["url"])
        self.assertNotIn("api_key", call["query"])

    def test_keyless_client_sends_no_key_header(self):
        opener = RecordingOpener({SERIES_PATH: _page([], 0, 0, False)})
        FXMacroDataClient(api_key="", opener=opener).series("usd", "policy_rate")
        self.assertNotIn("X-API-Key", opener.calls[0]["headers"])

    def test_documented_query_parameters_are_passed_through(self):
        opener = RecordingOpener({SERIES_PATH: _page([], 0, 0, False)})
        FXMacroDataClient(api_key="", opener=opener).series(
            "usd", "policy_rate", start="2020-01-01", end="2020-12-31", revisions="all",
            extra={"seasonality": "sa"})
        query = opener.calls[0]["query"]
        self.assertEqual(query["start_date"], "2020-01-01")
        self.assertEqual(query["end_date"], "2020-12-31")
        self.assertEqual(query["revisions"], "all")
        self.assertEqual(query["seasonality"], "sa")
        self.assertEqual(query["limit"], "100")

    def test_path_segments_are_validated(self):
        client = FXMacroDataClient(api_key="", opener=RecordingOpener({}))
        with self.assertRaises(ValueError):
            client.series("usd/../x", "policy_rate")
        with self.assertRaises(ValueError):
            client.series("usd", "policy rate")
        with self.assertRaises(ValueError):
            client.series("usd", "policy_rate", start="01/01/2020")

    def test_pagination_follows_next_offset_until_done(self):
        def route(query):
            if query["offset"] == "0":
                return _page([_row("2026-02-01", 2.0, 1772000000)], 0, 2, True, 100)
            return _page([_row("2026-01-01", 1.0, 1769000000)], 100, 2, False)

        opener = RecordingOpener({SERIES_PATH: route})
        payload = FXMacroDataClient(api_key="", opener=opener).series("usd", "policy_rate")
        self.assertEqual([r["date"] for r in payload["data"]], ["2026-02-01", "2026-01-01"])
        self.assertEqual([c["query"]["offset"] for c in opener.calls], ["0", "100"])
        self.assertEqual(payload["indicator"], "policy_rate")
        self.assertNotIn("pagination", payload)

    def test_non_advancing_pagination_is_refused(self):
        opener = RecordingOpener({SERIES_PATH: _page([_row("2026-01-01", 1.0, 1)], 0, 9, True, 0)})
        with self.assertRaises(FXMacroDataError):
            FXMacroDataClient(api_key="", opener=opener).series("usd", "policy_rate")

    def test_auth_error_explains_the_key_and_never_echoes_it(self):
        opener = RecordingOpener({"/v1/forex/eur/usd": (403, {"detail": "bad key fixture-key"})})
        with self.assertRaises(FXMacroDataError) as caught:
            FXMacroDataClient(api_key="fixture-key", opener=opener).fx("EUR", "USD")
        self.assertIn("403", str(caught.exception))
        self.assertNotIn("fixture-key", str(caught.exception))

        opener = RecordingOpener({"/v1/forex/eur/usd": (401, {"detail": "subscription required"})})
        with self.assertRaises(FXMacroDataError) as caught:
            FXMacroDataClient(api_key="", opener=opener).fx("eur", "usd")
        self.assertIn("FXMACRODATA_API_KEY", str(caught.exception))

    def test_keyless_truncation_is_reported(self):
        opener = RecordingOpener({SERIES_PATH: _page(
            [], 0, 0, False,
            freemium_window={"applied": True, "max_days": 90, "cutoff_date": "2026-07-17"})})
        client = FXMacroDataClient(api_key="", opener=opener)
        client.series("usd", "policy_rate")
        self.assertEqual(len(client.notices), 1)
        self.assertIn("2026-07-17", client.notices[0])


class VintageTests(unittest.TestCase):
    ROWS = [
        {"date": "2026-03-01", "val": 120.0, "announcement_datetime": 1775800000,
         "revisions": [
             {"epoch": 1775200000, "val": 100.0, "publication_time_status": "confirmed",
              "is_first_release": True},
             {"epoch": 1775800000, "val": 120.0, "publication_time_status": "confirmed"},
         ]},
        {"date": "2026-02-01", "val": 90.0, "announcement_datetime": 1772600000,
         "revisions": [
             {"epoch": 1772600000, "val": 90.0, "publication_time_status": "unverified"},
         ]},
    ]

    def test_vintage_rows_expand_the_ledger_with_their_own_clocks(self):
        rows = vintage_rows(self.ROWS)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["date"], "2026-03-01")
        self.assertEqual(rows[0]["val"], 100.0)
        self.assertEqual(rows[0]["announcement_datetime"], 1775200000)
        self.assertEqual(rows[1]["vintage_index"], 1)
        self.assertEqual(rows[1]["val"], 120.0)

    def test_known_at_selects_latest_public_confirmed_vintage(self):
        rows = vintage_rows(self.ROWS)
        before_revision = known_at(rows, 1775500000)
        self.assertEqual(before_revision["2026-03-01"]["val"], 100.0)
        # The February value has no confirmed publication time.
        self.assertNotIn("2026-02-01", before_revision)
        after_revision = known_at(rows, 1775900000)
        self.assertEqual(after_revision["2026-03-01"]["val"], 120.0)
        self.assertEqual(known_at(rows, 1775100000), {})
        self.assertIn("2026-02-01", known_at(rows, 1775900000, confirmed_only=False))

    def test_csv_keeps_field_names_and_adds_utc_time(self):
        text = to_csv([_row("2026-01-01", 4.5, 0)])
        header, line = text.splitlines()
        self.assertEqual(
            header,
            "date,val,announcement_datetime,announcement_datetime_utc,"
            "publication_time_status,publication_time_precision",
        )
        self.assertEqual(line, "2026-01-01,4.5,0,1970-01-01T00:00:00Z,confirmed,minute")


if __name__ == "__main__":
    unittest.main()
