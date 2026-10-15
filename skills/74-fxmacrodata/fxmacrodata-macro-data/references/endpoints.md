# Endpoints

All requests are `GET` against `https://api.fxmacrodata.com/v1`. The script
wraps the four endpoints an empirical project usually needs; the full list is
in the [API reference](https://fxmacrodata.com/documentation/reference?utm_source=github&utm_medium=referral&utm_campaign=auto-empirical-research-skills&utm_content=docs).

Currencies: AUD, BRL, CAD, CHF, CNH, CNY, DKK, EUR, GBP, HUF, ILS, JPY, KRW,
MYR, NGN, NOK, NZD, PEN, SEK, THB, TWD, USD. Paths use lower case (`usd`).

| Script command | Endpoint | Key needed |
|---|---|---|
| `catalogue CUR` | `/data_catalogue/{currency}` | no |
| `series CUR SLUG` | `/announcements/{currency}/{indicator}` | USD: no (90-day window). Others: yes |
| `calendar CUR` | `/calendar/{currency}` | USD: no. Others: yes |
| `fx BASE QUOTE` | `/forex/{base}/{quote}` | yes |

## Catalogue

An object keyed by indicator slug. Each entry carries `name`, `unit`,
`frequency`, `source`, `source_url`, `seasonal_adjustment`,
`source_history_start` and related metadata. The CSV adds an `indicator`
column holding the slug.

## Indicator history

Query parameters: `start_date`, `end_date` (YYYY-MM-DD), `limit` (max 100),
`offset`, `revisions` (`latest` default, `first`, `final`, `all`) and, where
the series supports them, `seasonality` (`sa`, `nsa`), `frequency` (`level`,
`yoy`, `qoq`, `mom`), `annualization`, `period_aggregation`, `basis` (`real`,
`nominal`) and `series_mode` (`raw` default, `canonical`). Unsupported options
return an error naming the supported values; `supported_options` in the
response lists them. Pass them with `--option name=value`.

The envelope carries series metadata (`name`, `source`, `source_url`,
`seasonal_adjustment`, `earliest_available_date`, `latest_available_date`),
`pagination` (`has_more`, `next_offset`, `total_count`) and `data`, newest
first. The script follows pagination until `has_more` is false and refuses a
page sequence that does not advance.

Row fields used most:

| Field | Meaning |
|---|---|
| `date` | Reference period |
| `val` | Value in the series unit |
| `announcement_datetime` | Publication time, Unix seconds UTC |
| `publication_time_status` | `confirmed`, `unverified`, `assumed_historical` or `unknown` |
| `publication_time_precision` | `minute`, `day` or `unknown` |
| `release_time_assumed` | True when the time was derived from the series' measured lag |
| `vintage_status`, `is_first_release` | Vintage provenance |
| `revisions` | With `revisions=all`: the retained vintages, each with `epoch`, `val` and its own timing fields |

`freemium_window` appears when keyless access shortened the history;
`freemium_delay` when the newest release is held back. The script reports both
on stderr.

## Release calendar

Optional `indicator`, `start_date`, `end_date` and `timezone` (IANA name).
Rows carry `announcement_datetime` (Unix seconds), `announcement_datetime_utc`,
`release`, `name`, `release_date_confirmed` and `release_time_status`.
Upcoming dates come from the agencies' published release schedules.

## FX

`start_date`, `end_date`, paginated like indicator history. Rows carry `date`
and `val` (the base/quote rate), plus OHLC fields where available.
