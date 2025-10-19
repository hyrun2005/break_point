import os
import shutil
from django.conf import settings
from players.models import Player

def copy_photos_from_id_to_name():
    old_folder = os.path.join(settings.MEDIA_ROOT, "players", "photos")
    new_folder = os.path.join(settings.MEDIA_ROOT, "players", "photos_by_name")
    os.makedirs(new_folder, exist_ok=True)

    for player in Player.objects.all():
        # search for file with id (any extension)
        found_file = None
        for ext in [".jpg", ".jpeg", ".png", ".webp"]:
            path = os.path.join(old_folder, f"{player.id}{ext}")
            if os.path.exists(path):
                found_file = path
                break

        if not found_file:
            print(f"⚠️ No file found for {player.name} (id={player.id})")
            continue

        # new file name: Name_Surname.png (always png extension)
        new_filename = f"{player.name.replace(' ', '_')}.png"
        new_path = os.path.join(new_folder, new_filename)

        shutil.copy2(found_file, new_path)
        print(f"✅ Copied {found_file} → {new_path}")
