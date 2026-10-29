#!/usr/bin/env python3
"""Unit tests for IndexNow submit behaviour (no live POSTs)."""
from __future__ import annotations

import io
import os
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
        self.assertIsNone(ping.file_to_url("fb1027b/index.html"))
        self.assertIsNone(ping.file_to_url("li1027b/index.html"))


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


SAMPLE_PAGE = """<!doctype html>
<html>
<head>
  <title>Hello</title>
  <meta name="description" content="A page" />
  <link rel="canonical" href="https://gemmisi.com/hello/" />
  <meta name="robots" content="index, follow" />
  <link rel="stylesheet" href="styles.css?v=old" />
</head>
<body>
  <header class="nav">Shared nav</header>
  <main>
    <h1>Hello</h1>
    <p>Body copy.</p>
    <p class="uc-all"><a href="../index.html">See all 160 use cases →</a></p>
  </main>
  <footer>LinkedIn · Facebook</footer>
  <script>alert(1)</script>
</body>
</html>
"""


class PageContentFingerprintTests(unittest.TestCase):
    def test_ignores_shared_chrome_and_see_all_count(self) -> None:
        chrome = SAMPLE_PAGE.replace("Shared nav", "New nav")
        chrome = chrome.replace("LinkedIn · Facebook", "LinkedIn · Facebook Page")
        chrome = chrome.replace("styles.css?v=old", "styles.css?v=new")
        chrome = chrome.replace("See all 160 use cases", "See all 203 use cases")
        chrome = chrome.replace("<script>alert(1)</script>", "<script>alert(2)</script>")
        self.assertEqual(
            ping.page_content_fingerprint(SAMPLE_PAGE),
            ping.page_content_fingerprint(chrome),
        )

    def test_detects_title_and_main_changes(self) -> None:
        titled = SAMPLE_PAGE.replace("<title>Hello</title>", "<title>Hello there</title>")
        body = SAMPLE_PAGE.replace("Body copy.", "Updated copy.")
        self.assertNotEqual(
            ping.page_content_fingerprint(SAMPLE_PAGE),
            ping.page_content_fingerprint(titled),
        )
        self.assertNotEqual(
            ping.page_content_fingerprint(SAMPLE_PAGE),
            ping.page_content_fingerprint(body),
        )

    def test_reads_meta_with_content_first(self) -> None:
        html = SAMPLE_PAGE.replace(
            '<meta name="description" content="A page" />',
            '<meta content="A page" name="description" />',
        )
        self.assertEqual(
            ping.page_content_fingerprint(SAMPLE_PAGE),
            ping.page_content_fingerprint(html),
        )


class GitChangedFilesTests(unittest.TestCase):
    def test_failed_range_does_not_fall_back_to_head(self) -> None:
        calls: list[tuple[str, ...]] = []

        def fake_git(*args: str):
            calls.append(args)

            class Result:
                returncode = 1
                stdout = "index.html\n"
                stderr = "bad revision"

            return Result()

        with patch.object(ping, "_git", side_effect=fake_git):
            self.assertEqual(ping.git_changed_files("abc", "def"), [])
        self.assertEqual(calls, [("diff", "--name-only", "--diff-filter=ACDMRT", "abc", "def")])
        self.assertTrue(all("HEAD~1" not in arg for call in calls for arg in call))

    def test_zero_sha_is_empty(self) -> None:
        self.assertEqual(ping.git_changed_files(ping.ZERO_SHA, "HEAD"), [])
        self.assertEqual(ping.git_changed_files("", "HEAD"), [])


class UrlsFromPageChangesTests(unittest.TestCase):
    def test_added_deleted_and_chrome_only(self) -> None:
        files = [
            "index.html",
            "use-cases/inbox-triage/index.html",
            "use-cases/new-slug/index.html",
            "gone/index.html",
            "fb1101/index.html",
            "scripts/indexnow_ping.py",
        ]
        blobs = {
            ("old", "index.html"): SAMPLE_PAGE,
            ("new", "index.html"): SAMPLE_PAGE.replace("LinkedIn · Facebook", "Facebook Page"),
            ("old", "use-cases/inbox-triage/index.html"): SAMPLE_PAGE,
            ("new", "use-cases/inbox-triage/index.html"): SAMPLE_PAGE.replace(
                "Body copy.", "Inbox triage body."
            ),
            ("new", "use-cases/new-slug/index.html"): SAMPLE_PAGE,
            ("old", "gone/index.html"): SAMPLE_PAGE,
        }

        def fake_file(sha: str, rel: str) -> str | None:
            return blobs.get((sha, rel))

        with patch.object(ping, "git_file_at", side_effect=fake_file):
            urls = ping.urls_from_page_changes(files, "old", "new")
        self.assertEqual(
            urls,
            [
                "https://gemmisi.com/use-cases/inbox-triage/",
                "https://gemmisi.com/use-cases/new-slug/",
                "https://gemmisi.com/gone/",
            ],
        )
        self.assertNotIn("https://gemmisi.com/", urls)


class ResolveUrlsTests(unittest.TestCase):
    def test_all_is_only_sitemap_path(self) -> None:
        urls, source = ping.resolve_urls(True)
        self.assertEqual(source, "sitemap")
        self.assertGreater(len(urls), 50)
        self.assertTrue(all(item.startswith("https://gemmisi.com/") for item in urls))
        self.assertEqual(len(urls), len(set(urls)))

    def test_missing_before_does_not_use_sitemap(self) -> None:
        with patch.object(ping, "resolve_diff_range", return_value=("", "HEAD")):
            urls, source = ping.resolve_urls(False)
        self.assertEqual(urls, [])
        self.assertEqual(source, "no diff")

    def test_no_mapped_files_does_not_use_sitemap(self) -> None:
        with (
            patch.object(ping, "resolve_diff_range", return_value=("aaa", "bbb")),
            patch.object(ping, "git_changed_files", return_value=["fb1101/index.html"]),
            patch.object(ping, "urls_from_page_changes", return_value=[]),
        ):
            urls, source = ping.resolve_urls(False)
        self.assertEqual(urls, [])
        self.assertEqual(source, "no content changes")

    def test_caps_automatic_submit_but_keeps_candidates(self) -> None:
        candidates = [f"https://gemmisi.com/p{i}/" for i in range(51)]
        with (
            patch.object(ping, "resolve_diff_range", return_value=("aaa", "bbb")),
            patch.object(ping, "git_changed_files", return_value=["index.html"]),
            patch.object(ping, "urls_from_page_changes", return_value=candidates),
        ):
            urls, source = ping.resolve_urls(False, cap=50)
        self.assertEqual(urls, candidates)
        self.assertEqual(source, "capped (51 > 50)")
        self.assertFalse(ping.should_submit(False, urls, source))

    def test_under_cap_submits_changed_pages(self) -> None:
        changed = ["https://gemmisi.com/"]
        with (
            patch.object(ping, "resolve_diff_range", return_value=("aaa", "bbb")),
            patch.object(ping, "git_changed_files", return_value=["index.html"]),
            patch.object(ping, "urls_from_page_changes", return_value=changed),
        ):
            urls, source = ping.resolve_urls(False)
        self.assertEqual(urls, changed)
        self.assertEqual(source, "changed page content")
        self.assertTrue(ping.should_submit(False, urls, source))

    def test_all_ignores_cap(self) -> None:
        sitemap = ping.sitemap_urls()
        self.assertGreater(len(sitemap), ping.AUTO_SUBMIT_CAP)
        urls, source = ping.resolve_urls(True, cap=1)
        self.assertEqual(source, "sitemap")
        self.assertEqual(urls, sitemap)
        self.assertTrue(ping.should_submit(True, urls, source))


class ShouldSubmitTests(unittest.TestCase):
    def test_empty_never_submits(self) -> None:
        self.assertFalse(ping.should_submit(True, [], "sitemap"))
        self.assertFalse(ping.should_submit(False, [], "no content changes"))


class ResolveDiffRangeTests(unittest.TestCase):
    def test_uses_after_first_parent_not_head(self) -> None:
        env = {
            "INDEXNOW_BEFORE": "",
            "INDEXNOW_AFTER": "deadbeef",
        }
        with patch.dict(os.environ, env, clear=False):
            with patch.object(ping, "first_parent", return_value="parentsha") as parent:
                before, after = ping.resolve_diff_range()
        self.assertEqual((before, after), ("parentsha", "deadbeef"))
        parent.assert_called_once_with("deadbeef")

    def test_explicit_before_wins(self) -> None:
        env = {"INDEXNOW_BEFORE": "aaa", "INDEXNOW_AFTER": "bbb"}
        with patch.dict(os.environ, env, clear=False):
            self.assertEqual(ping.resolve_diff_range(), ("aaa", "bbb"))


if __name__ == "__main__":
    unittest.main()

