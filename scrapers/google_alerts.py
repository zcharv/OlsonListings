import logging

import feedparser

from scrapers.base import BaseScraper
from models import Listing

logger = logging.getLogger(__name__)


class GoogleAlertsScraper(BaseScraper):
    source_name = "google_alerts"

    def __init__(self, config: dict, rate_limit: float = 2.0):
        super().__init__(config, rate_limit)
        self.feeds = config.get("feeds", [])

    def search(self) -> list[Listing]:
        if not self.feeds:
            logger.info(f"[{self.source_name}] No RSS feed URLs configured — skipping. "
                        "Set up Google Alerts at google.com/alerts with RSS delivery.")
            return []

        listings = []
        seen_urls = set()

        for feed_url in self.feeds:
            try:
                results = self._parse_feed(feed_url)
                for listing in results:
                    if listing.url not in seen_urls:
                        seen_urls.add(listing.url)
                        listings.append(listing)
            except Exception as e:
                logger.warning(f"[{self.source_name}] Failed to parse feed: {e}")

        logger.info(f"[{self.source_name}] Found {len(listings)} Olson 911 listings "
                     f"from {len(self.feeds)} feeds")
        return listings

    def _parse_feed(self, feed_url: str) -> list[Listing]:
        feed = feedparser.parse(feed_url)
        listings = []

        for entry in feed.entries:
            title = entry.get("title", "")
            link = entry.get("link", "")

            # Google Alerts wraps links in a redirect — extract actual URL
            if "google.com/url" in link:
                from urllib.parse import parse_qs, urlparse
                parsed = urlparse(link)
                params = parse_qs(parsed.query)
                link = params.get("url", [link])[0]

            # Strip HTML tags from title (Google Alerts sometimes includes <b> tags)
            from bs4 import BeautifulSoup
            clean_title = BeautifulSoup(title, "lxml").get_text(strip=True)

            summary = entry.get("summary", "")
            clean_summary = BeautifulSoup(summary, "lxml").get_text(strip=True)

            if not self.matches_olson_911(clean_title + " " + clean_summary):
                continue

            published = entry.get("published", "")

            listings.append(Listing(
                source=self.source_name,
                listing_id=link,
                title=clean_title,
                url=link,
                description=clean_summary[:200] if clean_summary else None,
                date_found=published or None,
            ))

        return listings
