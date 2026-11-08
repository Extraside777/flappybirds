#!/usr/bin/env python3
"""
Версія гри для Steam: копія ПК-гри в папці steam/ -- без кнопки «монети за рекламу».

Запуск (з кореня проєкту):
    python tools/make_steam.py

Що робить:
  * копіює src/ (без __pycache__) і assets/ (без assets/images -- це вихідні картинки для tools/, грі вони
    не потрібні) у steam/
  * у steam/src/edition.py ставить AD_BUTTON = False -- кнопки реклами в меню нема
  * збереження гравця (save.json, settings.json) не копіює -- у Steam-версії гра почнеться з нуля
Після змін у грі просто запустіть скрипт ще раз -- папка steam/ збереться наново.
"""
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "steam")
MARK = os.path.join(OUT, ".made_by_make_steam")   # -- щоб не стерти чужу папку steam/

if os.path.exists(OUT):
    if not os.path.exists(MARK):
        raise SystemExit(f"{OUT} вже є, і її зробив не цей скрипт -- перейменуйте її або видаліть самі")
    shutil.rmtree(OUT)

shutil.copytree(os.path.join(ROOT, "src"), os.path.join(OUT, "src"),
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
shutil.copytree(os.path.join(ROOT, "assets"), os.path.join(OUT, "assets"),
                ignore=lambda folder, names: ["images"] if os.path.samefile(folder, os.path.join(ROOT, "assets"))
                else [])
shutil.copy2(os.path.join(ROOT, "requirements.txt"), OUT)

with open(os.path.join(OUT, "src", "edition.py"), "w", encoding="utf-8") as fh:
    fh.write("# -- збірка для Steam (tools/make_steam.py): без кнопки «монети за рекламу»\n"
             "AD_BUTTON = False\n")

with open(os.path.join(OUT, "README.txt"), "w", encoding="utf-8") as fh:
    fh.write("Flappy Bird -- версія для Steam (без кнопки «монети за рекламу»).\n"
             "Зібрано з основного проєкту скриптом tools/make_steam.py -- міняйте гру там, а цю папку\n"
             "збирайте наново.\n\n"
             "Запуск:\n"
             "    pip install -r requirements.txt\n"
             "    python src/main.py\n")
open(MARK, "w").close()
print("готово ->", OUT)
