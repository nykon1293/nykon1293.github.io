#!/usr/bin/env python3
"""Generate static service landing pages (run from repo root)."""
from __future__ import annotations

import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SERVICES_DIR = ROOT / "services"
BASE = "https://nykon1293.github.io"

SERVICE_PAGES = [
    ("ai-automation.html", "AI automation", "ai-automation"),
    ("dashboards-reporting.html", "Dashboards & reporting", "dashboards-reporting"),
    ("ecommerce-operations.html", "Ecommerce operations", "ecommerce-operations"),
    ("tutoring-project-help.html", "Tutoring & project help", "tutoring-project-help"),
]


def nav_for(slug: str) -> str:
    lines = ['<nav id="site-nav" class="nav-links" aria-label="Primary navigation">']
    lines.append('        <a href="../index.html">Home</a>')
    lines.append('        <details class="nav-dropdown">')
    lines.append('          <summary class="nav-dropdown-trigger">Services</summary>')
    lines.append('          <div class="nav-dropdown-menu">')
    for href, label, key in SERVICE_PAGES:
        cur = ' aria-current="page"' if key == slug else ""
        lines.append(f'            <a href="{href}"{cur}>{escape(label)}</a>')
    lines.append('            <a class="nav-dropdown-muted" href="../index.html#service-hub">All services on homepage</a>')
    lines.append("          </div>")
    lines.append("        </details>")
    lines.append('        <a href="../index.html#work">Work Examples</a>')
    lines.append('        <a href="../index.html#faq">FAQ</a>')
    lines.append('        <a href="../index.html#contact">Contact</a>')
    lines.append("      </nav>")
    return "\n".join(lines)


def faq_schema(
    faqs: list[tuple[str, str]],
    *,
    service_name: str,
    meta_description: str,
    canonical: str,
) -> str:
    entities = []
    for q, a in faqs:
        entities.append(
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            }
        )
    graph = [
        {
            "@type": "Service",
            "name": service_name,
            "description": meta_description,
            "url": canonical,
            "provider": {
                "@type": "Person",
                "name": "Yonatan Gemmi",
                "url": f"{BASE}/",
            },
            "areaServed": ["South Florida", "Remote"],
        },
        {"@type": "FAQPage", "mainEntity": entities},
    ]
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, indent=2)


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
          <p class="section-kicker">Working together</p>
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
            f'            <div><strong>{title}</strong><span>{body}</span></div>'
        )
    caption_html = (
        f'              <span class="portrait-caption">{caption}</span>\n'
        if caption
        else ""
    )
    return f"""
        <aside class="hero-card service-pfd-card" aria-label="Typical client pains">
          <div class="profile-strip">
            <div>
              <p class="snapshot-label">{label}</p>
{caption_html}            </div>
          </div>
          <div class="snapshot-list">
{chr(10).join(rows)}
          </div>
        </aside>
"""


PAGES = [
    {
        "slug": "ai-automation",
        "filename": "ai-automation.html",
        "title": "AI Workflow Automation | Yonatan Gemmi | South FL",
        "meta_description": "Useful AI tools, workflow automation, Custom GPTs, and hands-on support for teams and founders. Remote or South Florida.",
        "service_name": "AI tools and workflow automation",
        "eyebrow": "AI workflows",
        "h1": "Turn AI tests into tools your team uses each week",
        "lead": "I help teams move from random AI tests to useful tools. These tools can help with research, reports, drafts, checks, and intake. People can review the work where needed.",
        "pfd_label": "When teams call for AI automation",
        "pfd_caption": "For teams that need a working tool, not another demo.",
        "pfd_pains": [
            (
                "AI tests never reach daily work",
                "Map the real steps, choose simple tools, and build something the team can run.",
            ),
            (
                "Manual copy-paste between tools",
                "Connect files, CRMs, inboxes, and apps so the work moves in one clear flow.",
            ),
            (
                "No checks on AI output",
                "Add reviews, clear steps, and training so people can trust the results.",
            ),
        ],
        "sections": [
            (
                "What this looks like",
                "I start with the work, not the AI model. We find where time is lost and which choices need a person. Then I build the smallest useful system and show the team how to run it.",
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
        "faq_topic": "AI tools and workflow automation",
        "buyer_details": [
            ("Good fit when", ["A repeated workflow is still manual", "AI experiments need guardrails and ownership", "Your team needs one reviewed process—not another tool demo"]),
            ("What you receive", ["Workflow map and scoped implementation plan", "Working automation, assistant, or integration", "Testing notes, SOPs, and team handoff"]),
            ("What I need from you", ["A workflow owner who knows the real process", "Representative examples or safe test data", "Access to approved tools, exports, or APIs"]),
            ("Engagement options", ["Audit and roadmap", "Short implementation project", "Ongoing improvement and support"]),
        ],
        "layout": "split",
        "faqs": [
            (
                "Do you only build Custom GPTs?",
                "No. They are only one option. A simple script, automation, or dashboard may fit the job better.",
            ),
            (
                "Can you work with our existing tools?",
                "Usually. I can connect files, CRMs, online stores, email, chat tools, and cloud data when access is available.",
            ),
            (
                "Is this remote or on-site?",
                "Most work is remote. I am based in North Miami Beach and can meet in South Florida when it helps for workshops or discovery.",
            ),
            (
                "How do we start?",
                "Send a short note about the problem and tools. Use the homepage form or email. We can then agree on the scope.",
            ),
        ],
    },
    {
        "slug": "dashboards-reporting",
        "filename": "dashboards-reporting.html",
        "title": "Dashboards & Reporting | Yonatan Gemmi | South FL",
        "meta_description": "Clear dashboards, reports, and spreadsheet cleanup for ecommerce and operations teams. Remote consulting and contract work.",
        "service_name": "Dashboards, reporting, and data cleanup",
        "eyebrow": "Data visibility",
        "h1": "Clear reports your team can trust each day",
        "lead": "Work slows down when each team has different numbers. I clean the data, set clear rules, and build reports people can trust. The goal is a useful daily view, not another report to rebuild by hand.",
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
        "faqs": [
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
                "Tell me which reports you trust, which you do not, and who uses them. Use the homepage form or email to start.",
            ),
        ],
    },
    {
        "slug": "ecommerce-operations",
        "filename": "ecommerce-operations.html",
        "title": "Ecommerce Operations | Yonatan Gemmi | South FL",
        "meta_description": "Ecommerce operations systems: Amazon, eBay, inventory, fulfillment, listings, and marketplace reporting. Consulting and contract support.",
        "service_name": "Ecommerce operations systems",
        "eyebrow": "Ecommerce ops",
        "h1": "Fix the ecommerce problems that keep coming back",
        "lead": "I help online sellers fix problems with listings, inventory, shipping, and reports. I build clear work steps, simple automation, and useful daily views. My approach comes from real warehouse and marketplace work.",
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
                "Amazon and eBay work steps • Tracked and multi-SKU inventory • Better listings and product data • Shipping and warehouse guides • Marketplace reports and dashboards • AI help for research, drafts, and checks",
            ),
            (
                "Proof you can expect",
                "I have worked in multi-brand ecommerce, FBA, and eBay operations. I have built systems that turn scattered work into clear daily steps.",
            ),
        ],
        "faq_topic": "ecommerce operations systems",
        "buyer_details": [
            ("Good fit when", ["Inventory, listings, or fulfillment repeatedly fall out of sync", "Peak periods expose undocumented handoffs", "Marketplace reporting arrives too late to act"]),
            ("What you receive", ["Current-state process and failure-point map", "Improved workflow, SOPs, and lightweight tooling", "Owner checks, escalation rules, and handoff documentation"]),
            ("What I need from you", ["Examples of the highest-cost weekly problems", "Safe exports or approved access to relevant tools", "An operations owner available for testing"]),
            ("Engagement options", ["Ops audit and roadmap", "Focused workflow implementation", "Ongoing operator-builder support"]),
        ],
        "layout": "steps",
        "faqs": [
            (
                "Do you only work with large brands?",
                "No. I also help founders and small teams that sell on more than one channel.",
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
                "How do we start?",
                "Tell me where you sell, how many items you manage, and the top two weekly problems. Use the homepage form or email.",
            ),
        ],
    },
    {
        "slug": "tutoring-project-help",
        "filename": "tutoring-project-help.html",
        "title": "Technical Tutoring & Project Help | Yonatan Gemmi",
        "meta_description": "One-on-one help with AI tools, workflows, and technical projects for founders, students, and teams. Remote sessions.",
        "service_name": "Technical tutoring, coaching, and project help",
        "eyebrow": "Hands-on help",
        "h1": "Get hands-on help and move your project forward",
        "lead": "Not every problem needs a large project. I help founders, students, and teams learn AI tools, fix workflows, and finish builds. We agree on a clear goal before the session starts.",
        "pfd_label": "When you need hands-on help",
        "pfd_caption": "For people who want help now and clear steps they can use later.",
        "pfd_pains": [
            (
                "Stuck on a build with no one to pair with",
                "Review the system, fix the problem, and write down steps you can repeat.",
            ),
            (
                "AI tools feel useful but risky",
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
                "Learning ChatGPT, Custom GPTs, or AI agents • Spreadsheet and dashboard help • Ecommerce work steps • Fixing automations • Technical interview practice • Helping founders decide what to build or buy",
            ),
            (
                "Who it is for",
                "This is for students, solo founders, operators, and teams that want hands-on help. I do not give legal, medical, or financial advice.",
            ),
        ],
        "faq_topic": "technical tutoring, coaching, and project help",
        "buyer_details": [
            ("Good fit when", ["You are blocked on a specific build or workflow", "A team needs practical AI-tool training", "You want to validate an approach before a larger project"]),
            ("What you receive", ["Focused working session or short project burst", "A resolved blocker, documented approach, or working draft", "Repeatable next steps you can own"]),
            ("What I need from you", ["The goal and current blocker", "Relevant files, screenshots, or a safe example", "Your timezone, availability, and desired pace"]),
            ("Engagement options", ["One-on-one working session", "Short project help", "Team workshop and follow-up"]),
        ],
        "layout": "simple",
        "faqs": [
            (
                "Is this the same as full consulting?",
                "Tutoring is for a small, clear goal. Larger builds become consulting or contract work with a written plan.",
            ),
            (
                "Remote only?",
                "Most sessions are remote by video. Longer South Florida workshops may be held in person.",
            ),
            (
                "Can you help my team adopt a new AI tool?",
                "Yes. I can teach the tool, set safety checks, share prompt patterns, and write simple steps for the team.",
            ),
            (
                "How do we start?",
                "Tell me what you want to learn or finish. Use the homepage form or email, and include your time zone and schedule.",
            ),
        ],
    },
]


FOOTER_SCRIPTS = """
    <footer>
      <p>© <span id="year"></span> Yonatan Gemmi. Built with GitHub Pages • Based in North Miami Beach, Florida</p>
    </footer>
  </div>
  <script>document.getElementById('year').textContent = new Date().getFullYear();</script>
  <script>
    (() => {
      const nav = document.querySelector('.nav');
      const toggle = document.querySelector('.nav-toggle');
      const links = document.getElementById('site-nav');
      if (!nav || !toggle || !links) return;
      const setOpen = (open) => {
        nav.classList.toggle('is-menu-open', open);
        toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
        toggle.setAttribute('aria-label', open ? 'Close site menu' : 'Open site menu');
      };
      toggle.addEventListener('click', () => setOpen(!nav.classList.contains('is-menu-open')));
      links.querySelectorAll('a').forEach((link) => {
        link.addEventListener('click', () => {
          setOpen(false);
          links.querySelectorAll('details.nav-dropdown[open]').forEach((d) => d.removeAttribute('open'));
        });
      });
      document.addEventListener('keydown', (e) => { if (e.key === 'Escape') setOpen(false); });
      document.addEventListener('click', (e) => {
        if (!nav.classList.contains('is-menu-open')) return;
        if (nav.contains(e.target)) return;
        setOpen(false);
      });
    })();
  </script>
  <script src="../assets/portfolio-chatbot.js" data-chatbot-url="https://personal-github-pages-chatbot-lime.vercel.app" defer></script>
</body>
</html>
"""


def sections_cards_html(page: dict) -> str:
    parts: list[str] = []
    for title, body in page["sections"]:
        parts.append(
            f"""        <article class="card service-detail-card">
          <h3>{title}</h3>
          <p>{body}</p>
        </article>"""
        )
    return "\n".join(parts)


def scope_block(page: dict) -> str:
    layout = page.get("layout", "split")
    intro = (
        f"This page is the dedicated entry point for <strong>{page['faq_topic']}</strong>. "
        "The homepage lists my other consulting, contract, and technical services."
    )
    cards = sections_cards_html(page)

    if layout == "proof":
        proof = page.get("proof_strip", "From scattered exports to one trusted morning view.")
        return f"""
      <section class="section service-layout-proof">
        <div class="proof-strip" role="presentation">
          <p class="proof-strip-label">{proof}</p>
        </div>
        <div class="section-heading stacked">
          <p class="section-kicker">Scope</p>
          <h2>Focused help for one kind of problem.</h2>
          <p class="section-intro">{intro}</p>
        </div>
        <div class="cards capability-list service-detail-stack">
{cards}
        </div>
      </section>"""

    if layout == "steps":
        return f"""
      <section class="section split service-layout-steps">
        <div>
          <p class="section-kicker">Scope</p>
          <h2>How we improve the work, one step at a time.</h2>
          <p class="section-intro">{intro}</p>
        </div>
        <div class="cards capability-list">
{cards}
        </div>
      </section>"""

    if layout == "simple":
        return f"""
      <section class="section service-layout-simple">
        <div class="section-heading stacked">
          <p class="section-kicker">What sessions cover</p>
          <h2>Practical help without a large project.</h2>
          <p class="section-intro">{intro}</p>
        </div>
        <div class="cards service-detail-stack">
{cards}
        </div>
      </section>"""

    return f"""
      <section class="section split">
        <div>
          <p class="section-kicker">Scope</p>
          <h2>Focused help for one kind of problem.</h2>
          <p class="section-intro">{intro}</p>
        </div>
        <div class="cards capability-list">
{cards}
        </div>
      </section>"""


def render(page: dict) -> str:
    slug = page["slug"]
    canonical = f"{BASE}/services/{page['filename']}"
    faqs = page["faqs"]
    title = escape(page["title"])
    meta_description = escape(page["meta_description"], quote=True)
    service_name = escape(page["service_name"])
    faq_topic = escape(page["faq_topic"])
    schema = faq_schema(
        faqs,
        service_name=page["service_name"],
        meta_description=page["meta_description"],
        canonical=canonical,
    )
    scope_html = scope_block(page)
    buyer_html = buyer_details_html(page)
    related_case_study = ""
    if slug == "ai-automation":
        related_case_study = """
      <section class="section related-case-study" aria-labelledby="related-ai-case-study-title">
        <div>
          <p class="section-kicker">Related system case study</p>
          <h2 id="related-ai-case-study-title">See how I built an AI content system with safety checks.</h2>
          <p class="section-intro">This private-client example shows review steps, automatic checks, safe stops, and an optional hands-free mode.</p>
        </div>
        <a class="button ghost" href="../work/governed-ai-content-engine.html">View the case study</a>
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
  <meta property="og:title" content="{title}" />
  <meta property="og:description" content="{meta_description}" />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="{canonical}" />
  <meta property="og:site_name" content="Yonatan Gemmi" />
  <meta property="og:image" content="{BASE}/assets/social-preview.png" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{title}" />
  <meta name="twitter:description" content="{meta_description}" />
  <meta name="twitter:image" content="{BASE}/assets/social-preview.png" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&amp;family=JetBrains+Mono:wght@500;700&amp;display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="../styles.css" />
  <link rel="stylesheet" href="../assets/portfolio-chatbot.css" />
  <link rel="icon" href="../assets/yonatan-gemmi-pixel-portrait-256.png" type="image/png" />
  <script type="application/ld+json">
{schema}
  </script>
</head>
<body>
  <div class="site-shell">
    <header class="nav">
      <a class="brand" href="../index.html" aria-label="YG Yonatan Gemmi home">
        <span class="brand-mark">YG</span>
        <span>Yonatan Gemmi</span>
      </a>
      <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav" aria-label="Open site menu">
        <span class="nav-toggle__bars" aria-hidden="true"></span>
        <span class="nav-toggle__label">Menu</span>
      </button>
{nav_for(slug)}
    </header>

    <main id="top">
      <section class="service-landing-hero section">
        <p class="section-kicker">{page['eyebrow']}</p>
        <nav class="breadcrumb" aria-label="Breadcrumb">
          <a href="../index.html">Home</a>
          <span aria-hidden="true">/</span>
          <span>{service_name}</span>
        </nav>
        <h1>{page['h1']}</h1>
        <p class="lead">{page['lead']}</p>
        <div class="actions">
          <a class="button primary" href="../index.html#contact">Discuss this service</a>
          <a class="button ghost" href="../index.html#work">See work examples</a>
        </div>
{pfd_card_html(page)}
      </section>
{scope_html}{related_case_study}
{buyer_html}

      <section id="faq" class="section">
        <div class="section-heading stacked">
          <p class="section-kicker">FAQ</p>
          <h2>Questions about {faq_topic}.</h2>
        </div>
        <div class="faq-grid faq-accordion">
{faq_html(faqs)}
        </div>
      </section>

      <section class="section closing-card service-landing-cta">
        <div>
          <p class="section-kicker">Next step</p>
          <h2>Tell me what you are trying to fix or build.</h2>
          <p class="section-intro">Use the homepage form or email me. I will reply with clear next steps.</p>
        </div>
        <div class="contact-panel">
          <a class="button primary full" href="../index.html#contact">Go to contact form</a>
          <a class="button full contact-secondary" href="mailto:josh.gemmi@gmail.com">Email Yonatan</a>
          <a class="button full contact-secondary" href="https://www.linkedin.com/in/joshuah-gemmi-16046233/" target="_blank" rel="noreferrer">LinkedIn</a>
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