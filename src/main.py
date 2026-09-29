import os
import random
import pygame

from sprites import SpriteKit

# -- карочє тут путь к файлікам
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
FONT_PATH = os.path.join(ASSETS_DIR, "fonts", "OutlineStyleRegular.ttf")
SPRITES_DIR = os.path.join(ASSETS_DIR, "sprites")   # готовые спрайты (tools/make_sprites.py)

# -- віконечко 
WIDTH, HEIGHT = 400, 700
FPS = 60

GRAVITY = 0.4 # -- гравітація 
JUMP_VELOCITY = -8
BIRD_START_X, BIRD_START_Y = 80, 300 # -- позиція пташки
BIRD_SIZE = 30  # ну типу хітбокс пташки по осі x+y
BIRD_DRAW_HEIGHT = 25   # висота саме намальованого тіла

PIPE_WIDTH = 70
PIPE_GAP = 150
PIPE_SPEED = 3
PIPE_SPACING_X = 250
PIPE_GAP_Y_RANGE = (150, 450)

MENU_SCROLL_SPEED = 60     # -- px/сек, як швидко їде земля в меню (місто і кущі повільніше)
GAME_OVER_ANIM = 0.45      # -- сек, за скільки виїжджає напис GAME OVER і кнопка MENU

PRESS_ACTION_DELAY = 120   # -- показний що відповідає за затемнення (типу анімація)
FADE_SPEED = 12   #  -- тут просто швидкість затемнення

# -- тут просто хітбокси для кліків в меню
PLAY_BTN = pygame.Rect(78, 360, 244, 62)
SHOP_BTN = pygame.Rect(78, 440, 244, 62)
SETTINGS_BTN = pygame.Rect(328, 8, 56, 56)

# -- сайз кнопки що зявляється після смерті
MENU_BTN_SIZE = (220, 94)

# -- кольори
COLOR_PIPE = (50, 180, 70)
COLOR_TEXT_SHADOW = (65, 40, 70)
COLOR_TEXT_MAIN = (255, 255, 255)

PRESS_OVERLAY_MAX_ALPHA = 70   # -- наскільки темнішає кнопка при натисканні (0..255)

COLOR_BIRD_BODY = (255, 220, 40)
COLOR_BIRD_WING = (255, 150, 30)
COLOR_BIRD_EYE_WHITE = (255, 255, 255)
COLOR_BIRD_EYE_PUPIL = (40, 40, 40)
COLOR_BIRD_BEAK = (240, 120, 20)

# -- пайгейм, ресурси
pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.RESIZABLE)
pygame.display.set_caption("Flappy Bird")
clock = pygame.time.Clock()

title_font = pygame.font.Font(FONT_PATH, 48)
button_font = pygame.font.Font(FONT_PATH, 30)

# -- анімовані спрайти: фон, хмари, заголовок, кнопки (див. src/sprites.py)
kit = SpriteKit(SPRITES_DIR, press_dark=PRESS_OVERLAY_MAX_ALPHA / 255)
scenery = kit.scenery
GROUND_Y = kit.ground_y   # -- з цієї висоти починається земля, пташка про неї розбивається

MENU_BTN_RECT = pygame.Rect(0, 0, *MENU_BTN_SIZE)
MENU_BTN_RECT.center = (WIDTH // 2, HEIGHT // 2 + 60)

# -- який спрайт малює яку кнопку меню
MENU_SPRITES = {
    "play": kit.play,
    "shop": kit.shop,
    "settings": kit.settings,
}

# -- хітбокси кнопок в одному місці
MENU_BUTTONS = {
    "play": PLAY_BTN,
    "shop": SHOP_BTN,
    "settings": SETTINGS_BTN,
}

bird_y = BIRD_START_Y
bird_v = 0

pipes = []
score = 0

start = False
over = False

pressed = None      # -- яку кнопку тримають
press_time = 0

fade = 0
fading = False

t_total = 0.0       # -- загальний час у секундах, від нього рахуються всі анімації
over_time = 0.0     # -- скільки секунд пройшло після смерті


# -- доп функціонал
def new_pipes():
    """генерація труб"""
    pipes.clear()
    for x in (WIDTH, WIDTH + PIPE_SPACING_X):
        gap_y = random.randint(*PIPE_GAP_Y_RANGE)
        pipes.append([x, gap_y, False])


def draw_text(text, font, x, y):
    """текст + тінь та місце розташування"""
    shadow = font.render(text, True, COLOR_TEXT_SHADOW)
    main = font.render(text, True, COLOR_TEXT_MAIN)

    screen.blit(shadow, (x - shadow.get_width() // 2 + 2, y - shadow.get_height() // 2 + 3))
    screen.blit(main, (x - main.get_width() // 2, y - main.get_height() // 2))


def draw_bird(x, y):
    x, y = int(x), int(y)

    pygame.draw.rect(screen, COLOR_BIRD_BODY, (x, y, BIRD_SIZE, BIRD_DRAW_HEIGHT))
    pygame.draw.rect(screen, COLOR_BIRD_WING, (x + 20, y + 10, 15, 8))
    pygame.draw.rect(screen, COLOR_BIRD_EYE_WHITE, (x + 18, y + 3, 8, 8))
    pygame.draw.rect(screen, COLOR_BIRD_EYE_PUPIL, (x + 21, y + 5, 4, 4))
    pygame.draw.rect(screen, COLOR_BIRD_BEAK, (x - 5, y + 15, 10, 6))


def reset_game():
    global bird_y, bird_v, score, over, start

    bird_y = BIRD_START_Y
    bird_v = 0
    score = 0
    over = False
    start = True

    new_pipes()
    scenery.update(0, PIPE_SPEED * FPS, snap=True)   # -- фон їде з тією ж швидкістю, що й труби


def go_to_menu():
    """повертання в головне меню після смерті"""
    global start, over

    start = False
    over = False


new_pipes()

# -- головний ницкл
run = True

while run:
    dt = clock.tick(FPS)
    dts = min(dt / 1000, 0.05)   # -- dt в секундах (обмежуємо, щоб після лагу анімації не стрибали)
    t_total += dts

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and start and not over:
                bird_v = JUMP_VELOCITY

        elif event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos

            if not start:
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
                print("SHOP")
            elif pressed == "settings":
                print("SETTINGS")
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

        for pipe in pipes:
            pipe[0] -= PIPE_SPEED

            if not pipe[2] and pipe[0] + PIPE_WIDTH < BIRD_START_X:
                pipe[2] = True
                score += 1

            if BIRD_START_X + BIRD_SIZE > pipe[0] and BIRD_START_X < pipe[0] + PIPE_WIDTH:
                if bird_y < pipe[1] or bird_y + BIRD_SIZE > pipe[1] + PIPE_GAP:
                    over = True

        pipes[:] = [p for p in pipes if p[0] > -PIPE_WIDTH]

        if len(pipes) < 2:
            x = pipes[-1][0] + PIPE_SPACING_X if pipes else WIDTH
            gap_y = random.randint(*PIPE_GAP_Y_RANGE)
            pipes.append([x, gap_y, False])

        if bird_y < 0 or bird_y + BIRD_SIZE > GROUND_Y:
            over = True

    press_progress = press_time / PRESS_ACTION_DELAY if pressed else 0
    over_time = over_time + dts if over else 0.0

    # -- анімація фону: у меню повільно, у грі як труби, після смерті стоїть
    if over:
        scenery.update(dts, 0, snap=True)
    else:
        scenery.update(dts, PIPE_SPEED * FPS if start else MENU_SCROLL_SPEED)

    if not start:
        mouse_pos = pygame.mouse.get_pos()

        for name, sprite in MENU_SPRITES.items():
            sprite.update(dts, MENU_BUTTONS[name].collidepoint(mouse_pos),
                          press_progress if pressed == name else 0.0)

        scenery.draw_back(screen)
        scenery.draw_ground(screen)
        kit.title.draw(screen, t_total)

        for sprite in MENU_SPRITES.values():
            sprite.draw(screen, t_total)

    else:
        scenery.draw_back(screen)

        for pipe in pipes:
            x, gap_y = pipe[0], pipe[1]

            pygame.draw.rect(screen, COLOR_PIPE, (x, 0, PIPE_WIDTH, gap_y))
            pygame.draw.rect(
                screen, COLOR_PIPE,
                (x, gap_y + PIPE_GAP, PIPE_WIDTH, HEIGHT - gap_y - PIPE_GAP)
            )

        scenery.draw_ground(screen)

        draw_bird(BIRD_START_X, bird_y)
        draw_text(str(score), title_font, WIDTH // 2, 50)

        if over:
            # -- напис і кнопка виїжджають зверху (ease-out)
            k = min(1.0, over_time / GAME_OVER_ANIM)
            slide = int(-40 * (1 - k) ** 3)

            draw_text("GAME OVER", button_font, WIDTH // 2, HEIGHT // 2 - 30 + slide)

            kit.menu.update(dts, MENU_BTN_RECT.collidepoint(pygame.mouse.get_pos()),
                            press_progress if pressed == "menu" else 0.0)
            kit.menu.draw(screen, t_total, MENU_BTN_RECT.x, MENU_BTN_RECT.y + slide)

    if fading:
        fade_surface = pygame.Surface((WIDTH, HEIGHT))
        fade_surface.fill((0, 0, 0))
        fade_surface.set_alpha(fade)
        screen.blit(fade_surface, (0, 0))

    pygame.display.flip()

pygame.quit()
