from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlsplit


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


class RecordingOpener:
    """Replays canned responses keyed by path and records every request."""

    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def __call__(self, url, headers, timeout):
        parts = urlsplit(url)
        query = {k: v[0] for k, v in parse_qs(parts.query).items()}
        self.calls.append({"url": url, "path": parts.path, "query": query, "headers": dict(headers)})
        route = self.routes[parts.path]
        status, body = route(query) if callable(route) else route
        return status, json.dumps(body).encode("utf-8")
