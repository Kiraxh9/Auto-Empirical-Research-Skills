from __future__ import annotations

import re
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SKILL_FILE = SKILL_ROOT / "SKILL.md"


class SkillContractTests(unittest.TestCase):
    def test_frontmatter_and_commands(self):
        text = SKILL_FILE.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        self.assertRegex(text, r"(?m)^name: fxmacrodata-macro-data$")
        self.assertRegex(text, r"(?m)^description: Use when .+$")
        for command in ("catalogue", "series", "calendar", "fx"):
            self.assertIn(f"scripts/fxmacrodata_data.py {command}", text)
        self.assertIn("FXMACRODATA_API_KEY", text)
        self.assertIn("AERS_FXMACRODATA_LIVE=1", text)

    def test_reference_links_resolve(self):
        text = SKILL_FILE.read_text(encoding="utf-8")
        links = re.findall(r"\]\((references/[^)]+)\)", text)
        self.assertEqual(sorted(set(links)), ["references/endpoints.md", "references/vintages.md"])
        for link in links:
            self.assertTrue((SKILL_ROOT / link).is_file(), link)

    def test_skill_stays_short(self):
        lines = SKILL_FILE.read_text(encoding="utf-8").splitlines()
        self.assertLess(len(lines), 150)


if __name__ == "__main__":
    unittest.main()
