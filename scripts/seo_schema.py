#!/usr/bin/env python3
"""Shared JSON-LD and head-tag fragments for the public GitHub Pages site."""
from __future__ import annotations

import json
import re
from pathlib import Path

BASE = "https://gemmisi.com"
PERSON_ID = f"{BASE}/#person"
BUSINESS_ID = f"{BASE}/#business"
WEBSITE_ID = f"{BASE}/#website"
CALENDLY = "https://calendly.com/josh-gemmi/30min"
LINKEDIN = "https://www.linkedin.com/in/joshuah-gemmi-16046233/"
GITHUB = "https://github.com/nykon1293"
OG_IMAGE = f"{BASE}/assets/brand/gemmisi-og.png"
PORTRAIT = f"{BASE}/assets/yonatan-gemmi-pixel-portrait-256.png"
LOGO = f"{BASE}/assets/brand/gemmisi-icon-512.png"
OG_IMAGE_ALT = "GemmiSI — SI & AI, automation, dashboards, and technical operations"
SITE_NAME = "GemmiSI"
SITE_ALTERNATE_NAME = "GemmiSI - Super Intelligence (SI) AI implementation"
THEME_COLOR = "#d3aa55"
BACKGROUND_COLOR = "#080b0a"
OWN_EQUIPMENT = (
    "GemmiSI sets this up on your own equipment and accounts; your data stays with you."
)
SI_GLOSS = "SI (Super Intelligence, the new name for AI)"
APPROVAL_LINE = (
    "Anything that sends, pays, orders, posts, or changes a record waits for your approval."
)

KNOWS_ABOUT = [
    "SI",
    "Super Intelligence",
    "AI automation",
    "AI agents",
    "dashboards",
    "ecommerce operations",
    "Hermes Agents",
    "Hermes Desk setup",
    "SI implementation",
    "workflow automation",
    "technical operations",
    "data dashboards",
    "Shopify inventory",
    "Stocky dump recovery",
    "Custom GPTs",
    "ChatGPT workflows",
    "technical tutoring",
    "Google BigQuery",
    "Amazon FBA",
    "eBay operations",
]

AREA_SERVED = [
    {
        "@type": "City",
        "name": "North Miami Beach",
        "containedInPlace": {
            "@type": "State",
            "name": "Florida",
            "addressCountry": "US",
        },
    },
    {"@type": "AdministrativeArea", "name": "Miami-Dade County"},
    {"@type": "AdministrativeArea", "name": "Broward County"},
    {"@type": "AdministrativeArea", "name": "South Florida"},
    {"@type": "Country", "name": "United States"},
    {"@type": "Place", "name": "Remote"},
]


def clip_meta(text: str, limit: int = 155) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rsplit(" ", 1)[0].rstrip(",.;:") + "…"


def with_si_ai(text: str) -> str:
    """Put the searchable AI synonym on the first SI (titles and meta)."""
    if re.search(r"\bSI \(AI\)", text):
        return text
    if re.search(r"\bSI\b", text):
        return re.sub(r"\bSI\b", "SI (AI)", text, count=1)
    if re.search(r"\bAI\b", text) and "SI" not in text:
        return re.sub(r"\bAI\b", "SI (AI)", text, count=1)
    return f"SI (AI): {text}"


def with_si_gloss(text: str) -> str:
    """First body mention: SI as Super Intelligence, the new name for AI."""
    if "Super Intelligence" in text:
        return text
    if re.search(r"\bSI\b", text):
        return re.sub(r"\bSI\b", SI_GLOSS, text, count=1)
    return f"{SI_GLOSS} can help with this kind of work. {text}"


def use_case_seo_title(title: str) -> str:
    """Lead the qualifier with SI, add AI, brand as GemmiSI. Prefer ≤60 characters."""
    name = re.sub(r"^(A|An|The) ", "", title).strip()
    style_a = f"{name} with SI (AI) | GemmiSI Use Cases"
    style_b = f"{name} | SI (AI) | GemmiSI"
    if len(style_a) <= 60:
        return style_a
    if len(style_b) <= 60:
        return style_b
    suffix = " | SI (AI) | GemmiSI"
    words = name.split()
    dangling = {"that", "the", "and", "for", "of", "to", "a", "an", "or", "with", "from", "into"}
    while len(" ".join(words)) + len(suffix) > 60 and len(words) > 2:
        words = words[:-1]
        while words and words[-1].lower().rstrip(",.;:") in dangling:
            words = words[:-1]
    short = " ".join(words)
    candidate = f"{short}{suffix}"
    if len(candidate) > 60:
        budget = max(12, 60 - len(suffix))
        short = short[:budget].rsplit(" ", 1)[0]
        candidate = f"{short}{suffix}"
    return candidate


def use_case_seo_titles(entries: list[dict]) -> dict[str, str]:
    """Unique document titles; disambiguate with industry or slug if a short form collides."""
    assigned: dict[str, str] = {}
    used: set[str] = set()
    suffix = " | SI (AI) | GemmiSI"
    for item in entries:
        candidate = use_case_seo_title(item["title"])
        if candidate.casefold() in used:
            industry = str((item.get("industries") or ["use-case"])[0]).replace("-", " ")
            stem = re.sub(r"( with SI \(AI\) \| GemmiSI Use Cases| \| SI \(AI\) \| GemmiSI)$", "", candidate)
            tag = f" ({industry})"
            words = stem.split()
            dangling = {"that", "the", "and", "for", "of", "to", "a", "an", "or", "with", "from", "into"}
            while words and len(" ".join(words)) + len(tag) + len(suffix) > 60:
                words.pop()
                while words and words[-1].lower().rstrip(",.;:") in dangling:
                    words.pop()
            candidate = f"{' '.join(words)}{tag}{suffix}"
        if candidate.casefold() in used or len(candidate) > 60:
            slug_words = item["slug"].replace("-", " ")
            candidate = f"{slug_words}{suffix}"
            if len(candidate) > 60:
                budget = 60 - len(suffix)
                candidate = f"{slug_words[:budget].rsplit(' ', 1)[0]}{suffix}"
        used.add(candidate.casefold())
        assigned[item["slug"]] = candidate
    return assigned


def use_case_seo_desc(summary: str) -> str:
    return clip_meta(with_si_ai(summary))


def _offer(name: str, url: str, *, price: str | None = None, service: str, description: str | None = None) -> dict:
    item: dict = {
        "@type": "Offer",
        "name": name,
        "url": url,
        "offeredBy": {"@id": BUSINESS_ID},
        "seller": {"@id": BUSINESS_ID},
        "itemOffered": {
            "@type": "Service",
            "name": service,
            "provider": {"@id": BUSINESS_ID},
        },
    }
    if price is not None:
        item["price"] = price
        item["priceCurrency"] = "USD"
    if description:
        item["description"] = description
    return item


def person_node() -> dict:
    return {
        "@type": "Person",
        "@id": PERSON_ID,
        "name": "Yonatan (Josh) Gemmi",
        "alternateName": "Josh Gemmi",
        "url": f"{BASE}/",
        "image": PORTRAIT,
        "email": "mailto:y@gemmisi.com",
        "jobTitle": "Technical Operations and SI Implementation Specialist",
        "worksFor": {"@id": BUSINESS_ID},
        "address": {
            "@type": "PostalAddress",
            "addressLocality": "North Miami Beach",
            "addressRegion": "FL",
            "addressCountry": "US",
        },
        "areaServed": AREA_SERVED,
        "sameAs": [
            LINKEDIN,
            GITHUB,
        ],
        "knowsAbout": KNOWS_ABOUT,
    }


def professional_service_node(*, include_catalog: bool = True) -> dict:
    node: dict = {
        "@type": ["ProfessionalService", "Organization"],
        "@id": BUSINESS_ID,
        "name": SITE_NAME,
        "alternateName": SITE_ALTERNATE_NAME,
        "url": f"{BASE}/",
        "image": OG_IMAGE,
        "logo": {
            "@type": "ImageObject",
            "url": LOGO,
            "width": 512,
            "height": 512,
        },
        "email": "y@gemmisi.com",
        "description": (
            "SI (Super Intelligence, also known as AI) implementation, AI automation, "
            "AI agents, dashboards, ecommerce operations, Hermes Desk setups, tutoring, "
            "and Stocky dump recovery. Based in North Miami Beach. Serves Miami-Dade, "
            "Broward, South Florida, the United States, and remote clients."
        ),
        "priceRange": "$$",
        "currenciesAccepted": "USD",
        "address": {
            "@type": "PostalAddress",
            "addressLocality": "North Miami Beach",
            "addressRegion": "FL",
            "addressCountry": "US",
        },
        "areaServed": AREA_SERVED,
        "founder": {
            "@type": "Person",
            "@id": PERSON_ID,
            "name": "Josh Gemmi",
            "alternateName": "Yonatan (Josh) Gemmi",
        },
        "employee": {"@id": PERSON_ID},
        "knowsAbout": KNOWS_ABOUT,
        "sameAs": [
            LINKEDIN,
            GITHUB,
        ],
        "contactPoint": {
            "@type": "ContactPoint",
            "contactType": "sales",
            "email": "y@gemmisi.com",
            "url": CALENDLY,
            "availableLanguage": "English",
        },
    }
    if include_catalog:
        node["hasOfferCatalog"] = {
            "@type": "OfferCatalog",
            "name": "Desks, Discovery, Care, tutoring, and consultation",
            "itemListElement": [
                _offer(
                    "Free 30-minute consultation",
                    CALENDLY,
                    price="0",
                    service="30-minute consultation",
                    description="Google Meet. Direction on the simplest next step. Not paid Discovery.",
                ),
                _offer(
                    "Starter Desk",
                    f"{BASE}/pricing.html#desks",
                    price="500",
                    service="Starter Desk Hermes setup",
                ),
                _offer(
                    "Operator Desk",
                    f"{BASE}/pricing.html#desks",
                    price="1500",
                    service="Operator Desk Hermes setup",
                ),
                _offer(
                    "Connected Desk",
                    f"{BASE}/pricing.html#desks",
                    price="3500",
                    service="Connected Desk Hermes setup",
                ),
                _offer(
                    "Paid Discovery",
                    f"{BASE}/pricing.html#consulting",
                    price="2000",
                    service="Paid workflow discovery",
                    description=(
                        "One workflow mapped for custom work such as a dashboard, system "
                        "integration, report, automation, or cleanup, with a written next-step quote."
                    ),
                ),
                _offer(
                    "Care retainer — Owner",
                    f"{BASE}/pricing.html#retainers",
                    price="300",
                    service="Monthly Care retainer — Owner",
                ),
                _offer(
                    "Care retainer — Starter",
                    f"{BASE}/pricing.html#retainers",
                    price="750",
                    service="Monthly Care retainer — Starter",
                ),
                _offer(
                    "Care retainer — Operator",
                    f"{BASE}/pricing.html#retainers",
                    price="1500",
                    service="Monthly Care retainer — Operator",
                ),
                _offer(
                    "Tutoring",
                    f"{BASE}/pricing.html#tutoring",
                    price="125",
                    service="Tutoring and pairing",
                    description="$125 per hour. Minimum booking 90 minutes at $175.",
                ),
            ],
        }
    return node


def website_node() -> dict:
    return {
        "@type": "WebSite",
        "@id": WEBSITE_ID,
        "url": f"{BASE}/",
        "name": SITE_NAME,
        "alternateName": SITE_ALTERNATE_NAME,
        "inLanguage": "en-US",
        "publisher": {"@id": BUSINESS_ID},
        "about": {"@id": BUSINESS_ID},
    }


def sitewide_nodes(*, include_catalog: bool = False) -> list[dict]:
    return [
        website_node(),
        person_node(),
        professional_service_node(include_catalog=include_catalog),
    ]


def webpage_node(*, name: str, url: str, description: str, extra: dict | None = None) -> dict:
    node = {
        "@type": "WebPage",
        "@id": f"{url}#webpage",
        "url": url,
        "name": name,
        "description": description,
        "isPartOf": {"@id": WEBSITE_ID},
        "about": {"@id": BUSINESS_ID},
        "inLanguage": "en-US",
    }
    if extra:
        node.update(extra)
    return node


def breadcrumb_node(items: list[tuple[str, str | None]]) -> dict:
    elements = []
    for i, (name, url) in enumerate(items, start=1):
        item: dict = {"@type": "ListItem", "position": i, "name": name}
        if url:
            item["item"] = url
        elements.append(item)
    return {
        "@type": "BreadcrumbList",
        "itemListElement": elements,
    }


def faq_node(faqs: list[tuple[str, str]]) -> dict:
    return {
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            }
            for q, a in faqs
        ],
    }


def service_node(*, name: str, description: str, url: str) -> dict:
    return {
        "@type": "Service",
        "name": name,
        "description": description,
        "url": url,
        "serviceType": [name, "SI automation", "AI automation"],
        "provider": {"@id": BUSINESS_ID},
        "brand": {"@id": BUSINESS_ID},
        "areaServed": AREA_SERVED,
        "isRelatedTo": {"@id": BUSINESS_ID},
    }


CSS_VERSION = "uc-motifs-2"


def graph_payload(nodes: list[dict]) -> str:
    payload = {"@context": "https://schema.org", "@graph": nodes}
    return json.dumps(payload, indent=2, ensure_ascii=False)


def _font_face_css() -> str:
    raw = (Path(__file__).resolve().parent.parent / "assets" / "fonts.css").read_text(encoding="utf-8")
    raw = re.sub(r"/\*.*?\*/", "", raw, flags=re.S)
    return re.sub(r"\s+", " ", raw).strip()


def font_and_css_links(*, stylesheet: str, extra_css: str | None = None) -> str:
    """Preload Plex, inline @font-face, then site CSS. Replaces the Google Fonts <link>s."""
    lines = [
        '  <link rel="preload" href="/assets/fonts/ibm-plex-sans-latin.woff2" as="font" type="font/woff2" crossorigin />',
        f"  <style>{_font_face_css()}</style>",
        f'  <link rel="stylesheet" href="{stylesheet}" />',
    ]
    if extra_css:
        lines.append(f'  <link rel="stylesheet" href="{extra_css}" />')
    return "\n".join(lines)


NAV_SCRIPT = '  <script src="/assets/nav.js" defer></script>\n'
# Module beacon: async, non-blocking. Place immediately before </body> on public pages only.
CLOUDFLARE_WEB_ANALYTICS = (
    "<!-- Cloudflare Web Analytics --><script type='module' src='https://static.cloudflareinsights.com/beacon.min.js' "
    "data-cf-beacon='{\"token\": \"c9c911628ffd4644bce7bea8d47eb16c\"}'></script><!-- End Cloudflare Web Analytics -->\n"
)

ICON_BLOCK_RE = re.compile(
    r'  <link rel="icon" href="/favicon\.ico"[^>]*>\n'
    r'(?:  <link rel="(?:icon|apple-touch-icon)"[^>]*>\n)*'
    r'(?:  <link rel="manifest" href="/site\.webmanifest" />\n)?'
    r'(?:  <meta name="theme-color"[^>]*>\n)?'
)


def icon_links() -> str:
    """Favicon, apple touch, manifest, and theme color used on every public page."""
    return f"""  <link rel="icon" href="/favicon.ico" sizes="any" />
  <link rel="icon" href="/assets/brand/gemmisi-icon.svg" type="image/svg+xml" />
  <link rel="icon" href="/assets/brand/gemmisi-icon-16.png" type="image/png" sizes="16x16" />
  <link rel="icon" href="/assets/brand/gemmisi-icon-32.png" type="image/png" sizes="32x32" />
  <link rel="icon" href="/assets/brand/gemmisi-icon-48.png" type="image/png" sizes="48x48" />
  <link rel="icon" href="/assets/brand/gemmisi-icon-96.png" type="image/png" sizes="96x96" />
  <link rel="icon" href="/assets/brand/gemmisi-icon-192.png" type="image/png" sizes="192x192" />
  <link rel="apple-touch-icon" href="/assets/brand/gemmisi-icon-180.png" />
  <link rel="manifest" href="/site.webmanifest" />
  <meta name="theme-color" content="{THEME_COLOR}" />"""


def replace_icon_links(html: str) -> str:
    updated, count = ICON_BLOCK_RE.subn(icon_links() + "\n", html, count=1)
    if count != 1:
        raise SystemExit(f"expected 1 favicon block, found {count}")
    return updated


def common_head_tags(*, title: str, description: str, canonical: str, og_type: str = "website") -> str:
    """Meta tags that should appear on every public HTML page after robots/author."""
    return f"""  <meta property="og:title" content="{title}" />
  <meta property="og:description" content="{description}" />
  <meta property="og:type" content="{og_type}" />
  <meta property="og:url" content="{canonical}" />
  <meta property="og:site_name" content="{SITE_NAME}" />
  <meta property="og:locale" content="en_US" />
  <meta property="og:image" content="{OG_IMAGE}" />
  <meta property="og:image:width" content="1200" />
  <meta property="og:image:height" content="630" />
  <meta property="og:image:alt" content="{OG_IMAGE_ALT}" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{title}" />
  <meta name="twitter:description" content="{description}" />
  <meta name="twitter:image" content="{OG_IMAGE}" />
  <meta name="twitter:image:alt" content="{OG_IMAGE_ALT}" />
  <link rel="sitemap" type="application/xml" title="Sitemap" href="{BASE}/sitemap.xml" />"""


def service_page_graph(
    *,
    service_name: str,
    meta_description: str,
    canonical: str,
    page_name: str,
    faqs: list[tuple[str, str]],
    breadcrumb_label: str,
) -> str:
    nodes = [
        website_node(),
        person_node(),
        professional_service_node(),
        webpage_node(name=page_name, url=canonical, description=meta_description),
        breadcrumb_node(
            [
                ("Home", f"{BASE}/"),
                (breadcrumb_label, canonical),
            ]
        ),
        service_node(name=service_name, description=meta_description, url=canonical),
        faq_node(faqs),
    ]
    return graph_payload(nodes)
