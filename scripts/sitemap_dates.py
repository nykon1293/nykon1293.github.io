#!/usr/bin/env python3
"""Stable sitemap lastmod dates from git history of source content.

Generated HTML is rebuilt often (nav chrome, library counts). lastmod follows
the JSON / taxonomy / unique-page source instead of today's date. Directory
index.html href rewrites are treated as chrome, not content.
"""
from __future__ import annotations

import json
import subprocess
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://gemmisi.com"
USE_CASES_JSON = "data/use-cases.json"
TAXONOMY_JSON = "data/taxonomy.json"

UNIQUE_HTML = {
    f"{BASE}/": "index.html",
    f"{BASE}/pricing.html": "pricing.html",
    f"{BASE}/advisory.html": "advisory.html",
    f"{BASE}/services/hermes-agents.html": "services/hermes-agents.html",
    f"{BASE}/services/ai-automation.html": "services/ai-automation.html",
    f"{BASE}/services/dashboards-reporting.html": "services/dashboards-reporting.html",
    f"{BASE}/services/ecommerce-operations.html": "services/ecommerce-operations.html",
    f"{BASE}/services/tutoring-project-help.html": "services/tutoring-project-help.html",
    f"{BASE}/services/stocky-recovery.html": "services/stocky-recovery.html",
    f"{BASE}/work/governed-ai-content-engine.html": "work/governed-ai-content-engine.html",
}


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def git_log_commits(rel_path: str) -> list[tuple[str, str]]:
    """Oldest-first (hash, YYYY-MM-DD) commits that touched rel_path."""
    result = _git("log", "--reverse", "--format=%H %cs", "--", rel_path)
    rows: list[tuple[str, str]] = []
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2:
            rows.append((parts[0], parts[1]))
    return rows


def git_show(sha: str, rel_path: str) -> str | None:
    result = _git("show", f"{sha}:{rel_path}")
    if result.returncode != 0:
        return None
    return result.stdout


def _dump(value: object) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)


def max_date(*values: str | None) -> str:
    dates = [item for item in values if item]
    if not dates:
        return date.today().isoformat()
    return max(dates)


def json_keyed_dates(rel_path: str, extract) -> dict[str, str]:
    """Last commit date each extracted object actually changed."""
    last_dump: dict[str, str] = {}
    dates: dict[str, str] = {}
    for sha, cs in git_log_commits(rel_path):
        text = git_show(sha, rel_path)
        if text is None:
            continue
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            continue
        snapshot = extract(data)
        for key, obj in snapshot.items():
            dumped = _dump(obj)
            if last_dump.get(key) != dumped:
                dates[key] = cs
                last_dump[key] = dumped
    path = ROOT / rel_path
    current: set[str] = set()
    if path.is_file():
        snapshot = extract(json.loads(path.read_text(encoding="utf-8")))
        current = set(snapshot)
        today = date.today().isoformat()
        for key, obj in snapshot.items():
            dumped = _dump(obj)
            if last_dump.get(key) != dumped:
                dates[key] = today
                last_dump[key] = dumped
            elif key not in dates:
                dates[key] = today
    if current:
        return {key: dates[key] for key in current if key in dates}
    return dates


def extract_use_cases(data: object) -> dict[str, object]:
    if not isinstance(data, list):
        return {}
    return {item["slug"]: item for item in data if isinstance(item, dict) and item.get("slug")}


def extract_taxonomy(data: object) -> dict[str, object]:
    if not isinstance(data, dict):
        return {}
    out: dict[str, object] = {}
    for group in ("industries", "functions", "hobbies"):
        block = data.get(group) or {}
        if isinstance(block, dict):
            for slug, info in block.items():
                out[f"{group}:{slug}"] = info
    if data.get("hobbies_hub") is not None:
        out["hobbies_hub"] = data["hobbies_hub"]
    for kit in data.get("kits") or []:
        if isinstance(kit, dict) and kit.get("slug"):
            out[f"kits:{kit['slug']}"] = kit
    return out


def html_source_lastmod(rel_path: str, public_url: str) -> str:
    """Last date the unique page's public content changed, ignoring index.html hrefs."""
    from indexnow_ping import page_content_fingerprint

    last = None
    prev = None
    for sha, cs in git_log_commits(rel_path):
        text = git_show(sha, rel_path)
        if text is None:
            continue
        fp = page_content_fingerprint(text, base_url=public_url)
        if fp != prev:
            last = cs
            prev = fp
    path = ROOT / rel_path
    if path.is_file():
        fp = page_content_fingerprint(path.read_text(encoding="utf-8"), base_url=public_url)
        if fp != prev:
            last = date.today().isoformat()
    return last or date.today().isoformat()


class LastmodIndex:
    def __init__(self, entries: list[dict]):
        self.entries = entries
        self.entry_dates = json_keyed_dates(USE_CASES_JSON, extract_use_cases)
        self.tax_dates = json_keyed_dates(TAXONOMY_JSON, extract_taxonomy)
        self._html_cache: dict[str, str] = {}

    def entry(self, slug: str) -> str:
        return self.entry_dates.get(slug) or date.today().isoformat()

    def tax(self, key: str) -> str | None:
        return self.tax_dates.get(key)

    def unique_html(self, loc: str) -> str:
        if loc not in self._html_cache:
            rel = UNIQUE_HTML[loc]
            self._html_cache[loc] = html_source_lastmod(rel, loc)
        return self._html_cache[loc]

    def matching_entry_dates(self, slugs: list[str]) -> list[str]:
        return [self.entry(slug) for slug in slugs]

    def for_url(
        self,
        loc: str,
        *,
        industry_slug: str | None = None,
        function_slug: str | None = None,
        hobby_slug: str | None = None,
        kit_slug: str | None = None,
        use_case_slug: str | None = None,
        member_slugs: list[str] | None = None,
        tax_keys: list[str] | None = None,
    ) -> str:
        if loc in UNIQUE_HTML:
            return self.unique_html(loc)
        dates: list[str | None] = []
        if use_case_slug:
            dates.append(self.entry(use_case_slug))
        if industry_slug:
            dates.append(self.tax(f"industries:{industry_slug}"))
        if function_slug:
            dates.append(self.tax(f"functions:{function_slug}"))
        if hobby_slug:
            dates.append(self.tax(f"hobbies:{hobby_slug}"))
        if kit_slug:
            dates.append(self.tax(f"kits:{kit_slug}"))
        for key in tax_keys or []:
            dates.append(self.tax(key))
        dates.extend(self.matching_entry_dates(member_slugs or []))
        return max_date(*dates)
