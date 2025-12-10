import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re

OUTPUT_FILE = "docs/uk_tv_sports_today.json"
ALLOWED_CHANNELS = ["BBC", "ITV"]  # Only desired channels
SPORT_KEYWORDS = [
    "football","rugby","cricket","tennis","golf","boxing",
    "basketball","hockey","motorsport","formula","f1","mma"
]

def today_str():
    """Return today's date in YYYY-MM-DD format."""
    return datetime.now().strftime("%Y-%m-%d")

# ----------------------- TV24 -----------------------
def fetch_tv24():
    url = "https://tv24.co.uk/sports"
    events = []

    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        print(f"[INFO] TV24 fetched successfully")
    except Exception as e:
        print(f"[WARNING] TV24 fetch failed: {e}")
        return events

    soup = BeautifulSoup(r.text, "html.parser")
    listings = soup.find_all("div", class_="listing")

    for li in listings:
        date_attr = li.get("data-date")
        if date_attr != today_str():
            continue

        time_tag = li.find("span", class_="time")
        time_str = time_tag.text.strip() if time_tag else "TBD"

        title_tag = li.find("span", class_="event")
        title = title_tag.text.strip() if title_tag else "Unknown"

        channel_tag = li.find("span", class_="channel")
        channel = channel_tag.text.strip() if channel_tag else "Unknown"

        if channel not in ALLOWED_CHANNELS:
            continue

        sport = "Other"
        for keyword in SPORT_KEYWORDS:
            if keyword in title.lower():
                sport = keyword.capitalize()
                break

        events.append({
            "date": today_str(),
            "time": time_str,
            "title": title,
            "sport": sport,
            "channel": channel
        })
        print(f"[DEBUG] TV24: Added {time_str} - {title} ({sport}) on {channel}")

    return events

# ----------------------- BBC Sport -----------------------
def fetch_bbc():
    url = "https://www.bbc.co.uk/sport"
    events = []

    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        print("[INFO] BBC Sport fetched successfully")
    except Exception as e:
        print(f"[WARNING] BBC Sport fetch failed: {e}")
        return events

    soup = BeautifulSoup(r.text, "html.parser")
    lines = [line.strip() for line in soup.get_text().split("\n") if line.strip()]

    for line in lines:
        if re.search(r'\d{1,2}:\d{2}', line) and any(s in line.lower() for s in SPORT_KEYWORDS):
            if any(bbc_channel.lower() in line.lower() for bbc_channel in ["bbc one", "bbc two", "bbc three", "bbc four"]):
                time_match = re.search(r'(\d{1,2}:\d{2})', line)
                if time_match:
                    time_str = time_match.group(1)
                    title = re.sub(r'\d{1,2}:\d{2}', '', line).strip()
                    title = re.sub(r'(bbc one|bbc two|bbc three|bbc four)', '', title, flags=re.IGNORECASE).strip()

                    sport = "Other"
                    for keyword in SPORT_KEYWORDS:
                        if keyword in title.lower():
                            sport = keyword.capitalize()
                            break

                    events.append({
                        "date": today_str(),
                        "time": time_str,
                        "title": title,
                        "sport": sport,
                        "channel": "BBC"
                    })
                    print(f"[DEBUG] BBC: Added {time_str} - {title} ({sport})")

    return events

# ----------------------- RadioTimes -----------------------
def fetch_radiotimes():
    urls_to_try = [
        "https://www.radiotimes.com/tv/sport/",
        "https://www.radiotimes.com/tv/"
    ]
    events = []

    headers = {"User-Agent": "Mozilla/5.0"}

    for url in urls_to_try:
        try:
            r = requests.get(url, headers=headers, timeout=10)
            r.raise_for_status()
            print(f"[INFO] RadioTimes fetched successfully: {url}")
        except Exception as e:
            print(f"[WARNING] RadioTimes fetch failed ({url}): {e}")
            continue

        soup = BeautifulSoup(r.text, "html.parser")
        programme_items = soup.find_all(['div','li','article'], class_=re.compile(r'(programme|listing|guide|show)', re.I))

        for item in programme_items:
            text = item.get_text(" ", strip=True)
            if len(text) > 500:
                continue

            # Check for sport keywords and allowed channels
            if any(s in text.lower() for s in SPORT_KEYWORDS) and any(ch.lower() in text.lower() for ch in ALLOWED_CHANNELS):
                time_match = re.search(r'(\d{1,2}:\d{2})', text)
                if not time_match:
                    continue
                time_str = time_match.group(1)

                channel_found = None
                for ch in ALLOWED_CHANNELS:
                    if ch.lower() in text.lower():
                        channel_found = ch
                        break
                if not channel_found:
                    continue

                title = re.sub(r'(\d{1,2}:\d{2})', '', text).strip()
                title = re.sub(r'(' + '|'.join(ALLOWED_CHANNELS) + ')', '', title, flags=re.IGNORECASE).strip()
                title = re.sub(r'(watch|live|tonight|today|programme|show)', '', title, flags=re.IGNORECASE).strip()

                if title and len(title) < 100:
                    sport = "Other"
                    for keyword in SPORT_KEYWORDS:
                        if keyword in title.lower():
                            sport = keyword.capitalize()
                            break

                    events.append({
                        "date": today_str(),
                        "time": time_str,
                        "title": title,
                        "sport": sport,
                        "channel": channel_found
                    })
                    print(f"[DEBUG] RadioTimes: Added {time_str} - {title} ({sport}) on {channel_found}")

        if events:
            break

    return events

# ----------------------- MAIN -----------------------
def main():
    all_events = []

    print("[INFO] Fetching TV24 events...")
    all_events.extend(fetch_tv24())

    print("[INFO] Fetching BBC events...")
    all_events.extend(fetch_bbc())

    print("[INFO] Fetching RadioTimes events...")
    all_events.extend(fetch_radiotimes())

    if not all_events:
        print("[WARNING] No events found. JSON will be empty.")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_events, f, indent=4, ensure_ascii=False)

    print(f"[INFO] Saved {len(all_events)} events to {OUTPUT_FILE}")
    for ev in all_events[:5]:
        print(f"{ev['time']} - {ev['title']} ({ev['sport']}) on {ev['channel']}")

if __name__ == "__main__":
    main()
