import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json

OUTPUT_FILE = "docs/uk_tv_sports_today.json"
ALLOWED_CHANNELS = ["Sky Sports", "TNT Sports", "BBC", "ITV"]

def fetch_live_football():
    url = "https://www.live-footballontv.com/tv-guide-uk/"
    events = []
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        r.raise_for_status()
    except requests.RequestException as e:
        print("[WARNING] Live Football on TV skipped:", e)
        return events

    soup = BeautifulSoup(r.text, "html.parser")
    rows = soup.select("table.tvguide tr")
    for row in rows:
        cols = row.select("td")
        if len(cols) < 3:
            continue
        channel = cols[0].get_text(strip=True)
        time = cols[1].get_text(strip=True)
        title = cols[2].get_text(strip=True)
        if not any(c.lower() in channel.lower() for c in ALLOWED_CHANNELS):
            continue
        events.append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "sport": "Football",
            "title": title,
            "time": time,
            "channel": channel
        })
    return events

def fetch_radiotimes():
    url = "https://www.radiotimes.com/tv/tv-guide/"
    events = []
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        r.raise_for_status()
    except requests.RequestException as e:
        print("[WARNING] RadioTimes skipped:", e)
        return events

    soup = BeautifulSoup(r.text, "html.parser")
    listings = soup.select("li.listing-item")
    for li in listings:
        time_el = li.select_one("time")
        title_el = li.select_one(".listing-title")
        channel_el = li.select_one(".listing-channel")
        category_el = li.select_one(".listing-category")
        if not (time_el and title_el and channel_el):
            continue
        channel = channel_el.get_text(strip=True)
        if not any(c.lower() in channel.lower() for c in ALLOWED_CHANNELS):
            continue
        events.append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "sport": category_el.get_text(strip=True) if category_el else "Sport",
            "title": title_el.get_text(strip=True),
            "time": time_el.get_text(strip=True),
            "channel": channel
        })
    return events

def fetch_bbc_sport():
    url = "https://www.bbc.co.uk/sport/tv-radio-guide"
    events = []
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        r.raise_for_status()
    except requests.RequestException as e:
        print("[WARNING] BBC Sport skipped:", e)
        return events

    soup = BeautifulSoup(r.text, "html.parser")
    rows = soup.select(".programme-item")
    for row in rows:
        time_el = row.select_one(".time")
        title_el = row.select_one(".title")
        channel_el = row.select_one(".channel")
        sport_el = row.select_one(".category")
        if not (time_el and title_el and channel_el):
            continue
        channel = channel_el.get_text(strip=True)
        if not any(c.lower() in channel.lower() for c in ALLOWED_CHANNELS):
            continue
        events.append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "sport": sport_el.get_text(strip=True) if sport_el else "Sport",
            "title": title_el.get_text(strip=True),
            "time": time_el.get_text(strip=True),
            "channel": channel
        })
    return events

def main():
    all_events = []
    all_events.extend(fetch_live_football())
    all_events.extend(fetch_radiotimes())
    all_events.extend(fetch_bbc_sport())

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_events, f, indent=4, ensure_ascii=False)

    print(f"Saved {len(all_events)} events to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
