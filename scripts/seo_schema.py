#!/usr/bin/env python3
"""Shared JSON-LD and head-tag fragments for the public GitHub Pages site."""
from __future__ import annotations

import json

BASE = "https://nykon1293.github.io"
PERSON_ID = f"{BASE}/#person"
BUSINESS_ID = f"{BASE}/#business"
WEBSITE_ID = f"{BASE}/#website"
CALENDLY = "https://calendly.com/josh-gemmi/30min"
OG_IMAGE = f"{BASE}/assets/social-preview.png"
PORTRAIT = f"{BASE}/assets/yonatan-gemmi-pixel-portrait-256.png"
OG_IMAGE_ALT = "Yonatan Gemmi — AI, automation, dashboards, and technical operations"

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
    {"@type": "Place", "name": "Remote"},
]


def _offer(name: str, url: str, *, price: str | None = None, service: str, description: str | None = None) -> dict:
    item: dict = {
        "@type": "Offer",
        "name": name,
        "url": url,
        "itemOffered": {"@type": "Service", "name": service},
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
        "name": "Yonatan Gemmi",
        "url": f"{BASE}/",
        "image": PORTRAIT,
        "email": "mailto:josh.gemmi@gmail.com",
        "jobTitle": "Technical Operations and AI Implementation Specialist",
        "worksFor": {"@id": BUSINESS_ID},
        "address": {
            "@type": "PostalAddress",
            "addressLocality": "North Miami Beach",
            "addressRegion": "FL",
            "addressCountry": "US",
        },
        "areaServed": AREA_SERVED,
        "sameAs": [
            "https://www.linkedin.com/in/joshuah-gemmi-16046233/",
            "https://github.com/nykon1293",
        ],
        "knowsAbout": [
            "Hermes Agents",
            "Hermes Desk setup",
            "AI implementation",
            "workflow automation",
            "technical operations",
            "data dashboards",
            "ecommerce operations",
            "Shopify inventory",
            "Stocky dump recovery",
            "Custom GPTs",
            "ChatGPT workflows",
            "technical tutoring",
            "Google BigQuery",
            "Amazon FBA",
            "eBay operations",
        ],
    }


def professional_service_node(*, include_catalog: bool = True) -> dict:
    node: dict = {
        "@type": "ProfessionalService",
        "@id": BUSINESS_ID,
        "name": "Yonatan Gemmi",
        "alternateName": "Yonatan Gemmi AI and operations",
        "url": f"{BASE}/",
        "image": OG_IMAGE,
        "logo": PORTRAIT,
        "email": "josh.gemmi@gmail.com",
        "description": (
            "AI implementation, workflow automation, dashboards, ecommerce operations, "
            "Hermes Desk setups, tutoring, and Stocky dump recovery. Based in North Miami Beach. "
            "Serves Miami-Dade, Broward, South Florida, and remote clients."
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
        "founder": {"@id": PERSON_ID},
        "employee": {"@id": PERSON_ID},
        "sameAs": [
            "https://www.linkedin.com/in/joshuah-gemmi-16046233/",
            "https://github.com/nykon1293",
        ],
        "contactPoint": {
            "@type": "ContactPoint",
            "contactType": "sales",
            "email": "josh.gemmi@gmail.com",
            "url": CALENDLY,
            "availableLanguage": "English",
        },
    }
    if include_catalog:
        node["hasOfferCatalog"] = {
            "@type": "OfferCatalog",
            "name": "Desks, Discovery, tutoring, and consultation",
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
        "name": "Yonatan Gemmi",
        "inLanguage": "en-US",
        "publisher": {"@id": PERSON_ID},
        "about": {"@id": BUSINESS_ID},
    }


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
        "provider": {"@id": PERSON_ID},
        "areaServed": AREA_SERVED,
        "isRelatedTo": {"@id": BUSINESS_ID},
    }


def graph_payload(nodes: list[dict]) -> str:
    payload = {"@context": "https://schema.org", "@graph": nodes}
    return json.dumps(payload, indent=2, ensure_ascii=False)


def common_head_tags(*, title: str, description: str, canonical: str, og_type: str = "website") -> str:
    """Meta tags that should appear on every public HTML page after robots/author."""
    return f"""  <meta property="og:title" content="{title}" />
  <meta property="og:description" content="{description}" />
  <meta property="og:type" content="{og_type}" />
  <meta property="og:url" content="{canonical}" />
  <meta property="og:site_name" content="Yonatan Gemmi" />
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
