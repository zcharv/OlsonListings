import logging

from scrapers.base import BaseScraper
from models import Listing

logger = logging.getLogger(__name__)

DEFAULT_INSTANCES = [
    "https://search.indst.eu",
    "https://metacat.online",
    "https://search.federicociro.com",
]

DEFAULT_QUERIES = [
    "olson 911se sailboat",
    "olson 911 se sailboat for sale",
    "olson 911se for sale",
]


class SearXNGScraper(BaseScraper):
    source_name = "searxng"

    def __init__(self, config: dict, rate_limit: float = 5.0):
        super().__init__(config, rate_limit)
        self.instances = config.get("instances", DEFAULT_INSTANCES)
        self.queries = config.get("queries", DEFAULT_QUERIES)

    def search(self) -> list[Listing]:
        listings = []
        seen_urls = set()

        for query in self.queries:
            results = self._search_query(query)
            for listing in results:
                if listing.url not in seen_urls:
                    seen_urls.add(listing.url)
                    listings.append(listing)

        logger.info(f"[{self.source_name}] Found {len(listings)} Olson 911 listings")
        return listings

    def _search_query(self, query: str) -> list[Listing]:
        for instance in self.instances:
            # Try JSON API first
            try:
                results = self._try_json(instance, query)
                if results is not None:
                    return results
            except Exception as e:
                logger.debug(f"[{self.source_name}] JSON failed at {instance}: {e}")

            # Fall back to HTML parsing
            try:
                results = self._try_html(instance, query)
                if results is not None:
                    return results
            except Exception as e:
                logger.debug(f"[{self.source_name}] HTML failed at {instance}: {e}")

        logger.warning(f"[{self.source_name}] All instances failed for '{query}'")
        return []

    def _try_json(self, instance: str, query: str) -> list[Listing] | None:
        url = f"{instance}/search"
        params = {"q": query, "format": "json", "categories": "general"}
        resp = self._get(url, params=params)

        if resp.status_code == 403:
            return None

        data = resp.json()
        results = data.get("results", [])
        if not results:
            return []

        listings = []
        for r in results:
            title = r.get("title", "")
            href = r.get("url", "")
            content = r.get("content", "")

            if not self.matches_olson_911(title + " " + content):
                continue

            listings.append(Listing(
                source=self.source_name,
                listing_id=href,
                title=title,
                url=href,
                description=content[:200] if content else None,
            ))

        logger.info(f"[{self.source_name}] {instance}: {len(listings)} matches for '{query}'")
        return listings

    def _try_html(self, instance: str, query: str) -> list[Listing] | None:
        from bs4 import BeautifulSoup

        url = f"{instance}/search"
        params = {"q": query, "categories": "general"}
        resp = self._get(url, params=params)

        if resp.status_code == 403:
            return None

        soup = BeautifulSoup(resp.text, "lxml")

        listings = []
        # SearXNG uses article.result or div.result
        for result in soup.select("article.result, div.result"):
            link_el = result.select_one("h3 a, h4 a, a.url_header")
            if not link_el:
                continue

            title = link_el.get_text(strip=True)
            href = link_el.get("href", "")

            if not href.startswith("http"):
                continue

            snippet_el = result.select_one("p.content, p.result-content, .result_content")
            snippet = snippet_el.get_text(strip=True) if snippet_el else ""

            if not self.matches_olson_911(title + " " + snippet):
                continue

            listings.append(Listing(
                source=self.source_name,
                listing_id=href,
                title=title,
                url=href,
                description=snippet[:200] if snippet else None,
            ))

        logger.info(f"[{self.source_name}] {instance} (HTML): {len(listings)} matches for '{query}'")
        return listings
