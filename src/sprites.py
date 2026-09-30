import json
import math
import os
import random
import pygame


def _load(base_dir, rel_path):
    return pygame.image.load(os.path.join(base_dir, rel_path)).convert_alpha()


class Animation:

    def __init__(self, sheet, frames, fps, pause=0.0, start=0.0):
        fw = sheet.get_width() // frames
        fh = sheet.get_height()
        self.frames = [sheet.subsurface((i * fw, 0, fw, fh)).copy() for i in range(frames)]
        self.fps = fps
        self.pause = pause
        self.play_time = frames / fps
        self.t = start % (self.play_time + pause)

    def update(self, dt):
        self.t = (self.t + dt) % (self.play_time + self.pause)

    def frame(self):
        if self.t >= self.play_time:
            return self.frames[0]
        return self.frames[min(int(self.t * self.fps), len(self.frames) - 1)]

class ScrollLayer:

    def __init__(self, image, y, factor):
        self.image = image
        self.y = y
        self.factor = factor
        self.period = image.get_width() // 2  
        self.offset = 0.0

    def update(self, speed, dt):
        self.offset = (self.offset + speed * self.factor * dt) % (self.period * 2)

    def draw(self, surf):
        x = -int(self.offset)
        w = self.image.get_width()
        while x < surf.get_width():
            surf.blit(self.image, (x, self.y))
            x += w


class Cloud:
    def __init__(self, image, x, y, speed, screen_w):
        self.image = image
        self.x = float(x)
        self.base_y = y
        self.y = y
        self.speed = speed
        self.screen_w = screen_w

    def update(self, dt):
        self.x -= self.speed * dt
        if self.x + self.image.get_width() < 0:
            self.x = self.screen_w + random.uniform(10, 140)
            self.y = self.base_y + random.randint(-12, 12)

    def draw(self, surf):
        surf.blit(self.image, (int(self.x), int(self.y)))


class Scenery:
    def __init__(self, base_dir, manifest, screen_w):
        self.sky = _load(base_dir, manifest["sky"]["file"]).convert()
        self.sky_wide = self.sky
        self.screen_w = screen_w
        self.cloud_specs = [(_load(base_dir, c["file"]), c) for c in manifest["clouds"]]
        self.clouds = [
            Cloud(img, c["x"], c["y"], c["speed"], screen_w) for img, c in self.cloud_specs
        ]
        self.view_w = screen_w
        layers = manifest["layers"]
        self.far = ScrollLayer(_load(base_dir, layers["far"]["file"]), layers["far"]["y"], layers["far"]["factor"])
        self.bushes = ScrollLayer(_load(base_dir, layers["bushes"]["file"]), layers["bushes"]["y"], layers["bushes"]["factor"])
        self.ground = ScrollLayer(_load(base_dir, layers["ground"]["file"]), layers["ground"]["y"], layers["ground"]["factor"])
        self.ground_y = manifest["screen"]["ground_y"]
        self.speed = 60.0  

    def set_view(self, view_w, ox):
        """
        полотно стало ширшим (широке вікно / повний екран): небо розтягуємо,
        а набір хмар повторюємо кожні screen_w пікселів, щоб по боках теж були хмари.
        ox -- де на полотні починається ігрове поле
        """
        if view_w == self.view_w:
            return
        self.view_w = view_w
        self.sky_wide = pygame.transform.scale(self.sky, (view_w, self.sky.get_height()))
        first = -math.ceil(ox / self.screen_w)
        last = math.ceil((view_w - ox) / self.screen_w)
        self.clouds = [
            Cloud(img, c["x"] + ox + k * self.screen_w, c["y"], c["speed"], view_w)
            for k in range(first, last) for img, c in self.cloud_specs
        ]

    def update(self, dt, target_speed=None, snap=False):
        if target_speed is not None:
            if snap:
                self.speed = float(target_speed)
            else:
                self.speed += (target_speed - self.speed) * min(1.0, 4.0 * dt)
        for c in self.clouds:
            c.update(dt)
        for layer in (self.far, self.bushes, self.ground):
            layer.update(self.speed, dt)

    def draw_back(self, surf):
        surf.blit(self.sky_wide if surf.get_width() == self.view_w else self.sky, (0, 0))
        for c in self.clouds:
            c.draw(surf)
        self.far.draw(surf)
        self.bushes.draw(surf)

    def draw_ground(self, surf):
        self.ground.draw(surf)


class TitleLine:
    CYCLE = 1.7    
    HOP = 0.75     
    LAND = 0.18   

    def __init__(self, image, x, y, delay, amp):
        self.image = image
        self.x = x
        self.y = y
        self.delay = delay
        self.amp = amp

    def draw(self, surf, t):
        c = (t - self.delay) % self.CYCLE
        dy, squash = 0.0, 0.0
        if c < self.HOP:
            u = c / self.HOP
            dy = -self.amp * 4 * u * (1 - u)             
        elif c < self.HOP + self.LAND:
            k = (c - self.HOP) / self.LAND
            squash = 0.10 * math.sin(math.pi * k)         
        img = self.image
        w, h = img.get_size()
        x, y = self.x, self.y + round(dy)
        if squash > 0.005:
            nw, nh = int(w * (1 + squash * 0.5)), int(h * (1 - squash))
            img = pygame.transform.smoothscale(img, (nw, nh))
            x -= (nw - w) // 2
            y += h - nh
        surf.blit(img, (x, y))


class Title:

    def __init__(self, base_dir, lines):
        self.lines = []
        for i, ln in enumerate(lines):
            self.lines.append(TitleLine(_load(base_dir, ln["file"]), ln["x"], ln["y"],
                                        delay=0.22 * i, amp=15 - 3 * i))

    def draw(self, surf, t):
        for line in reversed(self.lines):   
            line.draw(surf, t)


class GearFace:

    def __init__(self, base, gear_anim, ox, oy):
        self.base = base
        self.gear = gear_anim
        self.ox, self.oy = ox, oy
        self.speed = 1.0

    def update(self, dt):
        self.gear.update(dt * self.speed)

    def frame(self):
        img = self.base.copy()
        img.blit(self.gear.frame(), (self.ox, self.oy))
        return img


class ShineFace:

    def __init__(self, anim):
        self.anim = anim

    def update(self, dt):
        self.anim.update(dt)

    def frame(self):
        return self.anim.frame()


class SpriteButton:

    BOB_SPEED = 2.4

    def __init__(self, face, x, y, bob_phase=0.0, bob_amp=2.0, dark=0.27):
        self.face = face
        self.x, self.y = x, y
        self.bob_phase = bob_phase
        self.bob_amp = bob_amp
        self.dark = dark
        self.hover = 0.0
        self.press = 0.0

    def update(self, dt, hover=False, press=0.0):
        self.hover += ((1.0 if hover else 0.0) - self.hover) * min(1.0, 12.0 * dt)
        self.press = press
        if hasattr(self.face, "speed"):
            self.face.speed = 1.0 + 1.5 * self.hover + 7.0 * press 
        self.face.update(dt)

    def draw(self, surf, t, x=None, y=None):
        img = self.face.frame()
        w, h = img.get_size()
        x = self.x if x is None else x
        y = self.y if y is None else y
        y += round(math.sin(t * self.BOB_SPEED + self.bob_phase) * self.bob_amp)
        if self.press > 0.001:
            img = img.copy()
            m = int(255 * (1 - self.dark * self.press))
            img.fill((m, m, m), special_flags=pygame.BLEND_RGB_MULT)
        s = 1.0 + 0.03 * self.hover - 0.06 * self.press
        if abs(s - 1.0) > 0.004:
            nw, nh = int(w * s), int(h * s)
            img = pygame.transform.smoothscale(img, (nw, nh))
            x += (w - nw) // 2
            y += (h - nh) // 2
        surf.blit(img, (x, y))


class PipeArt:
    """Труба зі спрайтів: тіло повторюється по вертикалі, зверху/знизу капелюшок."""

    def __init__(self, base_dir, spec):
        self.body = _load(base_dir, spec["body"])
        self.neck = _load(base_dir, spec["neck"])
        self.cap = _load(base_dir, spec["cap"])
        self.cap_flip = pygame.transform.flip(self.cap, False, True)
        self.neck_flip = pygame.transform.flip(self.neck, False, True)
        self.body_w = spec["body_w"]
        self.cap_w = spec["cap_w"]
        self.cap_h = spec["cap_h"]

    def _column(self, surf, x, y0, y1):
        """тіло труби від y0 до y1"""
        th = self.body.get_height()
        y = y0
        while y < y1:
            h = min(th, y1 - y)
            surf.blit(self.body, (x, y), (0, 0, self.body_w, h))
            y += h

    def draw(self, surf, x, width, gap_y, gap, bottom):
        """x, width -- хітбокс труби; gap_y..gap_y+gap -- прохід; bottom -- де закінчується нижня труба"""
        cx = x + (width - self.cap_w) // 2
        bx = x + (width - self.body_w) // 2
        # -- верхня труба (капелюшок знизу)
        top_cap = gap_y - self.cap_h
        self._column(surf, bx, 0, top_cap)
        surf.blit(self.neck_flip, (bx, top_cap - self.neck.get_height()))
        surf.blit(self.cap_flip, (cx, top_cap))
        # -- нижня труба
        low = gap_y + gap
        self._column(surf, bx, low + self.cap_h, bottom)
        surf.blit(self.neck, (bx, low + self.cap_h))
        surf.blit(self.cap, (cx, low))


class BirdArt:
    """
    Пташка (скін): махає крилами і нахиляється залежно від швидкості.
    (ax, ay) -- де в кадрі центр тіла; саме ця точка ставиться в центр хітбокса
    (у великих пташок крила виходять далеко за тіло).
    """

    def __init__(self, base_dir, spec):
        self.id = spec["id"]
        self.price = spec["price"]
        self.anim = Animation(_load(base_dir, spec["file"]), spec["frames"], spec["fps"])
        self.w, self.h = spec["fw"], spec["fh"]
        self.ax, self.ay = spec.get("ax", self.w / 2), spec.get("ay", self.h / 2)

    def update(self, dt, flap_speed=1.0):
        self.anim.update(dt * flap_speed)

    def draw(self, surf, cx, cy, angle=0.0, frame=None):
        img = self.anim.frame() if frame is None else self.anim.frames[frame % len(self.anim.frames)]
        # -- зсув від центру картинки до центру тіла, повернутий разом з картинкою
        off = pygame.math.Vector2(self.ax - self.w / 2, self.ay - self.h / 2)
        if abs(angle) > 0.5:
            img = pygame.transform.rotate(img, angle)
            off = off.rotate(-angle)
        surf.blit(img, img.get_rect(center=(int(cx - off.x), int(cy - off.y))))


class NineSlice:
    """
    Розтягує картинку-панель під будь-який розмір, не чіпаючи кути.
    Середина по вертикалі -- один рядок з центру (інакше градієнт панелі розтягується смугами).
    """

    def __init__(self, image, border):
        self.b = border
        iw, ih = image.get_size()
        mid = image.subsurface((0, ih // 2, iw, 1))
        self.image = pygame.Surface((iw, 2 * border + 1), pygame.SRCALPHA)
        self.image.blit(image.subsurface((0, 0, iw, border)), (0, 0))
        self.image.blit(mid, (0, border))
        self.image.blit(image.subsurface((0, ih - border, iw, border)), (0, border + 1))
        self.cache = {}

    def render(self, w, h):
        if (w, h) in self.cache:
            return self.cache[(w, h)]
        img, b = self.image, self.b
        iw, ih = img.get_size()
        out = pygame.Surface((w, h), pygame.SRCALPHA)
        xs = [(0, b, 0, b), (b, iw - b, b, w - b), (iw - b, iw, w - b, w)]
        ys = [(0, b, 0, b), (b, ih - b, b, h - b), (ih - b, ih, h - b, h)]
        for sx0, sx1, dx0, dx1 in xs:
            for sy0, sy1, dy0, dy1 in ys:
                part = img.subsurface((sx0, sy0, sx1 - sx0, sy1 - sy0))
                if (dx1 - dx0, dy1 - dy0) != part.get_size():
                    part = pygame.transform.scale(part, (dx1 - dx0, dy1 - dy0))
                out.blit(part, (dx0, dy0))
        self.cache[(w, h)] = out
        return out


class SpriteKit:
    LANGS = ("en", "uk")

    def __init__(self, base_dir, press_dark=0.27):
        path = os.path.join(base_dir, "manifest.json")
        if not os.path.exists(path):
            raise FileNotFoundError(
                "нема assets/sprites/manifest.json -- запусти tools/make_sprites.py"
            )
        with open(path, encoding="utf-8") as fh:
            m = json.load(fh)
        extra_path = os.path.join(base_dir, "extra.json")
        if not os.path.exists(extra_path):
            raise FileNotFoundError(
                "нема assets/sprites/extra.json -- запусти tools/make_extra_sprites.py"
            )
        with open(extra_path, encoding="utf-8") as fh:
            ex = json.load(fh)

        screen_w = m["screen"]["w"]
        self.ground_y = m["screen"]["ground_y"]
        self.scenery = Scenery(base_dir, m, screen_w)

        # -- все, що залежить від мови: кнопки і тексти. Заголовок FLAPPY BIRD -- назва, не перекладаємо
        buttons = ex["buttons"]
        self.title = Title(base_dir, m["title"])

        def shine(b, start=0.0):
            return ShineFace(Animation(_load(base_dir, b["file"]), b["frames"], b["fps"], b["pause"], start))

        self.faces = {
            lang: {
                "play": shine(buttons[lang]["play"]),
                "shop": shine(buttons[lang]["shop"], start=1.6),
                "menu": shine(buttons[lang]["menu"]),
                "record": shine(buttons[lang]["record"], start=0.8),
            }
            for lang in self.LANGS
        }
        self.texts = {
            lang: {key: _load(base_dir, f) for key, f in items.items()}
            for lang, items in ex["texts"].items()
        }
        self.lang_names = {lang: _load(base_dir, f) for lang, f in ex["lang_names"].items()}
        # -- цифри: "dark" -- на кремовій панелі, "light" -- білі з контуром, "big" -- для рекорду
        self.digits = {
            name: {c: _load(base_dir, f) for c, f in ex[key].items()}
            for name, key in (("dark", "digits"), ("light", "digits_light"), ("big", "digits_big"))
        }
        self.trophy_small = _load(base_dir, ex["trophy"]["small"])
        self.trophy_big = _load(base_dir, ex["trophy"]["big"])

        bp = buttons["en"]
        self.play = SpriteButton(self.faces["en"]["play"], bp["play"]["x"], bp["play"]["y"],
                                 bob_phase=0.0, dark=press_dark)
        self.shop = SpriteButton(self.faces["en"]["shop"], bp["shop"]["x"], bp["shop"]["y"],
                                 bob_phase=1.3, dark=press_dark)
        self.menu = SpriteButton(self.faces["en"]["menu"], 0, 0, bob_phase=0.6, bob_amp=1.5, dark=press_dark)
        self.record = SpriteButton(self.faces["en"]["record"], bp["record"]["x"], bp["record"]["y"],
                                   bob_phase=2.6, dark=press_dark)

        st = m["settings"]
        g = st["gear"]
        gear = Animation(_load(base_dir, g["file"]), g["frames"], g["fps"])
        face = GearFace(_load(base_dir, st["base"]), gear, g["ox"], g["oy"])
        self.settings = SpriteButton(face, st["x"], st["y"], bob_amp=0.0, dark=press_dark)

        self.pipe = PipeArt(base_dir, ex["pipe"])
        # -- скіни пташок у порядку магазину; self.bird -- та, якою граємо
        self.skins = [BirdArt(base_dir, spec) for spec in ex["skins"]]
        self.skin_by_id = {b.id: b for b in self.skins}
        self.bird = self.skins[0]
        self.panel = NineSlice(_load(base_dir, ex["panel"]["file"]), ex["panel"]["slice"])

        c = ex["coin"]
        self.coin = Animation(_load(base_dir, c["file"]), c["frames"], c["fps"])
        self.coin_icon = self.coin.frames[0]

        self.lang = "en"

    def set_lang(self, lang):
        if lang not in self.LANGS:
            lang = "en"
        self.lang = lang
        self.play.face = self.faces[lang]["play"]
        self.shop.face = self.faces[lang]["shop"]
        self.menu.face = self.faces[lang]["menu"]
        self.record.face = self.faces[lang]["record"]

    def set_skin(self, skin_id):
        self.bird = self.skin_by_id.get(skin_id, self.skins[0])
        return self.bird.id

    def text(self, key):
        return self.texts[self.lang][key]

    def number_width(self, text, style="light", gap=2):
        digits = self.digits[style]
        imgs = [digits[c] for c in text if c in digits]
        return sum(i.get_width() for i in imgs) + gap * max(0, len(imgs) - 1)

    def draw_number(self, surf, text, x, cy, style="light", align="center", gap=2):
        """
        число зі спрайтів-цифр по вертикальному центру cy.
        Усі цифри одного стилю однакової висоти (базова лінія на одному місці),
        тому стоять рівно в рядок і з підписами того ж розміру.
        align: "center" -- x це центр, "left" -- лівий край, "right" -- правий край
        """
        digits = self.digits[style]
        imgs = [digits[c] for c in text if c in digits]
        if not imgs:
            return
        w = self.number_width(text, style, gap)
        if align == "center":
            x -= w // 2
        elif align == "right":
            x -= w
        for img in imgs:
            surf.blit(img, (x, cy - img.get_height() // 2))
            x += img.get_width() + gap
