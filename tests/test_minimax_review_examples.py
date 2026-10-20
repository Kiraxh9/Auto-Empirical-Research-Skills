"""Exercise the vendored review skills' actual curl request examples offline."""

from __future__ import annotations

import json
import os
import re
import subprocess
import unittest

from _helpers import ROOT


SKILLS = ROOT / "skills/42-wanshuiyin-ARIS/skills"
VARIANTS = (SKILLS, SKILLS / "skills-codex")
FLASH = "MiniMax-M3.1-Flash"


def capture_request(command, **settings):
    # A shell function intercepts curl after Bash has serialized its arguments.
    # No server is started, no network is used, and no real credentials enter.
    completed = subprocess.run(
        ["bash", "--noprofile", "--norc", "-c",
         "curl() { printf '%s\\0' \"$@\"; };\n" + command],
        env={"PATH": os.defpath, "MINIMAX_API_KEY": "offline-test-key",
             "LLM_API_KEY": "offline-test-key", **settings},
        capture_output=True,
        check=True,
        timeout=10,
    )
    args = completed.stdout.decode().rstrip("\0").split("\0")
    return args, json.loads(args[args.index("-d") + 1])


class TestMiniMaxReviewExamples(unittest.TestCase):
    def test_all_curl_requests_use_flash_and_compatible_defaults(self):
        for variant in VARIANTS:
            text = (variant / "auto-review-loop-minimax/SKILL.md").read_text()
            examples = re.findall(r"```bash\n(curl .*?)\n```", text, re.DOTALL)
            self.assertEqual(len(examples), 3)
            for index, command in enumerate(examples):
                with self.subTest(variant=variant.name, example=index):
                    args, payload = capture_request(command)
                    self.assertIn("https://api.minimax.io/v1/chat/completions", args)
                    self.assertIn("Authorization: Bearer offline-test-key", args)
                    self.assertEqual(payload["model"], FLASH)
                    self.assertEqual(payload["max_tokens"], 4096)
                    self.assertEqual(set(payload), {"model", "messages", "max_tokens"})
                    self.assertEqual([m["role"] for m in payload["messages"]],
                                     ["system", "user"])
                    self.assertTrue(all(m["content"] for m in payload["messages"]))
                    if index == 2:
                        self.assertIn("Previous Review Summary", payload["messages"][1]["content"])

    def test_review_override_preserves_saved_legacy_and_custom_ids(self):
        for variant in VARIANTS:
            text = (variant / "auto-review-loop-minimax/SKILL.md").read_text()
            examples = re.findall(r"```bash\n(curl .*?)\n```", text, re.DOTALL)
            for command in examples:
                _, default = capture_request(command)
                for model in ("", "MiniMax-M3", "MiniMax-M2.7", 'custom/"quoted"\\model\'$(false)'):
                    with self.subTest(variant=variant.name, model=model):
                        _, payload = capture_request(command, REVIEWER_MODEL=model)
                        self.assertEqual(payload, dict(default, model=model or FLASH))

    def test_generic_requests_serialize_the_configured_model_and_endpoint(self):
        for variant in VARIANTS:
            text = (variant / "auto-review-loop-llm/SKILL.md").read_text()
            examples = re.findall(r"```bash\n(curl .*?)\n```", text, re.DOTALL)
            self.assertEqual(len(examples), 2)
            for command in examples:
                for base in ("https://api.minimax.io/v1", "https://api.minimax.cn/v1",
                             "https://custom.invalid/v1"):
                    for model in (FLASH, "MiniMax-M3", "MiniMax-M2.7", 'custom/"quoted"\\model\'$(false)'):
                        with self.subTest(variant=variant.name, base=base, model=model):
                            args, payload = capture_request(command, LLM_BASE_URL=base, LLM_MODEL=model)
                            self.assertIn(base + "/chat/completions", args)
                            self.assertEqual(payload["model"], model)
                            self.assertEqual(payload["max_tokens"], 4096)
                            self.assertEqual(set(payload), {"model", "messages", "max_tokens"})
                            self.assertEqual([m["role"] for m in payload["messages"]],
                                             ["system", "user"])

    def test_mcp_examples_match_default_without_changing_port_arguments(self):
        for variant in VARIANTS:
            text = (variant / "auto-review-loop-minimax/SKILL.md").read_text()
            models = re.findall(r'^\s*(?:- )?model: "([^"]+)"', text, re.MULTILINE)
            self.assertEqual(models, [FLASH] * 3)
            argument = "message" if variant.name == "skills-codex" else "prompt"
            self.assertIn(f"  {argument}: |", text)
            self.assertIn("configured/custom model ID", text)
            self.assertIn("model recorded in a resumed review", text)
            self.assertIn("substitute the selected REVIEWER_MODEL", text)

    def test_provider_tables_offer_current_models_and_preserve_configuration(self):
        for variant in VARIANTS:
            text = (variant / "auto-review-loop-llm/SKILL.md").read_text()
            row = next(line for line in text.splitlines() if line.startswith("| **MiniMax**"))
            self.assertEqual(re.findall(r"`([^`]+)`", row),
                             ["https://api.minimax.io/v1", FLASH, "MiniMax-M3"])
            self.assertIn("Keep an existing `LLM_MODEL`", text)
            self.assertIn("custom model unchanged", text)


if __name__ == "__main__":
    unittest.main()
