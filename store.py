import sqlite3
from datetime import datetime, timezone
from models import Listing


class ListingStore:
    def __init__(self, db_path: str = "listings.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS seen_listings (
                source TEXT NOT NULL,
                listing_id TEXT NOT NULL,
                title TEXT,
                price TEXT,
                location TEXT,
                url TEXT NOT NULL,
                date_found TEXT NOT NULL,
                description TEXT,
                PRIMARY KEY (source, listing_id)
            )
        """)
        self.conn.commit()

    def is_seen(self, source: str, listing_id: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM seen_listings WHERE source = ? AND listing_id = ?",
            (source, listing_id),
        ).fetchone()
        return row is not None

    def mark_seen(self, listing: Listing) -> None:
        self.conn.execute(
            """INSERT OR IGNORE INTO seen_listings
               (source, listing_id, title, price, location, url, date_found, description)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                listing.source,
                listing.listing_id,
                listing.title,
                listing.price,
                listing.location,
                listing.url,
                listing.date_found or datetime.now(timezone.utc).isoformat(),
                listing.description,
            ),
        )
        self.conn.commit()

    def filter_new(self, listings: list[Listing]) -> list[Listing]:
        return [l for l in listings if not self.is_seen(l.source, l.listing_id)]

    def close(self):
        self.conn.close()
