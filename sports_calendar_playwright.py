import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json

URL = "https://www.tv24.co.uk/sports"
OUTPUT_FILE = "docs/uk_tv_sports_today.json"

ALLOWED_CHANNEL_KEYWORDS = [
    "Sky Sports", "TNT Sports", "BBC", "ITV"
]

def fetch_events():
    resp = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
    if resp.status_code != 200:
        print("Failed to fetch page:", resp.status_code)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    events = []
    today = datetime.now().strftime("%A %d %B %Y")  # e.g., 'Friday 14 November 2025'

    # Each event appears in an <li> under a listing (inspect visually)
    listings = soup.select("ul.listings-list > li")  # based on structure

    for item in listings:
        # extract date if present
        date_el = item.select_one("div.listings-date")
        date_text = date_el.get_text(strip=True) if date_el else today
        if today not in date_text:
            continue

        time_el = item.select_one("time")
        if not time_el:
            continue
        time_text = time_el.get_text(strip=True)

        title_el = item.select_one("h3.title")
        if not title_el:
            continue
        title_text = title_el.get_text(strip=True)

        channel_el = item.select_one("div.channel")
        if not channel_el:
            continue
        channel_text = channel_el.get_text(strip=True)

        # filter by channel keywords
        if not any(key.lower() in channel_text.lower() for key in ALLOWED_CHANNEL_KEYWORDS):
            continue

        sport_el = item.select_one("div.category")
        sport_text = sport_el.get_text(strip=True) if sport_el else "Sport"

        events.append({
            "date": date_text,
            "sport": sport_text,
            "title": title_text,
            "time": time_text,
            "channel": channel_text
        })

    return events

def main():
    ev = fetch_events()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(ev, f, indent=4, ensure_ascii=False)
    print(f"Saved {len(ev)} events to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
