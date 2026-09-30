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

# -- магазин: вікно з картками пташок, по 3 в ряд; якщо рядів більше -- гортається коліщатком
SHOP_TITLE_Y = 84
SHOP_PANEL = pygame.Rect(14, 116, 372, 350)
SHOP_COLS = 3
CARD_W, CARD_H, CARD_GAP = 108, 150, 10
CARD_PAD_TOP = 16
SHOP_SCROLL_STEP = 40
NOT_ENOUGH_TIME = 1.6      # -- сек, скільки висить «недостатньо монет»
CARD_PREVIEW = (88, 80)    # -- у яку рамку вписується пташка на картці

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
SHOP_BACK_RECT.midtop = (WIDTH // 2, SHOP_PANEL.bottom + 30)

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
GROUND_Y = kit.ground_y   # -- з цієї висоти починається земля, пташка про неї розбивається

music = Music({"menu": os.path.join(MUSIC_DIR, "menu.mp3"),
               "game": os.path.join(MUSIC_DIR, "game.mp3")},
              max_volume=MUSIC_MAX_VOLUME)
music.set_level("menu", config["menu_music"])
music.set_level("game", config["game_music"])

sfx = Sounds({"coin": os.path.join(SOUNDS_DIR, "coin.wav")}, max_volume=SFX_MAX_VOLUME)
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
coins = []          # -- [x центру, y центру, фаза анімації, час після підбору або None]
score = 0
run_coins = 0       # -- монетки, зібрані за цю гру
new_record = False
run_saved = True    # -- чи вже записали результат цієї гри

start = False
over = False

in_settings = False
in_records = False
in_shop = False
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
        coins.append([x + PIPE_WIDTH / 2, cy, random.random() * 8, None])

    if prev and random.random() < COIN_CHANCE_BETWEEN:
        mid_x = (prev[0] + x) / 2 + PIPE_WIDTH / 2
        mid_y = (prev[1] + gap_y) / 2 + PIPE_GAP // 2 + random.randint(-30, 30)
        coins.append([mid_x, mid_y, random.random() * 8, None])


def fill_pipes():
    """додаємо труби, поки не заповнимо все видиме полотно праворуч (на широкому екрані їх більше)"""
    right = WIDTH + VIEW_X
    while not pipes or pipes[-1][0] <= right:
        add_pipe(pipes[-1][0] + PIPE_SPACING_X if pipes else WIDTH)


def new_pipes():
    """генерація труб"""
    pipes.clear()
    coins.clear()
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
    kit.bird.draw(screen, x + BIRD_SIZE / 2, y + BIRD_SIZE / 2, angle)


def draw_coins():
    """монетки малюються на всьому полотні (як і труби)"""
    frames = kit.coin.frames
    for x, y, phase, taken in coins:
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


# -- магазин
def shop_cards():
    """(скін, прямокутник картки) з урахуванням прокрутки"""
    x0 = SHOP_PANEL.x + (SHOP_PANEL.width - SHOP_COLS * CARD_W - (SHOP_COLS - 1) * CARD_GAP) // 2
    y0 = SHOP_PANEL.y + CARD_PAD_TOP - shop_scroll
    for i, bird in enumerate(kit.skins):
        row, col = divmod(i, SHOP_COLS)
        yield bird, pygame.Rect(x0 + col * (CARD_W + CARD_GAP), y0 + row * (CARD_H + CARD_GAP), CARD_W, CARD_H)


def shop_view():
    """видима частина вікна магазину (все, що нижче/вище -- обрізається)"""
    return pygame.Rect(SHOP_PANEL.x, SHOP_PANEL.y + PANEL_INNER_TOP,
                       SHOP_PANEL.width, SHOP_PANEL.height - PANEL_INNER_TOP - PANEL_INNER_BOTTOM)


def shop_max_scroll():
    rows = (len(kit.skins) + SHOP_COLS - 1) // SHOP_COLS
    content = CARD_PAD_TOP * 2 + rows * CARD_H + (rows - 1) * CARD_GAP
    return max(0, content - shop_view().height)


def shop_click(x, y):
    """клік по картці: купити (якщо вистачає монет) або обрати"""
    global not_enough

    if not shop_view().collidepoint(x, y):
        return
    for bird, rect in shop_cards():
        if not rect.collidepoint(x, y):
            continue
        if bird.id not in progress["owned"]:
            if progress["coins"] < bird.price:
                not_enough = NOT_ENOUGH_TIME
                return
            progress["coins"] -= bird.price
            progress["owned"].append(bird.id)
            sfx.play("coin")
        progress["skin"] = kit.set_skin(bird.id)
        settings.save(SAVE_PATH, progress)
        return


_preview_cache = {}


def card_preview(bird, i):
    """кадр пташки, збільшений під картку (маленька класична -- рівно в 2 рази, без розмиття)"""
    key = (bird.id, i)
    if key not in _preview_cache:
        img = bird.anim.frames[i]
        k = min(CARD_PREVIEW[0] / img.get_width(), CARD_PREVIEW[1] / img.get_height())
        if k >= 2:
            k = int(k)
        size = (round(img.get_width() * k), round(img.get_height() * k))
        _preview_cache[key] = pygame.transform.scale(img, size) if k == int(k) else             pygame.transform.smoothscale(img, size)
    return _preview_cache[key]


def draw_card(bird, rect, mouse_pos):
    selected = bird.id == progress["skin"]
    owned = bird.id in progress["owned"]

    screen.blit(kit.panel.render(rect.width, rect.height), rect)
    if selected:
        pygame.draw.rect(screen, COLOR_ARROW, rect.inflate(-4, -6).move(0, -2), 3, border_radius=8)
    elif rect.collidepoint(mouse_pos) and shop_view().collidepoint(mouse_pos):
        pygame.draw.rect(screen, COLOR_CARD_HOVER, rect.inflate(-4, -6).move(0, -2), 2, border_radius=8)

    # -- пташка махає крилами (кожна зі своєю швидкістю кадрів)
    i = int(t_total * bird.anim.fps) % len(bird.anim.frames)
    blit_center(card_preview(bird, i), rect.centerx, rect.y + 58)

    y = rect.bottom - 34
    if selected:
        blit_center(kit.text("selected"), rect.centerx, y)
    elif owned:
        blit_center(kit.text("select"), rect.centerx, y)
    else:
        price = str(bird.price)
        w = counter_width(kit.coin_icon, price)
        draw_counter(kit.coin_icon, price, rect.centerx - w // 2, y)


def draw_shop(mouse_pos):
    blit_center(kit.text("shop_title"), WIDTH // 2, SHOP_TITLE_Y)
    screen.blit(kit.panel.render(SHOP_PANEL.width, SHOP_PANEL.height), SHOP_PANEL)

    screen.set_clip(shop_view())
    for bird, rect in shop_cards():
        draw_card(bird, rect, mouse_pos)
    screen.set_clip(None)

    # -- смужка прокрутки, якщо пташок більше, ніж влазить
    top = shop_max_scroll()
    if top > 0:
        view_rect = shop_view()
        h = max(30, view_rect.height * view_rect.height // (view_rect.height + top))
        y = view_rect.y + (view_rect.height - h) * shop_scroll // top
        pygame.draw.rect(screen, COLOR_KNOB_SHADE, (SHOP_PANEL.right - 12, y, 5, h), border_radius=3)

    if not_enough > 0 and int((NOT_ENOUGH_TIME - not_enough) * 6) % 2 == 0:
        blit_center(kit.text("not_enough"), WIDTH // 2, SHOP_PANEL.bottom + 14)


def reset_game():
    global bird_y, bird_v, score, over, start, run_coins, new_record, run_saved

    bird_y = BIRD_START_Y
    bird_v = 0
    score = 0
    run_coins = 0
    new_record = False
    run_saved = False
    over = False
    start = True

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

    # -- фізика
    if start and not over:
        bird_v += GRAVITY
        bird_y += bird_v
        bird_rect = pygame.Rect(BIRD_START_X, int(bird_y), BIRD_SIZE, BIRD_SIZE)

        for pipe in pipes:
            pipe[0] -= PIPE_SPEED

            if not pipe[2] and pipe[0] + PIPE_WIDTH < BIRD_START_X:
                pipe[2] = True
                score += 1

            if BIRD_START_X + BIRD_SIZE > pipe[0] and BIRD_START_X < pipe[0] + PIPE_WIDTH:
                if bird_y < pipe[1] or bird_y + BIRD_SIZE > pipe[1] + PIPE_GAP:
                    over = True

        # -- труба зникає, коли повністю виїхала за лівий край полотна
        pipes[:] = [p for p in pipes if p[0] > -PIPE_WIDTH - VIEW_X]
        fill_pipes()

        # -- монетки їдуть разом з трубами; зачепив -- підібрав
        for coin in coins:
            coin[0] -= PIPE_SPEED
            if coin[3] is None:
                hit = pygame.Rect(0, 0, COIN_HITBOX, COIN_HITBOX)
                hit.center = (int(coin[0]), int(coin[1]))
                if not over and hit.colliderect(bird_rect):
                    coin[3] = 0.0
                    run_coins += 1
                    progress["coins"] += 1
                    sfx.play("coin")

        if bird_y < 0 or bird_y + BIRD_SIZE > GROUND_Y:
            over = True

    # -- анімація підбору монеток йде і після смерті
    for coin in coins:
        if coin[3] is not None:
            coin[3] += dts
    coins[:] = [c for c in coins
                if c[0] > -COIN_HITBOX - VIEW_X and (c[3] is None or c[3] < COIN_PICKUP_TIME)]

    if over:
        finish_run()

    # -- крила: під час гри махає швидше при стрибку, після смерті завмирає
    if start and not over:
        kit.bird.update(dts, 2.0 if bird_v < 0 else 1.0)

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
        scenery.update(dts, PIPE_SPEED * FPS if start else MENU_SCROLL_SPEED)

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
        scenery.draw_ground(view)

        draw_bird(BIRD_START_X, bird_y, bird_v)
        draw_text(str(score), title_font, WIDTH // 2, 50)
        draw_counter(kit.coin_icon, run_coins, 14, 30)

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
