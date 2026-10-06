import math
import os
import random
import pygame

import settings
from audio import Music, Sounds
from display import Display, enable_dpi_awareness
from sprites import SpriteKit

# -- карочє тут путь к файлікам
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
FONT_PATH = os.path.join(ASSETS_DIR, "fonts", "OutlineStyleRegular.ttf")
SPRITES_DIR = os.path.join(ASSETS_DIR, "sprites")   # готовые спрайты (tools/make_sprites.py)
MUSIC_DIR = os.path.join(ASSETS_DIR, "music")
SOUNDS_DIR = os.path.join(ASSETS_DIR, "sounds")
SETTINGS_PATH = os.path.join(BASE_DIR, "settings.json")   # -- тут зберігаються мова, вікно і гучність
SAVE_PATH = os.path.join(BASE_DIR, "save.json")           # -- рекорд і монетки

# -- віконечко: ігрове поле 400x700 завжди по центру, а небо/земля/труби тягнуться на всю ширину вікна
# -- (src/display.py). Координати в грі -- відносно ігрового поля, VIEW_X -- його зсув на полотні
WIDTH, HEIGHT = 400, 700
FPS = 60

GRAVITY = 0.4 # -- гравітація
JUMP_VELOCITY = -8
BIRD_START_X, BIRD_START_Y = 80, 300 # -- позиція пташки
BIRD_SIZE = 30  # ну типу хітбокс пташки по осі x+y
BIRD_MAX_UP = 25        # -- градуси: наскільки пташка задирає дзьоб при стрибку
BIRD_MAX_DOWN = -75     # -- і наскільки опускає при падінні

PIPE_WIDTH = 70
PIPE_GAP = 150
PIPE_SPEED = 3
PIPE_SPACING_X = 250
PIPE_GAP_Y_RANGE = (150, 450)

# -- монетки
COIN_CHANCE_GAP = 0.6       # -- шанс, що в проході труби буде монетка
COIN_CHANCE_BETWEEN = 0.3   # -- шанс монетки між двома трубами
COIN_GAP_JITTER = 35        # -- на скільки px монетка може бути вище/нижче центру проходу
COIN_HITBOX = 24
COIN_PICKUP_TIME = 0.35     # -- сек, анімація підбору
COIN_FPS = 10

# -- бонуси: щит рятує від одного удару, сповільнення на кілька секунд пригальмовує світ,
# -- x2 -- кожна монетка рахується за дві
POWERUP_CHANCE = 0.18       # -- шанс бонусу між двома трубами (тоді монетки там нема)
POWERUP_HITBOX = 30
POWERUP_BOB = 4             # -- px, наскільки бонус гойдається вгору-вниз
BOOST_TIME = {"slow": 5.0, "x2": 10.0}   # -- сек, скільки діють бонуси з таймером
BOOST_COLORS = {"slow": ((176, 112, 255), (220, 190, 255)),    # -- смужка часу: колір і блік
                "x2": ((255, 196, 50), (255, 236, 150))}
SLOW_FACTOR = 0.55          # -- швидкість труб і фону під час сповільнення (1.0 = звичайна)
SLOW_TINT = (70, 30, 150)   # -- екран трохи фіолетовіє, поки діє сповільнення
SLOW_TINT_ALPHA = 45
SHIELD_GRACE = 1.0          # -- сек невразливості після того, як щит лопнув (пташка блимає)
SHIELD_POP_TIME = 0.35      # -- сек, анімація лопання щита
POWERUP_HUD_Y = 72          # -- де під лічильником монет показуються активні бонуси
POWERUP_HUD_STEP = 44       # -- відстань між рядками бонусів з таймером

TRAIL_LIFE = 0.6            # -- сек, скільки живе точка шлейфу (довжина шлейфу)

MENU_SCROLL_SPEED = 60     # -- px/сек, як швидко їде земля в меню (місто і кущі повільніше)
GAME_OVER_ANIM = 0.45      # -- сек, за скільки виїжджає напис GAME OVER і кнопка MENU

PRESS_ACTION_DELAY = 120   # -- показний що відповідає за затемнення (типу анімація)
FADE_SPEED = 12   #  -- тут просто швидкість затемнення

# -- тут просто хітбокси для кліків в меню
PLAY_BTN = pygame.Rect(65, 360, 270, 62)
SHOP_BTN = pygame.Rect(65, 440, 270, 62)
RECORD_BTN = pygame.Rect(65, 520, 270, 62)
SETTINGS_BTN = pygame.Rect(328, 8, 56, 56)

# -- сайз кнопки що зявляється після смерті
MENU_BTN_SIZE = (220, 94)

# -- панелі: рамка зверху тонша, знизу товща (там тінь) -- рядки рахуємо всередині
PANEL_INNER_TOP = 8
PANEL_INNER_BOTTOM = 16

# -- екран після смерті: напис, панель з рахунком, кнопка MENU
GAME_OVER_Y = 190
RESULT_PANEL = pygame.Rect(62, 226, 276, 150)
MENU_BTN_RECT = pygame.Rect(0, 0, *MENU_BTN_SIZE)
MENU_BTN_RECT.midtop = (WIDTH // 2, RESULT_PANEL.bottom + 34)

# -- екран рекордів
RECORDS_TITLE_Y = 70
RECORDS_PANEL = pygame.Rect(40, 112, 320, 326)

# -- магазин: вкладки ПТАШКИ | ШЛЕЙФИ, під ними вікно з картками по 2 в ряд (4 картки -- рівно 2x2);
# -- якщо рядів більше -- гортається коліщатком
SHOP_TITLE_Y = 80
SHOP_TABS = {"birds": pygame.Rect(14, 106, 182, 46),     # -- висота панелі не менша за 2 рамки (2 * 22)
             "trails": pygame.Rect(204, 106, 182, 46)}
SHOP_PANEL = pygame.Rect(14, 156, 372, 328)
SHOP_COLS = 2
CARD_W, CARD_H, CARD_GAP = 164, 137, 10
CARD_PAD_TOP = 10
SHOP_SCROLL_STEP = 40
NOT_ENOUGH_TIME = 1.6      # -- сек, скільки висить «недостатньо монет»
CARD_PREVIEW = (124, 86)   # -- у яку рамку вписується пташка на картці
TRAIL_PREVIEW = (70, 60)   # -- пташка на картці шлейфу менша -- позаду неї ще шлейф
TAB_DIM = 0.78             # -- неактивна вкладка темніша

# -- екран налаштувань: панель з 5 рядками (підпис + перемикач або повзунок)
SETTINGS_TITLE_Y = 56
SETTINGS_PANEL = pygame.Rect(24, 90, 352, 446)
ROW_Y0 = SETTINGS_PANEL.y + 20
ROW_H = 84
ROWS = ["language", "window_size", "menu_music", "game_music", "sounds"]
SELECTORS = {                                 # -- перемикачі зі стрілками < ... >
    "lang": pygame.Rect(52, ROW_Y0 + 0 * ROW_H + 30, 296, 44),
    "window": pygame.Rect(52, ROW_Y0 + 1 * ROW_H + 30, 296, 44),
}
SELECTOR_ARROW = 46   # -- ширина зони стрілки з кожного боку
SLIDERS = {                                   # -- повзунки гучності: доріжка
    "menu_music": pygame.Rect(58, ROW_Y0 + 2 * ROW_H + 46, 214, 16),
    "game_music": pygame.Rect(58, ROW_Y0 + 3 * ROW_H + 46, 214, 16),
    "sfx": pygame.Rect(58, ROW_Y0 + 4 * ROW_H + 46, 214, 16),
}
SLIDER_LABELS = {"menu_music": "menu_music", "game_music": "game_music", "sfx": "sounds"}
SLIDER_GRAB = 14      # -- на скільки px навколо доріжки ще можна схопити повзунок
BACK_BTN_RECT = pygame.Rect(0, 0, *MENU_BTN_SIZE)
BACK_BTN_RECT.midtop = (WIDTH // 2, SETTINGS_PANEL.bottom + 6)
RECORDS_BACK_RECT = pygame.Rect(0, 0, *MENU_BTN_SIZE)
RECORDS_BACK_RECT.midtop = (WIDTH // 2, RECORDS_PANEL.bottom + 14)
SHOP_BACK_RECT = pygame.Rect(0, 0, *MENU_BTN_SIZE)
SHOP_BACK_RECT.midtop = (WIDTH // 2, SHOP_PANEL.bottom + 24)

# -- лічильник монет у меню
COINS_CHIP = pygame.Rect(10, 12, 128, 46)

MUSIC_MAX_VOLUME = 0.5    # -- гучність музики при повзунку на 100% (1.0 = максимум pygame)
SFX_MAX_VOLUME = 0.6

# -- кольори
COLOR_TEXT_SHADOW = (65, 40, 70)
COLOR_TEXT_MAIN = (255, 255, 255)

PRESS_OVERLAY_MAX_ALPHA = 70   # -- наскільки темнішає кнопка при натисканні (0..255)

COLOR_OUTLINE = (45, 16, 40)
COLOR_SLIDER_BACK = (150, 96, 60)
COLOR_SLIDER_FILL = (86, 180, 50)
COLOR_SLIDER_SHINE = (160, 225, 100)
COLOR_KNOB = (255, 236, 200)
COLOR_KNOB_SHADE = (240, 180, 90)
COLOR_ARROW = (70, 175, 50)
COLOR_ARROW_HOVER = (120, 215, 80)
COLOR_CARD_HOVER = (255, 255, 255)

# -- пайгейм, ресурси
enable_dpi_awareness()
pygame.mixer.pre_init(44100, -16, 2, 1024)
pygame.init()

config = settings.load(SETTINGS_PATH)
progress = settings.load(SAVE_PATH, settings.PROGRESS_DEFAULTS)

display = Display(WIDTH, HEIGHT, "Flappy Bird")
config["window"] = display.apply(config["window"])
view = display.view       # -- все полотно (на всю ширину вікна)
screen = display.screen   # -- ігрове поле 400x700 по центру полотна
VIEW_X = display.ox
clock = pygame.time.Clock()

title_font = pygame.font.Font(FONT_PATH, 48)

# -- анімовані спрайти: фон, хмари, заголовок, кнопки (див. src/sprites.py)
kit = SpriteKit(SPRITES_DIR, press_dark=PRESS_OVERLAY_MAX_ALPHA / 255)
scenery = kit.scenery
kit.set_lang(config["lang"])

# -- скін: стара гра могла зберегти пташку, якої вже нема -- тоді класична
if "classic" not in progress["owned"]:
    progress["owned"].insert(0, "classic")
if progress["skin"] not in progress["owned"]:
    progress["skin"] = "classic"
progress["skin"] = kit.set_skin(progress["skin"])
if "none" not in progress["owned_trails"]:
    progress["owned_trails"].insert(0, "none")
if progress["trail"] not in progress["owned_trails"]:
    progress["trail"] = "none"
progress["trail"] = kit.set_trail(progress["trail"])
GROUND_Y = kit.ground_y   # -- з цієї висоти починається земля, пташка про неї розбивається

music = Music({"menu": os.path.join(MUSIC_DIR, "menu.mp3"),
               "game": os.path.join(MUSIC_DIR, "game.mp3")},
              max_volume=MUSIC_MAX_VOLUME)
music.set_level("menu", config["menu_music"])
music.set_level("game", config["game_music"])

sfx = Sounds({name: os.path.join(SOUNDS_DIR, name + ".wav") for name in ("coin", "powerup", "shield_break")},
             max_volume=SFX_MAX_VOLUME)
sfx.set_level(config["sfx"])

# -- який спрайт малює яку кнопку меню
MENU_SPRITES = {
    "play": kit.play,
    "shop": kit.shop,
    "record": kit.record,
    "settings": kit.settings,
}

# -- хітбокси кнопок в одному місці
MENU_BUTTONS = {
    "play": PLAY_BTN,
    "shop": SHOP_BTN,
    "record": RECORD_BTN,
    "settings": SETTINGS_BTN,
}

bird_y = BIRD_START_Y
bird_v = 0

pipes = []
coins = []          # -- [x центру, y центру, фаза анімації, час після підбору або None, скільки дала монет]
score = 0
run_coins = 0       # -- монетки, зібрані за цю гру
powerups = []       # -- бонуси на полі: [x центру, y центру, "shield"/"slow", фаза, час після підбору або None]
shield = False      # -- чи є щит
grace = 0.0         # -- скільки ще секунд невразливості після удару щитом
boost = {kind: 0.0 for kind in BOOST_TIME}   # -- скільки ще секунд діє сповільнення / x2
trail_pts = []      # -- точки шлейфу: [x, y, вік, випадкове 0..1]
speed_k = 1.0       # -- поточний множник швидкості світу (плавно йде до SLOW_FACTOR і назад)
pops = []           # -- лопнуті щити: [x, y, час після удару]
new_record = False
run_saved = True    # -- чи вже записали результат цієї гри

start = False
over = False

in_settings = False
in_records = False
in_shop = False
shop_tab = "birds"  # -- вкладка магазину: "birds" або "trails"
shop_scroll = 0
not_enough = 0.0    # -- таймер напису «недостатньо монет»
dragging = None     # -- який повзунок тягнуть мишкою

pressed = None      # -- яку кнопку тримають
press_time = 0

fade = 0
fading = False

t_total = 0.0       # -- загальний час у секундах, від нього рахуються всі анімації
over_time = 0.0     # -- скільки секунд пройшло після смерті


# -- доп функціонал
def add_pipe(x):
    """нова труба + можливо монетки: у проході і між нею та попередньою трубою"""
    gap_y = random.randint(*PIPE_GAP_Y_RANGE)
    prev = pipes[-1] if pipes else None
    pipes.append([x, gap_y, False])

    if random.random() < COIN_CHANCE_GAP:
        cy = gap_y + PIPE_GAP // 2 + random.randint(-COIN_GAP_JITTER, COIN_GAP_JITTER)
        coins.append([x + PIPE_WIDTH / 2, cy, random.random() * 8, None, 1])

    if not prev:
        return
    mid_x = (prev[0] + x) / 2 + PIPE_WIDTH / 2
    mid_y = (prev[1] + gap_y) / 2 + PIPE_GAP // 2 + random.randint(-30, 30)
    kinds = free_powerups()
    if kinds and random.random() < POWERUP_CHANCE:
        powerups.append([mid_x, mid_y, random.choice(kinds), random.random() * 6, None])
    elif random.random() < COIN_CHANCE_BETWEEN:
        coins.append([mid_x, mid_y, random.random() * 8, None, 1])


def free_powerups():
    """які бонуси можна поставити: не той, що вже діє, і не той, що вже чекає на полі"""
    waiting = {p[2] for p in powerups if p[4] is None}
    kinds = []
    if not shield and "shield" not in waiting:
        kinds.append("shield")
    kinds += [kind for kind, left in boost.items() if left <= 0 and kind not in waiting]
    return kinds


def powerup_y(p):
    """бонус гойдається вгору-вниз (і хітбокс разом з ним)"""
    return p[1] + math.sin(t_total * 3 + p[3]) * POWERUP_BOB


def fill_pipes():
    """додаємо труби, поки не заповнимо все видиме полотно праворуч (на широкому екрані їх більше)"""
    right = WIDTH + VIEW_X
    while not pipes or pipes[-1][0] <= right:
        add_pipe(pipes[-1][0] + PIPE_SPACING_X if pipes else WIDTH)


def new_pipes():
    """генерація труб"""
    pipes.clear()
    coins.clear()
    powerups.clear()
    fill_pipes()


def draw_text(text, font, x, y):
    """текст + тінь та місце розташування"""
    shadow = font.render(text, True, COLOR_TEXT_SHADOW)
    main = font.render(text, True, COLOR_TEXT_MAIN)

    screen.blit(shadow, (x - shadow.get_width() // 2 + 2, y - shadow.get_height() // 2 + 3))
    screen.blit(main, (x - main.get_width() // 2, y - main.get_height() // 2))


def blit_center(img, x, y):
    screen.blit(img, img.get_rect(center=(int(x), int(y))))


def draw_bird(x, y, v):
    """спрайт пташки по центру хітбокса, нахил залежить від швидкості"""
    angle = max(BIRD_MAX_DOWN, min(BIRD_MAX_UP, -v * 4))
    cx, cy = x + BIRD_SIZE / 2, y + BIRD_SIZE / 2
    # -- після удару щитом пташка блимає, поки невразлива
    if not (grace > 0 and not over and int(grace * 12) % 2):
        kit.bird.draw(screen, cx, cy, angle)
    if shield:
        blit_center(kit.aura.frame(), cx, cy)
    # -- лопнутий щит: бульбашка роздувається і зникає
    for px, py, t in pops:
        k = t / SHIELD_POP_TIME
        img = kit.aura.frames[0]
        img = pygame.transform.scale(img, (int(img.get_width() * (1 + 0.6 * k)),
                                           int(img.get_height() * (1 + 0.6 * k))))
        img.set_alpha(int(255 * (1 - k)))
        blit_center(img, px, py)


def draw_powerups():
    """бонуси на полі (на всьому полотні, як монетки); підібраний -- летить вгору і зникає"""
    for p in powerups:
        x, taken = p[0] + VIEW_X, p[4]
        img = kit.powerups[p[2]].frame()
        if taken is None:
            view.blit(img, img.get_rect(center=(int(x), int(powerup_y(p)))))
        else:
            k = taken / COIN_PICKUP_TIME
            img = pygame.transform.scale(img, (int(img.get_width() * (1 + 0.5 * k)),
                                               int(img.get_height() * (1 + 0.5 * k))))
            img.set_alpha(int(255 * (1 - k)))
            view.blit(img, img.get_rect(center=(int(x), int(p[1] - 34 * k))))


def draw_powerup_hud():
    """активні бонуси під лічильником монет, кожен у своєму рядку: щит -- іконка,
    сповільнення і x2 -- іконка і смужка часу (за 1.5 сек до кінця смужка блимає)"""
    x, y = 10, POWERUP_HUD_Y
    if shield:
        img = kit.powerups["shield"].frames[0]
        screen.blit(img, (x, y - img.get_height() // 2))
        y += POWERUP_HUD_STEP
    for kind, left in boost.items():
        if left <= 0:
            continue
        img = kit.powerups[kind].frame()
        screen.blit(img, (x, y - img.get_height() // 2))
        if not (left < 1.5 and int(left * 8) % 2):
            draw_timer_bar(pygame.Rect(x + img.get_width() + 6, y - 5, 60, 10), left / BOOST_TIME[kind],
                           *BOOST_COLORS[kind])
        y += POWERUP_HUD_STEP


def draw_timer_bar(bar, value, color, shine):
    fill_w = int(bar.width * value)
    pygame.draw.rect(screen, COLOR_OUTLINE, bar.inflate(6, 6), border_radius=6)
    pygame.draw.rect(screen, COLOR_SLIDER_BACK, bar, border_radius=4)
    if fill_w > 0:
        pygame.draw.rect(screen, color, (bar.x, bar.y, fill_w, bar.height), border_radius=4)
        pygame.draw.rect(screen, shine, (bar.x + 2, bar.y + 2, max(0, fill_w - 4), 2))


_tint = None


def draw_slow_tint():
    """поки діє сповільнення, все трохи фіолетовіє (плавно з'являється і зникає разом зі швидкістю)"""
    global _tint
    k = (1 - speed_k) / (1 - SLOW_FACTOR)
    if k < 0.02:
        return
    if _tint is None or _tint.get_size() != view.get_size():
        _tint = pygame.Surface(view.get_size())
        _tint.fill(SLOW_TINT)
    _tint.set_alpha(int(SLOW_TINT_ALPHA * min(1.0, k)))
    view.blit(_tint, (0, 0))


def take_powerup(kind):
    global shield
    if kind == "shield":
        shield = True
    else:
        boost[kind] = BOOST_TIME[kind]
    sfx.play("powerup")


def hit():
    """удар об трубу / землю / стелю: щит лопає і дає секунду невразливості, без щита -- кінець гри"""
    global over, shield, grace
    if grace > 0:
        return
    if shield:
        shield = False
        grace = SHIELD_GRACE
        pops.append([BIRD_START_X + BIRD_SIZE / 2, bird_y + BIRD_SIZE / 2, 0.0])
        sfx.play("shield_break")
    else:
        over = True


def draw_coins():
    """монетки малюються на всьому полотні (як і труби)"""
    frames = kit.coin.frames
    for x, y, phase, taken, value in coins:
        img = frames[int(t_total * COIN_FPS + phase) % len(frames)]
        x += VIEW_X
        if taken is None:
            view.blit(img, img.get_rect(center=(int(x), int(y))))
        else:
            # -- підібрана: летить вгору, трохи росте і зникає
            k = taken / COIN_PICKUP_TIME
            s = 1 + 0.5 * k
            img = pygame.transform.scale(img, (int(img.get_width() * s), int(img.get_height() * s)))
            img.set_alpha(int(255 * (1 - k)))
            view.blit(img, img.get_rect(center=(int(x), int(y - 34 * k))))
            if value > 1:               # -- з x2 над монеткою вилітає «+2»
                plus = number_image(f"+{value}")
                plus.set_alpha(int(255 * (1 - k * k)))
                view.blit(plus, plus.get_rect(center=(int(x), int(y - 22 - 40 * k))))


_number_cache = {}


def number_image(text, style="light"):
    """число зі спрайтів-цифр як окрема картинка (щоб можна було зробити напівпрозорим)"""
    if (text, style) not in _number_cache:
        h = max(img.get_height() for img in kit.digits[style].values())
        img = pygame.Surface((kit.number_width(text, style), h), pygame.SRCALPHA)
        kit.draw_number(img, text, 0, h // 2, style=style, align="left")
        _number_cache[(text, style)] = img
    return _number_cache[(text, style)].copy()


def counter_width(icon, value):
    return icon.get_width() + 6 + kit.number_width(str(value))


def draw_counter(icon, value, x, y):
    """іконка + число (світлі цифри), x -- лівий край, y -- центр"""
    blit_center(icon, x + icon.get_width() // 2, y)
    kit.draw_number(screen, str(value), x + icon.get_width() + 6, y, align="left")


def draw_row(panel, y, key, value, icon=None):
    """рядок панелі: підпис зліва, значення (і іконка) справа, все по центру y"""
    label = kit.text(key)
    screen.blit(label, (panel.x + 26, y - label.get_height() // 2))
    value = str(value)
    if icon is None:
        kit.draw_number(screen, value, panel.right - 26, y, align="right")
    else:
        draw_counter(icon, value, panel.right - 26 - counter_width(icon, value), y)


def panel_rows(panel, n):
    """y центрів n рядків, рівномірно всередині панелі"""
    top = panel.y + PANEL_INNER_TOP
    h = panel.height - PANEL_INNER_TOP - PANEL_INNER_BOTTOM
    return [round(top + h * (i + 0.5) / n) for i in range(n)]


def finish_run():
    """смерть: оновлюємо рекорд і зберігаємо прогрес"""
    global new_record, run_saved

    if run_saved:
        return
    new_record = score > progress["best"]
    if new_record:
        progress["best"] = score
    progress["games"] += 1
    settings.save(SAVE_PATH, progress)
    run_saved = True


# -- налаштування
def slider_value(name, mouse_x):
    rect = SLIDERS[name]
    return max(0.0, min(1.0, (mouse_x - rect.x) / rect.width))


def set_slider(name, value):
    config[name] = round(value, 2)
    if name == "sfx":
        sfx.set_level(config[name])
    else:
        music.set_level(name.split("_")[0], config[name])


def selector_options(name):
    return list(kit.LANGS) if name == "lang" else display.options()


def selector_current(name):
    return config["lang"] if name == "lang" else display.mode


def selector_step(name, step):
    """перемикає вибір вперед/назад по колу"""
    options = selector_options(name)
    cur = selector_current(name)
    i = options.index(cur) if cur in options else 0
    value = options[(i + step) % len(options)]
    if name == "lang":
        config["lang"] = value
        kit.set_lang(value)
    else:
        config["window"] = display.apply(value)
    settings.save(SETTINGS_PATH, config)


def draw_slider(name):
    rect = SLIDERS[name]
    value = config[name]
    fill_w = int(rect.width * value)

    pygame.draw.rect(screen, COLOR_OUTLINE, rect.inflate(6, 6), border_radius=6)
    pygame.draw.rect(screen, COLOR_SLIDER_BACK, rect, border_radius=4)
    if fill_w > 0:
        pygame.draw.rect(screen, COLOR_SLIDER_FILL, (rect.x, rect.y, fill_w, rect.height), border_radius=4)
        pygame.draw.rect(screen, COLOR_SLIDER_SHINE, (rect.x + 3, rect.y + 3, max(0, fill_w - 6), 3))

    # -- ручка
    knob = pygame.Rect(0, 0, 22, 30)
    knob.center = (rect.x + fill_w, rect.centery)
    pygame.draw.rect(screen, COLOR_OUTLINE, knob.inflate(6, 6), border_radius=7)
    pygame.draw.rect(screen, COLOR_KNOB_SHADE, knob, border_radius=5)
    pygame.draw.rect(screen, COLOR_KNOB, (knob.x, knob.y, knob.width, knob.height - 6), border_radius=5)

    kit.draw_number(screen, f"{round(value * 100)}%", SETTINGS_PANEL.right - 44, rect.centery, style="dark")


def draw_arrow(cx, cy, direction, hover):
    """зелений трикутник-стрілка з контуром (як іконка PLAY)"""
    w, h = 12, 14
    pts = [(cx - w * direction, cy - h), (cx + w * direction, cy), (cx - w * direction, cy + h)]
    pygame.draw.polygon(screen, COLOR_OUTLINE, pts)
    inner = [(cx - (w - 4) * direction, cy - h + 6), (cx + (w - 5) * direction, cy),
             (cx - (w - 4) * direction, cy + h - 6)]
    pygame.draw.polygon(screen, COLOR_ARROW_HOVER if hover else COLOR_ARROW, inner)


def selector_label(name, value):
    """картинка з назвою поточного варіанту перемикача"""
    if name == "lang":
        return kit.lang_names[value]
    if value in ("auto", "fullscreen"):
        return kit.text(value)
    return None     # -- розмір вікна малюється цифрами


def draw_selector(name, mouse_pos):
    rect = SELECTORS[name]
    screen.blit(kit.panel.render(rect.width, rect.height), rect)
    value = selector_current(name)

    label = selector_label(name, value)
    if label is not None:
        blit_center(label, rect.centerx, rect.centery - 1)
    else:
        w, h = display.size_for(value)
        kit.draw_number(screen, f"{w}×{h}", rect.centerx, rect.centery - 1)

    left = pygame.Rect(rect.x, rect.y, SELECTOR_ARROW, rect.height)
    right = pygame.Rect(rect.right - SELECTOR_ARROW, rect.y, SELECTOR_ARROW, rect.height)
    draw_arrow(left.centerx + 2, rect.centery - 1, -1, left.collidepoint(mouse_pos))
    draw_arrow(right.centerx - 2, rect.centery - 1, 1, right.collidepoint(mouse_pos))


def draw_settings(mouse_pos):
    blit_center(kit.text("settings"), WIDTH // 2, SETTINGS_TITLE_Y)
    screen.blit(kit.panel.render(SETTINGS_PANEL.width, SETTINGS_PANEL.height), SETTINGS_PANEL)

    for i, key in enumerate(ROWS):
        screen.blit(kit.text(key), (SETTINGS_PANEL.x + 26, ROW_Y0 + i * ROW_H))

    for name in SELECTORS:
        draw_selector(name, mouse_pos)
    for name in SLIDERS:
        draw_slider(name)


def settings_click(x, y):
    global dragging, pressed, press_time

    for name, rect in SELECTORS.items():
        if rect.collidepoint(x, y):
            selector_step(name, -1 if x < rect.x + SELECTOR_ARROW else 1)
            return
    for name, rect in SLIDERS.items():
        if rect.inflate(SLIDER_GRAB * 2, SLIDER_GRAB * 2).collidepoint(x, y):
            dragging = name
            set_slider(name, slider_value(name, x))
            return
    if BACK_BTN_RECT.collidepoint(x, y):
        pressed, press_time = "back", 0


# -- екрани
def draw_menu_counters():
    """монетки зліва вгорі (стануть валютою магазину)"""
    screen.blit(kit.panel.render(COINS_CHIP.width, COINS_CHIP.height), COINS_CHIP)
    draw_counter(kit.coin_icon, progress["coins"], COINS_CHIP.x + 12, COINS_CHIP.centery - 3)


def draw_result(slide):
    """панель після смерті: рахунок, рекорд, монетки за гру"""
    panel = RESULT_PANEL.move(0, slide)
    screen.blit(kit.panel.render(panel.width, panel.height), panel)

    y_score, y_best, y_coins = panel_rows(panel, 3)
    draw_row(panel, y_score, "score", score)
    draw_row(panel, y_best, "best", progress["best"])
    draw_row(panel, y_coins, "coins", f"+{run_coins}", icon=kit.coin_icon)

    if new_record:
        bob = round(math.sin(t_total * 6) * 3)
        blit_center(kit.text("new_record"), WIDTH // 2, panel.bottom + 16 + bob)


def draw_records():
    """екран рекордів: кубок, найкращий рахунок великими цифрами, скільки ігор і монет"""
    blit_center(kit.text("records"), WIDTH // 2, RECORDS_TITLE_Y)
    panel = RECORDS_PANEL
    screen.blit(kit.panel.render(panel.width, panel.height), panel)

    trophy = kit.trophy_big
    bob = round(math.sin(t_total * 2.4) * 3)
    blit_center(trophy, WIDTH // 2, panel.y + 26 + trophy.get_height() // 2 + bob)
    kit.draw_number(screen, str(progress["best"]), WIDTH // 2, panel.y + 150, style="big", gap=3)

    rows = pygame.Rect(panel.x, panel.y + 190, panel.width, panel.height - 190)
    y_games, y_coins = panel_rows(rows, 2)
    pygame.draw.line(screen, COLOR_KNOB_SHADE, (panel.x + 24, rows.y), (panel.right - 24, rows.y), 2)
    draw_row(panel, y_games, "games", progress["games"])
    draw_row(panel, y_coins, "coins", progress["coins"], icon=kit.coin_icon)


# -- магазин: на кожній вкладці -- що продається, де в збереженні обране і куплене
SHOP = {
    "birds": {"items": kit.skins, "pick": "skin", "owned": "owned", "set": kit.set_skin},
    "trails": {"items": kit.trails, "pick": "trail", "owned": "owned_trails", "set": kit.set_trail},
}


def shop_cards():
    """(товар, прямокутник картки) поточної вкладки з урахуванням прокрутки"""
    x0 = SHOP_PANEL.x + (SHOP_PANEL.width - SHOP_COLS * CARD_W - (SHOP_COLS - 1) * CARD_GAP) // 2
    y0 = SHOP_PANEL.y + CARD_PAD_TOP - shop_scroll
    for i, item in enumerate(SHOP[shop_tab]["items"]):
        row, col = divmod(i, SHOP_COLS)
        yield item, pygame.Rect(x0 + col * (CARD_W + CARD_GAP), y0 + row * (CARD_H + CARD_GAP), CARD_W, CARD_H)


def shop_view():
    """видима частина вікна магазину (все, що нижче/вище -- обрізається)"""
    return pygame.Rect(SHOP_PANEL.x, SHOP_PANEL.y + PANEL_INNER_TOP,
                       SHOP_PANEL.width, SHOP_PANEL.height - PANEL_INNER_TOP - PANEL_INNER_BOTTOM)


def shop_max_scroll():
    rows = (len(SHOP[shop_tab]["items"]) + SHOP_COLS - 1) // SHOP_COLS
    content = CARD_PAD_TOP * 2 + rows * CARD_H + (rows - 1) * CARD_GAP
    return max(0, content - shop_view().height)


def shop_click(x, y):
    """клік по вкладці -- перемикаємо; по картці -- купити (якщо вистачає монет) або обрати"""
    global not_enough, shop_tab, shop_scroll

    for name, rect in SHOP_TABS.items():
        if rect.collidepoint(x, y):
            shop_tab, shop_scroll, not_enough = name, 0, 0.0
            return
    if not shop_view().collidepoint(x, y):
        return
    tab = SHOP[shop_tab]
    owned = progress[tab["owned"]]
    for item, rect in shop_cards():
        if not rect.collidepoint(x, y):
            continue
        if item.id not in owned:
            if progress["coins"] < item.price:
                not_enough = NOT_ENOUGH_TIME
                return
            progress["coins"] -= item.price
            owned.append(item.id)
            sfx.play("coin")
        progress[tab["pick"]] = tab["set"](item.id)
        settings.save(SAVE_PATH, progress)
        return


_preview_cache = {}


def card_preview(bird, i, frame_box=CARD_PREVIEW):
    """
    кадр пташки, збільшений під рамку frame_box. Порожні краї кадрів (запас під крила) обрізаємо --
    одна рамка на всі кадри, щоб пташка не смикалась. Піксель-арт збільшуємо так, щоб кожен
    художній піксель став цілим числом пікселів -- тоді картинка не розмивається.
    """
    key = (bird.id, i, frame_box)
    if key not in _preview_cache:
        box = bird.anim.frames[0].get_bounding_rect().unionall(
            [f.get_bounding_rect() for f in bird.anim.frames])
        img = bird.anim.frames[i].subsurface(box)
        k = min(frame_box[0] / img.get_width(), frame_box[1] / img.get_height())
        if bird.art_px and k >= 1:
            k = max(1, math.floor(k * bird.art_px)) / bird.art_px
        elif k >= 2:
            k = int(k)
        size = (round(img.get_width() * k), round(img.get_height() * k))
        crisp = bird.art_px or k == int(k)
        _preview_cache[key] = (pygame.transform.scale if crisp else pygame.transform.smoothscale)(img, size)
    return _preview_cache[key]


def draw_trail_preview(trail, rect):
    """картка шлейфу: обрана пташка гойдається, а за нею тягнеться шлейф (там, де вона щойно була)"""
    bird = kit.bird
    img = card_preview(bird, int(t_total * bird.anim.fps) % len(bird.anim.frames), TRAIL_PREVIEW)
    bx = rect.right - 14 - img.get_width() // 2

    def wave_y(t):
        return rect.y + 50 + math.sin(t * 3) * 8

    n, length = 24, bx - rect.x - 2
    pts = [(bx - 6 - length * j / n, wave_y(t_total - 0.8 * j / n), j / n, (j * 0.618) % 1)
           for j in range(n + 1)]
    screen.set_clip(rect.inflate(-6, -6).clip(shop_view()))
    trail.draw(screen, pts, t_total)
    screen.set_clip(shop_view())
    blit_center(img, bx, wave_y(t_total))


def draw_card(item, rect, mouse_pos):
    tab = SHOP[shop_tab]
    selected = item.id == progress[tab["pick"]]
    owned = item.id in progress[tab["owned"]]

    screen.blit(kit.panel.render(rect.width, rect.height), rect)
    if selected:
        pygame.draw.rect(screen, COLOR_ARROW, rect.inflate(-4, -6).move(0, -2), 3, border_radius=8)
    elif rect.collidepoint(mouse_pos) and shop_view().collidepoint(mouse_pos):
        pygame.draw.rect(screen, COLOR_CARD_HOVER, rect.inflate(-4, -6).move(0, -2), 2, border_radius=8)

    if shop_tab == "birds":
        # -- пташка махає крилами (кожна зі своєю швидкістю кадрів)
        i = int(t_total * item.anim.fps) % len(item.anim.frames)
        blit_center(card_preview(item, i), rect.centerx, rect.y + 50)
    else:
        draw_trail_preview(item, rect)

    y = rect.bottom - 34
    if selected:
        blit_center(kit.text("selected"), rect.centerx, y)
    elif owned:
        blit_center(kit.text("select"), rect.centerx, y)
    else:
        price = str(item.price)
        w = counter_width(kit.coin_icon, price)
        draw_counter(kit.coin_icon, price, rect.centerx - w // 2, y)


def draw_tabs(mouse_pos):
    """вкладки ПТАШКИ | ШЛЕЙФИ: активна -- з зеленою рамкою, інша -- трохи темніша"""
    for name, rect in SHOP_TABS.items():
        img = kit.panel.render(rect.width, rect.height)
        active = name == shop_tab
        if not active:
            img = img.copy()
            m = int(255 * TAB_DIM)
            img.fill((m, m, m), special_flags=pygame.BLEND_RGB_MULT)
        screen.blit(img, rect)
        frame = rect.inflate(-4, -6).move(0, -2)
        if active:
            pygame.draw.rect(screen, COLOR_ARROW, frame, 3, border_radius=8)
        elif rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, COLOR_CARD_HOVER, frame, 2, border_radius=8)
        blit_center(kit.text("tab_" + name), rect.centerx, rect.centery - 3)


def draw_shop(mouse_pos):
    blit_center(kit.text("shop_title"), WIDTH // 2, SHOP_TITLE_Y)
    draw_tabs(mouse_pos)
    screen.blit(kit.panel.render(SHOP_PANEL.width, SHOP_PANEL.height), SHOP_PANEL)

    screen.set_clip(shop_view())
    for item, rect in shop_cards():
        draw_card(item, rect, mouse_pos)
    screen.set_clip(None)

    # -- смужка прокрутки, якщо карток більше, ніж влазить
    top = shop_max_scroll()
    if top > 0:
        view_rect = shop_view()
        h = max(30, view_rect.height * view_rect.height // (view_rect.height + top))
        y = view_rect.y + (view_rect.height - h) * shop_scroll // top
        pygame.draw.rect(screen, COLOR_KNOB_SHADE, (SHOP_PANEL.right - 12, y, 5, h), border_radius=3)

    if not_enough > 0 and int((NOT_ENOUGH_TIME - not_enough) * 6) % 2 == 0:
        blit_center(kit.text("not_enough"), WIDTH // 2, SHOP_PANEL.bottom + 10)


def reset_game():
    global bird_y, bird_v, score, over, start, run_coins, new_record, run_saved
    global shield, grace, speed_k

    bird_y = BIRD_START_Y
    bird_v = 0
    score = 0
    run_coins = 0
    new_record = False
    run_saved = False
    over = False
    start = True
    shield = False
    grace = 0.0
    for kind in boost:
        boost[kind] = 0.0
    speed_k = 1.0
    pops.clear()
    trail_pts.clear()

    new_pipes()
    scenery.update(0, PIPE_SPEED * FPS, snap=True)   # -- фон їде з тією ж швидкістю, що й труби


def go_to_menu():
    """повертання в головне меню після смерті"""
    global start, over

    start = False
    over = False


def close_settings():
    """повернення в головне меню з налаштувань / рекордів / магазину"""
    global in_settings, in_records, in_shop, dragging

    in_settings = False
    in_records = False
    in_shop = False
    dragging = None
    settings.save(SETTINGS_PATH, config)


new_pipes()

# -- головний ницкл
run = True

while run:
    dt = clock.tick(FPS)
    dts = min(dt / 1000, 0.05)   # -- dt в секундах (обмежуємо, щоб після лагу анімації не стрибали)
    t_total += dts

    # -- вікно могли розтягнути / розвернути -- беремо актуальне полотно
    display.update()
    view, screen, VIEW_X = display.view, display.screen, display.ox
    scenery.set_view(view.get_width(), VIEW_X)

    for event in pygame.event.get():
        if event.type in (pygame.QUIT, pygame.WINDOWCLOSE):
            run = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and start and not over:
                bird_v = JUMP_VELOCITY
            elif event.key == pygame.K_ESCAPE and (in_settings or in_records or in_shop):
                close_settings()
            elif event.key == pygame.K_F11:
                # -- швидкий повний екран / назад
                config["window"] = display.apply("auto" if display.mode == "fullscreen" else "fullscreen")
                settings.save(SETTINGS_PATH, config)

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if dragging:
                dragging = None
                settings.save(SETTINGS_PATH, config)

        elif event.type == pygame.MOUSEWHEEL:
            if in_shop:
                shop_scroll = max(0, min(shop_max_scroll(), shop_scroll - event.y * SHOP_SCROLL_STEP))

        elif event.type == pygame.MOUSEMOTION:
            if dragging:
                set_slider(dragging, slider_value(dragging, display.to_game(event.pos)[0]))

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            x, y = display.to_game(event.pos)

            if in_settings:
                if not pressed:
                    settings_click(x, y)

            elif in_records:
                if not pressed and RECORDS_BACK_RECT.collidepoint(x, y):
                    pressed, press_time = "back", 0

            elif in_shop:
                if not pressed:
                    if SHOP_BACK_RECT.collidepoint(x, y):
                        pressed, press_time = "back", 0
                    else:
                        shop_click(x, y)

            elif not start:
                if pressed or fading:
                    continue
                for name, rect in MENU_BUTTONS.items():
                    if rect.collidepoint(x, y):
                        pressed, press_time = name, 0
                        break

            elif over:
                if over_time >= GAME_OVER_ANIM and MENU_BTN_RECT.collidepoint(x, y):
                    pressed, press_time = "menu", 0

            else:
                bird_v = JUMP_VELOCITY

    # -- затримка після натискання кнопки меню перед дією
    # -- TODO треба погратися з показником бо мені не дуже подобається тривалість затримки
    if pressed is not None:
        press_time += dt

        if press_time > PRESS_ACTION_DELAY:
            if pressed == "play":
                fading = True
                fade = 0
            elif pressed == "shop":
                in_shop = True
                shop_scroll = 0
            elif pressed == "settings":
                in_settings = True
            elif pressed == "record":
                in_records = True
            elif pressed == "back":
                close_settings()
            elif pressed == "menu":
                go_to_menu()

            pressed = None

    # -- затемнення єкрану перед сратом гри
    if fading:
        fade += FADE_SPEED

        if fade >= 255:
            fade = 255
            fading = False
            reset_game()

    # -- сповільнення: швидкість світу плавно йде до потрібної (гравітація і стрибок не змінюються)
    slowed = start and not over and boost["slow"] > 0
    speed_k += ((SLOW_FACTOR if slowed else 1.0) - speed_k) * min(1.0, 5.0 * dts)
    speed = PIPE_SPEED * speed_k

    # -- фізика
    if start and not over:
        for kind in boost:
            boost[kind] = max(0.0, boost[kind] - dts)
        grace = max(0.0, grace - dts)

        bird_v += GRAVITY
        bird_y += bird_v
        bird_rect = pygame.Rect(BIRD_START_X, int(bird_y), BIRD_SIZE, BIRD_SIZE)

        for pipe in pipes:
            pipe[0] -= speed

            if not pipe[2] and pipe[0] + PIPE_WIDTH < BIRD_START_X:
                pipe[2] = True
                score += 1

            if BIRD_START_X + BIRD_SIZE > pipe[0] and BIRD_START_X < pipe[0] + PIPE_WIDTH:
                if bird_y < pipe[1] or bird_y + BIRD_SIZE > pipe[1] + PIPE_GAP:
                    hit()

        # -- труба зникає, коли повністю виїхала за лівий край полотна
        pipes[:] = [p for p in pipes if p[0] > -PIPE_WIDTH - VIEW_X]
        fill_pipes()

        # -- монетки їдуть разом з трубами; зачепив -- підібрав
        for coin in coins:
            coin[0] -= speed
            if coin[3] is None:
                box = pygame.Rect(0, 0, COIN_HITBOX, COIN_HITBOX)
                box.center = (int(coin[0]), int(coin[1]))
                if not over and box.colliderect(bird_rect):
                    coin[3] = 0.0
                    coin[4] = 2 if boost["x2"] > 0 else 1
                    run_coins += coin[4]
                    progress["coins"] += coin[4]
                    sfx.play("coin")

        # -- бонуси теж їдуть з трубами; підібраний одразу діє
        for p in powerups:
            p[0] -= speed
            if p[4] is None:
                box = pygame.Rect(0, 0, POWERUP_HITBOX, POWERUP_HITBOX)
                box.center = (int(p[0]), int(powerup_y(p)))
                if not over and box.colliderect(bird_rect):
                    p[4] = 0.0
                    p[1] = powerup_y(p)
                    take_powerup(p[2])

        # -- земля і стеля: зі щитом пташка відскакує, без щита -- кінець гри
        if bird_y + BIRD_SIZE > GROUND_Y:
            hit()
            if not over:
                bird_y = GROUND_Y - BIRD_SIZE
                bird_v = JUMP_VELOCITY
        elif bird_y < 0:
            hit()
            if not over:
                bird_y = 0
                bird_v = max(bird_v, 0)

    # -- анімація підбору монеток і бонусів йде і після смерті
    for item in coins:
        if item[3] is not None:
            item[3] += dts
    coins[:] = [c for c in coins
                if c[0] > -COIN_HITBOX - VIEW_X and (c[3] is None or c[3] < COIN_PICKUP_TIME)]
    for p in powerups:
        if p[4] is not None:
            p[4] += dts
    powerups[:] = [p for p in powerups
                   if p[0] > -POWERUP_HITBOX - VIEW_X and (p[4] is None or p[4] < COIN_PICKUP_TIME)]
    for pop in pops:
        pop[2] += dts
    pops[:] = [p for p in pops if p[2] < SHIELD_POP_TIME]

    # -- шлейф: точки, де пролетіла пташка; їдуть разом зі світом і згасають.
    # -- після смерті нові не додаються -- шлейф просто тане
    for tp in trail_pts:
        tp[2] += dts
        if start and not over:
            tp[0] -= speed
    trail_pts[:] = [tp for tp in trail_pts if tp[2] < TRAIL_LIFE]
    if start and not over and kit.trail.id != "none":
        trail_pts.append([BIRD_START_X + BIRD_SIZE / 2 - 6, bird_y + BIRD_SIZE / 2, 0.0, random.random()])

    if over:
        finish_run()

    # -- крила: під час гри махає швидше при стрибку, після смерті завмирає
    if start and not over:
        kit.bird.update(dts, 2.0 if bird_v < 0 else 1.0)
    if start:
        kit.aura.update(dts)
        for a in kit.powerups.values():
            a.update(dts)

    # -- музика: у меню своя, у грі своя; поки тягнуть повзунок гри -- грає музика гри
    music.play("game" if start or dragging == "game_music" else "menu")
    music.update(dts)

    press_progress = press_time / PRESS_ACTION_DELAY if pressed else 0
    not_enough = max(0.0, not_enough - dts)
    over_time = over_time + dts if over else 0.0

    # -- анімація фону: у меню повільно, у грі як труби, після смерті стоїть
    if over:
        scenery.update(dts, 0, snap=True)
    else:
        scenery.update(dts, speed * FPS if start else MENU_SCROLL_SPEED)

    mouse_pos = display.mouse_pos()

    if not start and (in_settings or in_records or in_shop):
        back = BACK_BTN_RECT if in_settings else RECORDS_BACK_RECT if in_records else SHOP_BACK_RECT

        scenery.draw_back(view)
        scenery.draw_ground(view)
        if in_settings:
            draw_settings(mouse_pos)
        elif in_records:
            draw_records()
        else:
            draw_shop(mouse_pos)
            draw_menu_counters()     # -- баланс монет видно в магазині

        kit.menu.update(dts, back.collidepoint(mouse_pos),
                        press_progress if pressed == "back" else 0.0)
        kit.menu.draw(screen, t_total, back.x, back.y)

    elif not start:
        for name, sprite in MENU_SPRITES.items():
            sprite.update(dts, MENU_BUTTONS[name].collidepoint(mouse_pos),
                          press_progress if pressed == name else 0.0)

        scenery.draw_back(view)
        scenery.draw_ground(view)
        kit.title.draw(screen, t_total)

        for sprite in MENU_SPRITES.values():
            sprite.draw(screen, t_total)

        draw_menu_counters()

    else:
        scenery.draw_back(view)

        for pipe in pipes:
            kit.pipe.draw(view, int(pipe[0]) + VIEW_X, PIPE_WIDTH, pipe[1], PIPE_GAP, GROUND_Y)

        draw_coins()
        draw_powerups()
        scenery.draw_ground(view)
        draw_slow_tint()

        kit.trail.draw(view, [(x + VIEW_X, y, age / TRAIL_LIFE, seed)
                              for x, y, age, seed in reversed(trail_pts)], t_total)
        draw_bird(BIRD_START_X, bird_y, bird_v)
        draw_text(str(score), title_font, WIDTH // 2, 50)
        draw_counter(kit.coin_icon, run_coins, 14, 30)
        draw_powerup_hud()

        if over:
            # -- напис, панель і кнопка виїжджають зверху (ease-out)
            k = min(1.0, over_time / GAME_OVER_ANIM)
            slide = int(-40 * (1 - k) ** 3)

            blit_center(kit.text("game_over"), WIDTH // 2, GAME_OVER_Y + slide)
            draw_result(slide)

            kit.menu.update(dts, MENU_BTN_RECT.collidepoint(mouse_pos),
                            press_progress if pressed == "menu" else 0.0)
            kit.menu.draw(screen, t_total, MENU_BTN_RECT.x, MENU_BTN_RECT.y + slide)

    if fading:
        fade_surface = pygame.Surface(view.get_size())
        fade_surface.fill((0, 0, 0))
        fade_surface.set_alpha(fade)
        view.blit(fade_surface, (0, 0))

    display.present()

# -- монетки, зібрані в незакінченій грі, теж зберігаємо
settings.save(SAVE_PATH, progress)
settings.save(SETTINGS_PATH, config)
pygame.quit()
