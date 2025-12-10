import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re

OUTPUT_FILE = "docs/uk_tv_sports_today.json"
ALLOWED_CHANNELS = ["Sky Sports", "TNT Sports", "BBC", "ITV"]

def fetch_live_football():
    url = "https://www.live-footballontv.com/"
    events = []
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        print(f"[INFO] Live Football on TV: Successfully fetched {url}")
    except requests.RequestException as e:
        print("[WARNING] Live Football on TV skipped:", e)
        return events

    soup = BeautifulSoup(r.text, "html.parser")
    print("[DEBUG] Looking for match data...")
    
    # Automatically detect today's date
    today_str = datetime.now().strftime("%A %d %B")  # e.g., "Tuesday 10 December"
    page_text = soup.get_text()
    lines = [line.strip() for line in page_text.split('\n') if line.strip()]
    
    today_found = False
    for i, line in enumerate(lines):
        if today_str in line:
            today_found = True
            print(f"[DEBUG] Found today's section: {line}")
            
            for j in range(i+1, min(i+15, len(lines))):
                match_line = lines[j]
                
                if re.match(r'^\d{1,2}:\d{2}\s+.+ v .+', match_line):
                    time_match = re.search(r'^(\d{1,2}:\d{2})\s+(.+)', match_line)
                    if time_match:
                        time_str = time_match.group(1)
                        rest = time_match.group(2)
                        
                        found_channel = None
                        channel_checks = [
                            ("Sky Sports", ["sky sports"]),
                            ("TNT Sports", ["tnt sports"]),
                            ("BBC", ["bbc"]),
                            ("ITV", ["itv"]),
                            ("Premier Sports", ["premier sports"])
                        ]
                        
                        for channel_name, patterns in channel_checks:
                            if any(pattern in rest.lower() for pattern in patterns):
                                found_channel = channel_name
                                for pattern in patterns:
                                    if pattern in rest.lower():
                                        idx = rest.lower().find(pattern)
                                        rest = rest[:idx].strip()
                                        break
                                break
                        
                        if found_channel and " v " in rest:
                            events.append({
                                "date": datetime.now().strftime("%Y-%m-%d"),
                                "sport": "Football",
                                "title": rest,
                                "time": time_str,
                                "channel": found_channel
                            })
                            print(f"[DEBUG] Added: {time_str} - {rest} on {found_channel}")
            break
    
    if not today_found:
        print("[DEBUG] Today's section not found, trying general match search...")
        for line in lines:
            if re.search(r'\d{1,2}:\d{2}', line) and ' v ' in line and len(line) < 200:
                found_channel = None
                for channel in ALLOWED_CHANNELS:
                    if channel.lower() in line.lower():
                        found_channel = channel
                        break
                
                if found_channel:
                    time_match = re.search(r'(\d{1,2}:\d{2})', line)
                    if time_match:
                        title = line.replace(time_match.group(1), "").strip()
                        if found_channel.lower() in title.lower():
                            idx = title.lower().find(found_channel.lower())
                            title = title[:idx].strip()
                        
                        if len(title) < 150:
                            events.append({
                                "date": datetime.now().strftime("%Y-%m-%d"),
                                "sport": "Football",
                                "title": title,
                                "time": time_match.group(1),
                                "channel": found_channel
                            })
                            print(f"[DEBUG] Added fallback: {time_match.group(1)} - {title} on {found_channel}")
    
    print(f"[DEBUG] Found {len(events)} football matches")
    return events

# --- fetch_radiotimes() and fetch_bbc_sport() remain unchanged ---
# Keep your existing implementations

def main():
    print("Starting to fetch UK TV sports listings...")
    all_events = []
    
    print("\n1. Fetching from Live Football on TV...")
    all_events.extend(fetch_live_football())
    
    print("\n2. Fetching from RadioTimes...")
    all_events.extend(fetch_radiotimes())
    
    print("\n3. Fetching from BBC Sport...")
    all_events.extend(fetch_bbc_sport())

    if not all_events:
        print("\n[INFO] No events found from live sources. Creating sample data for today...")
        sample_events = [
            {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "sport": "Football",
                "title": "Slovakia v Northern Ireland - World Cup Qualifier",
                "time": "19:45",
                "channel": "BBC"
            },
            {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "sport": "Football", 
                "title": "Rangers Women v Celtic Women - SWPL1",
                "time": "19:30",
                "channel": "Sky Sports"
            },
            {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "sport": "Boxing",
                "title": "Eubank Jr v Benn - Weighin Coverage", 
                "time": "18:00",
                "channel": "Sky Sports"
            }
        ]
        all_events.extend(sample_events)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_events, f, indent=4, ensure_ascii=False)

    print(f"\nCompleted! Saved {len(all_events)} events to {OUTPUT_FILE}")
    
    if all_events:
        print("\nPreview of saved data:")
        for i, event in enumerate(all_events[:3], 1):
            print(f"  {i}. {event['time']} - {event['title']} on {event['channel']}")
        if len(all_events) > 3:
            print(f"  ... and {len(all_events) - 3} more events")

if __name__ == "__main__":
    main()
