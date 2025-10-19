from django.shortcuts import render
from django.utils.timezone import now
from datetime import timedelta
from .models import Ranking, Player, PlayerRecord


def home_page(request):
    return render(request, "players/home.html")

def atp_ranking(request):
    limit_options = ["50", "100", "200", "500", "all"]

    selected_limit = request.GET.get("limit", "100")
    selected_date = request.GET.get("date")

    available_dates = (
        Ranking.objects.order_by("-date")
        .values_list("date", flat=True)
        .distinct()
    )

    if not selected_date:
        latest_date = available_dates.first()
    else:
        latest_date = selected_date

    rankings = Ranking.objects.filter(date=latest_date).select_related("player").order_by("rank")

    if selected_limit != "all":
        try:
            selected_limit = int(selected_limit)
            rankings = rankings[:selected_limit]
        except ValueError:
            pass

    context = {
        "rankings": rankings,
        "ranking_date": latest_date,
        "available_dates": available_dates,
        "selected_limit": selected_limit,
        "limit_options": limit_options
    }
    return render(request, "players/atp_ranking.html", context)


