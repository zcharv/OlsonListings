# Sailboat Listing Monitor

Automated daily search for sailboat listings across multiple sites. Sends an email when new listings are found. Currently searching for **Olson 911SE** and **Olson 34**.

## Setup

### 1. Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure

```bash
cp config.yaml.example config.yaml
```

Edit `config.yaml` with your email credentials. For Gmail, use an [App Password](https://myaccount.google.com/apppasswords) (requires 2-Step Verification).

### 3. Add or change boats

Edit the `boats` section in `config.yaml`:

```yaml
boats:
  - name: Olson 911SE
    search_queries:
      - "olson 911se sailboat"
      - "olson 911 se sailboat for sale"
    filter_pattern: 'olson\s*911|911\s*se|911s[e\b]'

  - name: Olson 34
    search_queries:
      - "olson 34 sailboat for sale"
    filter_pattern: 'olson\s*34'

  # Add more boats:
  # - name: J/24
  #   search_queries:
  #     - "j/24 sailboat for sale"
  #   filter_pattern: 'j[/\s-]*24'
```

Each boat needs:
- **name**: display name for email notifications
- **search_queries**: terms sent to web search engines
- **filter_pattern**: regex applied to titles/descriptions to filter results

### 4. Run locally

```bash
python main.py
```

### 5. Deploy to GitHub Actions

Push to GitHub, then add these repo secrets (**Settings > Secrets and variables > Actions**):

| Secret | Value |
|---|---|
| `SMTP_USER` | Your Gmail address |
| `SMTP_PASSWORD` | Gmail App Password |
| `EMAIL_TO` | Recipient email(s), comma-separated |

The workflow runs daily at 8 AM PST. You can also trigger it manually from the Actions tab.

## Automated Sources

| Source | What it searches |
|---|---|
| **Web Search** (DuckDuckGo/Bing/Google) | Broad web search — catches listings on YachtWorld, Boat Trader, eBay, Cruisers Forum, Sailing Anarchy, SailNet, EY.o, and any other indexed site |
| **SearXNG** | Backup web search via public SearXNG instances |
| **Google Alerts RSS** | Passive monitoring via Google Alerts RSS feeds (optional setup) |
| [Sailboat Listings](https://www.sailboatlistings.com) | All Olson manufacturer listings |
| [Craigslist](https://craigslist.org) | 38 regions (PNW priority + nationwide coastal) |
| [48° North](https://48north.com/classifieds/) | PNW sailing magazine classifieds |
| [Sailboat Owners Forum](https://forums.sailboatowners.com) | Ericson section + boats for sale |
| [Sailing Texas](https://www.sailingtexas.com) | Sailboat index pages |

## Optional: Google Alerts RSS

For passive monitoring with zero blocking risk:

1. Go to [google.com/alerts](https://www.google.com/alerts)
2. Create alerts for your boat search terms (e.g. "olson 911se", "olson 34 sailboat")
3. Set **"Deliver to"** → **RSS feed**
4. Copy the RSS feed URLs into `config.yaml` under `sources.google_alerts.feeds`

## Manual Alerts to Set Up

These sites block automated scraping but offer their own saved search features:

### YachtWorld
Search for **"Olson 911"** and **"Olson 34"** → Save Search → enable email notifications

### Boat Trader
Search under Sail boats → Save search → enable email alerts

### eBay
Search for your boat → **Save this search** → eBay emails you when new matches appear

### Facebook Marketplace
Search → **Save Search** → get push notifications

### Facebook Groups (join these)
- [Ericson Sailboat Owners](https://www.facebook.com/groups/ericsonsailboatowners/)
- [Olson 30 Sailboat Group](https://www.facebook.com/groups/olson30/)

### Other sites to check periodically
- [EY.o Forum](https://ericsonyachts.org/ie/) — Ericson Yachts owners forum classifieds
- [Sailing Anarchy Classifieds](https://sailinganarchy.com/classifieds/)
- [Cruisers Forum Boats for Sale](https://www.cruisersforum.com/forums/f152/)
- [SailNet Marketplace](https://www.sailnet.com/forums/ericson.28/)
