import random
import sys
import pygame

W, H = 400, 700
FPS = 60

pygame.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Flappy Clone")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 45)

bird_x = 90
bird_y = H // 2
bird_v = 0
pipes = []
score = 0
over = False


def new_game():
    global bird_y, bird_v, pipes, score, over
    bird_y = H // 2
    bird_v = 0
    pipes = [[W + 100, random.randint(130, 430), False]]
    score = 0
    over = False


def add_pipe():
    y = random.randint(130, 430)
    pipes.append([W, y, False])


def hit():
    r = pygame.Rect(bird_x - 15, int(bird_y) - 15, 30, 30)
    if bird_y - 15 <= 0 or bird_y + 15 >= H - 30:
        return True
    for x, y, _ in pipes:
        top = pygame.Rect(x, 0, 60, y - 90)
        bot = pygame.Rect(x, y + 90, 60, H - y - 90)
        if r.colliderect(top) or r.colliderect(bot):
            return True
    return False


new_game()
run = True
while run:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            run = False
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                run = False
            if e.key == pygame.K_SPACE and not over:
                bird_v = -8
            if e.key == pygame.K_r and over:
                new_game()
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and not over:
            bird_v = -8
        if e.type == pygame.FINGERDOWN and not over:
            bird_v = -8

    if not over:
        bird_v += 0.45
        bird_y += bird_v

        for p in pipes:
            p[0] -= 3
            if not p[2] and p[0] + 60 < bird_x:
                p[2] = True
                score += 1

        if pipes[-1][0] < W - 190:
            add_pipe()
        pipes = [p for p in pipes if p[0] > -60]

        if hit():
            over = True

    screen.fill((35, 45, 90))

    for p in pipes:
        x, y, _ = p
        pygame.draw.rect(screen, (70, 190, 80), (x, 0, 60, y - 90))
        pygame.draw.rect(screen, (70, 190, 80), (x, y + 90, 60, H - y - 90))

    pygame.draw.rect(screen, (85, 170, 75), (0, H - 30, W, 30))
    pygame.draw.circle(screen, (245, 205, 55), (bird_x, int(bird_y)), 15)
    pygame.draw.circle(screen, (30, 30, 30), (bird_x + 6, int(bird_y) - 5), 2)

    text = font.render(str(score), True, (245, 245, 245))
    screen.blit(text, (W // 2 - text.get_width() // 2, 20))

    if over:
        text = font.render("GAME OVER", True, (220, 70, 70))
        screen.blit(text, (W // 2 - text.get_width() // 2, H // 2 - 30))
        text = font.render("R - restart", True, (245, 245, 245))
        screen.blit(text, (W // 2 - text.get_width() // 2, H // 2 + 20))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
