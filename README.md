# Olson 911SE Listing Monitor

Automated daily search for Olson 911SE sailboat listings across multiple sites. Sends an email when new listings are found.

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

### 3. Run locally

```bash
python main.py
```

### 4. Deploy to GitHub Actions

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
| [Sailboat Listings](https://www.sailboatlistings.com) | All Olson manufacturer listings, filtered for 911 |
| [Craigslist](https://craigslist.org) | 38 regions (PNW priority + nationwide coastal) |
| [48° North](https://48north.com/classifieds/) | PNW sailing magazine classifieds |
| [Sailboat Owners Forum](https://forums.sailboatowners.com) | Ericson section + boats for sale |
| [Sailing Texas](https://www.sailingtexas.com) | Sailboat index pages |
| [EY.o Forum](https://ericsonyachts.org/ie/) | Ericson Yachts owners forum classifieds |

## Manual Alerts to Set Up

These sites block automated scraping. Set up their built-in email alerts or saved searches:

### YachtWorld
1. Go to [yachtworld.com](https://www.yachtworld.com)
2. Search for **"Olson 911"** (also try manufacturer **"Ericson"**, model **"Olson 911 SE"**)
3. Click **Save Search** and enable email notifications

### Boat Trader
1. Go to [boattrader.com](https://www.boattrader.com)
2. Search for **"Olson 911"** under Sail boats
3. Save the search and enable email alerts

### eBay
1. Go to [ebay.com](https://www.ebay.com)
2. Search for **"olson 911se sailboat"**
3. Click **Save this search** — eBay will email you when new matches appear

### Facebook Marketplace
1. Open Facebook Marketplace
2. Search for **"olson 911se"** and **"olson 911 se"**
3. Tap **Save Search** to get push notifications

### Facebook Groups (join these)
- [Ericson Sailboat Owners](https://www.facebook.com/groups/ericsonsailboatowners/) — active community, boats frequently posted for sale
- [Olson 30 Sailboat Group](https://www.facebook.com/groups/olson30/) — Olson-specific group, check for 911SE posts

### Other sites to check periodically
- [Sailing Anarchy Classifieds](https://sailinganarchy.com/classifieds/) — search for "olson" (site blocks automated access)
- [Cruisers Forum Boats for Sale](https://www.cruisersforum.com/forums/f152/) — browse or search for "olson 911"
- [SailNet Marketplace](https://www.sailnet.com/forums/ericson.28/) — Ericson section, check for 911SE posts
