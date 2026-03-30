import logging
import re

from scrapers.base import BaseScraper
from models import Listing

logger = logging.getLogger(__name__)

# Sailing Texas has a simple index of sailboats
# Try multiple known URL patterns
URLS = [
    "https://www.sailingtexas.com/sailb.html",
    "https://www.sailingtexas.com/sail2.html",
    "https://www.sailingtexas.com/",
]


class SailingTexasScraper(BaseScraper):
    source_name = "sailing_texas"

    def search(self) -> list[Listing]:
        listings = []
        seen_ids = set()

        for page_url in URLS:
            try:
                soup = self._soup(page_url)
            except Exception as e:
                logger.debug(f"[{self.source_name}] Failed to fetch {page_url}: {e}")
                continue
            self._extract_from_page(soup, listings, seen_ids)

        logger.info(f"[{self.source_name}] Found {len(listings)} Olson 911 listings")
        return listings

    def _extract_from_page(self, soup, listings, seen_ids):
        for link in soup.find_all("a", href=True):
            text = link.get_text(strip=True)
            href = link["href"]

            if not self.matches_olson_911(text):
                continue

            if not href.startswith("http"):
                href = f"https://www.sailingtexas.com/{href.lstrip('/')}"

            listing_id = href.rstrip("/").split("/")[-1].replace(".html", "")

            if listing_id in seen_ids:
                continue
            seen_ids.add(listing_id)

            # Try to extract price from link text
            price_match = re.search(r'\$[\d,]+', text)
            price = price_match.group(0) if price_match else None

            listings.append(Listing(
                source=self.source_name,
                listing_id=listing_id,
                title=text,
                url=href,
                price=price,
            ))
