#!/usr/bin/env python3
"""Submit changed public URLs (or the sitemap) to IndexNow for gemmisi.com.

Uses ACTIVE_KEY (the 32-hex `{key}.txt` at the repo root). Older key files
may stay on disk so prior verifications do not 404. Maps git-changed HTML to
https://gemmisi.com/ URLs, waits until the live key URL returns that key,
then POSTs to each IndexNow engine.

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
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
HOST = "gemmisi.com"
BASE = f"https://{HOST}"
SITEMAP = ROOT / "sitemap.xml"
KEY_NAME = re.compile(r"^[0-9a-f]{32}$")
# Bing latched 403 UserForbiddedToAccessSite on 23c3690d323f2e5687c21ef152e1cd87.
# Keep that file at the site root; submit with this key only.
ACTIVE_KEY = "f702ca108ee22cc8602abd433bed3cf5"
ZERO_SHA = "0" * 40
USER_AGENT = "gemmisi-indexnow/1.0 (+https://gemmisi.com/)"

OK_STATUSES = {200, 202}
RETRY_STATUSES = {403, 429}
RETRY_DELAYS = (5, 15)
KEY_FETCH_DELAYS = (2, 5, 10, 20, 30)

# Bing operates api.indexnow.org and www.bing.com; Seznam and Naver verify
# independently. Submit to each so a Bing-only 403 does not drop the ping.
ENGINES: tuple[tuple[str, str], ...] = (
    ("api.indexnow.org", "https://api.indexnow.org/indexnow"),
    ("bing.com", "https://www.bing.com/indexnow"),
    ("seznam.cz", "https://search.seznam.cz/indexnow"),
    ("naver.com", "https://searchadvisor.naver.com/indexnow"),
)

SKIP_PREFIXES = (
    "chatbot/",
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
def tracking_slugs() -> set[str]:
    """Campaign short links are noindex and must not be submitted to IndexNow."""
    try:
        import build_tracking_links as tracking
    except ImportError:
        return set()
    return tracking.tracking_slug_set()

SleepFn = Callable[[float], None]


def discover_key() -> tuple[str, Path]:
    matches = [
        path
        for path in ROOT.glob("*.txt")
        if KEY_NAME.fullmatch(path.stem)
    ]
    path = next((item for item in matches if item.stem == ACTIVE_KEY), None)
    if path is None:
        names = ", ".join(item.name for item in matches) or "none"
        raise SystemExit(f"active IndexNow key {ACTIVE_KEY}.txt missing at repo root (found {names})")
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
    parts = rel.split("/")
    if len(parts) == 2 and parts[1] == "index.html" and parts[0] in tracking_slugs():
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


def _headers() -> dict[str, str]:
    return {
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": USER_AGENT,
    }


def summarize_body(body: str) -> str:
    text = body.strip()
    if not text:
        return ""
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return " ".join(text.split())[:200]
    if not isinstance(data, dict):
        return " ".join(text.split())[:200]
    parts = [str(data[key]) for key in ("errorCode", "message") if data.get(key)]
    return " — ".join(parts) if parts else " ".join(text.split())[:200]


def fetch_url(url: str, timeout: int = 30) -> tuple[int, str]:
    request = urllib.request.Request(
        url,
        method="GET",
        headers={"User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", "replace")
            return response.getcode() or 0, body
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        return exc.code, body
    except urllib.error.URLError as exc:
        return 0, str(exc.reason if getattr(exc, "reason", None) else exc)


def wait_for_live_key(
    key: str,
    key_location: str,
    delays: tuple[int, ...] = KEY_FETCH_DELAYS,
    sleep: SleepFn = time.sleep,
) -> None:
    """GET the public key URL until it returns HTTP 200 and the key body."""
    attempts = len(delays) + 1
    last_detail = "not fetched"
    for attempt in range(1, attempts + 1):
        status, body = fetch_url(key_location)
        got = body.strip()
        if status == 200 and got == key:
            print(f"key URL live HTTP {status} {key_location}", flush=True)
            return
        last_detail = f"HTTP {status}"
        if status == 200 and got != key:
            last_detail = f"HTTP {status} unexpected body {got[:80]!r}"
        elif not status:
            last_detail = body or "request failed"
        print(
            f"key URL not ready ({last_detail}), attempt {attempt}/{attempts}",
            flush=True,
        )
        if attempt <= len(delays):
            sleep(delays[attempt - 1])
    raise SystemExit(
        f"key URL {key_location} did not return the expected key ({last_detail})"
    )


def post_indexnow(endpoint: str, payload: dict) -> tuple[int, str]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=body,
        method="POST",
        headers=_headers(),
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            text = response.read().decode("utf-8", "replace")
            return response.getcode() or 0, text
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", "replace")
        return exc.code, text
    except urllib.error.URLError as exc:
        return 0, str(exc.reason if getattr(exc, "reason", None) else exc)


def warn(message: str) -> None:
    print(f"::warning::{message}", flush=True)
    print(f"warning: {message}", file=sys.stderr, flush=True)


def submit_to_engines(
    payload: dict,
    engines: tuple[tuple[str, str], ...] = ENGINES,
    retry_delays: tuple[int, ...] = RETRY_DELAYS,
    sleep: SleepFn = time.sleep,
) -> tuple[list[tuple[str, int]], list[tuple[str, int, str]]]:
    """POST to every engine. Retry 403/429 together with backoff.

    Returns (accepted, rejected) where accepted is (name, status) and
    rejected is (name, status, detail).
    """
    pending = list(engines)
    accepted: list[tuple[str, int]] = []
    rejected: list[tuple[str, int, str]] = []
    attempts = len(retry_delays) + 1

    for attempt in range(1, attempts + 1):
        still: list[tuple[str, str]] = []
        for name, endpoint in pending:
            status, body = post_indexnow(endpoint, payload)
            detail = summarize_body(body)
            label = f"{name} HTTP {status}" + (f" {detail}" if detail else "")
            if status in OK_STATUSES:
                print(f"ok: {label}", flush=True)
                accepted.append((name, status))
                continue
            retryable = status in RETRY_STATUSES or status == 0
            if retryable and attempt < attempts:
                print(
                    f"{label}, retrying after {retry_delays[attempt - 1]}s "
                    f"(attempt {attempt}/{attempts})",
                    flush=True,
                )
                still.append((name, endpoint))
                continue
            rejected.append((name, status, detail))
            warn(f"IndexNow {label} for {len(payload.get('urlList', []))} URLs")

        pending = still
        if not pending:
            break
        sleep(retry_delays[attempt - 1])

    return accepted, rejected


def resolve_urls(all_urls: bool) -> tuple[list[str], str]:
    before = os.environ.get("INDEXNOW_BEFORE", "").strip()
    after = os.environ.get("INDEXNOW_AFTER", "").strip()
    if all_urls:
        return sitemap_urls(), "sitemap"
    if not before:
        parent = subprocess.run(
            ["git", "rev-parse", "HEAD~1"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if parent.returncode == 0:
            before = parent.stdout.strip()
    files = git_changed_files(before, after)
    urls = urls_from_files(files)
    if urls:
        return urls, "changed files"
    return sitemap_urls(), "sitemap fallback"


def main() -> None:
    parser = argparse.ArgumentParser(description="Ping IndexNow for gemmisi.com")
    parser.add_argument("--all", action="store_true", help="submit every sitemap URL")
    parser.add_argument("--dry-run", action="store_true", help="print the payload and exit")
    parser.add_argument("--check", action="store_true", help="verify the key file and exit")
    args = parser.parse_args()

    key, key_path = discover_key()
    key_location = f"{BASE}/{key_path.name}"
    if args.check:
        print(f"key {key_path.name}", flush=True)
        print(f"keyLocation {key_location}", flush=True)
        print(f"sitemap {len(sitemap_urls())} urls", flush=True)
        print(f"engines {', '.join(name for name, _ in ENGINES)}", flush=True)
        return

    urls, source = resolve_urls(args.all)
    payload = {
        "host": HOST,
        "key": key,
        "keyLocation": key_location,
        "urlList": urls,
    }
    print(f"source={source} urls={len(urls)} keyLocation={key_location}", flush=True)
    if args.dry_run:
        preview = dict(payload)
        preview["urlList"] = urls[:8] + (["…"] if len(urls) > 8 else [])
        print(json.dumps(preview, indent=2, ensure_ascii=False), flush=True)
        return

    wait_for_live_key(key, key_location)
    accepted, rejected = submit_to_engines(payload)
    if not accepted:
        details = ", ".join(
            f"{name} HTTP {status}" + (f" {detail}" if detail else "")
            for name, status, detail in rejected
        )
        raise SystemExit(
            f"IndexNow rejected by every engine for {len(urls)} URLs: {details}"
        )
    engine_names = ", ".join(name for name, _ in accepted)
    print(
        f"IndexNow accepted {len(urls)} URLs via {engine_names} "
        f"({len(accepted)}/{len(ENGINES)} engines)",
        flush=True,
    )


if __name__ == "__main__":
    main()
