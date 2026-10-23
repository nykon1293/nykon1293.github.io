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


class TrackingConfigTests(unittest.TestCase):
    def test_required_slugs_present(self) -> None:
        slugs = tracking.load_slugs()
        for prefix in ("fb", "li"):
            for day in ("1025", "1026", "1027", "1028", "1029", "1030", "1101", "1102", "1103", "1104", "1105", "1106"):
                self.assertIn(prefix + day, slugs)
        for generic in ("wa", "fb", "li"):
            self.assertIn(generic, slugs)
        self.assertEqual(tracking.destination(), "https://gemmisi.com/")

    def test_pages_match_generator(self) -> None:
        self.assertEqual(tracking.build(check_only=True), 0)

    def test_pages_are_noindex_with_beacon_and_delay(self) -> None:
        html = (ROOT / "fb1101" / "index.html").read_text(encoding="utf-8")
        self.assertIn("noindex", html)
        self.assertIn('http-equiv="refresh"', html)
        self.assertIn("content=\"1;", html)
        self.assertIn("location.replace", html)
        self.assertIn(", 300)", html)
        self.assertIn("cloudflareinsights.com/beacon.min.js", html)
        self.assertIn("c9c911628ffd4644bce7bea8d47eb16c", html)
        self.assertIn(tracking.MARKER, html)
        self.assertTrue(validate_seo.is_moved_page(ROOT / "fb1101" / "index.html"))

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
            folder = Path(tmp)
            data = folder / "tracking-links.json"
            data.write_text(
                json.dumps({"destination": "https://gemmisi.com/", "slugs": ["services"]}),
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
