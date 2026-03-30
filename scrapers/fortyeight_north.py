import logging

from scrapers.base import BaseScraper
from models import Listing

logger = logging.getLogger(__name__)

BASE_URL = "https://48north.com/classifieds/"
SEARCH_URL = "https://48north.com/classifieds/?filter[field_keyword]={query}&num=50"


class FortyEightNorthScraper(BaseScraper):
    source_name = "fortyeight_north"

    def search(self) -> list[Listing]:
        listings = []
        queries = ["olson", "olson 911", "ericson"]
        seen_urls = set()

        for query in queries:
            try:
                url = SEARCH_URL.format(query=query.replace(" ", "+"))
                soup = self._soup(url)
            except Exception as e:
                logger.warning(f"[{self.source_name}] Search failed for '{query}': {e}")
                continue

            for card in soup.select("div.drts-display--summary"):
                title_el = card.select_one("a.drts-entity-permalink")
                if not title_el:
                    continue

                title = title_el.get_text(strip=True)
                href = title_el.get("href", "")

                if href in seen_urls:
                    continue
                seen_urls.add(href)

                if not self.matches_olson_911(title):
                    continue

                price_el = card.select_one("[data-name='entity_field_field_price']")
                price = price_el.get_text(strip=True) if price_el else None

                desc_el = card.select_one("[data-name='entity_field_post_content']")
                description = desc_el.get_text(strip=True)[:200] if desc_el else None

                listing_id = card.get("data-entity-id", href.rstrip("/").split("/")[-1])

                listings.append(Listing(
                    source=self.source_name,
                    listing_id=str(listing_id),
                    title=title,
                    url=href,
                    price=price,
                    description=description,
                ))

        logger.info(f"[{self.source_name}] Found {len(listings)} Olson 911 listings")
        return listings
