---
name: fxmacrodata-macro-data
description: Use when an empirical macro, monetary or international-finance project needs official-source series (policy rates, CPI, GDP, payrolls, unemployment, bond yields), their release timestamps and revision vintages, the official release calendar, or daily FX rates for 22 currencies, pulled reproducibly into CSV through the FXMacroData REST API.
---

# FXMacroData Macro Data

Pull official macro series, release timing and FX into analysis-ready files
with `scripts/fxmacrodata_data.py` (standard library only). Values come from
central banks and statistics agencies; each row keeps its source fields,
including when it was published.

## Access

- USD indicators, the USD release calendar and every currency's catalogue work
  without an account. Keyless history covers a rolling 90-day window and the
  newest release appears after a short delay; the script prints a `note:` line
  when either applies, so a truncated sample is never silent.
- Other currencies, full history and FX need an API key in
  `FXMACRODATA_API_KEY`. The script sends it as a header. Never put it in a
  command, notebook, file or log.

## Workflow

1. Find the indicator slug for the currency. Slugs differ by country
   (`policy_rate`, `inflation`, `core_inflation`, `gdp`, `non_farm_payrolls`,
   `unemployment`, `gov_bond_10y`, ...):

   ```bash
   python scripts/fxmacrodata_data.py catalogue usd --out usd_catalogue.csv
   ```

   Check `unit`, `frequency`, `seasonal_adjustment` and `source` before using a
   series, and before combining series across countries.

2. Download the history. Rows are reference periods (`date`) with the value
   (`val`) and the publication timestamp (`announcement_datetime`, Unix
   seconds; the CSV adds `announcement_datetime_utc`):

   ```bash
   python scripts/fxmacrodata_data.py series usd policy_rate --start 2000-01-01 --out fed_funds.csv
   python scripts/fxmacrodata_data.py series eur inflation --option frequency=yoy --out hicp.csv
   ```

3. For real-time or event-study designs, download the vintages and keep only
   what was public at each decision date:

   ```bash
   python scripts/fxmacrodata_data.py series usd non_farm_payrolls --revisions all --vintages --out nfp_vintages.csv
   ```

   Gate on `publication_time_status == "confirmed"` per row. Read
   [references/vintages.md](references/vintages.md) before building any
   point-in-time sample.

4. Release dates and times for announcement windows:

   ```bash
   python scripts/fxmacrodata_data.py calendar usd --indicator inflation --start 2026-01-01
   ```

5. Daily FX (key required):

   ```bash
   python scripts/fxmacrodata_data.py fx eur usd --start 2015-01-01 --out eurusd.csv
   ```

6. Record the exact commands, the download date and the slugs in the
   replication package. Report gaps and keyless truncation as they are; do
   not fill missing periods or infer unpublished values.

## Rules

- Use the documented slugs and field names as returned. The CSV flattens rows
  but never renames, rescales or seasonally adjusts a value.
- `date` is the economic reference period, not the day the number was known.
  Use `announcement_datetime` (or a vintage's `epoch`) for availability.
- Only `publication_time_status == "confirmed"` timestamps are evidence of
  when a value became public. Treat other statuses as unknown timing.
- FX rows are reference rates, not executable quotes.
- Request failures exit with code 2 and a message on stderr. HTTP 401/403
  means the request needs a key; it is not missing data.

## References

- Endpoints, parameters and fields: [references/endpoints.md](references/endpoints.md)
- Release timestamps, vintages and point-in-time samples: [references/vintages.md](references/vintages.md)

Tests run offline against recorded response shapes:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

`AERS_FXMACRODATA_LIVE=1` additionally runs one keyless USD request.
