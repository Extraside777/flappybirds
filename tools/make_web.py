#!/usr/bin/env python3
"""
Збирає веб-версію гри в одну папку -- для застосунку на iPhone (iphone/, Capacitor) або для сайту.

    python tools/make_web.py [папка] [--admob iphone/admob.properties]

Що робить:
  * копіює web/ (index.html, js/) і assets/ (спрайти, музика, звуки, шрифт; без assets/images --
    це вихідні картинки для tools/) у папку (за замовчуванням iphone/www)
  * малює іконки: icon.png (180x180, для браузера) і app-icon-1024.png (для iPhone; без прозорості --
    так вимагає Apple), та splash-2732.png -- екран запуску кольору неба
  * з --admob -- записує ID рекламного блоку з файлу в js/admob-ids.js
Для перевірки в браузері збирати не треба: python tools/serve_web.py бере все прямо з web/ і assets/.
"""
import importlib.util
import os
import shutil
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPLASH_COLOR = (78, 192, 234)     # -- як фон екрана завантаження в web/index.html (#4ec0ea)


def android_icons():
    """tools/make_android_icons.py -- там уже є, як намалювати небо, землю і пташку"""
    spec = importlib.util.spec_from_file_location("icons", os.path.join(ROOT, "tools", "make_android_icons.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def icon(size):
    """квадратна іконка без прозорості: ті самі пропорції, що в адаптивної іконки Android (108 dp)"""
    m = android_icons()
    img = m.scene(size, round(size * 34 / 108))
    m.place_bird(img, m.bird_art(), round(size * 50 / 108), size * 0.47)
    return img.convert("RGB")


def read_props(path):
    out = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                out[key.strip()] = value.strip()
    return out


def main():
    args = sys.argv[1:]
    admob = None
    if "--admob" in args:
        i = args.index("--admob")
        admob = read_props(args[i + 1])
        del args[i:i + 2]
    out = os.path.abspath(args[0]) if args else os.path.join(ROOT, "iphone", "www")

    if os.path.exists(out):
        shutil.rmtree(out)
    shutil.copytree(os.path.join(ROOT, "web"), out)
    for name in ("sprites", "music", "sounds", "fonts"):
        shutil.copytree(os.path.join(ROOT, "assets", name), os.path.join(out, "assets", name))

    icon(180).save(os.path.join(out, "icon.png"), optimize=True)
    icon(1024).save(os.path.join(out, "app-icon-1024.png"), optimize=True)
    Image.new("RGB", (2732, 2732), SPLASH_COLOR).save(os.path.join(out, "splash-2732.png"), optimize=True)

    if admob:
        testing = admob.get("testing", "true").lower() == "true"
        with open(os.path.join(out, "js", "admob-ids.js"), "w", encoding="utf-8") as fh:
            fh.write("// -- згенеровано tools/make_web.py з admob.properties\n"
                     f"export const REWARDED_ID = '{admob['rewardedId']}';\n"
                     f"export const TESTING = {'true' if testing else 'false'};\n")
    print("готово ->", out)


if __name__ == "__main__":
    main()
