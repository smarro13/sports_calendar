import json
import time
from playwright.sync_api import sync_playwright

BASE_URL = "https://www.thesportsdb.com/browse_tv/?c=united_kingdom"
OUTPUT_FILE = "uk_tv_shows.json"

def scrape_shows():
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")  # wait until page fully loads

        # Get all show cards
        show_cards = page.query_selector_all("div.col-lg-3")
        for card in show_cards:
            # Title is inside <h5>
            h5 = card.query_selector("h5")
            title = h5.inner_text().strip() if h5 else None

            # Link is inside <a>
            a_tag = card.query_selector("a")
            link = a_tag.get_attribute("href") if a_tag else None
            if link and not link.startswith("http"):
                link = "https://www.thesportsdb.com" + link

            broadcast_time = None
            if link:
                # Visit detail page to get broadcast time
                try:
                    page.goto(link)
                    page.wait_for_load_state("networkidle")
                    span = page.query_selector("span.text-success")
                    broadcast_time = span.inner_text().strip() if span else None
                    time.sleep(0.5)  # polite delay
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
