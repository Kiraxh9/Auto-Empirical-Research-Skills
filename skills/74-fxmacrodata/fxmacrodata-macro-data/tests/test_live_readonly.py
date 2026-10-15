from __future__ import annotations

import os
import unittest

import _support  # noqa: F401
from fxmacrodata_data import FXMacroDataClient


@unittest.skipUnless(os.getenv("AERS_FXMACRODATA_LIVE") == "1", "set AERS_FXMACRODATA_LIVE=1 to call the live API")
class LiveReadOnlyTests(unittest.TestCase):
    def test_keyless_usd_catalogue_lists_core_indicators(self):
        catalogue = FXMacroDataClient(api_key="").catalogue("usd")
        for slug in ("policy_rate", "inflation", "non_farm_payrolls"):
            self.assertIn(slug, catalogue)
            self.assertTrue(catalogue[slug].get("unit"))


if __name__ == "__main__":
    unittest.main()
