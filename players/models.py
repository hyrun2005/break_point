import uuid
from django.db import models
from datetime import date
import random
import string


import os
from django.db import models
from django.utils.text import slugify

import random
import string
from datetime import date
from django.db import models


def generate_player_id():
    """Generate a unique 5-character alphanumeric ID."""
    while True:
        new_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        # avoid collision if by chance already exists
        if not Player.objects.filter(id=new_id).exists():
            return new_id


def player_name_photo_path(instance, filename):
    ext = filename.split('.')[-1]
    clean_name = instance.name.replace(" ", "_")
    return f"players/photos_by_name/{clean_name}.{ext}"


class Player(models.Model):
    id = models.CharField(
        primary_key=True,
        max_length=5,
        default=generate_player_id,  # 👈 auto-generate unique ID
        editable=False,
        unique=True
    )
    name = models.CharField(max_length=100)
    url = models.URLField(blank=True, null=True)
    photo = models.ImageField(upload_to=player_name_photo_path, blank=True, null=True)

    # Bio / Overview
    birth_date = models.DateField(blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    birthplace = models.CharField(max_length=150, blank=True, null=True)
    plays = models.CharField(max_length=100, blank=True, null=True)
    coach = models.CharField(max_length=200, blank=True, null=True)
    turned_pro = models.IntegerField(blank=True, null=True)

    # Physical
    weight_lbs = models.IntegerField(blank=True, null=True)
    weight_kg = models.IntegerField(blank=True, null=True)
    height_cm = models.IntegerField(blank=True, null=True)
    height_feet = models.IntegerField(blank=True, null=True)
    height_inches = models.IntegerField(blank=True, null=True)

    # Career high rank
    career_high_rank = models.IntegerField(blank=True, null=True)
    career_high_rank_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.id})"

    @property
    def age(self):
        if not self.birth_date:
            return None
        today = date.today()
        return (
            today.year
            - self.birth_date.year
            - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        )

    def get_career_record(self):
        return self.records.filter(season="Career").first()

    def get_ytd_record(self):
        return self.records.filter(season="YTD").first()


class PlayerStat(models.Model):
    player = models.OneToOneField(Player, on_delete=models.CASCADE, related_name="stats")

    # Serve stats
    aces = models.IntegerField(blank=True, null=True)
    double_faults = models.IntegerField(blank=True, null=True)
    first_serve_pct = models.FloatField(blank=True, null=True)
    first_serve_points_won = models.FloatField(blank=True, null=True)
    second_serve_points_won = models.FloatField(blank=True, null=True)
    break_points_faced = models.IntegerField(blank=True, null=True)
    break_points_saved = models.FloatField(blank=True, null=True)
    service_games_played = models.IntegerField(blank=True, null=True)
    service_games_won = models.FloatField(blank=True, null=True)
    total_service_points_won = models.FloatField(blank=True, null=True)

    # Return stats
    first_serve_return_points_won = models.FloatField(blank=True, null=True)
    second_serve_return_points_won = models.FloatField(blank=True, null=True)
    break_points_opportunities = models.IntegerField(blank=True, null=True)
    break_points_converted = models.FloatField(blank=True, null=True)
    return_games_played = models.IntegerField(blank=True, null=True)
    return_games_won = models.FloatField(blank=True, null=True)
    return_points_won = models.FloatField(blank=True, null=True)
    total_points_won = models.FloatField(blank=True, null=True)


class PlayerRecord(models.Model):
    SEASON_CHOICES = [("YTD", "Year To Date"), ("Career", "Career")]
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="records")
    season = models.CharField(max_length=10, choices=SEASON_CHOICES)

    rank = models.IntegerField(blank=True, null=True)
    move = models.CharField(max_length=10, blank=True, null=True)
    wl_record = models.CharField(max_length=20, blank=True, null=True)
    titles = models.IntegerField(blank=True, null=True)
    prize_money = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        unique_together = ("player", "season")



class Ranking(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="rankings")
    date = models.DateField()

    rank = models.IntegerField(blank=True, null=True)
    rank_change = models.CharField(max_length=10, blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)
    points = models.IntegerField(blank=True, null=True)
    earn_drop = models.CharField(max_length=10, blank=True, null=True)
    tournaments = models.IntegerField(blank=True, null=True)
    dropping = models.CharField(max_length=10, blank=True, null=True)
    next_best = models.CharField(max_length=10, blank=True, null=True)
    country = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        unique_together = ("player", "date")
        ordering = ["date", "rank"]
