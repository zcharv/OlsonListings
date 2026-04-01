import logging

from scrapers.base import BaseScraper
from models import Listing

logger = logging.getLogger(__name__)

DEFAULT_QUERIES = [
    "olson 911se sailboat",
    "olson 911 se sailboat for sale",
    "olson 911se for sale",
]

BACKENDS = ["duckduckgo", "bing", "google", "yahoo"]


class WebSearchScraper(BaseScraper):
    source_name = "web_search"

    def __init__(self, config: dict, rate_limit: float = 5.0):
        super().__init__(config, rate_limit)
        self.queries = config.get("queries", DEFAULT_QUERIES)
        self.backends = config.get("backends", BACKENDS)

    def search(self) -> list[Listing]:
        try:
            from ddgs import DDGS
        except ImportError:
            try:
                from duckduckgo_search import DDGS
            except ImportError:
                logger.error(f"[{self.source_name}] ddgs not installed. Run: pip install ddgs")
                return []

        listings = []
        seen_urls = set()

        for query in self.queries:
            results = self._search_query(DDGS, query)
            for listing in results:
                if listing.url not in seen_urls:
                    seen_urls.add(listing.url)
                    listings.append(listing)

        logger.info(f"[{self.source_name}] Found {len(listings)} Olson 911 listings "
                     f"across {len(self.queries)} queries")
        return listings

    def _search_query(self, DDGS, query: str) -> list[Listing]:
        for backend in self.backends:
            try:
                logger.debug(f"[{self.source_name}] Trying {backend} for: {query}")
                results = list(DDGS().text(query, backend=backend, max_results=15))

                if not results:
                    continue

                listings = []
                for r in results:
                    title = r.get("title", "")
                    href = r.get("href", "")
                    body = r.get("body", "")

                    if not self.matches_olson_911(title + " " + body):
                        continue

                    listings.append(Listing(
                        source=self.source_name,
                        listing_id=href,
                        title=title,
                        url=href,
                        description=body[:200] if body else None,
                    ))

                logger.info(f"[{self.source_name}] {backend}: {len(listings)} matches "
                            f"from {len(results)} results for '{query}'")
                return listings

            except Exception as e:
                logger.warning(f"[{self.source_name}] {backend} failed for '{query}': {e}")
                continue

        logger.warning(f"[{self.source_name}] All backends failed for '{query}'")
        return []
