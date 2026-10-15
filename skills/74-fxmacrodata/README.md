# FXMacroData Macro Data

Official macro series, release timestamps, revision vintages, release
calendars and daily FX for 22 currencies, pulled into CSV through the
[FXMacroData](https://fxmacrodata.com/?utm_source=github&utm_medium=referral&utm_campaign=auto-empirical-research-skills&utm_content=readme)
REST API.

Open [`fxmacrodata-macro-data/SKILL.md`](fxmacrodata-macro-data/SKILL.md) for
agent instructions. The script and tests are self-contained inside the skill
directory and use only the Python standard library. The skill provides:

- indicator discovery per currency (units, frequency, source agency);
- full-history downloads with publication timestamps on every row;
- revision vintages and a `known_at` helper for real-time samples, gated on
  confirmed publication times;
- the official release calendar for announcement windows;
- offline unit tests and an opt-in live keyless USD check.

USD indicators, the USD calendar and every currency's catalogue work without
an account (90-day history window). Other currencies, full history and FX need
an API key in `FXMACRODATA_API_KEY`; see
[plans](https://fxmacrodata.com/subscribe?utm_source=github&utm_medium=referral&utm_campaign=auto-empirical-research-skills&utm_content=readme_subscribe).
