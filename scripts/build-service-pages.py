#!/usr/bin/env python3
"""Generate static service landing pages (run from repo root)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SERVICES_DIR = ROOT / "services"
BASE = "https://nykon1293.github.io"

NAV = """
      <nav id="site-nav" class="nav-links" aria-label="Primary navigation">
        <a href="../index.html">Home</a>
        <a href="ai-automation.html" aria-current="page">AI automation</a>
        <a href="dashboards-reporting.html">Dashboards</a>
        <a href="ecommerce-operations.html">Ecommerce</a>
        <a href="tutoring-project-help.html">Tutoring</a>
        <a href="../index.html#contact">Contact</a>
      </nav>
""".strip()

def nav_for(slug: str) -> str:
    items = [
        ("../index.html", "Home", None),
        ("ai-automation.html", "AI automation", "ai-automation"),
        ("dashboards-reporting.html", "Dashboards", "dashboards-reporting"),
        ("ecommerce-operations.html", "Ecommerce", "ecommerce-operations"),
        ("tutoring-project-help.html", "Tutoring", "tutoring-project-help"),
        ("../index.html#contact", "Contact", None),
    ]
    lines = ['<nav id="site-nav" class="nav-links" aria-label="Primary navigation">']
    for href, label, key in items:
        cur = ' aria-current="page"' if key == slug else ""
        lines.append(f'        <a href="{href}"{cur}>{label}</a>')
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
            f'          <article class="faq-item"><h3>{q}</h3><p>{a}</p></article>'
        )
    return "\n".join(parts)


PAGES = [
    {
        "slug": "ai-automation",
        "filename": "ai-automation.html",
        "title": "AI Workflow Automation | Yonatan Gemmi | South FL",
        "meta_description": "Practical AI implementation, workflow automation, Custom GPTs, and agent-assisted ops for teams and founders. Remote or South Florida.",
        "service_name": "AI implementation and workflow automation",
        "eyebrow": "AI workflows",
        "h1": "AI implementation and workflow automation that fits real operations",
        "lead": "I help businesses and operators turn AI from scattered experiments into reviewed workflows—research, reporting, drafting, QA, intake, and internal execution—with human checkpoints where they matter.",
        "sections": [
            (
                "What this looks like",
                "I start with the process, not the model. We map where time is lost, what decisions need a human, and which steps can be assisted, routed, or automated. Deliverables might include prompt systems, Custom GPTs, lightweight agents, API glue, SOPs, and training so the team can run it without heroics.",
            ),
            (
                "Common project types",
                "Internal research and summarization pipelines • Reporting and briefing assistants • Ecommerce and ops intake routing • Documentation and QA helpers • Custom GPT / assistant design with review loops • Connecting spreadsheets, CRMs, and tools into one repeatable flow",
            ),
            (
                "Proof you can expect",
                "9+ years in operations and systems, multi-brand ecommerce background, and hands-on builds—not slideware. I stay close enough to test with real data and real users before calling it done.",
            ),
        ],
        "faqs": [
            (
                "Do you only build Custom GPTs?",
                "No. Custom GPTs and AI assistants are one option. I choose the lightest stack that fits—sometimes that is scripts, automations, or dashboards with AI steps, not a standalone bot.",
            ),
            (
                "Can you work with our existing tools?",
                "Usually yes. I integrate with spreadsheets, CRMs, marketplaces, email, Slack-style workflows, and cloud data tools when APIs or exports are available.",
            ),
            (
                "Is this remote or on-site?",
                "Most work is remote. I am based in North Miami Beach and can meet in South Florida when it helps for workshops or discovery.",
            ),
            (
                "How do we start?",
                "Send a short note about the workflow, pain point, and tools involved via the contact form on the homepage or email. We scope from there—no invented fixed rates in chat.",
            ),
        ],
    },
    {
        "slug": "dashboards-reporting",
        "filename": "dashboards-reporting.html",
        "title": "Dashboards & Reporting | Yonatan Gemmi | South FL",
        "meta_description": "Dashboards, reporting, spreadsheet cleanup, and operational visibility for ecommerce and ops teams. Remote consulting and contract work.",
        "service_name": "Dashboards, reporting, and data cleanup",
        "eyebrow": "Data visibility",
        "h1": "Dashboards, reporting, and data cleanup people actually use",
        "lead": "Messy spreadsheets and disconnected exports slow every decision. I help teams find a source of truth, standardize key fields, and build reporting and dashboards that match how work really runs.",
        "sections": [
            (
                "What this looks like",
                "Audit which files and systems drive decisions, remove duplicate manual entry, define the metrics that matter, and build a path from raw data to a daily view—whether that is Looker-style BI, sheets with guardrails, or a lightweight data platform.",
            ),
            (
                "Common project types",
                "Spreadsheet consolidation and cleanup • Ecommerce and inventory reporting • CRM and sales activity views • Fulfillment and ops KPIs • ETL-style movement into a warehouse (e.g. BigQuery) • Training teams on maintaining the pipeline",
            ),
            (
                "Proof you can expect",
                "Built operational cockpits for multi-brand ecommerce—orders, inventory, ads, fulfillment, and team activity in one place. Comfortable with serialized inventory scale (95k+ items tracked) and real ops constraints.",
            ),
        ],
        "faqs": [
            (
                "Can you fix our spreadsheets without a full BI project?",
                "Often yes. Many engagements start with structure, validation, and clearer ownership in sheets before any heavier platform work.",
            ),
            (
                "Do you build the dashboards or only advise?",
                "Both. I implement when that is the fastest path to value—queries, models, charts, and documentation—not strategy decks alone.",
            ),
            (
                "What tools do you use?",
                "Depends on your stack: Google Sheets, BigQuery, Looker-style tools, Python for cleanup, and marketplace or CRM exports. I match what you already pay for when possible.",
            ),
            (
                "How do we start?",
                "Share which reports you trust today, which you do not, and who makes decisions from them. Use the homepage contact form or email to begin.",
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
        "h1": "Ecommerce operations systems for marketplaces and multi-channel sellers",
        "lead": "I help ecommerce operators reduce guesswork across listings, inventory, fulfillment, product data, and marketplace reporting—with SOPs, automations, and visibility tools grounded in real warehouse and ops experience.",
        "sections": [
            (
                "What this looks like",
                "Map how product, order, and inventory data moves today, fix the breakpoints (item specifics, QC, handoffs, reporting), and put lightweight systems in place so the team is not living in emergency spreadsheets.",
            ),
            (
                "Common project types",
                "Amazon and eBay workflow improvement • Serialized and multi-SKU inventory tracking • Listing and product data quality • Fulfillment and warehouse SOPs • Marketplace reporting and ops dashboards • AI-assisted research, drafting, or QA for listings and ops tasks",
            ),
            (
                "Proof you can expect",
                "Multi-brand ecommerce ops background, FBA and eBay experience, and builds that connected scattered activity into clearer daily workflows—not generic agency playbooks.",
            ),
        ],
        "faqs": [
            (
                "Do you only work with large brands?",
                "No. Founders, small teams, and operators with messy multi-channel setups are a good fit when you want practical systems, not a reorg deck.",
            ),
            (
                "Can you help with Amazon and eBay at the same time?",
                "Yes. Much of my experience is multi-channel—shared inventory truth, channel-specific listing rules, and reporting that rolls up cleanly.",
            ),
            (
                "Do you replace an agency or VA team?",
                "I complement execution teams: SOPs, tooling, data quality, and systems so VAs and staff have a clearer playbook.",
            ),
            (
                "How do we start?",
                "Describe channels, SKU scale, and the top two weekly fires. Contact via the homepage form or email.",
            ),
        ],
    },
    {
        "slug": "tutoring-project-help",
        "filename": "tutoring-project-help.html",
        "title": "Technical Tutoring & Project Help | Yonatan Gemmi",
        "meta_description": "One-on-one technical tutoring, AI tool coaching, workflow training, and project help for founders, students, and operators. Remote sessions.",
        "service_name": "Technical tutoring, coaching, and project help",
        "eyebrow": "Hands-on help",
        "h1": "Technical tutoring, coaching, and project help—paid and practical",
        "lead": "Not every request is a full consulting engagement. I help individuals and small teams learn AI tools, debug workflows, choose software, improve SOPs, or get unstuck on a build—with clear scope and my hourly project rate.",
        "sections": [
            (
                "What this looks like",
                "Focused sessions or short project bursts: explain the system, pair on the fix, document the steps, and leave you with something you can repeat—not dependency on me for every click.",
            ),
            (
                "Common request types",
                "Learning ChatGPT, Custom GPTs, or agent tools responsibly • Spreadsheet and dashboard coaching • Ecommerce ops walkthroughs • Debugging automations • Career-adjacent technical interview prep for ops/systems roles • Helping founders scope what to build vs buy",
            ),
            (
                "Who it is for",
                "Students, solo founders, operators, and teams who want a practitioner in the room—not a course catalog. If the topic is legal, medical, or financial advice, I stay in the technical and operational lane.",
            ),
        ],
        "faqs": [
            (
                "Is this the same as full consulting?",
                "Tutoring and project help are usually narrower and session-based. Larger builds roll into consulting or contract work with a written scope.",
            ),
            (
                "Remote only?",
                "Mostly remote video sessions. South Florida in-person can be arranged for longer workshops when useful.",
            ),
            (
                "Can you help my team adopt a new AI tool?",
                "Yes—live walkthroughs, guardrails, prompt patterns, and simple SOPs so adoption sticks.",
            ),
            (
                "How do we start?",
                "Tell me what you are trying to learn or finish. Use the homepage contact form or email with your timezone and availability.",
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
        link.addEventListener('click', () => setOpen(false));
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


def render(page: dict) -> str:
    slug = page["slug"]
    canonical = f"{BASE}/services/{page['filename']}"
    faqs = page["faqs"]
    schema = faq_schema(
        faqs,
        service_name=page["service_name"],
        meta_description=page["meta_description"],
        canonical=canonical,
    )
    sections_html = ""
    for title, body in page["sections"]:
        sections_html += f"""
        <article class="card service-detail-card">
          <h3>{title}</h3>
          <p>{body}</p>
        </article>
"""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{page['title']}</title>
  <meta name="description" content="{page['meta_description']}" />
  <link rel="canonical" href="{canonical}" />
  <meta name="robots" content="index, follow" />
  <meta name="author" content="Yonatan Gemmi" />
  <meta property="og:title" content="{page['title']}" />
  <meta property="og:description" content="{page['meta_description']}" />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="{canonical}" />
  <meta property="og:site_name" content="Yonatan Gemmi" />
  <meta property="og:image" content="{BASE}/assets/social-preview.png" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{page['title']}" />
  <meta name="twitter:description" content="{page['meta_description']}" />
  <meta name="twitter:image" content="{BASE}/assets/social-preview.png" />
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../styles.css" />
  <link rel="stylesheet" href="../assets/portfolio-chatbot.css" />
  <script type="application/ld+json">
{schema}
  </script>
</head>
<body>
  <div class="site-shell">
    <header class="nav">
      <a class="brand" href="../index.html" aria-label="Yonatan Gemmi home">
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
          <span>{page['service_name']}</span>
        </nav>
        <h1>{page['h1']}</h1>
        <p class="lead">{page['lead']}</p>
        <div class="actions">
          <a class="button primary" href="../index.html#contact">Discuss this service</a>
          <a class="button ghost" href="../index.html#work">See work examples</a>
        </div>
      </section>

      <section class="section split">
        <div>
          <p class="section-kicker">Scope</p>
          <h2>Focused help for one kind of problem.</h2>
          <p class="section-intro">This page is the dedicated entry point for <strong>{page['service_name'].lower()}</strong>. The homepage still covers the full range of offerings—consulting, contract work, and adjacent technical help.</p>
        </div>
        <div class="cards capability-list">
{sections_html}
        </div>
      </section>

      <section id="faq" class="section">
        <div class="section-heading stacked">
          <p class="section-kicker">FAQ</p>
          <h2>Questions about {page['service_name'].lower()}.</h2>
        </div>
        <div class="faq-grid">
{faq_html(faqs)}
        </div>
      </section>

      <section class="section closing-card service-landing-cta">
        <div>
          <p class="section-kicker">Next step</p>
          <h2>Tell me what you are trying to fix or build.</h2>
          <p class="section-intro">Use the contact form on the homepage or email directly. I will respond with practical next steps—not a generic pitch deck.</p>
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