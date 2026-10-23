#!/usr/bin/env python3
"""Pixel-art motifs for use-case detail pages.

Nine function motifs share one 24×24 grid, palette, and framing. A tenth
drawing (shield) is a simple lock, used only for true privacy topics.
Legal pages use the scales of justice, or the sealed-document motif.
Industry accent comes from the entry's primary industry, or from the
primary function when the industry is ``any-business``. An optional JSON
field ``motif`` overrides the keyword rules.
"""

from __future__ import annotations

import html
import re
from pathlib import Path

N = 24
BG = "#121914"
PAPER = "#efe6c8"
INK = "#080b0a"
GREEN = "#36d399"
INNER = "#1a231c"

# Nine function motifs, plus shield as the privacy-only lock.
FUNCTION_MOTIFS = (
    "inbox",
    "calendar",
    "invoices",
    "dashboard",
    "inventory",
    "documents",
    "phone",
    "checklist",
    "scales",
)
MOTIFS = FUNCTION_MOTIFS + ("shield",)

# Plain-language alt for the <img> thumbnails. Lockups stay alt="".
MOTIF_ALT = {
    "inbox": "Pixel drawing of an open email inbox",
    "calendar": "Pixel drawing of a calendar with marked days",
    "invoices": "Pixel drawing of a paper invoice and a stamp",
    "dashboard": "Pixel drawing of a dashboard with bars and charts",
    "inventory": "Pixel drawing of three stacked stock boxes",
    "documents": "Pixel drawing of stacked papers with a seal",
    "phone": "Pixel drawing of a phone next to a short message",
    "checklist": "Pixel drawing of a checklist with two boxes checked",
    "scales": "Pixel drawing of a balance scale",
    "shield": "Pixel drawing of a padlock",
}


def motif_alt_text(motif: str) -> str:
    return MOTIF_ALT.get(motif, "Pixel drawing for this use case")


INDUSTRY_ACCENT = {
    "legal": ("legal", "#c9a45c"),
    "medical": ("medical", "#7eb8a4"),
    "ecommerce": ("ecommerce", "#e3b45a"),
    "local-seasonal": ("local", "#87b58a"),
    "real-estate": ("real-estate", "#c4a06a"),
    "home-services": ("home-services", "#d3aa55"),
    "accounting": ("accounting", "#cfc09a"),
    "education": ("education", "#8aa07a"),
    "restaurants-food": ("restaurants-food", "#d0894e"),
    "auto-repair": ("auto-repair", "#b89a58"),
    "fitness-salons-wellness": ("fitness-salons-wellness", "#9aaf7a"),
    "short-term-rentals": ("short-term-rentals", "#c9a878"),
    "insurance-agencies": ("insurance-agencies", "#8aa0b0"),
    "appraisers": ("appraisers", "#b7a48a"),
    "travel-agencies": ("travel-agencies", "#7aa0c4"),
    "marketing-agencies": ("marketing-agencies", "#c4786a"),
    "nonprofits": ("nonprofits", "#6f9a86"),
    "warehousing-wholesale": ("warehousing-wholesale", "#b09a62"),
}

FUNCTION_ACCENT = {
    "customer-support": ("support", "#d3aa55"),
    "sales-follow-up": ("sales", "#dbb05e"),
    "billing-admin": ("billing", "#d3aa55"),
    "scheduling": ("scheduling", "#a8b56a"),
    "reporting-dashboards": ("reporting", "#8fbf9a"),
    "inventory-orders": ("inventory", "#c4a056"),
    "content-marketing": ("marketing", "#d3aa55"),
    "hiring": ("hiring", "#b89a74"),
    "research-documents": ("research", "#cfc09a"),
    "community": ("community", "#d4a06e"),
}

DEFAULT_INDUSTRY = ("default", "#d3aa55")

INDUSTRY_MOTIF = {
    "any-business": "inbox",
    "legal": "scales",
    "medical": "checklist",
    "ecommerce": "inventory",
    "local-seasonal": "inbox",
    "real-estate": "inbox",
    "home-services": "phone",
    "accounting": "documents",
    "education": "documents",
    "restaurants-food": "inventory",
    "auto-repair": "phone",
    "fitness-salons-wellness": "calendar",
    "short-term-rentals": "calendar",
    "insurance-agencies": "documents",
    "appraisers": "documents",
    "travel-agencies": "calendar",
    "marketing-agencies": "dashboard",
    "nonprofits": "checklist",
    "warehousing-wholesale": "inventory",
}

FUNCTION_MOTIF = {
    "customer-support": "inbox",
    "sales-follow-up": "inbox",
    "billing-admin": "invoices",
    "reporting-dashboards": "dashboard",
    "scheduling": "calendar",
    "inventory-orders": "inventory",
    "content-marketing": "documents",
    "hiring": "checklist",
    "research-documents": "documents",
    "community": "inbox",
}

# First matching keyword wins. Slug, then title, then summary. Short tokens
# use word boundaries. Shield is privacy only — not legal-admin or weather.
KEYWORD_RULES: list[tuple[str, tuple[str, ...]]] = [
    (
        "shield",
        (
            "privacy",
            "hipaa",
            "phi",
            "baa",
            "security-plan",
            "security plan",
            "access review",
        ),
    ),
    (
        "scales",
        (
            "conflict-prep",
            "conflict prep",
            "conflict check",
        ),
    ),
    (
        "invoices",
        (
            "invoice",
            "billing",
            "unpaid",
            "payments",
            "receipt",
            "unbilled",
            "tax document",
            "cash flow",
            "cash-flow",
            "balance",
            "claim denial",
            "claim-denial",
            "payroll",
            "time-entry",
            "time entry",
            "donation",
            "subscription",
            "renewal",
            "margin",
            "price increase",
            "month-end",
            "month end",
            "rent-reminder",
            "rent reminder",
            "1099",
            "sales-tax",
            "sales tax",
            "reconciliation",
            "transaction",
        ),
    ),
    (
        "phone",
        (
            "call",
            "calls",
            "calling",
            "phone",
            "sms",
            "text message",
            "text-back",
            "after-hours",
            "after hours",
            "front desk",
            "front-desk",
            "voicemail",
            "missed-call",
        ),
    ),
    (
        "calendar",
        (
            "calendar",
            "schedule",
            "scheduling",
            "scheduled",
            "appointment",
            "reminder",
            "reminders",
            "waitlist",
            "interview",
            "volunteer-scheduling",
            "volunteer schedul",
            "event registration",
            "deadline",
            "recall visit",
            "recall-visit",
            "confirmation",
            "confirmations",
            "showing",
            "open-house",
            "dispatch",
        ),
    ),
    (
        "inventory",
        (
            "inventory",
            "stock",
            "reorder",
            "receiving",
            "warehouse",
            "catalog",
            "sku",
            "supplier",
            "purchase order",
            "stuck order",
            "lead time",
            "store stock",
            "parts-materials",
            "parts and materials",
        ),
    ),
    (
        "dashboard",
        (
            "dashboard",
            "snapshot",
            "weekly team report",
            "weekly-team-report",
            "revenue",
            "ad spend",
            "ad-spend",
            "competitor",
            "look-ahead",
            "look ahead",
            "feedback theme",
            "feedback-themes",
        ),
    ),
    (
        "inbox",
        (
            "inbox",
            "email",
            "reply",
            "replies",
            "thread",
            "triage",
            "faq",
            "chat",
            "outreach",
            "comment",
            "announcement",
            "status update",
            "status-question",
            "status question",
            "follow-up",
            "follow up",
            "speed-to-lead",
            "speed to lead",
            "review request",
            "bilingual",
            "quote-follow",
            "check-in",
            "checkins",
            "check-ins",
            "inquiry",
        ),
    ),
    (
        "documents",
        (
            "document",
            "contract",
            "pdf",
            "file",
            "brief",
            "letter",
            "naming",
            "records",
            "proposal",
            "rfp",
            "grant",
            "lesson",
            "training materials",
            "lesson-and-training",
            "marketing draft",
            "firm-marketing",
            "job posting",
            "job-posting",
            "engagement letter",
            "matter file",
            "matter-file",
            "board packet",
            "board-packet",
            "session notes",
            "session-notes",
            "long-document",
            "long document",
            "web pages",
            "search snippet",
            "newsletter",
            "social-post",
            "repurpose",
            "claims check",
            "marketing-claims",
            "listing",
            "ad-drafts",
            "job-photo",
            "notice-drafts",
        ),
    ),
    (
        "checklist",
        (
            "checklist",
            "onboarding",
            "sop",
            "sops",
            "intake checklist",
            "intake-checklist",
            "patient-intake",
            "verification",
            "tracker",
            "tracking",
            "form filling",
            "portal",
            "license",
            "certification",
            "authorization",
            "readiness",
            "approval queue",
            "application",
            "timesheet",
            "options comparison",
            "google-business",
            "google business",
            "work-order",
            "move-in",
            "move-out",
            "permit",
            "inspection",
            "completeness",
        ),
    ),
]


def _hex_rgb(color: str) -> tuple[int, int, int]:
    raw = color.lstrip("#")
    return int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)


def _rgb_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def _mix(a: str, b: str, t: float) -> str:
    ar, ag, ab = _hex_rgb(a)
    br, bg, bb = _hex_rgb(b)
    return _rgb_hex(
        (
            round(ar + (br - ar) * t),
            round(ag + (bg - ag) * t),
            round(ab + (bb - ab) * t),
        )
    )


def _grid() -> list[list[str]]:
    return [["."] * N for _ in range(N)]


def _plot(grid: list[list[str]], x: int, y: int, ch: str) -> None:
    if 0 <= x < N and 0 <= y < N:
        grid[y][x] = ch


def _rect(grid: list[list[str]], x: int, y: int, w: int, h: int, ch: str) -> None:
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            _plot(grid, xx, yy, ch)


def _outline(grid: list[list[str]], x: int, y: int, w: int, h: int, ch: str) -> None:
    _rect(grid, x, y, w, 1, ch)
    _rect(grid, x, y + h - 1, w, 1, ch)
    _rect(grid, x, y, 1, h, ch)
    _rect(grid, x + w - 1, y, 1, h, ch)


def _hline(grid: list[list[str]], x: int, y: int, w: int, ch: str) -> None:
    _rect(grid, x, y, w, 1, ch)


def _vline(grid: list[list[str]], x: int, y: int, h: int, ch: str) -> None:
    _rect(grid, x, y, 1, h, ch)


def _check(grid: list[list[str]], x: int, y: int, ch: str) -> None:
    _plot(grid, x, y + 2, ch)
    _plot(grid, x + 1, y + 3, ch)
    _plot(grid, x + 2, y + 2, ch)
    _plot(grid, x + 3, y + 1, ch)
    _plot(grid, x + 4, y, ch)


def _seal(grid: list[list[str]], cx: int, cy: int) -> None:
    """Circular-ish wax seal, no lettering."""
    _rect(grid, cx - 2, cy - 3, 5, 7, "#")
    _rect(grid, cx - 3, cy - 2, 7, 5, "#")
    _rect(grid, cx - 1, cy - 1, 3, 3, "=")
    _plot(grid, cx, cy, "s")


def draw_inbox() -> list[list[str]]:
    g = _grid()
    _outline(g, 2, 5, 20, 14, "#")
    _rect(g, 3, 6, 18, 12, "+")
    _hline(g, 2, 5, 20, "#")
    for i in range(10):
        _plot(g, 2 + i, 5 + i, "#")
        _plot(g, 21 - i, 5 + i, "#")
        if i < 9:
            _plot(g, 3 + i, 5 + i, "=")
            _plot(g, 20 - i, 5 + i, "=")
    _plot(g, 3, 6, "s")
    return g


def draw_calendar() -> list[list[str]]:
    g = _grid()
    _outline(g, 3, 2, 18, 20, "#")
    _rect(g, 4, 3, 16, 18, "+")
    _rect(g, 4, 3, 16, 5, "#")
    _rect(g, 7, 4, 3, 3, "@")
    _rect(g, 14, 4, 3, 3, "@")
    _plot(g, 8, 5, "d")
    _plot(g, 15, 5, "d")
    cols = (5, 8, 11, 14)
    rows = (10, 13, 16)
    for y in rows:
        for x in cols:
            _rect(g, x, y, 2, 2, "d")
    _rect(g, 11, 13, 2, 2, "#")
    _rect(g, 8, 10, 2, 2, "s")
    return g


def draw_invoices() -> list[list[str]]:
    g = _grid()
    _outline(g, 3, 2, 13, 19, "#")
    _rect(g, 4, 3, 11, 17, "+")
    _hline(g, 6, 5, 7, "#")
    _hline(g, 6, 8, 6, "=")
    _hline(g, 6, 10, 7, "=")
    _hline(g, 6, 12, 5, "=")
    _hline(g, 6, 16, 6, "#")
    _rect(g, 16, 15, 6, 6, "#")
    _hline(g, 17, 14, 4, "#")
    _hline(g, 17, 21, 4, "#")
    _vline(g, 15, 16, 4, "#")
    _vline(g, 22, 16, 4, "#")
    _rect(g, 17, 16, 4, 4, "s")
    _rect(g, 18, 17, 2, 2, "=")
    _plot(g, 5, 3, "s")
    return g


def draw_dashboard() -> list[list[str]]:
    g = _grid()
    _outline(g, 2, 2, 20, 20, "#")
    _rect(g, 3, 3, 18, 18, "d")
    _rect(g, 3, 3, 18, 3, "#")
    _plot(g, 5, 4, "@")
    _plot(g, 7, 4, "@")
    _plot(g, 9, 4, "s")
    _outline(g, 4, 7, 8, 5, "=")
    _plot(g, 6, 10, "g")
    _plot(g, 7, 9, "g")
    _plot(g, 8, 8, "#")
    _plot(g, 9, 9, "s")
    _outline(g, 13, 7, 7, 5, "=")
    _hline(g, 14, 9, 5, "s")
    heights = (6, 4, 7, 3, 5)
    xs = (5, 8, 11, 14, 17)
    for x, h in zip(xs, heights):
        _rect(g, x, 19 - h, 2, h, "#")
        _plot(g, x, 19 - h, "s")
    return g


def draw_inventory() -> list[list[str]]:
    g = _grid()

    def crate(x: int, y: int) -> None:
        _outline(g, x, y, 10, 8, "#")
        _rect(g, x + 1, y + 1, 8, 6, "+")
        _rect(g, x + 1, y + 3, 8, 2, "#")
        _plot(g, x + 1, y + 1, "s")

    crate(7, 3)
    crate(2, 13)
    crate(12, 13)
    return g


def draw_documents() -> list[list[str]]:
    g = _grid()
    _outline(g, 6, 2, 14, 16, "=")
    _rect(g, 7, 3, 12, 14, INNER)
    _outline(g, 3, 5, 14, 16, "#")
    _rect(g, 4, 6, 12, 14, "+")
    _hline(g, 6, 8, 8, "=")
    _hline(g, 6, 10, 7, "=")
    _hline(g, 6, 12, 8, "=")
    _seal(g, 14, 17)
    _plot(g, 5, 6, "s")
    return g


def draw_phone() -> list[list[str]]:
    g = _grid()
    _outline(g, 5, 2, 10, 20, "#")
    _rect(g, 6, 3, 8, 18, "@")
    _rect(g, 7, 5, 6, 11, "d")
    _hline(g, 8, 7, 4, "=")
    _hline(g, 8, 9, 3, "s")
    _hline(g, 8, 11, 4, "=")
    _rect(g, 8, 18, 4, 2, "#")
    _outline(g, 14, 6, 8, 7, "#")
    _rect(g, 15, 7, 6, 5, "+")
    _hline(g, 16, 8, 4, "=")
    _hline(g, 16, 10, 3, "=")
    _plot(g, 14, 12, "#")
    _plot(g, 15, 13, "#")
    _plot(g, 6, 3, "s")
    return g


def draw_checklist() -> list[list[str]]:
    g = _grid()
    _outline(g, 3, 2, 18, 20, "#")
    _rect(g, 4, 3, 16, 18, "+")
    rows = (5, 11, 17)
    for i, y in enumerate(rows):
        _outline(g, 6, y, 4, 4, "=" if i < 2 else "#")
        _rect(g, 7, y + 1, 2, 2, "d")
        _hline(g, 12, y + 1, 6 if i < 2 else 4, "=" if i else "#")
        if i < 2:
            _check(g, 6, y, "g")
    _plot(g, 5, 3, "s")
    return g


def draw_scales() -> list[list[str]]:
    g = _grid()
    _rect(g, 11, 1, 2, 1, "s")
    _rect(g, 10, 2, 4, 2, "#")
    _rect(g, 3, 4, 18, 2, "#")
    _plot(g, 3, 4, "s")
    _plot(g, 20, 4, "s")
    _rect(g, 11, 6, 2, 13, "#")
    _vline(g, 5, 6, 5, "=")
    _vline(g, 8, 6, 5, "=")
    _hline(g, 3, 11, 8, "#")
    _hline(g, 4, 12, 6, "=")
    _hline(g, 5, 13, 4, "#")
    _vline(g, 15, 6, 5, "=")
    _vline(g, 18, 6, 5, "=")
    _hline(g, 13, 11, 8, "#")
    _hline(g, 14, 12, 6, "=")
    _hline(g, 15, 13, 4, "#")
    _rect(g, 9, 19, 6, 1, "#")
    _rect(g, 7, 20, 10, 2, "#")
    return g


def draw_shield() -> list[list[str]]:
    """Simple padlock. Privacy topics only — not a stand-in for legal work."""
    g = _grid()
    _hline(g, 8, 3, 8, "#")
    _vline(g, 8, 4, 7, "#")
    _vline(g, 15, 4, 7, "#")
    _hline(g, 9, 4, 6, "=")
    _vline(g, 9, 5, 6, "=")
    _vline(g, 14, 5, 6, "=")
    _outline(g, 5, 10, 14, 11, "#")
    _rect(g, 6, 11, 12, 9, "=")
    _rect(g, 10, 13, 4, 3, "@")
    _rect(g, 11, 16, 2, 3, "@")
    _plot(g, 11, 14, "d")
    _plot(g, 6, 11, "s")
    return g


DRAWERS = {
    "inbox": draw_inbox,
    "calendar": draw_calendar,
    "invoices": draw_invoices,
    "dashboard": draw_dashboard,
    "inventory": draw_inventory,
    "documents": draw_documents,
    "phone": draw_phone,
    "checklist": draw_checklist,
    "scales": draw_scales,
    "shield": draw_shield,
}


def _palette(accent: str) -> dict[str, str]:
    return {
        "#": accent,
        "=": _mix(accent, INK, 0.38),
        "+": PAPER,
        "@": INK,
        "g": GREEN,
        "d": INNER,
        "s": _mix(accent, PAPER, 0.42),
    }


def _rects(grid: list[list[str]], palette: dict[str, str]) -> list[tuple[int, int, int, int, str]]:
    used = [[False] * N for _ in range(N)]
    out: list[tuple[int, int, int, int, str]] = []
    for y in range(N):
        for x in range(N):
            if used[y][x]:
                continue
            ch = grid[y][x]
            if ch not in palette:
                used[y][x] = True
                continue
            x2 = x + 1
            while x2 < N and grid[y][x2] == ch and not used[y][x2]:
                x2 += 1
            y2 = y + 1
            while y2 < N and all(grid[y2][xx] == ch and not used[y2][xx] for xx in range(x, x2)):
                y2 += 1
            for yy in range(y, y2):
                for xx in range(x, x2):
                    used[yy][xx] = True
            out.append((x, y, x2 - x, y2 - y, palette[ch]))
    return out


def _contains(blob: str, word: str) -> bool:
    if " " in word or "-" in word:
        return word in blob
    return re.search(r"(?<![a-z0-9])" + re.escape(word) + r"(?![a-z0-9])", blob) is not None


def _primary(item: dict, field: str) -> str:
    values = item.get(field) or []
    return values[0] if values else ""


def pick_industry(item: dict) -> tuple[str, str]:
    ind = _primary(item, "industries")
    if ind in INDUSTRY_ACCENT:
        return INDUSTRY_ACCENT[ind]
    fn = _primary(item, "functions")
    return FUNCTION_ACCENT.get(fn, DEFAULT_INDUSTRY)


def pick_motif(item: dict) -> str:
    explicit = (item.get("motif") or "").strip()
    if explicit:
        if explicit not in MOTIFS:
            raise SystemExit(
                f"{item.get('slug', '?')} motif {explicit!r} is not one of {', '.join(MOTIFS)}"
            )
        return explicit
    slug = item.get("slug") or ""
    slug_blob = f"{slug} {slug.replace('-', ' ')}".lower()
    title = (item.get("title") or "").lower()
    summary = (item.get("summary") or "").lower()
    for blob in (slug_blob, title, summary):
        for motif, words in KEYWORD_RULES:
            if any(_contains(blob, word) for word in words):
                return motif
    ind = _primary(item, "industries")
    if ind in INDUSTRY_MOTIF:
        return INDUSTRY_MOTIF[ind]
    return FUNCTION_MOTIF.get(_primary(item, "functions"), "documents")


def render_svg(motif: str, accent: str) -> str:
    if motif not in DRAWERS:
        motif = "documents"
    grid = DRAWERS[motif]()
    rects = _rects(grid, _palette(accent))
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {N} {N}" width="220" height="220" '
        'focusable="false" shape-rendering="crispEdges">',
        f'<rect width="{N}" height="{N}" fill="{BG}"/>',
    ]
    for x, y, w, h, fill in rects:
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"/>')
    parts.append("</svg>")
    svg = "".join(parts)
    if "<text" in svg:
        raise SystemExit(f"motif {motif} svg must not contain text")
    return svg


def motif_html_from_parts(motif: str, key: str, accent: str, *, inline: bool = True) -> str:
    if inline:
        inner = render_svg(motif, accent)
    else:
        inner = (
            f'<img src="/assets/use-case-motifs/{motif}--{key}.svg" '
            f'width="220" height="220" alt="{html.escape(motif_alt_text(motif), quote=True)}" decoding="async">'
        )
    return (
        f'<div class="uc-motif uc-motif--{key}" data-motif="{motif}" aria-hidden="true">\n'
        f'            <div class="uc-motif-frame">\n'
        f"              {inner}\n"
        f"            </div>\n"
        f"          </div>"
    )


def motif_html(item: dict, *, inline: bool = True) -> str:
    motif = pick_motif(item)
    key, accent = pick_industry(item)
    return motif_html_from_parts(motif, key, accent, inline=inline)


def motif_thumb_html(item: dict) -> str:
    return motif_html(item, inline=False)


def landing_motif_parts(kind: str, slug: str) -> tuple[str, str, str]:
    if kind == "industry":
        if slug in INDUSTRY_ACCENT:
            key, accent = INDUSTRY_ACCENT[slug]
            motif = INDUSTRY_MOTIF.get(slug, "documents")
        else:
            key, accent = DEFAULT_INDUSTRY
            motif = INDUSTRY_MOTIF.get(slug, "inbox")
        return motif, key, accent
    key, accent = FUNCTION_ACCENT.get(slug, DEFAULT_INDUSTRY)
    motif = FUNCTION_MOTIF.get(slug, "documents")
    return motif, key, accent


def landing_motif_html(kind: str, slug: str, *, inline: bool = True) -> str:
    motif, key, accent = landing_motif_parts(kind, slug)
    return motif_html_from_parts(motif, key, accent, inline=inline)


def write_motif_assets(entries: list) -> None:
    dest = Path(__file__).resolve().parent.parent / "assets" / "use-case-motifs"
    dest.mkdir(parents=True, exist_ok=True)
    wanted: dict[tuple[str, str], str] = {}
    for item in entries:
        motif = pick_motif(item)
        key, accent = pick_industry(item)
        wanted[(motif, key)] = accent
    for slug in list(INDUSTRY_MOTIF) + list(INDUSTRY_ACCENT):
        motif, key, accent = landing_motif_parts("industry", slug)
        wanted[(motif, key)] = accent
    for slug in FUNCTION_ACCENT:
        motif, key, accent = landing_motif_parts("function", slug)
        wanted[(motif, key)] = accent
    keep = set()
    for (motif, key), accent in wanted.items():
        name = f"{motif}--{key}.svg"
        keep.add(name)
        (dest / name).write_text(render_svg(motif, accent) + "\n", encoding="utf-8")
    for old in dest.glob("*.svg"):
        if old.name not in keep:
            old.unlink()


def motif_bytes(item: dict) -> int:
    return len(motif_html(item).encode("utf-8"))


def contact_sheet_html(accent: str = "#d3aa55") -> str:
    labels = {
        "inbox": "inbox",
        "calendar": "calendar",
        "invoices": "invoices",
        "dashboard": "dashboard",
        "inventory": "inventory",
        "documents": "documents",
        "phone": "phone",
        "checklist": "checklist",
        "scales": "scales",
        "shield": "privacy lock",
    }
    parts = [
        "<!doctype html><html lang='en'><meta charset='utf-8'><title>Use-case motifs</title>",
        "<style>",
        "body{margin:0;padding:28px;background:#080b0a;color:#f5f4ec;",
        "font:600 13px/1.3 'IBM Plex Sans',system-ui,sans-serif}",
        ".grid{display:grid;grid-template-columns:repeat(5,160px);gap:22px;justify-content:center}",
        ".card{width:160px;text-align:center}",
        ".frame{padding:3px;border:1px solid rgba(255,255,255,.16);border-radius:8px;",
        "background:linear-gradient(180deg,rgba(255,255,255,.10),rgba(255,255,255,.035)),",
        "radial-gradient(circle at 30% 20%,rgba(211,170,85,.22),transparent 58%)}",
        "svg{display:block;width:100%;height:auto;border-radius:5px;image-rendering:pixelated}",
        "label{display:block;margin:8px 0 0;color:#d3aa55;letter-spacing:.02em}",
        "</style><div class='grid'>",
    ]
    for motif in MOTIFS:
        parts.append(
            f"<div class='card'><div class='frame'>{render_svg(motif, accent)}</div>"
            f"<label>{labels[motif]}</label></div>"
        )
    parts.append("</div></html>")
    return "".join(parts)


if __name__ == "__main__":
    from pathlib import Path

    out = Path("/tmp/uc-motifs-contact.html")
    out.write_text(contact_sheet_html(), encoding="utf-8")
    print(out)
