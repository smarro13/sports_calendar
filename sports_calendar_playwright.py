import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json

URL = "https://www.tv24.co.uk/sports"
OUTPUT_FILE = "docs/uk_tv_sports_today.json"

ALLOWED_CHANNEL_KEYWORDS = ["Sky Sports", "TNT Sports", "BBC", "ITV"]

def fetch_events():
    resp = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
    if resp.status_code != 200:
        print("Failed to fetch page:", resp.status_code)
        return []
    soup = BeautifulSoup(resp.text, "html.parser")
    events = []

    # Example selector: list items under some class – you will need to inspect live page
    rows = soup.select("div.listing article")  # approximate; update after inspection

    today_str = datetime.now().strftime("%A %d %B %Y")  # e.g., "Friday 14 November 2025"

    for row in rows:
        date_el = row.select_one(".date")
        date_text = date_el.get_text(strip=True) if date_el else today_str
        if today_str not in date_text:
            continue

        title_el = row.select_one("h3.title")
        time_el = row.select_one(".time")
        channel_el = row.select_one(".channel")

        if not (title_el and time_el and channel_el):
            continue

        channel = channel_el.get_text(strip=True)
        if not any(k in channel for k in ALLOWED_CHANNEL_KEYWORDS):
            continue

        events.append({
            "date": date_text,
            "sport": row.select_one(".category").get_text(strip=True) if row.select_one(".category") else "Sport",
            "title": title_el.get_text(strip=True),
            "time": time_el.get_text(strip=True),
            "channel": channel
        })

    return events

def main():
    ev = fetch_events()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(ev, f, indent=4, ensure_ascii=False)
    print(f"Saved {len(ev)} events to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
