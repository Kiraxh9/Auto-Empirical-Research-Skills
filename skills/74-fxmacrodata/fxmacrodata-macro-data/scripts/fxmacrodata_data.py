#!/usr/bin/env python3
"""Download official macro series, release timing and FX from FXMacroData.

Standard library only. Responses keep FXMacroData's own field names; the CSV
writer flattens rows without renaming or rescaling anything.

    python fxmacrodata_data.py catalogue usd
    python fxmacrodata_data.py series usd policy_rate --start 2000-01-01 --out fed_funds.csv
    python fxmacrodata_data.py series usd non_farm_payrolls --revisions all --vintages --out nfp_vintages.csv
    python fxmacrodata_data.py calendar usd --indicator inflation
    python fxmacrodata_data.py fx eur usd --start 2024-01-01 --out eurusd.csv

The API key, when needed, is read from FXMACRODATA_API_KEY and sent in the
X-API-Key header. It is never accepted on the command line or put in a URL.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

API_BASE = "https://api.fxmacrodata.com/v1"
KEY_ENV = "FXMACRODATA_API_KEY"
PAGE_LIMIT = 100
MAX_PAGES = 500
USER_AGENT = "aers-fxmacrodata-macro-data/1.0"

_CURRENCY = re.compile(r"^[a-z]{3,4}$")
_SLUG = re.compile(r"^[a-z0-9_]{1,64}$")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# opener(url, headers, timeout) -> (status, body bytes)
Opener = Callable[[str, Dict[str, str], float], Tuple[int, bytes]]


class FXMacroDataError(RuntimeError):
    """A request failed; the message never contains the API key."""


def _urllib_opener(url: str, headers: Dict[str, str], timeout: float) -> Tuple[int, bytes]:
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed https base
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def _code(value: str, kind: str = "currency") -> str:
    text = str(value).strip().lower()
    pattern = _CURRENCY if kind == "currency" else _SLUG
    if not pattern.match(text):
        raise ValueError(f"invalid {kind}: {value!r}")
    return text


def _date(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if not _DATE.match(value):
        raise ValueError(f"dates must be YYYY-MM-DD, got {value!r}")
    return value


class FXMacroDataClient:
    """Small read-only client for the documented REST endpoints."""

    def __init__(self, api_key: Optional[str] = None, *, opener: Optional[Opener] = None,
                 timeout: float = 30.0, base_url: str = API_BASE):
        self._api_key = api_key if api_key is not None else os.getenv(KEY_ENV, "")
        self._opener = opener or _urllib_opener
        self._timeout = timeout
        self._base = base_url.rstrip("/")
        self.notices: List[str] = []

    @property
    def authenticated(self) -> bool:
        return bool(self._api_key)

    def _redact(self, text: str) -> str:
        return text.replace(self._api_key, "[redacted]") if self._api_key else text

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        query = {k: v for k, v in (params or {}).items() if v is not None}
        url = self._base + path
        if query:
            url += "?" + urllib.parse.urlencode(query)
        headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
        if self._api_key:
            headers["X-API-Key"] = self._api_key
        try:
            status, body = self._opener(url, headers, self._timeout)
        except OSError as exc:
            raise FXMacroDataError(self._redact(f"request to {path} failed: {exc}")) from None
        text = body.decode("utf-8", errors="replace")
        if status in (401, 402, 403):
            hint = "" if self._api_key else f"; set {KEY_ENV} for non-USD data, FX and full history"
            raise FXMacroDataError(self._redact(f"{path} returned HTTP {status}{hint}: {text[:300]}"))
        if status >= 400:
            raise FXMacroDataError(self._redact(f"{path} returned HTTP {status}: {text[:300]}"))
        try:
            payload = json.loads(text)
        except ValueError:
            raise FXMacroDataError(f"{path} did not return JSON") from None
        if not isinstance(payload, dict):
            raise FXMacroDataError(f"{path} returned an unexpected JSON shape")
        self._collect_notices(payload)
        return payload

    def _collect_notices(self, payload: Dict[str, Any]) -> None:
        window = payload.get("freemium_window")
        if isinstance(window, dict) and window.get("applied"):
            self.notices.append(
                "history truncated to the keyless window"
                + (f" (from {window['cutoff_date']})" if window.get("cutoff_date") else "")
                + f"; set {KEY_ENV} for the full history"
            )
        delay = payload.get("freemium_delay")
        if isinstance(delay, dict) and delay:
            self.notices.append("keyless responses are delayed; the newest release may be withheld")

    def get_all(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Follow offset pagination and return the first envelope with every row in ``data``."""
        query = dict(params or {})
        query["limit"] = PAGE_LIMIT
        query["offset"] = 0
        first: Optional[Dict[str, Any]] = None
        rows: List[Any] = []
        for _ in range(MAX_PAGES):
            payload = self.get(path, query)
            data = payload.get("data")
            if not isinstance(data, list):
                raise FXMacroDataError(f"{path} response has no data array")
            if first is None:
                first = payload
            rows.extend(data)
            page = payload.get("pagination")
            if not isinstance(page, dict) or not page.get("has_more"):
                break
            next_offset = page.get("next_offset")
            if not isinstance(next_offset, int) or next_offset <= query["offset"]:
                raise FXMacroDataError(f"{path} pagination did not advance; refusing a partial history")
            query["offset"] = next_offset
        else:
            raise FXMacroDataError(f"{path} exceeded {MAX_PAGES} pages")
        assert first is not None
        result = dict(first)
        result["data"] = rows
        result.pop("pagination", None)
        return result

    def catalogue(self, currency: str) -> Dict[str, Any]:
        return self.get(f"/data_catalogue/{_code(currency)}")

    def series(self, currency: str, indicator: str, *, start: Optional[str] = None,
               end: Optional[str] = None, revisions: Optional[str] = None,
               extra: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        if revisions not in (None, "latest", "first", "final", "all"):
            raise ValueError("revisions must be latest, first, final or all")
        params: Dict[str, Any] = {"start_date": _date(start), "end_date": _date(end),
                                  "revisions": revisions}
        params.update(extra or {})
        return self.get_all(f"/announcements/{_code(currency)}/{_code(indicator, 'indicator')}", params)

    def calendar(self, currency: str, *, indicator: Optional[str] = None,
                 start: Optional[str] = None, end: Optional[str] = None) -> Dict[str, Any]:
        params = {"indicator": _code(indicator, "indicator") if indicator else None,
                  "start_date": _date(start), "end_date": _date(end)}
        return self.get(f"/calendar/{_code(currency)}", params)

    def fx(self, base: str, quote: str, *, start: Optional[str] = None,
           end: Optional[str] = None) -> Dict[str, Any]:
        params = {"start_date": _date(start), "end_date": _date(end)}
        return self.get_all(f"/forex/{_code(base)}/{_code(quote)}", params)


def utc_iso(epoch: Any) -> Optional[str]:
    """Render an epoch-seconds timestamp as ISO-8601 UTC, or None."""
    if isinstance(epoch, bool) or not isinstance(epoch, (int, float)):
        return None
    return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def vintage_rows(rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """One row per retained vintage from a ``revisions=all`` response.

    Each ledger entry keeps its own value and clocks; ``epoch`` is the
    publication timestamp of that vintage and is copied, unchanged, to
    ``announcement_datetime`` so it lines up with the headline rows.
    """
    out: List[Dict[str, Any]] = []
    for row in rows:
        ledger = row.get("revisions")
        if not isinstance(ledger, list) or not ledger:
            flat = {k: v for k, v in row.items() if k != "revisions"}
            flat["vintage_index"] = 0
            out.append(flat)
            continue
        for index, vintage in enumerate(v for v in ledger if isinstance(v, dict)):
            flat = {"date": row.get("date"), "vintage_index": index}
            flat.update(vintage)
            if "epoch" in vintage:
                flat["announcement_datetime"] = vintage["epoch"]
            out.append(flat)
    return out


def known_at(rows: Iterable[Dict[str, Any]], cutoff_epoch: float, *,
             confirmed_only: bool = True) -> Dict[str, Dict[str, Any]]:
    """Latest vintage per reference period that was public at ``cutoff_epoch``.

    ``rows`` are vintage rows (see :func:`vintage_rows`). With
    ``confirmed_only`` a vintage counts only when ``publication_time_status``
    is ``confirmed``; any other status means its timestamp is not evidence of
    when the value became public.
    """
    best: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        stamp = row.get("announcement_datetime")
        if isinstance(stamp, bool) or not isinstance(stamp, (int, float)) or stamp > cutoff_epoch:
            continue
        if confirmed_only and row.get("publication_time_status") != "confirmed":
            continue
        if row.get("val") in (None, ""):
            continue
        period = str(row.get("date"))
        current = best.get(period)
        if current is None or stamp >= current["announcement_datetime"]:
            best[period] = row
    return dict(sorted(best.items()))


def to_csv(rows: Iterable[Dict[str, Any]]) -> str:
    """Flatten rows to CSV. Scalar fields are kept as-is; nested ones become JSON."""
    rows = list(rows)
    columns: List[str] = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
            if key == "announcement_datetime" and "announcement_datetime_utc" not in columns:
                columns.append("announcement_datetime_utc")
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        flat = {}
        for key in columns:
            value = row.get(key)
            if key == "announcement_datetime_utc" and value is None:
                value = utc_iso(row.get("announcement_datetime"))
            flat[key] = json.dumps(value, sort_keys=True) if isinstance(value, (dict, list)) else value
        writer.writerow(flat)
    return buffer.getvalue()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = parser.add_subparsers(dest="command", required=True)

    def output_options(p: argparse.ArgumentParser, default: str) -> None:
        p.add_argument("--format", choices=("csv", "json"), default=default)
        p.add_argument("--out", help="write to this file instead of stdout")

    p = sub.add_parser("catalogue", help="indicators available for a currency")
    p.add_argument("currency")
    output_options(p, "csv")

    p = sub.add_parser("series", help="indicator history with release timestamps")
    p.add_argument("currency")
    p.add_argument("indicator")
    p.add_argument("--start")
    p.add_argument("--end")
    p.add_argument("--revisions", choices=("latest", "first", "final", "all"))
    p.add_argument("--vintages", action="store_true",
                   help="with --revisions all, emit one row per retained vintage")
    p.add_argument("--option", action="append", default=[], metavar="NAME=VALUE",
                   help="extra documented query option, e.g. seasonality=sa or frequency=yoy")
    output_options(p, "csv")

    p = sub.add_parser("calendar", help="scheduled release dates and times")
    p.add_argument("currency")
    p.add_argument("--indicator")
    p.add_argument("--start")
    p.add_argument("--end")
    output_options(p, "json")

    p = sub.add_parser("fx", help="daily FX history (API key required)")
    p.add_argument("base")
    p.add_argument("quote")
    p.add_argument("--start")
    p.add_argument("--end")
    output_options(p, "csv")
    return parser


_ALLOWED_OPTIONS = {"seasonality", "frequency", "annualization", "period_aggregation",
                    "basis", "series_mode"}


def _options(pairs: List[str]) -> Dict[str, str]:
    options = {}
    for pair in pairs:
        name, sep, value = pair.partition("=")
        if not sep or name not in _ALLOWED_OPTIONS or not _SLUG.match(value):
            raise ValueError(f"unsupported --option {pair!r}; allowed: {', '.join(sorted(_ALLOWED_OPTIONS))}")
        options[name] = value
    return options


def run(argv: Optional[List[str]] = None, client: Optional[FXMacroDataClient] = None) -> int:
    args = build_parser().parse_args(argv)
    client = client or FXMacroDataClient()
    try:
        if args.command == "catalogue":
            payload = client.catalogue(args.currency)
            # The catalogue is an object keyed by indicator slug.
            rows = [dict({"indicator": slug}, **entry) for slug, entry in sorted(payload.items())
                    if isinstance(entry, dict)]
        elif args.command == "series":
            if args.vintages and args.revisions != "all":
                raise ValueError("--vintages needs --revisions all")
            payload = client.series(args.currency, args.indicator, start=args.start, end=args.end,
                                    revisions=args.revisions, extra=_options(args.option))
            rows = vintage_rows(payload["data"]) if args.vintages else payload["data"]
        elif args.command == "calendar":
            payload = client.calendar(args.currency, indicator=args.indicator,
                                      start=args.start, end=args.end)
            rows = payload.get("data") or []
        else:
            payload = client.fx(args.base, args.quote, start=args.start, end=args.end)
            rows = payload["data"]
    except (FXMacroDataError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.format == "csv":
        text = to_csv(rows)
    else:
        text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
    else:
        sys.stdout.write(text)
    for notice in dict.fromkeys(client.notices):
        print(f"note: {notice}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(run())
