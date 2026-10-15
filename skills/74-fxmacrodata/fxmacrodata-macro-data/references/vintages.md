# Release timestamps and vintages

Macro data is revised. A regression on today's GDP or payroll history uses
numbers nobody had at the time, which biases surprise, Taylor-rule and
event-study estimates. Build real-time samples from vintages, not from the
latest view.

## Two clocks per row

- `date`: the reference period the value describes (March CPI is
  `2026-03-01` or the period end, depending on the series).
- `announcement_datetime`: when that value was published, Unix seconds UTC.
  In a vintage ledger the same instant is called `epoch`.

Never use `date` as the availability date.

## How much to trust a timestamp

`publication_time_status` says what `announcement_datetime` is, row by row:

| Status | Meaning | Point-in-time use |
|---|---|---|
| `confirmed` | Read from the publisher's own release or timestamp | Yes |
| `unverified` | A real timestamp whose origin this row does not evidence; most older rows | Only as a labelled robustness check |
| `assumed_historical` | Derived from the series' measured publication lag (`release_time_assumed` is true) | Only as a labelled robustness check |
| `unknown` | No publication time; `announcement_datetime` is null | No |

`publication_time_precision` is `minute` when the publisher gave a clock time
and `day` when only the release date is known. With `day` precision, do not
place the release inside an intraday window.

## Downloading vintages

```bash
python scripts/fxmacrodata_data.py series usd non_farm_payrolls --revisions all --vintages --out nfp_vintages.csv
```

`--vintages` writes one row per retained vintage: `date`, `vintage_index`,
`val`, `announcement_datetime` (copied from the vintage `epoch`), and that
vintage's own `publication_time_status`, `vintage_status` and
`is_first_release`. `revisions=first` and `revisions=final` return a single
value per period when you only need the first print or the latest settled one.

## Selecting what was known at a date

`known_at` in the script returns, for every reference period, the latest
vintage published at or before a cutoff, counting only `confirmed` timestamps
by default:

```python
import csv, sys
sys.path.insert(0, "scripts")
from fxmacrodata_data import known_at

with open("nfp_vintages.csv", encoding="utf-8") as handle:
    rows = []
    for row in csv.DictReader(handle):
        if row["announcement_datetime"]:
            row["announcement_datetime"] = int(row["announcement_datetime"])
        rows.append(row)

cutoff = 1767225600  # 2026-01-01T00:00:00Z
snapshot = known_at(rows, cutoff)
```

Report how many periods were excluded for unconfirmed timing. If the excluded
share is large for your window, say so; do not switch the gate off silently.

## Surprises

The release calendar gives scheduled times for event windows. Measure an event
from the actual `announcement_datetime` of the confirmed vintage, not from the
scheduled time, when the two differ.
