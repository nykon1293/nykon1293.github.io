#!/usr/bin/env python3
"""Generate the static use-cases library from data/use-cases.json.

Run from the repo root:

    python3 scripts/build_use_cases.py

Writes use-cases/index.html, one folder per slug, and refreshes the
use-case URLs in sitemap.xml. Pages are plain HTML. GitHub Pages serves
them with no build step.
"""

from __future__ import annotations

import html
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "use-cases.json"
OUT = ROOT / "use-cases"
SITEMAP = ROOT / "sitemap.xml"

BASE = "https://gemmisi.com"
CAL = "https://calendly.com/josh-gemmi/30min"
OG_IMAGE = f"{BASE}/assets/use-cases-social-preview.png"
OG_ALT = "Yonatan Gemmi — 72 practical SI use cases for small teams"

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


def json_ld(obj) -> str:
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
        slugs.append(item["slug"])
    dupes = {slug for slug in slugs if slugs.count(slug) > 1}
    if dupes:
        raise SystemExit(f"Duplicate slugs: {', '.join(sorted(dupes))}")
    return entries


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
      <a class="brand" href="{up}index.html" aria-label="Yonatan Gemmi home">
        <img class="brand-mark" src="{up}assets/yonatan-gemmi-pixel-portrait-256.png" alt="" width="34" height="34" />
        <span>Yonatan Gemmi</span>
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


SCRIPTS = """  <script>document.getElementById('year').textContent = new Date().getFullYear();</script>
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
      document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') setOpen(false);
      });
      document.addEventListener('click', (event) => {
        if (!nav.classList.contains('is-menu-open')) return;
        if (nav.contains(event.target)) return;
        setOpen(false);
      });
    })();
  </script>
"""


def head(title: str, desc: str, canon: str, depth: int, ld: dict) -> str:
    up = "../" * depth
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
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&amp;family=JetBrains+Mono:wght@500;700&amp;display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="{up}styles.css?v=nav-row-1" />
  <link rel="stylesheet" href="{up}assets/use-cases.css" />
  <link rel="icon" href="{up}assets/yonatan-gemmi-pixel-portrait-256.png" type="image/png" />
  <link rel="apple-touch-icon" href="/assets/yonatan-gemmi-pixel-portrait-256.png" />
  <script type="application/ld+json">
{json_ld(ld)}
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


def card(item: dict, href: str, show_cat: bool = True, extra: bool = False) -> str:
    short = SHORT[item["category"]]
    cat = f'<span class="uc-card-cat">{e(short[0])}</span>' if show_cat else ""
    extra_cls = " uc-extra" if extra else ""
    return f"""<li class="uc-card{extra_cls}" data-cat="{short[1]}" data-hay="{e(haystack(item))}">
            <a href="{href}">
              {cat}
              <h3>{e(item['title'])}</h3>
              <p>{e(item['summary'])}</p>
              <span class="uc-card-more">Read the use case <span aria-hidden="true">→</span></span>
            </a>
          </li>"""


def library_page(entries: list) -> str:
    n = len(entries)
    cats = categories(entries)
    title = "SI use cases for small businesses and community organizations | Yonatan Gemmi"
    desc = (
        f"{n} practical ways SI can take routine work off a small team: inbox and support, "
        "sales follow-up, bookkeeping, reporting, scheduling, inventory, content, hiring, "
        "documents, and community organizations. Each one shows what a human still checks."
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
    sections = []
    for index, cat in enumerate(cats, 1):
        label, slug, blurb = SHORT[cat]
        items = [item for item in entries if item["category"] == cat]
        cards = "\n          ".join(
            card(item, f"{item['slug']}/", show_cat=False, extra=i >= 4) for i, item in enumerate(items)
        )
        more = ""
        if len(items) > 4:
            more = (
                f'<button type="button" class="uc-more" data-n="{len(items)}" '
                f'aria-expanded="false">Show all {len(items)}</button>'
            )
        sections.append(
            f"""      <section class="uc-group" data-group="{slug}" aria-labelledby="g-{slug}">
        <div class="uc-group-head">
          <span class="section-kicker">{index:02d}</span>
          <h2 id="g-{slug}">{e(label)}</h2>
          <p>{e(blurb)}</p>
        </div>
        <ul class="uc-grid">
          {cards}
        </ul>
        {more}
      </section>"""
        )
    # The single allowed "AI" bridge lives in this intro and nowhere else.
    return head(title, desc, "/use-cases/", 1, ld) + f"""
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
        <p class="uc-count" id="uc-count" role="status" aria-live="polite">Showing {n} of {n} use cases</p>
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
""" + foot(1) + SCRIPTS + """  <script>
    (() => {
      const q = document.getElementById('uc-q');
      const pills = [...document.querySelectorAll('.uc-pill')];
      const cards = [...document.querySelectorAll('.uc-card')];
      const groups = [...document.querySelectorAll('.uc-group')];
      const count = document.getElementById('uc-count');
      const empty = document.getElementById('uc-empty');
      let cat = 'all';
      const apply = () => {
        const terms = q.value.trim().toLowerCase().split(/\\s+/).filter(Boolean);
        const filtering = terms.length > 0 || cat !== 'all';
        let shown = 0;
        cards.forEach((card) => {
          const ok = (cat === 'all' || card.dataset.cat === cat) && terms.every((term) => card.dataset.hay.includes(term));
          card.hidden = !ok;
          if (ok) shown++;
        });
        groups.forEach((group) => {
          const vis = group.querySelectorAll('.uc-card:not([hidden])').length;
          group.hidden = vis === 0;
          const btn = group.querySelector('.uc-more');
          group.classList.toggle('is-open', filtering || (btn && btn.getAttribute('aria-expanded') === 'true'));
          if (btn) btn.hidden = filtering;
        });
        count.textContent = 'Showing ' + shown + ' of ' + cards.length + ' use cases';
        empty.hidden = shown > 0;
      };
      groups.forEach((group) => {
        const btn = group.querySelector('.uc-more');
        if (!btn) return;
        btn.addEventListener('click', () => {
          const open = btn.getAttribute('aria-expanded') !== 'true';
          btn.setAttribute('aria-expanded', open ? 'true' : 'false');
          btn.textContent = open ? 'Show fewer' : 'Show all ' + btn.dataset.n;
          group.classList.toggle('is-open', open);
        });
      });
      pills.forEach((pill) => pill.addEventListener('click', () => {
        cat = pill.dataset.filter;
        pills.forEach((other) => {
          const on = other === pill;
          other.classList.toggle('is-active', on);
          other.setAttribute('aria-pressed', on ? 'true' : 'false');
        });
        apply();
      }));
      q.addEventListener('input', apply);
    })();
  </script>
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
          {caution}
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
    for item in entries:
        page = (OUT / item["slug"] / "index.html").read_text(encoding="utf-8")
        if re.search(r"\bAI\b", page) or "noindex" in page or "Nous" in page or "Brandgate" in page:
            raise SystemExit(f"Wording check failed for {item['slug']}")


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
