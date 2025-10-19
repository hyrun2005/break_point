from django.core.management.base import BaseCommand
from players.models import Player
import os


class Command(BaseCommand):
    help = "Import player photos into Player.photo field"

    def handle(self, *args, **options):
        base_folder = "data/media/photos_by_name"  # adjust your actual folder path here

        # Iterate through photos
        count = 0
        for filename in os.listdir(base_folder):
            if not filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                continue

            name = os.path.splitext(filename)[0].replace("_", " ").title()
            try:
                player = Player.objects.get(name=name)
                player.photo.name = f"players/photos_by_name/{filename}"
                player.save(update_fields=["photo"])
                count += 1
                self.stdout.write(self.style.SUCCESS(f"✅ Added photo for {name}"))
            except Player.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"⚠️ No player found for {name}"))

        self.stdout.write(self.style.SUCCESS(f"\n✅ Imported {count} photos total"))
