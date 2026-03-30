from dataclasses import dataclass


@dataclass
class Listing:
    source: str
    listing_id: str
    title: str
    url: str
    price: str | None = None
    location: str | None = None
    date_found: str | None = None
    description: str | None = None
