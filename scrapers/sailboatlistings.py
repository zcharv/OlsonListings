import logging
import re

from scrapers.base import BaseScraper
from models import Listing

logger = logging.getLogger(__name__)

BASE_URL = "https://www.sailboatlistings.com/sailboats/Olson"


class SailboatListingsScraper(BaseScraper):
    source_name = "sailboatlistings"

    def search(self) -> list[Listing]:
        listings = []
        try:
            soup = self._soup(BASE_URL)
        except Exception as e:
            logger.error(f"[{self.source_name}] Failed to fetch: {e}")
            return []

        for link in soup.select("a.sailheader"):
            title = link.get_text(strip=True)
            href = link.get("href", "")

            # Exclude Nicholson boats that match "olson" substring
            if "nicholson" in title.lower():
                continue

            if not self.matches_olson_911(title):
                continue

            listing_id = href.rstrip("/").split("/")[-1]

            # Extract specs from the parent table
            price = None
            location = None
            description = None

            # Walk up to the containing table to find spec rows
            table = link.find_parent("table")
            if table:
                for spec_label in table.select("span.sailvb"):
                    label_text = spec_label.get_text(strip=True).lower()
                    value_span = spec_label.find_parent("td")
                    if value_span:
                        value_el = value_span.find_next_sibling("td")
                        if value_el:
                            val = value_el.get_text(strip=True)
                            if "asking" in label_text:
                                price = val
                            elif "location" in label_text:
                                location = val

            listings.append(Listing(
                source=self.source_name,
                listing_id=listing_id,
                title=title,
                url=href if href.startswith("http") else f"https://www.sailboatlistings.com{href}",
                price=price,
                location=location,
                description=description,
            ))

        logger.info(f"[{self.source_name}] Found {len(listings)} Olson 911 listings")
        return listings
