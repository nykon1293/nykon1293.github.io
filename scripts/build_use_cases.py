#!/usr/bin/env python3
"""Generate the static use-cases library from data/use-cases.json.

Run from the repo root:

    python3 scripts/build_use_cases.py

Writes use-cases/index.html, use-cases/search.json, one folder per slug,
and refreshes the use-case URLs in sitemap.xml. Pages are plain HTML.
GitHub Pages serves them with no build step. The search index is fetched
only when someone searches or filters the library.
"""

from __future__ import annotations

import html
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seo_schema import CSS_VERSION, NAV_SCRIPT, font_and_css_links

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "use-cases.json"
OUT = ROOT / "use-cases"
SITEMAP = ROOT / "sitemap.xml"

BASE = "https://gemmisi.com"
CAL = "https://calendly.com/josh-gemmi/30min"
OG_IMAGE = f"{BASE}/assets/brand/gemmisi-og.png"
OG_ALT = "GemmiSI — SI, automation, dashboards, and technical operations"

# Short labels match the approved library design. Add a row here if a new
# category name shows up in the data file.
SHORT = {
    "Customer support and inbox": (
        "Support & inbox",
        "support-inbox",
        "Fewer repeat questions, faster first replies, and a calmer inbox.",
    ),
    "Sales and follow-up": (
        "Sales & follow-up",
        "sales-follow-up",
        "Quotes, leads and call notes that actually get followed up.",
    ),
    "Bookkeeping, invoices and admin": (
        "Bookkeeping & admin",
        "bookkeeping-admin",
        "Invoices, receipts, reminders and month-end prep.",
    ),
    "Reporting and dashboards": (
        "Reporting & dashboards",
        "reporting-dashboards",
        "One trusted view of the business, written in plain language.",
    ),
    "Scheduling and operations": (
        "Scheduling & operations",
        "scheduling-operations",
        "Schedules, procedures, confirmations and calendar chores.",
    ),
    "Inventory and orders": (
        "Inventory & orders",
        "inventory-orders",
        "Reorders, receiving, stock watch and order checks.",
    ),
    "Content and marketing": (
        "Content & marketing",
        "content-marketing",
        "Drafts from your real material, in your voice, for you to edit.",
    ),
    "Hiring and team admin": (
        "Hiring & team admin",
        "hiring-team",
        "Postings, applications, onboarding and renewals for your team.",
    ),
    "Research and documents": (
        "Research & documents",
        "research-documents",
        "Contracts, forms, long documents and vendor comparisons.",
    ),
    "Community and membership organizations": (
        "Community & membership",
        "community-orgs",
        "Announcements, donations, volunteers, events and member lists.",
    ),
    "Ecommerce operations": (
        "Ecommerce operations",
        "ecommerce-operations",
        "Store stock, checkouts, shipping, catalogs, disputes, and marketplace listings.",
    ),
    "Local business & seasonal": (
        "Local & seasonal",
        "local-seasonal",
        "Storm prep, bilingual replies, and the listing customers see on the map.",
    ),
    "Legal practices": (
        "Legal practices",
        "legal-practices",
        "Business-side admin for solo attorneys and small firms. Attorneys review and decide.",
    ),
    "Medical and healthcare practices": (
        "Medical & healthcare",
        "medical-healthcare",
        "Scheduling, reminders, intake, and billing admin for small practices. Clinicians and staff review and decide.",
    ),
    "Real estate and property management": (
        "Real estate",
        "real-estate",
        "Business-side admin for agents, landlords and small property managers. Licensed professionals and owners review and decide.",
    ),
    "Home services and contractors": (
        "Home services",
        "home-services",
        "Office help for HVAC, plumbing, roofing, electrical, landscaping, pool and cleaning businesses. The owner approves every quote and message.",
    ),
    "Accounting, tax and bookkeeping firms": (
        "Accounting & tax",
        "accounting-tax",
        "Admin for small CPA, tax and bookkeeping firms. Professionals review, sign and decide.",
    ),
}

# Shown on the Legal practices section. The opinion title is quoted as published.
LEGAL_READ_FIRST = (
    "<strong>Read this first.</strong> The use cases in this category are about running the "
    "<em>business side</em> of a law practice: scheduling, intake logistics, billing admin, "
    "document organization, and communications drafts. SI does not give legal advice, does not "
    "practice law, and does not replace an attorney's judgment. An attorney reviews and approves "
    "anything client-facing or substantive before it goes out, and nothing here promises any legal "
    "outcome or result. Client confidentiality comes first: confidential or privileged client "
    "information should only be put into a tool after the firm has checked the vendor's terms and "
    "data practices, has proper agreements and access controls in place, and has any consent the "
    "rules require. ABA Formal Opinion 512 (2024) addresses lawyers' use of generative artificial "
    "intelligence tools and is a good starting point; state bar rules differ, so check yours. "
    "Trust-account (IOLTA) and billing records are handled with extra care, and a person approves "
    "every entry. These pages are general information, not legal or ethics advice, and not a "
    "guarantee of compliance with any rule."
)
LEGAL_SHORT = (
    "Admin and operations help for solo attorneys and small firms. SI drafts and organizes; "
    "attorneys review and decide. No legal advice, no filing-ready work product, and client "
    "confidentiality comes first."
)
LEGAL_FOOT = (
    "Not legal or ethics advice. Talk with your state bar or ethics counsel about your obligations."
)
LEGAL_OWN_ACCOUNTS = (
    "GemmiSI sets this up on your own equipment and accounts; your data stays with you."
)
LEGAL_CAUTION_PREFIX = (
    "Administrative support only: this is not legal advice and does not replace attorney judgment. "
    "An attorney reviews and approves anything client-facing or substantive, and client-confidential "
    "information is used only with the firm's agreements, access controls and consent."
)

# Shown on the Medical and healthcare practices section.
MEDICAL_READ_FIRST = (
    "<strong>Read this first.</strong> The use cases in this category are about running the "
    "<em>business side</em> of a healthcare practice: scheduling, reminders, intake logistics, "
    "insurance and billing admin, referral tracking, and communications drafts. SI does not name a "
    "condition, give medical advice, or make clinical decisions, and it does not replace a "
    "clinician's judgment. A clinician or trained staff member reviews and approves anything "
    "clinical or patient-facing before it goes out, and nothing here promises any health outcome "
    "or result. Patient privacy comes first: protected health information (PHI) should only go into "
    "tools covered by a signed business associate agreement (BAA) with the practice, with proper "
    "access controls, and only the minimum necessary; it never belongs in consumer tools or free "
    "chat apps. Billing and coding are always approved by a person; SI never invents documentation "
    "or assigns codes on its own. Recording or transcribing calls and visits may require consent, "
    "texting patients is regulated, and state laws differ, so check yours. SI never handles "
    "emergencies: anything urgent goes to a person or to 911. These pages are general information, "
    "not medical, legal or compliance advice, and not a guarantee of compliance with HIPAA or any "
    "other rule. <a href=\"https://www.hhs.gov/hipaa/for-professionals/privacy/guidance/business-associates/index.html\" "
    "target=\"_blank\" rel=\"noopener noreferrer\">HHS guidance on business associates</a> is a good starting point."
)
MEDICAL_SHORT = (
    "Admin and operations help for small practices. SI drafts, tracks and organizes; "
    "clinicians and staff review and decide. No medical advice or clinical decisions, and patient "
    "information stays in tools covered by a BAA."
)
MEDICAL_FOOT = (
    "Not medical, legal or compliance advice. Talk with your compliance officer or healthcare counsel about HIPAA and your state's rules."
)
MEDICAL_OWN_ACCOUNTS = LEGAL_OWN_ACCOUNTS
MEDICAL_CAUTION_PREFIX = (
    "Administrative support only: SI does not name a condition, recommend treatment, or make clinical decisions, "
    "and does not replace a clinician's judgment. A clinician or trained staff member reviews and approves "
    "anything clinical, billing-related or patient-facing. Patient information (PHI) is used only in tools "
    "covered by a signed business associate agreement, with access controls and the minimum necessary, never in consumer tools."
)

# Shown on the Real estate and property management section.
REAL_ESTATE_READ_FIRST = (
    "<strong>Read this first.</strong> The use cases in this category are about running the "
    "<em>business side</em> of real estate and property management: lead follow-up, scheduling, "
    "maintenance coordination, reminders, tracking and communications drafts. SI does not give "
    "legal, lease or financial advice, does not negotiate or sign anything, and does not replace "
    "the judgment of a licensed agent, broker or property manager. SI prepares drafts for the "
    "licensed agent or owner and does not lease, collect rent, screen or rank applicants. A "
    "licensed professional or the property owner reviews and approves anything client-facing, "
    "tenant-facing or contractual before it goes out, and nothing here promises any sale, lease, "
    "price or result. Fair housing laws apply however a task is done: SI never screens, ranks, "
    "steers, targets or describes people or neighborhoods by protected characteristics, and every "
    "listing, ad and message is reviewed by a person before it is used. Applicant and tenant "
    "information is private, so it should only go into tools the business has checked, with access "
    "controls and the minimum necessary. Texting is regulated, so get consent and honor opt-outs. "
    "Licensing, landlord-tenant and advertising rules differ by state, so check yours. These pages "
    "are general information, not legal or compliance advice, and not a guarantee of compliance "
    "with any law."
)
REAL_ESTATE_SHORT = (
    "Admin and operations help for agents, landlords and small property managers. SI prepares "
    "drafts for the licensed agent or owner; they review and decide. SI does not lease, collect "
    "rent, screen or rank applicants."
)
REAL_ESTATE_FOOT = (
    "Not legal advice. Talk with your broker, attorney or local fair housing resources about your obligations."
)
REAL_ESTATE_OWN_ACCOUNTS = LEGAL_OWN_ACCOUNTS
REAL_ESTATE_CAUTION_PREFIX = (
    "Administrative support only: SI does not give legal or lease advice, make leasing, screening "
    "or pricing decisions, or act as an agent or broker. SI prepares drafts for the licensed agent "
    "or owner and does not lease, collect rent, screen or rank applicants. A licensed professional "
    "or the property owner reviews and approves anything client-facing, tenant-facing or "
    "contractual. Fair housing laws apply: SI never screens, ranks, steers or targets by protected "
    "characteristics, and applicant and tenant information is used only in checked tools with "
    "access controls and the minimum necessary."
)

# Shown on the Home services and contractors section.
HOME_SERVICES_READ_FIRST = (
    "<strong>Read this first.</strong> The use cases in this category are about running the "
    "<em>office side</em> of a home-service business: missed calls, quotes, scheduling, invoices, "
    "reminders, paperwork and records. SI does not set prices, make promises, or give safety, "
    "repair, code or insurance advice, and it does not replace a licensed professional's judgment "
    "on the job. The owner or an authorized person reviews and approves every quote, price, "
    "schedule commitment and customer message before it goes out, and nothing here promises any "
    "job, timeline, savings or result. Licensing, advertising, deposit, permit and contract rules "
    "differ by state and city, so check yours. The business's license number and required notices "
    "come from the owner, not from SI. Texting customers is regulated, so get consent and honor "
    "opt-outs. Customer information is private and should only go into tools the business has "
    "checked. If something sounds like an emergency, such as gas, fire, smoke or flooding near "
    "electricity, it goes to a person and to 911 or the utility, never to SI. These pages are "
    "general information, not legal, safety or compliance advice, and not a guarantee of "
    "compliance with any rule."
)
HOME_SERVICES_SHORT = (
    "Office help for HVAC, plumbing, roofing, electrical, landscaping, pool and cleaning "
    "businesses. SI drafts, tracks and reminds; the owner approves every quote and message. No "
    "pricing promises, no safety or code advice, and customers' information stays private."
)
HOME_SERVICES_FOOT = (
    "Not legal, safety or compliance advice. Check your state's contractor licensing board and your local permitting office."
)
HOME_SERVICES_OWN_ACCOUNTS = LEGAL_OWN_ACCOUNTS
HOME_SERVICES_CAUTION_PREFIX = (
    "Office support only: SI does not set or promise prices, give safety, repair, code or "
    "insurance advice, or make any commitment for the business. The owner or an authorized person "
    "reviews and approves every quote, schedule commitment and customer message. Licensing, "
    "advertising, deposit and permit rules vary by state, and customer information is used only in "
    "checked tools with access controls."
)

# Shown on the Accounting, tax and bookkeeping firms section.
ACCOUNTING_READ_FIRST = (
    "<strong>Read this first.</strong> The use cases in this category are about running the "
    "<em>practice side</em> of an accounting, tax or bookkeeping firm: chasing documents, "
    "organizing intake, tracking dates, preparing checklists, drafting routine communications and "
    "getting information ready for a professional's review. SI does not give tax, accounting or "
    "legal advice, does not prepare, sign or file any return or report, and does not replace a "
    "CPA's, enrolled agent's or preparer's judgment. A qualified professional reviews, signs and "
    "takes responsibility for all work product, and every deadline SI tracks is verified by a "
    "person against official sources. Nothing here promises any refund, tax result or savings. "
    "Client financial and tax information is among the most sensitive a firm holds: firms that "
    "prepare returns have legal duties around data security (the FTC Safeguards Rule, covered in "
    "IRS Publication 4557) and around using or disclosing tax return information (Internal Revenue "
    "Code section 7216), and professional rules apply on top. Put client information only into "
    "tools the firm has vetted, with the agreements, access controls and any client consent the "
    "rules require, and start with sample data. State rules differ, so check yours. These pages "
    "are general information, not tax, legal or compliance advice, and not a guarantee of "
    "compliance with any rule."
)
ACCOUNTING_SHORT = (
    "Admin and operations help for small CPA, tax and bookkeeping firms. SI chases, organizes and "
    "drafts; professionals review, sign and decide. No tax advice, no filings, and client data "
    "stays protected under your firm's security plan."
)
ACCOUNTING_FOOT = (
    "Not tax, accounting or legal advice. Talk with your professional-liability advisor, state board and counsel about your obligations."
)
ACCOUNTING_OWN_ACCOUNTS = LEGAL_OWN_ACCOUNTS
ACCOUNTING_CAUTION_PREFIX = (
    "Administrative support only: SI does not give tax or accounting advice, prepare or sign "
    "returns or reports, file anything, or calculate legal deadlines. A qualified professional "
    "reviews, signs and approves all work product and every date SI tracks. Client information is "
    "used only in tools the firm has vetted, under its written security plan and with any client "
    "consent or agreements the rules require."
)

CATEGORY_NOTES = {
    "Legal practices": {
        "read_first": LEGAL_READ_FIRST,
        "short": LEGAL_SHORT,
        "foot": LEGAL_FOOT,
        "own": LEGAL_OWN_ACCOUNTS,
        "foot_class": "uc-legal-foot",
        "library_needles": ("generative artificial intelligence",),
    },
    "Medical and healthcare practices": {
        "read_first": MEDICAL_READ_FIRST,
        "short": MEDICAL_SHORT,
        "foot": MEDICAL_FOOT,
        "own": MEDICAL_OWN_ACCOUNTS,
        "foot_class": "uc-cat-foot",
        "library_needles": ("healthcare practice",),
    },
    "Real estate and property management": {
        "read_first": REAL_ESTATE_READ_FIRST,
        "short": REAL_ESTATE_SHORT,
        "foot": REAL_ESTATE_FOOT,
        "own": REAL_ESTATE_OWN_ACCOUNTS,
        "foot_class": "uc-cat-foot",
        "library_needles": ("does not lease, collect rent, screen or rank applicants",),
    },
    "Home services and contractors": {
        "read_first": HOME_SERVICES_READ_FIRST,
        "short": HOME_SERVICES_SHORT,
        "foot": HOME_SERVICES_FOOT,
        "own": HOME_SERVICES_OWN_ACCOUNTS,
        "foot_class": "uc-cat-foot",
        "library_needles": ("office side",),
    },
    "Accounting, tax and bookkeeping firms": {
        "read_first": ACCOUNTING_READ_FIRST,
        "short": ACCOUNTING_SHORT,
        "foot": ACCOUNTING_FOOT,
        "own": ACCOUNTING_OWN_ACCOUNTS,
        "foot_class": "uc-cat-foot",
        "library_needles": ("FTC Safeguards Rule",),
    },
}

REQUIRED = (
    "slug",
    "title",
    "category",
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

CTA = "Book a free 30-minute consult"


def e(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


PAGE_SIZE = 24


def json_ld(obj, *, compact: bool = False) -> str:
    if compact:
        raw = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    else:
        raw = json.dumps(obj, ensure_ascii=False, indent=2)
    return raw.replace("<", "\\u003c")


def load() -> list:
    entries = json.loads(DATA.read_text(encoding="utf-8"))
    if not isinstance(entries, list) or not entries:
        raise SystemExit("data/use-cases.json must be a non-empty list")
    slugs = []
    for item in entries:
        missing = [key for key in REQUIRED if key not in item]
        if missing:
            raise SystemExit(f"{item.get('slug', '?')} is missing {', '.join(missing)}")
        if item["category"] not in SHORT:
            raise SystemExit(
                f"Unknown category {item['category']!r} on {item['slug']}. "
                "Add it to SHORT in scripts/build_use_cases.py."
            )
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", item["slug"]):
            raise SystemExit(f"Slug must be lowercase hyphenated words: {item['slug']}")
        if not item["examples"] or not all(
            isinstance(ex, dict) and ex.get("business_type") and ex.get("scenario")
            for ex in item["examples"]
        ):
            raise SystemExit(f"{item['slug']} examples must include business_type and scenario")
        blob = json.dumps(item)
        if re.search(r"\bAI\b", blob) or "Nous" in blob or "Brandgate" in blob:
            raise SystemExit(f"{item['slug']} contains wording that must stay off the public site")
        if item["category"] == "Legal practices":
            caution = (item.get("caution") or "").strip()
            if not caution.startswith(LEGAL_CAUTION_PREFIX):
                raise SystemExit(f"{item['slug']} caution must start with the legal guardrail")
            prompt = item["copy_prompt"]
            if "Pause and show me before sending, filing, posting or changing anything" not in prompt:
                raise SystemExit(f"{item['slug']} prompt must pause before sending, filing, posting, or changing")
            if (
                "Use only the sample or de-identified information I provide; do not include client-confidential details"
                not in prompt
            ):
                raise SystemExit(f"{item['slug']} prompt must limit itself to sample or de-identified information")
            if len(item["human_checks"]) < 3:
                raise SystemExit(f"{item['slug']} needs at least three human checks")
            if LEGAL_OWN_ACCOUNTS not in item["setup"]:
                raise SystemExit(f"{item['slug']} setup must say the work stays on the firm's own equipment and accounts")
            for banned in ("Ohr", "Kayla", "josh.gemmi@gmail.com"):
                if banned in blob:
                    raise SystemExit(f"{item['slug']} contains wording that must stay off the public site")
        if item["category"] == "Medical and healthcare practices":
            caution = (item.get("caution") or "").strip()
            if not caution.startswith(MEDICAL_CAUTION_PREFIX):
                raise SystemExit(f"{item['slug']} caution must start with the medical guardrail")
            prompt = item["copy_prompt"]
            if "Pause and show me before sending, submitting, billing, posting or changing anything" not in prompt:
                raise SystemExit(f"{item['slug']} prompt must pause before sending, submitting, billing, posting, or changing")
            if (
                "Use only the sample or de-identified information I provide; do not include any patient names or health information"
                not in prompt
            ):
                raise SystemExit(f"{item['slug']} prompt must limit itself to sample or de-identified information")
            if len(item["human_checks"]) < 3:
                raise SystemExit(f"{item['slug']} needs at least three human checks")
            if not item["setup"].startswith(MEDICAL_OWN_ACCOUNTS):
                raise SystemExit(f"{item['slug']} setup must start with the own-equipment sentence")
            if re.search(r"diagnose", blob, re.I):
                raise SystemExit(f"{item['slug']} must not use the word diagnose")
            lowered = blob.lower()
            for banned in (
                "hipaa compliant",
                "hipaa-compliant",
                "hipaa certified",
                "hipaa-certified",
                "hipaa safe",
                "hipaa-safe",
                "ohr",
                "kayla",
                "josh.gemmi@gmail.com",
            ):
                if banned in lowered:
                    raise SystemExit(f"{item['slug']} contains wording that must stay off the public site")
        if item["category"] in (
            "Real estate and property management",
            "Home services and contractors",
            "Accounting, tax and bookkeeping firms",
        ):
            _check_industry_entry(item)
        slugs.append(item["slug"])
    dupes = {slug for slug in slugs if slugs.count(slug) > 1}
    if dupes:
        raise SystemExit(f"Duplicate slugs: {', '.join(sorted(dupes))}")
    return entries


def _check_industry_entry(item: dict) -> None:
    cat = item["category"]
    caution = (item.get("caution") or "").strip()
    prompt = item["copy_prompt"]
    blob = json.dumps(item)
    lowered = blob.lower()
    if len(item["human_checks"]) < 3:
        raise SystemExit(f"{item['slug']} needs at least three human checks")
    if not item["setup"].startswith(LEGAL_OWN_ACCOUNTS):
        raise SystemExit(f"{item['slug']} setup must start with the own-equipment sentence")
    for banned in ("Ohr", "Kayla", "josh.gemmi@gmail.com", "Brandgate"):
        if banned in blob:
            raise SystemExit(f"{item['slug']} contains wording that must stay off the public site")
    extra = ""
    texting = False
    if cat == "Real estate and property management":
        if not caution.startswith(REAL_ESTATE_CAUTION_PREFIX):
            raise SystemExit(f"{item['slug']} caution must start with the real-estate guardrail")
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
    elif cat == "Home services and contractors":
        if not caution.startswith(HOME_SERVICES_CAUTION_PREFIX):
            raise SystemExit(f"{item['slug']} caution must start with the home-services guardrail")
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
        if not caution.startswith(ACCOUNTING_CAUTION_PREFIX):
            raise SystemExit(f"{item['slug']} caution must start with the accounting guardrail")
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


def categories(entries: list) -> list:
    seen = []
    for item in entries:
        if item["category"] not in seen:
            seen.append(item["category"])
    return seen


def nav(depth: int) -> str:
    up = "../" * depth
    library = "index.html" if depth == 1 else "../index.html"
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
    library = "index.html" if depth == 1 else "../index.html"
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


def head(title: str, desc: str, canon: str, depth: int, ld: dict, *, compact_ld: bool = False) -> str:
    up = "../" * depth
    assets = font_and_css_links(
        stylesheet=f"{up}styles.css?v={CSS_VERSION}",
        extra_css=f"{up}assets/use-cases.css?v={CSS_VERSION}",
    )
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
<body>
  <div class="site-shell">
{nav(depth)}
"""


def haystack(item: dict) -> str:
    short = SHORT[item["category"]][0]
    parts = [item["title"], item["summary"], short, item["category"]]
    parts.extend(item.get("tools_examples") or [])
    for example in item.get("examples") or []:
        parts.append(example.get("business_type", ""))
        parts.append(example.get("scenario", ""))
    return " ".join(parts).lower()


def card_note(item: dict) -> str:
    info = CATEGORY_NOTES.get(item["category"])
    return info["short"] if info else ""


def card(item: dict, href: str, show_cat: bool = True, extra: bool = False) -> str:
    short = SHORT[item["category"]]
    cat = f'<span class="uc-card-cat">{e(short[0])}</span>' if show_cat else ""
    extra_cls = " uc-extra" if extra else ""
    note = card_note(item)
    note_html = f'\n              <p class="uc-card-note">{e(note)}</p>' if note else ""
    return f"""<li class="uc-card{extra_cls}" data-cat="{short[1]}" data-slug="{e(item['slug'])}">
            <a href="{href}">
              {cat}
              <h3>{e(item['title'])}</h3>
              <p>{e(item['summary'])}</p>{note_html}
              <span class="uc-card-more">Read the use case <span aria-hidden="true">→</span></span>
            </a>
          </li>"""


def compact_link(item: dict, href: str) -> str:
    short = SHORT[item["category"]]
    return (
        f'<li class="uc-compact" data-cat="{short[1]}" data-slug="{e(item["slug"])}">'
        f'<a href="{href}">{e(item["title"])}</a></li>'
    )


def pick_visible_slugs(entries: list, cats: list) -> set[str]:
    """One card per category first, then fill up to PAGE_SIZE in category order."""
    by_cat = {cat: [item for item in entries if item["category"] == cat] for cat in cats}
    visible: list[str] = []
    for cat in cats:
        if by_cat[cat]:
            visible.append(by_cat[cat][0]["slug"])
    for cat in cats:
        for item in by_cat[cat][1:]:
            if len(visible) >= PAGE_SIZE:
                return set(visible)
            visible.append(item["slug"])
    return set(visible)


def search_records(entries: list) -> list[dict]:
    records = []
    for item in entries:
        short = SHORT[item["category"]]
        row = {
            "s": item["slug"],
            "t": item["title"],
            "u": item["summary"],
            "c": short[1],
            "l": short[0],
            "h": haystack(item),
        }
        note = card_note(item)
        if note:
            row["n"] = note
        records.append(row)
    return records


def write_search_index(entries: list) -> None:
    payload = {"items": search_records(entries)}
    (OUT / "search.json").write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def library_page(entries: list) -> str:
    n = len(entries)
    cats = categories(entries)
    title = "SI use cases for small businesses and community organizations | Yonatan Gemmi"
    desc = (
        f"{n} practical ways SI can take routine work off a small team: inbox and support, "
        "sales follow-up, bookkeeping, reporting, scheduling, inventory, ecommerce, content, "
        "hiring, documents, community organizations, local business, legal-practice admin, "
        "medical-practice admin, real estate, home services, and accounting-firm admin. "
        "Each one shows what a human still checks."
    )
    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Use cases", "item": BASE + "/use-cases/"},
                ],
            },
            {
                "@type": "CollectionPage",
                "name": "SI use cases",
                "url": BASE + "/use-cases/",
                "description": desc,
                "isPartOf": {"@type": "WebSite", "name": "Yonatan Gemmi", "url": BASE + "/"},
                "mainEntity": {
                    "@type": "ItemList",
                    "numberOfItems": n,
                    "itemListElement": [
                        {
                            "@type": "ListItem",
                            "position": i + 1,
                            "url": f"{BASE}/use-cases/{item['slug']}/",
                            "name": item["title"],
                        }
                        for i, item in enumerate(entries)
                    ],
                },
            },
        ],
    }
    pills = [
        f'<button type="button" class="uc-pill is-active" data-filter="all" aria-pressed="true">All <span>{n}</span></button>'
    ]
    for cat in cats:
        label, slug, _blurb = SHORT[cat]
        count = sum(1 for item in entries if item["category"] == cat)
        pills.append(
            f'<button type="button" class="uc-pill" data-filter="{slug}" aria-pressed="false">{e(label)} <span>{count}</span></button>'
        )
    visible = pick_visible_slugs(entries, cats)
    sections = []
    for index, cat in enumerate(cats, 1):
        label, slug, blurb = SHORT[cat]
        items = [item for item in entries if item["category"] == cat]
        shown = [item for item in items if item["slug"] in visible]
        rest = [item for item in items if item["slug"] not in visible]
        cards = "\n          ".join(card(item, f"{item['slug']}/", show_cat=False) for item in shown)
        compact = ""
        if rest:
            links = "\n          ".join(compact_link(item, f"{item['slug']}/") for item in rest)
            compact = (
                f'        <ul class="uc-index" aria-label="All {e(label)} use cases">\n'
                f"          {links}\n"
                "        </ul>\n"
            )
        more = ""
        if rest:
            more = (
                f'<button type="button" class="uc-more" data-n="{len(items)}" '
                f'aria-expanded="false">Show all {len(items)}</button>'
            )
        banner = ""
        closing_note = ""
        info = CATEGORY_NOTES.get(cat)
        if info:
            banner = (
                '        <div class="uc-read-first" role="note">\n'
                f"          <p>{info['read_first']}</p>\n"
                f"          <p class=\"uc-own-accounts\">{e(info['own'])}</p>\n"
                "        </div>\n"
            )
            closing_note = f'        <p class="{info["foot_class"]}">{e(info["foot"])}</p>\n'
        sections.append(
            f"""      <section class="uc-group" data-group="{slug}" aria-labelledby="g-{slug}">
        <div class="uc-group-head">
          <span class="section-kicker">{index:02d}</span>
          <h2 id="g-{slug}">{e(label)}</h2>
          <p>{e(blurb)}</p>
        </div>
{banner}        <ul class="uc-grid">
          {cards}
        </ul>
{compact}        {more}
{closing_note}      </section>"""
        )
    # The single allowed "AI" bridge lives in this intro and nowhere else.
    return head(title, desc, "/use-cases/", 1, ld, compact_ld=True) + f"""
    <main id="top">
      <section class="uc-hero">
        <nav class="breadcrumb" aria-label="Breadcrumb">
          <a href="../index.html">Home</a>
          <span aria-hidden="true">/</span>
          <span>Use cases</span>
        </nav>
        <p class="eyebrow"><span class="status-dot" aria-hidden="true"></span>{n} practical examples</p>
        <h1>What SI can take off your plate</h1>
        <p class="lead">SI (Super Intelligence, formerly called AI) can take on a lot of the repetitive work in almost any business or organization: reading, sorting, matching, drafting, checking and summarizing. Each entry describes one practical job, what it needs to get started, and where a person stays in charge. Anything that sends, pays, orders or posts always waits for your approval.</p>
        <p class="uc-note-intro">The examples show how the same job looks in different kinds of businesses. They are illustrations of what is possible, not reports of client results. Setup times are rough and depend on how clean your data and tools are.</p>
        <div class="actions">
          <a class="button primary" href="{CAL}" target="_blank" rel="noreferrer">{CTA}</a>
          <a class="button ghost" href="#library">Browse the use cases</a>
        </div>
      </section>

      <section id="library" class="uc-tools" aria-label="Search and filter use cases">
        <div class="uc-search">
          <label for="uc-q" class="visually-hidden">Search use cases</label>
          <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" stroke-width="2"/><path d="M20 20l-4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
          <input id="uc-q" type="search" placeholder="Search, e.g. invoices, schedule, Gmail" autocomplete="off" />
        </div>
        <div class="uc-pills" role="group" aria-label="Filter by category">
          {chr(10) + '          '.join(pills)}
        </div>
        <p class="uc-count" id="uc-count" role="status" aria-live="polite">Showing {len(visible)} of {n} use cases</p>
        <button type="button" class="uc-more uc-show-all" id="uc-show-all">Show all {n} use cases</button>
      </section>
{chr(10).join(sections)}
      <p class="uc-empty" id="uc-empty" hidden>No use case matches that search. Try a broader word, or <a class="text-link" href="{CAL}" target="_blank" rel="noreferrer">tell me what you need</a> on a free call.</p>

      <section class="section closing-card uc-closing">
        <div class="contact-panel">
          <p class="section-kicker">Don’t see yours?</p>
          <h2>Bring the task that keeps eating your week</h2>
          <p class="section-intro">If it is repetitive, rule-based, and lives in email, spreadsheets, a store, or a CRM, there is a good chance it can be drafted by SI and checked by you. Book a free 30-minute call and we will look at it together.</p>
          <div class="actions"><a class="button primary" href="{CAL}" target="_blank" rel="noreferrer">{CTA}</a></div>
        </div>
      </section>
    </main>
""" + foot(1) + SCRIPTS + """  <script src="/assets/use-cases-library.js" defer></script>
</body>
</html>
"""


def detail_page(item: dict, entries: list) -> str:
    n = len(entries)
    label, slug, _blurb = SHORT[item["category"]]
    url = f"/use-cases/{item['slug']}/"
    title = f"{item['title']} | SI use case | Yonatan Gemmi"
    desc = item["summary"]
    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Use cases", "item": BASE + "/use-cases/"},
                    {"@type": "ListItem", "position": 3, "name": item["title"], "item": BASE + url},
                ],
            },
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
    same = [other for other in entries if other["category"] == item["category"] and other["slug"] != item["slug"]]
    rest = [other for other in entries if other["category"] != item["category"]]
    related = (same + rest)[:3]
    related_html = "\n          ".join(card(other, f"../{other['slug']}/") for other in related)
    checks = "\n            ".join(f"<li>{e(line)}</li>" for line in item["human_checks"])
    examples = "\n            ".join(
        f'<li class="uc-ex"><span class="uc-ex-type">{e(ex["business_type"])}</span><p>{e(ex["scenario"])}</p></li>'
        for ex in item["examples"]
    )
    caution = ""
    if (item.get("caution") or "").strip():
        caution = f'<p class="uc-caution" role="note"><strong>Worth knowing:</strong> {e(item["caution"])}</p>'
    legal_note = ""
    info = CATEGORY_NOTES.get(item["category"])
    if info:
        legal_note = f'<p class="uc-read-first" role="note">{e(info["short"])}</p>\n          '
    tools = "".join(f'<span class="tag green">{e(tool)}</span>' for tool in item["tools_examples"])
    return head(title, desc, url, 2, ld) + f"""
    <main id="top">
      <article class="uc-detail">
        <header class="uc-detail-head">
          <nav class="breadcrumb" aria-label="Breadcrumb">
            <a href="../../index.html">Home</a>
            <span aria-hidden="true">/</span>
            <a href="../index.html">Use cases</a>
            <span aria-hidden="true">/</span>
            <span>{e(item['title'])}</span>
          </nav>
          <p class="uc-card-cat"><a href="../index.html#g-{slug}">{e(label)}</a></p>
          <h1>{e(item['title'])}</h1>
          <p class="lead">{e(item['summary'])}</p>
          {legal_note}{caution}
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
</body>
</html>
"""


def url_block(loc: str, priority: str) -> str:
    # Stamp the day the library is regenerated so lastmod does not stay frozen.
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
    if "Read this first." not in library:
        raise SystemExit("A category section is missing the full disclaimer")
    for cat, info in CATEGORY_NOTES.items():
        if e(info["short"]) not in library:
            raise SystemExit(f"{cat} cards are missing the short disclaimer")
        if info["own"] not in library:
            raise SystemExit(f"{cat} section is missing the own-equipment line")
        for needle in info.get("library_needles") or ():
            if needle not in library:
                raise SystemExit(f"{cat} section is missing expected disclaimer text")
    for item in entries:
        page = (OUT / item["slug"] / "index.html").read_text(encoding="utf-8")
        if re.search(r"\bAI\b", page) or "noindex" in page or "Nous" in page or "Brandgate" in page:
            raise SystemExit(f"Wording check failed for {item['slug']}")
        info = CATEGORY_NOTES.get(item["category"])
        if info:
            if e(info["short"]) not in page:
                raise SystemExit(f"{item['slug']} is missing the short category disclaimer")
            if info["own"] not in page:
                raise SystemExit(f"{item['slug']} is missing the own-equipment setup line")
        if item["category"] == "Medical and healthcare practices":
            if re.search(r"diagnose", page, re.I):
                raise SystemExit(f"{item['slug']} page must not use the word diagnose")
    if "data-hay=" in library:
        raise SystemExit("Library page must not inline search haystacks")
    if 'id="uc-show-all"' not in library:
        raise SystemExit("Library page needs a show-all control")
    index_path = OUT / "search.json"
    if not index_path.exists():
        raise SystemExit("use-cases/search.json is missing")
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    records = payload["items"] if isinstance(payload, dict) else payload
    if len(records) != len(entries):
        raise SystemExit(f"search.json has {len(records)} items, expected {len(entries)}")
    record_slugs = {row["s"] for row in records}
    for item in entries:
        if item["slug"] not in record_slugs:
            raise SystemExit(f"search.json is missing {item['slug']}")
        if f'{item["slug"]}/' not in library:
            raise SystemExit(f"Library is missing a crawlable link for {item['slug']}")


def main() -> None:
    entries = load()
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
    for item in entries:
        folder = OUT / item["slug"]
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "index.html").write_text(detail_page(item, entries), encoding="utf-8")
    update_sitemap(entries)
    assert_wording(entries)
    print(f"built {len(entries)} use cases")


if __name__ == "__main__":
    main()
