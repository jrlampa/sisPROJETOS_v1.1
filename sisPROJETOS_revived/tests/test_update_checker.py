from datetime import datetime, timedelta, timezone

from src.utils.update_checker import UpdateChecker


class TestUpdateChecker:
    def test_should_check_now_when_never_checked(self):
        checker = UpdateChecker(current_version="2.0.1")
        assert checker.should_check_now(last_checked="", interval_days=1)

    def test_should_check_now_false_inside_interval(self):
        checker = UpdateChecker(current_version="2.0.1")
        last_checked = (datetime.now(timezone.utc) - timedelta(hours=6)).isoformat()
        assert not checker.should_check_now(last_checked=last_checked, interval_days=1)

    def test_extract_version(self):
        checker = UpdateChecker(current_version="2.0.1")
        assert checker._extract_version("v2.1.0") == "2.1.0"

    def test_is_newer(self):
        checker = UpdateChecker(current_version="2.0.1")
        assert checker._is_newer("2.1.0", "2.0.1")
        assert not checker._is_newer("2.0.1", "2.0.1")
        assert not checker._is_newer("1.9.9", "2.0.1")

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
