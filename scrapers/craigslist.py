import json
import logging
import re

from scrapers.base import BaseScraper
from models import Listing

logger = logging.getLogger(__name__)

# Craigslist search API
SAPI_URL = "https://sapi.craigslist.org/web/v8/postings/search/full"

# Area IDs for Craigslist regions — discovered via API responses
# We search by constructing the HTML URL and parsing JSON-LD as a fallback,
# but prefer the SAPI when possible.

DEFAULT_REGIONS = [
    # PNW
    "seattle", "portland", "olympic", "skagit", "bellingham", "eugene",
    "corvallis", "kpr", "medford",
    # California
    "sfbay", "losangeles", "sandiego", "sacramento", "santacruz",
    "monterey", "humboldt",
    # East Coast
    "boston", "newyork", "longisland", "newjersey", "baltimore",
    "annapolis", "norfolk", "charleston", "savannah",
    # Southeast / Gulf
    "miami", "tampa", "jacksonville", "neworleans",
    # Great Lakes
    "chicago", "detroit", "milwaukee", "cleveland",
    # Other
    "honolulu", "maine", "newlondon", "rhodeisland", "delaware",
]


class CraigslistScraper(BaseScraper):
    source_name = "craigslist"

    def __init__(self, config: dict, rate_limit: float = 2.0):
        super().__init__(config, rate_limit)
        self.regions = config.get("regions", DEFAULT_REGIONS)

    def search(self) -> list[Listing]:
        all_listings = []
        for region in self.regions:
            try:
                results = self._search_region(region)
                all_listings.extend(results)
            except Exception as e:
                logger.warning(f"[{self.source_name}] Failed for {region}: {e}")
        logger.info(f"[{self.source_name}] Found {len(all_listings)} Olson 911 listings across {len(self.regions)} regions")
        return all_listings

    def _search_region(self, region: str) -> list[Listing]:
        """Search a single Craigslist region using the HTML page with JSON-LD."""
        url = f"https://{region}.craigslist.org/search/boo?query=olson+911"
        listings = []

        try:
            resp = self._get(url)
        except Exception as e:
            logger.debug(f"[{self.source_name}] {region} request failed: {e}")
            return []

        # Extract JSON-LD from the page
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "lxml")

        for script in soup.select('script[type="application/ld+json"]'):
            try:
                data = json.loads(script.string)
            except (json.JSONDecodeError, TypeError):
                continue

            if data.get("@type") != "SearchResultsPage":
                continue

            item_list = data.get("mainEntity", {})
            elements = item_list.get("itemListElement", [])

            for element in elements:
                item = element.get("item", {})
                title = item.get("name", "")

                if not self.matches_olson_911(title):
                    continue

                offers = item.get("offers", {})
                price = offers.get("price")
                if price:
                    price = f"${float(price):,.0f}"

                place = offers.get("availableAtOrFrom", {})
                addr = place.get("address", {})
                city = addr.get("addressLocality", "")
                state = addr.get("addressRegion", "")
                location = f"{city}, {state}".strip(", ") if city or state else None

                # JSON-LD doesn't include individual URLs, construct from region
                # We'll use a hash of title+price+location as listing_id
                listing_id = f"{region}_{hash(title + str(price) + str(location))}"

                listings.append(Listing(
                    source=f"{self.source_name}_{region}",
                    listing_id=listing_id,
                    title=title,
                    url=url,  # Link to search results page
                    price=price,
                    location=location,
                ))

        # Also try parsing the static search results as fallback
        if not listings:
            listings = self._parse_static_results(soup, region)

        return listings

    def _parse_static_results(self, soup, region: str) -> list[Listing]:
        """Fallback: parse cl-static-search-results if present."""
        listings = []
        for item in soup.select("ol.cl-static-search-results li"):
            link = item.select_one("a")
            if not link:
                continue
            title = link.get_text(strip=True)
            if not self.matches_olson_911(title):
                continue
            href = link.get("href", "")
            posting_id = href.rstrip("/").split("/")[-1].replace(".html", "")

            price_el = item.select_one(".price")
            price = price_el.get_text(strip=True) if price_el else None

            listings.append(Listing(
                source=f"{self.source_name}_{region}",
                listing_id=posting_id or f"{region}_{hash(title)}",
                title=title,
                url=href if href.startswith("http") else f"https://{region}.craigslist.org{href}",
                price=price,
            ))
        return listings
