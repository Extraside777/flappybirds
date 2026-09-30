#!/usr/bin/env python3
"""
Додаткові спрайти: труби, пташка, українські версії написів/кнопок і тексти екрану налаштувань.

Запуск (з кореня проєкту, ПІСЛЯ tools/make_sprites.py):
    pip install pillow numpy
    python tools/make_extra_sprites.py

Що робить:
  * малює трубу (тіло + капелюшок) у піксель-арт стилі
  * малює пташку: 3 кадри помаху крилами
  * перемальовує кнопки меню для обох мов одним шрифтом і розміром (PLAY/ГРАТИ, SHOP/МАГАЗИН,
    RECORD/РЕКОРД з кубком, MENU/МЕНЮ), перегенеровує кадри блику
    (заголовок FLAPPY BIRD -- назва гри, не перекладається)
  * малює тексти для екрану налаштувань і GAME OVER обома мовами
  * робить «порожню» панель (кнопку без іконки і тексту) -- гра розтягує її під будь-який розмір
  * малює монетку, що крутиться, і генерує звук «дзинь» для неї
  * ріже скіни пташок для магазину з картинок у assets/images/skins (див. SKIN_SOURCES)
  * пише assets/sprites/extra.json -- його читає гра

Кирилиці в assets/fonts/OutlineStyleRegular.ttf немає, тому букви малюються шрифтом
Segoe UI Black (є в Windows), без згладжування і збільшені -- виходять «пікселі».
"""
import json
import math
import os
import struct
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "sprites")
FONT_CANDIDATES = [
    r"C:\Windows\Fonts\seguibl.ttf",
    r"C:\Windows\Fonts\ariblk.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]

OUTLINE = (45, 16, 40)
WHITE = (255, 255, 255)
CREAM = (255, 232, 196)
SHADOW = (0, 60, 200)      # такий самий колір тіні, як у tools/make_sprites.py

with open(os.path.join(OUT, "manifest.json"), encoding="utf-8") as fh:
    base_manifest = json.load(fh)

extra = {}


# --------------------------------------------------------------------------
# утиліти
# --------------------------------------------------------------------------
def save(name, arr, sub=""):
    folder = os.path.join(OUT, sub)
    os.makedirs(folder, exist_ok=True)
    Image.fromarray(np.ascontiguousarray(arr.astype(np.uint8))).save(os.path.join(folder, name), optimize=True)
    return f"{sub}/{name}" if sub else name


def load(rel):
    return np.array(Image.open(os.path.join(OUT, rel)).convert("RGBA"))


def dilate(mask, r=1, square=True):
    """Розширення маски без scipy: квадрат (піксельні кути) або хрест (заокруглені)."""
    out = mask.copy()
    for _ in range(r):
        m = out.copy()
        m[1:] |= out[:-1]
        m[:-1] |= out[1:]
        m[:, 1:] |= out[:, :-1]
        m[:, :-1] |= out[:, 1:]
        if square:
            m[1:, 1:] |= out[:-1, :-1]
            m[1:, :-1] |= out[:-1, 1:]
            m[:-1, 1:] |= out[1:, :-1]
            m[:-1, :-1] |= out[1:, 1:]
        out = m
    return out


def upscale(a, k):
    return np.repeat(np.repeat(a, k, axis=0), k, axis=1)


def trim(rgba):
    ys, xs = np.nonzero(rgba[..., 3] > 0)
    return rgba[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def shine_frames(rgba, n=14, band=13, strength=0.62, slope=0.55):
    """Те саме, що в tools/make_sprites.py: блик, що пробігає по кнопці."""
    h, w = rgba.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    diag = xx + slope * yy
    span = w + slope * h + 2 * band
    solid = rgba[..., 3] == 255
    frames = []
    for i in range(n):
        centre = -band + span * i / (n - 1)
        a = np.clip(1 - np.abs(diag - centre) / band, 0, 1) ** 1.4 * strength
        a = a * solid
        f = rgba.copy()
        f[..., :3] = np.clip(f[..., :3] + (255 - f[..., :3]) * a[..., None], 0, 255)
        frames.append(f)
    return frames


# --------------------------------------------------------------------------
# піксельний текст
# --------------------------------------------------------------------------
FONT_PATH = next(p for p in FONT_CANDIDATES if os.path.exists(p))
_font_cache = {}


def font_for_cap(cap):
    """Підбирає розмір шрифту, щоб висота великої літери була cap «пікселів»."""
    if cap not in _font_cache:
        best = None
        for size in range(6, 80):
            f = ImageFont.truetype(FONT_PATH, size)
            b = f.getbbox("Н")
            if b[3] - b[1] >= cap:
                best = f
                break
        _font_cache[cap] = best
    return _font_cache[cap]


ACCENT_ROOM = 0.36   # -- місце над великими літерами (Й, Ї) у частках cap
DESC_ROOM = 0.30     # -- місце під рядком (хвостики Д, Ц, Щ)


def glyph_mask(text, cap, track=1, bold=0):
    """
    Маска тексту в «художніх» пікселях (без згладжування). Повертає (маска, y верху великих літер).
    bold -- на скільки пікселів потовщити штрихи вправо (дрібний текст інакше надто тонкий).
    """
    f = font_for_cap(cap)
    top = f.getbbox("Н")[1]
    w = int(sum(f.getlength(c) for c in text) + (track + bold) * len(text) + 20)
    top_pad = cap + 4                      # -- запас зверху, щоб влізли надрядкові знаки
    h = int(f.size * 1.6 + 10) + top_pad
    m = np.zeros((h, w), bool)
    x = 4
    for c in text:
        im = Image.new("1", (w, h), 0)
        d = ImageDraw.Draw(im)
        d.fontmode = "1"
        d.text((round(x), top_pad), c, font=f, fill=1)
        g = np.array(im)
        for _ in range(bold):
            g[:, 1:] |= g[:, :-1]
        m |= g
        x += f.getlength(c) + track + bold
    ys, xs = np.nonzero(m)
    m = m[:, xs.min():xs.max() + 1]
    return m, top_pad + top


def pixel_text(text, cap, scale=1, outline=2, shade=0.62, shade_color=CREAM,
               drop=0, track=2, fill=WHITE, bold=0, fixed=False):
    """
    Текст у стилі гри: біла заливка, нижня частина кремова, темний заокруглений контур.
    cap -- висота великої літери, outline -- товщина контуру, drop -- м'яка синя тінь знизу
    (як у заголовка). Усе в «художніх» пікселях, scale -- у скільки разів їх збільшити.
    fixed -- однакова висота картинки для всіх написів з цим cap (базова лінія на одному місці),
    тоді підписи і цифри, вирівняні по центру, стоять рівно в рядок.
    """
    m, cap_top = glyph_mask(text, cap, track, bold)
    pad = outline + drop + 1
    m = np.pad(m, pad)
    cap_top += pad
    ol = dilate(m, outline, square=False) if outline else m
    h, w = m.shape
    rgba = np.zeros((h, w, 4), np.uint8)
    if drop:
        sh = np.zeros_like(ol)
        sh[drop:] = ol[:-drop]
        rgba[sh] = (*SHADOW, 100)
    rgba[ol] = (*OUTLINE, 255)
    rgba[m] = (*fill, 255)
    split = int(round(cap_top + cap * shade))
    low = m.copy()
    low[:split] = False
    rgba[low] = (*shade_color, 255)
    if fixed:
        y0 = cap_top - int(math.ceil(cap * ACCENT_ROOM)) - outline
        y1 = cap_top + cap + int(math.ceil(cap * DESC_ROOM)) + outline + drop
        rgba = rgba[y0:y1]
        xs = np.nonzero(rgba[..., 3].any(axis=0))[0]
        return upscale(rgba[:, xs.min():xs.max() + 1], scale)
    return trim(upscale(rgba, scale))


def paste(dst, src, x, y):
    """Альфа-накладання src на dst (обидва RGBA uint8)."""
    h, w = src.shape[:2]
    region = dst[y:y + h, x:x + w].astype(float)
    s = src.astype(float)
    a = s[..., 3:4] / 255
    region[..., :3] = s[..., :3] * a + region[..., :3] * (1 - a)
    region[..., 3:4] = np.maximum(region[..., 3:4], s[..., 3:4])
    dst[y:y + h, x:x + w] = region.astype(np.uint8)


# --------------------------------------------------------------------------
# 1. кнопки українською
# --------------------------------------------------------------------------
def erase_text(btn, x0, x1, y0, y1):
    """
    Стирає текст/іконку на кремовій панелі між x0 і x1.
    Колір панелі в кожному рядку беремо з вільних смужок по краях (x0..x0+5 і x1-5..x1),
    замальовуємо тільки ті пікселі, що від нього відрізняються (+ запас 2 px).
    """
    out = btn.copy()
    rgb = btn[..., :3].astype(int)
    ref = np.zeros((btn.shape[0], 3))
    for y in range(y0, y1):
        ref[y] = np.median(np.concatenate([rgb[y, x0:x0 + 6], rgb[y, x1 - 6:x1]]), axis=0)
    mask = np.zeros(btn.shape[:2], bool)
    mask[y0:y1, x0:x1] = np.abs(rgb[y0:y1, x0:x1] - ref[y0:y1, None]).max(axis=2) >= 16
    ys, xs = np.nonzero(mask)
    bbox = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
    fillm = dilate(mask, 2)
    fillm[:y0] = fillm[y1:] = False
    fillm[:, :x0] = fillm[:, x1:] = False
    for y in range(y0, y1):
        out[y, fillm[y], :3] = np.round(ref[y]).astype(np.uint8)
    return out, bbox


def widen(img, width, left=32, edge=32):
    """
    розтягує кнопку по ширині: ліва частина (з іконкою) і правий край як є,
    середина (вже порожня, без тексту) -- повтором одного стовпчика
    """
    h, w = img.shape[:2]
    if width == w:
        return img
    mid = np.repeat(img[:, left:left + 1], width - left - edge, axis=1)
    return np.concatenate([img[:, :left], mid, img[:, w - edge:]], axis=1)


def relabel(key, text, x0, cap, text_cx, src=None, icon=None, icon_x=None, folder="buttons", width=None):
    """
    Кнопка з новим написом. Стирається все від x0 до правої рамки (текст, а з icon -- і іконка).
    cap -- розмір літер, text_cx -- центр тексту по X (однаковий для всіх кнопок меню -- так рівно).
    src -- з якої кнопки брати основу (за замовчуванням key). width -- розширити кнопку до цієї ширини.
    """
    b = base_manifest["buttons"][src or key]
    fw, fh = b["fw"], b["fh"]
    btn = load(b["file"])[:, :fw]
    solid_rows = np.nonzero(btn[:, fw // 2, 3] == 255)[0]
    # внутрішня кремова частина: без рамки зверху/знизу
    y0, y1 = solid_rows.min() + 6, solid_rows.max() - 9
    clean, (tx0, ty0, tx1, ty1) = erase_text(btn, x0, fw - 22, y0, y1)
    cy = (ty0 + ty1) / 2
    if width:
        clean = widen(clean, width, left=x0)
        fw = width
    spr = pixel_text(text, cap, shade=0.6, fixed=True, track=BTN_TRACK)
    paste(clean, spr, int(round(text_cx - spr.shape[1] / 2)), int(round(cy - spr.shape[0] / 2)))
    if icon is not None:
        paste(clean, icon, int(icon_x - icon.shape[1] // 2), int(round(cy - icon.shape[0] / 2)))
    frames = shine_frames(clean)
    name = save(f"btn_{key}_sheet.png", np.concatenate(frames, axis=1), folder)
    return {**b, "file": name, "fw": int(fw)}


def fit_cap(words, width, max_cap):
    """найбільший розмір літер, з яким УСІ слова влазять у ширину"""
    cap = max_cap
    while cap > 10 and max(pixel_text(w, cap, fixed=True, track=BTN_TRACK).shape[1] for w in words) > width:
        cap -= 1
    return cap


# --------------------------------------------------------------------------
# 2. порожня панель (для екрану налаштувань, 9-slice)
# --------------------------------------------------------------------------
b = base_manifest["buttons"]["play"]
btn = load(b["file"])[:, :b["fw"]]
solid_rows = np.nonzero(btn[:, b["fw"] // 2, 3] == 255)[0]
panel, _ = erase_text(btn, 16, b["fw"] - 16, solid_rows.min() + 6, solid_rows.max() - 9)
extra["panel"] = {"file": save("panel.png", panel, "ui"), "slice": 22}

# --------------------------------------------------------------------------
# 2б. кубок і кнопка РЕКОРД (для обох мов)
# --------------------------------------------------------------------------
TROPHY = [
    "...KKKKKKKKKK...",
    "KKKKhYYYYYYdKKKK",
    "KYYKhYYYYYYdKYYK",
    "KY.KhYYYYYYdK.YK",
    "KY.KhYYYYYYdK.YK",
    ".KYKKhYYYYdKKYK.",
    "..KKKhYYYYdKKK..",
    "....KKhYYdKK....",
    "......KYdK......",
    "......KYdK......",
    ".....KKYdKK.....",
    "....KhYYYYdK....",
    "...KKKKKKKKKK...",
    "...KBbbbbbbbK...",
    "...KKKKKKKKKK...",
]
TROPHY_COLORS = {
    "K": OUTLINE, "Y": (255, 198, 40), "h": (255, 240, 150), "d": (220, 140, 24),
    "B": (196, 128, 80), "b": (150, 88, 52),
}


def pixel_map(rows, colors):
    a = np.zeros((len(rows), len(rows[0]), 4), np.uint8)
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            if c != ".":
                a[y, x] = (*colors[c], 255)
    return a


trophy = pixel_map(TROPHY, TROPHY_COLORS)
extra["trophy"] = {
    "small": save("trophy_small.png", upscale(trophy, 2), "ui"),
    "big": save("trophy_big.png", upscale(trophy, 4), "ui"),
}

# --------------------------------------------------------------------------
# 3. кнопки меню (обидві мови): один шрифт, один розмір, текст по одному центру
# --------------------------------------------------------------------------
BTN_TRACK = 1
BUTTON_WORDS = {
    "en": {"play": "PLAY", "shop": "SHOP", "record": "RECORD", "menu": "MENU"},
    "uk": {"play": "ГРАТИ", "shop": "МАГАЗИН", "record": "РЕКОРД", "menu": "МЕНЮ"},
}
MENU_BTN_W = 272          # -- кнопки меню ширші за оригінал (246), щоб «МАГАЗИН» влазив великими літерами
MENU_TEXT_X0 = 94         # -- текст починається після іконки...
MENU_TEXT_X1 = MENU_BTN_W - 24   # -- ...і закінчується перед правою рамкою
MENU_TEXT_CX = (MENU_TEXT_X0 + MENU_TEXT_X1) // 2
MENU_BTN_TEXT_CX = 139    # -- центр тексту для кнопки МЕНЮ (вона вужча)
_play = base_manifest["buttons"]["play"]
_menu_x = (base_manifest["screen"]["w"] - MENU_BTN_W) // 2

extra["buttons"] = {}
for lang, words in BUTTON_WORDS.items():
    cap = fit_cap([words["play"], words["shop"], words["record"]], MENU_TEXT_X1 - MENU_TEXT_X0, 22)
    kw = dict(folder=f"buttons/{lang}", width=MENU_BTN_W)
    out = {
        "play": relabel("play", words["play"], 92, cap, MENU_TEXT_CX, **kw),
        "shop": relabel("shop", words["shop"], 94, cap, MENU_TEXT_CX, **kw),
        # основа -- кнопка PLAY: стираємо і трикутник, і текст, малюємо кубок
        "record": relabel("record", words["record"], 20, cap, MENU_TEXT_CX, src="play",
                          icon=upscale(trophy, 3), icon_x=58, **kw),
        "menu": relabel("menu", words["menu"], 80, cap, MENU_BTN_TEXT_CX, folder=f"buttons/{lang}"),
    }
    for i, k in enumerate(("play", "shop", "record")):
        out[k].update({"x": _menu_x, "y": _play["y"] + 80 * i})
    extra["buttons"][lang] = out
    print(lang, "cap кнопок:", cap)

# --------------------------------------------------------------------------
# 4. тексти: GAME OVER, налаштування, рекорд
# --------------------------------------------------------------------------
TEXTS = {
    "en": {"game_over": "GAME OVER", "settings": "SETTINGS", "language": "LANGUAGE",
           "menu_music": "MENU MUSIC", "game_music": "GAME MUSIC", "sounds": "SOUNDS",
           "window_size": "WINDOW SIZE", "auto": "AUTO", "fullscreen": "FULL SCREEN",
           "score": "SCORE", "best": "BEST", "new_record": "NEW RECORD!",
           "coins": "COINS", "games": "GAMES PLAYED", "records": "RECORDS",
           "shop_title": "SHOP", "select": "SELECT", "selected": "SELECTED", "not_enough": "NOT ENOUGH COINS"},
    "uk": {"game_over": "КІНЕЦЬ ГРИ", "settings": "НАЛАШТУВАННЯ", "language": "МОВА",
           "menu_music": "МУЗИКА В МЕНЮ", "game_music": "МУЗИКА В ГРІ", "sounds": "ЗВУКИ",
           "window_size": "РОЗМІР ВІКНА", "auto": "АВТО", "fullscreen": "ПОВНИЙ ЕКРАН",
           "score": "РАХУНОК", "best": "РЕКОРД", "new_record": "НОВИЙ РЕКОРД!",
           "coins": "МОНЕТИ", "games": "ЗІГРАНО ІГОР", "records": "РЕКОРДИ",
           "shop_title": "МАГАЗИН", "select": "ОБРАТИ", "selected": "ОБРАНО", "not_enough": "НЕДОСТАТНЬО МОНЕТ"},
}
BIG = {"game_over", "settings", "records", "shop_title"}
CARD = {"select", "selected"}     # -- написи на картці пташки в магазині: дрібніші
GREEN = (150, 230, 90)
GREEN_SHADE = (80, 180, 60)
GOLD = (255, 214, 60)
GOLD_SHADE = (240, 150, 30)
extra["texts"] = {}
for lang, items in TEXTS.items():
    extra["texts"][lang] = {}
    for key, text in items.items():
        if key in BIG:
            cap = 30
            spr = pixel_text(text, cap, outline=3, shade=0.7, drop=3)
            while spr.shape[1] > 372:           # -- довгі слова (НАЛАШТУВАННЯ) зменшуємо, щоб влізли в екран
                cap -= 1
                spr = pixel_text(text, cap, outline=3, shade=0.7, drop=3)
        elif key in CARD:
            green = key == "selected"
            cap = 14
            while True:
                spr = pixel_text(text, cap, shade=0.55, fixed=True, track=1,
                                 fill=GREEN if green else WHITE, shade_color=GREEN_SHADE if green else CREAM)
                if spr.shape[1] <= 94 or cap <= 10:     # -- влазить у картку магазину
                    break
                cap -= 1
        elif key == "new_record":
            spr = pixel_text(text, 17, shade=0.55, fill=GOLD, shade_color=GOLD_SHADE, fixed=True)
        else:
            spr = pixel_text(text, 17, shade=0.6, fixed=True)
        extra["texts"][lang][key] = save(f"{key}.png", spr, f"text/{lang}")

# назви мов -- завжди своєю мовою
extra["lang_names"] = {
    "en": save("lang_en.png", pixel_text("ENGLISH", 18, fixed=True), "text"),
    "uk": save("lang_uk.png", pixel_text("УКРАЇНСЬКА", 18, fixed=True), "text"),
}

# цифри: темні (на кремовій панелі) і світлі з контуром (на небі і на кнопках)
DIGIT_CHARS = [(str(i), str(i)) for i in range(10)] + [("%", "percent"), ("×", "x"), ("+", "plus")]
extra["digits"] = {
    c: save(f"digit_{name}.png", pixel_text(c, 14, outline=0, fill=OUTLINE, shade_color=OUTLINE, track=0,
                                          fixed=True), "text/digits")
    for c, name in DIGIT_CHARS
}
extra["digits_light"] = {
    c: save(f"digit_{name}.png", pixel_text(c, 17, shade=0.6, track=0, fixed=True), "text/digits_light")
    for c, name in DIGIT_CHARS
}
# великі цифри для рекорду
extra["digits_big"] = {
    c: save(f"digit_{name}.png", pixel_text(c, 40, outline=3, shade=0.7, drop=3, track=0, fixed=True),
            "text/digits_big")
    for c, name in DIGIT_CHARS
}

# --------------------------------------------------------------------------
# 5. труба
# --------------------------------------------------------------------------
PIPE_SCALE = 2
# палітра зелених, від найсвітлішого до найтемнішого
G = {
    "h": (190, 245, 120),
    "l": (132, 214, 72),
    "m": (86, 180, 50),
    "d": (52, 132, 38),
    "x": (32, 92, 30),
    "o": OUTLINE,
}


def pipe_profile(w):
    """Горизонтальний профіль труби: які кольори йдуть зліва направо."""
    inner = w - 2
    cols = []
    for i in range(inner):
        u = i / (inner - 1)
        if u < 0.06:
            c = "d"
        elif u < 0.14:
            c = "l"
        elif u < 0.22:
            c = "h"
        elif u < 0.30:
            c = "l"
        elif u < 0.62:
            c = "m"
        elif u < 0.70:
            c = "l" if i % 2 == 0 else "m"   # дрібний «дизеринг»
        elif u < 0.86:
            c = "d"
        else:
            c = "x"
        cols.append(c)
    return ["o"] + cols + ["o"]


def paint(rows):
    h, w = len(rows), len(rows[0])
    a = np.zeros((h, w, 4), np.uint8)
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            if c != ".":
                a[y, x] = (*G[c], 255)
    return a


BODY_W, CAP_W, CAP_H = 31, 35, 13
body_row = pipe_profile(BODY_W)
body = paint([body_row] * 4)                         # 4 рядки -- тайл, гра повторює його по вертикалі
cap_row = pipe_profile(CAP_W)
cap_rows = [["o"] * CAP_W]
for y in range(CAP_H - 2):
    r = list(cap_row)
    if y == 0:                                        # світла кромка зверху
        r = ["o"] + ["h" if c in "lm" else ("l" if c == "d" else c) for c in r[1:-1]] + ["o"]
    if y >= CAP_H - 4:                                # тінь знизу капелюшка
        r = ["o"] + ["d" if c in "hlm" else "x" for c in r[1:-1]] + ["o"]
    cap_rows.append(r)
cap_rows.append(["o"] * CAP_W)
cap = paint(cap_rows)
# під капелюшком на тілі -- смужка тіні
shade_row = ["o"] + ["x" if c != "o" else c for c in body_row[1:-1]] + ["o"]
neck = paint([shade_row] * 2)

extra["pipe"] = {
    "body": save("pipe_body.png", upscale(body, PIPE_SCALE), "pipe"),
    "cap": save("pipe_cap.png", upscale(cap, PIPE_SCALE), "pipe"),
    "neck": save("pipe_neck.png", upscale(neck, PIPE_SCALE), "pipe"),
    "body_w": BODY_W * PIPE_SCALE, "cap_w": CAP_W * PIPE_SCALE, "cap_h": CAP_H * PIPE_SCALE,
}

# --------------------------------------------------------------------------
# 6. пташка (3 кадри помаху)
# --------------------------------------------------------------------------
BIRD_SCALE = 2
BW, BH = 19, 15
BC = {
    "y": (255, 214, 48),     # тіло
    "Y": (255, 240, 130),    # відблиск
    "s": (236, 160, 30),     # тінь тіла
    "b": (255, 246, 222),    # животик
    "w": (255, 255, 255),    # око
    "k": OUTLINE,            # зіниця
    "r": (242, 88, 40),      # дзьоб
    "R": (255, 140, 60),     # дзьоб світлий
    "c": (255, 150, 150),    # щічка
    "f": (255, 250, 235),    # крило
    "F": (238, 212, 170),    # тінь крила
}


def bird_frame(wing):
    yy, xx = np.mgrid[0:BH, 0:BW]
    col = np.full((BH, BW), "", dtype=object)

    # тіло -- еліпс, трохи зсунутий вліво (справа дзьоб)
    cx, cy, rx, ry = 8.2, 7.4, 7.6, 6.2
    body = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1
    col[body] = "y"
    col[body & (yy >= cy + 2.2)] = "s"
    belly = ((xx - (cx + 1.5)) / 4.6) ** 2 + ((yy - (cy + 3.2)) / 2.6) ** 2 <= 1
    col[body & belly] = "b"
    glint = ((xx - (cx - 2.5)) / 2.6) ** 2 + ((yy - (cy - 3.6)) / 1.2) ** 2 <= 1
    col[body & glint] = "Y"

    # хвостик
    for (x, y) in [(0, 5), (0, 6), (1, 6), (0, 7)]:
        col[y, x] = "y"

    # око
    eye = ((xx - 11.6) / 2.6) ** 2 + ((yy - 4.6) / 2.6) ** 2 <= 1
    col[eye] = "w"
    col[4, 12] = col[5, 12] = "k"
    col[4, 13] = col[5, 13] = "k"
    col[4, 13] = "k"
    col[6, 10] = col[7, 10] = "c"   # щічка

    # дзьоб
    for (x, y, c) in [(14, 7, "R"), (15, 7, "R"), (16, 7, "R"), (17, 7, "R"), (18, 8, "r"),
                      (14, 8, "r"), (15, 8, "r"), (16, 8, "r"), (17, 8, "r"),
                      (14, 9, "r"), (15, 9, "r"), (16, 9, "r")]:
        col[y, x] = c

    # крило: три положення
    wing_px = {
        "up": [(3, 3), (4, 3), (2, 4), (3, 4), (4, 4), (5, 4), (3, 5), (4, 5), (5, 5), (6, 5), (4, 6), (5, 6),
               (6, 6)],
        "mid": [(2, 7), (3, 7), (4, 7), (5, 7), (6, 7), (1, 8), (2, 8), (3, 8), (4, 8), (5, 8), (6, 8),
                (2, 9), (3, 9), (4, 9), (5, 9)],
        "down": [(4, 8), (5, 8), (6, 8), (3, 9), (4, 9), (5, 9), (6, 9), (2, 10), (3, 10), (4, 10), (5, 10),
                 (3, 11), (4, 11)],
    }[wing]
    for (x, y) in wing_px:
        col[y, x] = "f"
    # тінь під крилом (нижній край кожного стовпчика)
    by_x = {}
    for (x, y) in wing_px:
        by_x[x] = max(by_x.get(x, -1), y)
    for x, y in by_x.items():
        col[y, x] = "F"

    filled = col != ""
    rgba = np.zeros((BH + 2, BW + 2, 4), np.uint8)
    m = np.pad(filled, 1)
    rgba[dilate(m, 1, square=False)] = (*OUTLINE, 255)
    for y in range(BH):
        for x in range(BW):
            if col[y, x]:
                rgba[y + 1, x + 1] = (*BC[col[y, x]], 255)
    # контур крила (щоб читалося на тілі)
    wm = np.zeros((BH + 2, BW + 2), bool)
    for (x, y) in wing_px:
        wm[y + 1, x + 1] = True
    ring = dilate(wm, 1, square=False) & ~wm & (rgba[..., 3] > 0)
    rgba[ring] = (*OUTLINE, 255)
    return upscale(rgba, BIRD_SCALE)


frames = [bird_frame(w) for w in ("up", "mid", "down", "mid")]
fh, fw = frames[0].shape[:2]
extra["bird"] = {"file": save("bird_sheet.png", np.concatenate(frames, axis=1), "bird"),
                 "frames": len(frames), "fw": int(fw), "fh": int(fh), "fps": 12}

# --------------------------------------------------------------------------
# 6б. скіни для магазину
# --------------------------------------------------------------------------
# Щоб додати нову пташку: поклади картинку з кадрами (прозорий фон, пташка дивиться вправо,
# кадри сіткою cols x rows) в assets/images/skins і допиши рядок сюди. Порядок = порядок у магазині.
SKIN_SOURCES = [
    {"id": "blue", "price": 100, "image": "blue_bird.webp", "cols": 4, "rows": 3,
     "scale": 0.15, "fps": 24,
     # -- де центр тіла (хітбокса) відносно кінчика дзьоба, у пікселях вихідної картинки
     "body": (-120, 25)},
]


def runs(occ):
    out, start = [], None
    for i, v in enumerate(occ):
        if v and start is None:
            start = i
        elif not v and start is not None:
            out.append((start, i))
            start = None
    if start is not None:
        out.append((start, len(occ)))
    return out


def keep_main_blob(mask, step=4):
    """лишає тільки найбільшу зв'язну пляму (шматки сусідніх кадрів викидаємо)"""
    h, w = mask.shape
    small = mask[:h - h % step, :w - w % step].reshape(h // step, step, w // step, step).any(axis=(1, 3))
    lab = np.zeros(small.shape, int)
    sizes = [0]
    for y0, x0 in zip(*np.nonzero(small)):
        if lab[y0, x0]:
            continue
        n = len(sizes)
        stack, size = [(y0, x0)], 0
        lab[y0, x0] = n
        while stack:
            y, x = stack.pop()
            size += 1
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < small.shape[0] and 0 <= xx < small.shape[1] and small[yy, xx] and not lab[yy, xx]:
                        lab[yy, xx] = n
                        stack.append((yy, xx))
        sizes.append(size)
    main = int(np.argmax(sizes))
    keep = np.repeat(np.repeat(lab == main, step, axis=0), step, axis=1)
    out = np.zeros_like(mask)
    out[:keep.shape[0], :keep.shape[1]] = keep
    return mask & out


def cut_skin(src):
    a = np.array(Image.open(os.path.join(ROOT, "assets", "images", "skins", src["image"])).convert("RGBA"))
    alpha = a[..., 3].astype(float)
    a[..., 3] = np.clip(alpha * 255 / max(1, alpha.max()), 0, 255).astype(np.uint8)
    occ = a[..., 3] > 20
    H, W = occ.shape

    # -- рядки -- по порожніх смугах; стовпці -- розріз у найпорожнішому місці біля межі сітки
    row_runs = [r for r in runs(occ.any(axis=1)) if r[1] - r[0] > 20][:src["rows"]]
    cells = []
    for y0, y1 in row_runs:
        col = occ[y0:y1].sum(axis=0)
        cuts = [0]
        for k in range(1, src["cols"]):
            b = W * k // src["cols"]
            lo, hi = b - W // 30, b + W // 30
            cuts.append(lo + int(np.argmin(col[lo:hi])))
        cuts.append(W)
        cells += [(x0, y0, x1, y1) for x0, x1 in zip(cuts, cuts[1:])]

    # -- кожен кадр: чистимо, знаходимо кінчик дзьоба (найправіша точка)
    raw = []
    for x0, y0, x1, y1 in cells:
        c = a[y0:y1, x0:x1].copy()
        keep = keep_main_blob(c[..., 3] > 20)
        c[~keep] = 0
        ys, xs = np.nonzero(c[..., 3] > 128)
        tx = int(xs.max())
        ty = int(np.median(ys[xs >= tx - 2]))
        raw.append((c, tx, ty))

    # -- спільне полотно: всі кадри вирівняні по дзьобу
    left = max(tx for c, tx, ty in raw)
    right = max(c.shape[1] - tx for c, tx, ty in raw)
    up = max(ty for c, tx, ty in raw)
    down = max(c.shape[0] - ty for c, tx, ty in raw)
    k = src["scale"]
    fw, fh = int(round((left + right) * k)) + 4, int(round((up + down) * k)) + 4
    frames = []
    for c, tx, ty in raw:
        big = Image.new("RGBA", (left + right, up + down), (0, 0, 0, 0))
        big.paste(Image.fromarray(c), (left - tx, up - ty))
        small = big.convert("RGBa").resize((fw - 4, fh - 4), Image.LANCZOS).convert("RGBA")
        f = np.zeros((fh, fw, 4), np.uint8)
        f[2:-2, 2:-2] = np.array(small)
        # -- чіткий край + темний контур, як у решти спрайтів гри
        solid = f[..., 3] >= 120
        f[..., 3] = np.where(solid, 255, 0)
        ring = dilate(solid, 1, square=False) & ~solid
        f[ring] = (*OUTLINE, 255)
        frames.append(f)

    bx, by = src["body"]
    anchor = (2 + (left + bx) * k, 2 + (up + by) * k)
    return frames, anchor


extra["skins"] = [{"id": "classic", "price": 0, **extra["bird"],
                   "ax": extra["bird"]["fw"] / 2, "ay": extra["bird"]["fh"] / 2}]
for src in SKIN_SOURCES:
    sk_frames, (ax, ay) = cut_skin(src)
    sfh, sfw = sk_frames[0].shape[:2]
    extra["skins"].append({
        "id": src["id"], "price": src["price"],
        "file": save(f"{src['id']}_sheet.png", np.concatenate(sk_frames, axis=1), "skins"),
        "frames": len(sk_frames), "fw": int(sfw), "fh": int(sfh), "fps": src["fps"],
        "ax": round(ax, 1), "ay": round(ay, 1),
    })

# --------------------------------------------------------------------------
# 7. монетка (8 кадрів обертання) + звук
# --------------------------------------------------------------------------
COIN_SCALE = 2
CR = 6                      # радіус монетки в художніх пікселях
COIN = {
    "o": OUTLINE,
    "e": (196, 116, 20),    # ребро
    "g": (255, 198, 40),    # золото
    "G": (255, 236, 130),   # відблиск
    "d": (226, 150, 26),    # тінь / карбування
}


def coin_frame(k, n, size=16, r=7.0):
    """
    k-й кадр із n: монетка повертається навколо вертикальної осі.
    Сітка парного розміру, центр між пікселями -- тому коло виходить симетричне;
    радіус на 1 піксель менший за половину сітки, щоб контур не обрізався.
    """
    c = size / 2
    rx = max(1.6, abs(math.cos(math.pi * k / n)) * r)
    yy, xx = np.mgrid[0:size, 0:size] + 0.5
    inside = ((xx - c) / rx) ** 2 + ((yy - c) / r) ** 2 <= 1.0
    # кільця: зовнішній контур, обідок, серединка
    outline = inside & ~erode(inside)
    rim = erode(inside) & ~erode(erode(inside))
    face = erode(erode(inside))
    a = np.zeros((size, size, 4), np.uint8)
    a[outline] = (*COIN["o"], 255)
    a[face] = (*COIN["g"], 255)
    upper_left = (xx - c) + (yy - c) < 0
    a[rim & upper_left] = (*COIN["G"], 255)
    a[rim & ~upper_left] = (*COIN["d"], 255)
    if rx > 4.5:                                    # карбування: риска посередині (2 px, по центру)
        for y in range(5, size - 5):
            a[y, int(c) - 1] = (*COIN["d"], 255)
            a[y, int(c)] = (*COIN["e"], 255)
    elif rx < 2.5:                                  # майже ребром: суцільне ребро
        side = inside & ~(outline & ((yy < c - r + 1.5) | (yy > c + r - 1.5)))
        side &= ~outline | (np.abs(xx - c) < 0.6)
        a[side] = (*COIN["g"], 255)
        a[side & (xx > c)] = (*COIN["e"], 255)
    return upscale(a, COIN_SCALE)


def erode(m):
    out = m.copy()
    out[1:] &= m[:-1]
    out[:-1] &= m[1:]
    out[:, 1:] &= m[:, :-1]
    out[:, :-1] &= m[:, 1:]
    return out


coin_frames = [coin_frame(k, 8) for k in range(8)]
cfh, cfw = coin_frames[0].shape[:2]
extra["coin"] = {"file": save("coin_sheet.png", np.concatenate(coin_frames, axis=1), "coin"),
                 "frames": len(coin_frames), "fw": int(cfw), "fh": int(cfh), "fps": 10}


def write_coin_sound(path, rate=44100):
    """короткий «дзинь»: дві ноти вгору, згасання"""
    notes = [(987.8, 0.06), (1318.5, 0.22)]       # сі5 -> мі6
    samples = []
    for freq, dur in notes:
        n = int(rate * dur)
        for i in range(n):
            t = i / rate
            env = min(1.0, i / (rate * 0.004)) * math.exp(-t * (9 if dur > 0.1 else 3))
            v = 0.6 * math.sin(2 * math.pi * freq * t) + 0.25 * math.sin(4 * math.pi * freq * t)
            samples.append(int(max(-1, min(1, v * env * 0.8)) * 32767))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"".join(struct.pack("<h", s_) for s_ in samples))


write_coin_sound(os.path.join(ROOT, "assets", "sounds", "coin.wav"))

with open(os.path.join(OUT, "extra.json"), "w", encoding="utf-8") as fh_:
    json.dump(extra, fh_, ensure_ascii=False, indent=2)
print("готово ->", os.path.join(OUT, "extra.json"))
