import logging
import os

import requests

from scrapers.base import BaseScraper
from models import Listing

logger = logging.getLogger(__name__)

# Google Custom Search JSON API
CSE_URL = "https://www.googleapis.com/customsearch/v1"

# Queries — no site: operators needed since CSE is scoped to target sites
DEFAULT_QUERIES = [
    '"olson 911se"',
    '"olson 911 se"',
    '"olson 911se" sailboat',
    '"ericson olson 911"',
    'olson 911 sailboat for sale',
]


class GoogleCSEScraper(BaseScraper):
    source_name = "google_cse"

    def __init__(self, config: dict, rate_limit: float = 2.0):
        super().__init__(config, rate_limit)
        self.api_key = config.get("api_key") or os.environ.get("GOOGLE_CSE_API_KEY", "")
        self.cx = config.get("cx") or os.environ.get("GOOGLE_CSE_CX", "")
        self.queries = config.get("queries", DEFAULT_QUERIES)

    def search(self) -> list[Listing]:
        if not self.api_key or not self.cx:
            logger.warning(f"[{self.source_name}] Missing API key or CX — skipping. "
                           "Set GOOGLE_CSE_API_KEY and GOOGLE_CSE_CX env vars or config values.")
            return []

        listings = []
        seen_urls = set()

        for query in self.queries:
            try:
                results = self._run_query(query)
                for listing in results:
                    if listing.url not in seen_urls:
                        seen_urls.add(listing.url)
                        listings.append(listing)
            except Exception as e:
                logger.warning(f"[{self.source_name}] Query failed for '{query}': {e}")

        logger.info(f"[{self.source_name}] Found {len(listings)} Olson 911 listings across {len(self.queries)} queries")
        return listings

    def _run_query(self, query: str) -> list[Listing]:
        params = {
            "key": self.api_key,
            "cx": self.cx,
            "q": query,
            "num": 10,
            "sort": "date",  # prefer recent results
        }

        resp = requests.get(CSE_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        listings = []
        for item in data.get("items", []):
            title = item.get("title", "")
            url = item.get("link", "")
            snippet = item.get("snippet", "")

            if not self.matches_olson_911(title + " " + snippet):
                continue

            # Use URL as listing ID since it's unique across all sources
            listing_id = url

            listings.append(Listing(
                source=self.source_name,
                listing_id=listing_id,
                title=title,
                url=url,
                description=snippet[:200] if snippet else None,
            ))

        return listings
