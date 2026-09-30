import math
import os
import sys
import pygame
from pygame._sdl2 import video

# -- масштаби вікна, які можна вибрати в налаштуваннях (показуються тільки ті, що влазять в екран)
SCALES = ("1", "1.25", "1.5", "2", "2.5", "3", "4")
AUTO_FILL = 0.88     # -- «авто»: вікно займає стільки висоти екрана
MAX_VIEW_W = 2400    # -- ширше за це сцену не розтягуємо (ультраширокі монітори)


def enable_dpi_awareness():
    """
    Windows з масштабом 125%/150% сам розтягує вікно гри -- виходить мило.
    Кажемо системі, що масштабуємо самі, тоді розміри екрана -- в справжніх пікселях.
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def _texture(renderer, size, quality, **kw):
    """текстура з потрібним фільтром: "0" -- чіткі пікселі, "1" -- плавний"""
    os.environ["SDL_RENDER_SCALE_QUALITY"] = quality
    return video.Texture(renderer, size, **kw)


class Display:
    """
    Гра малює на полотно висотою 700. Ширина полотна підлаштовується під вікно:
    ігрове поле 400x700 завжди по центру (self.screen), а небо, земля і труби
    тягнуться на всю ширину (self.view) -- тому чорних смуг по боках нема.

    Масштабування робить відеокарта в два кроки:
      1) полотно збільшується в ціле число разів «пікселями» (без згладжування)
      2) результат плавно підганяється під точний розмір вікна
    Так пікселі виходять однакові за розміром, і нічого не «кривить».
    """

    def __init__(self, width, height, caption):
        self.w, self.h = width, height
        # -- приховане вікно pygame.display потрібне тільки для convert()/convert_alpha()
        pygame.display.set_mode((1, 1), pygame.HIDDEN)
        sizes = pygame.display.get_desktop_sizes()
        self.desktop = sizes[0] if sizes else (width, height)

        self.window = video.Window(caption, size=(width, height), resizable=True)
        self.renderer = video.Renderer(self.window)
        self.mode = None
        self.win_size = None
        self.view = None
        self._layout()

    # -- режими вікна
    def options(self):
        """режими для налаштувань: авто, масштаби, що влазять, повний екран"""
        dw, dh = self.desktop
        fits = [s for s in SCALES if self.w * float(s) <= dw and self.h * float(s) <= dh * 0.95]
        return ["auto"] + fits + ["fullscreen"]

    def size_for(self, mode):
        if mode == "auto":
            k = self.desktop[1] * AUTO_FILL / self.h
            k = max(1.0, min(k, self.desktop[0] * 0.95 / self.w))
        else:
            k = float(mode)
        return max(1, round(self.w * k)), max(1, round(self.h * k))

    def apply(self, mode):
        if mode not in self.options():
            mode = "auto"
        if mode == self.mode:
            return mode
        if mode == "fullscreen":
            self.window.set_fullscreen(True)      # -- «desktop» fullscreen: без зміни режиму монітора
        else:
            if self.mode == "fullscreen":
                self.window.set_windowed()
            self.window.size = self.size_for(mode)
            self.window.position = video.WINDOWPOS_CENTERED
        self.mode = mode
        self._layout()
        return mode

    # -- розкладка: ширина полотна, масштаб, текстури
    def _layout(self):
        ww, wh = self.window.size
        if (ww, wh) == self.win_size:
            return
        self.win_size = (ww, wh)

        k = wh / self.h
        view_w = round(ww / k)
        if view_w < self.w:                  # -- вікно вужче за поле: смуги зверху/знизу
            view_w = self.w
            k = ww / self.w
        view_w = min(view_w, MAX_VIEW_W)
        self.k = k
        dw, dh = round(view_w * k), round(self.h * k)
        if abs(dw - ww) <= 2:                # -- похибка округлення: тягнемо рівно на все вікно
            dw = ww
        if abs(dh - wh) <= 2:
            dh = wh
        self.dest = pygame.Rect((ww - dw) // 2, (wh - dh) // 2, dw, dh)

        if self.view is None or self.view.get_width() != view_w:
            self.view = pygame.Surface((view_w, self.h)).convert()
            self.ox = (view_w - self.w) // 2
            self.screen = self.view.subsurface((self.ox, 0, self.w, self.h))
            self.tex_view = _texture(self.renderer, (view_w, self.h), "0", streaming=True)

        n = max(1, math.ceil(k - 0.01))      # -- ціле збільшення «пікселями»
        self.big_size = (view_w * n, self.h * n)
        self.tex_big = _texture(self.renderer, self.big_size, "1", target=True)

    def update(self):
        """викликати раз на кадр до малювання: підхоплює зміну розміру вікна"""
        self._layout()

    def present(self):
        self.tex_view.update(self.view)
        r = self.renderer
        r.target = self.tex_big
        self.tex_view.draw(dstrect=(0, 0, *self.big_size))
        r.target = None
        r.draw_color = (0, 0, 0, 255)
        r.clear()
        self.tex_big.draw(dstrect=self.dest)
        r.present()

    # -- мишка: з координат вікна в координати ігрового поля 400x700
    def to_game(self, pos):
        x = (pos[0] - self.dest.x) / self.k - self.ox
        y = (pos[1] - self.dest.y) / self.k
        return int(x), int(y)

    def mouse_pos(self):
        return self.to_game(pygame.mouse.get_pos())
