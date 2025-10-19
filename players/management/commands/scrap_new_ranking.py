from django.core.management.base import BaseCommand
from playwright.sync_api import sync_playwright
from lxml import etree
import json
import re
import os
from django.core import management

class Command(BaseCommand):
    help = "Scrape latest ATP ranking and save as JSON"

    def handle(self, *args, **options):
        def clean_name(raw):
            return re.sub(r'\s+', ' ', raw).strip()

        def safe_text(el_list):
            return el_list[0].strip() if el_list else '-'

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()

            page.set_viewport_size({"width": 1920, "height": 1080})
            page.goto("https://www.atptour.com/en/rankings/singles?rankRange=0-5000")

            # Accept cookies
            page.wait_for_selector('#onetrust-reject-all-handler')
            page.click('#onetrust-reject-all-handler')

            html = page.content()
            browser.close()

        dom = etree.HTML(html)

        rows = dom.xpath(
            '//table[contains(@class, "mega-table desktop-table non-live")]/tbody/tr[@class="lower-row"]'
        )

        current_date = safe_text(dom.xpath('//select[@id="dateWeek-filter"]/option[1]/text()'))
        current_date = current_date.replace('.', '-') if current_date else "unknown-date"

        player_data = []

        for row in rows:
            rank = safe_text(row.xpath('.//td[contains(@class,"rank")]/text()'))
            rank_change = safe_text(row.xpath('.//li[@class="rank"]//span[contains(@class,"rank-")]/text()'))
            player = safe_text(row.xpath('.//td[contains(@class,"player")]//li[contains(@class,"name")]//a/span/text()'))
            age = safe_text(row.xpath('.//td[contains(@class,"age")]/text()'))
            points = safe_text(row.xpath('.//td[contains(@class,"points")]//a/text()'))
            points = points.replace(",", "") if points else None
            earn_drop = safe_text(row.xpath('.//td[contains(@class,"pointsMove")]/text()'))
            tournaments = safe_text(row.xpath('.//td[contains(@class,"tourns")]/text()'))
            dropping = safe_text(row.xpath('.//td[contains(@class,"drop")]/text()'))
            next_best = safe_text(row.xpath('.//td[contains(@class,"best")]/text()'))
            flag_href = row.xpath('.//li[contains(@class,"avatar")]//use/@href')
            country = flag_href[0].split("-")[-1] if flag_href else None

            player_data.append({
                "Rank": rank,
                "Rank_change": rank_change,
                "Player": clean_name(player) if player else None,
                "Age": age,
                "Points": points,
                "Earn_Drop": earn_drop,
                "Tournaments": tournaments,
                "Dropping": dropping,
                "Next Best": next_best,
                "Country": country
            })

        # Save safely
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        save_dir = os.path.join(project_root, "data", "rankings", "ATP")
        os.makedirs(save_dir, exist_ok=True)
        output_path = os.path.join(save_dir, f"{current_date}.json")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(player_data, f, ensure_ascii=False, indent=2)

        self.stdout.write(self.style.SUCCESS(
            f"✅ Scraped {len(player_data)} players into {output_path}"
        ))

        self.stdout.write(self.style.NOTICE("📥 Importing latest ranking into DB..."))
        management.call_command("import_tennis_data", add_latest_ranking=os.path.join(save_dir))
        self.stdout.write(self.style.SUCCESS("✅ Latest ranking imported successfully."))