import json
from playwright.sync_api import sync_playwright

url = "https://www.atptour.com/en/rankings/singles?rankRange=0-5000"


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


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(url, wait_until="domcontentloaded")
    handle_cookies(page)

    # Find all <a> elements using XPath
    anchors = page.locator(
        "//table[@class='mega-table desktop-table non-live']/tbody/tr[@class='lower-row']/td[@class='player bold heavy large-cell']/ul/li[@class='name center']/a"
    )

    players_lk = page.locator('//table[@class="mega-table desktop-table non-live"]/tbody/tr')
    players = []

    for i in range(1,players_lk.count()):
        a = page.locator(f"//table[@class='mega-table desktop-table non-live']/tbody/tr[@class='lower-row'][{i}]/td[@class='player bold heavy large-cell']/ul/li[@class='name center']/a")
        a.scroll_into_view_if_needed()
        link = a.get_attribute("href")
        name = a.inner_text().strip()
        if link and name:
            players.append({
                "name": name,
                "url": "https://www.atptour.com" + link
            })

    with open("../data/players.json", "w", encoding="utf-8") as f:
        json.dump(players, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved {len(players)} players to players.json")

    browser.close()