"""
Іконки Android-версії (android/app/src/main/res/mipmap-*) зі спрайтів гри:
небо + земля на фоні, класична пташка спереду. Адаптивна іконка (Android 8+) -- два шари,
для старіших -- звичайна квадратна з заокругленими кутами.

    python tools/make_android_icons.py
"""
import os
from PIL import Image, ImageDraw

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPRITES = os.path.join(BASE, "assets", "sprites")
RES = os.path.join(BASE, "android", "app", "src", "main", "res")
DENSITIES = {"mdpi": 1, "hdpi": 1.5, "xhdpi": 2, "xxhdpi": 3, "xxxhdpi": 4}

BIRD_FRAME_W, BIRD_ART_PX = 42, 2


def bird_art():
    """перший кадр класичної пташки, по одному пікселю на художній піксель"""
    sheet = Image.open(os.path.join(SPRITES, "bird", "bird_sheet.png")).convert("RGBA")
    frame = sheet.crop((0, 0, BIRD_FRAME_W, sheet.height))
    frame = frame.crop(frame.getbbox())
    return frame.resize((frame.width // BIRD_ART_PX, frame.height // BIRD_ART_PX), Image.NEAREST)


def scene(size, ground_h):
    """небо (градієнт з bg_sky.png) і смуга землі знизу"""
    sky = Image.open(os.path.join(SPRITES, "bg_sky.png")).convert("RGBA")
    img = sky.crop((0, 200, sky.width, sky.height)).resize((size, size), Image.BILINEAR)
    ground = Image.open(os.path.join(SPRITES, "layers", "bg_ground.png")).convert("RGBA")
    k = ground_h / ground.height
    strip = ground.resize((max(1, round(ground.width * k)), ground_h), Image.NEAREST)
    img.alpha_composite(strip.crop((0, 0, size, ground_h)), (0, size - ground_h))
    return img


def place_bird(img, art, width, cy):
    k = max(1, width // art.width)
    bird = art.resize((art.width * k, art.height * k), Image.NEAREST)
    img.alpha_composite(bird, ((img.width - bird.width) // 2, round(cy - bird.height / 2)))


def main():
    art = bird_art()
    for name, d in DENSITIES.items():
        folder = os.path.join(RES, "mipmap-" + name)
        os.makedirs(folder, exist_ok=True)

        # -- адаптивна: 108dp, видно круг/квадрат ~72dp посередині
        full = round(108 * d)
        scene(full, round(34 * d)).save(os.path.join(folder, "ic_launcher_background.png"))
        fg = Image.new("RGBA", (full, full), (0, 0, 0, 0))
        place_bird(fg, art, round(50 * d), full * 0.47)
        fg.save(os.path.join(folder, "ic_launcher_foreground.png"))

        # -- звичайна: 48dp з заокругленими кутами
        size = round(48 * d)
        icon = scene(size, round(12 * d))
        place_bird(icon, art, round(34 * d), size * 0.45)
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, size - 1, size - 1), radius=round(9 * d), fill=255)
        icon.putalpha(mask)
        icon.save(os.path.join(folder, "ic_launcher.png"))

    folder = os.path.join(RES, "mipmap-anydpi-v26")
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "ic_launcher.xml"), "w", encoding="utf-8") as fh:
        fh.write('<?xml version="1.0" encoding="utf-8"?>\n'
                 '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
                 '    <background android:drawable="@mipmap/ic_launcher_background" />\n'
                 '    <foreground android:drawable="@mipmap/ic_launcher_foreground" />\n'
                 '</adaptive-icon>\n')
    print("іконки готові:", RES)


if __name__ == "__main__":
    main()
