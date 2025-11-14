import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json

URL = "https://tv24.co.uk/sport"
OUTPUT_FILE = "docs/uk_tv_sports_today.json"

ALLOWED_CHANNEL_KEYWORDS = [
    "Sky Sports",
    "TNT Sports",
    "BBC",
    "ITV"
]

def fetch_sports():
    print("Fetching:", URL)
    response = requests.get(URL, headers={
        "User-Agent": "Mozilla/5.0"
    })

    if response.status_code != 200:
        print("Failed to fetch page:", response.status_code)
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    events = []

    cards = soup.select("div.listing")  # event card container

    for card in cards:
        # title
        title_el = card.select_one("h3")
        if not title_el:
            continue
        title = title_el.get_text(strip=True)

        # sport type (football, rugby, etc.)
        sport_el = card.select_one(".category")
        sport = sport_el.get_text(strip=True) if sport_el else "Sport"

        # time
        time_el = card.select_one(".time")
        if not time_el:
            continue
        time = time_el.get_text(strip=True)

        # channel name
        channel_el = card.select_one(".channel")
        if not channel_el:
            continue
        channel = channel_el.get_text(strip=True)

        # filter
        if not any(key.lower() in channel.lower() for key in ALLOWED_CHANNEL_KEYWORDS):
            continue

        events.append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "sport": sport,
            "title": title,
            "time": time,
            "channel": channel
        })

    return events


def main():
    events = fetch_sports()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=4, ensure_ascii=False)

    print(f"Saved {len(events)} events to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
