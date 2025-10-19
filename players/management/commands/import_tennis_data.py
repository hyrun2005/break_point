import os
import json
from datetime import datetime, date

from django.core.management.base import BaseCommand
from django.db import transaction

from players.models import Player, PlayerStat, PlayerRecord, Ranking



# ---------- Helpers ----------
def normalize_name(name: str) -> str:
    if not name:
        return None
    return name.strip().title()


def to_int(value):
    if value in ("", "-", None):
        return None
    try:
        # strip commas, %, and trailing 'T'
        cleaned = str(value).replace(",", "").replace("%", "").strip()
        if cleaned.endswith("T"):
            cleaned = cleaned[:-1]
        return int(cleaned)
    except ValueError:
        return None


def to_float(value):
    if value in ("", "-", None):
        return None
    try:
        return float(str(value).replace("%", "").replace(",", "").strip())
    except ValueError:
        return None


def to_date(value):
    if value in ("", "-", "", None):
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def calculate_age(birth_date, on_date=None):
    if not birth_date:
        return None
    if not on_date:
        on_date = date.today()
    return (
        on_date.year
        - birth_date.year
        - ((on_date.month, on_date.day) < (birth_date.month, birth_date.day))
    )


# ---------- Import players + stats ----------
def import_players(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        players = json.load(f)

    for row in players:
        # Safe dicts
        overview = row.get("Overview") or {}
        if not isinstance(overview, dict):
            overview = {}

        stats = row.get("Stats") or {}
        if not isinstance(stats, dict):
            stats = {}

        serve = stats.get("Serve") or {}
        if not isinstance(serve, dict):
            serve = {}

        ret = stats.get("Return") or {}
        if not isinstance(ret, dict):
            ret = {}

        ytd = row.get("YTD") or {}
        if not isinstance(ytd, dict):
            ytd = {}

        career = row.get("Career") or {}
        if not isinstance(career, dict):
            career = {}

        # ---- Player ----
        player, _ = Player.objects.update_or_create(
            name=normalize_name(row["name"]),
            defaults={
                "url": row.get("url"),
                "birth_date": to_date(row.get("birth_date")),
                "country": overview.get("Country"),
                "birthplace": overview.get("Birthplace"),
                "plays": overview.get("Plays"),
                "coach": overview.get("Coach"),
                "turned_pro": to_int(overview.get("Turned pro")),
                "weight_lbs": to_int(row.get("weight_lbs")),
                "weight_kg": to_int(row.get("weight_kg")),
                "height_cm": to_int(row.get("height_cm")),
                "height_feet": to_int(row.get("height_feet")),
                "height_inches": to_int(row.get("height_inches")),
                "career_high_rank": to_int(row.get("career_high_rank")),
                "career_high_rank_date": to_date(row.get("career_high_rank_date")),
            }
        )

        # ---- Stats ----
        PlayerStat.objects.update_or_create(
            player=player,
            defaults={
                "aces": to_int(serve.get("Aces")),
                "double_faults": to_int(serve.get("Double Faults")),
                "first_serve_pct": to_float(serve.get("1st Serve")),
                "first_serve_points_won": to_float(serve.get("1st Serve Points Won")),
                "second_serve_points_won": to_float(serve.get("2nd Serve Points Won")),
                "break_points_faced": to_int(serve.get("Break Points Faced")),
                "break_points_saved": to_float(serve.get("Break Points Saved")),
                "service_games_played": to_int(serve.get("Service Games Played")),
                "service_games_won": to_float(serve.get("Service Games Won")),
                "total_service_points_won": to_float(serve.get("Total Service Points Won")),

                "first_serve_return_points_won": to_float(ret.get("1st Serve Return Points Won")),
                "second_serve_return_points_won": to_float(ret.get("2nd Serve Return Points Won")),
                "break_points_opportunities": to_int(ret.get("Break Points Opportunities")),
                "break_points_converted": to_float(ret.get("Break Points Converted")),
                "return_games_played": to_int(ret.get("Return Games Played")),
                "return_games_won": to_float(ret.get("Return Games Won")),
                "return_points_won": to_float(ret.get("Return Points Won")),
                "total_points_won": to_float(ret.get("Total Points Won")),
            }
        )

        # ---- Records ----
        PlayerRecord.objects.update_or_create(
            player=player, season="YTD",
            defaults={
                "rank": to_int(ytd.get("Rank")),
                "move": ytd.get("Move") if ytd.get("Move") != "-" else None,
                "wl_record": ytd.get("W-L"),
                "titles": to_int(ytd.get("Titles")),
                "prize_money": ytd.get("Prize Money"),
            }
        )

        PlayerRecord.objects.update_or_create(
            player=player, season="Career",
            defaults={
                "rank": None,
                "move": None,
                "wl_record": career.get("W-L"),
                "titles": to_int(career.get("Titles")),
                "prize_money": career.get("Prize Money Singles & Doubles Combined"),
            }
        )


# ---------- Import ranking snapshots ----------
def import_ranking_file(filepath):
    filename = os.path.basename(filepath)
    snapshot_date = datetime.strptime(filename.replace(".json", ""), "%Y-%m-%d").date()

    with open(filepath, "r", encoding="utf-8") as f:
        rankings = json.load(f)

    with transaction.atomic():
        for row in rankings:
            player, _ = Player.objects.get_or_create(
                name=normalize_name(row["Player"]),
                defaults={"country": row.get("Country")}
            )

            Ranking.objects.update_or_create(
                player=player,
                date=snapshot_date,
                defaults={
                    "rank": to_int(row.get("Rank")),
                    "rank_change": row.get("Rank_change") if row.get("Rank_change") != "-" else None,
                    "age": calculate_age(player.birth_date, snapshot_date),
                    "points": to_int(row.get("Points")),
                    "earn_drop": row.get("Earn_Drop") if row.get("Earn_Drop") != "-" else None,
                    "tournaments": to_int(row.get("Tournaments")),
                    "dropping": row.get("Dropping") if row.get("Dropping") != "-" else None,
                    "next_best": row.get("Next Best") if row.get("Next Best") != "-" else None,
                    "country": row.get("Country"),
                }
            )


def import_rankings(folder):
    for filename in os.listdir(folder):
        if filename.endswith(".json"):
            import_ranking_file(os.path.join(folder, filename))


# ---------- Management command ----------
class Command(BaseCommand):
    help = "Import players and rankings from JSON"

    def add_arguments(self, parser):
        parser.add_argument("--players", type=str, help="Path to players JSON file")
        parser.add_argument("--rankings", type=str, help="Path to rankings folder")
        parser.add_argument("--clear", action="store_true", help="Delete old data before import")
        parser.add_argument("--add_latest_ranking", type=str, help="Path to rankings folder")

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("Clearing old data...")
            Ranking.objects.all().delete()
            PlayerRecord.objects.all().delete()
            PlayerStat.objects.all().delete()
            Player.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Old data deleted."))

        if options["players"]:
            self.stdout.write(f"Importing players from {options['players']}...")
            import_players(options["players"])
            self.stdout.write(self.style.SUCCESS("Players imported."))

        if options["rankings"]:
            self.stdout.write(f"Importing rankings from {options['rankings']}...")
            import_rankings(options["rankings"])
            self.stdout.write(self.style.SUCCESS("Rankings imported."))

        if options["add_latest_ranking"]:
            self.stdout.write(f"Importing rankings from {options['add_latest_ranking']}...")

            folder = options["add_latest_ranking"]
            self.stdout.write(f"Looking for latest ranking file in {folder}...")

            # find all json files
            json_files = [f for f in os.listdir(folder) if f.endswith(".json")]
            if not json_files:
                self.stdout.write(self.style.ERROR("No ranking JSON files found."))
                return

            # sort by date parsed from filename
            json_files.sort(key=lambda x: datetime.strptime(x.replace(".json", ""), "%Y-%m-%d"), reverse=True)
            latest_file = json_files[0]
            latest_path = os.path.join(folder, latest_file)

            self.stdout.write(f"Importing latest ranking: {latest_file}")
            import_ranking_file(latest_path)
            self.stdout.write(self.style.SUCCESS("Latest ranking imported."))
