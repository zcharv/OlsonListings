#!/usr/bin/env python3
"""Olson 911SE listing monitor — searches multiple sites and emails new finds."""

import logging
import os
import sys

import yaml

from models import Listing
from store import ListingStore
from notifier import send_notification
from scrapers.base import set_boat_patterns

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Scraper registry — maps config key to scraper class
SCRAPER_MAP = {
    "web_search": "scrapers.web_search.WebSearchScraper",
    "searxng": "scrapers.searxng.SearXNGScraper",
    "google_alerts": "scrapers.google_alerts.GoogleAlertsScraper",
    "sailboatlistings": "scrapers.sailboatlistings.SailboatListingsScraper",
    "craigslist": "scrapers.craigslist.CraigslistScraper",
    "fortyeight_north": "scrapers.fortyeight_north.FortyEightNorthScraper",
    "sailboatowners": "scrapers.sailboatowners.SailboatOwnersScraper",
    "sailing_texas": "scrapers.sailing_texas.SailingTexasScraper",
    "ericson_yachts": "scrapers.ericson_yachts.EricsonYachtsScraper",
}


def load_config() -> dict:
    """Load config from file, with env var overrides for CI."""
    config_path = os.environ.get("CONFIG_PATH", "config.yaml")

    if os.path.exists(config_path):
        with open(config_path) as f:
            config = yaml.safe_load(f)
    else:
        config = {"email": {}, "sources": {}, "rate_limit": {}, "database": {}}

    # Allow env var overrides for GitHub Actions secrets
    email = config.setdefault("email", {})
    if os.environ.get("SMTP_HOST"):
        email["smtp_host"] = os.environ["SMTP_HOST"]
    if os.environ.get("SMTP_PORT"):
        email["smtp_port"] = int(os.environ["SMTP_PORT"])
    if os.environ.get("SMTP_USER"):
        email["smtp_user"] = os.environ["SMTP_USER"]
    if os.environ.get("SMTP_PASSWORD"):
        email["smtp_password"] = os.environ["SMTP_PASSWORD"]
    if os.environ.get("EMAIL_FROM"):
        email["from_addr"] = os.environ["EMAIL_FROM"]
    if os.environ.get("EMAIL_TO"):
        email["to_addrs"] = os.environ["EMAIL_TO"].split(",")

    # Default email settings
    email.setdefault("smtp_host", "smtp.gmail.com")
    email.setdefault("smtp_port", 587)

    # Google Alerts feeds from env var (comma-separated URLs)
    if os.environ.get("GOOGLE_ALERTS_FEEDS"):
        sources = config.setdefault("sources", {})
        ga = sources.setdefault("google_alerts", {})
        ga["feeds"] = [u.strip() for u in os.environ["GOOGLE_ALERTS_FEEDS"].split(",")]

    # Default boats config if none specified
    config.setdefault("boats", [
        {
            "name": "Olson 911SE",
            "search_queries": [
                "olson 911se sailboat",
                "olson 911 se sailboat for sale",
                "olson 911se for sale",
            ],
            "filter_pattern": r"olson\s*911|911\s*se|911s[e\b]",
        },
        {
            "name": "Olson 34",
            "search_queries": [
                "olson 34 sailboat for sale",
                "olson 34 sailboat",
            ],
            "filter_pattern": r"olson\s*34",
        },
    ])

    return config


def import_scraper(dotted_path: str):
    """Import a scraper class from a dotted module path."""
    module_path, class_name = dotted_path.rsplit(".", 1)
    import importlib
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def run():
    config = load_config()
    db_path = config.get("database", {}).get("path", "listings.db")
    rate_limit = config.get("rate_limit", {}).get("delay_between_requests", 2.0)

    # Initialize boat patterns from config
    boats = config.get("boats", [])
    set_boat_patterns(boats)
    boat_names = ", ".join(b["name"] for b in boats)
    logger.info(f"Searching for: {boat_names}")

    # Collect all search queries from all boats for web search scrapers
    all_queries = []
    for boat in boats:
        all_queries.extend(boat.get("search_queries", []))
    config["_search_queries"] = all_queries

    store = ListingStore(db_path)

    all_new = []
    sources_config = config.get("sources", {})

    for source_key, scraper_path in SCRAPER_MAP.items():
        source_cfg = sources_config.get(source_key, {})
        if not source_cfg.get("enabled", True):
            logger.info(f"Skipping disabled source: {source_key}")
            continue

        try:
            scraper_cls = import_scraper(scraper_path)
            # Pass boat search queries to web search scrapers if not overridden
            if source_key in ("web_search", "searxng") and "queries" not in source_cfg:
                source_cfg = {**source_cfg, "queries": all_queries}
            scraper = scraper_cls(config=source_cfg, rate_limit=rate_limit)
            logger.info(f"Searching {source_key}...")
            listings = scraper.search()
            new_listings = store.filter_new(listings)

            for listing in new_listings:
                store.mark_seen(listing)
                all_new.append(listing)

            if new_listings:
                logger.info(f"  {len(new_listings)} NEW from {source_key}")
            else:
                logger.info(f"  No new listings from {source_key}")

        except Exception as e:
            logger.error(f"Error with {source_key}: {e}")

    # Send notification
    if all_new:
        logger.info(f"Total new listings: {len(all_new)}")
        try:
            send_notification(all_new, config)
        except Exception as e:
            logger.error(f"Notification failed: {e}")
            # Still print listings to stdout for cron/CI logs
            for l in all_new:
                print(f"  NEW: {l.title} | {l.price} | {l.url}")
    else:
        logger.info("No new listings found across all sources.")

    store.close()
    return len(all_new)


if __name__ == "__main__":
    count = run()
    sys.exit(0)
