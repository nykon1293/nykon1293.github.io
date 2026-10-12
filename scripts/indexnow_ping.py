#!/usr/bin/env python3
"""Submit changed public URLs (or the sitemap) to IndexNow for gemmisi.com.

Finds the 32-hex key file at the repo root, maps git-changed HTML to
https://gemmisi.com/ URLs, and POSTs to https://api.indexnow.org/indexnow.

    python3 scripts/indexnow_ping.py              # changed files, else sitemap
    python3 scripts/indexnow_ping.py --all        # every sitemap URL
    python3 scripts/indexnow_ping.py --dry-run    # print payload, do not POST
    python3 scripts/indexnow_ping.py --check      # verify the key file only
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOST = "gemmisi.com"
BASE = f"https://{HOST}"
ENDPOINT = "https://api.indexnow.org/indexnow"
SITEMAP = ROOT / "sitemap.xml"
KEY_NAME = re.compile(r"^[0-9a-f]{32}$")
ZERO_SHA = "0" * 40

SKIP_PREFIXES = (
    "chatbot/",
    "sofer-preview/",
    "scripts/",
    "data/",
    "docs/",
    ".github/",
    ".cursor/",
    "assets/",
)
SKIP_FILES = {
    "404.html",
    "PRODUCT.md",
    "README.md",
    "llms.txt",
    "robots.txt",
    "sitemap.xml",
    "site.webmanifest",
    "favicon.ico",
    "_config.yml",
}


def discover_key() -> tuple[str, Path]:
    matches = [
        path
        for path in ROOT.glob("*.txt")
        if KEY_NAME.fullmatch(path.stem)
    ]
    if len(matches) != 1:
        names = ", ".join(path.name for path in matches) or "none"
        raise SystemExit(f"expected one 32-hex IndexNow key file at repo root, found {names}")
    path = matches[0]
    key = path.read_text(encoding="utf-8").strip()
    if key != path.stem:
        raise SystemExit(f"{path.name} must contain its own 32-hex filename as the key")
    return key, path


def sitemap_urls() -> list[str]:
    text = SITEMAP.read_text(encoding="utf-8")
    urls = re.findall(r"<loc>(https://gemmisi\.com/[^<]*)</loc>", text)
    if not urls:
        raise SystemExit("sitemap.xml has no gemmisi.com URLs")
    return list(dict.fromkeys(urls))


def file_to_url(rel: str) -> str | None:
    rel = rel.replace("\\", "/").lstrip("./")
    if not rel or rel.startswith(SKIP_PREFIXES) or Path(rel).name in SKIP_FILES:
        return None
    if KEY_NAME.fullmatch(Path(rel).stem) and rel.endswith(".txt"):
        return None
    if re.fullmatch(r"google[0-9a-f]+\.html", Path(rel).name):
        return None
    if rel == "index.html":
        return f"{BASE}/"
    if rel.endswith("/index.html"):
        return f"{BASE}/{rel[: -len('index.html')]}"
    if rel.endswith(".html"):
        return f"{BASE}/{rel}"
    return None


def git_changed_files(before: str, after: str) -> list[str]:
    if not before or before == ZERO_SHA:
        return []
    result = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACDMRT", before, after or "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        fallback = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=ACDMRT", "HEAD~1", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if fallback.returncode != 0:
            return []
        result = fallback
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def urls_from_files(files: list[str]) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    for rel in files:
        url = file_to_url(rel)
        if url and url not in seen and not url.startswith(f"{BASE}/chatbot/"):
            seen.add(url)
            urls.append(url)
    return urls


def post_indexnow(payload: dict) -> int:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        ENDPOINT,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.getcode()
    except urllib.error.HTTPError as exc:
        return exc.code


def main() -> None:
    parser = argparse.ArgumentParser(description="Ping IndexNow for gemmisi.com")
    parser.add_argument("--all", action="store_true", help="submit every sitemap URL")
    parser.add_argument("--dry-run", action="store_true", help="print the payload and exit")
    parser.add_argument("--check", action="store_true", help="verify the key file and exit")
    args = parser.parse_args()

    key, key_path = discover_key()
    key_location = f"{BASE}/{key_path.name}"
    if args.check:
        print(f"key {key_path.name}")
        print(f"keyLocation {key_location}")
        print(f"sitemap {len(sitemap_urls())} urls")
        return

    before = os.environ.get("INDEXNOW_BEFORE", "").strip()
    after = os.environ.get("INDEXNOW_AFTER", "").strip()
    if args.all:
        urls = sitemap_urls()
        source = "sitemap"
    else:
        files = git_changed_files(before, after)
        urls = urls_from_files(files)
        source = "changed files"
        if not urls:
            urls = sitemap_urls()
            source = "sitemap fallback"

    payload = {
        "host": HOST,
        "key": key,
        "keyLocation": key_location,
        "urlList": urls,
    }
    print(f"source={source} urls={len(urls)} keyLocation={key_location}")
    if args.dry_run:
        preview = dict(payload)
        preview["urlList"] = urls[:8] + (["…"] if len(urls) > 8 else [])
        print(json.dumps(preview, indent=2, ensure_ascii=False))
        return

    status = post_indexnow(payload)
    if status == 429:
        time.sleep(5)
        status = post_indexnow(payload)
    if status not in (200, 202):
        raise SystemExit(f"IndexNow returned HTTP {status} for {len(urls)} URLs")
    print(f"IndexNow accepted {len(urls)} URLs (HTTP {status})")


if __name__ == "__main__":
    main()
