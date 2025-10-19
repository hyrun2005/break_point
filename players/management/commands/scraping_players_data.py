import json
import re
from datetime import datetime
from playwright.sync_api import sync_playwright


def apply_stealth(page):
    page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
        Object.defineProperty(navigator, 'userAgent', {
            get: () => "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/124.0.0.0 Safari/537.36"
        });
    """)


# --- Normalize data and fill with "-" if missing ---
def normalize_name(name: str) -> str:
    if not name:
        return name
    return name.strip().title()


def normalize_player_data(player_data: dict) -> dict:
    overview = player_data.get("Overview", {})
    ytd = player_data.get("YTD", {})
    career = player_data.get("Career", {})

    cleaned = dict(player_data)

    # Birth date
    birth_date = "-"
    if "Age" in overview:
        age_match = re.search(r"\((\d{4}/\d{2}/\d{2})\)", overview["Age"])
        if age_match:
            birth_date = datetime.strptime(age_match.group(1), "%Y/%m/%d").date()
    cleaned["birth_date"] = birth_date

    # Weight
    weight_lbs, weight_kg = "-", "-"
    if "Weight" in overview:
        w_match = re.match(r"(\d+)\s*lbs\s*\((\d+)kg\)", overview["Weight"])
        if w_match:
            weight_lbs = int(w_match.group(1))
            weight_kg = int(w_match.group(2))
    cleaned["weight_lbs"] = weight_lbs
    cleaned["weight_kg"] = weight_kg

    # Height
    height_feet, height_inches, height_cm = "-", "-", "-"
    if "Height" in overview:
        h_match = re.match(r"(\d+)'\s*(\d+)", overview["Height"])
        cm_match = re.search(r"\((\d+)cm\)", overview["Height"])
        if h_match and cm_match:
            height_feet = int(h_match.group(1))
            height_inches = int(h_match.group(2))
            height_cm = int(cm_match.group(1))
    cleaned["height_feet"] = height_feet
    cleaned["height_inches"] = height_inches
    cleaned["height_cm"] = height_cm

    # Career High Rank cleanup
    def extract_rank(block: dict, prefix: str):
        rank_val, rank_date = "-", "-"
        for key in list(block.keys()):
            if key.startswith("Career High Rank"):
                val = block[key]
                date_match = re.search(r"\(([\d.]+)\)", key)
                if date_match:
                    rank_val = int(val) if val.isdigit() else "-"
                    try:
                        rank_date = datetime.strptime(date_match.group(1), "%Y.%m.%d").date()
                    except Exception:
                        rank_date = "-"
                del block[key]
        cleaned[f"{prefix}_high_rank"] = rank_val
        cleaned[f"{prefix}_high_rank_date"] = rank_date

    extract_rank(career, "career")

    return cleaned


def handle_cookies(page):
    try:
        # Wait up to 5 seconds for cookie popup
        page.wait_for_selector("#onetrust-accept-btn-handler", timeout=5000)
        btn = page.locator("#onetrust-accept-btn-handler")
        if btn.is_visible():
            btn.click()
            page.wait_for_timeout(1200)  # wait for overlay to disappear
            print("✅ Accepted cookies")
    except Exception:
        print("ℹ️ No cookie banner found (probably already accepted)")


# --- Scraper for a single player ---
def scrape_player(page, url):
    page.goto(url, wait_until="domcontentloaded")

    # Name
    try:
        name = page.locator("//div[@class='player_name']/span").inner_text().strip()
    except Exception:
        name = "-"

    # Overview
    overview = {}
    overview_items = page.locator("ul.pd_left li, ul.pd_right li")
    for i in range(overview_items.count()):
        spans = overview_items.nth(i).locator("span")
        if spans.count() >= 2:
            key = spans.nth(0).inner_text().strip()
            val = spans.nth(1).inner_text().strip()
            overview[key] = val

    stats_data, ytd_data, career_data = {}, {}, {}


    try:
        stats_tab = page.locator("//a[@href='player-stats']")
        if stats_tab.count() > 0:
            stats_tab.first.click()
            page.wait_for_selector("//div[@class='statistics_content']", timeout=5000)

            sections = page.locator("//div[@class='statistics_content']/div")
            for i in range(sections.count()):
                section = sections.nth(i)
                title = section.locator("h3").inner_text().strip()
                stats = {}
                items = section.locator("li.stats_items")
                for j in range(items.count()):
                    spans = items.nth(j).locator("span")
                    if spans.count() >= 2:
                        key = spans.nth(0).inner_text().strip()
                        val = spans.nth(1).inner_text().strip()
                        stats[key] = val
                stats_data[title] = stats


            # YTD
            ytd_stats = page.locator("//div[@class='player-stats-details'][1]/div")
            for i in range(ytd_stats.count()):
                stat_block = ytd_stats.nth(i)
                label = stat_block.locator(".stat-label")
                if label.count() > 0:
                    key = label.inner_text().strip()
                    value = stat_block.inner_text().replace(key, "").strip()
                    ytd_data[key] = value if value else "-"

            # Career
            career_stats = page.locator("//div[@class='player-stats-details'][2]/div")
            for i in range(career_stats.count()):
                stat_block = career_stats.nth(i)
                label = stat_block.locator(".stat-label")
                if label.count() > 0:
                    key = label.inner_text().strip()
                    value = stat_block.inner_text().replace(key, "").strip()
                    career_data[key] = value if value else "-"
    except Exception:
        pass

    player_data = {
        "name": normalize_name(name),
        "url": url,
        "Overview": overview if overview else "-",
        "Stats": stats_data if stats_data else "-",
        "YTD": ytd_data if ytd_data else "-",
        "Career": career_data if career_data else "-"
    }
    return normalize_player_data(player_data)


# --- Main loop ---
with open("../data/players.json", "r", encoding="utf-8") as f:
    players_list = json.load(f)

all_players_data = []

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        args=["--disable-blink-features=AutomationControlled"]
    )
    page = browser.new_page()
    apply_stealth(page)

    for i, player in enumerate(players_list):
        print(f"Scraping {player['name']} ...")
        try:
            page.goto(player["url"], wait_until="domcontentloaded")

            if i == 0:
                handle_cookies(page)

            data = scrape_player(page, player["url"])
            all_players_data.append(data)

        except Exception as e:
            print(f"⚠️ Failed for {player['name']} ({player['url']}): {e}")
            all_players_data.append({
                "name": normalize_name(player["name"]),
                "url": player["url"],
                "Overview": "-",
                "Stats": "-",
                "YTD": "-",
                "Career": "-",
                "error": str(e)
            })

        # Save progress
        with open("../data/player_stats/players_data.json", "w", encoding="utf-8") as f:
            json.dump(all_players_data, f, ensure_ascii=False, indent=2, default=str)

    browser.close()