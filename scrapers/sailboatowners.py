import logging
import urllib3

from scrapers.base import BaseScraper

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from models import Listing

logger = logging.getLogger(__name__)

# Ericson section — Olson 911SE was built by Ericson Yachts
BASE_URL = "https://forums.sailboatowners.com/forums/ericson.71/"
# Also check the classifieds/for-sale section
CLASSIFIEDS_URL = "https://forums.sailboatowners.com/forums/sailboats-for-sale.62/"


class SailboatOwnersScraper(BaseScraper):
    source_name = "sailboatowners"

    def search(self) -> list[Listing]:
        listings = []
        seen_ids = set()

        for url in [BASE_URL, CLASSIFIEDS_URL]:
            try:
                results = self._search_forum(url)
                for l in results:
                    if l.listing_id not in seen_ids:
                        seen_ids.add(l.listing_id)
                        listings.append(l)
            except Exception as e:
                logger.warning(f"[{self.source_name}] Failed to fetch {url}: {e}")

        logger.info(f"[{self.source_name}] Found {len(listings)} Olson 911 listings")
        return listings

    def _search_forum(self, url: str) -> list[Listing]:
        listings = []
        # XenForo may have SSL issues — try with verify=False
        try:
            soup = self._soup(url)
        except Exception:
            try:
                import requests
                resp = self.session.get(url, timeout=30, verify=False)
                resp.raise_for_status()
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, "lxml")
            except Exception as e:
                logger.debug(f"[{self.source_name}] Fallback also failed for {url}: {e}")
                return []

        for thread in soup.select("div.structItem--thread"):
            title_el = thread.select_one("div.structItem-title a[data-preview-url]")
            if not title_el:
                # Try alternate selector
                title_el = thread.select_one("div.structItem-title a")
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            if not self.matches_olson_911(title):
                continue

            href = title_el.get("href", "")
            if not href.startswith("http"):
                href = f"https://forums.sailboatowners.com{href}"

            # Extract thread ID from URL
            thread_id = href.rstrip("/").split(".")[-1].rstrip("/")

            # Try to get date
            time_el = thread.select_one("time.u-dt")
            date = time_el.get("datetime") if time_el else None

            listings.append(Listing(
                source=self.source_name,
                listing_id=thread_id,
                title=title,
                url=href,
                date_found=date,
            ))

        return listings
