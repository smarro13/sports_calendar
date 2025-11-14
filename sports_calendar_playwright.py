from playwright.sync_api import sync_playwright
import json
from datetime import datetime
import time

URL = "https://www.skysports.com/watch/sport-on-sky"
OUTPUT_FILE = "sky_sports_today.json"

def scrape_sky_sports():
    results = []
    today = datetime.now().strftime("%a %d %B")  # e.g., 'Fri 14 November'

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.goto(URL)
        page.wait_for_load_state("networkidle", timeout=60000)
        time.sleep(5)  # allow JS to render

        # Scroll to trigger lazy loading
        page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
        time.sleep(2)

        # Wait for at least one timetable item
        try:
            page.wait_for_selector("div.timetable-item", timeout=60000)
        except:
            print("Timed out waiting for timetable items. Saving screenshot for debugging.")
            page.screenshot(path="sky_debug.png", full_page=True)
            browser.close()
            return results

        # Get timetable sections (sport headings)
        sections = page.query_selector_all("div.sdc-site-timetable__list > div.sdc-site-timetable__section")

        for section in sections:
            # Sport heading
            sport_el = section.query_selector("h3, h4")
            sport_name = sport_el.inner_text().strip() if sport_el else "Unknown"

            # Events in this section
            items = section.query_selector_all("div.timetable-item")
            for item in items:
                date_el = item.query_selector("span.timetable-event-date")
                date_text = date_el.inner_text().strip() if date_el else today

                if today not in date_text:
                    continue

                title_el = item.query_selector("span.timetable-event-title")
                time_el = item.query_selector("span.timetable-event-time")
                channel_el = item.query_selector("span.timetable-event-channel")

                if title_el and time_el and channel_el:
                    results.append({
                        "date": date_text,
                        "sport": sport_name,
                        "title": title_el.inner_text().strip(),
                        "time": time_el.inner_text().strip(),
                        "channel": channel_el.inner_text().strip()
                    })

        # Save screenshot for debugging
        if not results:
            page.screenshot(path="sky_debug.png", full_page=True)

        browser.close()
    return results

def main():
    events = scrape_sky_sports()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=4, ensure_ascii=False)
    print(f"Saved {len(events)} events to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
