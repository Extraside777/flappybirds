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
  * малює бонуси (щит, сповільнення, x2 монети), бульбашку щита навколо пташки і їхні звуки
  * ріже скіни пташок для магазину з картинок у assets/images/skins (див. SKIN_SOURCES)
  * малює ще дві пташки для магазину піксель-артом: ніндзя і фенікс (див. PAINTED)
  * малює кнопку ГОТОВО/DONE (вихід з редактора свого шлейфу)
  * малює фони для магазину: захід сонця, ніч і зиму (див. BACKGROUNDS)
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
           "shop_title": "SHOP", "select": "SELECT", "selected": "SELECTED", "not_enough": "NOT ENOUGH COINS",
           "tab_birds": "BIRDS", "tab_trails": "TRAILS", "tab_backgrounds": "WORLDS",
           "custom_title": "CUSTOM TRAIL", "edit": "EDIT", "colors": "COLORS", "style": "STYLE", "width": "WIDTH",
           "style_ribbon": "RIBBON", "style_glow": "GLOW", "style_bubbles": "BUBBLES", "style_pixels": "PIXELS",
           "style_sparks": "SPARKS"},
    "uk": {"game_over": "КІНЕЦЬ ГРИ", "settings": "НАЛАШТУВАННЯ", "language": "МОВА",
           "menu_music": "МУЗИКА В МЕНЮ", "game_music": "МУЗИКА В ГРІ", "sounds": "ЗВУКИ",
           "window_size": "РОЗМІР ВІКНА", "auto": "АВТО", "fullscreen": "ПОВНИЙ ЕКРАН",
           "score": "РАХУНОК", "best": "РЕКОРД", "new_record": "НОВИЙ РЕКОРД!",
           "coins": "МОНЕТИ", "games": "ЗІГРАНО ІГОР", "records": "РЕКОРДИ",
           "shop_title": "МАГАЗИН", "select": "ОБРАТИ", "selected": "ОБРАНО", "not_enough": "НЕДОСТАТНЬО МОНЕТ",
           "tab_birds": "ПТАШКИ", "tab_trails": "ШЛЕЙФИ", "tab_backgrounds": "ФОНИ",
           "custom_title": "СВІЙ ШЛЕЙФ", "edit": "ЗМІНИТИ", "colors": "КОЛЬОРИ", "style": "СТИЛЬ", "width": "ТОВЩИНА",
           "style_ribbon": "СТРІЧКА", "style_glow": "СЯЙВО", "style_bubbles": "БУЛЬБАШКИ", "style_pixels": "ПІКСЕЛІ",
           "style_sparks": "ІСКРИ"},
}
BIG = {"game_over", "settings", "records", "shop_title", "custom_title"}
CARD = {"select", "selected", "edit"}     # -- написи на картці пташки в магазині: дрібніші
GREEN_CARD = {"selected", "edit"}         # -- «обрано» і «змінити» (картка обраного свого шлейфу) -- зелені
TAB_TEXT_W = 100          # -- три вкладки магазину по 120 px: напис з запасом під рамку
# -- розмір літер вкладок: один на всі вкладки мови, найбільший, з яким кожна влазить
TAB_CAPS = {}
for lang, items in TEXTS.items():
    cap = 17
    while cap > 10 and max(pixel_text(t, cap, shade=0.6, fixed=True).shape[1]
                           for k, t in items.items() if k.startswith("tab_")) > TAB_TEXT_W:
        cap -= 1
    TAB_CAPS[lang] = cap
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
        elif key.startswith("tab_"):
            spr = pixel_text(text, TAB_CAPS[lang], shade=0.6, fixed=True)
        elif key in CARD:
            green = key in GREEN_CARD
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
     "scale": 0.15, "fps": 16,
     # -- де центр тіла (хітбокса) відносно кінчика дзьоба, у пікселях вихідної картинки
     "body": (-120, 25),
     # -- у картинці 12 кадрів -- це аж три помахи підряд (крила вгору -> вниз -> вгору ...), тому пташка
     # -- махала втричі швидше за інших. Беремо з них один повний помах: вгору -> назад -> вниз -> вгору
     # -- (8 кадрів на 16 fps = 2 помахи на секунду, як у ніндзя і фенікса)
     "order": [2, 3, 6, 4, 7, 5, 1, 0]},
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


# -- "art_px": піксель-арт, один художній піксель = стільки пікселів картинки
# -- (на картці магазину пташка збільшується так, щоб пікселі лишились чіткими)
extra["skins"] = [{"id": "classic", "price": 0, **extra["bird"],
                   "ax": extra["bird"]["fw"] / 2, "ay": extra["bird"]["fh"] / 2, "art_px": BIRD_SCALE}]
for src in SKIN_SOURCES:
    sk_frames, (ax, ay) = cut_skin(src)
    if "order" in src:
        sk_frames = [sk_frames[i] for i in src["order"]]
    sfh, sfw = sk_frames[0].shape[:2]
    extra["skins"].append({
        "id": src["id"], "price": src["price"],
        "file": save(f"{src['id']}_sheet.png", np.concatenate(sk_frames, axis=1), "skins"),
        "frames": len(sk_frames), "fw": int(sfw), "fh": int(sfh), "fps": src["fps"],
        "ax": round(ax, 1), "ay": round(ay, 1),
    })

# --------------------------------------------------------------------------
# 6в. намальовані скіни (без картинки-джерела): ніндзя і фенікс
# --------------------------------------------------------------------------
# Пташка малюється в «художніх пікселях» (полотно PW x PH), потім обводиться контуром і
# збільшується в PAINT_SCALE разів. Крило -- багатокутник, що повертається навколо плеча;
# кадри -- різні кути помаху. Стрічки ніндзя і полум'я фенікса колишуться разом з кадрами.
PAINT_SCALE = 2
PW, PH = 36, 30
P_BODY = (21, 18, 9.4, 8.4)          # центр і радіуси тіла
P_SHOULDER = (18.0, 19.0)            # навколо цієї точки обертається крило
WING_ANGLES = [72, 54, 28, -4, -32, -20, 12, 46]   # градуси: + крило вгору, - вниз
P_FPS = 16

# крило вздовж (u -- від плеча до кінчика, v -- поперек, + це задній край з пір'ям)
WING_SHAPE = [(0, -1.5), (3.5, -2.1), (7, -2.0), (9.6, -1.2), (11.4, 0.0), (11.2, 1.1),
              (9.6, 1.4), (9.8, 2.6), (7.6, 2.4), (7.6, 3.6), (5.2, 3.2), (5.0, 4.2),
              (2.6, 3.6), (0.4, 3.0), (-1, 1.6)]

PAINTED = {
    "ninja": {
        "body": [(92, 88, 128), (62, 58, 92), (46, 42, 72), (34, 30, 56)],   # світло .. темно
        "belly": [(104, 100, 140), (82, 78, 116)],
        "wing": [(150, 146, 190), (116, 112, 158), (84, 80, 124)],               # покривні, основа, кінчики
        "beak": [(255, 190, 70), (228, 120, 36)],
        "band": [(255, 96, 86), (222, 40, 52), (150, 22, 44)],
        "mask": (255, 226, 190),
    },
    "phoenix": {
        "body": [(255, 122, 84), (228, 58, 50), (176, 32, 50), (122, 20, 52)],
        "belly": [(255, 226, 150), (255, 176, 80)],
        "wing": [(255, 236, 130), (255, 186, 56), (255, 122, 40)],
        "beak": [(255, 236, 120), (232, 150, 30)],
        "flame": [(226, 52, 40), (255, 132, 40), (255, 214, 70), (255, 250, 190)],   # від основи до кінчика
    },
}
PAINTED_SHOP = [("ninja", 200), ("phoenix", 300)]     # порядок у магазині і ціна


def poly_mask(pts):
    img = Image.new("L", (PW, PH), 0)
    ImageDraw.Draw(img).polygon([(float(x), float(y)) for x, y in pts], fill=1)
    return np.array(img, bool)


def line_mask(pts, width):
    img = Image.new("L", (PW, PH), 0)
    ImageDraw.Draw(img).line([(float(x), float(y)) for x, y in pts], fill=1, width=width, joint="curve")
    return np.array(img, bool)


def wing_mask(angle):
    a = math.radians(angle)
    d = (-math.cos(a), -math.sin(a))          # уздовж крила (назад і вгору/вниз)
    p = (d[1], -d[0])                         # поперек, до заднього краю
    sx, sy = P_SHOULDER

    def at(u, v):
        return sx + u * d[0] + v * p[0], sy + u * d[1] + v * p[1]

    yy, xx = np.mgrid[0:PH, 0:PW]
    u = (xx + 0.5 - sx) * d[0] + (yy + 0.5 - sy) * d[1]   # відстань від плеча вздовж крила
    return poly_mask([at(u_, v_) for u_, v_ in WING_SHAPE]), u


def flame(base, tip, width, wobble):
    """язичок полум'я: від широкої основи до гострого кінчика, з вигином"""
    (bx, by), (tx, ty) = base, tip
    mx, my = (bx + tx) / 2 + wobble, (by + ty) / 2 - wobble * 0.5
    nx, ny = ty - by, bx - tx
    n = math.hypot(nx, ny) or 1
    nx, ny = nx / n * width, ny / n * width
    return poly_mask([(bx + nx, by + ny), (mx + nx * 0.6, my + ny * 0.6), (tx, ty),
                      (mx - nx * 0.6, my - ny * 0.6), (bx - nx, by - ny)])


def flame_colors(mask, base, tip, pal, img):
    """полум'я: колір за відстанню від основи (червоне -> жовте -> майже біле на кінчику)"""
    yy, xx = np.mgrid[0:PH, 0:PW]
    (bx, by), (tx, ty) = base, tip
    L2 = (tx - bx) ** 2 + (ty - by) ** 2
    t = ((xx - bx) * (tx - bx) + (yy - by) * (ty - by)) / L2
    for lo, c in zip((-9, 0.35, 0.65, 0.9), pal):
        img[mask & (t >= lo)] = c


def painted_frame(kind, f, n):
    pal = PAINTED[kind]
    img = np.zeros((PH, PW, 3), np.uint8)
    fill = np.zeros((PH, PW), bool)
    inner = []                        # маски, які треба ще й обвести всередині силуету
    yy, xx = np.mgrid[0:PH, 0:PW]
    ph = 2 * math.pi * f / n          # фаза для колихання стрічок / полум'я

    def put(mask, color):
        img[mask] = color
        fill[mask] = True

    cx, cy, rx, ry = P_BODY

    # -- позаду тіла: хвіст
    if kind == "phoenix":
        for i, (tip, w) in enumerate((((cx - 17.5, cy - 7.5), 1.9), ((cx - 18.5, cy - 0.5), 2.2),
                                       ((cx - 16.5, cy + 6.0), 1.9))):
            base = (cx - rx + 2.5, cy - 1.5 + i * 2.0)
            tip = (tip[0] + math.sin(ph + i * 1.9) * 1.2, tip[1] + math.cos(ph + i * 1.3) * 1.2)
            m = flame(base, tip, w, math.sin(ph * 2 + i) * 1.4)
            fill[m] = True
            flame_colors(m, base, tip, pal["flame"], img)
    else:
        put(poly_mask([(cx - rx + 2, cy - 1), (cx - rx - 3, cy - 3), (cx - rx - 2, cy + 1),
                       (cx - rx - 3, cy + 3), (cx - rx + 2, cy + 3)]), pal["body"][2])
        # -- кінці пов'язки маяють позаду голови
        kx, ky = cx - 6.5, cy - 5.5
        for j, (amp, drop, w) in enumerate(((1.4, -1.0, 2), (1.6, 2.4, 2))):
            pts = [(kx - s, ky + drop * s / 12 + amp * math.sin(ph - s * 0.55 + j * 1.2) * min(1, s / 4))
                   for s in np.linspace(0, 12, 13)]
            m = line_mask(pts, w)
            put(m, pal["band"][1 + j])
            put(m & (np.roll(m, 1, axis=0) == False), pal["band"][j])   # світла кромка зверху

    # -- тіло з тінню знизу і відблиском зверху-зліва
    nx, ny = (xx + 0.5 - cx) / rx, (yy + 0.5 - cy) / ry
    body = nx ** 2 + ny ** 2 <= 1
    b_hi, b_base, b_shade, b_dark = pal["body"]
    put(body, b_base)
    img[body & (ny > 0.3)] = b_shade
    img[body & (ny > 0.3) & (nx ** 2 + ny ** 2 > 0.72)] = b_dark
    img[body & ((nx + 0.35) ** 2 / 0.12 + (ny + 0.62) ** 2 / 0.03 <= 1)] = b_hi
    belly = ((xx + 0.5 - (cx + 3.0)) / 5.0) ** 2 + ((yy + 0.5 - (cy + 4.4)) / 3.0) ** 2 <= 1
    img[body & belly] = pal["belly"][0]
    img[body & belly & (yy + 0.5 > cy + 5.0)] = pal["belly"][1]

    # -- голова
    ex, ey = cx + 5.0, cy - 2.6
    if kind == "phoenix":
        # -- чубчик з трьох язичків полум'я
        for i, (bx, tip) in enumerate(((cx - 1, (cx - 6, cy - 14)), (cx + 1.5, (cx - 2.5, cy - 16.2)),
                                       (cx + 4, (cx + 1.5, cy - 13.5)))):
            base = (bx, cy - ry + 1.5)
            tip = (tip[0] + math.sin(ph + i * 2.1) * 0.9, tip[1] + math.cos(ph * 2 + i) * 0.6)
            m = flame(base, tip, 1.6, math.sin(ph + i) * 0.8) & ~body
            fill[m] = True
            flame_colors(m, base, tip, pal["flame"], img)
        # -- щічка
        img[(np.abs(xx + 0.5 - (ex - 1.2)) < 1.2) & (np.abs(yy + 0.5 - (ey + 4.2)) < 0.6)] = pal["belly"][1]
    else:
        # -- прорізь маски і пов'язка
        slit = body & (yy >= int(ey) - 2) & (yy <= int(ey) + 2) & (xx >= cx + 1)
        img[slit] = pal["mask"]
        band = body & (yy >= int(ey) - 5) & (yy <= int(ey) - 3)
        img[band] = pal["band"][1]
        img[band & (yy == int(ey) - 5)] = pal["band"][0]
        img[band & (yy == int(ey) - 3)] = pal["band"][2]
        # -- вузол на потилиці
        knot = ((xx + 0.5 - (cx - 6.0)) / 1.8) ** 2 + ((yy + 0.5 - (cy - 5.4)) / 1.8) ** 2 <= 1
        put(knot, pal["band"][1])
        img[knot & (yy + 0.5 < cy - 5.6) & (xx + 0.5 < cx - 6)] = pal["band"][0]
        inner.append(knot)

    # -- око: біле, зіниця дивиться вперед, блик
    eye = ((xx + 0.5 - ex) / 2.7) ** 2 + ((yy + 0.5 - ey) / 2.7) ** 2 <= 1
    if kind == "ninja":
        eye = ((xx + 0.5 - ex) / 2.6) ** 2 + ((yy + 0.5 - ey) / 1.9) ** 2 <= 1
    img[eye] = WHITE
    ix, iy = int(ex + 0.6), int(ey - 0.8)
    img[iy:iy + 3, ix:ix + 2] = OUTLINE
    img[iy, ix] = WHITE
    if kind == "ninja":                         # насуплена брова
        for x, y in ((ix - 3, iy - 1), (ix - 2, iy - 1), (ix - 1, iy), (ix, iy), (ix + 1, iy + 0)):
            img[y, x] = OUTLINE
        img[iy, ix] = OUTLINE

    # -- дзьоб
    bx0, by0 = int(cx + rx - 1.5), int(cy)
    beak_top = [(bx0, by0 - 1), (bx0 + 1, by0 - 1), (bx0 + 2, by0 - 1), (bx0 + 3, by0 - 1), (bx0 + 4, by0),
                (bx0, by0), (bx0 + 1, by0), (bx0 + 2, by0), (bx0 + 3, by0)]
    beak_low = [(bx0, by0 + 1), (bx0 + 1, by0 + 1), (bx0 + 2, by0 + 1), (bx0, by0 + 2), (bx0 + 1, by0 + 2)]
    for pts, c in ((beak_top, pal["beak"][0]), (beak_low, pal["beak"][1])):
        for x, y in pts:
            img[y, x] = c
            fill[y, x] = True

    # -- крило поверх тіла: покривні світлі, кінчики пір'я темніші
    wing, u = wing_mask(WING_ANGLES[f])
    w_cov, w_base, w_tip = pal["wing"]
    put(wing, w_base)
    img[wing & (u < 4.0)] = w_cov
    img[wing & (u > 7.4)] = w_tip
    inner.append(wing)

    # -- зовнішній контур + контур деталей усередині силуету
    rgba = np.zeros((PH + 2, PW + 2, 4), np.uint8)
    m = np.pad(fill, 1)
    rgba[dilate(m, 1, square=False)] = (*OUTLINE, 255)
    rgba[1:-1, 1:-1][fill] = np.concatenate([img, np.full((PH, PW, 1), 255, np.uint8)], axis=2)[fill]
    for part in inner:
        pm = np.pad(part, 1)
        ring = dilate(pm, 1, square=False) & ~pm & (rgba[..., 3] > 0)
        rgba[ring] = (*OUTLINE, 255)
    return upscale(rgba, PAINT_SCALE)


for kind, price in PAINTED_SHOP:
    p_frames = [painted_frame(kind, i, len(WING_ANGLES)) for i in range(len(WING_ANGLES))]
    pfh, pfw = p_frames[0].shape[:2]
    extra["skins"].append({
        "id": kind, "price": price,
        "file": save(f"{kind}_sheet.png", np.concatenate(p_frames, axis=1), "skins"),
        "frames": len(p_frames), "fw": int(pfw), "fh": int(pfh), "fps": P_FPS,
        # -- центр тіла = центр хітбокса (+1 художній піксель контуру)
        "ax": (P_BODY[0] + 1) * PAINT_SCALE, "ay": (P_BODY[1] + 1) * PAINT_SCALE, "art_px": PAINT_SCALE,
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

# --------------------------------------------------------------------------
# 8. бонуси: щит, сповільнення і x2 монети (іконки в бульбашках, бульбашка щита навколо пташки) + звуки
# --------------------------------------------------------------------------
PU_SCALE = 2
PU_SIZE = 18                 # бульбашка в художніх пікселях (+1 піксель контуру з кожного боку)
PU = {
    "shield": {"tint": (90, 190, 255), "rim": (190, 236, 255)},
    "slow": {"tint": (190, 120, 255), "rim": (234, 210, 255)},
    "x2": {"tint": (255, 190, 50), "rim": (255, 240, 170), "alpha": 235},   # -- щільна, як монетка
}
GOLD = [(255, 236, 130), (255, 196, 50), (206, 126, 30)]    # світле, основа, тінь


def grid(size):
    yy, xx = np.mgrid[0:size, 0:size]
    return yy + 0.5, xx + 0.5


def poly(pts, size):
    img = Image.new("L", (size, size), 0)
    ImageDraw.Draw(img).polygon([(float(x), float(y)) for x, y in pts], fill=1)
    return np.array(img, bool)


def bubble(kind):
    """напівпрозора кругла бульбашка з обідком, бліком і темним контуром"""
    s = PU_SIZE + 2
    yy, xx = grid(s)
    d = np.hypot(xx - s / 2, yy - s / 2)
    inside = d <= PU_SIZE / 2 - 0.5
    a = np.zeros((s, s, 4), np.uint8)
    a[inside] = (*PU[kind]["tint"], PU[kind].get("alpha", 90))
    a[inside & ~erode(inside)] = (*PU[kind]["rim"], 235)
    a[dilate(inside, 1, square=False) & ~inside] = (*OUTLINE, 255)
    ang = np.degrees(np.arctan2(yy - s / 2, xx - s / 2))
    a[inside & (d > 5.4) & (d < 7.2) & (ang > -160) & (ang < -110)] = (255, 255, 255, 230)   # блік
    return a


def put_item(a, mask, colors):
    """непрозорий предмет у бульбашці: кольори з масок + темний контур"""
    ring = dilate(mask, 1, square=False) & ~mask
    a[ring] = (*OUTLINE, 255)
    for m, c in colors:
        a[m & mask] = (*c, 255)


def shield_icon():
    s = PU_SIZE + 2
    a = bubble("shield")
    yy, xx = grid(s)
    shape = poly([(5.5, 4.5), (10, 3.5), (14.5, 4.5), (14.5, 9), (13, 12.5), (10, 15.5),
                  (7, 12.5), (5.5, 9)], s)
    rim = shape & ~erode(shape)
    cross = ((np.abs(xx - 10) < 1.1) & (yy > 5.5) & (yy < 13)) | ((np.abs(yy - 8.5) < 1.1) & (xx > 7) & (xx < 13))
    put_item(a, shape, [(shape & (xx < 10), (120, 200, 255)), (shape & (xx >= 10), (54, 124, 232)),
                        (cross, (236, 248, 255)), (rim & (xx < 10), GOLD[0]), (rim & (xx >= 10), GOLD[1]),
                        (rim & (yy > 12), GOLD[2])])
    return a


def hourglass_icon(k, n):
    """пісочний годинник; k-й кадр з n -- пісок пересипається зверху вниз"""
    s = PU_SIZE + 2
    a = bubble("slow")
    yy, xx = grid(s)
    caps = ((yy > 3) & (yy < 5) | (yy > 14) & (yy < 16)) & (np.abs(xx - 10) < 4.2)
    half_w = {5: 3, 6: 3, 7: 2.2, 8: 1.2, 9: 0.8, 10: 1.2, 11: 2.2, 12: 3, 13: 3, 14: 3}
    row = np.floor(yy).astype(int)
    glass = np.zeros_like(caps)
    for r, hw in half_w.items():
        glass |= (row == r) & (np.abs(xx - 10) < hw)
    top_level = 5 + 4 * k / (n - 1)               # верхній пісок тане
    bottom_level = 14.99 - 4 * k / (n - 1)        # нижній росте
    sand = glass & (((row <= 8) & (row >= top_level)) | ((row >= 10) & (row >= bottom_level)))
    stream = (row >= 9) & (row < bottom_level) & (np.floor(xx) == 9 + k % 2) if k < n - 1 else False
    shape = caps | glass
    put_item(a, shape, [(glass, (226, 244, 255)), (glass & (xx > 10.5), (186, 214, 240)),
                        (sand | stream, (255, 206, 80)), (sand & (xx > 10.5), (232, 156, 50)),
                        (caps, GOLD[1]), (caps & (yy < 4.6) | caps & (yy > 14) & (yy < 14.6), GOLD[0])])
    a[stream & ~shape] = (255, 206, 80, 255)
    return a


X2_GLYPHS = {
    "x": ["X...X",
          ".X.X.",
          "..X..",
          ".X.X.",
          "X...X"],
    "2": [".XXX.",
          "X...X",
          "....X",
          "...X.",
          "..X..",
          ".X...",
          "XXXXX"],
}


def x2_icon():
    """велике «x2» у золотій бульбашці (як у написів гри: біле зверху, кремове знизу)"""
    s = PU_SIZE + 2
    a = bubble("x2")
    yy, xx = grid(s)
    text = np.zeros((s, s), bool)
    for ch, (x0, y0) in (("x", (4, 8)), ("2", (10, 6))):
        for dy, line in enumerate(X2_GLYPHS[ch]):
            for dx, c in enumerate(line):
                text[y0 + dy, x0 + dx] = c == "X"
    put_item(a, text, [(text, WHITE), (text & (yy > 10), CREAM)])
    return a


def shield_aura(k, n, r=15.5):
    """бульбашка щита навколо пташки; іскорка біжить по колу"""
    s = int(2 * r) + 4
    yy, xx = grid(s)
    d = np.hypot(xx - s / 2, yy - s / 2)
    inside = d <= r
    edge = inside & ~erode(inside)
    a = np.zeros((s, s, 4), np.uint8)
    a[inside] = (120, 210, 255, 46)
    a[erode(inside) & ~erode(erode(inside))] = (170, 236, 255, 120)
    a[edge] = (60, 150, 240, 230)
    ang = np.degrees(np.arctan2(yy - s / 2, xx - s / 2))
    a[inside & (d > r - 4.2) & (d < r - 2.2) & (ang > -165) & (ang < -105)] = (255, 255, 255, 220)
    # -- іскорка-хрестик на обідку
    t = 2 * math.pi * k / n
    sx, sy = int(s / 2 + math.cos(t) * (r - 0.5)), int(s / 2 + math.sin(t) * (r - 0.5))
    for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
        a[sy + dy, sx + dx] = (255, 255, 255, 255)
    return upscale(a, PU_SCALE)


def sheet(frames, name):
    fh_, fw_ = frames[0].shape[:2]
    return {"file": save(name, np.concatenate(frames, axis=1), "powerups"),
            "frames": len(frames), "fw": int(fw_), "fh": int(fh_)}


extra["powerups"] = {
    "shield": {**sheet(shine_frames(upscale(shield_icon(), PU_SCALE), n=10, band=8), "shield_sheet.png"),
               "fps": 20, "pause": 0.9},
    "slow": {**sheet([upscale(hourglass_icon(k, 8), PU_SCALE) for k in range(8)], "slow_sheet.png"),
             "fps": 7, "pause": 0.5},
    "x2": {**sheet(shine_frames(upscale(x2_icon(), PU_SCALE), n=10, band=8), "x2_sheet.png"),
           "fps": 20, "pause": 0.7},
    "aura": {**sheet([shield_aura(k, 12) for k in range(12)], "aura_sheet.png"), "fps": 12, "pause": 0.0},
}


def write_sound(path, parts, rate=44100):
    """parts -- функції f(t) -> -1..1 з тривалістю, грають одна за одною"""
    samples = []
    for fn, dur in parts:
        for i in range(int(rate * dur)):
            samples.append(int(max(-1, min(1, fn(i / rate, dur))) * 32767))
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"".join(struct.pack("<h", s_) for s_ in samples))


def note(freq, decay):
    def fn(t, dur):
        env = min(1.0, t / 0.004) * math.exp(-t * decay)
        return 0.5 * env * (math.sin(2 * math.pi * freq * t) + 0.3 * math.sin(4 * math.pi * freq * t))
    return fn


def pop(t, dur):
    """щит лопається: частота швидко падає, трохи «шуму» від гармонік"""
    k = t / dur
    # -- частота 1020 -> 140 Гц; фаза -- інтеграл частоти, щоб звук не «рвався»
    phase = 2 * math.pi * (140 * t + 880 * dur / 3 * (1 - (1 - k) ** 3))
    env = min(1.0, t / 0.003) * (1 - k) ** 2
    return 0.55 * env * (math.sin(phase) + 0.4 * math.sin(phase * 2.7) + 0.25 * math.sin(phase * 5.3))


SOUNDS_OUT = os.path.join(ROOT, "assets", "sounds")
# -- бонус: швидке арпеджіо вгору (до-мі-соль-до)
write_sound(os.path.join(SOUNDS_OUT, "powerup.wav"),
            [(note(1046.5, 30), 0.055), (note(1318.5, 30), 0.055), (note(1568.0, 30), 0.055),
             (note(2093.0, 7), 0.28)])
write_sound(os.path.join(SOUNDS_OUT, "shield_break.wav"), [(pop, 0.32)])


# --------------------------------------------------------------------------
# 9. кнопка ГОТОВО (вихід з редактора свого шлейфу): основа -- кнопка MENU, замість будиночка галочка
# --------------------------------------------------------------------------
def check_icon():
    img = Image.new("L", (15, 13), 0)
    ImageDraw.Draw(img).line([(2, 7), (6, 10), (12, 2)], fill=1, width=3, joint="curve")
    m = np.pad(np.array(img, bool), 1)
    a = np.zeros(m.shape + (4,), np.uint8)
    a[dilate(m, 1, square=False)] = (*OUTLINE, 255)
    a[m] = (*G["m"], 255)
    a[m & ~np.roll(m, 1, axis=0)] = (*G["h"], 255)      # -- світла кромка зверху
    a[m & ~np.roll(m, -1, axis=0)] = (*G["d"], 255)     # -- тінь знизу
    return trim(a)


DONE_WORDS = {"en": "DONE", "uk": "ГОТОВО"}
DONE_TEXT_X0 = 84         # -- текст між галочкою і правою рамкою
for lang, word in DONE_WORDS.items():
    cap = fit_cap([word], 220 - 24 - DONE_TEXT_X0, fit_cap(list(BUTTON_WORDS[lang].values())[:3],
                                                           MENU_TEXT_X1 - MENU_TEXT_X0, 22))
    extra["buttons"][lang]["done"] = relabel("done", word, 22, cap, (DONE_TEXT_X0 + 220 - 24) // 2, src="menu",
                                             icon=upscale(check_icon(), 3), icon_x=52, folder=f"buttons/{lang}")

# --------------------------------------------------------------------------
# 10. фони для магазину: захід сонця, ніч, зима («день» -- звичайний фон з tools/make_sprites.py)
# --------------------------------------------------------------------------
# Кожен фон -- ті самі шари, що й звичайний: небо, дальній шар (гори / місто), кущі (ялинки) і земля,
# плюс світило (сонце / місяць) і ефекти, які гра малює сама (зорі, сніг, світлячки -- "fx").
# Шари малюються «художніми» пікселями BG_PX x BG_PX і повторюються по горизонталі без шва.
BG_PX = 2
BG_W = base_manifest["layers"]["ground"]["w"] // BG_PX    # -- 400 художніх пікселів = 800 px, як у звичайних шарів
SCREEN_W, SCREEN_H = base_manifest["screen"]["w"], base_manifest["screen"]["h"]
GROUND_Y = base_manifest["screen"]["ground_y"]
LAYER_BOTTOM = GROUND_Y + 6       # -- дальній шар трохи заходить під землю, щоб не було щілини


def sky_gradient(stops, bands=16):
    """небо смугами, як у піксель-арті: stops -- [(0..1 зверху вниз, колір)]; межі смуг -- «шахівницею»"""
    h, w = SCREEN_H // BG_PX, SCREEN_W // BG_PX
    pos = [p for p, _ in stops]
    cols = np.array([c for _, c in stops], float)

    def color_at(t):
        return np.stack([np.interp(t, pos, cols[:, i]) for i in range(3)], axis=1)

    t = (np.arange(h) + 0.5) / h
    band = np.minimum((t * bands).astype(int), bands - 1)
    row = color_at((band + 0.5) / bands)
    prev = color_at(np.maximum(band - 0.5, 0) / bands)
    img = np.repeat(row[:, None], w, axis=1)
    yy, xx = np.mgrid[0:h, 0:w]
    dith = ((t * bands - band)[:, None] < 0.2) & ((xx + yy) % 2 == 0) & (band[:, None] > 0)
    img[dith] = np.repeat(prev[:, None], w, axis=1)[dith]
    return upscale(np.round(img).astype(np.uint8), BG_PX)


def wrap_dx(x, cx):
    """відстань по x з урахуванням того, що шар зациклений (правий край переходить у лівий)"""
    return (x - cx + BG_W / 2) % BG_W - BG_W / 2


def wrap_dilate(m):
    """розширення маски на 1 піксель хрестом; по горизонталі -- через край шару (він зациклений)"""
    out = m | np.roll(m, 1, axis=1) | np.roll(m, -1, axis=1)
    out[1:] |= m[:-1]
    out[:-1] |= m[1:]
    return out


def spread(n, rng, jitter=0.35):
    """n точок по ширині шару, приблизно рівномірно, з випадковим зсувом"""
    return [(i + rng.uniform(-jitter, jitter)) * BG_W / n for i in range(n)]


def mountains(img, peaks, rng, light, shade, rim=None, snow=None):
    """
    гірське пасмо: peaks -- [(x вершини, y вершини, крутизна схилів)] у художніх пікселях.
    Лівий схил кожної гори світліший (light), правий -- в тіні (shade).
    snow -- (глибина шапки, світлий сніг, сніг у тіні): шапки на вершинах з нерівним нижнім краєм.
    """
    h = img.shape[0]
    xs = np.arange(BG_W)
    top = np.full(BG_W, 1e9)
    lit = np.zeros(BG_W, bool)
    summit = np.zeros(BG_W)
    for px, py, slope in peaks:
        dx = wrap_dx(xs, px)
        t = py + np.abs(dx) * slope
        better = t < top
        top[better], lit[better], summit[better] = t[better], dx[better] < 0, py
    top = np.round(top + (rng.random(BG_W) < 0.3) * rng.choice([-1, 1], BG_W)).astype(int)   # -- нерівний край
    yy = np.arange(h)[:, None]
    mask = yy >= top[None]
    img[mask & lit[None]] = (*light, 255)
    img[mask & ~lit[None]] = (*shade, 255)
    if snow:
        depth, s_light, s_shade = snow
        teeth = np.repeat(rng.integers(0, 4, BG_W // 3 + 1), 3)[:BG_W]     # -- зубчики шириною 3 px
        cap = mask & (yy < summit[None] + depth + teeth[None])
        img[cap & lit[None]] = (*s_light, 255)
        img[cap & ~lit[None]] = (*s_shade, 255)
    if rim:
        img[mask & (yy == top[None])] = (*rim, 255)                       # -- підсвічений край пасма
    return img


def skyline(img, rng, tops, widths, body, edge, lit, dark, lit_chance):
    """
    місто: будинки підряд по всій ширині шару (останній переходить через край -- шва нема).
    tops / widths -- діапазони висоти даху і ширини будинку; вікна 2x2, світиться частина з них
    """
    h = img.shape[0]
    x = 0
    while x < BG_W:
        w, top = int(rng.integers(*widths)), int(rng.integers(*tops))
        cols = np.arange(x, x + w) % BG_W
        kind = rng.random()
        if kind < 0.3 and w >= 10:                       # -- надбудова на даху
            img[top - 4:top, cols[2:w - 2]] = (*body, 255)
            img[top - 4, cols[2:w - 2]] = (*edge, 255)
        elif kind < 0.55:                                # -- антена з вогником
            img[top - 6:top, cols[w // 2]] = (*edge, 255)
            img[top - 7, cols[w // 2]] = (255, 90, 80, 255)
        img[top:h, cols] = (*body, 255)
        img[top, cols] = (*edge, 255)
        img[top:h, cols[0]] = (*edge, 255)
        for wy in range(top + 3, h - 3, 4):
            for wx in range(2, w - 2, 4):
                c = lit if rng.random() < lit_chance else dark
                img[wy:wy + 2, cols[wx:wx + 2]] = (*c, 255)
        x += w + int(rng.integers(0, 3))
    return img


def clumps(img, rng, n, radius, rise, base, light, dark, outline, aspect=1.0, leaves=True):
    """
    кущі (або кучугури снігу): круглі купки впритул, кожна з темним контуром, освітлена зверху-зліва.
    radius -- діапазон радіусів, rise -- на скільки центр купки вище низу шару,
    aspect -- у скільки разів купка ширша, ніж вища; leaves -- крапочки-листочки на межі світла і тіні
    """
    h = img.shape[0]
    yy, xx = np.mgrid[0:h, 0:BG_W]
    items = [(cx, h - rng.uniform(*rise), rng.uniform(*radius)) for cx in spread(n, rng)]
    rng.shuffle(items)
    for cx, cy, r in items:
        dx, dy = wrap_dx(xx, cx) / aspect, yy - cy
        inside = (dx ** 2 + dy ** 2 <= r * r) | ((dy >= 0) & (np.abs(dx) <= r))   # -- нижче центру -- до низу
        lit = inside & ((dx + r * 0.3) ** 2 + (dy + r * 0.38) ** 2 <= (r * 0.6) ** 2)
        img[wrap_dilate(inside) & ~inside] = (*outline, 255)
        img[inside] = (*base, 255)
        img[lit] = (*light, 255)
        img[inside & (dy > 0) & (dx ** 2 + dy ** 2 > (r * 0.72) ** 2)] = (*dark, 255)
        if leaves:
            edge = inside & ((dx + r * 0.3) ** 2 + (dy + r * 0.38) ** 2 <= (r * 0.8) ** 2) & ~lit & (dy < r * 0.3)
            img[edge & (rng.random(edge.shape) < 0.3)] = (*light, 255)
            img[lit & (rng.random(lit.shape) < 0.07)] = (*base, 255)
    return img


CLOUDS = [load(c["file"]) for c in base_manifest["clouds"]]


def recolor_clouds(dark, light, alpha, folder):
    """хмари звичайного фону в інших кольорах: світлість пікселя -> колір між dark і light"""
    files = []
    for i, c in enumerate(CLOUDS):
        lum = c[..., :3].astype(float) @ [0.3, 0.59, 0.11]
        solid = c[..., 3] > 0
        lo, hi = lum[solid].min(), lum[solid].max()
        k = np.clip((lum - lo) / max(1.0, hi - lo), 0, 1)[..., None]
        out = c.copy()
        out[..., :3] = np.round(np.array(dark) + (np.array(light) - np.array(dark)) * k)
        out[..., 3] = (c[..., 3].astype(int) * alpha // 255).astype(np.uint8)
        files.append(save(f"cloud_{i + 1}.png", out, folder))
    return files


def pines(img, rng, n, heights, base_y, leaf, leaf_shade, snow, snow_shade, outline):
    """ялинки в снігу: три яруси-трикутники, на кожному ярусі сніг; лівий бік світліший"""
    h = img.shape[0]
    yy, xx = np.mgrid[0:h, 0:BG_W]
    for cx in spread(n, rng, 0.3):
        th = rng.uniform(*heights)
        top = base_y - th
        dx = wrap_dx(xx, cx)
        tree = np.zeros((h, BG_W), bool)
        caps = np.zeros((h, BG_W), bool)
        trunk = (np.abs(dx + 0.5) <= 1) & (yy >= base_y - 4) & (yy < base_y)
        for i in range(3):
            y0, y1 = top + th * 0.26 * i, top + th * (0.42 + 0.27 * i)
            hw = th * (0.2 + 0.08 * i)
            tier = (yy >= y0) & (yy < y1) & (np.abs(dx) <= (yy - y0 + 1) / (y1 - y0) * hw)
            tree |= tier
            caps |= tier & (yy < y0 + (y1 - y0) * 0.5 - np.abs(dx) * 0.35 + (np.round(dx) % 3 == 0))
        img[wrap_dilate(tree | trunk) & ~(tree | trunk)] = (*outline, 255)
        img[trunk] = (110, 76, 64, 255)
        img[tree & (dx < 0)] = (*leaf, 255)
        img[tree & (dx >= 0)] = (*leaf_shade, 255)
        img[caps & (dx < 0)] = (*snow, 255)
        img[caps & (dx >= 0)] = (*snow_shade, 255)
    return img


GROUND = load(base_manifest["layers"]["ground"]["file"])


def recolor_ground(fn):
    """земля звичайного фону, перефарбована: fn(rgb, де трава) -> новий rgb"""
    rgb = GROUND[..., :3].astype(float)
    grass = (rgb[..., 1] > rgb[..., 0] + 20) & (rgb[..., 1] > rgb[..., 2] + 20)
    out = GROUND.copy()
    out[..., :3] = np.clip(np.round(fn(rgb, grass)), 0, 255).astype(np.uint8)
    return out


def snowy(rgb, grass):
    """трава -> сніг (світлість беремо із зеленого каналу), земля -> холодна сіро-фіолетова"""
    g = rgb[..., 1]
    snow = np.stack([np.interp(g, [70, 110, 150, 200, 255], c) for c in
                     ([86, 112, 150, 222, 248], [104, 136, 182, 236, 252], [150, 190, 228, 252, 255])], axis=-1)
    dirt = np.stack([np.interp(g, [60, 110, 180], c) for c in
                     ([112, 152, 190], [86, 120, 164], [110, 146, 180])], axis=-1)
    return np.where(grass[..., None], snow, dirt)


def disc(R, pad):
    s = 2 * (R + pad)
    yy, xx = np.mgrid[0:s, 0:s] + 0.5
    return s, yy - s / 2, xx - s / 2, np.hypot(xx - s / 2, yy - s / 2)


def sun_sprite(R=22):
    """велике сонце над горизонтом: знизу вгору від помаранчевого до світло-жовтого, внизу -- прорізи-смужки"""
    s, dy, dx, d = disc(R, 4)
    a = np.zeros((s, s, 4), np.uint8)
    a[d <= R + 4] = (255, 190, 140, 50)
    a[d <= R + 2] = (255, 205, 150, 100)
    body = d <= R
    k = (dy + R) / (2 * R)                                   # -- 0 зверху, 1 знизу
    for lo, c in ((-1, (255, 248, 196)), (0.3, (255, 226, 140)), (0.52, (255, 186, 100)), (0.74, (255, 148, 86))):
        a[body & (k >= lo)] = (*c, 255)
    for y0, th in ((0.56, 1), (0.68, 1), (0.78, 2), (0.88, 2)):
        a[body & (k >= y0) & (k < y0 + th / (2 * R))] = 0    # -- прорізи: крізь них видно небо
    return upscale(a, BG_PX)


def moon_sprite(R=12):
    """повний місяць з кратерами і м'яким сяйвом"""
    s, dy, dx, d = disc(R, 4)
    a = np.zeros((s, s, 4), np.uint8)
    a[d <= R + 4] = (190, 200, 255, 26)
    a[d <= R + 2] = (210, 215, 255, 60)
    body = d <= R
    a[body] = (250, 246, 222, 255)
    a[body & (np.hypot(dx - 4, dy - 3) > R - 1)] = (222, 216, 190, 255)    # -- тінь справа знизу
    for cx, cy, r in ((-4, -3, 3.0), (3, 4, 2.2), (4, -5, 1.6), (-3, 5, 1.4)):
        a[body & (np.hypot(dx - cx, dy - cy) <= r)] = (226, 220, 192, 255)
        a[body & (np.hypot(dx - cx + 0.8, dy - cy + 0.8) <= r - 0.9) & (np.hypot(dx - cx, dy - cy) <= r)] = \
            (212, 206, 178, 255)
    return upscale(a, BG_PX)


def far_layer(h):
    return np.zeros((h // BG_PX, BG_W, 4), np.uint8)


def sunset(rng):
    far = far_layer(180)
    for (n, tops, slopes), (light, shade, rim) in zip(
            [(5, (2, 22), (0.55, 0.8)), (7, (26, 46), (0.6, 0.9)), (9, (50, 66), (0.7, 1.0))],
            [((214, 120, 150), (186, 98, 140), (255, 182, 150)), ((156, 78, 128), (132, 62, 116), (236, 130, 130)),
             ((104, 48, 102), (88, 40, 92), (176, 84, 110))]):
        mountains(far, [(x, rng.uniform(*tops), rng.uniform(*slopes)) for x in spread(n, rng)], rng,
                  light, shade, rim=rim)
    bushes = clumps(far_layer(60), rng, 26, (8, 14), (4, 10),
                    (80, 40, 86), (128, 64, 104), (56, 28, 68), (36, 16, 46))
    return {"sky": sky_gradient([(0, (44, 38, 112)), (0.3, (120, 60, 150)), (0.55, (222, 92, 130)),
                                 (0.72, (255, 150, 100)), (0.86, (255, 206, 132)), (1, (255, 226, 160))]),
            "far": far, "bushes": bushes,
            "ground": recolor_ground(lambda rgb, grass: rgb * [1.0, 0.8, 0.76] + [12, 0, 18]),
            "body": (sun_sprite(), (118, 452)), "clouds": ((206, 104, 146), (255, 216, 192), 240), "fx": []}


def night(rng):
    far = far_layer(160)
    skyline(far, rng, (8, 36), (12, 26), (38, 46, 94), (52, 62, 116), (150, 140, 110), (44, 52, 104), 0.12)
    skyline(far, rng, (30, 58), (10, 22), (22, 26, 58), (36, 42, 84), (255, 214, 110), (32, 38, 76), 0.38)
    bushes = clumps(far_layer(60), rng, 26, (8, 14), (4, 10),
                    (20, 64, 62), (36, 100, 84), (12, 44, 48), (8, 26, 34))
    return {"sky": sky_gradient([(0, (8, 10, 32)), (0.45, (22, 30, 78)), (0.76, (48, 52, 118)),
                                 (1, (86, 70, 140))]),
            "far": far, "bushes": bushes,
            "ground": recolor_ground(lambda rgb, grass: rgb * [0.4, 0.48, 0.68] + [10, 12, 34]),
            "body": (moon_sprite(), (300, 130)), "body_thumb_y": 404,
            "clouds": ((30, 36, 80), (74, 84, 146), 190), "fx": ["stars", "fireflies"]}


def winter(rng):
    far = far_layer(220)
    mountains(far, [(x, rng.uniform(0, 20), rng.uniform(0.7, 1.0)) for x in spread(5, rng)], rng,
              (160, 180, 214), (132, 152, 192), snow=(12, (246, 250, 255), (206, 222, 244)))
    mountains(far, [(x, rng.uniform(34, 56), rng.uniform(0.75, 1.1)) for x in spread(7, rng)], rng,
              (112, 132, 176), (92, 110, 156), snow=(9, (236, 244, 255), (190, 208, 236)))
    trees = far_layer(112)
    th = trees.shape[0]
    pines(trees, rng, 16, (22, 32), th - 6, (84, 128, 132), (66, 106, 116), (232, 240, 252), (196, 212, 236),
          (46, 74, 92))
    pines(trees, rng, 12, (32, 46), th - 2, (40, 108, 88), (28, 82, 74), (248, 252, 255), (206, 222, 246),
          (20, 46, 54))
    clumps(trees, rng, 22, (4, 7), (0, 2), (232, 242, 255), (252, 254, 255), (200, 216, 242), (150, 174, 214),
           aspect=1.8, leaves=False)
    return {"sky": sky_gradient([(0, (110, 170, 230)), (0.5, (170, 210, 245)), (0.8, (215, 235, 252)),
                                 (1, (236, 246, 255))]),
            "far": far, "bushes": trees, "ground": recolor_ground(snowy),
            "body": None, "clouds": None, "fx": ["snow"]}


# -- фони в порядку магазину: (id, ціна, хто малює); «день» -- звичайний фон, він є в усіх
BACKGROUNDS = [("sunset", 150, sunset), ("night", 250, night), ("winter", 350, winter)]
_layers = base_manifest["layers"]
extra["backgrounds"] = [{
    "id": "day", "price": 0, "sky": base_manifest["sky"]["file"],
    "layers": {name: {"file": _layers[name]["file"], "y": _layers[name]["y"], "factor": _layers[name]["factor"]}
               for name in ("far", "bushes", "ground")},
    "body": None, "clouds": None, "fx": [],
}]
for i, (bg_id, price, paint_bg) in enumerate(BACKGROUNDS):
    art = paint_bg(np.random.default_rng(100 + i))     # -- своє зерно: фони не залежать один від одного
    folder = f"backgrounds/{bg_id}"
    layers = {}
    for name, factor in (("far", 0.12), ("bushes", 0.45), ("ground", 1.0)):
        a = art[name] if name == "ground" else upscale(art[name], BG_PX)
        bottom = GROUND_Y + a.shape[0] if name == "ground" else LAYER_BOTTOM if name == "far" else GROUND_Y
        layers[name] = {"file": save(f"{name}.png", a, folder), "y": int(bottom - a.shape[0]), "factor": factor}
    spec = {"id": bg_id, "price": price, "sky": save("sky.png", art["sky"], folder), "layers": layers,
            "body": None, "clouds": art["clouds"] and recolor_clouds(*art["clouds"], folder), "fx": art["fx"]}
    if art["body"] is not None:
        img, (cx, cy) = art["body"]
        x, y = cx - img.shape[1] // 2, cy - img.shape[0] // 2
        spec["body"] = {"file": save("body.png", img, folder), "x": int(x), "y": int(y),
                        # -- на мініатюрі в магазині видно тільки низ неба -- там і показуємо світило
                        "thumb_y": int(art.get("body_thumb_y", cy) - img.shape[0] // 2)}
    extra["backgrounds"].append(spec)

with open(os.path.join(OUT, "extra.json"), "w", encoding="utf-8") as fh_:
    json.dump(extra, fh_, ensure_ascii=False, indent=2)
print("готово ->", os.path.join(OUT, "extra.json"))
