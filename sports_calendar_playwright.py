from playwright.sync_api import sync_playwright
import json
import time
from datetime import datetime

URL = "https://www.skysports.com/watch/sport-on-sky"
OUTPUT_FILE = "sky_sports_today.json"

def scrape_sky_sports():
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.goto(URL)
        page.wait_for_load_state("networkidle", timeout=20000)
        time.sleep(3)  # allow JS content to load

        # Grab all date headings
        date_headers = page.query_selector_all("h2")
        for date_h in date_headers:
            date_text = date_h.inner_text().strip()

            # Only scrape today's date
            today_str = datetime.now().strftime("%a %d %B")  # e.g., 'Fri 14 November'
            if today_str not in date_text:
                continue

            # Get next sibling elements until next h2 (next date)
            sibling = date_h.next_sibling
            while sibling:
                tag_name = sibling.evaluate("el => el.tagName")
                if tag_name == "H2":
                    break  # next date reached
                # Sport section
                if tag_name in ["H3", "H4"]:
                    sport_name = sibling.inner_text().strip()
                    # Events under this sport
                    ul = sibling.next_sibling
                    if ul:
                        lis = ul.query_selector_all("li")
                        for li in lis:
                            title_el = li.query_selector("span.event-title")
                            time_el = li.query_selector("span.event-time")
                            channel_el = li.query_selector("span.event-channel")
                            if title_el and time_el and channel_el:
                                results.append({
                                    "date": date_text,
                                    "sport": sport_name,
                                    "title": title_el.inner_text().strip(),
                                    "time": time_el.inner_text().strip(),
                                    "channel": channel_el.inner_text().strip()
                                })
                sibling = sibling.next_sibling

        browser.close()
    return results

def main():
    events = scrape_sky_sports()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=4, ensure_ascii=False)
    print(f"Saved {len(events)} events to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
