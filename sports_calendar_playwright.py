import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json

URL = "https://www.tv24.co.uk/sports"
OUTPUT_FILE = "docs/uk_tv_sports_today.json"

ALLOWED_CHANNEL_KEYWORDS = [
    "Sky Sports", "TNT Sports", "BBC", "ITV"
]

def debug_print(msg):
    print(f"[DEBUG] {msg}")

def fetch_events():
    debug_print(f"Fetching: {URL}")
    resp = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})

    debug_print(f"Status code: {resp.status_code}")
    if resp.status_code != 200:
        return []

    # Save raw HTML for inspection
    with open("debug_tv24.html", "w", encoding="utf-8") as f:
        f.write(resp.text)
    debug_print("Saved HTML → debug_tv24.html")

    soup = BeautifulSoup(resp.text, "html.parser")
    today = datetime.now().strftime("%A %d %B %Y")

    # Debug: try several possible selectors
    possible_selectors = [
        "ul.listings-list > li",
        "li.listings-item",
        "div.listings-item",
        "article",
        "div.programme",
        "div.schedule-item"
    ]

    listings = []
    for sel in possible_selectors:
        found = soup.select(sel)
        debug_print(f"Selector '{sel}' matched {len(found)} elements")
        if len(found) > 0:
            listings = found
            debug_print(f"Using selector: {sel}")
            break

    if not listings:
        debug_print("No listings found with any selector!")
        return []

    # Show first 2 blocks for debugging
    for i, block in enumerate(listings[:2]):
        debug_print(f"---- RAW BLOCK {i} ----")
        debug_print(block.get_text(" ", strip=True))

    events = []

    # Now parse each listing
    for item in listings:
        date_el = item.select_one("div.listings-date")
        time_el = item.select_one("time")
        title_el = item.select_one("h3.title")
        channel_el = item.select_one("div.channel")
        sport_el = item.select_one("div.category")

        # Debug prints
        debug_print(f"Item text: {item.get_text(' ', strip=True)[:120]}...")

        if not time_el or not title_el or not channel_el:
            debug_print("Skipping item — missing time/title/channel")
            continue

        time_text = time_el.get_text(strip=True)
        title_text = title_el.get_text(strip=True)
        channel_text = channel_el.get_text(strip=True)
        sport_text = sport_el.get_text(strip=True) if sport_el else "Sport"
        date_text = (
            date_el.get_text(strip=True)
            if date_el else today
        )

        # Channel filter debugging
        debug_print(f"Detected channel: {channel_text}")
        if not any(key.lower() in channel_text.lower() for key in ALLOWED_CHANNEL_KEYWORDS):
            debug_print("→ Rejected (channel not allowed)")
            continue

        events.append({
            "date": date_text,
            "sport": sport_text,
            "title": title_text,
            "time": time_text,
            "channel": channel_text,
        })

        debug_print(f"→ ADDED EVENT: {title_text}")

    return events


def main():
    events = fetch_events()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=4, ensure_ascii=False)

    print(f"Saved {len(events)} events to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
