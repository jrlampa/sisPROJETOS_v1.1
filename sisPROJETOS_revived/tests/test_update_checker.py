import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
from urllib.error import URLError

import pytest

from src.utils.update_checker import UpdateChecker


class TestUpdateChecker:
    def test_should_check_now_when_never_checked(self):
        checker = UpdateChecker(current_version="2.0.1")
        assert checker.should_check_now(last_checked="", interval_days=1)

    def test_should_check_now_false_inside_interval(self):
        checker = UpdateChecker(current_version="2.0.1")
        last_checked = (datetime.now(timezone.utc) - timedelta(hours=6)).isoformat()
        assert not checker.should_check_now(last_checked=last_checked, interval_days=1)

    def test_should_check_now_past_interval(self):
        checker = UpdateChecker(current_version="2.0.1")
        last_checked = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        assert checker.should_check_now(last_checked=last_checked, interval_days=1)

    def test_should_check_now_invalid_date_returns_true(self):
        checker = UpdateChecker(current_version="2.0.1")
        assert checker.should_check_now(last_checked="not-a-date", interval_days=1)

    def test_should_check_now_naive_datetime(self):
        checker = UpdateChecker(current_version="2.0.1")
        # Naive datetime (no timezone) — should still work via tzinfo injection
        last_checked = (datetime.now() - timedelta(hours=1)).isoformat()
        assert not checker.should_check_now(last_checked=last_checked, interval_days=1)

    def test_should_check_now_interval_minimum_is_one_day(self):
        checker = UpdateChecker(current_version="2.0.1")
        last_checked = (datetime.now(timezone.utc) - timedelta(hours=12)).isoformat()
        # interval_days=0 should be treated as 1
        assert not checker.should_check_now(last_checked=last_checked, interval_days=0)

    def test_extract_version(self):
        checker = UpdateChecker(current_version="2.0.1")
        assert checker._extract_version("v2.1.0") == "2.1.0"

    def test_extract_version_uppercase_v(self):
        checker = UpdateChecker(current_version="2.0.1")
        assert checker._extract_version("V2.1.0") == "2.1.0"

    def test_extract_version_empty(self):
        checker = UpdateChecker(current_version="2.0.1")
        assert checker._extract_version("") == ""

    def test_is_newer(self):
        checker = UpdateChecker(current_version="2.0.1")
        assert checker._is_newer("2.1.0", "2.0.1")
        assert not checker._is_newer("2.0.1", "2.0.1")
        assert not checker._is_newer("1.9.9", "2.0.1")

    def test_is_newer_patch_version(self):
        checker = UpdateChecker(current_version="2.0.1")
        assert checker._is_newer("2.0.2", "2.0.1")
        assert not checker._is_newer("2.0.0", "2.0.1")

    def test_version_tuple_no_digits(self):
        checker = UpdateChecker(current_version="2.0.1")
        assert checker._version_tuple("no-digits") == (0,)

    def test_version_tuple_with_prerelease(self):
        checker = UpdateChecker(current_version="2.0.1")
        # Pre-release suffix should be stripped
        result = checker._version_tuple("2.1.0-beta")
        assert result == (2, 1, 0)

    def test_check_for_updates_available(self, monkeypatch):
        checker = UpdateChecker(current_version="2.0.1")
        monkeypatch.setattr(
            checker,
            "_fetch_release_data",
            lambda channel, timeout_seconds: {
                "tag_name": "v2.1.0",
                "html_url": "https://github.com/jrlampa/sisPROJETOS_v1.1/releases/tag/v2.1.0",
                "published_at": "2026-02-17T00:00:00Z",
            },
        )

        result = checker.check_for_updates(channel="stable")

        assert result.available
        assert result.latest_version == "2.1.0"
        assert result.release_url is not None

    def test_check_for_updates_not_available(self, monkeypatch):
        checker = UpdateChecker(current_version="2.1.0")
        monkeypatch.setattr(
            checker,
            "_fetch_release_data",
            lambda channel, timeout_seconds: {
                "tag_name": "v2.1.0",
                "html_url": "https://github.com/jrlampa/sisPROJETOS_v1.1/releases/tag/v2.1.0",
                "published_at": "2026-02-17T00:00:00Z",
            },
        )

        result = checker.check_for_updates(channel="stable")

        assert not result.available
        assert result.latest_version == "2.1.0"

    def test_check_for_updates_returns_none_release(self, monkeypatch):
        checker = UpdateChecker(current_version="2.0.1")
        monkeypatch.setattr(checker, "_fetch_release_data", lambda channel, timeout_seconds: None)
        result = checker.check_for_updates()
        assert not result.available
        assert result.reason == "No release data"

    def test_check_for_updates_invalid_tag(self, monkeypatch):
        checker = UpdateChecker(current_version="2.0.1")
        monkeypatch.setattr(
            checker,
            "_fetch_release_data",
            lambda channel, timeout_seconds: {"tag_name": "", "html_url": ""},
        )
        result = checker.check_for_updates()
        assert not result.available
        assert result.reason == "Invalid release tag"

    def test_check_for_updates_url_error(self, monkeypatch):
        checker = UpdateChecker(current_version="2.0.1")

        def raise_url_error(channel, timeout_seconds):
            raise URLError("Connection refused")

        monkeypatch.setattr(checker, "_fetch_release_data", raise_url_error)
        result = checker.check_for_updates()
        assert not result.available
        assert result.reason == "Network error"

    def test_check_for_updates_unexpected_error(self, monkeypatch):
        checker = UpdateChecker(current_version="2.0.1")

        def raise_generic(channel, timeout_seconds):
            raise RuntimeError("Something went wrong")

        monkeypatch.setattr(checker, "_fetch_release_data", raise_generic)
        result = checker.check_for_updates()
        assert not result.available
        assert result.reason == "Unexpected error"

    def test_fetch_release_data_beta_channel(self, monkeypatch):
        """Beta channel fetches list endpoint and returns first item."""
        checker = UpdateChecker(current_version="2.0.1")

        release_list = [
            {"tag_name": "v2.2.0-beta", "html_url": "https://github.com/.../v2.2.0-beta"},
            {"tag_name": "v2.1.0", "html_url": "https://github.com/.../v2.1.0"},
        ]

        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.read.return_value = json.dumps(release_list).encode("utf-8")

        with patch("src.utils.update_checker.urlopen", return_value=mock_response):
            data = checker._fetch_release_data(channel="beta", timeout_seconds=5)

        assert data["tag_name"] == "v2.2.0-beta"

    def test_fetch_release_data_beta_channel_empty_list(self, monkeypatch):
        """Beta channel with empty release list returns None."""
        checker = UpdateChecker(current_version="2.0.1")

        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.read.return_value = json.dumps([]).encode("utf-8")

        with patch("src.utils.update_checker.urlopen", return_value=mock_response):
            data = checker._fetch_release_data(channel="beta", timeout_seconds=5)

        assert data is None

    def test_fetch_release_data_stable_channel(self, monkeypatch):
        """Stable channel fetches /releases/latest and returns dict directly."""
        checker = UpdateChecker(current_version="2.0.1")

        release_data = {"tag_name": "v2.1.0", "html_url": "https://github.com/.../v2.1.0"}

        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.read.return_value = json.dumps(release_data).encode("utf-8")

        with patch("src.utils.update_checker.urlopen", return_value=mock_response):
            data = checker._fetch_release_data(channel="stable", timeout_seconds=5)

        assert data["tag_name"] == "v2.1.0"

    def test_fetch_release_data_custom_endpoint(self, monkeypatch):
        """Custom endpoint env var overrides default endpoint."""
        checker = UpdateChecker(current_version="2.0.1")

        release_data = {"tag_name": "v3.0.0", "html_url": "https://custom.example.com/v3.0.0"}

        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.read.return_value = json.dumps(release_data).encode("utf-8")

        monkeypatch.setenv("SISPROJETOS_UPDATE_ENDPOINT", "https://custom.example.com/releases/latest")

        with patch("src.utils.update_checker.urlopen", return_value=mock_response):
            data = checker._fetch_release_data(channel="stable", timeout_seconds=5)

        assert data["tag_name"] == "v3.0.0"
