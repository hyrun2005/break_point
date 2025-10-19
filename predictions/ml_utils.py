import pandas as pd
import joblib
import os
import json
from django.conf import settings  # ✅ use Django BASE_DIR

# Absolute paths
MODEL_PATH = os.path.join(settings.BASE_DIR, "predictions", "data", "tennis_model_v1.pkl")
FEATURES_PATH = os.path.join(settings.BASE_DIR, "predictions", "data", "model_features.json")

# ✅ Load model and features once
model = joblib.load(MODEL_PATH)
with open(FEATURES_PATH, "r") as f:
    model_columns = json.load(f)


def swap_players(row_df):
    swapped = row_df.copy()

    for col in row_df.columns:
        if "Player1_" in col:
            swapped[col.replace("Player1_", "TEMP_")] = row_df[col]
        elif "Player2_" in col:
            swapped[col.replace("Player2_", "Player1_")] = row_df[col]

    for col in row_df.columns:
        if "TEMP_" in col:
            new_col = col.replace("TEMP_", "Player2_")
            swapped[new_col] = swapped[col]

    temp_cols = [c for c in swapped.columns if c.startswith("TEMP_")]
    swapped.drop(columns=temp_cols, inplace=True)

    # Flip directional features
    for feat in ["rank_diff", "points_diff", "height_diff", "relative_rank_strength"]:
        if feat in swapped.columns:
            swapped.at[0, feat] = -swapped.at[0, feat]

    if "h2h_p1_winrate" in swapped.columns:
        swapped.at[0, "h2h_p1_winrate"] = 1.0 - swapped.at[0, "h2h_p1_winrate"]

    return swapped


def predict_match(input_raw):
    input_raw = input_raw.reindex(columns=model_columns, fill_value=0)

    if input_raw.at[0, "Player1_rank"] > input_raw.at[0, "Player2_rank"]:
        swapped = swap_players(input_raw.copy())
        probs = model.predict_proba(swapped)[0]
        win_prob = 1 - probs[1]
    else:
        probs = model.predict_proba(input_raw)[0]
        win_prob = probs[1]

    return win_prob
