#!/usr/bin/env python3
"""Validate titles, meta, JSON-LD, beacons, and FAQs on public HTML pages."""
from __future__ import annotations

import json
import re
import sys
from html import unescape
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SITEMAP = ROOT / "sitemap.xml"
BASE = "https://gemmisi.com"


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
                org = next((n for n in orgs if n.get("@id") == f"{BASE}/#business"), orgs[0])
                if org.get("name") not in (None, "GemmiSI") and org.get("@id") == f"{BASE}/#business":
                    if org.get("name") != "GemmiSI":
                        errors.append(f"{rel}: organization name should be GemmiSI")
                if "telephone" in org:
                    errors.append(f"{rel}: telephone must be omitted")
                if "streetAddress" in json.dumps(org.get("address") or {}):
                    errors.append(f"{rel}: no street address")
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
        service_page = path.parent.name == "services"
        if industry_landing or service_page:
            faq_count = html.count('class="faq-item"')
            if faq_count < 4 or faq_count > 6:
                errors.append(f"{rel}: FAQ count {faq_count} not in 4–6")
            if "FAQPage" not in html:
                errors.append(f"{rel}: missing FAQPage JSON-LD")

    if errors:
        print("\n".join(errors[:40]))
        if len(errors) > 40:
            print(f"... and {len(errors) - 40} more")
        raise SystemExit(f"SEO validation failed ({len(errors)} issues)")
    print(f"ok {len(paths)} pages, {len(titles)} unique titles")


if __name__ == "__main__":
    main()
