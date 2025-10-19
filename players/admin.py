from django.contrib import admin
from .models import Player, PlayerStat, PlayerRecord, Ranking


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ("name", "id", "country", "birth_date", "career_high_rank", "career_high_rank_date")
    search_fields = ("name", "country", "birthplace")
    list_filter = ("country", "turned_pro")
    ordering = ("name",)


@admin.register(PlayerStat)
class PlayerStatAdmin(admin.ModelAdmin):
    list_display = ("player", "aces", "double_faults", "first_serve_pct", "first_serve_points_won",
                    "second_serve_points_won", "return_points_won", "total_points_won")
    search_fields = ("player__name",)


@admin.register(PlayerRecord)
class PlayerRecordAdmin(admin.ModelAdmin):
    list_display = ("player", "season", "rank", "move", "wl_record", "titles", "prize_money")
    search_fields = ("player__name",)
    list_filter = ("season",)


from django.contrib.admin import DateFieldListFilter

@admin.register(Ranking)
class RankingSnapshotAdmin(admin.ModelAdmin):
    list_display = ("date", "player", "rank", "rank_change", "points", "tournaments", "country")
    search_fields = ("player__name", "country")
    list_filter = ("country",)
    date_hierarchy = "date"   # 👈 adds navigation by year → month → day
    ordering = ("-date", "rank")

