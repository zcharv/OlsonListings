import logging
from urllib.parse import urljoin

from scrapers.base import BaseScraper
from models import Listing

logger = logging.getLogger(__name__)

# EY.o Information Exchange — Ericson Yachts owners forum
# The forum likely uses phpBB or similar — we'll try the classifieds subforum
BASE_URL = "https://ericsonyachts.org/ie/"


class EricsonYachtsScraper(BaseScraper):
    source_name = "ericson_yachts"

    def search(self) -> list[Listing]:
        listings = []

        try:
            soup = self._soup(BASE_URL)
        except Exception as e:
            logger.error(f"[{self.source_name}] Failed to fetch forum index: {e}")
            return []

        # Find links to classifieds/for-sale subforum
        classifieds_links = []
        for link in soup.find_all("a", href=True):
            text = link.get_text(strip=True).lower()
            if any(kw in text for kw in ["classif", "for sale", "buy", "sell", "market"]):
                href = link["href"]
                if not href.startswith("http"):
                    href = urljoin(BASE_URL, href)
                classifieds_links.append(href)

        if not classifieds_links:
            # Fallback: scan all forum links for olson 911 mentions
            logger.info(f"[{self.source_name}] No classifieds subforum found, scanning all links")
            return self._scan_all_links(soup)

        # Search each classifieds subforum
        for cl_url in classifieds_links[:3]:  # limit to avoid excessive requests
            try:
                cl_soup = self._soup(cl_url)
                listings.extend(self._extract_listings(cl_soup, cl_url))
            except Exception as e:
                logger.warning(f"[{self.source_name}] Failed to fetch {cl_url}: {e}")

        logger.info(f"[{self.source_name}] Found {len(listings)} Olson 911 listings")
        return listings

    def _extract_listings(self, soup, base_url: str) -> list[Listing]:
        """Extract listings from a forum page — works for common forum software."""
        listings = []
        # Try common forum thread selectors
        for link in soup.find_all("a", href=True):
            text = link.get_text(strip=True)
            if not self.matches_olson_911(text):
                continue

            href = link["href"]
            if not href.startswith("http"):
                href = urljoin(base_url, href)

            listing_id = href.rstrip("/").split("/")[-1].split("?")[0].split("#")[0]

            listings.append(Listing(
                source=self.source_name,
                listing_id=listing_id,
                title=text,
                url=href,
            ))
        return listings

    def _scan_all_links(self, soup) -> list[Listing]:
        """Scan the entire page for any links mentioning olson 911."""
        listings = []
        for link in soup.find_all("a", href=True):
            text = link.get_text(strip=True)
            if self.matches_olson_911(text):
                href = link["href"]
                if not href.startswith("http"):
                    href = urljoin(BASE_URL, href)
                listing_id = href.rstrip("/").split("/")[-1].split("?")[0]
                listings.append(Listing(
                    source=self.source_name,
                    listing_id=listing_id,
                    title=text,
                    url=href,
                ))
        return listings
