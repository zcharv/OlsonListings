import logging
import re
import time
from abc import ABC, abstractmethod

import requests
from bs4 import BeautifulSoup

from models import Listing

logger = logging.getLogger(__name__)

# Default filter pattern — matches any boat in the configured boats list
_boat_patterns: list[re.Pattern] = []


def set_boat_patterns(boats: list[dict]) -> None:
    """Compile regex patterns from the boats config list."""
    global _boat_patterns
    _boat_patterns = []
    for boat in boats:
        pattern = boat.get("filter_pattern", "")
        if pattern:
            _boat_patterns.append(re.compile(pattern, re.IGNORECASE))


def matches_any_boat(text: str) -> bool:
    """Check if text matches any configured boat pattern."""
    return any(p.search(text) for p in _boat_patterns)


USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15",
]


class BaseScraper(ABC):
    def __init__(self, config: dict, rate_limit: float = 2.0):
        self.config = config
        self.rate_limit = rate_limit
        self._last_request = 0.0
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENTS[0],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })

    @property
    @abstractmethod
    def source_name(self) -> str: ...

    @abstractmethod
    def search(self) -> list[Listing]: ...

    def _get(self, url: str, **kwargs) -> requests.Response:
        elapsed = time.time() - self._last_request
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self._last_request = time.time()
        logger.debug(f"[{self.source_name}] GET {url}")
        resp = self.session.get(url, timeout=30, **kwargs)
        resp.raise_for_status()
        return resp

    def _soup(self, url: str, **kwargs) -> BeautifulSoup:
        resp = self._get(url, **kwargs)
        return BeautifulSoup(resp.text, "lxml")

    @staticmethod
    def matches_olson_911(text: str) -> bool:
        """Check if text matches any configured boat. Name kept for compatibility."""
        return matches_any_boat(text)
