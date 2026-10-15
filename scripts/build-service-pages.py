#!/usr/bin/env python3
"""Generate static service landing pages (run from repo root)."""
from __future__ import annotations

from html import escape
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from seo_schema import (
    APPROVAL_LINE,
    CALENDLY,
    BASE,
    CLOUDFLARE_WEB_ANALYTICS,
    CSS_VERSION,
    NAV_SCRIPT,
    OWN_EQUIPMENT,
    clip_meta,
    common_head_tags,
    font_and_css_links,
    icon_links,
    service_page_graph,
)
from use_case_motifs import landing_motif_html, motif_thumb_html

SERVICES_DIR = ROOT / "services"

SERVICE_PAGES = [
    ("hermes-agents.html", "Hermes Agents", "hermes-agents"),
    ("ai-automation.html", "SI automation", "ai-automation"),
    ("dashboards-reporting.html", "Dashboards & reporting", "dashboards-reporting"),
    ("ecommerce-operations.html", "Ecommerce operations", "ecommerce-operations"),
    ("tutoring-project-help.html", "Tutoring & project help", "tutoring-project-help"),
]


def nav_for(slug: str) -> str:
    lines = ['<nav id="site-nav" class="nav-links" aria-label="Primary navigation">']
    lines.append('        <a href="../index.html">Home</a>')
    work_cur = ' aria-current="page"' if slug == "work" else ""
    lines.append(f'        <a href="../index.html#work"{work_cur}>Work</a>')
    lines.append('        <details class="nav-dropdown">')
    lines.append('          <summary class="nav-dropdown-trigger">Services</summary>')
    lines.append('          <div class="nav-dropdown-menu">')
    for href, label, key in SERVICE_PAGES:
        cur = ' aria-current="page"' if key == slug else ""
        lines.append(f'            <a href="{href}"{cur}>{escape(label)}</a>')
    stocky_cur = ' aria-current="page"' if slug == "stocky-recovery" else ""
    lines.append(
        f'            <a class="nav-dropdown-muted" href="stocky-recovery.html"{stocky_cur}>Stocky dump recovery</a>'
    )
    lines.append('            <a class="nav-dropdown-muted" href="../index.html#service-hub">All services</a>')
    lines.append('            <a class="nav-dropdown-muted" href="../advisory.html">Advisory &amp; Fractional (ask first)</a>')
    lines.append("          </div>")
    lines.append("        </details>")
    lines.append('        <a href="../use-cases/">Use cases</a>')
    lines.append('        <a href="../pricing.html">Pricing</a>')
    lines.append("      </nav>")
    lines.append(f'      <a class="nav-cta" href="{CALENDLY}" target="_blank" rel="noreferrer">Book consultation</a>')
    return "\n".join(lines)


def faq_schema(
    faqs: list[tuple[str, str]],
    *,
    service_name: str,
    meta_description: str,
    canonical: str,
    page_name: str,
    breadcrumb_label: str,
) -> str:
    plain = [(q, re.sub(r"<[^>]+>", "", a)) for q, a in faqs]
    return service_page_graph(
        service_name=service_name,
        meta_description=meta_description,
        canonical=canonical,
        page_name=page_name,
        faqs=plain,
        breadcrumb_label=breadcrumb_label,
    )


def use_case_title_map() -> dict[str, str]:
    entries = json.loads((ROOT / "data" / "use-cases.json").read_text(encoding="utf-8"))
    return {item["slug"]: item["title"] for item in entries}


SERVICE_MOTIF = {
    "hermes-agents": ("function", "hiring"),
    "ai-automation": ("industry", "any-business"),
    "dashboards-reporting": ("function", "reporting-dashboards"),
    "ecommerce-operations": ("industry", "ecommerce"),
    "tutoring-project-help": ("industry", "education"),
    "stocky-recovery": ("industry", "ecommerce"),
}


def _entries_by_slug() -> dict:
    return {item["slug"]: item for item in json.loads((ROOT / "data" / "use-cases.json").read_text(encoding="utf-8"))}


def related_use_cases_html(page: dict) -> str:
    slugs = page.get("related_use_cases") or []
    landings = page.get("related_landings") or []
    if not slugs and not landings:
        return ""
    titles = use_case_title_map()
    catalog = _entries_by_slug()
    items = []
    for slug in slugs[:6]:
        label = titles.get(slug, slug.replace("-", " "))
        item = catalog.get(slug)
        thumb = motif_thumb_html(item) if item else ""
        items.append(
            f'            <li>{thumb}<a class="text-link" href="/use-cases/{slug}/">{escape(label)}</a></li>'
        )
    landing_bits = []
    for href, label in landings:
        landing_bits.append(f'<a class="text-link" href="{escape(href)}">{escape(label)}</a>')
    landings_html = ""
    if landing_bits:
        landings_html = f'          <p class="related-landings">Also see {", ".join(landing_bits)}.</p>'
    list_html = ""
    if items:
        list_html = "          <ul class=\"related-uc-list\">\n" + "\n".join(items) + "\n          </ul>\n"
    kind, key = SERVICE_MOTIF.get(page.get("slug"), ("industry", "any-business"))
    graphic = landing_motif_html(kind, key, inline=False)
    return f"""
      <section class="section related-case-study" aria-labelledby="related-uc-title">
        <div class="uc-detail-intro">
          <div class="uc-detail-copy">
          <h2 id="related-uc-title">Example SI (AI) use cases</h2>
          <p class="section-intro">These library entries are illustrations of the same kind of job, not client results.</p>
{list_html}{landings_html}
          </div>
          {graphic}
        </div>
        <a class="button ghost" href="../use-cases/">All use cases</a>
      </section>
"""


def faq_html(faqs: list[tuple[str, str]]) -> str:
    parts = []
    for q, a in faqs:
        parts.append(
            f'          <details class="faq-item"><summary>{q}</summary><p>{a}</p></details>'
        )
    return "\n".join(parts)


def buyer_details_html(page: dict) -> str:
    """Concrete qualification and deliverable details for prospective buyers."""
    details = page["buyer_details"]
    cards = []
    for label, items in details:
        item_html = "".join(f"<li>{item}</li>" for item in items)
        cards.append(
            f"""          <article class="buyer-detail-card">
            <h3>{label}</h3>
            <ul>{item_html}</ul>
          </article>"""
        )
    return f"""
      <section class="section service-buyer-details">
        <div class="section-heading stacked">
          <h2>Clear scope before the build starts.</h2>
          <p class="section-intro">The tools depend on the problem. Before work starts, we agree on what I will fix, what you will get, what access I need, and who owns the result.</p>
        </div>
        <div class="buyer-detail-grid">
{chr(10).join(cards)}
        </div>
      </section>"""


def pfd_card_html(page: dict) -> str:
    """PFD L1/L3: buyer-recognizable pains (three rows, no catch-all)."""
    pains = page.get("pfd_pains") or []
    if not pains:
        return ""
    label = page.get("pfd_label", "Problems I help fix")
    caption = page.get("pfd_caption", "")
    rows = []
    for title, body in pains[:3]:
        rows.append(
            f"""            <li>
              <strong>{title}</strong>
              <span>{body}</span>
            </li>"""
        )
    caption_html = (
        f'              <span class="portrait-caption">{caption}</span>\n'
        if caption
        else ""
    )
    return f"""
        <aside class="hero-panel service-pfd-card" aria-label="Typical client pains">
          <div class="hero-identity">
            <div>
              <p class="snapshot-label">{label}</p>
{caption_html}            </div>
          </div>
          <ul class="problem-list">
{chr(10).join(rows)}
          </ul>
        </aside>
"""


PAGES = [
    {
        "slug": "hermes-agents",
        "filename": "hermes-agents.html",
        "title": "Hermes SI (AI) Agents | GemmiSI",
        "meta_description": "Install a Hermes SI (AI) Desk on a Mac you control. Windows is extra, quoted separately. ChatGPT and Claude are examples; you pay those bills.",
        "service_name": "Hermes Agent setup",
        "eyebrow": "On your machine",
        "h1": "Hermes is an SI agent on your computer, not another chat tab.",
        "lead": "ChatGPT and Claude are chat boxes. Hermes is the software around them: an SI (Super Intelligence, the new name for AI) agent on a Mac you control. It uses the model you already pay for and can work with your files and tools. If a ChatGPT seat is already on the bill and sitting idle, we put it on a real job. I install it, write the limits, and hand it off so you can run it.",
        "cta_primary": "Book a free 30-minute consultation",
        "closing_intro": "Tell me what you want the agent to do. Book a free 30-minute consultation. Bring questions.",
        "scope_intro": "Hermes runs on a Mac you control, uses the model you already pay for, and works only inside limits we write down first. You leave with a running install you can use yourself.",
        "pfd_label": "When people ask for an agent",
        "pfd_caption": "For people who want a working install they can run themselves.",
        "pfd_pains": [
            (
                "Chat tools forget the business overnight",
                "Hermes stays on your machine with your files and tools, so it already knows the work.",
            ),
            (
                "You don’t want an agent touching the wrong files",
                "We agree on folders, accounts, and what it must not do before it starts working.",
            ),
            (
                "You don’t have time to learn the stack",
                "I do the install, configuration, and a short walkthrough so you can use it the same day.",
            ),
        ],
        "sections": [
            (
                "What Hermes is",
                "Hermes is not a website and not another ChatGPT tab. It is software we install on your machine. The model — ChatGPT, Claude, or another one you choose — is the brain. Hermes is the software around it: it can open files, draft messages, run a checklist, and remember your rules, only in the folders and accounts we agree on first.",
            ),
            (
                "What this looks like",
                "I start with the jobs you want the agent to do. Then I install Hermes, set it up for your work, and write the rules for which projects it may touch. You leave with a working agent and a short way to run it.",
            ),
            (
                "What gets set up",
                "Hermes Agent install on your Mac • Setup for your files and tools • Clear project and account limits • A first real task so you see it work • Notes so you can keep using it",
            ),
            (
                "Proof you can expect",
                "I recently set one up for a client and handed it off as a working install. I also build agent workflows with review steps when the job needs them.",
            ),
        ],
        "faq_topic": "Hermes Agent setup",
        "buyer_details": [
            ("Good fit when", ["You want an agent on your own computer, not another chat tab", "You need the install, limits, and first setup done correctly", "You would rather pay for a working install than spend a week figuring it out"]),
            ("What you receive", ["Working Hermes install and configuration", "Skills, memory, and written limits for your projects", "Handoff session and short run notes"]),
            ("What I need from you", ["A Mac you control and can install software on", "The first jobs you want the agent to do", "Which folders, repos, and accounts it may and may not touch"]),
            ("Engagement options", ["Starter, Operator, or Connected Desk — see the pricing page", "Setup plus a first real workflow", "Ongoing care after handoff"]),
        ],
        "layout": "split",
        "packages_note": (
            "Three Desk setups, with prices.",
            "Starter, Operator, and Connected Desk are the Hermes installs. What’s included, what’s not, and the other prices are on the pricing page. The next step is still a free 30-minute consultation.",
            "../pricing.html#desks",
            "See pricing",
        ),
        "related_jobs": [
            (
                "Need a Custom GPT or a script instead of a Desk?",
                "A Hermes Desk is one packaged install. Workflow automation and Custom GPTs are a different job when a chat tool or script fits better.",
                "ai-automation.html",
                "SI automation",
            ),
        ],
        "related_use_cases": [
            "standing-si-desk-approval-queue",
            "inbox-triage",
            "weekly-owner-snapshot",
            "after-hours-inquiry-triage",
        ],
        "related_landings": [
            ("/use-cases/", "the use-case hub"),
            ("/use-cases/industry/any-business/", "any-business use cases"),
            ("/use-cases/function/customer-support/", "customer support"),
        ],
        "faqs": [
            (
                "Does Hermes run on my own computer?",
                f"Yes. {OWN_EQUIPMENT} We agree on folders, repos, and accounts first.",
            ),
            (
                "Will the agent send messages or change files on its own?",
                f"No. {APPROVAL_LINE} We write those limits down before the Desk starts working.",
            ),
            (
                "What is Hermes?",
                "Hermes is an SI agent you run on your own computer. ChatGPT and Claude are chat boxes. Hermes is the software around them: it can work with your files and tools, follow written limits, and remember your rules. I install a Desk and hand it off so you can run it.",
            ),
            (
                "Can I use a ChatGPT seat I already pay for?",
                'Yes. A Desk uses the ChatGPT or Claude seat you already pay for around files you control. You keep those bills. Named Desk prices are on the <a href="../pricing.html">pricing page</a>.',
            ),
            (
                "What does Starter Desk include?",
                "Hermes on a Mac you control, written limits, one channel, one standard connection, a proof task, and a walkthrough. CRM plus books is a Connected Desk. Full prices are on the pricing page.",
            ),
            (
                "How do we start?",
                "Book a free 30-minute consultation. Bring what you want the agent to do and which tools you use. No note required.",
            ),
        ],
    },
    {
        "slug": "ai-automation",
        "filename": "ai-automation.html",
        "title": "SI & AI Workflow Automation | GemmiSI",
        "meta_description": "SI & AI workflow automation, Custom GPTs, and unused ChatGPT seats on real weekly jobs. Remote or North Miami Beach / South Florida.",
        "service_name": "SI tools and workflow automation",
        "eyebrow": "SI workflows",
        "h1": "Turn SI tests into tools your team uses each week",
        "lead": "I help teams move from random SI (Super Intelligence, the new name for AI) tests to useful tools. These tools can help with research, reports, drafts, checks, and intake. If you already pay for ChatGPT and it sits unused, we put that seat on a weekly job people can review.",
        "scope_intro": "I find where your team loses time to manual steps, build the smallest useful automation, and show the team how to run it.",
        "pfd_label": "When teams call for SI automation",
        "pfd_caption": "For teams that need a working tool, not another demo.",
        "pfd_pains": [
            (
                "SI tests never reach daily work",
                "Map the real steps, choose simple tools, and build something the team can run.",
            ),
            (
                "Manual copy-paste between tools",
                "Connect files, CRMs, inboxes, and apps so the work moves in one clear flow.",
            ),
            (
                "No checks on SI output",
                "Add reviews, clear steps, and training so people can trust the results.",
            ),
        ],
        "sections": [
            (
                "What this looks like",
                "I start with the work, not the SI model. We find where time is lost and which choices need a person. Then I build the smallest useful system and show the team how to run it.",
            ),
            (
                "Common project types",
                "Research and summary tools • Report helpers • Ecommerce and work intake • Draft and quality checks • Custom GPTs with review steps • Connections between files, CRMs, and other tools",
            ),
            (
                "Proof you can expect",
                "I have 9+ years in operations and systems, including multi-brand ecommerce. I test the work with real examples and users before I call it done.",
            ),
        ],
        "faq_topic": "SI tools and workflow automation",
        "buyer_details": [
            ("Good fit when", ["A repeated workflow is still manual", "SI experiments need clear limits and an owner", "Your team needs one reviewed process—not another tool demo"]),
            ("What you receive", ["Workflow map and scoped implementation plan", "Working automation, assistant, or integration", "Testing notes, written steps, and a team handoff"]),
            ("What I need from you", ["A workflow owner who knows the real process", "Representative examples or safe test data", "Access to approved tools, exports, or APIs"]),
            ("Engagement options", ["Audit and roadmap", "Short implementation project", "Ongoing improvement and support"]),
        ],
        "layout": "split",
        "packages_note": (
            "Quoted after Paid Discovery.",
            "Custom GPTs and workflow automation are scoped as custom work. Paid Discovery maps one workflow, then a written quote. Named prices are on the pricing page.",
            "../pricing.html#consulting",
            "See pricing",
        ),
        "related_use_cases": [
            "inbox-triage",
            "quote-follow-ups",
            "invoice-intake-to-draft-bills",
            "bilingual-english-spanish-replies",
            "appointment-reminders",
            "client-document-chasing",
        ],
        "related_landings": [
            ("/use-cases/", "the use-case hub"),
            ("/use-cases/industry/any-business/", "any-business use cases"),
            ("/use-cases/function/customer-support/", "customer support"),
            ("/use-cases/function/sales-follow-up/", "sales & follow-up"),
        ],
        "faqs": [
            (
                "Does this run on my own equipment?",
                f"Yes. {OWN_EQUIPMENT}",
            ),
            (
                "Will SI send or change things without me?",
                f"No. {APPROVAL_LINE}",
            ),
            (
                "Do you only build Custom GPTs?",
                "No. They are only one option. A simple script, automation, or dashboard may fit the job better.",
            ),
            (
                "Can you work with our existing tools?",
                "Usually. I can connect files, CRMs, online stores, email, chat tools, and cloud data when access is available.",
            ),
            (
                "Can you put unused ChatGPT seats to work?",
                'Yes. Many jobs use the ChatGPT or Claude seat you already pay for around files and tools you already have. A <a href="hermes-agents.html">Hermes Desk</a> is one option when an agent on your Mac fits.',
            ),
            (
                "How do we start?",
                "Book a free 30-minute consultation. Bring a short note about the problem and tools if you have one. No note required.",
            ),
        ],
        "related_jobs": [
            (
                "Want the agent on your Mac, not in a chat tab?",
                "Unused ChatGPT seats often fit a Hermes Desk: install, limits, and a first real task on a machine you control. Only when that actually fits.",
                "hermes-agents.html",
                "Hermes Desk setup",
            ),
        ],
    },
    {
        "slug": "dashboards-reporting",
        "filename": "dashboards-reporting.html",
        "title": "SI & AI Dashboards & Reporting | GemmiSI",
        "meta_description": "SI & AI dashboards, spreadsheet cleanup, and trusted daily reporting for ecommerce and ops teams. BigQuery when it fits. Remote or North Miami Beach.",
        "service_name": "Dashboards, reporting, and data cleanup",
        "eyebrow": "Data visibility",
        "h1": "Dashboards and reports your team can trust each day",
        "lead": "Work slows down when each team has different numbers. I clean the data, set clear rules, and build reports people can trust — including SI (Super Intelligence, the new name for AI) help for notes and checks. The goal is a useful daily view, not another report to rebuild by hand.",
        "scope_intro": "I clean the data, agree on the numbers that matter, and build a daily view your team can trust — not another export to rebuild by hand.",
        "pfd_label": "When the numbers are not clear",
        "pfd_caption": "For teams that are tired of guessing from exports and mixed-up files.",
        "pfd_pains": [
            (
                "Nobody agrees which numbers are real",
                "Check the sources, remove repeat entry, and agree on what each number means.",
            ),
            (
                "Reports take days to assemble",
                "Turn raw exports into a daily view with simple checks and tools that fit the job.",
            ),
            (
                "Leaders still can’t see what is happening",
                "Build clear views for orders, inventory, sales, or daily work.",
            ),
        ],
        "sections": [
            (
                "What this looks like",
                "I check which files drive decisions and remove repeat work. We agree on the numbers that matter. Then I turn the raw data into a clear daily view.",
            ),
            (
                "Common project types",
                "Spreadsheet cleanup • Ecommerce and inventory reports • CRM and sales views • Shipping and operations measures • Moving data into BigQuery or another store • Training teams to maintain the reports",
            ),
            (
                "Proof you can expect",
                "I built daily dashboards for multi-brand ecommerce. They brought orders, inventory, ads, shipping, and team work into one place. I have also worked with 95k+ tracked items.",
            ),
        ],
        "faq_topic": "dashboards, reporting, and data cleanup",
        "buyer_details": [
            ("Good fit when", ["Teams disagree about which numbers are real", "Weekly reporting depends on copy-paste", "Decision-makers need one dependable operating view"]),
            ("What you receive", ["Source and metric audit", "Cleaned model, dashboard, or reporting workflow", "Definitions, checks, and maintenance notes"]),
            ("What I need from you", ["Current exports, sheets, or approved system access", "The decisions each report should support", "An owner for metric definitions and sign-off"]),
            ("Engagement options", ["Reporting audit and cleanup", "Dashboard implementation", "Ongoing reporting support"]),
        ],
        "layout": "proof",
        "proof_strip": "From conflicting spreadsheets → one trusted morning dashboard.",
        "packages_note": (
            "Quoted after Paid Discovery.",
            "Dashboards and reporting are custom work: Paid Discovery maps the workflow, then a written build quote. Named prices are on the pricing page.",
            "../pricing.html#consulting",
            "See pricing",
        ),
        "related_jobs": [
            (
                "Inventory and listings still fighting each other?",
                "Dashboards show the week. Ecommerce ops is the listings, inventory, and fulfillment work underneath.",
                "ecommerce-operations.html",
                "Ecommerce operations",
            ),
        ],
        "related_use_cases": [
            "weekly-owner-snapshot",
            "weekly-team-report",
            "revenue-in-one-view",
            "cash-flow-look-ahead",
            "ad-spend-vs-results",
        ],
        "related_landings": [
            ("/use-cases/function/reporting-dashboards/", "reporting & dashboards"),
            ("/use-cases/industry/ecommerce/", "ecommerce use cases"),
        ],
        "faqs": [
            (
                "Does this run on my own accounts?",
                f"Yes. {OWN_EQUIPMENT}",
            ),
            (
                "Will SI change source systems on its own?",
                f"No. {APPROVAL_LINE} Dashboards read and draft; you decide what gets written back.",
            ),
            (
                "Can you fix our spreadsheets without a full BI project?",
                "Often. Many projects start by cleaning the files, adding checks, and naming an owner. A larger tool may not be needed.",
            ),
            (
                "Do you build the dashboards or only advise?",
                "Both. I can build the queries, charts, data model, and notes when that is the fastest way to help.",
            ),
            (
                "What tools do you use?",
                "It depends on your tools. I use Google Sheets, BigQuery, dashboard tools, Python, and system exports. I try to use tools you already pay for.",
            ),
            (
                "How do we start?",
                "Book a free 30-minute consultation. Bring which reports you trust, which you do not, and who uses them. No note required.",
            ),
        ],
    },
    {
        "slug": "ecommerce-operations",
        "filename": "ecommerce-operations.html",
        "title": "Ecommerce Ops with SI (AI) | GemmiSI",
        "meta_description": "Ecommerce ops with SI (AI): Amazon, eBay, inventory, fulfillment, listings, and marketplace reporting. Remote or South Florida. Free 30-minute consultation.",
        "service_name": "Ecommerce operations systems",
        "eyebrow": "Ecommerce ops",
        "h1": "Fix the ecommerce problems that keep coming back",
        "lead": "I help online sellers fix problems with listings, inventory, shipping, and reports. I build clear work steps, simple automation — including SI (Super Intelligence, the new name for AI) help for research, drafts, and checks — and useful daily views. My approach comes from real warehouse and marketplace work.",
        "scope_intro": "I map how product, inventory, and order data moves, fix the weak points in listings and handoffs, and turn scattered work into clear daily steps.",
        "pfd_label": "When ecommerce work feels chaotic",
        "pfd_caption": "For Amazon, eBay, and product teams that spend each week putting out fires.",
        "pfd_pains": [
            (
                "Inventory and listings don’t match reality",
                "Match sales-channel rules, tracked items, and product data so the team uses the same facts.",
            ),
            (
                "Shipping and handoffs break in busy seasons",
                "Write down warehouse steps, quality checks, and when to ask for help.",
            ),
            (
                "Marketplace reports are always late",
                "Connect exports and work data so the team can spot problems early.",
            ),
        ],
        "sections": [
            (
                "What this looks like",
                "I map how product, order, and inventory data moves. Then I fix weak points in listings, checks, handoffs, and reports. The goal is less time spent in emergency spreadsheets.",
            ),
            (
                "Common project types",
                "Amazon and eBay work steps • Tracked and multi-SKU inventory • Stocky dump → weekly system • Better listings and product data • Photo-to-listing copy you can paste into eBay • Shipping and warehouse guides • Marketplace reports and dashboards • SI help for research, drafts, and checks",
            ),
            (
                "Proof you can expect",
                "I have worked in multi-brand ecommerce, FBA, and eBay operations. I have built systems that turn scattered work into clear daily steps.",
            ),
        ],
        "faq_topic": "ecommerce operations systems",
        "buyer_details": [
            ("Good fit when", ["Inventory, listings, or fulfillment repeatedly fall out of sync", "Peak periods expose handoffs nobody wrote down", "Marketplace reporting arrives too late to act"]),
            ("What you receive", ["Current-state process and failure-point map", "Improved workflow, written steps, and lightweight tooling", "Owner checks, clear steps for problems, and handoff notes"]),
            ("What I need from you", ["Examples of the highest-cost weekly problems", "Safe exports or approved access to relevant tools", "An operations owner available for testing"]),
            ("Engagement options", ["Ops audit and roadmap", "Focused workflow implementation", "Ongoing operator-builder support"]),
        ],
        "layout": "steps",
        "packages_note": (
            "Quoted after Paid Discovery.",
            "Ecommerce ops is custom work unless it is a named Desk. Paid Discovery maps one workflow, then a written quote. Stocky dump recovery is a separate, named job.",
            "../pricing.html#consulting",
            "See pricing",
        ),
        "related_job": (
            "Stocky shut down. Your dump still has to run the week.",
            "If the operating system was Stocky and you now have CSVs in Sheets, I have a page for that job. It is not another inventory app.",
            "stocky-recovery.html",
            "Stocky dump recovery",
        ),
        "related_jobs": [
            (
                "Reports you cannot trust?",
                "If the weekly pain is the numbers, not the warehouse, start with dashboards and reporting.",
                "dashboards-reporting.html",
                "Dashboards &amp; reporting",
            ),
        ],
        "related_use_cases": [
            "reorder-from-sales-pace",
            "abandoned-checkout-follow-up-drafts",
            "shipping-exceptions-package-watch",
            "store-stock-and-spreadsheet-agreement",
            "marketplace-listing-sync-checks",
            "catalog-pricing-and-margin-check",
        ],
        "related_landings": [
            ("/use-cases/industry/ecommerce/", "ecommerce use cases"),
            ("/use-cases/function/inventory-orders/", "inventory & orders"),
        ],
        "faqs": [
            (
                "Does this run on my own store and accounts?",
                f"Yes. {OWN_EQUIPMENT}",
            ),
            (
                "Will SI refund orders or post listings?",
                f"No. {APPROVAL_LINE} That includes refunds, marketplace posts, and customer messages.",
            ),
            (
                "Can you help with Amazon and eBay at the same time?",
                "Yes. I can help with shared inventory, different listing rules, and reports that bring both channels together.",
            ),
            (
                "Do you replace an agency or VA team?",
                "No. I help the team work better with clear steps, tools, and cleaner data.",
            ),
            (
                "Can you help after Stocky shut down?",
                'Yes. If you exported a Shopify Stocky CSV dump, I have a dedicated <a href="stocky-recovery.html">recovery page</a>. That job is making the dump operable for the week, not selling another inventory app.',
            ),
            (
                "How do we start?",
                "Book a free 30-minute consultation. Bring where you sell, how many items you manage, and the top two weekly problems. No note required.",
            ),
        ],
    },
    {
        "slug": "tutoring-project-help",
        "filename": "tutoring-project-help.html",
        "title": "SI (AI) Tutoring & Project Help | GemmiSI",
        "meta_description": "One-on-one SI (AI) tutoring, ChatGPT help, and technical project pairing. Remote or South Florida. $125/hr after a free consult.",
        "service_name": "Technical tutoring, coaching, and project help",
        "eyebrow": "Hands-on help",
        "h1": "Hands-on help with SI tools, workflows, and technical projects",
        "lead": "Not every problem needs a large project. I help founders, students, and teams learn SI (Super Intelligence, the new name for AI) tools, fix workflows, and finish builds. We agree on a clear goal before the session starts.",
        "scope_intro": "We focus on one problem at a time. I work through the fix with you and write down the steps so you can use them again.",
        "pfd_label": "When you need hands-on help",
        "pfd_caption": "For people who want help now and clear steps they can use later.",
        "pfd_pains": [
            (
                "Stuck on a build with no one to pair with",
                "Review the system, fix the problem, and write down steps you can repeat.",
            ),
            (
                "SI tools feel useful but risky",
                "Learn simple prompts, safety checks, and steps that fit your tools.",
            ),
            (
                "Not sure whether to build or buy",
                "Compare the options before you agree to a larger project.",
            ),
        ],
        "sections": [
            (
                "What this looks like",
                "We focus on one problem at a time. I explain the system, work through the fix with you, and write down the steps. You leave with something you can use again.",
            ),
            (
                "Common request types",
                "Learning ChatGPT, Custom GPTs, or SI agents • Spreadsheet and dashboard help • Ecommerce work steps • Fixing automations • Technical interview practice • Helping founders decide what to build or buy",
            ),
            (
                "Who it is for",
                "This is for students, solo founders, operators, and teams that want hands-on help. I do not give legal, medical, or financial advice.",
            ),
        ],
        "faq_topic": "technical tutoring, coaching, and project help",
        "buyer_details": [
            ("Good fit when", ["You are blocked on a specific build or workflow", "A team needs practical SI-tool training", "You want to validate an approach before a larger project"]),
            ("What you receive", ["Focused working session or short project burst", "A resolved blocker, documented approach, or working draft", "Repeatable next steps you can own"]),
            ("What I need from you", ["The goal and current blocker", "Relevant files, screenshots, or a safe example", "Your timezone, availability, and desired pace"]),
            ("Engagement options", ["One-on-one working session", "Short project help", "Team workshop and follow-up"]),
        ],
        "layout": "simple",
        "packages_note": (
            "Tutoring rates are listed.",
            "$125 per hour. Minimum booking 90 minutes at $175. Start with a free 30-minute consultation.",
            "../pricing.html#tutoring",
            "See tutoring rates",
        ),
        "related_jobs": [
            (
                "Need a working tool built, not a lesson?",
                "Tutoring is pairing on a clear goal. Larger automations and Custom GPTs live on the SI automation page. Rates are on the <a href=\"../pricing.html#tutoring\">pricing page</a>.",
                "ai-automation.html",
                "SI automation",
            ),
        ],
        "related_use_cases": [
            "sops-from-walkthroughs",
            "internal-answers-helper",
            "website-chat-assistant",
            "routine-form-filling",
        ],
        "related_landings": [
            ("/use-cases/", "the use-case hub"),
            ("/use-cases/industry/education/", "education use cases"),
            ("/use-cases/function/research-documents/", "research & documents"),
        ],
        "faqs": [
            (
                "Do we work in my own accounts?",
                f"Yes. {OWN_EQUIPMENT}",
            ),
            (
                "Do you give legal, medical, or tax advice?",
                "No. Tutoring is hands-on help with tools and projects. I do not give legal, medical, accounting, or tax advice.",
            ),
            (
                "Is this the same as full consulting?",
                "Tutoring is for a small, clear goal. Larger builds become consulting or contract work with a written plan.",
            ),
            (
                "Can you help my team adopt a new SI tool?",
                "Yes. I can teach the tool, set safety checks, share prompt patterns, and write simple steps for the team.",
            ),
            (
                "How do we start?",
                "Book a free 30-minute consultation. Bring what you want to learn or finish, plus your time zone. No note required. Tutoring rates are on the <a href=\"../pricing.html#tutoring\">pricing page</a>.",
            ),
        ],
    },
]


FOOTER_SCRIPTS = f"""
    <footer>
      <a class="footer-brand" href="../index.html" aria-label="GemmiSI home">
        <img class="footer-lockup" src="../assets/brand/gemmisi-lockup-dark.svg" alt="" width="123" height="28" />
      </a>
      <p>© <span id="year"></span> Yonatan Gemmi. Based in North Miami Beach, Florida · Miami-Dade, Broward, and remote</p>
      <p class="footer-nav">
        <a href="../index.html">Home</a>
        <a href="../use-cases/">Use cases</a>
        <a href="../pricing.html">Pricing</a>
        <a href="hermes-agents.html">Hermes desks</a>
        <a href="ai-automation.html">SI automation</a>
        <a href="dashboards-reporting.html">Dashboards</a>
        <a href="ecommerce-operations.html">Ecommerce</a>
        <a href="tutoring-project-help.html">Tutoring</a>
        <a href="https://calendly.com/josh-gemmi/30min" target="_blank" rel="noreferrer">Book consultation</a>
      </p>
    </footer>
  </div>
{NAV_SCRIPT}{CLOUDFLARE_WEB_ANALYTICS}</body>
</html>
"""


def packages_note_html(page: dict) -> str:
    note = page.get("packages_note")
    if not note:
        return ""
    title, body, href, link = note
    return f"""
      <section class="section pricing-pointer" aria-labelledby="pricing-pointer-title">
        <div>
          <h2 id="pricing-pointer-title">{title}</h2>
          <p class="section-intro">{body}</p>
        </div>
        <a class="button ghost" href="{href}">{link}</a>
      </section>"""


def sections_cards_html(page: dict) -> str:
    parts: list[str] = []
    for title, body in page["sections"]:
        parts.append(
            f"""        <article>
          <h3>{title}</h3>
          <p>{body}</p>
        </article>"""
        )
    return "\n".join(parts)


def scope_block(page: dict) -> str:
    layout = page.get("layout", "split")
    intro = page.get("scope_intro", "This is one of the kinds of work I take on. The homepage lists my other services.")
    cards = sections_cards_html(page)

    if layout == "proof":
        proof = page.get("proof_strip", "From scattered exports to one trusted morning view.")
        return f"""
      <section class="section service-layout-proof">
        <div class="proof-strip" role="presentation">
          <p class="proof-strip-label">{proof}</p>
        </div>
        <div class="section-heading stacked">
          <h2>Focused help for one kind of problem.</h2>
          <p class="section-intro">{intro}</p>
        </div>
        <div class="offering-list service-detail-stack">
{cards}
        </div>
      </section>"""

    if layout == "steps":
        return f"""
      <section class="section split service-layout-steps">
        <div>
          <h2>How we improve the work, one step at a time.</h2>
          <p class="section-intro">{intro}</p>
        </div>
        <div class="offering-list">
{cards}
        </div>
      </section>"""

    if layout == "simple":
        return f"""
      <section class="section service-layout-simple">
        <div class="section-heading stacked">
          <h2>Practical help without a large project.</h2>
          <p class="section-intro">{intro}</p>
        </div>
        <div class="offering-list service-detail-stack">
{cards}
        </div>
      </section>"""

    return f"""
      <section class="section split">
        <div>
          <h2>Focused help for one kind of problem.</h2>
          <p class="section-intro">{intro}</p>
        </div>
        <div class="offering-list">
{cards}
        </div>
      </section>"""


def render(page: dict) -> str:
    slug = page["slug"]
    canonical = f"{BASE}/services/{page['filename']}"
    faqs = page["faqs"]
    if not (4 <= len(faqs) <= 6):
        raise SystemExit(f"{page['slug']} must have 4–6 FAQs, found {len(faqs)}")
    title = escape(page["title"])
    meta_description = escape(clip_meta(page["meta_description"]), quote=True)
    service_name = escape(page["service_name"])
    faq_topic = escape(page["faq_topic"])
    cta_primary = escape(page.get("cta_primary", "Book a free 30-minute consultation"))
    closing_intro = page.get(
        "closing_intro",
        "Thirty minutes. Google Meet. Bring questions. No note to send first.",
    )
    schema = faq_schema(
        faqs,
        service_name=page["service_name"],
        meta_description=page["meta_description"],
        canonical=canonical,
        page_name=page["title"],
        breadcrumb_label=page["service_name"],
    )
    og_block = common_head_tags(title=title, description=meta_description, canonical=canonical)
    scope_html = scope_block(page)
    packages_html = packages_note_html(page)
    buyer_html = buyer_details_html(page)
    related_case_study = ""
    if slug in ("ai-automation", "hermes-agents"):
        related_case_study = """
      <section class="section related-case-study" aria-labelledby="related-ai-case-study-title">
        <div>
          <h2 id="related-ai-case-study-title">See how I built an SI content system with safety checks.</h2>
          <p class="section-intro">This private-client example shows review steps, automatic checks, safe stops, and an optional hands-free mode.</p>
        </div>
        <a class="button ghost" href="../work/governed-ai-content-engine.html">View the case study</a>
      </section>
"""
    related_case_study += related_use_cases_html(page)
    related_jobs = []
    if page.get("related_job"):
        related_jobs.append(page["related_job"])
    related_jobs.extend(page.get("related_jobs") or [])
    for i, (job_title, job_body, job_href, job_link) in enumerate(related_jobs):
        aid = "related-job-title" if i == 0 else f"related-job-title-{i}"
        related_case_study += f"""
      <section class="section related-case-study" aria-labelledby="{aid}">
        <div>
          <h2 id="{aid}">{job_title}</h2>
          <p class="section-intro">{job_body}</p>
        </div>
        <a class="button ghost" href="{job_href}">{job_link}</a>
      </section>
"""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <meta name="description" content="{meta_description}" />
  <link rel="canonical" href="{canonical}" />
  <meta name="robots" content="index, follow" />
  <meta name="author" content="Yonatan Gemmi" />
{og_block}
{font_and_css_links(stylesheet=f"../styles.css?v={CSS_VERSION}", extra_css=f"../assets/use-cases.css?v={CSS_VERSION}")}
{icon_links()}
  <script type="application/ld+json">
{schema}
  </script>
</head>
<body>
  <div class="site-shell">
    <header class="nav">
      <a class="brand" href="../index.html" aria-label="GemmiSI home">
        <img class="brand-lockup" src="../assets/brand/gemmisi-lockup-dark.svg" alt="" width="159" height="36" />
      </a>
      <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav" aria-label="Open site menu">
        <span class="nav-toggle__bars" aria-hidden="true"></span>
        <span class="nav-toggle__label">Menu</span>
      </button>
{nav_for(slug)}
    </header>

    <main id="top">
      <section class="hero service-landing-hero">
        <div class="hero-copy">
          <nav class="breadcrumb" aria-label="Breadcrumb">
            <a href="../index.html">Home</a>
            <span aria-hidden="true">/</span>
            <span>{service_name}</span>
          </nav>
          <h1>{page['h1']}</h1>
          <p class="lead">{page['lead']}</p>
          <div class="actions">
            <a class="button primary" href="{CALENDLY}" target="_blank" rel="noreferrer">{cta_primary}</a>
            <a class="button ghost" href="../index.html#work">See work examples</a>
          </div>
        </div>
{pfd_card_html(page)}
      </section>
{scope_html}{packages_html}{related_case_study}
{buyer_html}

      <section id="faq" class="section">
        <div class="section-heading stacked">
          <h2>Questions about {faq_topic}.</h2>
        </div>
        <div class="faq-grid faq-accordion">
{faq_html(faqs)}
        </div>
      </section>

      <section class="section closing-card service-landing-cta">
        <div>
          <h2>Book a free 30-minute consultation.</h2>
          <p class="section-intro">{closing_intro}</p>
        </div>
        <div class="contact-panel">
          <a class="button primary full" href="{CALENDLY}" target="_blank" rel="noreferrer">{cta_primary}</a>
          <p class="contact-quiet">Or <a class="text-link" href="mailto:y@gemmisi.com">email me</a> instead.</p>
        </div>
      </section>
    </main>
{FOOTER_SCRIPTS}
"""


def main() -> None:
    SERVICES_DIR.mkdir(exist_ok=True)
    for page in PAGES:
        path = SERVICES_DIR / page["filename"]
        path.write_text(render(page), encoding="utf-8")
        print("wrote", path.relative_to(ROOT))


if __name__ == "__main__":
    main()