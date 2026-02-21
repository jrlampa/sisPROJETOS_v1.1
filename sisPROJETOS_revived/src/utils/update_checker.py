import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.error import URLError
from urllib.request import Request, urlopen

from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class UpdateInfo:
    available: bool
    latest_version: str | None = None
    release_url: str | None = None
    published_at: str | None = None
    reason: str | None = None


class UpdateChecker:
    def __init__(self, current_version: str, owner: str = "jrlampa", repo: str = "sisPROJETOS_v1.1"):
        self.current_version = current_version
        self.owner = owner
        self.repo = repo

    def should_check_now(self, last_checked: str, interval_days: int = 1) -> bool:
        if not last_checked:
            return True

        try:
            last = datetime.fromisoformat(last_checked)
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
        except ValueError:
            return True

        return datetime.now(timezone.utc) - last >= timedelta(days=max(interval_days, 1))

    def check_for_updates(self, channel: str = "stable", timeout_seconds: int = 6) -> UpdateInfo:
        try:
            payload = self._fetch_release_data(channel=channel, timeout_seconds=timeout_seconds)
            if payload is None:
                return UpdateInfo(available=False, reason="No release data")

            latest_version = self._extract_version(payload.get("tag_name", ""))
            if not latest_version:
                return UpdateInfo(available=False, reason="Invalid release tag")

            if self._is_newer(latest_version, self.current_version):
                return UpdateInfo(
                    available=True,
                    latest_version=latest_version,
                    release_url=payload.get("html_url"),
                    published_at=payload.get("published_at"),
                )

            return UpdateInfo(available=False, latest_version=latest_version, reason="Already up to date")
        except URLError as exc:
            logger.warning(f"Update check failed due to network error: {exc}")
            return UpdateInfo(available=False, reason="Network error")
        except Exception as exc:
            logger.exception(f"Unexpected update check error: {exc}")
            return UpdateInfo(available=False, reason="Unexpected error")

    def _fetch_release_data(self, channel: str, timeout_seconds: int):
        if channel == "beta":
            endpoint = f"https://api.github.com/repos/{self.owner}/{self.repo}/releases"
        else:
            endpoint = f"https://api.github.com/repos/{self.owner}/{self.repo}/releases/latest"

        custom_endpoint = os.getenv("SISPROJETOS_UPDATE_ENDPOINT")
        if custom_endpoint:
            endpoint = custom_endpoint

        req_headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "sisPROJETOS-update-checker",
        }

        logger.info(f"Checking updates from endpoint: {endpoint}")
        request = Request(endpoint, headers=req_headers)

        with urlopen(request, timeout=timeout_seconds) as response:
            data = json.loads(response.read().decode("utf-8"))

        if isinstance(data, list):
            if not data:
                return None
            return data[0]

        return data

    @staticmethod
    def _extract_version(tag: str) -> str:
        if not tag:
            return ""
        return tag.lstrip("vV").strip()

    @staticmethod
    def _version_tuple(version: str):
        base = version.split("-")[0]
        chunks = re.findall(r"\d+", base)
        if not chunks:
            return (0,)
        return tuple(int(chunk) for chunk in chunks)

    def _is_newer(self, latest: str, current: str) -> bool:
        latest_tuple = self._version_tuple(latest)
        current_tuple = self._version_tuple(self._extract_version(current))
        max_len = max(len(latest_tuple), len(current_tuple))
        latest_tuple += (0,) * (max_len - len(latest_tuple))
        current_tuple += (0,) * (max_len - len(current_tuple))
        return latest_tuple > current_tuple
