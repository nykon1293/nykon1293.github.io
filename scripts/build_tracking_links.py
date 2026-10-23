#!/usr/bin/env python3
"""Generate noindex Cloudflare-tracked short-link pages at the site root.

Cloudflare Web Analytics ignores query strings, so each social post gets a
real path such as /fb1101 or /li1025. GitHub Pages serves <slug>/index.html
at /<slug>/ and 301s /<slug> there. Each page loads the same JS beacon as
the rest of the site, waits ~300ms, then forwards to that post's destination.

Source of truth: data/tracking-links.json

    python3 scripts/build_tracking_links.py           # write pages
    python3 scripts/build_tracking_links.py --check   # verify committed output
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "tracking-links.json"
MARKER = "gemmisi-tracking-link"
SLUG_RE = re.compile(r"^[a-z0-9]+(?:[a-z0-9-]*[a-z0-9])?$")
DATE_RE = re.compile(r"^\d{4}$")
PATH_RE = re.compile(r"^/(?:[a-z0-9]+(?:-[a-z0-9]+)*/)*$")
BASE = "https://gemmisi.com"
CHANNELS = ("fb", "li")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seo_schema import CLOUDFLARE_WEB_ANALYTICS  # noqa: E402


def load_config() -> dict:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit("data/tracking-links.json must be an object")
    return data


def absolute_url(path: str) -> str:
    if not isinstance(path, str) or not PATH_RE.fullmatch(path):
        raise SystemExit(f"invalid tracking destination path: {path!r}")
    return BASE + path


def local_page_for_path(path: str) -> Path:
    if path == "/":
        return ROOT / "index.html"
    return ROOT / path.strip("/") / "index.html"


def assert_real_destination(path: str) -> None:
    page = local_page_for_path(path)
    rel = page.relative_to(ROOT).as_posix()
    if not page.is_file():
        raise SystemExit(f"destination {path} has no local file {rel}")
    html = page.read_text(encoding="utf-8")
    if MARKER in html:
        raise SystemExit(f"destination {path} must not be a tracking short link")
    if 'http-equiv="refresh"' in html and "noindex" in html:
        raise SystemExit(
            f"destination {path} is a moved stub ({rel}); use the merged live page"
        )


def load_links() -> list[tuple[str, str]]:
    cfg = load_config()
    posts = cfg.get("posts")
    generic = cfg.get("generic")
    if not isinstance(posts, dict) or not isinstance(generic, dict):
        raise SystemExit("data/tracking-links.json needs posts and generic objects")

    links: list[tuple[str, str]] = []
    seen: set[str] = set()

    def add(slug: str, path: str) -> None:
        if not SLUG_RE.fullmatch(slug):
            raise SystemExit(f"invalid tracking slug: {slug!r}")
        if slug in seen:
            raise SystemExit(f"duplicate tracking slug: {slug}")
        assert_real_destination(path)
        seen.add(slug)
        links.append((slug, absolute_url(path)))

    for date, path in posts.items():
        if not isinstance(date, str) or not DATE_RE.fullmatch(date):
            raise SystemExit(f"invalid post date key: {date!r}")
        if not isinstance(path, str):
            raise SystemExit(f"post {date} destination must be a path string")
        for channel in CHANNELS:
            add(f"{channel}{date}", path)

    for slug, path in generic.items():
        if not isinstance(slug, str) or not isinstance(path, str):
            raise SystemExit(f"invalid generic tracking entry: {slug!r}")
        add(slug, path)

    if not links:
        raise SystemExit("data/tracking-links.json produced no tracking slugs")
    return links


def load_slugs() -> list[str]:
    return [slug for slug, _dest in load_links()]


def tracking_slug_set() -> set[str]:
    try:
        return set(load_slugs())
    except SystemExit:
        return set()


def is_tracking_rel(rel: str) -> bool:
    rel = rel.replace("\\", "/").lstrip("./")
    parts = rel.split("/")
    slugs = tracking_slug_set()
    if len(parts) == 2 and parts[1] == "index.html":
        return parts[0] in slugs
    return False


def reserved_names(slugs: set[str]) -> set[str]:
    names: set[str] = set()
    for path in ROOT.iterdir():
        name = path.name
        if name.startswith("."):
            continue
        if path.is_dir() and name in slugs and is_tracking_dir(path):
            continue
        names.add(name)
        if path.is_file() and name.endswith(".html"):
            names.add(path.stem)
    names.update(
        {
            "index",
            "404",
            "CNAME",
            "favicon",
            "robots",
            "sitemap",
            "styles",
            "llms",
            "README",
            "PRODUCT",
        }
    )
    return names


def is_tracking_dir(folder: Path) -> bool:
    page = folder / "index.html"
    if not page.is_file():
        return False
    return MARKER in page.read_text(encoding="utf-8")


def page_html(dest: str) -> str:
    beacon = CLOUDFLARE_WEB_ANALYTICS.rstrip("\n")
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>GemmiSI</title>
  <meta name="robots" content="noindex, follow" />
  <meta http-equiv="refresh" content="1; url={dest}" />
  <link rel="canonical" href="{dest}" />
  <link rel="icon" href="/favicon.ico" sizes="any" />
</head>
<body>
  <!-- {MARKER} -->
  <p>Continue to <a href="{dest}">GemmiSI</a>.</p>
  <script>
    setTimeout(function () {{
      location.replace({dest!r});
    }}, 300);
  </script>
  {beacon}
</body>
</html>
"""


def existing_tracking_dirs() -> list[Path]:
    found = []
    for path in ROOT.iterdir():
        if path.is_dir() and is_tracking_dir(path):
            found.append(path)
    return found


def planned_files(links: list[tuple[str, str]]) -> dict[Path, str]:
    return {ROOT / slug / "index.html": page_html(dest) for slug, dest in links}


def build(check_only: bool = False) -> int:
    links = load_links()
    slugs = [slug for slug, _dest in links]
    reserved = reserved_names(set(slugs))
    collisions = [slug for slug in slugs if slug in reserved]
    if collisions:
        raise SystemExit(
            "tracking slugs collide with existing site paths: " + ", ".join(collisions)
        )

    planned = planned_files(links)
    stale = [
        folder
        for folder in existing_tracking_dirs()
        if folder.name not in set(slugs)
    ]

    if check_only:
        errors: list[str] = []
        for path, html in planned.items():
            if not path.is_file():
                errors.append(f"missing {path.relative_to(ROOT)}")
                continue
            if path.read_text(encoding="utf-8") != html:
                errors.append(f"stale {path.relative_to(ROOT)}")
        for folder in stale:
            errors.append(f"extra {folder.relative_to(ROOT)}/")
        if errors:
            print("\n".join(errors[:20]), file=sys.stderr)
            raise SystemExit(f"tracking pages out of date ({len(errors)} issues)")
        print(f"ok {len(slugs)} tracking pages")
        return 0

    for folder in stale:
        page = folder / "index.html"
        page.unlink()
        try:
            folder.rmdir()
        except OSError as exc:
            raise SystemExit(f"could not remove stale tracking folder {folder}: {exc}") from exc

    for path, html in planned.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html, encoding="utf-8")
    print(f"wrote {len(planned)} tracking pages")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Build campaign tracking short-link pages")
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit non-zero if committed pages do not match the generator",
    )
    args = parser.parse_args()
    build(check_only=args.check)


if __name__ == "__main__":
    main()
