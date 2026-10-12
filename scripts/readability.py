#!/usr/bin/env python3
"""Flesch-Kincaid grade for use-case and landing copy.

Run from the repo root:

    python3 scripts/readability.py
    python3 scripts/readability.py --csv /tmp/readability.csv
    python3 scripts/readability.py --compare /tmp/before.csv /tmp/after.csv
    python3 scripts/readability.py --text "Short sentences help. Everyday words help too."

Scores public-facing copy only. Use-case ``copy_prompt`` is omitted unless
you pass ``--include-prompts``. Target grade is 8.5 where the required terms
allow.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import re
import statistics
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
USE_CASES = ROOT / "data" / "use-cases.json"
TAXONOMY = ROOT / "data" / "taxonomy.json"
BUILD = ROOT / "scripts" / "build_use_cases.py"
TARGET = 8.5

# Fields that readers see on a use-case page (not the copy-ready prompt).
ENTRY_FIELDS = (
    "title",
    "summary",
    "problem",
    "what_si_does",
    "setup",
    "human_checks",
    "examples",
    "effect",
    "caution",
)

ABBREV = {
    "mr",
    "mrs",
    "ms",
    "dr",
    "prof",
    "sr",
    "jr",
    "vs",
    "etc",
    "approx",
    "al",
    "fig",
    "no",
    "nos",
    "vol",
    "inc",
    "ltd",
    "co",
    "corp",
    "st",
    "ave",
    "dept",
}

# Keep letter-name counts modest: treat common all-caps tags as spoken words.
SYLLABLE_OVERRIDES = {
    "si": 1,
    "ai": 1,
    "phi": 1,
    "baa": 1,
    "crm": 1,
    "sku": 1,
    "skus": 1,
    "pdf": 1,
    "rfp": 1,
    "rfps": 1,
    "faq": 1,
    "faqs": 1,
    "sla": 1,
    "hvac": 2,
    "hipaa": 2,
    "ferpa": 2,
    "iolta": 3,
    "aba": 3,
    "irs": 3,
    "ftc": 3,
    "cpa": 3,
    "gtin": 2,
    "mpn": 3,
    "csv": 3,
    "us": 1,
    "usa": 3,
}


class _StripHTML(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def get_text(self) -> str:
        return " ".join(self.parts)


def strip_html(value: str) -> str:
    parser = _StripHTML()
    parser.feed(value or "")
    return re.sub(r"\s+", " ", parser.get_text()).strip()


def _load_build():
    spec = importlib.util.spec_from_file_location("build_use_cases", BUILD)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Cannot import {BUILD}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def count_syllables(word: str) -> int:
    raw = word.strip().lower()
    letters = re.sub(r"[^a-z]", "", raw)
    if not letters:
        if re.search(r"\d", raw):
            return 1
        return 0
    if letters in SYLLABLE_OVERRIDES:
        return SYLLABLE_OVERRIDES[letters]
    if len(letters) <= 2:
        return 1
    w = letters
    if w.endswith("e's"):
        w = w[:-2]
    if w.endswith("s") and not w.endswith(("ss", "us", "is")):
        w = w[:-1]
    if w.endswith("e") and not w.endswith(("le", "ie")) and len(w) > 2:
        w = w[:-1]
    groups = re.findall(r"[aeiouy]+", w)
    count = len(groups)
    if letters.endswith("le") and len(letters) > 2 and letters[-3] not in "aeiouy":
        count += 1
    return max(1, count)


_SENT_SPLIT = re.compile(
    r"(?<=[.!?])(?:['\"”’)]+)?\s+(?=[\"“‘'(A-Z0-9])"
)


def split_sentences(text: str) -> list[str]:
    text = strip_html(text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    protected = text
    for abbr in sorted(ABBREV, key=len, reverse=True):
        protected = re.sub(
            rf"\b({re.escape(abbr)})\.",
            lambda m: m.group(1) + "<prd>",
            protected,
            flags=re.I,
        )
    protected = re.sub(r"\b([A-Z])\.", r"\1<prd>", protected)
    protected = re.sub(r"(\d)\.(\d)", r"\1<prd>\2", protected)
    protected = re.sub(r"\be\.g\.", "e<prd>g<prd>", protected, flags=re.I)
    protected = re.sub(r"\bi\.e\.", "i<prd>e<prd>", protected, flags=re.I)
    if protected[-1] not in ".!?":
        protected += "."
    parts = _SENT_SPLIT.split(protected)
    out = []
    for part in parts:
        sentence = part.replace("<prd>", ".").strip()
        if sentence:
            out.append(sentence)
    return out


def tokenize_words(text: str) -> list[str]:
    return [tok for tok in re.findall(r"[A-Za-z0-9]+(?:'[A-Za-z]+)?", text) if tok]


def score_text(text: str) -> dict:
    sentences = split_sentences(text)
    words: list[str] = []
    for sentence in sentences:
        words.extend(tokenize_words(sentence))
    n_sent = len(sentences)
    n_words = len(words)
    n_syll = sum(count_syllables(w) for w in words)
    if n_sent == 0 or n_words == 0:
        return {
            "grade": 0.0,
            "ease": 0.0,
            "sentences": 0,
            "words": 0,
            "syllables": 0,
            "asl": 0.0,
            "asw": 0.0,
        }
    asl = n_words / n_sent
    asw = n_syll / n_words
    grade = 0.39 * asl + 11.8 * asw - 15.59
    ease = 206.835 - 1.015 * asl - 84.6 * asw
    return {
        "grade": round(grade, 2),
        "ease": round(ease, 2),
        "sentences": n_sent,
        "words": n_words,
        "syllables": n_syll,
        "asl": round(asl, 2),
        "asw": round(asw, 3),
    }


def flatten_value(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return " ".join(flatten_value(item) for item in value if item)
    if isinstance(value, dict):
        return " ".join(flatten_value(item) for item in value.values() if item)
    return str(value).strip()


def entry_text(item: dict, *, include_prompt: bool = False) -> str:
    parts = []
    for key in ENTRY_FIELDS:
        parts.append(flatten_value(item.get(key)))
    if include_prompt:
        parts.append(flatten_value(item.get("copy_prompt")))
    return " ".join(p for p in parts if p)


def industry_text(slug: str, info: dict, faqs: list[tuple[str, str]] | None = None) -> str:
    parts = [
        info.get("label") or "",
        info.get("blurb") or "",
        info.get("seo_h1") or "",
        info.get("meta") or "",
        info.get("short") or "",
        info.get("foot") or "",
        strip_html(info.get("read_first") or ""),
        info.get("caution_prefix") or "",
    ]
    if faqs:
        for q, a in faqs:
            parts.append(q)
            parts.append(a)
    return " ".join(p for p in parts if p)


def function_text(info: dict) -> str:
    return " ".join(
        p
        for p in (
            info.get("label") or "",
            info.get("blurb") or "",
            info.get("seo_h1") or "",
            info.get("meta") or "",
        )
        if p
    )


def extract_hub_copy(source: str) -> str:
    leads = re.findall(r'<p class="lead">(.*?)</p>', source, flags=re.S)
    notes = re.findall(r'<p class="uc-note-intro">(.*?)</p>', source, flags=re.S)
    closing = re.findall(r'<p class="section-intro">(.*?)</p>', source, flags=re.S)
    featured = re.findall(
        r'<h2 id="featured-h">.*?</h2>\s*<p>(.*?)</p>',
        source,
        flags=re.S,
    )
    chunks = []
    for group in (leads, notes, closing, featured):
        chunks.extend(group)
    # Keep unique hub/library strings, skip template interpolations that are empty.
    cleaned = []
    seen = set()
    for chunk in chunks:
        text = strip_html(chunk)
        text = re.sub(r"\{.*?\}", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        if text and text not in seen and "e(with_si_gloss" not in text:
            seen.add(text)
            cleaned.append(text)
    return " ".join(cleaned)


def collect_rows(
    *,
    use_cases_path: Path,
    taxonomy_path: Path,
    include_prompt: bool = False,
) -> list[dict]:
    entries = json.loads(use_cases_path.read_text(encoding="utf-8"))
    tax = json.loads(taxonomy_path.read_text(encoding="utf-8"))
    build = _load_build()
    build.TAX = tax
    build.INDUSTRIES = tax["industries"]
    build.FUNCTIONS = tax["functions"]
    build.OWN_ACCOUNTS = tax["own_accounts"]
    build.ALSO_USED_NOTE = tax["also_used_note"]
    rows = []

    def add(kind: str, key: str, label: str, text: str) -> None:
        stats = score_text(text)
        rows.append(
            {
                "kind": kind,
                "id": key,
                "label": label,
                "grade": stats["grade"],
                "asl": stats["asl"],
                "asw": stats["asw"],
                "sentences": stats["sentences"],
                "words": stats["words"],
                "syllables": stats["syllables"],
                "ease": stats["ease"],
                "over_target": stats["grade"] > TARGET,
            }
        )

    for item in entries:
        add(
            "use-case",
            item["slug"],
            item.get("title") or item["slug"],
            entry_text(item, include_prompt=include_prompt),
        )

    add(
        "site",
        "own_accounts",
        "Own equipment line",
        tax.get("own_accounts") or "",
    )
    add(
        "site",
        "also_used_note",
        "Also-used note",
        tax.get("also_used_note") or "",
    )

    for slug, info in tax["industries"].items():
        faqs = build.industry_faqs(slug)
        add("industry", slug, info.get("label") or slug, industry_text(slug, info, faqs))
        add(
            "industry-intro",
            slug,
            f"{info.get('label') or slug} intro",
            industry_text(slug, info, faqs=None),
        )
        for i, (q, a) in enumerate(faqs, start=1):
            add("industry-faq", f"{slug}-{i}", q, f"{q} {a}")

    for slug, info in tax["functions"].items():
        add("function", slug, info.get("label") or slug, function_text(info))

    hub = extract_hub_copy(BUILD.read_text(encoding="utf-8"))
    add("hub", "use-cases-hub", "Use-case hub intros", hub)
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = [
        "kind",
        "id",
        "label",
        "grade",
        "asl",
        "asw",
        "sentences",
        "words",
        "syllables",
        "ease",
        "over_target",
    ]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def summarize(rows: list[dict], *, kinds: tuple[str, ...] | None = None) -> dict:
    grades = [
        float(row["grade"])
        for row in rows
        if kinds is None or row["kind"] in kinds
    ]
    if not grades:
        return {"count": 0, "median": 0, "min": 0, "max": 0, "over": 0}
    return {
        "count": len(grades),
        "median": round(statistics.median(grades), 2),
        "min": round(min(grades), 2),
        "max": round(max(grades), 2),
        "mean": round(statistics.mean(grades), 2),
        "over": sum(1 for g in grades if g > TARGET),
    }


def print_summary(title: str, stats: dict) -> None:
    print(
        f"{title}: n={stats['count']} median={stats['median']} "
        f"range={stats['min']}–{stats['max']} mean={stats.get('mean', 0)} "
        f"over_{TARGET}={stats['over']}"
    )


def compare(before_path: Path, after_path: Path) -> None:
    before = {(row["kind"], row["id"]): row for row in read_csv(before_path)}
    after = {(row["kind"], row["id"]): row for row in read_csv(after_path)}
    keys = sorted(set(before) | set(after))
    print("kind,id,before,after,delta,over_after")
    deltas = []
    for key in keys:
        b = before.get(key)
        a = after.get(key)
        if not b or not a:
            continue
        bg = float(b["grade"])
        ag = float(a["grade"])
        delta = round(ag - bg, 2)
        deltas.append(delta)
        flag = "YES" if ag > TARGET else ""
        print(f"{key[0]},{key[1]},{bg},{ag},{delta},{flag}")
    if deltas:
        print(
            f"# delta median={round(statistics.median(deltas), 2)} "
            f"range={round(min(deltas), 2)}–{round(max(deltas), 2)}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--use-cases", type=Path, default=USE_CASES)
    parser.add_argument("--taxonomy", type=Path, default=TAXONOMY)
    parser.add_argument("--csv", type=Path, help="Write scores to this CSV")
    parser.add_argument("--json", type=Path, help="Write scores to this JSON file")
    parser.add_argument("--include-prompts", action="store_true")
    parser.add_argument("--text", help="Score a single string and exit")
    parser.add_argument(
        "--kind",
        action="append",
        help="Limit printed rows to this kind (repeatable)",
    )
    parser.add_argument(
        "--fail-above",
        type=float,
        help="Exit 1 if any selected row is above this grade",
    )
    parser.add_argument("--compare", nargs=2, metavar=("BEFORE", "AFTER"))
    args = parser.parse_args()

    if args.text is not None:
        stats = score_text(args.text)
        print(json.dumps(stats, indent=2))
        return

    if args.compare:
        compare(Path(args.compare[0]), Path(args.compare[1]))
        return

    rows = collect_rows(
        use_cases_path=args.use_cases,
        taxonomy_path=args.taxonomy,
        include_prompt=args.include_prompts,
    )
    selected = [row for row in rows if not args.kind or row["kind"] in args.kind]
    if args.csv:
        write_csv(args.csv, selected if args.kind else rows)
    if args.json:
        args.json.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")

    print_summary("use-cases", summarize(rows, kinds=("use-case",)))
    print_summary("industries", summarize(rows, kinds=("industry",)))
    print_summary("industry-intros", summarize(rows, kinds=("industry-intro",)))
    print_summary("industry-faqs", summarize(rows, kinds=("industry-faq",)))
    print_summary("functions", summarize(rows, kinds=("function",)))
    print_summary("hub", summarize(rows, kinds=("hub",)))
    print_summary("all", summarize(rows))

    over = [row for row in selected if float(row["grade"]) > TARGET]
    over.sort(key=lambda row: float(row["grade"]), reverse=True)
    if over:
        print(f"\nAbove {TARGET}:")
        for row in over:
            print(f"  {row['grade']:5.2f}  {row['kind']:14}  {row['id']}")
    if args.fail_above is not None:
        bad = [row for row in selected if float(row["grade"]) > args.fail_above]
        if bad:
            sys.exit(1)


if __name__ == "__main__":
    main()
