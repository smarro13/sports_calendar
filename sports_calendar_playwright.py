import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re

OUTPUT_FILE = "docs/uk_tv_sports_today.json"
ALLOWED_CHANNELS = ["Sky Sports", "TNT Sports", "BBC", "ITV"]

# -----------------------------
# 1. Live Football on TV
# -----------------------------
def fetch_live_football():
    url = "https://www.live-footballontv.com/"
    events = []

    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        print(f"[INFO] Live Football on TV: Successfully fetched {url}")
    except requests.RequestException as e:
        print("[WARNING] Live Football on TV skipped:", e)
        return events

    soup = BeautifulSoup(r.text, "html.parser")
    page_text = soup.get_text()
    lines = [line.strip() for line in page_text.split("\n") if line.strip()]

    # Dynamically find today's date on the page
    today = datetime.now()
    try:
        today_str = today.strftime("%A %-d %B")  # Linux/Mac
    except ValueError:
        today_str = today.strftime("%A %#d %B")  # Windows

    today_found = False
    for i, line in enumerate(lines):
        if today_str in line:
            today_found = True
            print(f"[DEBUG] Found today's section: {line}")
            for j in range(i+1, min(i+20, len(lines))):
                match_line = lines[j]
                if re.match(r'^\d{1,2}:\d{2}\s+.+ v .+', match_line):
                    time_match = re.search(r'^(\d{1,2}:\d{2})\s+(.+)', match_line)
                    if time_match:
                        time_str = time_match.group(1)
                        rest = time_match.group(2)
                        found_channel = None
                        for channel_name in ALLOWED_CHANNELS:
                            if channel_name.lower() in rest.lower():
                                found_channel = channel_name
                                idx = rest.lower().find(channel_name.lower())
                                rest = rest[:idx].strip()
                                break
                        if found_channel and " v " in rest:
                            events.append({
                                "date": today.strftime("%Y-%m-%d"),
                                "sport": "Football",
                                "title": rest,
                                "time": time_str,
                                "channel": found_channel
                            })
                            print(f"[DEBUG] Added: {time_str} - {rest} on {found_channel}")
            break

    if not today_found:
        print("[DEBUG] Today's section not found; attempting fallback search...")
        for line in lines:
            if re.search(r'\d{1,2}:\d{2}', line) and ' v ' in line:
                found_channel = None
                for channel_name in ALLOWED_CHANNELS:
                    if channel_name.lower() in line.lower():
                        found_channel = channel_name
                        break
                if found_channel:
                    time_match = re.search(r'(\d{1,2}:\d{2})', line)
                    if time_match:
                        time_str = time_match.group(1)
                        title = line.replace(time_str, "").strip()
                        idx = title.lower().find(found_channel.lower())
                        if idx != -1:
                            title = title[:idx].strip()
                        events.append({
                            "date": today.strftime("%Y-%m-%d"),
                            "sport": "Football",
                            "title": title,
                            "time": time_str,
                            "channel": found_channel
                        })
                        print(f"[DEBUG] Fallback added: {time_str} - {title} on {found_channel}")

    print(f"[DEBUG] Total football matches found: {len(events)}")
    return events

# -----------------------------
# 2. RadioTimes
# -----------------------------
def fetch_radiotimes():
    urls_to_try = [
        "https://www.radiotimes.com/tv/sport/",
        "https://www.radiotimes.com/tv/",
        "https://www.radiotimes.com/tv-guide/"
    ]
    events = []
    today = datetime.now().strftime("%Y-%m-%d")

    for url in urls_to_try:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers, timeout=10)
            r.raise_for_status()
            print(f"[INFO] RadioTimes: Successfully fetched {url}")

            soup = BeautifulSoup(r.text, "html.parser")
            programme_items = soup.find_all(['div','li','article'], class_=re.compile(r'(programme|listing|guide|show)', re.I))

            for item in programme_items[:20]:
                text = item.get_text(strip=True)
                if len(text) > 500:
                    continue
                if (any(word in text.lower() for word in ['football','sport','match','live']) and
                    re.search(r'\d{1,2}[:.:]\d{2}', text) and
                    any(chan.lower() in text.lower() for chan in ALLOWED_CHANNELS)):
                    time_match = re.search(r'(\d{1,2}[:.:]\d{2})', text)
                    if time_match:
                        time_str = time_match.group(1).replace('.', ':')
                        found_channel = next((c for c in ALLOWED_CHANNELS if c.lower() in text.lower()), None)
                        title = text.replace(time_str, "").strip()
                        if found_channel:
                            title = re.sub(found_channel, "", title, flags=re.IGNORECASE).strip()
                            if len(title) > 5:
                                events.append({
                                    "date": today,
                                    "sport": "Sport",
                                    "title": title,
                                    "time": time_str,
                                    "channel": found_channel
                                })
                                print(f"[DEBUG] RadioTimes added: {time_str} - {title} on {found_channel}")
            if events:
                break
        except Exception as e:
            print(f"[WARNING] RadioTimes URL {url} failed: {e}")
            continue
    print(f"[DEBUG] Total events from RadioTimes: {len(events)}")
    return events

# -----------------------------
# 3. BBC Sport
# -----------------------------
def fetch_bbc_sport():
    url = "https://www.bbc.co.uk/sport"
    events = []
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        print(f"[INFO] BBC Sport: Successfully fetched {url}")
    except requests.RequestException as e:
        print("[WARNING] BBC Sport skipped:", e)
        return events

    soup = BeautifulSoup(r.text, "html.parser")
    page_text = soup.get_text()
    lines = [line.strip() for line in page_text.split("\n") if line.strip()]

    for line in lines:
        if (re.search(r'\d{1,2}:\d{2}', line) and 
            any(word in line.lower() for word in ['football','sport','rugby','cricket']) and
            len(line) < 200):
            time_match = re.search(r'(\d{1,2}:\d{2})', line)
            if time_match:
                time_str = time_match.group(1)
                title = line.replace(time_str, "").strip()
                events.append({
                    "date": today,
                    "sport": "Sport",
                    "title": title,
                    "time": time_str,
                    "channel": "BBC"
                })
                print(f"[DEBUG] BBC added: {time_str} - {title}")
    print(f"[DEBUG] Total events from BBC: {len(events)}")
    return events

# -----------------------------
# Main function
# -----------------------------
def main():
    print("Starting to fetch UK TV sports listings...")
    all_events = []

    print("\n1. Fetching Live Football on TV...")
    all_events.extend(fetch_live_football())

    print("\n2. Fetching RadioTimes...")
    all_events.extend(fetch_radiotimes())

    print("\n3. Fetching BBC Sport...")
    all_events.extend(fetch_bbc_sport())

    # Fallback sample data if no live events found
    if not all_events:
        print("[INFO] No live events found. Adding sample events...")
        today = datetime.now().strftime("%Y-%m-%d")
        all_events.extend([
            {"date": today, "sport": "Football", "title": "Sample Match 1", "time": "19:30", "channel": "Sky Sports"},
            {"date": today, "sport": "Football", "title": "Sample Match 2", "time": "20:00", "channel": "BBC"},
        ])

    # Save to JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_events, f, indent=4, ensure_ascii=False)

    print(f"\nCompleted! Saved {len(all_events)} events to {OUTPUT_FILE}")
    if all_events:
        print("\nPreview of saved events:")
        for ev in all_events[:5]:
            print(f" {ev['time']} - {ev['title']} on {ev['channel']}")

if __name__ == "__main__":
    main()
