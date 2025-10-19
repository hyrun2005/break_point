from django.shortcuts import render
from django.db.models import OuterRef, Subquery
from .forms import PredictForm
from players.models import Player, Ranking
import pandas as pd
from .ml_utils import predict_match, model_columns
from django.http import JsonResponse


def predict(request):
    # Annotate players with their latest rank and points
    latest_rank = Ranking.objects.filter(player=OuterRef("pk")).order_by("-date")
    players = (
        Player.objects.annotate(
            latest_rank_value=Subquery(latest_rank.values("rank")[:1]),
            latest_points=Subquery(latest_rank.values("points")[:1]),
        )
        .filter(latest_rank_value__lte=300)
        .order_by("name")
    )

    # 🎯 Handle AJAX POST request for prediction
    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":
        form = PredictForm(request.POST)
        if not form.is_valid():
            errors = [f"{field}: {', '.join(errs)}" for field, errs in form.errors.items()]
            return JsonResponse({"error": " | ".join(errors)}, status=400)

        try:
            p1 = form.cleaned_data["player1"]
            p2 = form.cleaned_data["player2"]
            tourney_level = form.cleaned_data["tourney_level"]
            best_of = int(form.cleaned_data["best_of"])
            round_encoded = int(form.cleaned_data["round_encoded"])
            surface = form.cleaned_data["surface"]
            draw_size = form.cleaned_data["draw_size"]

            # Build model input
            input_raw = pd.DataFrame(columns=model_columns)
            input_raw.loc[0] = 0

            # 🧮 Player info
            p1_rank = p1.rankings.order_by("-date").first()
            p2_rank = p2.rankings.order_by("-date").first()

            p1_right_hand = 1 if "Right" in (p1.plays or "") else 0
            p2_right_hand = 1 if "Right" in (p2.plays or "") else 0

            input_raw.at[0, "draw_size"] = draw_size
            input_raw.at[0, "Player1_rank"] = p1_rank.rank if p1_rank else 999
            input_raw.at[0, "Player2_rank"] = p2_rank.rank if p2_rank else 999
            input_raw.at[0, "Player1_rank_points"] = p1_rank.points if p1_rank else 0
            input_raw.at[0, "Player2_rank_points"] = p2_rank.points if p2_rank else 0
            input_raw.at[0, "Player1_ht"] = p1.height_cm or 180
            input_raw.at[0, "Player2_ht"] = p2.height_cm or 180
            input_raw.at[0, "Player1_age"] = p1.age or 25
            input_raw.at[0, "Player2_age"] = p2.age or 25
            input_raw.at[0, "Player1_hand_R"] = p1_right_hand
            input_raw.at[0, "Player2_hand_R"] = p2_right_hand
            input_raw.at[0, "Player1_seed"] = form.cleaned_data["player1_seed"] or 0
            input_raw.at[0, "Player2_seed"] = form.cleaned_data["player2_seed"] or 0
            input_raw.at[0, "Player1_entry_Direct"] = 1
            input_raw.at[0, "Player2_entry_Direct"] = 1

            input_raw.at[0, "best_of"] = best_of
            input_raw.at[0, "round_encoded"] = round_encoded
            input_raw.at[0, surface] = 1
            input_raw.at[0, tourney_level] = 1

            # ⚙️ Engineered features
            if p1_rank and p2_rank:
                input_raw.at[0, "rank_diff"] = p1_rank.rank - p2_rank.rank
                input_raw.at[0, "points_diff"] = p1_rank.points - p2_rank.points
                input_raw.at[0, "relative_rank_strength"] = (
                    (p1_rank.rank - p2_rank.rank) / (p1_rank.rank + p2_rank.rank)
                )

            input_raw.at[0, "height_diff"] = (p1.height_cm or 180) - (p2.height_cm or 180)
            input_raw.at[0, "h2h_p1_winrate"] = 0.5

            # 🔮 Predict
            win_prob = predict_match(input_raw)

            result = {
                "p1": p1.name,
                "p2": p2.name,
                "p1_win": f"{win_prob * 100:.2f}%",
                "p2_win": f"{(1 - win_prob) * 100:.2f}%",
            }
            return JsonResponse(result)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({"error": str(e)}, status=500)

    # 🧱 Normal GET render
    form = PredictForm()
    players_with_data = []
    for p in players:
        latest_ranking = p.rankings.order_by("-date").first()
        stats = getattr(p, "stats", None)
        record = p.get_career_record() if hasattr(p, "get_career_record") else None

        players_with_data.append({
            "id": p.id,
            "name": p.name,
            "photo": p.photo.url if p.photo else None,
            "rank": latest_ranking.rank if latest_ranking else "-",
            "points": latest_ranking.points if latest_ranking else "-",
            "stats": {
                "aces": stats.aces if stats and stats.aces is not None else "-",
            } if stats else None,
            "career_record": {
                "wl_record": record.wl_record if record else "-",
                "prize_money": record.prize_money if record else "-",
            } if record else None,
        })

    # ✅ define match fields for the template
    match_fields = [
        ("Tourney Level", "tourney_level"),
        ("Surface", "surface"),
        ("Round", "round_encoded"),
        ("Best Of", "best_of"),
        ("Draw Size", "draw_size"),
        ("Player 1 Seed", "player1_seed"),
        ("Player 2 Seed", "player2_seed"),
    ]

    context = {
        "form": form,
        "players": players_with_data,
        "tourney_levels": form.fields["tourney_level"].choices,
        "surfaces": form.fields["surface"].choices,
        "rounds": form.fields["round_encoded"].choices,
        "best_of": form.fields["best_of"].choices,
        "match_fields": match_fields,
    }
    return render(request, "predictions/predict.html", context)