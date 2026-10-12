#!/usr/bin/env python3
"""Generate the static use-cases library from data/use-cases.json.

Run from the repo root:

    python3 scripts/build_use_cases.py

Writes use-cases/index.html, industry and function landings, use-cases/search.json,
one folder per slug, and refreshes the use-case URLs in sitemap.xml. Pages are
plain HTML. GitHub Pages serves them with no build step. The search index is
fetched only when someone searches, filters, or asks to show more.
"""

from __future__ import annotations

import html
import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seo_schema import CLOUDFLARE_WEB_ANALYTICS, CSS_VERSION, NAV_SCRIPT, font_and_css_links
from use_case_motifs import motif_bytes, motif_html, pick_industry, pick_motif

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "use-cases.json"
TAXONOMY_PATH = ROOT / "data" / "taxonomy.json"
OUT = ROOT / "use-cases"
SITEMAP = ROOT / "sitemap.xml"

BASE = "https://gemmisi.com"
CAL = "https://calendly.com/josh-gemmi/30min"
OG_IMAGE = f"{BASE}/assets/brand/gemmisi-og.png"
OG_ALT = "GemmiSI — SI, automation, dashboards, and technical operations"

REQUIRED = (
    "slug",
    "title",
    "industries",
    "functions",
    "summary",
    "problem",
    "what_si_does",
    "setup",
    "human_checks",
    "examples",
    "copy_prompt",
    "tools_examples",
    "effect",
)
RESERVED_SLUGS = {"industry", "function"}
SHOW_MORE = 18
ANY_VISIBLE = 12
HUB_MIN_BYTES = 20_000
HUB_MAX_BYTES = 90_000
CTA = "Book a free 30-minute consult"

BANNED_SUBSTRINGS = ("Nous", "Brandgate", "Ohr", "Kayla", "josh.gemmi@gmail.com")
HIPAA_CLAIM = re.compile(
    r"hipaa[ -]?(compliant|certified|safe)|guaranteed compliance",
    re.I,
)
HOSTING_CLAIM = re.compile(
    r"gemmisi (hosts|stores|host|store)|we host your|we store your data|"
    r"hosted by gemmisi|gemmisi hosts your|stores client data",
    re.I,
)

TAX: dict = {}
INDUSTRIES: dict = {}
FUNCTIONS: dict = {}
OWN_ACCOUNTS = ""
ALSO_USED_NOTE = ""
FEATURED_SLUGS: list[str] = []
LEGACY: dict = {}


def e(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def json_ld(obj, *, compact: bool = False) -> str:
    if compact:
        raw = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    else:
        raw = json.dumps(obj, ensure_ascii=False, indent=2)
    return raw.replace("<", "\\u003c")


def primary_industry(item: dict) -> str:
    return item["industries"][0]


def primary_function(item: dict) -> str:
    return item["functions"][0]


def is_regulated(slug: str) -> bool:
    return bool(INDUSTRIES.get(slug, {}).get("regulated"))


def industry_info(slug: str) -> dict:
    info = INDUSTRIES.get(slug)
    if not info:
        raise SystemExit(f"Unknown industry {slug!r}")
    return info


def function_info(slug: str) -> dict:
    info = FUNCTIONS.get(slug)
    if not info:
        raise SystemExit(f"Unknown function {slug!r}")
    return info


def card_label(item: dict) -> str:
    ind = primary_industry(item)
    if ind != "any-business":
        return industry_info(ind)["label"]
    return function_info(primary_function(item))["label"]


def dedicated_note(item: dict) -> str:
    ind = primary_industry(item)
    info = industry_info(ind)
    return info["short"] if info.get("regulated") else ""


def load_taxonomy() -> None:
    global TAX, INDUSTRIES, FUNCTIONS, OWN_ACCOUNTS, ALSO_USED_NOTE, FEATURED_SLUGS, LEGACY
    TAX = json.loads(TAXONOMY_PATH.read_text(encoding="utf-8"))
    INDUSTRIES = TAX["industries"]
    FUNCTIONS = TAX["functions"]
    OWN_ACCOUNTS = TAX["own_accounts"]
    ALSO_USED_NOTE = TAX["also_used_note"]
    FEATURED_SLUGS = list(TAX["featured"])
    LEGACY = dict(TAX["legacy_anchors"])
    if len(FEATURED_SLUGS) != 12:
        raise SystemExit(f"taxonomy.featured must list 12 slugs, found {len(FEATURED_SLUGS)}")
    if OWN_ACCOUNTS != "GemmiSI sets this up on your own equipment and accounts; your data stays with you.":
        raise SystemExit("taxonomy.own_accounts must keep the approved own-accounts line")


def _check_banned_blob(item: dict, blob: str) -> None:
    slug = item["slug"]
    if re.search(r"\bAI\b", blob) or HIPAA_CLAIM.search(blob) or HOSTING_CLAIM.search(blob):
        raise SystemExit(f"{slug} contains wording that must stay off the public site")
    for banned in BANNED_SUBSTRINGS:
        if banned in blob:
            raise SystemExit(f"{slug} contains wording that must stay off the public site")


def _check_industry_entry(item: dict) -> None:
    ind = primary_industry(item)
    caution = (item.get("caution") or "").strip()
    prompt = item["copy_prompt"]
    blob = json.dumps(item)
    lowered = blob.lower()
    info = industry_info(ind)
    if len(item["human_checks"]) < 3:
        raise SystemExit(f"{item['slug']} needs at least three human checks")
    prefix = info.get("caution_prefix") or ""
    if prefix and not caution.startswith(prefix):
        raise SystemExit(f"{item['slug']} caution must start with the {ind} guardrail")
    extra = ""
    texting = False
    if ind == "real-estate":
        if not item["setup"].startswith(OWN_ACCOUNTS):
            raise SystemExit(f"{item['slug']} setup must start with the own-equipment sentence")
        if "Pause and show me before sending, posting, signing or changing anything" not in prompt:
            raise SystemExit(f"{item['slug']} prompt must pause before sending, posting, signing, or changing")
        if (
            "Use only the sample or made-up information I provide; do not include real tenant or applicant names, IDs or financial details"
            not in prompt
        ):
            raise SystemExit(f"{item['slug']} prompt must limit itself to sample or made-up information")
        if item["slug"] in (
            "listing-rental-ad-drafts",
            "maintenance-request-intake",
            "rental-application-completeness",
        ):
            extra = "Do not describe or evaluate any person or neighborhood; describe only the property."
        texting = item["slug"] in (
            "rental-lead-inquiry-follow-up",
            "showing-scheduling-confirmations",
            "showing-open-house-follow-up",
            "rent-reminder-drafts",
        )
        if "does not lease, collect rent, screen or rank applicants" not in blob:
            raise SystemExit(f"{item['slug']} must say SI does not lease, collect rent, screen or rank applicants")
        for phrase in (
            "fair housing compliant",
            "guaranteed compliance",
            "tenant scoring",
            "best tenants",
            "ideal tenant",
            "good neighborhood",
            "safe area",
            "family-friendly",
            "never miss a lead",
            "fully automated",
            "we handle your leasing",
            "boost sales",
        ):
            if phrase in lowered:
                raise SystemExit(f"{item['slug']} contains wording that must stay off the public site")
    elif ind == "home-services":
        if not item["setup"].startswith(OWN_ACCOUNTS):
            raise SystemExit(f"{item['slug']} setup must start with the own-equipment sentence")
        if "Pause and show me before sending, quoting, booking, ordering or changing anything" not in prompt:
            raise SystemExit(f"{item['slug']} prompt must pause before sending, quoting, booking, ordering, or changing")
        if (
            "Use only the sample or made-up information I provide; do not include real customer names, addresses or payment details"
            not in prompt
        ):
            raise SystemExit(f"{item['slug']} prompt must limit itself to sample or made-up information")
        if item["slug"] in ("quote-estimate-drafts", "permit-inspection-tracking"):
            extra = "Do not decide prices, code requirements or whether a permit is needed."
        texting = item["slug"] in (
            "missed-call-text-back",
            "contractor-invoice-reminders",
            "contractor-review-reply-drafts",
            "warranty-maintenance-reminders",
            "contractor-after-hours-sorting",
        )
        for phrase in (
            "lowest price",
            "best in town",
            "instant quote",
            "automatic pricing",
            "book jobs automatically",
            "never miss a call",
            "boost revenue",
            "fully automated",
            "free roof inspection",
            "si diagnoses",
        ):
            if phrase in lowered:
                raise SystemExit(f"{item['slug']} contains wording that must stay off the public site")
    else:
        if not item["setup"].startswith(OWN_ACCOUNTS):
            raise SystemExit(f"{item['slug']} setup must start with the own-equipment sentence")
        if "Pause and show me before sending, filing, posting or changing anything" not in prompt:
            raise SystemExit(f"{item['slug']} prompt must pause before sending, filing, posting, or changing")
        if (
            "Use only the sample or made-up information I provide; do not include real client names, SSNs, account numbers or tax details"
            not in prompt
        ):
            raise SystemExit(f"{item['slug']} prompt must limit itself to sample or made-up information")
        if item["slug"] in (
            "tax-deadline-tracking",
            "vendor-1099-information-collection",
            "sales-tax-filing-reminders",
        ):
            extra = "Do not calculate or confirm any due date, threshold or tax; list only what I give you for a professional to verify."
        if item["slug"] in (
            "tax-new-client-intake",
            "reconciliation-prep-for-review",
            "vendor-1099-information-collection",
            "security-plan-upkeep-checklists",
        ):
            extra2 = "Tax return information has special disclosure and use rules for preparers; check with your professional advisor before using any outside tool."
            if extra2 not in prompt and extra2 not in caution:
                raise SystemExit(f"{item['slug']} must note tax return information disclosure rules")
        for phrase in (
            "maximize your refund",
            "audit-proof",
            "irs compliant",
            "safeguards compliant",
            "7216 compliant",
            "bank-level security",
            "never miss a deadline",
            "guaranteed on time",
            "audit-ready books",
            "fully automated",
            "cpa-approved",
            "replace your accountant",
        ):
            if phrase in lowered:
                raise SystemExit(f"{item['slug']} contains wording that must stay off the public site")
    if extra and extra not in prompt:
        raise SystemExit(f"{item['slug']} prompt must include {extra!r}")
    if texting and "Texting rules vary; get consent and honor opt-outs." not in caution and "Texting rules vary; get consent and honor opt-outs." not in prompt:
        raise SystemExit(f"{item['slug']} must note texting consent and opt-outs")


def load() -> list:
    load_taxonomy()
    entries = json.loads(DATA.read_text(encoding="utf-8"))
    if not isinstance(entries, list) or not entries:
        raise SystemExit("data/use-cases.json must be a non-empty list")
    slugs = []
    featured_flags = []
    for item in entries:
        missing = [key for key in REQUIRED if key not in item]
        if missing:
            raise SystemExit(f"{item.get('slug', '?')} is missing {', '.join(missing)}")
        slug = item["slug"]
        if slug in RESERVED_SLUGS:
            raise SystemExit(f"{slug} is reserved for landing routes")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
            raise SystemExit(f"Slug must be lowercase hyphenated words: {slug}")
        inds = item["industries"]
        fns = item["functions"]
        if not isinstance(inds, list) or not inds or not isinstance(fns, list) or not fns:
            raise SystemExit(f"{slug} needs non-empty industries and functions lists")
        if len(inds) > 4:
            raise SystemExit(f"{slug} industries cap is 4")
        if len(set(inds)) != len(inds) or len(set(fns)) != len(fns):
            raise SystemExit(f"{slug} has duplicate industry or function tags")
        for ind in inds:
            if ind not in INDUSTRIES:
                raise SystemExit(f"Unknown industry {ind!r} on {slug}")
        for fn in fns:
            if fn not in FUNCTIONS:
                raise SystemExit(f"Unknown function {fn!r} on {slug}")
        if primary_industry(item) != "any-business" and "any-business" in inds:
            raise SystemExit(f"{slug} dedicated vertical entries must not also be any-business")
        if not item["examples"] or not all(
            isinstance(ex, dict) and ex.get("business_type") and ex.get("scenario")
            for ex in item["examples"]
        ):
            raise SystemExit(f"{slug} examples must include business_type and scenario")
        blob = json.dumps(item)
        _check_banned_blob(item, blob)
        ind = primary_industry(item)
        if is_regulated(ind):
            if OWN_ACCOUNTS not in item["setup"]:
                raise SystemExit(f"{slug} setup must say the work stays on your own equipment and accounts")
        if ind == "legal":
            caution = (item.get("caution") or "").strip()
            if not caution.startswith(industry_info("legal")["caution_prefix"]):
                raise SystemExit(f"{slug} caution must start with the legal guardrail")
            prompt = item["copy_prompt"]
            if "Pause and show me before sending, filing, posting or changing anything" not in prompt:
                raise SystemExit(f"{slug} prompt must pause before sending, filing, posting, or changing")
            if (
                "Use only the sample or de-identified information I provide; do not include client-confidential details"
                not in prompt
            ):
                raise SystemExit(f"{slug} prompt must limit itself to sample or de-identified information")
            if len(item["human_checks"]) < 3:
                raise SystemExit(f"{slug} needs at least three human checks")
        elif ind == "medical":
            caution = (item.get("caution") or "").strip()
            if not caution.startswith(industry_info("medical")["caution_prefix"]):
                raise SystemExit(f"{slug} caution must start with the medical guardrail")
            prompt = item["copy_prompt"]
            if "Pause and show me before sending, submitting, billing, posting or changing anything" not in prompt:
                raise SystemExit(f"{slug} prompt must pause before sending, submitting, billing, posting, or changing")
            if (
                "Use only the sample or de-identified information I provide; do not include any patient names or health information"
                not in prompt
            ):
                raise SystemExit(f"{slug} prompt must limit itself to sample or de-identified information")
            if len(item["human_checks"]) < 3:
                raise SystemExit(f"{slug} needs at least three human checks")
            if not item["setup"].startswith(OWN_ACCOUNTS):
                raise SystemExit(f"{slug} setup must start with the own-equipment sentence")
            if re.search(r"diagnose", blob, re.I):
                raise SystemExit(f"{slug} must not use the word diagnose")
        elif ind in ("real-estate", "home-services", "accounting"):
            _check_industry_entry(item)
        if item.get("featured"):
            featured_flags.append(slug)
        slugs.append(slug)
    dupes = {slug for slug in slugs if slugs.count(slug) > 1}
    if dupes:
        raise SystemExit(f"Duplicate slugs: {', '.join(sorted(dupes))}")
    if set(featured_flags) != set(FEATURED_SLUGS):
        raise SystemExit(
            "featured: true flags must match taxonomy.featured "
            f"(flags={sorted(featured_flags)} taxonomy={FEATURED_SLUGS})"
        )
    return entries


def featured_entries(entries: list) -> list:
    by_slug = {item["slug"]: item for item in entries}
    return [by_slug[slug] for slug in FEATURED_SLUGS]


def matching_industry(entries: list, slug: str) -> list:
    return [item for item in entries if slug in item["industries"]]


def matching_function(entries: list, slug: str) -> list:
    return [item for item in entries if slug in item["functions"]]


def dedicated(entries: list, industry: str) -> list:
    return [item for item in entries if primary_industry(item) == industry]


def cross_tagged(entries: list, industry: str) -> list:
    return [
        item
        for item in entries
        if industry in item["industries"] and primary_industry(item) != industry
    ]


def industry_counts(entries: list) -> dict[str, int]:
    return {slug: len(matching_industry(entries, slug)) for slug in INDUSTRIES}


def function_counts(entries: list) -> dict[str, int]:
    return {slug: len(matching_function(entries, slug)) for slug in FUNCTIONS}


def nav(depth: int) -> str:
    up = "../" * depth
    library = "../" * (depth - 1) + "index.html" if depth else "index.html"
    return f"""    <header class="nav">
      <a class="brand" href="{up}index.html" aria-label="GemmiSI home">
        <img class="brand-lockup" src="{up}assets/brand/gemmisi-lockup-dark.svg" alt="" width="159" height="36" />
      </a>
      <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav" aria-label="Open site menu">
        <span class="nav-toggle__bars" aria-hidden="true"></span>
        <span class="nav-toggle__label">Menu</span>
      </button>
      <nav id="site-nav" class="nav-links" aria-label="Primary navigation">
        <a href="{up}index.html">Home</a>
        <a href="{up}index.html#work">Work</a>
        <details class="nav-dropdown">
          <summary class="nav-dropdown-trigger">Services</summary>
          <div class="nav-dropdown-menu">
            <a href="{up}services/hermes-agents.html">Hermes Agents</a>
            <a href="{up}services/ai-automation.html">SI automation</a>
            <a href="{up}services/dashboards-reporting.html">Dashboards &amp; reporting</a>
            <a href="{up}services/ecommerce-operations.html">Ecommerce operations</a>
            <a href="{up}services/tutoring-project-help.html">Tutoring &amp; project help</a>
            <a class="nav-dropdown-muted" href="{up}services/stocky-recovery.html">Stocky dump recovery</a>
            <a class="nav-dropdown-muted" href="{up}index.html#service-hub">All services</a>
            <a class="nav-dropdown-muted" href="{up}advisory.html">Advisory &amp; Fractional (ask first)</a>
          </div>
        </details>
        <a href="{library}" aria-current="page">Use cases</a>
        <a href="{up}pricing.html">Pricing</a>
      </nav>
      <a class="nav-cta" href="{CAL}" target="_blank" rel="noreferrer">Book consultation</a>
    </header>"""


def foot(depth: int) -> str:
    up = "../" * depth
    library = "../" * (depth - 1) + "index.html" if depth else "index.html"
    return f"""    <footer>
      <a class="footer-brand" href="{up}index.html" aria-label="GemmiSI home">
        <img class="footer-lockup" src="{up}assets/brand/gemmisi-lockup-dark.svg" alt="" width="123" height="28" />
      </a>
      <p>© <span id="year"></span> Yonatan Gemmi. Based in North Miami Beach, Florida · Miami-Dade, Broward, and remote</p>
      <p class="footer-nav">
        <a href="{up}index.html">Home</a>
        <a href="{library}">Use cases</a>
        <a href="{up}pricing.html">Pricing</a>
        <a href="{up}services/hermes-agents.html">Hermes desks</a>
        <a href="{up}services/ai-automation.html">SI automation</a>
        <a href="{up}services/dashboards-reporting.html">Dashboards</a>
        <a href="{up}services/ecommerce-operations.html">Ecommerce</a>
        <a href="{up}services/tutoring-project-help.html">Tutoring</a>
        <a href="{CAL}" target="_blank" rel="noreferrer">Book consultation</a>
      </p>
    </footer>"""


SCRIPTS = NAV_SCRIPT
LIBRARY_JS = '  <script src="/assets/use-cases-library.js" defer></script>\n'
PAGE_END = CLOUDFLARE_WEB_ANALYTICS + "</body>\n</html>\n"


def head(
    title: str,
    desc: str,
    canon: str,
    depth: int,
    ld: dict,
    *,
    compact_ld: bool = False,
    body_attrs: str = "",
) -> str:
    up = "../" * depth
    assets = font_and_css_links(
        stylesheet=f"{up}styles.css?v={CSS_VERSION}",
        extra_css=f"{up}assets/use-cases.css?v={CSS_VERSION}",
    )
    attrs = f" {body_attrs}" if body_attrs else ""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{e(title)}</title>
  <meta name="description" content="{e(desc)}" />
  <link rel="canonical" href="{BASE}{canon}" />
  <meta name="robots" content="index, follow" />
  <meta name="author" content="Yonatan Gemmi" />
  <meta property="og:title" content="{e(title)}" />
  <meta property="og:description" content="{e(desc)}" />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="{BASE}{canon}" />
  <meta property="og:site_name" content="Yonatan Gemmi" />
  <meta property="og:locale" content="en_US" />
  <meta property="og:image" content="{OG_IMAGE}" />
  <meta property="og:image:width" content="1200" />
  <meta property="og:image:height" content="630" />
  <meta property="og:image:alt" content="{e(OG_ALT)}" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{e(title)}" />
  <meta name="twitter:description" content="{e(desc)}" />
  <meta name="twitter:image" content="{OG_IMAGE}" />
  <meta name="twitter:image:alt" content="{e(OG_ALT)}" />
  <link rel="sitemap" type="application/xml" title="Sitemap" href="{BASE}/sitemap.xml" />
{assets}
  <link rel="icon" href="/favicon.ico" sizes="any" />
  <link rel="icon" href="/assets/brand/gemmisi-icon.svg" type="image/svg+xml" />
  <link rel="icon" href="/assets/brand/gemmisi-icon-32.png" type="image/png" sizes="32x32" />
  <link rel="icon" href="/assets/brand/gemmisi-icon-16.png" type="image/png" sizes="16x16" />
  <link rel="apple-touch-icon" href="/assets/brand/gemmisi-icon-180.png" />
  <link rel="manifest" href="/site.webmanifest" />
  <script type="application/ld+json">
{json_ld(ld, compact=compact_ld)}
  </script>
</head>
<body{attrs}>
  <div class="site-shell">
{nav(depth)}
"""


def haystack(item: dict) -> str:
    parts = [item["title"], item["summary"], card_label(item)]
    for slug in item["industries"]:
        parts.append(industry_info(slug)["label"])
        parts.append(slug.replace("-", " "))
    for slug in item["functions"]:
        parts.append(function_info(slug)["label"])
        parts.append(slug.replace("-", " "))
    parts.extend(item.get("tools_examples") or [])
    for example in item.get("examples") or []:
        parts.append(example.get("business_type", ""))
        parts.append(example.get("scenario", ""))
    return " ".join(parts).lower()


def card(item: dict, *, extra_cls: str = "", note: str | None = None, featured: bool = False) -> str:
    label = card_label(item)
    cls = "uc-card"
    if extra_cls:
        cls += f" {extra_cls}"
    if featured:
        cls += " uc-featured"
    note_text = dedicated_note(item) if note is None else note
    note_html = f'\n              <p class="uc-card-note">{e(note_text)}</p>' if note_text else ""
    inds = ",".join(item["industries"])
    fns = ",".join(item["functions"])
    return f"""<li class="{cls}" data-slug="{e(item['slug'])}" data-i="{e(inds)}" data-f="{e(fns)}">
            <a href="/use-cases/{e(item['slug'])}/">
              <span class="uc-card-cat">{e(label)}</span>
              <h3>{e(item['title'])}</h3>
              <p>{e(item['summary'])}</p>{note_html}
              <span class="uc-card-more">Read the use case <span aria-hidden="true">→</span></span>
            </a>
          </li>"""


def compact_link(item: dict) -> str:
    inds = ",".join(item["industries"])
    fns = ",".join(item["functions"])
    return (
        f'<li class="uc-compact" data-slug="{e(item["slug"])}" data-i="{e(inds)}" data-f="{e(fns)}">'
        f'<a href="/use-cases/{e(item["slug"])}/">{e(item["title"])}</a></li>'
    )


def item_list(entries: list) -> dict:
    return {
        "@type": "ItemList",
        "numberOfItems": len(entries),
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "url": f"{BASE}/use-cases/{item['slug']}/",
                "name": item["title"],
            }
            for i, item in enumerate(entries)
        ],
    }


def crumbs(*parts: tuple[str, str]) -> dict:
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": name, "item": url}
            for i, (name, url) in enumerate(parts)
        ],
    }


def collection_ld(name: str, url: str, desc: str, entries: list, trail: list[tuple[str, str]]) -> dict:
    return {
        "@context": "https://schema.org",
        "@graph": [
            crumbs(*trail),
            {
                "@type": "CollectionPage",
                "name": name,
                "url": url,
                "description": desc,
                "isPartOf": {"@type": "WebSite", "name": "Yonatan Gemmi", "url": BASE + "/"},
                "mainEntity": item_list(entries),
            },
        ],
    }


def breadcrumb_html(depth: int, items: list[tuple[str, str | None]]) -> str:
    up = "../" * depth
    parts = []
    for i, (label, href) in enumerate(items):
        if i:
            parts.append('<span aria-hidden="true">/</span>')
        if href:
            parts.append(f'<a href="{href if href.startswith("/") or href.startswith(".") else up + href}">{e(label)}</a>')
        else:
            parts.append(f"<span>{e(label)}</span>")
    return f'        <nav class="breadcrumb" aria-label="Breadcrumb">\n          ' + "\n          ".join(parts) + "\n        </nav>"


def industry_tiles(entries: list, *, current: str | None = None, extra_query: str = "") -> str:
    counts = industry_counts(entries)
    tiles = []
    for slug, info in INDUSTRIES.items():
        n = counts[slug]
        if n == 0:
            continue
        href = f"/use-cases/industry/{slug}/"
        if extra_query:
            href = f"/use-cases/?industry={slug}&{extra_query}"
        active = " is-active" if current == slug else ""
        tiles.append(
            f'<a class="uc-tile{active}" href="{href}" data-industry="{slug}">'
            f'<span class="uc-tile-label">{e(info["label"])}</span>'
            f'<span class="uc-tile-count">{n}</span></a>'
        )
    return (
        '<div class="uc-tiles" role="navigation" aria-label="Browse by industry">\n          '
        + "\n          ".join(tiles)
        + "\n        </div>"
    )


def function_pills(
    entries: list,
    *,
    current: str | None = None,
    industry: str | None = None,
    toggles: bool = False,
) -> str:
    counts = function_counts(entries)
    pills = []
    for slug, info in FUNCTIONS.items():
        n = counts[slug]
        if n == 0:
            continue
        if industry:
            href = f"/use-cases/?industry={industry}&function={slug}"
        else:
            href = f"/use-cases/function/{slug}/"
        active = " is-active" if current == slug else ""
        if toggles:
            pills.append(
                f'<button type="button" class="uc-pill{active}" data-function="{slug}" aria-pressed="false">'
                f'{e(info["label"])} <span>{n}</span></button>'
            )
        else:
            pills.append(
                f'<a class="uc-pill{active}" href="{href}" data-function="{slug}">'
                f'{e(info["label"])} <span>{n}</span></a>'
            )
    return "\n            ".join(pills)


def function_chip_row(
    entries: list,
    *,
    industry: str | None = None,
    current_fn: str | None = None,
    toggles: bool = False,
) -> str:
    pills = function_pills(entries, current=current_fn, industry=industry, toggles=toggles)
    return (
        '<div class="uc-pills" id="uc-functions" role="group" aria-label="Filter by function">\n'
        f"            {pills}\n"
        "          </div>"
    )


def read_first_banner(industry: str) -> str:
    info = industry_info(industry)
    if not info.get("regulated"):
        return ""
    return (
        '        <div class="uc-read-first" role="note">\n'
        f"          <p>{info['read_first']}</p>\n"
        f'          <p class="uc-own-accounts">{e(OWN_ACCOUNTS)}</p>\n'
        "        </div>\n"
    )


def search_records(entries: list) -> list[dict]:
    records = []
    featured = set(FEATURED_SLUGS)
    for item in entries:
        row = {
            "s": item["slug"],
            "t": item["title"],
            "u": item["summary"],
            "i": item["industries"],
            "f": item["functions"],
            "l": card_label(item),
            "h": haystack(item),
        }
        note = dedicated_note(item)
        if note:
            row["n"] = note
        if item["slug"] in featured:
            row["g"] = True
        records.append(row)
    return records


def write_search_index(entries: list) -> None:
    payload = {"legacy": LEGACY, "page": SHOW_MORE, "items": search_records(entries)}
    (OUT / "search.json").write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def closing_section() -> str:
    return f"""      <section class="section closing-card uc-closing">
        <div class="contact-panel">
          <p class="section-kicker">Don’t see yours?</p>
          <h2>Bring the task that keeps eating your week</h2>
          <p class="section-intro">If it is repetitive, rule-based, and lives in email, spreadsheets, a store, or a CRM, there is a good chance it can be drafted by SI and checked by you. Book a free 30-minute call and we will look at it together.</p>
          <div class="actions"><a class="button primary" href="{CAL}" target="_blank" rel="noreferrer">{CTA}</a></div>
        </div>
      </section>"""


def library_page(entries: list) -> str:
    n = len(entries)
    featured = featured_entries(entries)
    title = "SI use cases for small businesses and community organizations | Yonatan Gemmi"
    desc = (
        f"{n} practical ways SI can take routine work off a small team. Browse by industry "
        "or search. Each entry shows what a human still checks."
    )
    ld = collection_ld(
        "SI use cases",
        BASE + "/use-cases/",
        desc,
        featured,
        [("Home", BASE + "/"), ("Use cases", BASE + "/use-cases/")],
    )
    ld["@graph"][1]["mainEntity"]["numberOfItems"] = n
    cards = "\n          ".join(card(item, featured=True, note="") for item in featured)
    config = json.dumps(
        {"legacy": LEGACY, "n": n, "page": SHOW_MORE, "mode": "hub"},
        ensure_ascii=False,
        separators=(",", ":"),
    )
    # The single allowed "AI" bridge lives in this intro and nowhere else.
    return head(
        title,
        desc,
        "/use-cases/",
        1,
        ld,
        compact_ld=True,
        body_attrs='data-uc="hub"',
    ) + f"""
    <main id="top">
      <section class="uc-hero">
{breadcrumb_html(1, [("Home", "../index.html"), ("Use cases", None)])}
        <p class="eyebrow"><span class="status-dot" aria-hidden="true"></span>{n} practical examples</p>
        <h1>What SI can take off your plate</h1>
        <p class="lead">SI (Super Intelligence, formerly called AI) can take on a lot of the repetitive work in almost any business or organization: reading, sorting, matching, drafting, checking and summarizing. Each entry describes one practical job, what it needs to get started, and where a person stays in charge. Anything that sends, pays, orders or posts always waits for your approval.</p>
        <p class="uc-note-intro">The examples show how the same job looks in different kinds of businesses. They are illustrations of what is possible, not reports of client results. Setup times are rough and depend on how clean your data and tools are.</p>
        <div class="actions">
          <a class="button primary" href="{CAL}" target="_blank" rel="noreferrer">{CTA}</a>
        </div>
      </section>

      <section id="library" class="uc-tools" aria-label="Search and filter use cases">
        <div class="uc-search">
          <label for="uc-q" class="visually-hidden">Search use cases</label>
          <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" stroke-width="2"/><path d="M20 20l-4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
          <input id="uc-q" type="search" placeholder="Search, e.g. invoices, schedule, Gmail" autocomplete="off" />
        </div>
        {function_chip_row(entries, toggles=True)}
        <p class="uc-tile-legend">Industry</p>
        {industry_tiles(entries)}
        <p class="uc-count" id="uc-count" role="status" aria-live="polite">Showing {len(featured)} of {n} use cases</p>
        <button type="button" class="uc-clear" id="uc-clear" hidden>Clear all</button>
      </section>

      <section class="uc-group" aria-labelledby="featured-h">
        <div class="uc-group-head">
          <span class="section-kicker">Featured</span>
          <h2 id="featured-h">A dozen places to start</h2>
          <p>Twelve examples from the library. Pick an industry above for the rest, or show more.</p>
        </div>
        <ul class="uc-grid" id="uc-grid">
          {cards}
        </ul>
        <button type="button" class="uc-more uc-show-all" id="uc-show-more">Show more</button>
      </section>
      <p class="uc-empty" id="uc-empty" hidden>No use case matches that search. Try a broader word, or <a class="text-link" href="{CAL}" target="_blank" rel="noreferrer">tell me what you need</a> on a free call.</p>
      <p class="uc-noscript-links"><a class="text-link" href="industry/">Browse by industry</a> · <a class="text-link" href="function/">Browse by function</a></p>

      {closing_section()}
    </main>
    <script type="application/json" id="uc-config">{config}</script>
""" + foot(1) + SCRIPTS + LIBRARY_JS + PAGE_END


def dimension_index_page(kind: str, entries: list) -> str:
    is_industry = kind == "industry"
    catalog = INDUSTRIES if is_industry else FUNCTIONS
    counts = industry_counts(entries) if is_industry else function_counts(entries)
    title = f"SI use cases by {'industry' if is_industry else 'function'} | Yonatan Gemmi"
    desc = (
        "Browse the GemmiSI use-case library by industry."
        if is_industry
        else "Browse the GemmiSI use-case library by the kind of job: support, sales, billing, scheduling, and more."
    )
    h1 = "Browse by industry" if is_industry else "Browse by function"
    canon = f"/use-cases/{kind}/"
    listed = [{"slug": slug, "title": info["label"]} for slug, info in catalog.items() if counts[slug]]
    ld_items = [
        {
            "@type": "ListItem",
            "position": i + 1,
            "url": f"{BASE}/use-cases/{kind}/{row['slug']}/",
            "name": row["title"],
        }
        for i, row in enumerate(listed)
    ]
    ld = {
        "@context": "https://schema.org",
        "@graph": [
            crumbs(
                ("Home", BASE + "/"),
                ("Use cases", BASE + "/use-cases/"),
                ("Industries" if is_industry else "Functions", BASE + canon),
            ),
            {
                "@type": "CollectionPage",
                "name": h1,
                "url": BASE + canon,
                "description": desc,
                "isPartOf": {"@type": "WebSite", "name": "Yonatan Gemmi", "url": BASE + "/"},
                "mainEntity": {"@type": "ItemList", "numberOfItems": len(ld_items), "itemListElement": ld_items},
            },
        ],
    }
    cards = []
    for slug, info in catalog.items():
        n = counts[slug]
        if not n:
            continue
        cards.append(
            f'<li class="uc-card"><a href="/use-cases/{kind}/{slug}/">'
            f'<span class="uc-card-cat">{n}</span>'
            f'<h3>{e(info["label"])}</h3>'
            f'<p>{e(info["blurb"])}</p>'
            f'<span class="uc-card-more">View use cases <span aria-hidden="true">→</span></span>'
            f"</a></li>"
        )
    crumb_label = "Industries" if is_industry else "Functions"
    return head(title, desc, canon, 2, ld, compact_ld=True) + f"""
    <main id="top">
      <section class="uc-hero">
{breadcrumb_html(2, [("Home", "../../index.html"), ("Use cases", "../index.html"), (crumb_label, None)])}
        <h1>{e(h1)}</h1>
        <p class="lead">{e(desc)}</p>
      </section>
      <ul class="uc-grid">
          {chr(10) + "          ".join(cards)}
      </ul>
      {closing_section()}
    </main>
""" + foot(2) + SCRIPTS + PAGE_END


def industry_landing(slug: str, entries: list) -> str:
    info = industry_info(slug)
    dedicated_items = dedicated(entries, slug)
    also = cross_tagged(entries, slug)
    all_items = dedicated_items + also
    if not all_items:
        raise SystemExit(f"Refusing empty industry landing {slug}")
    lazy = slug == "any-business"
    visible = dedicated_items[:ANY_VISIBLE] if lazy else dedicated_items
    rest = dedicated_items[ANY_VISIBLE:] if lazy else []
    title = info["seo_title"]
    desc = info["meta"]
    canon = f"/use-cases/industry/{slug}/"
    ld = collection_ld(
        info["seo_h1"],
        BASE + canon,
        desc,
        all_items,
        [
            ("Home", BASE + "/"),
            ("Use cases", BASE + "/use-cases/"),
            (info["label"], BASE + canon),
        ],
    )
    banner = read_first_banner(slug)
    cards = "\n          ".join(card(item) for item in visible)
    compact = ""
    more = ""
    if rest:
        links = "\n          ".join(compact_link(item) for item in rest)
        compact = (
            f'        <ul class="uc-index" aria-label="All {e(info["label"])} use cases">\n'
            f"          {links}\n"
            "        </ul>\n"
        )
        more = (
            f'<button type="button" class="uc-more" id="uc-show-more">Show more</button>'
        )
    also_html = ""
    if also:
        also_cards = "\n          ".join(
            card(item, extra_cls="uc-also", note="A general illustration, not written for this industry.")
            for item in also
        )
        also_html = f"""      <section class="uc-group uc-also-used" aria-labelledby="also-h">
        <div class="uc-group-head">
          <h2 id="also-h">Also used in this kind of business</h2>
          <p>{e(ALSO_USED_NOTE)}</p>
        </div>
        <ul class="uc-grid">
          {also_cards}
        </ul>
      </section>
"""
    foot_note = ""
    if info.get("regulated"):
        foot_note = f'      <p class="uc-cat-foot">{e(info["foot"])}</p>\n'
    body = f'data-uc="industry" data-uc-slug="{slug}"' + (' data-uc-lazy="1"' if lazy else "")
    config = json.dumps(
        {"n": len(dedicated_items), "page": SHOW_MORE, "mode": "industry"},
        ensure_ascii=False,
        separators=(",", ":"),
    )
    config_html = f'    <script type="application/json" id="uc-config">{config}</script>\n' if lazy else ""
    return head(title, desc, canon, 3, ld, compact_ld=True, body_attrs=body) + f"""
    <main id="top">
      <section class="uc-hero">
{breadcrumb_html(3, [("Home", "../../../index.html"), ("Use cases", "../../index.html"), (info["label"], None)])}
        <p class="eyebrow"><span class="status-dot" aria-hidden="true"></span>{len(all_items)} use cases</p>
        <h1>{e(info["seo_h1"])}</h1>
        <p class="lead">{e(info["blurb"])}</p>
      </section>
{banner}      <section class="uc-tools" aria-label="Filter this industry">
        <form class="uc-search" action="/use-cases/" method="get">
          <label for="uc-q" class="visually-hidden">Search use cases</label>
          <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" stroke-width="2"/><path d="M20 20l-4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
          <input type="hidden" name="industry" value="{e(slug)}" />
          <input id="uc-q" name="q" type="search" placeholder="Search this library" autocomplete="off" />
        </form>
        {function_chip_row(entries, industry=slug)}
      </section>
      <section class="uc-group" aria-labelledby="list-h">
        <h2 id="list-h" class="visually-hidden">{e(info["label"])} use cases</h2>
        <ul class="uc-grid" id="uc-grid">
          {cards}
        </ul>
{compact}        {more}
      </section>
{also_html}{foot_note}      {closing_section()}
    </main>
{config_html}""" + foot(3) + SCRIPTS + (LIBRARY_JS if lazy else "") + PAGE_END


def function_landing(slug: str, entries: list) -> str:
    info = function_info(slug)
    items = matching_function(entries, slug)
    if not items:
        raise SystemExit(f"Refusing empty function landing {slug}")
    title = info["seo_title"]
    desc = info["meta"]
    canon = f"/use-cases/function/{slug}/"
    ld = collection_ld(
        info["seo_h1"],
        BASE + canon,
        desc,
        items,
        [
            ("Home", BASE + "/"),
            ("Use cases", BASE + "/use-cases/"),
            (info["label"], BASE + canon),
        ],
    )
    cards = []
    for item in items:
        note = dedicated_note(item)
        extra = ""
        if note:
            extra = note
        cards.append(card(item, note=extra or ""))
    card_html = "\n          ".join(cards)
    return head(
        title,
        desc,
        canon,
        3,
        ld,
        compact_ld=True,
        body_attrs=f'data-uc="function" data-uc-slug="{slug}"',
    ) + f"""
    <main id="top">
      <section class="uc-hero">
{breadcrumb_html(3, [("Home", "../../../index.html"), ("Use cases", "../../index.html"), (info["label"], None)])}
        <p class="eyebrow"><span class="status-dot" aria-hidden="true"></span>{len(items)} use cases</p>
        <h1>{e(info["seo_h1"])}</h1>
        <p class="lead">{e(info["blurb"])}</p>
      </section>
      <section class="uc-tools" aria-label="Combine with an industry">
        <p class="uc-tile-legend">Narrow by industry</p>
        {industry_tiles(entries, extra_query=f"function={slug}")}
      </section>
      <section class="uc-group" aria-labelledby="list-h">
        <h2 id="list-h" class="visually-hidden">{e(info["label"])} use cases</h2>
        <ul class="uc-grid">
          {card_html}
        </ul>
      </section>
      {closing_section()}
    </main>
""" + foot(3) + SCRIPTS + PAGE_END


def related_entries(item: dict, entries: list, cap: int = 3) -> list:
    self_slug = item["slug"]
    ind = set(item["industries"])
    fn = set(item["functions"])
    primary_i = primary_industry(item)
    primary_f = primary_function(item)

    def score(other: dict) -> tuple:
        shared_i = len(ind & set(other["industries"]))
        shared_f = len(fn & set(other["functions"]))
        return (
            1 if primary_industry(other) == primary_i else 0,
            shared_i,
            1 if primary_function(other) == primary_f else 0,
            shared_f,
        )

    others = [other for other in entries if other["slug"] != self_slug]
    others.sort(key=score, reverse=True)
    return others[:cap]


def detail_page(item: dict, entries: list) -> str:
    n = len(entries)
    ind = primary_industry(item)
    info = industry_info(ind)
    url = f"/use-cases/{item['slug']}/"
    title = f"{item['title']} | SI use case | Yonatan Gemmi"
    desc = item["summary"]
    trail = [("Home", BASE + "/"), ("Use cases", BASE + "/use-cases/")]
    if ind != "any-business":
        trail.append((info["label"], BASE + f"/use-cases/industry/{ind}/"))
    trail.append((item["title"], BASE + url))
    ld = {
        "@context": "https://schema.org",
        "@graph": [
            crumbs(*trail),
            {
                "@type": "WebPage",
                "name": item["title"],
                "url": BASE + url,
                "description": desc,
                "isPartOf": {"@type": "CollectionPage", "name": "SI use cases", "url": BASE + "/use-cases/"},
                "author": {"@type": "Person", "name": "Yonatan Gemmi", "url": BASE + "/"},
            },
        ],
    }
    related = related_entries(item, entries)
    related_html = "\n          ".join(card(other) for other in related)
    checks = "\n            ".join(f"<li>{e(line)}</li>" for line in item["human_checks"])
    examples = "\n            ".join(
        f'<li class="uc-ex"><span class="uc-ex-type">{e(ex["business_type"])}</span><p>{e(ex["scenario"])}</p></li>'
        for ex in item["examples"]
    )
    caution = ""
    if (item.get("caution") or "").strip():
        caution = f'<p class="uc-caution" role="note"><strong>Worth knowing:</strong> {e(item["caution"])}</p>'
    legal_note = ""
    if info.get("regulated"):
        legal_note = f'<p class="uc-read-first" role="note">{e(info["short"])}</p>\n          '
    tools = "".join(f'<span class="tag green">{e(tool)}</span>' for tool in item["tools_examples"])
    graphic = motif_html(item)
    crumb_items = [("Home", "../../index.html"), ("Use cases", "../index.html")]
    if ind != "any-business":
        crumb_items.append((info["label"], f"../industry/{ind}/"))
    crumb_items.append((item["title"], None))
    tags = []
    if ind != "any-business":
        tags.append(f'<a href="../industry/{e(ind)}/">{e(info["label"])}</a>')
    for fn in item["functions"]:
        tags.append(f'<a href="../function/{e(fn)}/">{e(function_info(fn)["label"])}</a>')
    tag_html = ' <span aria-hidden="true">·</span> '.join(tags)
    return head(title, desc, url, 2, ld) + f"""
    <main id="top">
      <article class="uc-detail">
        <header class="uc-detail-head">
{breadcrumb_html(2, crumb_items)}
          <div class="uc-detail-intro">
            <div class="uc-detail-copy">
              <p class="uc-card-cat">{tag_html}</p>
              <h1>{e(item['title'])}</h1>
              <p class="lead">{e(item['summary'])}</p>
              {legal_note}{caution}
            </div>
            {graphic}
          </div>
        </header>

        <div class="uc-detail-body">
          <div class="uc-detail-main">
            <section class="uc-block" aria-labelledby="problem">
              <h2 id="problem">The problem</h2>
              <p>{e(item['problem'])}</p>
            </section>
            <section class="uc-block" aria-labelledby="what">
              <h2 id="what">What SI does</h2>
              <p>{e(item['what_si_does'])}</p>
            </section>
            <section class="uc-block" aria-labelledby="examples">
              <h2 id="examples">Examples</h2>
              <p class="uc-ex-intro">The same job looks different in different businesses. These are illustrations, not client results.</p>
              <ul class="uc-examples">
            {examples}
              </ul>
            </section>
            <section class="uc-block" aria-labelledby="setup">
              <h2 id="setup">What it takes to set up</h2>
              <p>{e(item['setup'])}</p>
            </section>
            <section class="uc-block uc-checks" aria-labelledby="checks">
              <h2 id="checks">What a human still checks</h2>
              <ul class="uc-checklist">
            {checks}
              </ul>
            </section>
            <section class="uc-block" aria-labelledby="prompt">
              <h2 id="prompt">Try it yourself</h2>
              <p>Paste this into your SI tool of choice and swap the [bracketed] parts for your own details. It asks SI to stop and show you before it does anything.</p>
              <div class="uc-prompt">
                <div class="uc-prompt-bar">
                  <span class="uc-prompt-label">Copy-ready prompt</span>
                  <button type="button" class="uc-copy" id="uc-copy" aria-live="polite">Copy</button>
                </div>
                <pre id="uc-prompt-text">{e(item['copy_prompt'])}</pre>
              </div>
            </section>
          </div>

          <aside class="uc-detail-side" aria-label="At a glance">
            <div class="uc-side-stick">
            <div class="uc-side-card">
              <h3>Typical effect</h3>
              <p>{e(item.get('effect', ''))}</p>
              <h3>Tools it usually touches</h3>
              <div class="uc-tags">{tools}</div>
            </div>
            <div class="uc-side-card uc-side-cta">
              <p class="section-kicker">Want this built?</p>
              <p>I will look at your setup on a free call and tell you honestly whether this is worth doing.</p>
              <a class="button primary full" href="{CAL}" target="_blank" rel="noreferrer">{CTA}</a>
            </div>
            </div>
          </aside>
        </div>

        <section class="uc-related" aria-labelledby="related">
          <h2 id="related">Related use cases</h2>
          <ul class="uc-grid">
          {related_html}
          </ul>
          <p class="uc-all"><a class="text-link" href="../index.html">See all {n} use cases →</a></p>
        </section>

        <section class="uc-cta-band" aria-labelledby="cta-h">
          <div>
            <p class="section-kicker">Next step</p>
            <h2 id="cta-h">Want this built? Book a free 30-minute consult</h2>
            <p>Bring one real example, such as an export, an inbox, or a spreadsheet. We will map the steps and decide what SI drafts and what you approve.</p>
          </div>
          <div class="actions"><a class="button primary" href="{CAL}" target="_blank" rel="noreferrer">{CTA}</a></div>
        </section>
      </article>
    </main>
""" + foot(2) + SCRIPTS + """  <script>
    (() => {
      const button = document.getElementById('uc-copy');
      const text = document.getElementById('uc-prompt-text');
      if (!button || !text) return;
      button.addEventListener('click', async () => {
        const value = text.textContent || '';
        try {
          await navigator.clipboard.writeText(value);
        } catch (err) {
          const range = document.createRange();
          range.selectNodeContents(text);
          const selection = getSelection();
          selection.removeAllRanges();
          selection.addRange(range);
          document.execCommand('copy');
          selection.removeAllRanges();
        }
        button.textContent = 'Copied';
        button.classList.add('is-done');
        window.setTimeout(() => {
          button.textContent = 'Copy';
          button.classList.remove('is-done');
        }, 1800);
      });
    })();
  </script>
""" + PAGE_END


def url_block(loc: str, priority: str) -> str:
    lastmod = date.today().isoformat()
    return (
        "  <url>\n"
        f"    <loc>{loc}</loc>\n"
        f"    <lastmod>{lastmod}</lastmod>\n"
        "    <changefreq>monthly</changefreq>\n"
        f"    <priority>{priority}</priority>\n"
        "  </url>\n"
    )


def update_sitemap(entries: list) -> None:
    text = SITEMAP.read_text(encoding="utf-8")
    text = re.sub(
        r"\n  <url>\s*<loc>https://[^<]*/use-cases/.*?</url>",
        "",
        text,
        flags=re.S,
    )
    blocks = [url_block(f"{BASE}/use-cases/", "0.8")]
    blocks.append(url_block(f"{BASE}/use-cases/industry/", "0.7"))
    blocks.append(url_block(f"{BASE}/use-cases/function/", "0.7"))
    for slug in INDUSTRIES:
        if matching_industry(entries, slug):
            blocks.append(url_block(f"{BASE}/use-cases/industry/{slug}/", "0.7"))
    for slug in FUNCTIONS:
        if matching_function(entries, slug):
            blocks.append(url_block(f"{BASE}/use-cases/function/{slug}/", "0.7"))
    blocks.extend(url_block(f"{BASE}/use-cases/{item['slug']}/", "0.6") for item in entries)
    if "</urlset>" not in text:
        raise SystemExit("sitemap.xml is missing </urlset>")
    text = text.replace("</urlset>", "".join(blocks) + "</urlset>")
    SITEMAP.write_text(text, encoding="utf-8")


def assert_wording(entries: list) -> None:
    library = (OUT / "index.html").read_text(encoding="utf-8")
    ai_hits = re.findall(r"\bAI\b", library)
    if ai_hits != ["AI"] or "formerly called AI" not in library:
        raise SystemExit(f"Library intro must mention formerly called AI exactly once, found {ai_hits}")
    if "noindex" in library:
        raise SystemExit("Library page must be indexable")
    if "Read this first." in library:
        raise SystemExit("Hub must stay a light page: regulated banners belong on industry landings")
    size = len(library.encode("utf-8"))
    if size < HUB_MIN_BYTES or size > HUB_MAX_BYTES:
        raise SystemExit(f"Hub HTML must be {HUB_MIN_BYTES}-{HUB_MAX_BYTES} bytes, found {size}")
    if library.count('class="uc-card') < 12:
        raise SystemExit("Hub must include about 12 featured cards")
    if "More filters" in library:
        raise SystemExit("Hub must not hide function filters behind More filters")
    if 'data-industry=' not in library or 'id="uc-functions"' not in library:
        raise SystemExit("Hub needs industry tiles and visible function filter chips")
    if "uc-card-note" in library:
        raise SystemExit("Hub cards must not include regulated-industry disclaimer notes")
    if "Browse the use cases" in library:
        raise SystemExit("Hub hero must not include the Browse the use cases button")
    if library.count("cloudflareinsights.com/beacon.min.js") != 1:
        raise SystemExit("Hub must include exactly one Cloudflare Web Analytics beacon")
    if "data-hay=" in library:
        raise SystemExit("Library page must not inline search haystacks")
    if 'id="uc-show-more"' not in library:
        raise SystemExit("Library page needs a show-more control")
    index_path = OUT / "search.json"
    if not index_path.exists():
        raise SystemExit("use-cases/search.json is missing")
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    records = payload["items"]
    if len(records) != len(entries):
        raise SystemExit(f"search.json has {len(records)} items, expected {len(entries)}")
    record_slugs = {row["s"] for row in records}
    sitemap = SITEMAP.read_text(encoding="utf-8")
    for item in entries:
        if item["slug"] not in record_slugs:
            raise SystemExit(f"search.json is missing {item['slug']}")
        landing = OUT / "industry" / primary_industry(item) / "index.html"
        if not landing.exists() or f"/use-cases/{item['slug']}/" not in landing.read_text(encoding="utf-8"):
            raise SystemExit(f"Primary industry landing is missing a crawlable link for {item['slug']}")
        if f"{BASE}/use-cases/{item['slug']}/" not in sitemap:
            raise SystemExit(f"sitemap is missing {item['slug']}")
        page = (OUT / item["slug"] / "index.html").read_text(encoding="utf-8")
        if re.search(r"\bAI\b", page) or "noindex" in page or "Nous" in page or "Brandgate" in page:
            raise SystemExit(f"Wording check failed for {item['slug']}")
        if page.count("cloudflareinsights.com/beacon.min.js") != 1:
            raise SystemExit(f"{item['slug']} must include exactly one Cloudflare beacon")
        if 'class="uc-motif' not in page or "aria-hidden" not in page:
            raise SystemExit(f"{item['slug']} is missing the decorative motif")
        graphic = page.split('class="uc-motif', 1)[1].split("</div>\n          </div>", 1)[0]
        if "<text" in graphic:
            raise SystemExit(f"{item['slug']} motif must not contain text")
        ind = primary_industry(item)
        info = industry_info(ind)
        if info.get("regulated"):
            if e(info["short"]) not in page:
                raise SystemExit(f"{item['slug']} is missing the short industry disclaimer")
            if OWN_ACCOUNTS not in page:
                raise SystemExit(f"{item['slug']} is missing the own-equipment setup line")
        if ind == "medical" and re.search(r"diagnose", page, re.I):
            raise SystemExit(f"{item['slug']} page must not use the word diagnose")
        if ind == "any-business" and f"/use-cases/industry/{ind}/" in page.split("breadcrumb", 1)[-1].split("</nav>", 1)[0]:
            raise SystemExit(f"{item['slug']} breadcrumb should skip the Any business crumb")
    for slug, info in INDUSTRIES.items():
        path = OUT / "industry" / slug / "index.html"
        if not matching_industry(entries, slug):
            if path.exists():
                raise SystemExit(f"Empty industry landing should not exist: {slug}")
            continue
        html_page = path.read_text(encoding="utf-8")
        if html_page.count("cloudflareinsights.com/beacon.min.js") != 1:
            raise SystemExit(f"{slug} landing must include exactly one Cloudflare beacon")
        if info.get("regulated"):
            if "Read this first." not in html_page:
                raise SystemExit(f"{slug} landing is missing the full disclaimer")
            if OWN_ACCOUNTS not in html_page:
                raise SystemExit(f"{slug} landing is missing the own-equipment line")
            for needle in info.get("needles") or ():
                if needle not in html_page:
                    raise SystemExit(f"{slug} landing is missing expected disclaimer text")
            if cross_tagged(entries, slug) and "Also used in this kind of business" not in html_page:
                raise SystemExit(f"{slug} landing needs the Also used section")
        if f"{BASE}/use-cases/industry/{slug}/" not in sitemap:
            raise SystemExit(f"sitemap is missing industry/{slug}")
    for slug in FUNCTIONS:
        path = OUT / "function" / slug / "index.html"
        if matching_function(entries, slug):
            if f"{BASE}/use-cases/function/{slug}/" not in sitemap:
                raise SystemExit(f"sitemap is missing function/{slug}")
            html_page = path.read_text(encoding="utf-8")
            if html_page.count("cloudflareinsights.com/beacon.min.js") != 1:
                raise SystemExit(f"function/{slug} landing must include exactly one Cloudflare beacon")
        elif path.exists():
            raise SystemExit(f"Empty function landing should not exist: {slug}")


def write_tree(entries: list) -> None:
    if OUT.exists():
        for path in OUT.rglob("*"):
            if path.is_file():
                path.unlink()
        for path in sorted(OUT.rglob("*"), reverse=True):
            if path.is_dir():
                path.rmdir()
    OUT.mkdir(parents=True, exist_ok=True)
    write_search_index(entries)
    (OUT / "index.html").write_text(library_page(entries), encoding="utf-8")
    (OUT / "industry").mkdir(parents=True, exist_ok=True)
    (OUT / "function").mkdir(parents=True, exist_ok=True)
    (OUT / "industry" / "index.html").write_text(dimension_index_page("industry", entries), encoding="utf-8")
    (OUT / "function" / "index.html").write_text(dimension_index_page("function", entries), encoding="utf-8")
    for slug in INDUSTRIES:
        if matching_industry(entries, slug):
            folder = OUT / "industry" / slug
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "index.html").write_text(industry_landing(slug, entries), encoding="utf-8")
    for slug in FUNCTIONS:
        if matching_function(entries, slug):
            folder = OUT / "function" / slug
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "index.html").write_text(function_landing(slug, entries), encoding="utf-8")
    for item in entries:
        folder = OUT / item["slug"]
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "index.html").write_text(detail_page(item, entries), encoding="utf-8")


def main() -> None:
    entries = load()
    write_tree(entries)
    update_sitemap(entries)
    assert_wording(entries)
    sizes = [motif_bytes(item) for item in entries]
    motifs = Counter(pick_motif(item) for item in entries)
    industries = Counter(pick_industry(item)[0] for item in entries)
    hub = len((OUT / "index.html").read_bytes())
    print(f"built {len(entries)} use cases")
    print(f"hub bytes={hub}")
    print("motifs " + " ".join(f"{name}={motifs[name]}" for name in sorted(motifs)))
    print("motif-industries " + " ".join(f"{name}={industries[name]}" for name in sorted(industries)))
    print(
        "graphic bytes min={0} median={1} max={2}".format(
            min(sizes), sorted(sizes)[len(sizes) // 2], max(sizes)
        )
    )


if __name__ == "__main__":
    main()
