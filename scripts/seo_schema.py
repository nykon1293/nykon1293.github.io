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
LINKEDIN_COMPANY = "https://www.linkedin.com/company/gemmisi/"
FACEBOOK = "https://www.facebook.com/1392236803978006"
GITHUB = "https://github.com/nykon1293"
SAME_AS = [LINKEDIN, LINKEDIN_COMPANY, FACEBOOK, GITHUB]
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


# Simple Icons paths (CC0). Decorative; the visible link text is the accessible name.
_LINKEDIN_ICON_PATH = (
    "M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 "
    "1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 "
    "3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 "
    "0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 "
    "2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 "
    "23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"
)
_FACEBOOK_ICON_PATH = (
    "M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 "
    "11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 "
    "2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 "
    "3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"
)


def _social_icon_svg(path: str) -> str:
    return (
        '<svg class="social-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        'width="1em" height="1em" aria-hidden="true" focusable="false">'
        f'<path fill="currentColor" d="{path}"/></svg>'
    )


def social_icon_for_url(url: str) -> str:
    """Brand mark for the GemmiSI LinkedIn company page and Facebook Page only."""
    if url.rstrip("/") == LINKEDIN_COMPANY.rstrip("/"):
        return _social_icon_svg(_LINKEDIN_ICON_PATH)
    if url == FACEBOOK:
        return _social_icon_svg(_FACEBOOK_ICON_PATH)
    return ""


def social_anchor(url: str, label: str, *, css_class: str | None = None) -> str:
    icon = social_icon_for_url(url)
    classes = [part for part in (css_class, "social-link" if icon else None) if part]
    cls = f' class="{" ".join(classes)}"' if classes else ""
    return f'<a{cls} href="{url}" target="_blank" rel="noreferrer">{icon}{label}</a>'


def company_social_pair(
    *,
    css_class: str | None = None,
    linkedin_label: str,
    facebook_label: str,
    joiner: str = "\n        ",
    extra_class: str = "",
) -> str:
    """GemmiSI LinkedIn page next to Facebook, grouped for wrapping."""
    linkedin = social_anchor(LINKEDIN_COMPANY, linkedin_label, css_class=css_class)
    facebook = social_anchor(FACEBOOK, facebook_label, css_class=css_class)
    cls = "social-pair" + (f" {extra_class}" if extra_class else "")
    return f'<span class="{cls}">{linkedin}{joiner}{facebook}</span>'


def footer_social_links() -> str:
    """Personal LinkedIn, then the company LinkedIn + Facebook pair."""
    return (
        f"{social_anchor(LINKEDIN, 'LinkedIn')}\n"
        f"        {company_social_pair(linkedin_label='GemmiSI on LinkedIn', facebook_label='Facebook')}"
    )


def contact_social_links() -> str:
    """Quiet LinkedIn · GemmiSI · Facebook for contact panels."""
    return (
        f"{social_anchor(LINKEDIN, 'LinkedIn', css_class='text-link')} · "
        f"{company_social_pair(css_class='text-link', linkedin_label='GemmiSI', facebook_label='Facebook', joiner=' · ')}"
    )


def about_company_social_links() -> str:
    """Homepage About: company LinkedIn then Facebook, stacked."""
    return company_social_pair(
        css_class="text-link",
        linkedin_label="GemmiSI on LinkedIn ↗",
        facebook_label="GemmiSI on Facebook ↗",
        joiner="",
        extra_class="social-pair--stack",
    )


_FOOTER_COMPANY_RE = re.compile(
    r'<a href="'
    + re.escape(LINKEDIN_COMPANY)
    + r'" target="_blank" rel="noreferrer">GemmiSI on LinkedIn</a>\s*'
    r'<a href="'
    + re.escape(FACEBOOK)
    + r'" target="_blank" rel="noreferrer">Facebook</a>'
)
_CONTACT_COMPANY_RE = re.compile(
    r'<a class="text-link" href="'
    + re.escape(LINKEDIN_COMPANY)
    + r'" target="_blank" rel="noreferrer">GemmiSI</a> · '
    r'<a class="text-link" href="'
    + re.escape(FACEBOOK)
    + r'" target="_blank" rel="noreferrer">Facebook</a>'
)
_ABOUT_COMPANY_RE = re.compile(
    r'<a class="text-link" href="'
    + re.escape(LINKEDIN_COMPANY)
    + r'" target="_blank" rel="noreferrer">GemmiSI on LinkedIn ↗</a><br />\s*'
    r'<a class="text-link" href="'
    + re.escape(FACEBOOK)
    + r'" target="_blank" rel="noreferrer">GemmiSI on Facebook ↗</a>'
)


def apply_company_social_icons(html: str) -> str:
    """Insert brand icons into existing company LinkedIn and Facebook anchors. Idempotent."""
    html = _FOOTER_COMPANY_RE.sub(
        lambda _: company_social_pair(linkedin_label="GemmiSI on LinkedIn", facebook_label="Facebook"),
        html,
    )
    html = _CONTACT_COMPANY_RE.sub(
        lambda _: company_social_pair(
            css_class="text-link",
            linkedin_label="GemmiSI",
            facebook_label="Facebook",
            joiner=" · ",
        ),
        html,
    )
    html = _ABOUT_COMPANY_RE.sub(lambda _: about_company_social_links(), html)
    return html


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


# Explicit document titles and meta for conversion pages. Keep SI, AI, and
# GemmiSI in every title; keep SI (AI) in every description; stay ≤60 / ≤155.
USE_CASE_SEO = {
    "rubric-lesson-plan-outlines": {
        "title": "Lesson Plan & Rubric Outlines with SI (AI) | GemmiSI",
        "description": (
            "SI (AI) drafts lesson outlines and rubric skeletons from the "
            "standards you already chose. You decide what to teach. Free copy-ready prompt."
        ),
    },
    "tuition-payment-reminders": {
        "title": "Tuition Payment Reminder Drafts with SI (AI) | GemmiSI",
        "description": (
            "SI (AI) drafts calm tuition reminders from your aging list. "
            "Your business office approves and sends every one. No fees or balance changes."
        ),
    },
    "missing-assignment-reminders": {
        "title": "Missing Assignment Reminders with SI (AI) | GemmiSI",
        "description": (
            "Turn a gradebook export into a missing-work list and gentle reminder drafts. "
            "SI (AI) never changes scores. You decide who is contacted."
        ),
    },
    "enrollment-inquiry-follow-up": {
        "title": "Enrollment Inquiry Follow-Up Drafts | SI (AI) | GemmiSI",
        "description": (
            "SI (AI) turns tour requests and inquiry emails into one list, then drafts "
            "replies in your approved wording. Admissions sends every reply."
        ),
    },
    "parent-teacher-conference-scheduling": {
        "title": "Parent-Teacher Conference Scheduling | SI (AI) | GemmiSI",
        "description": (
            "SI (AI) finds open conference slots, flags double-bookings and drafts "
            "confirmations. A teacher or office confirms every time."
        ),
    },
    "missed-call-text-back": {
        "title": "Missed-Call Text-Back for Businesses | SI (AI) | GemmiSI",
        "description": (
            "SI (AI) drafts a short text after a missed call and sorts after-hours notes. "
            "You call back, quote, and book. Set up on your own accounts."
        ),
    },
    "chargeback-and-dispute-evidence": {
        "title": "Chargeback Packet, Built for You to File | SI (AI) | GemmiSI",
        "description": (
            "SI (AI) gathers the order, tracking and messages into one dispute evidence packet "
            "with a timeline, and flags what's missing. You file it."
        ),
    },
    "rental-lead-inquiry-follow-up": {
        "title": "Rental Inquiry Follow-Up for Landlords | SI (AI) | GemmiSI",
        "description": (
            "SI (AI) drafts a fast rental reply from your unit sheet: rent, dates, pets, "
            "and parking. It can offer showing times. You approve."
        ),
    },
    "rental-prospect-question-replies": {
        "title": "Rental Prospect Question Replies | SI (AI) | GemmiSI",
        "description": (
            "SI (AI) answers still-available, pets, and parking from your listing sheet. "
            "Same facts for everyone. You approve each reply."
        ),
    },
    "landlord-morning-list": {
        "title": "Landlord Morning List | SI (AI) | GemmiSI",
        "description": (
            "SI (AI) builds a morning list of new rental questions, today's showings, "
            "late rent, and open repairs. You decide what to do."
        ),
    },
    "package-problem-watch": {
        "title": "Package Problem Watch | SI (AI) | GemmiSI",
        "description": (
            "SI (AI) flags late, stuck, exception, and return-to-sender tracking each "
            "morning, before customers ask. You decide the next step."
        ),
    },
    "heads-up-delay-emails": {
        "title": "Heads-Up Delay Email Drafts | SI (AI) | GemmiSI",
        "description": (
            "When tracking stalls, SI (AI) drafts a heads-up delay email from the scan "
            "on file. You approve it before it goes out."
        ),
    },
    "missing-item-upload-replies": {
        "title": "Missing-Item Upload Replies | SI (AI) | GemmiSI",
        "description": (
            "After a client uploads files, SI (AI) drafts a got-these, still-need-these "
            "note from your checklist. A person sends it."
        ),
    },
    "after-hours-call-summary-to-owner": {
        "title": "After-Hours Call Summary to Owner | SI (AI) | GemmiSI",
        "description": (
            "SI (AI) turns overnight home-service calls into a morning summary for the "
            "owner. You still call back, quote, and book."
        ),
    },
    "estimate-day-follow-up": {
        "title": "Estimate-Day Follow-Up for Trades | SI (AI) | GemmiSI",
        "description": (
            "SI (AI) drafts same-day, day-3, and day-7 follow-ups after an estimate visit. "
            "The owner approves every note. No price changes."
        ),
    },
    "weekly-money-in-digest": {
        "title": "Weekly Money-In Digest | SI (AI) | GemmiSI",
        "description": (
            "SI (AI) lists payments that came in this week and what is still owed. "
            "You check it against your books. No money is moved."
        ),
    },
    "tutoring-session-progress-notes": {
        "title": "Tutoring Progress Notes | SI (AI) | GemmiSI",
        "description": (
            "After a session, SI (AI) turns the tutor's notes into a short parent "
            "summary. The tutor still approves it."
        ),
    },
    "vendor-work-order-tracking": {
        "title": "Vendor Work-Order Tracking | SI (AI) | GemmiSI",
        "description": (
            "SI (AI) keeps landlord vendors and work orders in one tracker and drafts "
            "status notes. You hire, pay, and send."
        ),
    },
    "property-hurricane-season-prep": {
        "title": "Rental Hurricane Ready Sheets | SI (AI) | GemmiSI",
        "description": (
            "Before the season, SI (AI) builds a rental-property ready sheet and "
            "tenant message drafts. You decide what to send."
        ),
    },
    "hurricane-season-readiness": {
        "title": "Shop Hurricane-Season Checklist | SI (AI) | GemmiSI",
        "description": (
            "SI (AI) turns shop, crew, or office records into a storm checklist and "
            "draft messages. You decide what to send."
        ),
    },
    "salon-whatsapp-booking-drafts": {
        "title": "Salon WhatsApp Booking Drafts | SI (AI) | GemmiSI",
        "description": (
            "SI (AI) drafts salon and spa booking replies from the owner's calendar. "
            "The owner still confirms every slot."
        ),
    },
    "auto-service-history-reminders": {
        "title": "Auto Service History Reminders | SI (AI) | GemmiSI",
        "description": (
            "SI (AI) drafts oil-change and inspection reminders from the shop's own "
            "history. A person still sends each note."
        ),
    },
    "contractor-license-insurance-tracker": {
        "title": "Contractor License Tracker | SI (AI) | GemmiSI",
        "description": (
            "SI (AI) tracks license, insurance, and subcontractor dates the owner "
            "verified. You decide who may work."
        ),
    },
}


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


def _seo_override_title(slug: str) -> str | None:
    raw = (USE_CASE_SEO.get(slug) or {}).get("title")
    if not raw:
        return None
    title = re.sub(r"\s+", " ", raw).strip()
    if len(title) > 60:
        raise SystemExit(f"{slug} seo title is {len(title)} chars")
    if "SI" not in title or "AI" not in title or "GemmiSI" not in title:
        raise SystemExit(f"{slug} seo title must include SI, AI, and GemmiSI")
    return title


def use_case_seo_titles(entries: list[dict]) -> dict[str, str]:
    """Unique document titles; disambiguate with industry or slug if a short form collides."""
    assigned: dict[str, str] = {}
    used: set[str] = set()
    suffix = " | SI (AI) | GemmiSI"
    for item in entries:
        override = _seo_override_title(item["slug"])
        if override:
            if override.casefold() in used:
                raise SystemExit(f"{item['slug']} seo title collides")
            assigned[item["slug"]] = override
            used.add(override.casefold())
    for item in entries:
        if item["slug"] in assigned:
            continue
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


def use_case_seo_desc(item: dict | str) -> str:
    if isinstance(item, str):
        return clip_meta(with_si_ai(item))
    raw = (USE_CASE_SEO.get(item["slug"]) or {}).get("description")
    if raw:
        text = re.sub(r"\s+", " ", raw).strip()
        if len(text) > 155:
            raise SystemExit(f"{item['slug']} seo description is {len(text)} chars")
        if "SI" not in text or "AI" not in text:
            raise SystemExit(f"{item['slug']} seo description must include SI and AI")
        return text
    return clip_meta(with_si_ai(item["summary"]))


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
        "sameAs": list(SAME_AS),
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
        "sameAs": list(SAME_AS),
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


CSS_VERSION = "social-1"


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
