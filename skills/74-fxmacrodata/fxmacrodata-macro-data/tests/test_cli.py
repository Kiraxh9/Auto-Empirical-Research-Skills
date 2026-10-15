from __future__ import annotations

import contextlib
import io
import os
import tempfile
import unittest

from _support import RecordingOpener
from fxmacrodata_data import FXMacroDataClient, build_parser, run


def _run(argv, routes):
    opener = RecordingOpener(routes)
    client = FXMacroDataClient(api_key="", opener=opener)
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = run(argv, client=client)
    return code, out.getvalue(), err.getvalue(), opener


class CliTests(unittest.TestCase):
    def test_no_command_line_option_accepts_a_key(self):
        parser = build_parser()
        for argv in (["series", "usd", "gdp", "--api-key", "x"], ["fx", "eur", "usd", "--key", "x"]):
            with self.subTest(argv=argv), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    parser.parse_args(argv)

    def test_catalogue_csv_has_one_row_per_slug(self):
        routes = {"/v1/data_catalogue/usd": (200, {
            "policy_rate": {"name": "Policy Rate", "unit": "%", "frequency": "irregular"},
            "inflation": {"name": "Inflation", "unit": "%", "frequency": "monthly"},
        })}
        code, out, _, _ = _run(["catalogue", "USD"], routes)
        self.assertEqual(code, 0)
        lines = out.splitlines()
        self.assertEqual(lines[0], "indicator,name,unit,frequency")
        self.assertEqual(lines[1], "inflation,Inflation,%,monthly")

    def test_series_vintages_written_to_file(self):
        routes = {"/v1/announcements/usd/non_farm_payrolls": (200, {
            "data": [{"date": "2026-03-01", "val": 2.0, "announcement_datetime": 20,
                      "revisions": [{"epoch": 10, "val": 1.0}, {"epoch": 20, "val": 2.0}]}],
            "pagination": {"offset": 0, "returned_count": 1, "total_count": 1, "has_more": False},
        })}
        with tempfile.TemporaryDirectory() as tmp:
            target = os.path.join(tmp, "nfp.csv")
            code, out, _, opener = _run(
                ["series", "usd", "non_farm_payrolls", "--revisions", "all", "--vintages", "--out", target],
                routes)
            with open(target, encoding="utf-8") as handle:
                lines = handle.read().splitlines()
        self.assertEqual(code, 0)
        self.assertEqual(out, "")
        self.assertEqual(opener.calls[0]["query"]["revisions"], "all")
        self.assertEqual(len(lines), 3)
        self.assertTrue(lines[1].startswith("2026-03-01,0,10,"))

    def test_vintages_require_revisions_all(self):
        code, _, err, opener = _run(["series", "usd", "gdp", "--vintages"], {})
        self.assertEqual(code, 2)
        self.assertIn("--revisions all", err)
        self.assertEqual(opener.calls, [])

    def test_unknown_series_option_is_rejected(self):
        code, _, err, _ = _run(["series", "usd", "gdp", "--option", "api_key=x"], {})
        self.assertEqual(code, 2)
        self.assertIn("unsupported --option", err)

    def test_calendar_defaults_to_json_and_passes_filters(self):
        routes = {"/v1/calendar/usd": (200, {"currency": "USD", "data": [
            {"announcement_datetime": 1, "release": "inflation"}]})}
        code, out, _, opener = _run(["calendar", "usd", "--indicator", "inflation"], routes)
        self.assertEqual(code, 0)
        self.assertIn('"release": "inflation"', out)
        self.assertEqual(opener.calls[0]["query"], {"indicator": "inflation"})

    def test_http_error_exits_2(self):
        routes = {"/v1/forex/eur/usd": (401, {"detail": "subscription required"})}
        code, out, err, _ = _run(["fx", "eur", "usd"], routes)
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("HTTP 401", err)


if __name__ == "__main__":
    unittest.main()
