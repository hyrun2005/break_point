from django import forms
from players.models import Player

SURFACE_CHOICES = [
    ("surface_Hard", "Hard"),
    ("surface_Clay", "Clay"),
    ("surface_Grass", "Grass"),
    ("Carpet", "Carpet")
]

ROUND_CHOICES = [
    (1, "Round of 128"),
    (2, "Round of 64"),
    (3, "Round of 32"),
    (4, "Quarterfinal"),
    (5, "Semifinal"),
    (6, "Final"),
]

TOURNEY_LEVEL_CHOICES = [
    ("tourney_level_A", "ATP"),
    ("tourney_level_D", "Davis Cup"),
    ("tourney_level_F", "Tour Finals"),
    ("tourney_level_G", "Grand Slam"),
    ("tourney_level_M", "Masters"),
    ("tourney_level_O", "Olympics")
]

class PredictForm(forms.Form):
    player1 = forms.ModelChoiceField(queryset=Player.objects.all(), label="Player 1")
    player2 = forms.ModelChoiceField(queryset=Player.objects.all(), label="Player 2")
    tourney_level = forms.ChoiceField(choices=TOURNEY_LEVEL_CHOICES)
    player1_seed = forms.IntegerField(required=False, initial=0)
    player2_seed = forms.IntegerField(required=False, initial=0)
    best_of = forms.ChoiceField(choices=[(3, "Best of 3"), (5, "Best of 5")])
    round_encoded = forms.ChoiceField(choices=ROUND_CHOICES)
    surface = forms.ChoiceField(choices=SURFACE_CHOICES)
    draw_size = forms.IntegerField(initial=128)
