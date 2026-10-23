#!/usr/bin/env python3
"""Validate titles, meta, JSON-LD, beacons, and FAQs on public HTML pages."""
from __future__ import annotations

import json
import re
import struct
import sys
from html import unescape
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SITEMAP = ROOT / "sitemap.xml"
ROBOTS = ROOT / "robots.txt"
BASE = "https://gemmisi.com"
SITE_NAME = "GemmiSI"
SITE_ALTERNATE_NAME = "GemmiSI - Super Intelligence (SI) AI implementation"
LOGO_URL = f"{BASE}/assets/brand/gemmisi-icon-512.png"
SKIP_SITEMAP_DIRS = {"chatbot", "sofer-preview"}
NEW_INDUSTRY_PAGES = (
    "restaurants-food",
    "local-shops",
    "nonprofits",
    "real-estate",
    "ecommerce",
)


def public_paths() -> list[Path]:
    text = SITEMAP.read_text(encoding="utf-8")
    locs = re.findall(r"<loc>(.*?)</loc>", text)
    paths = []
    for loc in locs:
        parsed = urlparse(loc)
        rel = parsed.path
        if rel in ("", "/"):
            paths.append(ROOT / "index.html")
        elif rel.endswith("/"):
            paths.append(ROOT / rel.strip("/") / "index.html")
        else:
            paths.append(ROOT / rel.lstrip("/"))
    extra = ROOT / "404.html"
    if extra.exists():
        paths.append(extra)
    missing = [p for p in paths if not p.exists()]
    if missing:
        raise SystemExit(f"sitemap files missing: {missing[:5]}")
    return paths


def jsonld_blocks(html: str) -> list[dict]:
    blocks = []
    for raw in re.findall(
        r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
        html,
        flags=re.S,
    ):
        blocks.append(json.loads(raw))
    return blocks


def graph_nodes(payloads: list[dict]) -> list[dict]:
    nodes = []
    for payload in payloads:
        if isinstance(payload, dict) and "@graph" in payload:
            nodes.extend(payload["@graph"])
        elif isinstance(payload, dict):
            nodes.append(payload)
        elif isinstance(payload, list):
            nodes.extend(payload)
    return nodes


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path} is not a PNG")
    return struct.unpack(">II", data[16:24])


def ico_sizes(path: Path) -> list[tuple[int, int]]:
    data = path.read_bytes()
    reserved, kind, count = struct.unpack_from("<HHH", data)
    if reserved != 0 or kind != 1:
        raise ValueError(f"{path} is not an ICO")
    sizes = []
    cursor = 6
    for _ in range(count):
        width, height, _colors, _res, _planes, _bits, _nbytes, _off = struct.unpack_from(
            "<BBBBHHII", data, cursor
        )
        sizes.append((width or 256, height or 256))
        cursor += 16
    return sizes


def expected_canonical(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    if rel == "index.html":
        return f"{BASE}/"
    if rel.endswith("/index.html"):
        return f"{BASE}/{rel[: -len('index.html')]}"
    return f"{BASE}/{rel}"


def is_moved_page(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False
    return 'http-equiv="refresh"' in text and "noindex" in text


def public_html_files() -> list[Path]:
    files = []
    for path in ROOT.rglob("*.html"):
        rel = path.relative_to(ROOT)
        parts = rel.parts
        if parts[0] in SKIP_SITEMAP_DIRS or parts[0].startswith("."):
            continue
        if path.name.startswith("google") and path.name.endswith(".html"):
            continue
        files.append(path)
    return files


def check_assets(errors: list[str]) -> None:
    for size in (16, 32, 48, 96, 180, 192, 512):
        path = ROOT / "assets" / "brand" / f"gemmisi-icon-{size}.png"
        if not path.exists():
            errors.append(f"missing {path.relative_to(ROOT)}")
            continue
        try:
            width, height = png_size(path)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if (width, height) != (size, size):
            errors.append(f"{path.name} is {width}x{height}, expected {size}x{size}")
    ico = ROOT / "favicon.ico"
    if not ico.exists():
        errors.append("missing favicon.ico")
        return
    try:
        sizes = ico_sizes(ico)
    except ValueError as exc:
        errors.append(str(exc))
        return
    if sizes != [(16, 16), (32, 32), (48, 48)]:
        errors.append(f"favicon.ico sizes {sizes}, expected 16/32/48")
    robots = ROBOTS.read_text(encoding="utf-8")
    if "Sitemap: https://gemmisi.com/sitemap.xml" not in robots:
        errors.append("robots.txt must point to https://gemmisi.com/sitemap.xml")
    blocked = re.findall(r"(?i)^Disallow:\s*(\S+)", robots, flags=re.M)
    for rule in blocked:
        if rule.startswith("/favicon") or rule.startswith("/assets") or rule.startswith("/site.webmanifest"):
            errors.append(f"robots.txt blocks {rule}")
    if "Allow: /favicon.ico" not in robots:
        errors.append("robots.txt should explicitly allow /favicon.ico")
    sitemap = SITEMAP.read_text(encoding="utf-8")
    if "github.io" in sitemap:
        errors.append("sitemap.xml must not include github.io URLs")
    locs = re.findall(r"<loc>(.*?)</loc>", sitemap)
    blocks = re.findall(r"<url>(.*?)</url>", sitemap, flags=re.S)
    for block in blocks:
        if "<lastmod>" not in block:
            loc = re.search(r"<loc>(.*?)</loc>", block)
            errors.append(f"sitemap missing lastmod for {loc.group(1) if loc else 'unknown'}")
    for slug in NEW_INDUSTRY_PAGES:
        needle = f"{BASE}/use-cases/industry/{slug}/"
        if needle not in locs:
            errors.append(f"sitemap missing industry landing {slug}")
    loc_set = set(locs)
    tracking_data = ROOT / "data" / "tracking-links.json"
    if tracking_data.is_file():
        payload = json.loads(tracking_data.read_text(encoding="utf-8"))
        raw = payload.get("slugs") if isinstance(payload, dict) else None
        tracking_slugs = [slug for slug in raw or [] if isinstance(slug, str)]
        for slug in tracking_slugs:
            needle = f"{BASE}/{slug}/"
            if needle in loc_set or f"{BASE}/{slug}" in loc_set:
                errors.append(f"sitemap must not include tracking path {needle}")
            page = ROOT / slug / "index.html"
            if not page.is_file():
                errors.append(f"missing tracking page {slug}/index.html")
                continue
            html = page.read_text(encoding="utf-8")
            if not is_moved_page(page):
                errors.append(f"{slug}/index.html must be noindex with a refresh")
            if html.count("cloudflareinsights.com/beacon.min.js") != 1:
                errors.append(f"{slug}/index.html: expected one Cloudflare beacon")
            if "location.replace" not in html:
                errors.append(f"{slug}/index.html: missing location.replace")
    for path in public_html_files():
        if path.name == "404.html" or is_moved_page(path):
            continue
        canon = expected_canonical(path)
        if canon not in loc_set:
            errors.append(f"sitemap missing {canon}")
    manifest = json.loads((ROOT / "site.webmanifest").read_text(encoding="utf-8"))
    if manifest.get("name") != SITE_NAME:
        errors.append("site.webmanifest name should be GemmiSI")
    if manifest.get("background_color") != "#080b0a":
        errors.append("site.webmanifest background_color should be #080b0a")
    if manifest.get("theme_color") != "#d3aa55":
        errors.append("site.webmanifest theme_color should be #d3aa55")
    icon_sizes = {icon.get("sizes") for icon in manifest.get("icons") or []}
    if "192x192" not in icon_sizes or "512x512" not in icon_sizes:
        errors.append("site.webmanifest must include 192 and 512 icons")


def main() -> None:
    paths = public_paths()
    titles: dict[str, Path] = {}
    descs: dict[str, Path] = {}
    errors: list[str] = []
    for path in paths:
        html = path.read_text(encoding="utf-8")
        rel = path.relative_to(ROOT)
        title_m = re.search(r"<title>(.*?)</title>", html, flags=re.S)
        desc_m = re.search(r'<meta name="description" content="(.*?)" />', html)
        if not title_m:
            errors.append(f"{rel}: missing title")
            continue
        title = unescape(re.sub(r"\s+", " ", title_m.group(1)).strip())
        desc = unescape(desc_m.group(1)) if desc_m else ""
        if title in titles:
            errors.append(f"{rel}: duplicate title with {titles[title]}")
        titles[title] = rel
        if desc:
            if desc in descs:
                errors.append(f"{rel}: duplicate meta with {descs[desc]}")
            descs[desc] = rel
        if 'sizes="48x48"' not in html or 'sizes="96x96"' not in html or 'sizes="192x192"' not in html:
            errors.append(f"{rel}: missing 48/96/192 PNG favicon links")
        if 'property="og:image"' not in html:
            errors.append(f"{rel}: missing og:image")
        if 'property="og:title"' not in html:
            errors.append(f"{rel}: missing og:title")
        og_site = re.search(r'<meta property="og:site_name" content="(.*?)" />', html)
        if not og_site or unescape(og_site.group(1)) != SITE_NAME:
            errors.append(f"{rel}: og:site_name should be GemmiSI")
        if 'name="twitter:card"' not in html:
            errors.append(f"{rel}: missing twitter:card")
        if path.name != "404.html":
            if "SI" not in title or "AI" not in title:
                errors.append(f"{rel}: title must include SI and AI ({title!r})")
            if desc and ("SI" not in desc or "AI" not in desc):
                errors.append(f"{rel}: meta must include SI and AI")
            if desc and len(desc) > 155:
                errors.append(f"{rel}: meta is {len(desc)} chars")
            if html.count("cloudflareinsights.com/beacon.min.js") != 1:
                errors.append(f"{rel}: expected one Cloudflare beacon")
            if 'rel="canonical"' not in html:
                errors.append(f"{rel}: missing canonical")
            else:
                canon_m = re.search(r'<link rel="canonical" href="(.*?)" />', html)
                canon = canon_m.group(1) if canon_m else ""
                if "github.io" in canon:
                    errors.append(f"{rel}: canonical must not use github.io")
                if not canon.startswith(f"{BASE}"):
                    errors.append(f"{rel}: canonical must be on https://gemmisi.com")
                expected = expected_canonical(path)
                if canon != expected:
                    errors.append(f"{rel}: canonical {canon} should be {expected}")
                if "/use-cases/" in canon and canon.endswith(".html"):
                    errors.append(f"{rel}: use-case canonical should be a directory URL")
            try:
                payloads = jsonld_blocks(html)
            except json.JSONDecodeError as exc:
                errors.append(f"{rel}: JSON-LD parse error: {exc}")
                continue
            if not payloads:
                errors.append(f"{rel}: missing JSON-LD")
                continue
            nodes = graph_nodes(payloads)
            orgs = [
                n
                for n in nodes
                if isinstance(n, dict)
                and (
                    n.get("@id") == f"{BASE}/#business"
                    or n.get("name") == "GemmiSI"
                    or (
                        isinstance(n.get("@type"), list)
                        and "ProfessionalService" in n["@type"]
                    )
                )
            ]
            if not orgs:
                errors.append(f"{rel}: missing GemmiSI Organization/ProfessionalService")
            else:
                named = {n.get("name") for n in orgs if n.get("@id") == f"{BASE}/#business" and n.get("name")}
                if named - {SITE_NAME}:
                    errors.append(f"{rel}: conflicting organization names {sorted(named)}")
                org = next((n for n in orgs if n.get("@id") == f"{BASE}/#business"), orgs[0])
                if org.get("name") != SITE_NAME:
                    errors.append(f"{rel}: organization name should be GemmiSI")
                if org.get("email") != "y@gemmisi.com":
                    errors.append(f"{rel}: organization email should be y@gemmisi.com")
                if "telephone" in org or "telephone" in (org.get("contactPoint") or {}):
                    errors.append(f"{rel}: telephone must be omitted from structured data")
                if "streetAddress" in json.dumps(org.get("address") or {}):
                    errors.append(f"{rel}: no street address")
                logo = org.get("logo")
                logo_url = logo.get("url") if isinstance(logo, dict) else logo
                if logo_url != LOGO_URL:
                    errors.append(f"{rel}: organization logo should be the 512 PNG")
                founder = org.get("founder") or {}
                if founder.get("name") not in ("Josh Gemmi", "Yonatan (Josh) Gemmi"):
                    errors.append(f"{rel}: founder should be Josh Gemmi")
                served = json.dumps(org.get("areaServed") or [])
                if "South Florida" not in served or "United States" not in served:
                    errors.append(f"{rel}: areaServed should include South Florida and United States")
            sites = [n for n in nodes if isinstance(n, dict) and n.get("@type") == "WebSite"]
            if not sites:
                errors.append(f"{rel}: missing WebSite JSON-LD")
            else:
                site = sites[0]
                if site.get("name") != SITE_NAME:
                    errors.append(f"{rel}: WebSite name should be GemmiSI")
                if site.get("alternateName") != SITE_ALTERNATE_NAME:
                    errors.append(f"{rel}: WebSite alternateName should describe SI/AI")
            if '"telephone"' in json.dumps(nodes):
                errors.append(f"{rel}: telephone must not appear in JSON-LD")
            people = [n for n in nodes if isinstance(n, dict) and n.get("@id") == f"{BASE}/#person"]
            if people and people[0].get("alternateName") != "Josh Gemmi":
                errors.append(f"{rel}: Person alternateName should be Josh Gemmi")
            services = [n for n in nodes if isinstance(n, dict) and n.get("@type") == "Service"]
            for svc in services:
                provider = svc.get("provider") or {}
                if provider.get("@id") not in (None, f"{BASE}/#business", f"{BASE}/#person"):
                    errors.append(f"{rel}: Service provider should point at the org or person")
                if provider.get("@id") == f"{BASE}/#person" and not svc.get("isRelatedTo"):
                    errors.append(f"{rel}: Service should link to the organization @id")
            offers = [n for n in nodes if isinstance(n, dict) and n.get("@type") == "Offer"]
            for offer in offers:
                if offer.get("offeredBy", {}).get("@id") not in (None, f"{BASE}/#business"):
                    errors.append(f"{rel}: Offer should link to the organization")

        rel_str = str(rel)
        industry_landing = bool(re.fullmatch(r"use-cases/industry/[^/]+/index.html", rel_str))
        entry_page = bool(re.fullmatch(r"use-cases/[^/]+/index.html", rel_str)) and not rel_str.endswith(
            "use-cases/index.html"
        )
        service_page = path.parent.name == "services"
        if (industry_landing or entry_page) and "BreadcrumbList" not in html:
            errors.append(f"{rel}: missing BreadcrumbList JSON-LD")
        if industry_landing or service_page:
            faq_count = html.count('class="faq-item"')
            if faq_count < 4 or faq_count > 6:
                errors.append(f"{rel}: FAQ count {faq_count} not in 4–6")
            if "FAQPage" not in html:
                errors.append(f"{rel}: missing FAQPage JSON-LD")

    check_assets(errors)
    if errors:
        print("\n".join(errors[:40]))
        if len(errors) > 40:
            print(f"... and {len(errors) - 40} more")
        raise SystemExit(f"SEO validation failed ({len(errors)} issues)")
    print(f"ok {len(paths)} pages, {len(titles)} unique titles")


if __name__ == "__main__":
    main()
