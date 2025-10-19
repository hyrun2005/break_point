from django.core.management.base import BaseCommand
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
import time, os, json, base64
from django.conf import settings


USER_DATA_DIR = os.path.join(settings.BASE_DIR, "user_data")
MEDIA_DIR = os.path.join(settings.MEDIA_ROOT, "players", "photos_by_name")
PLAY_TIMEOUT = 30 * 1000  # ms

os.makedirs(MEDIA_DIR, exist_ok=True)


def humanize(page):
    page.mouse.move(100, 300)
    time.sleep(0.2)
    page.mouse.move(200, 350)
    time.sleep(0.15)
    page.mouse.click(200, 350)
    time.sleep(0.3)
    page.keyboard.type("Hello", delay=120)
    time.sleep(0.5)
    page.evaluate("window.scrollTo({top: 600, behavior: 'smooth'})")
    time.sleep(0.6)
    page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
    time.sleep(0.4)


def wait_for_cf_clear(page, timeout_seconds=60):
    end = time.time() + timeout_seconds
    while time.time() < end:
        try:
            if page.query_selector("div.player_image") or page.url.startswith("https://www.atptour.com/"):
                text = page.inner_text("body")
                if "Verifying you are human" not in text and "Checking your browser" not in text:
                    return True
        except Exception:
            pass
        time.sleep(1)
    return False


def fetch_player_image_via_canvas(page, profile_url, save_path):
    page.goto(profile_url, wait_until="domcontentloaded")
    try:
        page.wait_for_selector("div.player_image img", timeout=PLAY_TIMEOUT)
    except PWTimeout:
        print("Image selector not found within timeout.")
        return False

    img = page.query_selector("div.player_image img")
    data_url = page.evaluate(
        """(img) => {
            return new Promise((resolve, reject) => {
                try {
                    const canvas = document.createElement('canvas');
                    canvas.width = img.naturalWidth || img.width;
                    canvas.height = img.naturalHeight || img.height;
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(img, 0, 0);
                    resolve(canvas.toDataURL("image/png"));
                } catch (e) { reject(e.toString()); }
            });
        }""",
        img
    )
    _, b64 = data_url.split(",", 1)
    with open(save_path, "wb") as f:
        f.write(base64.b64decode(b64))
    print("Saved", save_path)
    return True


class Command(BaseCommand):
    help = "Scrape and save ATP player photos using Playwright"

    def handle(self, *args, **options):
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR,
                headless=False,
                args=["--disable-blink-features=AutomationControlled"]
            )
            page = browser.new_page()

            target = "https://www.atptour.com/"
            page.goto(target)

            humanize(page)
            print("If you see a Cloudflare verification, please solve it manually.")
            cleared = wait_for_cf_clear(page, timeout_seconds=120)
            if not cleared:
                print("⚠️ Cloudflare check not cleared automatically.")

            # Path to players.json
            players_json_path = os.path.join(settings.BASE_DIR, "data", "players.json")
            with open(players_json_path, "r", encoding="utf-8") as f:
                players = json.load(f)

            for pinfo in players:
                name = pinfo["name"].replace(" ", "_")
                url = pinfo["url"]
                save_path = os.path.join(MEDIA_DIR, f"{name}.png")
                if os.path.exists(save_path):
                    print("Skipping, exists:", save_path)
                    continue

                try:
                    success = fetch_player_image_via_canvas(page, url, save_path)
                    if not success:
                        print("Failed to fetch for", name)
                except Exception as e:
                    print("Error for", name, e)

            browser.close()
