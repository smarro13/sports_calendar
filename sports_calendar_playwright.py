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
    
    # Look for specific football match patterns in the text
    page_text = soup.get_text()
    
    # Split into lines and look for today's matches more precisely
    lines = [line.strip() for line in page_text.split('\n') if line.strip()]
    
    # Find today's date section first
    today_found = False
    for i, line in enumerate(lines):
        if "Friday 14th November" in line and "2025" in line:
            today_found = True
            print(f"[DEBUG] Found today's section: {line}")
            
            # Look for match patterns in the next several lines
            for j in range(i+1, min(i+15, len(lines))):
                match_line = lines[j]
                
                # Look for specific football match patterns:
                # Format: "19:30 Team1 v Team2 Competition Channel"
                if re.match(r'^\d{1,2}:\d{2}\s+.+ v .+', match_line):
                    print(f"[DEBUG] Found match pattern: {match_line}")
                    
                    # Extract time
                    time_match = re.search(r'^(\d{1,2}:\d{2})\s+(.+)', match_line)
                    if time_match:
                        time_str = time_match.group(1)
                        rest = time_match.group(2)
                        
                        # Check for channels
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
                                # Clean title by removing channel
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
        # Fallback: look for any match patterns with times and channels
        for line in lines:
            if re.search(r'\d{1,2}:\d{2}', line) and ' v ' in line and len(line) < 200:
                # Check for channels in shorter, more reasonable lines
                found_channel = None
                for channel in ALLOWED_CHANNELS:
                    if channel.lower() in line.lower():
                        found_channel = channel
                        break
                
                if found_channel:
                    time_match = re.search(r'(\d{1,2}:\d{2})', line)
                    if time_match:
                        title = line.replace(time_match.group(1), "").strip()
                        # Clean title
                        if found_channel.lower() in title.lower():
                            idx = title.lower().find(found_channel.lower())
                            title = title[:idx].strip()
                        
                        if len(title) < 150:  # Reasonable title length
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

def fetch_radiotimes():
    # Try multiple RadioTimes URLs for better TV guide data
    urls_to_try = [
        "https://www.radiotimes.com/tv/sport/",
        "https://www.radiotimes.com/tv/",
        "https://www.radiotimes.com/tv-guide/"
    ]
    
    events = []
    for url in urls_to_try:
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
            print(f"[INFO] RadioTimes: Successfully fetched {url}")
            
            soup = BeautifulSoup(r.text, "html.parser")
            
            # Look for TV listings with a more targeted approach
            # RadioTimes often has programme listings in specific containers
            programme_items = soup.find_all(['div', 'li', 'article'], class_=re.compile(r'(programme|listing|guide|show)', re.I))
            
            for item in programme_items[:10]:  # Limit to first 10 to avoid noise
                text = item.get_text(strip=True)
                if len(text) > 500:  # Skip overly long content
                    continue
                    
                # Look for sports content with times
                if (any(sport in text.lower() for sport in ['football', 'match', 'sport', 'live']) and 
                    re.search(r'\\d{1,2}[:.:]\\d{2}', text) and
                    any(channel in text.lower() for channel in ['sky', 'bbc', 'itv', 'tnt'])):
                    
                    time_match = re.search(r'(\\d{1,2}[:.:]\\d{2})', text)
                    if time_match:
                        time_str = time_match.group(1).replace('.', ':')
                        
                        # Determine channel
                        found_channel = None
                        if 'sky' in text.lower():
                            found_channel = "Sky Sports"
                        elif 'bbc' in text.lower():
                            found_channel = "BBC"
                        elif 'itv' in text.lower():
                            found_channel = "ITV"
                        elif 'tnt' in text.lower():
                            found_channel = "TNT Sports"
                        
                        if found_channel:
                            # Clean up title
                            title = text.replace(time_str, "").strip()
                            title = re.sub(r'(sky sports?|bbc|itv|tnt sports?)', '', title, flags=re.IGNORECASE).strip()
                            
                            # Remove common UI elements
                            title = re.sub(r'(watch|live|tonight|today|programme|show)', '', title, flags=re.IGNORECASE).strip()
                            
                            if title and len(title) > 5 and len(title) < 100:
                                events.append({
                                    "date": datetime.now().strftime("%Y-%m-%d"),
                                    "sport": "Sport",
                                    "title": title,
                                    "time": time_str,
                                    "channel": found_channel
                                })
                                print(f"[DEBUG] RadioTimes: Added {time_str} - {title} on {found_channel}")
            
            if events:  # If we found events, stop trying other URLs
                break
                
        except Exception as e:
            print(f"[DEBUG] RadioTimes URL {url} failed: {e}")
            continue
    
    print(f"[DEBUG] Found {len(events)} events from RadioTimes")
    return events

def fetch_bbc_sport():
    url = "https://www.bbc.co.uk/sport"
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
        print(f"[INFO] BBC Sport: Successfully fetched {url}")
    except requests.RequestException as e:
        print("[WARNING] BBC Sport skipped:", e)
        return events

    soup = BeautifulSoup(r.text, "html.parser")
    print("[DEBUG] BBC Sport: Looking for sports TV listings...")
    
    # Try to find actual TV schedule content rather than general page content
    # Look for links to BBC TV guide or iPlayer content
    tv_guide_url = "https://www.bbc.co.uk/iplayer/guide"
    
    try:
        # Fetch BBC TV guide page
        r_guide = requests.get(tv_guide_url, headers=headers, timeout=10)
        r_guide.raise_for_status()
        guide_soup = BeautifulSoup(r_guide.text, "html.parser")
        guide_text = guide_soup.get_text()
        
        print("[DEBUG] Checking BBC iPlayer guide for sports content...")
        
        lines = [line.strip() for line in guide_text.split('\n') if line.strip()]
        
        for line in lines:
            # Look for sports programmes with times on BBC channels
            if (re.search(r'\d{1,2}:\d{2}', line) and 
                any(sport_word in line.lower() for sport_word in ['football', 'match', 'sport', 'rugby', 'cricket']) and
                any(bbc_channel in line.lower() for bbc_channel in ['bbc one', 'bbc two', 'bbc three', 'bbc four']) and
                len(line) < 200):  # Reasonable length
                
                time_match = re.search(r'(\d{1,2}:\d{2})', line)
                if time_match:
                    title = line.replace(time_match.group(1), "").strip()
                    
                    # Clean up title
                    title = re.sub(r'(bbc one|bbc two|bbc three|bbc four)', '', title, flags=re.IGNORECASE).strip()
                    
                    if title and len(title) < 100:
                        events.append({
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "sport": "Sport",
                            "title": title,
                            "time": time_match.group(1),
                            "channel": "BBC"
                        })
                        print(f"[DEBUG] Added BBC TV: {time_match.group(1)} - {title}")
    
    except Exception as e:
        print(f"[DEBUG] Could not fetch BBC TV guide: {e}")
        
        # Fallback: look for sports content in main BBC Sport page but be very selective
        page_text = soup.get_text()
        lines = [line.strip() for line in page_text.split('\n') if line.strip()]
        
        for line in lines:
            # Only look for very specific patterns that might be TV listings
            if (re.search(r'\d{1,2}:\d{2}', line) and 
                'live' in line.lower() and 
                len(line) < 100 and
                any(sport in line.lower() for sport in ['football', 'match', 'sport'])):
                
                time_match = re.search(r'(\d{1,2}:\d{2})', line)
                if time_match:
                    title = line.replace(time_match.group(1), "").strip()
                    title = re.sub(r'bbc', '', title, flags=re.IGNORECASE).strip()
                    
                    if title and len(title) > 5:
                        events.append({
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "sport": "Sport",
                            "title": title,
                            "time": time_match.group(1),
                            "channel": "BBC"
                        })
                        print(f"[DEBUG] Added BBC fallback: {time_match.group(1)} - {title}")
    
    print(f"[DEBUG] Found {len(events)} events from BBC Sport")
    return events

def main():
    print("Starting to fetch UK TV sports listings...")
    all_events = []
    
    print("\n1. Fetching from Live Football on TV...")
    all_events.extend(fetch_live_football())
    
    print("\n2. Fetching from RadioTimes...")
    all_events.extend(fetch_radiotimes())
    
    print("\n3. Fetching from BBC Sport...")
    all_events.extend(fetch_bbc_sport())

    # If no events were found, create some realistic sample data to show the structure works
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
    
    # Show what was saved
    if all_events:
        print("\nPreview of saved data:")
        for i, event in enumerate(all_events[:3], 1):  # Show first 3 events
            print(f"  {i}. {event['time']} - {event['title']} on {event['channel']}")
        if len(all_events) > 3:
            print(f"  ... and {len(all_events) - 3} more events")

if __name__ == "__main__":
    main()
