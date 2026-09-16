import random
import sys

import pygame

WIDTH, HEIGHT = 900, 600
FPS = 60

BG = (35, 45, 90)
GROUND = (85, 170, 75)
PIPE = (70, 190, 80)
PIPE_DARK = (45, 130, 55)
BIRD = (245, 205, 55)
WHITE = (245, 245, 245)
RED = (220, 70, 70)


class Bird:
    def __init__(self):
        self.x = 180
        self.y = HEIGHT // 2
        self.radius = 18
        self.velocity = 0.0
        self.gravity = 0.45
        self.jump_strength = -8.5

    def flap(self):
        self.velocity = self.jump_strength

    def update(self):
        self.velocity += self.gravity
        self.y += self.velocity

    def rect(self):
        return pygame.Rect(
            int(self.x - self.radius),
            int(self.y - self.radius),
            self.radius * 2,
            self.radius * 2,
        )

    def draw(self, screen):
        pygame.draw.circle(screen, BIRD, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, (30, 30, 30), (int(self.x + 7), int(self.y - 6)), 3)


class PipePair:
    def __init__(self, x, speed, gap=175):
        self.x = x
        self.width = 75
        self.gap = gap
        self.speed = speed
        self.passed = False
        margin = 100
        self.gap_y = random.randint(margin, HEIGHT - margin - gap)

    def update(self):
        self.x -= self.speed

    def is_offscreen(self):
        return self.x + self.width < 0

    def rects(self):
        top = pygame.Rect(int(self.x), 0, self.width, int(self.gap_y))
        bottom_y = self.gap_y + self.gap
        bottom = pygame.Rect(
            int(self.x), int(bottom_y), self.width, HEIGHT - int(bottom_y)
        )
        return top, bottom

    def collides(self, bird_rect):
        top, bottom = self.rects()
        return bird_rect.colliderect(top) or bird_rect.colliderect(bottom)

    def draw(self, screen):
        top, bottom = self.rects()
        pygame.draw.rect(screen, PIPE, top)
        pygame.draw.rect(screen, PIPE, bottom)
        pygame.draw.rect(screen, PIPE_DARK, (top.x - 5, top.bottom - 18, self.width + 10, 18))
        pygame.draw.rect(screen, PIPE_DARK, (bottom.x - 5, bottom.top, self.width + 10, 18))


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Flappy Clone")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 42)
        self.big_font = pygame.font.Font(None, 72)
        self.running = True
        self.reset()

    def reset(self):
        self.bird = Bird()
        self.pipes = [
            PipePair(WIDTH + 150, speed=3.5),
            PipePair(WIDTH + 500, speed=3.5),
        ]
        self.score = 0
        self.game_over = False

    def spawn_pipe_if_needed(self):
        if not self.pipes or self.pipes[-1].x < WIDTH - 220:
            self.pipes.append(PipePair(WIDTH + 20, speed=3.5))

    def update(self):
        if self.game_over:
            return

        self.bird.update()

        for pipe in self.pipes:
            pipe.update()

            if not pipe.passed and pipe.x + pipe.width < self.bird.x:
                pipe.passed = True
                self.score += 1

            if pipe.collides(self.bird.rect()):
                self.game_over = True

        self.pipes = [pipe for pipe in self.pipes if not pipe.is_offscreen()]
        self.spawn_pipe_if_needed()

        bird_rect = self.bird.rect()
        if bird_rect.top <= 0 or bird_rect.bottom >= HEIGHT - 35:
            self.game_over = True

    def draw_background(self):
        self.screen.fill(BG)
        for x, y, radius in [
            (90, 100, 2),
            (270, 70, 2),
            (430, 120, 1),
            (650, 75, 2),
            (790, 150, 2),
        ]:
            pygame.draw.circle(self.screen, WHITE, (x, y), radius)
        pygame.draw.rect(self.screen, GROUND, (0, HEIGHT - 35, WIDTH, 35))

    def draw_ui(self):
        score_text = self.font.render(str(self.score), True, WHITE)
        self.screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, 25))

        if self.game_over:
            title = self.big_font.render("GAME OVER", True, RED)
            hint = self.font.render("R - restart | ESC - exit", True, WHITE)
            self.screen.blit(
                title,
                (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 70),
            )
            self.screen.blit(
                hint,
                (WIDTH // 2 - hint.get_width() // 2, HEIGHT // 2 + 10),
            )

    def draw(self):
        self.draw_background()
        for pipe in self.pipes:
            pipe.draw(self.screen)
        self.bird.draw(self.screen)
        self.draw_ui()
        pygame.display.flip()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE and not self.game_over:
                    self.bird.flap()
                elif event.key == pygame.K_r and self.game_over:
                    self.reset()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not self.game_over:
                    self.bird.flap()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()
