#!/usr/bin/env python3
"""Patch JSON-LD and common SEO head tags on hand-maintained HTML pages."""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seo_schema import (
    BASE,
    CALENDLY,
    _offer,
    breadcrumb_node,
    common_head_tags,
    faq_node,
    graph_payload,
    person_node,
    professional_service_node,
    service_node,
    webpage_node,
    website_node,
)

ROOT = Path(__file__).resolve().parent.parent

HOME_FAQS = [
    (
        "What happens in the free consultation?",
        "Thirty minutes on Google Meet, at no charge. Bring your questions. We'll talk through the work and the simplest next step. This is a consultation, not paid Discovery or a working session.",
    ),
    (
        "What should I prepare?",
        "No document or detailed brief is required. Bring the task, question, or problem you want help with. A simple example is useful if you have one.",
    ),
    (
        "Can I book for a small job or personal project?",
        "Yes. You do not need a large business project. Small setups, tutoring, troubleshooting, and one-on-one project help are welcome.",
    ),
    (
        "What does paid work cost?",
        "Fixed setups and tutoring rates are on the pricing page. Custom work is scoped and quoted separately. We agree on the price before work begins.",
    ),
    (
        "Am I committing to a project by booking?",
        "No. The consultation gives you direction. If you want to continue, we agree on a paid next step. You can also take the advice and decide later.",
    ),
    (
        "Can you help if Stocky shut down?",
        "Yes. If you ran Shopify inventory in Stocky and now have a CSV dump, that is a specific ecommerce job: a weekly system from the export, not another inventory app. See the Stocky dump recovery page.",
    ),
]

PRICING_FAQS = [
    (
        "What is Hermes?",
        "Hermes is an AI agent you run on your own computer. ChatGPT and Claude are chat boxes. Hermes is the software around them: it can work with your files and tools, follow written limits, and remember your rules. I install a Desk and hand it off so you can run it.",
    ),
    (
        "Is the 30-minute consultation free?",
        "Yes. Thirty minutes. No charge. Google Meet. We talk about your work and see if I can help.",
    ),
    (
        "Do I have to get a Hermes Desk?",
        "No. Discovery and builds are custom work: dashboards, system integrations, reporting systems, workflow automation, and cleanup of tools you already have. A Hermes Desk is a packaged install. We only recommend one when it actually fits.",
    ),
    (
        "What if I need Hermes plus CRM and accounting?",
        "That is a Connected Desk at $3,500, not a Starter Desk. Starter is one channel and one standard connection on a Mac you control.",
    ),
    (
        "Do I pay for the AI model and app subscriptions?",
        "Yes. You pay for your own model, Hermes, and app subscriptions. That can be ChatGPT, Claude, or another model you choose, including a local one. I install and configure the system on a machine you control.",
    ),
    (
        "Can I run a local model with a Desk?",
        "Yes, as an add-on on an existing Desk. I install it and hook it up after I see the machine. That add-on is quoted. It is not a fixed price.",
    ),
    (
        "What is a Care retainer?",
        "Care starts after a Desk or a build is live. Owner Care is $300 a month: a 45-minute pairing block so you stay fluent on the live Desk, plus getting it running if it will not start. Starter Care is $750 a month for fixes, small edits, a monthly check, help changing the model on the same Desk, and short questions from the people who use it. It does not add new systems. Operator Care is $1,500 a month and includes one small add each month on the system you already have. All three are month to month with 30 days' notice. Care is not unlimited chat, not a new Desk, and not a rebuild.",
    ),
    (
        "Do you offer Advisory or Fractional CTO?",
        "Yes. Seats are scarce. Ask first. These are monthly leadership seats, not Care and not a one-time Desk. Details are on the Advisory and Fractional page.",
    ),
    (
        "What payment methods do you accept?",
        "I accept bank wire, Zelle, X Money, USDC, or Bitcoin (BTC). Other crypto only if we agree first. Inquire for more info.",
    ),
    (
        "How do we start?",
        "Pick a time at https://calendly.com/josh-gemmi/30min. The free 30-minute consultation is the first step. No note to send first.",
    ),
    (
        "Does Stocky dump recovery have its own price?",
        "No. Starter Desk at $500 and Operator Desk at $1,500 are the usual sizes for turning a Stocky CSV dump into a weekly system. A larger rebuild is Paid Discovery. The recovery page explains the job. It is not another inventory app.",
    ),
]

ADVISORY_FAQS = [
    (
        "Are these retainers open to lots of companies?",
        "No. Seats are scarce. Ask first. If there is no seat, I will say so.",
    ),
    (
        "What is the difference between Advisory Light and Fractional CTO?",
        "Advisory Light is advice: priorities, a roadmap, vendor choices, and a written monthly note. No build. Fractional CTO is technical direction plus a real build slice each month.",
    ),
    (
        "Is this the same as Care?",
        "No. Care keeps a live Desk or build working after handoff. These monthly seats are for ongoing leadership.",
    ),
    (
        "How do I inquire?",
        "Email me or book the free 30-minute consultation and say you are asking about Advisory or Fractional CTO. The consultation does not reserve a retainer seat.",
    ),
]

STOCKY_FAQS = [
    (
        "Is this a Stocky replacement app?",
        "No. I am not selling Prediko, Klerio, or another inventory product. If you want a full inventory app, buy one. This job is making the dump operable: a weekly view you can run with Sheets and the ChatGPT or Claude seat you already pay for.",
    ),
    (
        "Is this a Stocky alternative?",
        "No. A Stocky alternative is another inventory app. This is recovery of the CSV export you already have after Stocky shut down — a weekly Shopify inventory view, not a new SKU system to migrate into.",
    ),
    (
        "Did supplier notes and par levels export from Stocky?",
        "Often they did not. SKUs, vendors, and purchase orders usually survive in the CSV. Supplier notes and par levels often stayed in Stocky or in someone's head. We recover what still exists and give the missing pieces a place to live.",
    ),
    (
        "I have a Stocky CSV export. Can you recover Shopify inventory from that?",
        "Yes. SKUs, vendors, and purchase orders usually survive in the dump. I build a weekly reorder view from those files. This is not a Stocky replacement app.",
    ),
    (
        "Starter Desk, Operator Desk, or Paid Discovery?",
        "Starter Desk is $500 for a first working weekly view from the dump. Operator Desk is $1,500 when you also need one defined weekly reorder workflow. If this is a bigger rebuild — many locations, messy vendors, reconstructing pars across a large catalog — that is Paid Discovery at $2,000, then a quoted build. Full prices are on the pricing page.",
    ),
    (
        "Do I need a new AI subscription?",
        "No. The usual setup uses ChatGPT or Claude, the seats you already pay for, around your files. You keep paying those bills. I set up the weekly system. Named Desk details are on the pricing page if you want them.",
    ),
    (
        "How do we start?",
        "Book a free 30-minute consultation. Bring the export folder and the two weekly jobs Stocky used to do. No note required.",
    ),
]


def replace_jsonld(html: str, payload: str) -> str:
    new_block = f'<script type="application/ld+json">\n{payload}\n  </script>'
    updated, n = re.subn(
        r'<script type="application/ld\+json">\s*\{.*?\}\s*</script>',
        new_block,
        html,
        count=1,
        flags=re.DOTALL,
    )
    if n != 1:
        raise SystemExit(f"expected 1 JSON-LD block, found {n}")
    return updated


def replace_between(html: str, start: str, end: str, new: str) -> str:
    i = html.find(start)
    j = html.find(end, i)
    if i < 0 or j < 0:
        raise SystemExit(f"could not find markers {start!r} .. {end!r}")
    return html[:i] + new + html[j:]


def patch_head(
    html: str,
    *,
    title: str,
    description: str,
    canonical: str,
    og_type: str = "website",
    stylesheet: str,
    icon: str,
) -> str:
    html = re.sub(r"<title>.*?</title>", f"<title>{title}</title>", html, count=1, flags=re.DOTALL)
    html = re.sub(
        r'<meta name="description" content=".*?" />',
        f'<meta name="description" content="{description}" />',
        html,
        count=1,
    )
    html = re.sub(
        r'<link rel="canonical" href=".*?" />',
        f'<link rel="canonical" href="{canonical}" />',
        html,
        count=1,
    )
    og = common_head_tags(title=title, description=description, canonical=canonical, og_type=og_type)
    html = re.sub(
        r'  <meta property="og:title".*?(?:\n  <link rel="sitemap"[^\n]*\n)?  <link rel="preconnect"',
        og + '\n  <link rel="preconnect"',
        html,
        count=1,
        flags=re.DOTALL,
    )
    html = re.sub(
        r'<link rel="stylesheet" href="[^"]+" />',
        f'<link rel="stylesheet" href="{stylesheet}" />',
        html,
        count=1,
    )
    return html


def home_graph() -> str:
    return graph_payload(
        [
            website_node(),
            person_node(),
            professional_service_node(),
            webpage_node(
                name="Yonatan Gemmi | AI, automation & operations | North Miami Beach",
                url=f"{BASE}/",
                description=(
                    "Free 30-min consult for AI, automation, dashboards, and ecommerce ops. "
                    "Hermes desks, Stocky dump recovery, and unused ChatGPT seats. Remote or North Miami Beach."
                ),
            ),
            faq_node(HOME_FAQS),
        ]
    )


def pricing_graph() -> str:
    url = f"{BASE}/pricing.html"
    extra_offers = [
        _offer("Care retainer — Owner", f"{url}#retainers", price="300", service="Monthly Care retainer — Owner"),
        _offer("Care retainer — Starter", f"{url}#retainers", price="750", service="Monthly Care retainer — Starter"),
        _offer("Care retainer — Operator", f"{url}#retainers", price="1500", service="Monthly Care retainer — Operator"),
        _offer("Tutoring", f"{url}#tutoring", price="125", service="Tutoring and pairing"),
    ]
    return graph_payload(
        [
            website_node(),
            person_node(),
            professional_service_node(),
            webpage_node(
                name="Pricing | Yonatan Gemmi | South FL",
                url=url,
                description=(
                    "Fixed prices for Hermes Desk setups, Paid Discovery, Care, and tutoring. "
                    "Stocky dump recovery uses Starter or Operator Desk. Free 30-minute consultation."
                ),
            ),
            breadcrumb_node([("Home", f"{BASE}/"), ("Pricing", url)]),
            *extra_offers,
            faq_node(PRICING_FAQS),
        ]
    )


def advisory_graph() -> str:
    url = f"{BASE}/advisory.html"
    return graph_payload(
        [
            website_node(),
            person_node(),
            professional_service_node(include_catalog=True),
            webpage_node(
                name="Advisory & Fractional CTO | Yonatan Gemmi",
                url=url,
                description="Advisory Light and Fractional CTO with Yonatan Gemmi. Extremely limited availability. Inquire first.",
            ),
            breadcrumb_node(
                [
                    ("Home", f"{BASE}/"),
                    ("Pricing", f"{BASE}/pricing.html"),
                    ("Advisory & Fractional", url),
                ]
            ),
            _offer(
                "Advisory Light",
                url,
                price="4500",
                service="Advisory Light monthly retainer",
                description="Advice, a roadmap, vendor choices, and a written monthly note. No build. Inquire first.",
            ),
            _offer(
                "Fractional CTO",
                url,
                price="7500",
                service="Fractional CTO monthly retainer",
                description="Technical direction plus a real build slice each month. Inquire first.",
            ),
            faq_node(ADVISORY_FAQS),
        ]
    )


def stocky_graph() -> str:
    url = f"{BASE}/services/stocky-recovery.html"
    return graph_payload(
        [
            website_node(),
            person_node(),
            professional_service_node(),
            webpage_node(
                name="Stocky Shut Down? Shopify CSV Dump Recovery | Yonatan Gemmi",
                url=url,
                description=(
                    "Stocky shut down Aug 31, 2026. I turn a Shopify CSV export into a weekly inventory system "
                    "using Sheets and ChatGPT or Claude seats you already pay for — not a Stocky replacement app. "
                    "Free 30-minute consultation."
                ),
            ),
            breadcrumb_node(
                [
                    ("Home", f"{BASE}/"),
                    ("Ecommerce operations", f"{BASE}/services/ecommerce-operations.html"),
                    ("Stocky dump recovery", url),
                ]
            ),
            service_node(
                name="Stocky dump recovery",
                description=(
                    "Turn a Shopify Stocky CSV dump into a weekly operating system using tools you already pay for. "
                    "Not an inventory-app replacement."
                ),
                url=url,
            ),
            _offer("Free 30-minute consultation", CALENDLY, price="0", service="30-minute consultation"),
            _offer(
                "Starter Desk",
                f"{BASE}/pricing.html#desks",
                price="500",
                service="Stocky dump to first weekly view",
            ),
            _offer(
                "Operator Desk",
                f"{BASE}/pricing.html#desks",
                price="1500",
                service="Stocky dump plus weekly reorder workflow",
            ),
            _offer(
                "Paid Discovery",
                f"{BASE}/pricing.html#consulting",
                price="2000",
                service="Paid workflow discovery for a larger rebuild",
            ),
            faq_node(STOCKY_FAQS),
        ]
    )


def work_graph() -> str:
    url = f"{BASE}/work/governed-ai-content-engine.html"
    creative = {
        "@type": "CreativeWork",
        "name": "Governed Multi-Agent AI Production System — Anonymized Case Study",
        "headline": "A multi-agent production operation that separates coordination from video execution",
        "description": (
            "An anonymized case study of a multi-agent AI production system designed by Yonatan Gemmi "
            "to turn operator-led creative briefs or research into reviewable concepts, coordinate video "
            "execution across machines, recover from failures, and preserve configurable operator control."
        ),
        "url": url,
        "author": {"@id": "https://nykon1293.github.io/#person"},
        "about": [
            "Multi-agent AI systems",
            "Agent orchestration",
            "Operator-led creative direction",
            "AI social content workflows",
            "AI video production",
            "Distributed AI workflows",
            "Human-in-the-loop systems",
            "Quality assurance",
        ],
    }
    return graph_payload(
        [
            website_node(),
            person_node(),
            professional_service_node(),
            webpage_node(
                name="Multi-Agent AI Production Case Study | Yonatan Gemmi",
                url=url,
                description=(
                    "An anonymized multi-agent AI case study by Yonatan Gemmi: operator-led briefs, "
                    "coordinated video execution, recovery, and configurable control."
                ),
            ),
            breadcrumb_node(
                [
                    ("Home", f"{BASE}/"),
                    ("Work examples", f"{BASE}/#work"),
                    ("Multi-agent AI production system", url),
                ]
            ),
            creative,
        ]
    )


def patch_home() -> None:
    path = ROOT / "index.html"
    html = path.read_text(encoding="utf-8")
    title = "Yonatan Gemmi | AI, automation &amp; operations | North Miami Beach"
    description = (
        "Free 30-min consult for AI, automation, dashboards, and ecommerce ops. "
        "Hermes desks, Stocky dump recovery, and unused ChatGPT seats. Remote or North Miami Beach."
    )
    html = patch_head(
        html,
        title=title,
        description=description,
        canonical=f"{BASE}/",
        stylesheet="styles.css?v=seo-1",
        icon="assets/yonatan-gemmi-pixel-portrait-256.png",
    )
    html = replace_jsonld(html, home_graph())
    html = html.replace(
        '<article id="hermes-agents"><h3>AI that does more than chat</h3><p>Hermes is an AI agent on your computer, not another chat tab. I install it, set limits, and help you run a first real task.</p><a class="service-card-link" href="services/hermes-agents.html">Explore Hermes setup →</a></article>',
        '<article id="hermes-agents"><h3>AI that does more than chat</h3><p>Hermes is an AI agent on your computer, not another chat tab. I install a Desk using ChatGPT or Claude seats you already pay for, set limits, and help you run a first real task.</p><a class="service-card-link" href="services/hermes-agents.html">Explore Hermes setup →</a></article>',
    )
    old_faq = """          <details class="faq-item"><summary>Am I committing to a project by booking?</summary><p>No. The consultation gives you direction. If you want to continue, we agree on a paid next step. You can also take the advice and decide later.</p></details>
        </div>"""
    new_faq = """          <details class="faq-item"><summary>Am I committing to a project by booking?</summary><p>No. The consultation gives you direction. If you want to continue, we agree on a paid next step. You can also take the advice and decide later.</p></details>
          <details class="faq-item"><summary>Can you help if Stocky shut down?</summary><p>Yes. If you ran Shopify inventory in Stocky and now have a CSV dump, that is a specific ecommerce job: a weekly system from the export, not another inventory app. See <a href="services/stocky-recovery.html">Stocky dump recovery</a>.</p></details>
        </div>"""
    if old_faq not in html:
        raise SystemExit("home FAQ marker missing")
    html = html.replace(old_faq, new_faq, 1)
    html = html.replace(
        '      <p>© <span id="year"></span> Yonatan Gemmi. Based in North Miami Beach, Florida · <a href="https://github.com/nykon1293" target="_blank" rel="noreferrer">GitHub</a></p>',
        '      <p>© <span id="year"></span> Yonatan Gemmi. Based in North Miami Beach, Florida · Miami-Dade, Broward, and remote</p>\n      <p class="footer-nav">\n        <a href="pricing.html">Pricing</a>\n        <a href="services/stocky-recovery.html">Stocky recovery</a>\n        <a href="services/hermes-agents.html">Hermes desks</a>\n        <a href="https://calendly.com/josh-gemmi/30min" target="_blank" rel="noreferrer">Book consultation</a>\n        <a href="https://github.com/nykon1293" target="_blank" rel="noreferrer">GitHub</a>\n      </p>',
    )
    path.write_text(html, encoding="utf-8")
    print("patched", path.relative_to(ROOT))


def patch_pricing() -> None:
    path = ROOT / "pricing.html"
    html = path.read_text(encoding="utf-8")
    title = "Pricing | Yonatan Gemmi | South FL"
    description = (
        "Fixed prices for Hermes Desk setups, Paid Discovery, Care, and tutoring. "
        "Stocky dump recovery uses Starter or Operator Desk. Free 30-minute consultation."
    )
    html = patch_head(
        html,
        title=title,
        description=description,
        canonical=f"{BASE}/pricing.html",
        stylesheet="styles.css?v=seo-1",
        icon="assets/yonatan-gemmi-pixel-portrait-256.png",
    )
    html = replace_jsonld(html, pricing_graph())
    old_faq = """          <details class="faq-item"><summary>How do we start?</summary><p>Pick a time at <a href="https://calendly.com/josh-gemmi/30min" target="_blank" rel="noreferrer">Calendly</a>. The free 30-minute consultation is the first step. No note to send first.</p></details>
        </div>"""
    new_faq = """          <details class="faq-item"><summary>How do we start?</summary><p>Pick a time at <a href="https://calendly.com/josh-gemmi/30min" target="_blank" rel="noreferrer">Calendly</a>. The free 30-minute consultation is the first step. No note to send first.</p></details>
          <details class="faq-item"><summary>Does Stocky dump recovery have its own price?</summary><p>No. Starter Desk at $500 and Operator Desk at $1,500 are the usual sizes for turning a Stocky CSV dump into a weekly system. A larger rebuild is Paid Discovery. The <a href="services/stocky-recovery.html">recovery page</a> explains the job. It is not another inventory app.</p></details>
        </div>"""
    if old_faq not in html:
        raise SystemExit("pricing FAQ marker missing")
    html = html.replace(old_faq, new_faq, 1)
    html = html.replace(
        '      <p>© <span id="year"></span> Yonatan Gemmi. Built with GitHub Pages • Based in North Miami Beach, Florida • <a class="text-link" href="https://www.linkedin.com/in/joshuah-gemmi-16046233/" target="_blank" rel="noreferrer">LinkedIn</a></p>',
        '      <p>© <span id="year"></span> Yonatan Gemmi. Based in North Miami Beach, Florida · Miami-Dade, Broward, and remote</p>\n      <p class="footer-nav">\n        <a href="index.html">Home</a>\n        <a href="pricing.html">Pricing</a>\n        <a href="services/stocky-recovery.html">Stocky recovery</a>\n        <a href="services/hermes-agents.html">Hermes desks</a>\n        <a href="https://calendly.com/josh-gemmi/30min" target="_blank" rel="noreferrer">Book consultation</a>\n        <a href="https://www.linkedin.com/in/joshuah-gemmi-16046233/" target="_blank" rel="noreferrer">LinkedIn</a>\n      </p>',
    )
    path.write_text(html, encoding="utf-8")
    print("patched", path.relative_to(ROOT))


def patch_advisory() -> None:
    path = ROOT / "advisory.html"
    html = path.read_text(encoding="utf-8")
    title = "Advisory &amp; Fractional CTO | Yonatan Gemmi"
    description = "Advisory Light and Fractional CTO with Yonatan Gemmi. Extremely limited availability. Inquire first."
    html = patch_head(
        html,
        title=title,
        description=description,
        canonical=f"{BASE}/advisory.html",
        stylesheet="styles.css?v=seo-1",
        icon="assets/yonatan-gemmi-pixel-portrait-256.png",
    )
    html = replace_jsonld(html, advisory_graph())
    html = html.replace(
        '      <p>© <span id="year"></span> Yonatan Gemmi. Built with GitHub Pages • Based in North Miami Beach, Florida • <a class="text-link" href="https://www.linkedin.com/in/joshuah-gemmi-16046233/" target="_blank" rel="noreferrer">LinkedIn</a></p>',
        '      <p>© <span id="year"></span> Yonatan Gemmi. Based in North Miami Beach, Florida · Miami-Dade, Broward, and remote</p>\n      <p class="footer-nav">\n        <a href="index.html">Home</a>\n        <a href="pricing.html">Pricing</a>\n        <a href="services/stocky-recovery.html">Stocky recovery</a>\n        <a href="services/hermes-agents.html">Hermes desks</a>\n        <a href="https://calendly.com/josh-gemmi/30min" target="_blank" rel="noreferrer">Book consultation</a>\n        <a href="https://www.linkedin.com/in/joshuah-gemmi-16046233/" target="_blank" rel="noreferrer">LinkedIn</a>\n      </p>',
    )
    path.write_text(html, encoding="utf-8")
    print("patched", path.relative_to(ROOT))


def patch_stocky() -> None:
    path = ROOT / "services/stocky-recovery.html"
    html = path.read_text(encoding="utf-8")
    title = "Stocky Shut Down? Shopify CSV Dump Recovery | Yonatan Gemmi"
    description = (
        "Stocky shut down Aug 31, 2026. I turn a Shopify CSV export into a weekly inventory system using Sheets "
        "and ChatGPT or Claude seats you already pay for — not a Stocky replacement app. Free 30-minute consultation."
    )
    html = patch_head(
        html,
        title=title,
        description=description,
        canonical=f"{BASE}/services/stocky-recovery.html",
        stylesheet="../styles.css?v=seo-1",
        icon="../assets/yonatan-gemmi-pixel-portrait-256.png",
    )
    html = replace_jsonld(html, stocky_graph())
    html = html.replace(
        "<h1>Stocky is gone. A CSV dump is not an operating system.</h1>",
        "<h1>Stocky shut down. I’ll turn your Shopify CSV dump into a weekly system.</h1>",
    )
    html = html.replace(
        '<p class="lead">I’m Yonatan Gemmi. If you ran Shopify inventory in Stocky and now have files in Sheets, I make that dump usable for the week. This is not another Prediko or Klerio. It is a working weekly system on seats you already pay for.</p>',
        '<p class="lead">I’m Yonatan Gemmi. If you ran Shopify inventory in Stocky and now have a CSV export in Sheets, I make that dump usable for the week. This is not a Stocky alternative app — not Prediko, not Klerio. It is a working weekly system on ChatGPT or Claude seats you already pay for.</p>',
    )
    old_faq = """          <details class="faq-item"><summary>Is this a Stocky replacement app?</summary><p>No. I am not selling Prediko, Klerio, or another inventory product. If you want a full inventory app, buy one. This job is making the dump operable: a weekly view you can run with Sheets and the ChatGPT or Claude seat you already pay for.</p></details>
          <details class="faq-item"><summary>Did supplier notes and par levels export from Stocky?</summary>"""
    new_faq = """          <details class="faq-item"><summary>Is this a Stocky replacement app?</summary><p>No. I am not selling Prediko, Klerio, or another inventory product. If you want a full inventory app, buy one. This job is making the dump operable: a weekly view you can run with Sheets and the ChatGPT or Claude seat you already pay for.</p></details>
          <details class="faq-item"><summary>Is this a Stocky alternative?</summary><p>No. A Stocky alternative is another inventory app. This is recovery of the CSV export you already have after Stocky shut down — a weekly Shopify inventory view, not a new SKU system to migrate into.</p></details>
          <details class="faq-item"><summary>Did supplier notes and par levels export from Stocky?</summary>"""
    if old_faq not in html:
        raise SystemExit("stocky FAQ marker missing")
    html = html.replace(old_faq, new_faq, 1)
    html = html.replace(
        """          <details class="faq-item"><summary>Did supplier notes and par levels export from Stocky?</summary><p>Often they did not. SKUs, vendors, and purchase orders usually survive in the CSV. Supplier notes and par levels often stayed in Stocky or in someone’s head. We recover what still exists and give the missing pieces a place to live.</p></details>
          <details class="faq-item"><summary>Starter Desk, Operator Desk, or Paid Discovery?</summary>""",
        """          <details class="faq-item"><summary>Did supplier notes and par levels export from Stocky?</summary><p>Often they did not. SKUs, vendors, and purchase orders usually survive in the CSV. Supplier notes and par levels often stayed in Stocky or in someone’s head. We recover what still exists and give the missing pieces a place to live.</p></details>
          <details class="faq-item"><summary>I have a Stocky CSV export. Can you recover Shopify inventory from that?</summary><p>Yes. SKUs, vendors, and purchase orders usually survive in the dump. I build a weekly reorder view from those files. This is not a Stocky replacement app.</p></details>
          <details class="faq-item"><summary>Starter Desk, Operator Desk, or Paid Discovery?</summary>""",
        1,
    )
    html = html.replace(
        '      <p>© <span id="year"></span> Yonatan Gemmi. Built with GitHub Pages • Based in North Miami Beach, Florida</p>',
        '      <p>© <span id="year"></span> Yonatan Gemmi. Based in North Miami Beach, Florida · Miami-Dade, Broward, and remote</p>\n      <p class="footer-nav">\n        <a href="../index.html">Home</a>\n        <a href="../pricing.html">Pricing</a>\n        <a href="stocky-recovery.html">Stocky recovery</a>\n        <a href="hermes-agents.html">Hermes desks</a>\n        <a href="https://calendly.com/josh-gemmi/30min" target="_blank" rel="noreferrer">Book consultation</a>\n      </p>',
    )
    path.write_text(html, encoding="utf-8")
    print("patched", path.relative_to(ROOT))


def patch_work() -> None:
    path = ROOT / "work/governed-ai-content-engine.html"
    html = path.read_text(encoding="utf-8")
    title = "Multi-Agent AI Production Case Study | Yonatan Gemmi"
    description = (
        "An anonymized multi-agent AI case study by Yonatan Gemmi: operator-led briefs, "
        "coordinated video execution, recovery, and configurable control."
    )
    html = patch_head(
        html,
        title=title,
        description=description,
        canonical=f"{BASE}/work/governed-ai-content-engine.html",
        og_type="article",
        stylesheet="../styles.css?v=seo-1",
        icon="../assets/yonatan-gemmi-pixel-portrait-256.png",
    )
    html = replace_jsonld(html, work_graph())
    html = html.replace(
        '      <p>© <span id="year"></span> Yonatan Gemmi. Built with GitHub Pages • Based in North Miami Beach, Florida • <a class="text-link" href="https://www.linkedin.com/in/joshuah-gemmi-16046233/" target="_blank" rel="noreferrer">LinkedIn</a></p>',
        '      <p>© <span id="year"></span> Yonatan Gemmi. Based in North Miami Beach, Florida · Miami-Dade, Broward, and remote</p>\n      <p class="footer-nav">\n        <a href="../index.html">Home</a>\n        <a href="../pricing.html">Pricing</a>\n        <a href="../services/stocky-recovery.html">Stocky recovery</a>\n        <a href="../services/hermes-agents.html">Hermes desks</a>\n        <a href="https://calendly.com/josh-gemmi/30min" target="_blank" rel="noreferrer">Book consultation</a>\n        <a href="https://www.linkedin.com/in/joshuah-gemmi-16046233/" target="_blank" rel="noreferrer">LinkedIn</a>\n      </p>',
    )
    path.write_text(html, encoding="utf-8")
    print("patched", path.relative_to(ROOT))


def main() -> None:
    patch_home()
    patch_pricing()
    patch_advisory()
    patch_stocky()
    patch_work()


if __name__ == "__main__":
    main()
