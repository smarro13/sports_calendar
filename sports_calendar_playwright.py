from playwright.sync_api import sync_playwright
import json
import time

BASE_URL = "https://www.thesportsdb.com/browse_tv/?c=united_kingdom"
OUTPUT_FILE = "uk_tv_shows.json"

def scrape_shows():
    results = []
    with sync_playwright() as p:
        # Launch Chromium in headless mode
        browser = p.chromium.launch(headless=True)
        # Set a common user-agent to reduce bot detection
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.goto(BASE_URL)
        # Wait for network to be idle (all JS loaded)
        page.wait_for_load_state("networkidle", timeout=20000)
        time.sleep(3)  # small buffer for rendering

        # Select all show cards
        page.wait_for_selector("div.card", timeout=20000)
        show_cards = page.query_selector_all("div.card")
        for card in show_cards:
            # Title
            h5 = card.query_selector("h5")
            title = h5.inner_text().strip() if h5 else None

            # Link
            a_tag = card.query_selector("a")
            link = a_tag.get_attribute("href") if a_tag else None
            if link and not link.startswith("http"):
                link = "https://www.thesportsdb.com" + link

            # Broadcast time
            broadcast_time = None
            if link:
                try:
                    page.goto(link)
                    page.wait_for_load_state("networkidle", timeout=15000)
                    time.sleep(1)
                    span = page.query_selector("span.text-success")
                    broadcast_time = span.inner_text().strip() if span else None
                except Exception:
                    broadcast_time = None

            if title and link:
                results.append({
                    "title": title,
                    "link": link,
                    "broadcast_time": broadcast_time
                })

        browser.close()
    return results

def main():
    shows = scrape_shows()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(shows, f, indent=4, ensure_ascii=False)
    print(f"Saved {len(shows)} shows to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
