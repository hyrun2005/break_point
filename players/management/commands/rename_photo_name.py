import os
from django.conf import settings
from players.models import Player


def renaming():
    old_folder = os.path.join(settings.BASE_DIR, 'players/commands/media')
    new_folder = os.path.join(settings.MEDIA_ROOT, "players/photos")
    os.makedirs(new_folder, exist_ok=True)

    for filename in os.listdir(old_folder):
        name, ext = os.path.splitext(filename)
        try:
            name = name.replace("_", " ")
            player = Player.objects.get(name__iexact=name.strip())
        except Player.DoesNotExist:
            print(f"❌ Not found {filename}")
            continue

        old_path = os.path.join(old_folder, filename)
        new_filename = f"{player.id}{ext.lower()}"
        new_rel = f"players/photos/{new_filename}"
        new_path = os.path.join(new_folder, new_filename)

        os.rename(old_path, new_path)

        player.photo = new_rel
        player.save()

        print(f"✅ {filename} → {new_filename}")
