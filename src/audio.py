import os
import pygame


class Music:
    """
    Фонова музика з плавним переходом між треками.
    pygame.mixer.music грає тільки один трек, тому перехід такий:
    старий трек тихо згасає -> вмикаємо новий і він плавно наростає.
    """

    FADE = 0.5      # -- сек, за скільки згасає/наростає трек

    def __init__(self, tracks, max_volume=0.5):
        self.tracks = tracks                 # -- {"menu": path, "game": path}
        self.max_volume = max_volume         # -- гучність при повзунку на 100%
        self.levels = {name: 0.5 for name in tracks}   # -- повзунки 0..1
        self.current = None
        self.wanted = None
        self.fade = 0.0                      # -- 0 = тиша, 1 = повна гучність
        self.ok = True
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except pygame.error:
            self.ok = False                  # -- нема звукової карти -- граємо без музики

    def set_level(self, name, value):
        self.levels[name] = max(0.0, min(1.0, value))

    def play(self, name):
        self.wanted = name

    def _volume(self):
        if self.current is None:
            return 0.0
        return (self.levels[self.current] ** 1.5) * self.max_volume * self.fade

    def update(self, dt):
        if not self.ok:
            return
        step = dt / self.FADE
        if self.wanted != self.current:
            self.fade -= step
            if self.fade <= 0 or self.current is None:
                self.fade = 0.0
                self.current = self.wanted
                path = self.tracks.get(self.current)
                if path and os.path.exists(path):
                    pygame.mixer.music.load(path)
                    pygame.mixer.music.set_volume(0)
                    pygame.mixer.music.play(-1)
                else:
                    pygame.mixer.music.stop()
        else:
            self.fade = min(1.0, self.fade + step)
        pygame.mixer.music.set_volume(self._volume())


class Sounds:
    """короткі звуки (монетка і т.д.) з одним спільним повзунком гучності"""

    def __init__(self, files, max_volume=0.6):
        self.max_volume = max_volume
        self.level = 0.6
        self.sounds = {}
        for name, path in files.items():
            try:
                self.sounds[name] = pygame.mixer.Sound(path)
            except (pygame.error, FileNotFoundError):
                pass                           # -- нема файлу або звуку -- просто мовчимо

    def set_level(self, value):
        self.level = max(0.0, min(1.0, value))

    def play(self, name):
        snd = self.sounds.get(name)
        if snd is None or self.level <= 0:
            return
        snd.set_volume((self.level ** 1.5) * self.max_volume)
        snd.play()
