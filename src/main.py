import pygame
import random

pygame.init()
# -- розмір вікна
W = 400
H = 700

screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Flappybirds")

clock = pygame.time.Clock()

font = pygame.font.Font(None, 50)
# -- позиція пташки
bird_x = 80
bird_y = 300
bird_v = 0

pipes = []
over = False
start = False

for x in [400, 650]:
    gap_y = random.randint(150, 450)
    pipes.append([x, gap_y])

run = True
# -- логіка
while run:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and start and not over:
                bird_v = -8

            if event.key == pygame.K_r and over:
                bird_y = 300
                bird_v = 0
                over = False
                start = True
                pipes = []

                for x in [400, 650]:
                    gap_y = random.randint(150, 450)
                    pipes.append([x, gap_y])

        if event.type == pygame.MOUSEBUTTONDOWN:
            x = event.pos[0]
            y = event.pos[1]

            if not start:
                if 100 < x < 300 and 300 < y < 370:
                    start = True

            elif not over:
                bird_v = -8

    if start and not over:
        bird_v += 0.4
        bird_y += bird_v

        for pipe in pipes:
            pipe[0] -= 3

            if bird_x + 30 > pipe[0] and bird_x < pipe[0] + 70:
                if bird_y < pipe[1] or bird_y + 30 > pipe[1] + 150:
                    over = True

        pipes = [p for p in pipes if p[0] > -70]

        if len(pipes) < 2:
            x = pipes[-1][0] + 250 if pipes else 400
            gap_y = random.randint(150, 450)
            pipes.append([x, gap_y])

        if bird_y < 0 or bird_y + 30 > H:
            over = True

    screen.fill((50, 80, 150))

    if not start:
        text = font.render("FLAPPY BIRD", True, (255, 255, 255))
        screen.blit(text, (W // 2 - text.get_width() // 2, 200))

        pygame.draw.rect(screen, (70, 180, 80), (100, 300, 200, 70))

        text = font.render("Грати", True, (255, 255, 255))
        screen.blit(text, (W // 2 - text.get_width() // 2, 315))

    else:
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

        if over:
            text = font.render("GAME OVER", True, (255, 70, 70))
            screen.blit(
                text,
                (W // 2 - text.get_width() // 2, H // 2 - 30)
            )

            text = font.render("R - restart", True, (255, 255, 255))
            screen.blit(
                text,
                (W // 2 - text.get_width() // 2, H // 2 + 30)
            )

    pygame.display.update()
    clock.tick(60)

pygame.quit()