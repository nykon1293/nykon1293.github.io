#!/usr/bin/env python3
"""Tests for campaign tracking short-link pages."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import build_tracking_links as tracking
import indexnow_ping as ping
import validate_seo


ROOT = Path(__file__).resolve().parents[1]
SITEMAP = ROOT / "sitemap.xml"

EXPECTED = {
    "1025": "https://gemmisi.com/use-cases/",
    "1026": "https://gemmisi.com/use-cases/report-card-comment-drafts/",
    "1027": "https://gemmisi.com/use-cases/missed-call-text-back/",
    "1028": "https://gemmisi.com/use-cases/status-question-replies/",
    "1029": "https://gemmisi.com/use-cases/daily-briefing/",
    "1030": "https://gemmisi.com/use-cases/",
    "1101": "https://gemmisi.com/use-cases/quote-follow-ups/",
    "1102": "https://gemmisi.com/",
    "1103": "https://gemmisi.com/use-cases/client-document-chasing/",
    "1104": "https://gemmisi.com/use-cases/requests-to-scheduled-jobs/",
    "1105": "https://gemmisi.com/",
    "1106": "https://gemmisi.com/use-cases/invoice-intake-to-draft-bills/",
}


class TrackingConfigTests(unittest.TestCase):
    def test_required_slugs_and_destinations(self) -> None:
        dest_by_slug = dict(tracking.load_links())
        for date, dest in EXPECTED.items():
            for prefix in ("fb", "li"):
                self.assertEqual(dest_by_slug[prefix + date], dest)
        for generic in ("wa", "fb", "li"):
            self.assertEqual(dest_by_slug[generic], "https://gemmisi.com/")
        for prefix in ("fb", "li"):
            self.assertEqual(dest_by_slug[prefix + "1026b"], "https://gemmisi.com/")
            self.assertEqual(
                dest_by_slug[prefix + "1026"],
                "https://gemmisi.com/use-cases/report-card-comment-drafts/",
            )
            self.assertEqual(
                dest_by_slug[prefix + "1027b"],
                "https://gemmisi.com/use-cases/overdue-invoice-reminders/",
            )
            self.assertEqual(
                dest_by_slug[prefix + "1027"],
                "https://gemmisi.com/use-cases/missed-call-text-back/",
            )

    def test_pages_match_generator(self) -> None:
        self.assertEqual(tracking.build(check_only=True), 0)

    def test_pages_are_noindex_with_beacon_and_delay(self) -> None:
        html = (ROOT / "fb1101" / "index.html").read_text(encoding="utf-8")
        self.assertIn("noindex", html)
        self.assertIn('http-equiv="refresh"', html)
        self.assertIn("content=\"1;", html)
        self.assertIn("location.replace('https://gemmisi.com/use-cases/quote-follow-ups/')", html)
        self.assertIn(", 300)", html)
        self.assertIn("cloudflareinsights.com/beacon.min.js", html)
        self.assertIn("c9c911628ffd4644bce7bea8d47eb16c", html)
        self.assertIn(tracking.MARKER, html)
        self.assertTrue(validate_seo.is_moved_page(ROOT / "fb1101" / "index.html"))

    def test_generic_and_remapped_pages(self) -> None:
        wa = (ROOT / "wa" / "index.html").read_text(encoding="utf-8")
        self.assertIn("location.replace('https://gemmisi.com/')", wa)
        shipping = (ROOT / "fb1028" / "index.html").read_text(encoding="utf-8")
        self.assertIn("/use-cases/status-question-replies/", shipping)
        self.assertNotIn("shipping-exceptions-package-watch", shipping)
        crew = (ROOT / "li1104" / "index.html").read_text(encoding="utf-8")
        self.assertIn("/use-cases/requests-to-scheduled-jobs/", crew)
        self.assertNotIn("crew-dispatch-schedule-prep", crew)

    def test_second_oct26_consult_pages_go_home_not_report_card(self) -> None:
        for slug in ("fb1026b", "li1026b"):
            html = (ROOT / slug / "index.html").read_text(encoding="utf-8")
            self.assertIn("location.replace('https://gemmisi.com/')", html)
            self.assertNotIn("report-card-comment-drafts", html)
            self.assertIn("noindex", html)
            self.assertIn(tracking.MARKER, html)
        first = (ROOT / "fb1026" / "index.html").read_text(encoding="utf-8")
        self.assertIn("/use-cases/report-card-comment-drafts/", first)

    def test_second_oct27_pages_go_to_overdue_invoices(self) -> None:
        dest = "https://gemmisi.com/use-cases/overdue-invoice-reminders/"
        for slug in ("fb1027b", "li1027b"):
            html = (ROOT / slug / "index.html").read_text(encoding="utf-8")
            self.assertIn(f"location.replace('{dest}')", html)
            self.assertIn(f'url={dest}', html)
            self.assertIn(f'rel="canonical" href="{dest}"', html)
            self.assertNotIn("missed-call-text-back", html)
            self.assertIn("noindex", html)
            self.assertIn(tracking.MARKER, html)
        first = (ROOT / "fb1027" / "index.html").read_text(encoding="utf-8")
        self.assertIn("/use-cases/missed-call-text-back/", first)

    def test_not_in_sitemap(self) -> None:
        sitemap = SITEMAP.read_text(encoding="utf-8")
        for slug in tracking.load_slugs():
            self.assertNotIn(f"https://gemmisi.com/{slug}", sitemap)

    def test_indexnow_skips_tracking_paths(self) -> None:
        self.assertIsNone(ping.file_to_url("fb1101/index.html"))
        self.assertIsNone(ping.file_to_url("wa/index.html"))
        self.assertEqual(ping.file_to_url("index.html"), "https://gemmisi.com/")
        self.assertEqual(
            ping.file_to_url("use-cases/pricing-pages/index.html"),
            "https://gemmisi.com/use-cases/pricing-pages/",
        )

    def test_refuses_collision_with_existing_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp) / "tracking-links.json"
            data.write_text(
                json.dumps({"posts": {}, "generic": {"services": "/"}}),
                encoding="utf-8",
            )
            original = tracking.DATA
            tracking.DATA = data
            try:
                with self.assertRaises(SystemExit) as ctx:
                    tracking.build(check_only=True)
            finally:
                tracking.DATA = original
            self.assertIn("collide", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
