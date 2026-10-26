#!/usr/bin/env python3
"""Unit tests for IndexNow submit behaviour (no live POSTs)."""
from __future__ import annotations

import io
import unittest
import urllib.error
from unittest.mock import patch

import indexnow_ping as ping


class FakeResponse:
    def __init__(self, code: int, body: bytes):
        self._code = code
        self._body = body

    def getcode(self) -> int:
        return self._code

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *args) -> bool:
        return False


def http_error(code: int, body: bytes, url: str = "https://example.test/indexnow"):
    return urllib.error.HTTPError(url, code, "error", None, io.BytesIO(body))


class FileToUrlTests(unittest.TestCase):
    def test_index_and_use_case(self) -> None:
        self.assertEqual(ping.file_to_url("index.html"), "https://gemmisi.com/")
        self.assertEqual(
            ping.file_to_url("use-cases/pricing-pages/index.html"),
            "https://gemmisi.com/use-cases/pricing-pages/",
        )
        self.assertIsNone(ping.file_to_url("scripts/indexnow_ping.py"))
        self.assertIsNone(ping.file_to_url("23c3690d323f2e5687c21ef152e1cd87.txt"))
        self.assertIsNone(ping.file_to_url(f"{ping.ACTIVE_KEY}.txt"))
        self.assertIsNone(ping.file_to_url("fb1101/index.html"))
        self.assertIsNone(ping.file_to_url("wa/index.html"))
        self.assertIsNone(ping.file_to_url("li1025/index.html"))
        self.assertIsNone(ping.file_to_url("fb1026b/index.html"))
        self.assertIsNone(ping.file_to_url("li1026b/index.html"))


class DiscoverKeyTests(unittest.TestCase):
    def test_repo_key_matches_filename(self) -> None:
        key, path = ping.discover_key()
        self.assertEqual(key, ping.ACTIVE_KEY)
        self.assertEqual(path.name, f"{ping.ACTIVE_KEY}.txt")
        self.assertEqual(key, path.stem)
        self.assertNotEqual(key, "23c3690d323f2e5687c21ef152e1cd87")
        self.assertTrue((ping.ROOT / "23c3690d323f2e5687c21ef152e1cd87.txt").is_file())


class LiveKeyTests(unittest.TestCase):
    def test_waits_until_body_matches(self) -> None:
        sleeps: list[float] = []
        responses = [
            http_error(404, b"Not Found", "https://gemmisi.com/key.txt"),
            FakeResponse(200, b"wrong-key\n"),
            FakeResponse(200, b"expected-key\n"),
        ]

        def urlopen(_request, timeout=30):
            item = responses.pop(0)
            if isinstance(item, Exception):
                raise item
            return item

        with patch("urllib.request.urlopen", side_effect=urlopen):
            ping.wait_for_live_key(
                "expected-key",
                "https://gemmisi.com/key.txt",
                delays=(1, 2),
                sleep=sleeps.append,
            )
        self.assertEqual(sleeps, [1, 2])

    def test_gives_up_when_never_live(self) -> None:
        with patch(
            "urllib.request.urlopen",
            side_effect=lambda *_a, **_k: FakeResponse(404, b"missing"),
        ):
            with self.assertRaises(SystemExit) as ctx:
                ping.wait_for_live_key(
                    "expected-key",
                    "https://gemmisi.com/key.txt",
                    delays=(1,),
                    sleep=lambda _s: None,
                )
        self.assertIn("did not return the expected key", str(ctx.exception))


class SubmitTests(unittest.TestCase):
    payload = {
        "host": "gemmisi.com",
        "key": "abc",
        "keyLocation": "https://gemmisi.com/abc.txt",
        "urlList": ["https://gemmisi.com/"],
    }
    engines = (
        ("bing", "https://www.bing.com/indexnow"),
        ("seznam", "https://search.seznam.cz/indexnow"),
        ("naver", "https://searchadvisor.naver.com/indexnow"),
    )

    def test_partial_403_warns_but_succeeds(self) -> None:
        calls: list[str] = []

        def urlopen(request, timeout=30):
            calls.append(request.full_url)
            if "bing.com" in request.full_url:
                raise http_error(
                    403,
                    b'{"errorCode":"UserForbiddedToAccessSite"}',
                    request.full_url,
                )
            return FakeResponse(200, b"")

        sleeps: list[float] = []
        with patch("urllib.request.urlopen", side_effect=urlopen):
            accepted, rejected = ping.submit_to_engines(
                self.payload,
                engines=self.engines,
                retry_delays=(5, 15),
                sleep=sleeps.append,
            )
        names = [name for name, _status in accepted]
        self.assertEqual(names, ["seznam", "naver"])
        self.assertEqual(len(rejected), 1)
        self.assertEqual(rejected[0][:2], ("bing", 403))
        self.assertIn("UserForbiddedToAccessSite", rejected[0][2])
        self.assertEqual(sleeps, [5, 15])
        self.assertEqual(calls.count("https://www.bing.com/indexnow"), 3)

    def test_all_403_is_total_rejection(self) -> None:
        def urlopen(request, timeout=30):
            raise http_error(
                403,
                b'{"errorCode":"UserForbiddedToAccessSite"}',
                request.full_url,
            )

        with patch("urllib.request.urlopen", side_effect=urlopen):
            accepted, rejected = ping.submit_to_engines(
                self.payload,
                engines=self.engines,
                retry_delays=(1,),
                sleep=lambda _s: None,
            )
        self.assertEqual(accepted, [])
        self.assertEqual(
            [name for name, _status, _detail in rejected],
            ["bing", "seznam", "naver"],
        )

    def test_403_then_202_counts_as_accepted(self) -> None:
        hits = {"n": 0}

        def urlopen(request, timeout=30):
            hits["n"] += 1
            if hits["n"] == 1:
                raise http_error(
                    403,
                    b'{"errorCode":"UserForbiddedToAccessSite"}',
                    request.full_url,
                )
            return FakeResponse(202, b"")

        with patch("urllib.request.urlopen", side_effect=urlopen):
            accepted, rejected = ping.submit_to_engines(
                self.payload,
                engines=(("bing", "https://www.bing.com/indexnow"),),
                retry_delays=(1,),
                sleep=lambda _s: None,
            )
        self.assertEqual(accepted, [("bing", 202)])
        self.assertEqual(rejected, [])


class SummarizeBodyTests(unittest.TestCase):
    def test_error_code_and_message(self) -> None:
        self.assertEqual(
            ping.summarize_body(
                '{"errorCode":"UserForbiddedToAccessSite","message":"User is unauthorized"}'
            ),
            "UserForbiddedToAccessSite — User is unauthorized",
        )


if __name__ == "__main__":
    unittest.main()
