from playwright.sync_api import sync_playwright
from datetime import datetime
import json
import time

URL = "https://www.wheresthematch.com/"
OUTPUT_FILE = "wtm_tv_sports_today.json"

def scrape_wtm():
    results = []
    today = datetime.now().strftime("%A %d %B %Y")  # e.g., 'Thursday 14 November 2025'

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width":1920,"height":1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.goto(URL)
        page.wait_for_load_state("networkidle")
        time.sleep(5)  # allow JS to render

        # Wait for live schedule table
        try:
            page.wait_for_selector("div.schedule-item", timeout=30000)
        except:
            print("Timed out waiting for schedule. Saving debug screenshot.")
            page.screenshot(path="wtm_debug.png", full_page=True)
            browser.close()
            return results

        rows = page.query_selector_all("div.schedule-item")

        for row in rows:
            date_el = row.query_selector("span.schedule-date")
            date_text = date_el.inner_text().strip() if date_el else today
            if today not in date_text:
                continue

            sport_el = row.query_selector("span.schedule-sport")
            sport = sport_el.inner_text().strip() if sport_el else "Unknown"

            title_el = row.query_selector("span.schedule-event")
            time_el = row.query_selector("span.schedule-time")
            channel_el = row.query_selector("span.schedule-channel")

            if title_el and time_el and channel_el:
                channel = channel_el.inner_text().strip()
                # Filter for Sky/TNT only if needed
                if "Sky Sports" not in channel and "TNT Sports" not in channel:
                    continue

                results.append({
                    "date": date_text,
                    "sport": sport,
                    "title": title_el.inner_text().strip(),
                    "time": time_el.inner_text().strip(),
                    "channel": channel
                })

        # Save debug screenshot if no results
        if not results:
            page.screenshot(path="wtm_debug.png", full_page=True)

        browser.close()
    return results

def main():
    events = scrape_wtm()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=4, ensure_ascii=False)
    print(f"Saved {len(events)} events to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
