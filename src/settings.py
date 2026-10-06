import copy
import json
import os

# -- налаштування гравця
DEFAULTS = {
    "lang": "en",          # -- "en" або "uk"
    "window": "auto",      # -- "auto", "fullscreen" або масштаб вікна ("1.5")
    "menu_music": 0.5,     # -- повзунки 0..1
    "game_music": 0.5,
    "sfx": 0.6,
}

# -- прогрес: рекорд і монетки (потім сюди ж -- куплені скіни)
PROGRESS_DEFAULTS = {
    "best": 0,
    "coins": 0,
    "games": 0,
    "skin": "classic",          # -- якою пташкою граємо
    "owned": ["classic"],       # -- куплені пташки
    "trail": "none",            # -- який шлейф тягнеться за пташкою
    "owned_trails": ["none"],   # -- куплені шлейфи
}


def load(path, defaults=DEFAULTS):
    data = copy.deepcopy(defaults)
    try:
        with open(path, encoding="utf-8") as fh:
            saved = json.load(fh)
        for key, default in defaults.items():
            value = saved.get(key)
            if isinstance(default, float) and isinstance(value, (int, float)):
                data[key] = max(0.0, min(1.0, float(value)))
            elif isinstance(default, int) and isinstance(value, int) and not isinstance(value, bool):
                data[key] = max(0, value)
            elif isinstance(default, str) and isinstance(value, str):
                data[key] = value
            elif isinstance(default, list) and isinstance(value, list):
                data[key] = [v for v in value if isinstance(v, str)]
    except (OSError, ValueError, AttributeError):
        pass                       # -- нема файлу або він битий -- беремо стандартні
    return data


def save(path, data):
    try:
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
        os.replace(tmp, path)      # -- щоб файл не побився, якщо гру закриють посеред запису
    except OSError:
        pass
