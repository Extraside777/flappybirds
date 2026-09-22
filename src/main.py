import pygame
import random
import math
from array import array

pygame.init()

W = 400
H = 700

screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Flappy Bird")
clock = pygame.time.Clock()

font = pygame.font.SysFont("arial", 42)
big_font = pygame.font.SysFont("arial", 55)

lang = "ua"
sound = True
state = "menu"

bird_x = 80
bird_y = 300
bird_v = 0
pipes = []
score = 0
over = False

txt = {
    "ua": {
        "play": "Грати",
        "settings": "Налаштування",
        "sound": "Звук",
        "on": "Увімкнено",
        "off": "Вимкнено",
        "language": "Мова",
        "back": "Назад",
        "gameover": "КІНЕЦЬ ГРИ",
        "restart": "R - перезапуск",
        "menu": "ESC - меню"
    },
    "en": {
        "play": "Play",
        "settings": "Settings",
        "sound": "Sound",
        "on": "On",
        "off": "Off",
        "language": "Language",
        "back": "Back",
        "gameover": "GAME OVER",
        "restart": "R - restart",
        "menu": "ESC - menu"
    }
}


def make_sound(freq, time):
    rate = 44100
    data = array("h")

    for i in range(int(rate * time)):
        v = int(2500 * math.sin(2 * math.pi * freq * i / rate))
        data.append(v)

    return pygame.mixer.Sound(buffer=data)


try:
    flap_sound = make_sound(500, 0.08)
    over_sound = make_sound(180, 0.2)
except pygame.error:
    sound = False
    flap_sound = None
    over_sound = None


def reset():
    global bird_y, bird_v, pipes, score, over

    bird_y = 300
    bird_v = 0
    score = 0
    over = False
    pipes = []

    for x in [400, 650]:
        gap_y = random.randint(150, 450)
        pipes.append([x, gap_y, False])


def button(text, y):
    r = pygame.Rect(70, y, 260, 65)

    pygame.draw.rect(screen, (70, 180, 80), r)

    t = font.render(text, True, (255, 255, 255))
    screen.blit(t, (W // 2 - t.get_width() // 2, y + 12))

    return r


def menu():
    screen.fill((50, 80, 150))

    t = big_font.render("FLAPPY BIRD", True, (255, 255, 255))
    screen.blit(t, (W // 2 - t.get_width() // 2, 160))

    play = button(txt[lang]["play"], 290)
    settings = button(txt[lang]["settings"], 380)

    return play, settings


def settings_menu():
    screen.fill((50, 80, 150))

    t = big_font.render(txt[lang]["settings"], True, (255, 255, 255))
    screen.blit(t, (W // 2 - t.get_width() // 2, 130))

    s = txt[lang]["on"] if sound else txt[lang]["off"]

    sound_btn = button(txt[lang]["sound"] + ": " + s, 260)
    lang_btn = button(txt[lang]["language"] + ": " + lang.upper(), 350)
    back_btn = button(txt[lang]["back"], 440)

    return sound_btn, lang_btn, back_btn


def game():
    global bird_y, bird_v, score, over

    if not over:
        bird_v += 0.4
        bird_y += bird_v

        for pipe in pipes:
            pipe[0] -= 3

            if not pipe[2] and pipe[0] + 70 < bird_x:
                pipe[2] = True
                score += 1

            if bird_x + 30 > pipe[0] and bird_x < pipe[0] + 70:
                if bird_y < pipe[1] or bird_y + 30 > pipe[1] + 150:
                    over = True
                    if sound and over_sound:
                        over_sound.play()

        pipes[:] = [p for p in pipes if p[0] > -70]

        if len(pipes) < 2:
            x = pipes[-1][0] + 250 if pipes else 400
            gap_y = random.randint(150, 450)
            pipes.append([x, gap_y, False])

        if bird_y < 0 or bird_y + 30 > H:
            over = True
            if sound and over_sound:
                over_sound.play()

    screen.fill((50, 80, 150))

    pygame.draw.circle(
        screen,
        (255, 220, 0),
        (bird_x + 15, int(bird_y) + 15),
        15
    )

    for pipe in pipes:
        x = pipe[0]
        gap_y = pipe[1]

        pygame.draw.rect(
            screen,
            (50, 180, 70),
            (x, 0, 70, gap_y)
        )

        pygame.draw.rect(
            screen,
            (50, 180, 70),
            (x, gap_y + 150, 70, H - gap_y - 150)
        )

    t = font.render(str(score), True, (255, 255, 255))
    screen.blit(t, (W // 2 - t.get_width() // 2, 25))

    if over:
        t = big_font.render(txt[lang]["gameover"], True, (255, 70, 70))
        screen.blit(t, (W // 2 - t.get_width() // 2, H // 2 - 60))

        t = font.render(txt[lang]["restart"], True, (255, 255, 255))
        screen.blit(t, (W // 2 - t.get_width() // 2, H // 2 + 10))

        t = font.render(txt[lang]["menu"], True, (255, 255, 255))
        screen.blit(t, (W // 2 - t.get_width() // 2, H // 2 + 60))


reset()

run = True

while run:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if state == "game":
                    state = "menu"
                    reset()
                elif state == "settings":
                    state = "menu"

            if state == "game":
                if event.key == pygame.K_SPACE and not over:
                    bird_v = -8
                    if sound and flap_sound:
                        flap_sound.play()

                if event.key == pygame.K_r and over:
                    reset()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            x, y = event.pos

            if state == "menu":
                if menu()[0].collidepoint(x, y):
                    reset()
                    state = "game"

                elif menu()[1].collidepoint(x, y):
                    state = "settings"

            elif state == "settings":
                sound_btn, lang_btn, back_btn = settings_menu()

                if sound_btn.collidepoint(x, y):
                    sound = not sound

                elif lang_btn.collidepoint(x, y):
                    lang = "en" if lang == "ua" else "ua"

                elif back_btn.collidepoint(x, y):
                    state = "menu"

            elif state == "game" and not over:
                bird_v = -8
                if sound and flap_sound:
                    flap_sound.play()

    if state == "menu":
        menu()

    elif state == "settings":
        settings_menu()

    elif state == "game":
        game()

    pygame.display.update()
    clock.tick(60)

pygame.quit()
