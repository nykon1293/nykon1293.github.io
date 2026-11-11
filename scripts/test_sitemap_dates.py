#!/usr/bin/env python3
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sitemap_dates as dates


class MaxDateTests(unittest.TestCase):
    def test_picks_latest(self) -> None:
        self.assertEqual(dates.max_date("2024-01-01", None, "2026-10-12"), "2026-10-12")


class UseCaseDateTests(unittest.TestCase):
    def test_entry_dates_vary_and_are_not_all_today(self) -> None:
        payload = json.loads((dates.ROOT / dates.USE_CASES_JSON).read_text(encoding="utf-8"))
        found = dates.json_keyed_dates(dates.USE_CASES_JSON, dates.extract_use_cases)
        self.assertGreater(len(found), 20)
        self.assertIn("inbox-triage", found)
        self.assertIn("card-pricecharting-collection", found)
        self.assertGreater(len(set(found.values())), 3)
        self.assertLess(min(found.values()), max(found.values()))
        self.assertEqual(set(found), {item["slug"] for item in payload})


if __name__ == "__main__":
    unittest.main()
