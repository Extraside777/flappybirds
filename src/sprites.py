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
        self.offset = 0.0
        self.set(image, y, factor)

    def set(self, image, y, factor):
        """інша картинка шару (інший фон); зсув лишається -- шар не стрибає"""
        self.image = image
        self.y = y
        self.factor = factor
        self.period = image.get_width() // 2
        self.offset %= self.period * 2

    def update(self, speed, dt):
        self.offset = (self.offset + speed * self.factor * dt) % (self.period * 2)

    def draw(self, surf):
        x = -int(self.offset)
        w = self.image.get_width()
        while x < surf.get_width():
            surf.blit(self.image, (x, self.y))
            x += w


class Cloud:
    """хмара пливе вліво; idx -- яка це хмара з набору (у кожного фону свої кольори хмар)"""

    def __init__(self, idx, width, x, y, speed, screen_w):
        self.idx = idx
        self.width = width
        self.x = float(x)
        self.base_y = y
        self.y = y
        self.speed = speed
        self.screen_w = screen_w

    def update(self, dt):
        self.x -= self.speed * dt
        if self.x + self.width < 0:
            self.x = self.screen_w + random.uniform(10, 140)
            self.y = self.base_y + random.randint(-12, 12)

    def draw(self, surf, image):
        surf.blit(image, (int(self.x), int(self.y)))


# -- ефекти фонів: гра малює їх сама поверх картинок (на всю ширину полотна).
# -- layer: "sky" -- одразу після неба (за хмарами і горами), "front" -- перед кущами
class Stars:
    """зорі на нічному небі: мерехтять кожна у своєму темпі; зорі дуже далеко -- тому не їдуть"""
    layer = "sky"

    def __init__(self, view_w):
        rnd = random.Random(3)    # -- однакове розташування щоразу
        self.stars = [(rnd.randrange(view_w // 2) * 2, rnd.randrange(230) * 2, rnd.random() * 6.3,
                       rnd.uniform(1.2, 3.5), rnd.random() < 0.22) for _ in range(int(view_w * 0.16))]

    def update(self, dt, speed):
        pass

    def draw(self, surf, t):
        for x, y, phase, rate, cross in self.stars:
            b = 0.6 + 0.4 * math.sin(t * rate + phase)
            c = (int(255 * b), int(248 * b), int(215 * b))
            if cross:                     # -- яскраві зорі -- хрестиком
                surf.fill(c, (x - 2, y, 6, 2))
                surf.fill(c, (x, y - 2, 2, 6))
            else:
                surf.fill(c, (x, y, 2, 2))


class Snow:
    """сніжинки: падають, гойдаються, вітер і рух світу зносять їх уліво (ближчі -- більші і швидші)"""
    layer = "front"
    BOTTOM = 640

    def __init__(self, view_w):
        self.rnd = random.Random(5)
        self.w = view_w
        self.flakes = [[self.rnd.uniform(0, view_w), self.rnd.uniform(0, self.BOTTOM), self.rnd.uniform(30, 70),
                        self.rnd.choice((2, 2, 2, 4)), self.rnd.random() * 6.3] for _ in range(int(view_w * 0.14))]

    def update(self, dt, speed):
        for f in self.flakes:
            f[1] += f[2] * dt
            f[0] -= (speed * 0.3 + 12) * dt * f[3] / 3
            if f[1] > self.BOTTOM:
                f[1] -= self.BOTTOM + 10
                f[0] = self.rnd.uniform(0, self.w)
            if f[0] < -10:
                f[0] += self.w + 20

    def draw(self, surf, t):
        for x, y, _, size, phase in self.flakes:
            x = int(x + math.sin(t * 1.3 + phase) * 5) // 2 * 2     # -- по сітці 2 px, як піксель-арт
            surf.fill((255, 255, 255) if size > 2 else (226, 238, 255), (x, int(y) // 2 * 2, size, size))


class Fireflies:
    """світлячки над нічними кущами: блимають і кружляють, їдуть разом з кущами"""
    layer = "front"

    def __init__(self, view_w):
        rnd = random.Random(9)
        self.w = view_w
        self.flies = [[rnd.uniform(0, view_w), rnd.uniform(500, 600), rnd.random() * 6.3, rnd.uniform(0.6, 1.2)]
                      for _ in range(max(4, int(view_w * 0.035)))]
        self.glow = pygame.Surface((12, 12), pygame.SRCALPHA)
        pygame.draw.circle(self.glow, (190, 255, 110, 60), (6, 6), 6)
        pygame.draw.circle(self.glow, (220, 255, 150, 120), (6, 6), 3)

    def update(self, dt, speed):
        for f in self.flies:
            f[0] -= speed * 0.45 * dt
            if f[0] < -30:
                f[0] += self.w + 60

    def draw(self, surf, t):
        for x, y, phase, rate in self.flies:
            k = 0.5 + 0.5 * math.sin(t * 2.5 * rate + phase)
            x += math.sin(t * 0.8 * rate + phase) * 14
            y += math.sin(t * 1.3 * rate + phase * 2) * 8
            self.glow.set_alpha(int(170 * k))
            surf.blit(self.glow, (int(x) - 6, int(y) - 6))
            if k > 0.3:
                surf.fill((250, 255, 170), (int(x) // 2 * 2, int(y) // 2 * 2, 2, 2))


FX = {"stars": Stars, "snow": Snow, "fireflies": Fireflies}


class Backdrop:
    """
    Один фон (з магазину): небо, шари гір/міста, кущів і землі, світило (сонце/місяць),
    свої кольори хмар і ефекти. Розташування хмар -- спільне для всіх фонів (manifest.json).
    """

    def __init__(self, base_dir, spec, default_clouds):
        self.id = spec["id"]
        self.price = spec["price"]
        self.sky = _load(base_dir, spec["sky"]).convert()
        self.layers = {name: (_load(base_dir, layer["file"]), layer["y"], layer["factor"])
                       for name, layer in spec["layers"].items()}
        body = spec.get("body")
        self.body = None if not body else (_load(base_dir, body["file"]), body["x"], body["y"], body["thumb_y"])
        self.clouds = [_load(base_dir, f) for f in spec["clouds"]] if spec.get("clouds") else default_clouds
        self.fx = [name for name in spec.get("fx", []) if name in FX]


class Scenery:
    # -- мініатюра фону в магазині: смуга сцени від неба над горизонтом до землі (у координатах поля)
    THUMB_TOP, THUMB_H = 360, 320

    def __init__(self, base_dir, manifest, backdrops, screen_w):
        self.screen_w = screen_w
        self.cloud_specs = manifest["clouds"]
        default_clouds = [_load(base_dir, c["file"]) for c in self.cloud_specs]
        self.themes = [Backdrop(base_dir, spec, default_clouds) for spec in backdrops]
        self.theme_by_id = {th.id: th for th in self.themes}
        self.view_w, self.ox = screen_w, 0
        self.clouds = [Cloud(i, default_clouds[i].get_width(), c["x"], c["y"], c["speed"], screen_w)
                       for i, c in enumerate(self.cloud_specs)]
        self.ground_y = manifest["screen"]["ground_y"]
        self.speed = 60.0
        self.t = 0.0
        first = self.themes[0]
        self.far = ScrollLayer(*first.layers["far"])
        self.bushes = ScrollLayer(*first.layers["bushes"])
        self.ground = ScrollLayer(*first.layers["ground"])
        self._thumbs = {}
        self.set_theme(first.id)

    def set_theme(self, theme_id):
        """змінює фон (шари їдуть далі з того ж місця); повертає id фону, який реально поставили"""
        self.theme = self.theme_by_id.get(theme_id, self.themes[0])
        self.sky = self.theme.sky
        self.sky_wide = self._wide_sky()
        for layer, name in ((self.far, "far"), (self.bushes, "bushes"), (self.ground, "ground")):
            layer.set(*self.theme.layers[name])
        self.fx = [FX[name](self.view_w) for name in self.theme.fx]
        return self.theme.id

    def _wide_sky(self):
        if self.view_w == self.sky.get_width():
            return self.sky
        return pygame.transform.scale(self.sky, (self.view_w, self.sky.get_height()))

    def set_view(self, view_w, ox):
        """
        полотно стало ширшим (широке вікно / повний екран): небо розтягуємо,
        а набір хмар повторюємо кожні screen_w пікселів, щоб по боках теж були хмари.
        ox -- де на полотні починається ігрове поле
        """
        if view_w == self.view_w:
            return
        self.view_w, self.ox = view_w, ox
        self.sky_wide = self._wide_sky()
        first = -math.ceil(ox / self.screen_w)
        last = math.ceil((view_w - ox) / self.screen_w)
        self.clouds = [
            Cloud(i, self.theme.clouds[i].get_width(), c["x"] + ox + k * self.screen_w, c["y"], c["speed"], view_w)
            for k in range(first, last) for i, c in enumerate(self.cloud_specs)
        ]
        self.fx = [FX[name](view_w) for name in self.theme.fx]

    def update(self, dt, target_speed=None, snap=False):
        if target_speed is not None:
            if snap:
                self.speed = float(target_speed)
            else:
                self.speed += (target_speed - self.speed) * min(1.0, 4.0 * dt)
        self.t += dt
        for c in self.clouds:
            c.update(dt)
        for layer in (self.far, self.bushes, self.ground):
            layer.update(self.speed, dt)
        for fx in self.fx:
            fx.update(dt, self.speed)

    def _draw_scene(self, surf, theme, ox, clouds, fx, t, thumb=False):
        """світило, хмари, гори/місто, кущі і ефекти -- усе, що позаду труб (небо вже намальоване)"""
        for f in fx:
            if f.layer == "sky":
                f.draw(surf, t)
        if theme.body:
            img, x, y, thumb_y = theme.body
            surf.blit(img, (ox + x, thumb_y if thumb else y))
        for c in clouds:
            c.draw(surf, theme.clouds[c.idx])
        self.far.draw(surf)
        self.bushes.draw(surf)
        for f in fx:
            if f.layer == "front":
                f.draw(surf, t)

    def draw_back(self, surf):
        surf.blit(self.sky_wide if surf.get_width() == self.view_w else self.sky, (0, 0))
        self._draw_scene(surf, self.theme, self.ox, self.clouds, self.fx, self.t)

    def draw_ground(self, surf):
        self.ground.draw(surf)

    def thumbnail(self, theme_id, size):
        """мініатюра фону для картки магазину (малюється один раз і запам'ятовується)"""
        key = (theme_id, size)
        if key not in self._thumbs:
            theme = self.theme_by_id[theme_id]
            w = round(self.THUMB_H * size[0] / size[1])
            ox = (w - self.screen_w) // 2
            surf = pygame.Surface((w, self.sky.get_height())).convert()
            surf.blit(pygame.transform.scale(theme.sky, surf.get_size()), (0, 0))
            clouds = [Cloud(i, 0, c["x"] + ox, c["y"], 0, w) for i, c in enumerate(self.cloud_specs)]
            # -- шари цього фону на час малювання, з нульовим зсувом
            saved = [(layer, layer.image, layer.y, layer.factor, layer.offset)
                     for layer in (self.far, self.bushes, self.ground)]
            for layer, name in ((self.far, "far"), (self.bushes, "bushes"), (self.ground, "ground")):
                layer.set(*theme.layers[name])
                layer.offset = 0.0
            self._draw_scene(surf, theme, ox, clouds, [FX[name](w) for name in theme.fx], 0.0, thumb=True)
            self.ground.draw(surf)
            for layer, image, y, factor, offset in saved:
                layer.set(image, y, factor)
                layer.offset = offset
            band = surf.subsurface((0, self.THUMB_TOP, w, self.THUMB_H))
            self._thumbs[key] = pygame.transform.smoothscale(band, size)
        return self._thumbs[key]


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
        self.art_px = spec.get("art_px")   # -- піксель-арт: розмір художнього пікселя (None -- звичайна картинка)

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


# -- шлейфи в порядку магазину: (id, ціна). "none" -- без шлейфу, є в усіх;
# -- "custom" -- свій: кольори, стиль і товщину гравець обирає сам (CustomTrail)
TRAILS = [("none", 0), ("neon", 150), ("rainbow", 250), ("custom", 500)]
RAINBOW = [(255, 72, 72), (255, 160, 48), (255, 228, 64), (96, 216, 88), (72, 160, 255), (164, 100, 240)]

# -- палітра свого шлейфу (у редакторі -- 2 ряди по 8) і стилі (у порядку перемикача)
TRAIL_PALETTE = [
    (255, 64, 64), (255, 140, 40), (255, 222, 60), (150, 230, 60),
    (50, 200, 90), (50, 220, 220), (70, 150, 255), (64, 72, 230),
    (150, 80, 245), (230, 70, 220), (255, 120, 180), (255, 255, 255),
    (255, 200, 130), (150, 100, 60), (140, 140, 160), (40, 30, 50),
]
TRAIL_STYLES = ("ribbon", "glow", "bubbles", "pixels", "sparks")
WHITE = (255, 255, 255)


def _lerp(c0, c1, k):
    return tuple(round(a + (b - a) * k) for a, b in zip(c0, c1))


class Trail:
    """
    Шлейф за пташкою: напівпрозора смуга по точках, де пташка вже пролетіла.
    pts -- [(x, y, k, seed)] від голови (k=0, біля пташки) до хвоста (k=1, майже зник);
    seed 0..1 -- випадкове число точки (для іскорок).
    Смуга малюється на окреме прозоре полотно розміром зі шлейф, а потім кладеться на екран.
    """

    RAINBOW_BAND = 3                         # -- px, товщина однієї смуги веселки
    NEON_GLOW, NEON_CORE = 22, 8             # -- px, ширина світіння і яскравої серединки
    NEON_FROM, NEON_TO = (255, 50, 190), (120, 50, 255)   # -- від рожевого біля пташки до фіолетового

    def __init__(self, trail_id, price):
        self.id = trail_id
        self.price = price

    def margin(self):
        """на скільки px шлейф може вилазити за свої точки (запас полотна)"""
        return 20

    def draw(self, surf, pts, t):
        if self.id == "none" or len(pts) < 2:
            return
        m = self.margin()
        x0 = int(min(p[0] for p in pts)) - m
        y0 = int(min(p[1] for p in pts)) - m
        w = int(max(p[0] for p in pts)) + m - x0
        h = int(max(p[1] for p in pts)) + m - y0
        layer = pygame.Surface((w, h), pygame.SRCALPHA)
        self.paint(layer, [(x - x0, y - y0, k, seed) for x, y, k, seed in pts], t)
        surf.blit(layer, (x0, y0))

    def paint(self, layer, pts, t):
        if self.id == "rainbow":
            self._rainbow(layer, pts)
        else:
            self._glow(layer, pts, t, self.NEON_FROM, self.NEON_TO, self.NEON_GLOW, self.NEON_CORE)

    @staticmethod
    def _normals(pts):
        """для кожної точки -- одиничний вектор поперек шлейфу (щоб товщина не залежала від нахилу)"""
        out = []
        for i in range(len(pts)):
            a, b = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]
            dx, dy = a[0] - b[0], a[1] - b[1]
            n = math.hypot(dx, dy) or 1.0
            out.append((-dy / n, dx / n))
        return out

    @staticmethod
    def _band(layer, a, b, na, nb, oa, ob, color):
        """чотирикутник між сусідніми точками a і b: oa/ob -- (від, до) зсуву поперек шлейфу"""
        pygame.draw.polygon(layer, color, [
            (round(a[0] + na[0] * oa[0]), round(a[1] + na[1] * oa[0])),
            (round(b[0] + nb[0] * ob[0]), round(b[1] + nb[1] * ob[0])),
            (round(b[0] + nb[0] * ob[1]), round(b[1] + nb[1] * ob[1])),
            (round(a[0] + na[0] * oa[1]), round(a[1] + na[1] * oa[1]))])

    def _rainbow(self, layer, pts):
        n = len(RAINBOW)
        normals = self._normals(pts)
        for i, (a, b) in enumerate(zip(pts, pts[1:])):
            ha = self.RAINBOW_BAND * (1 - 0.35 * a[2])        # -- до хвоста трохи тоншає
            hb = self.RAINBOW_BAND * (1 - 0.35 * b[2])
            alpha = int(210 * (1 - a[2]) ** 0.7)
            for j, color in enumerate(RAINBOW):
                o = j - n / 2
                self._band(layer, a, b, normals[i], normals[i + 1], (o * ha, (o + 1) * ha),
                           (o * hb, (o + 1) * hb), (*color, alpha))

    def _glow(self, layer, pts, t, c_from, c_to, glow, core):
        """неон: широке напівпрозоре світіння, яскрава серединка і іскорки поруч"""
        normals = self._normals(pts)
        for width, alpha, light in ((glow, 150, 0.0), (core, 255, 0.5)):
            for i, (a, b) in enumerate(zip(pts, pts[1:])):
                color = _lerp(c_from, c_to, a[2])
                color = _lerp(color, WHITE, light)
                wa = width * (1 - 0.6 * a[2]) / 2
                wb = width * (1 - 0.6 * b[2]) / 2
                self._band(layer, a, b, normals[i], normals[i + 1], (-wa, wa), (-wb, wb),
                           (*color, int(alpha * (1 - a[2]) ** 0.7)))
        # -- іскорки: маленькі хрестики, що мерехтять поруч зі смугою
        for (x, y, k, seed), (nx, ny) in zip(pts, normals):
            if seed > 0.14 or k < 0.12:
                continue
            r = 2 if math.sin(t * 18 + seed * 90) > 0 else 1
            c = (*WHITE, int(255 * (1 - k)))
            off = (seed - 0.07) * 160 * glow / self.NEON_GLOW
            x, y = int(x + nx * off), int(y + ny * off)
            layer.fill(c, (x - r, y, 2 * r + 1, 1))
            layer.fill(c, (x, y - r, 1, 2 * r + 1))


class CustomTrail(Trail):
    """
    Свій шлейф: колір біля пташки (c1) переходить у колір хвоста (c2), стиль -- з TRAIL_STYLES,
    товщина 0..1. Усе це -- в self.config: гра підставляє сюди словник зі збереження,
    і редактор у магазині міняє його прямо на льоту.
    """

    MIN_W, MAX_W = 6, 30     # -- px, товщина шлейфу при повзунку на 0 і на 100%

    def __init__(self, price):
        super().__init__("custom", price)
        self.config = {"c1": 9, "c2": 6, "style": "glow", "width": 0.5}

    def colors(self):
        n = len(TRAIL_PALETTE)
        return TRAIL_PALETTE[self.config["c1"] % n], TRAIL_PALETTE[self.config["c2"] % n]

    def width(self):
        return self.MIN_W + (self.MAX_W - self.MIN_W) * self.config["width"]

    def margin(self):
        return int(self.width() * 1.6) + 10

    def paint(self, layer, pts, t):
        c1, c2 = self.colors()
        w = self.width()
        style = self.config["style"]
        if style == "glow":
            self._glow(layer, pts, t, c1, c2, w * 1.25, w * 0.45)
        elif style == "bubbles":
            self._bubbles(layer, pts, c1, c2, w)
        elif style == "pixels":
            self._pixels(layer, pts, c1, c2, w)
        elif style == "sparks":
            self._sparks(layer, pts, t, c1, c2, w)
        else:
            self._ribbon(layer, pts, c1, c2, w)

    def _ribbon(self, layer, pts, c1, c2, w):
        """суцільна стрічка, до хвоста тоншає; уздовж верхнього краю -- світла смужка-блік"""
        normals = self._normals(pts)
        for i, (a, b) in enumerate(zip(pts, pts[1:])):
            color = _lerp(c1, c2, a[2])
            alpha = int(250 * (1 - a[2]) ** 0.55)
            wa, wb = w * (1 - 0.5 * a[2]) / 2, w * (1 - 0.5 * b[2]) / 2
            na, nb = normals[i], normals[i + 1]
            self._band(layer, a, b, na, nb, (-wa, wa), (-wb, wb), (*color, alpha))
            self._band(layer, a, b, na, nb, (-wa * 0.7, -wa * 0.2), (-wb * 0.7, -wb * 0.2),
                       (*_lerp(color, WHITE, 0.45), alpha))

    @staticmethod
    def _bubbles(layer, pts, c1, c2, w):
        """бульбашки: з'являються біля пташки маленькими, ростуть, розлітаються і зникають"""
        for x, y, k, seed in reversed(pts):          # -- старі (великі) знизу, нові зверху
            if seed > 0.2:
                continue
            r = max(2, round(w * (0.22 + 0.4 * k)))
            cy = y + (seed / 0.2 - 0.5) * w * 1.2 * k
            color = _lerp(c1, c2, k)
            alpha = int(250 * (1 - k) ** 0.5)
            centre = (round(x), round(cy))
            pygame.draw.circle(layer, (*color, alpha // 2), centre, r)
            pygame.draw.circle(layer, (*_lerp(color, WHITE, 0.15), alpha), centre, r, width=max(2, r // 4))
            layer.fill((*WHITE, alpha), (centre[0] - r // 2, centre[1] - r // 2, 2, 2))

    @staticmethod
    def _pixels(layer, pts, c1, c2, w):
        """8-бітні «пікселі»: квадратики по сітці, розлітаються і зменшуються до хвоста"""
        s = max(4, round(w / 3) // 2 * 2)
        for x, y, k, seed in pts:
            if seed > 0.6:
                continue
            size = max(2, round(s * (1 - 0.6 * k)) // 2 * 2)
            off = (seed / 0.6 - 0.5) * w * (0.5 + 0.9 * k)
            color = c1 if seed < 0.2 else c2 if seed > 0.45 else _lerp(c1, c2, k)
            layer.fill((*color, int(255 * (1 - k) ** 0.4)),
                       (int(x) // 2 * 2 - size // 2, int(y + off) // 2 * 2 - size // 2, size, size))

    def _sparks(self, layer, pts, t, c1, c2, w):
        """тонка яскрава нитка і зірочки навколо неї, що мерехтять"""
        normals = self._normals(pts)
        core = max(3.0, w * 0.22)
        for i, (a, b) in enumerate(zip(pts, pts[1:])):
            color = _lerp(_lerp(c1, c2, a[2]), WHITE, 0.3)
            wa, wb = core * (1 - 0.5 * a[2]) / 2, core * (1 - 0.5 * b[2]) / 2
            self._band(layer, a, b, normals[i], normals[i + 1], (-wa, wa), (-wb, wb),
                       (*color, int(230 * (1 - a[2]) ** 0.7)))
        for (x, y, k, seed), (nx, ny) in zip(pts, normals):
            if seed > 0.32 or k < 0.05:
                continue
            r = max(1, round(w / 6 * (1 - k) * (0.6 + seed)))
            if math.sin(t * 16 + seed * 70) < -0.4:
                r = max(1, r - 1)
            th = 2 if r >= 3 else 1                     # -- великі зірочки -- з товстішими променями
            off = (seed / 0.32 - 0.5) * w * 1.4
            x, y = int(x + nx * off), int(y + ny * off)
            alpha = int(255 * (1 - k) ** 0.6)
            color = (*(c1 if seed < 0.16 else c2), alpha)
            layer.fill(color, (x - r, y, 2 * r + th, th))
            layer.fill(color, (x, y - r, th, 2 * r + th))
            layer.fill((*WHITE, alpha), (x, y, th, th))


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
        # -- фони в порядку магазину (перший -- звичайний «день»); self.scenery малює обраний
        self.scenery = Scenery(base_dir, m, ex["backgrounds"], screen_w)
        self.backgrounds = self.scenery.themes

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
                "done": shine(buttons[lang]["done"]),
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
        self.done = SpriteButton(self.faces["en"]["done"], 0, 0, bob_phase=0.6, bob_amp=1.5, dark=press_dark)
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

        # -- бонуси (іконки в бульбашках) і бульбашка щита навколо пташки
        def anim(spec):
            return Animation(_load(base_dir, spec["file"]), spec["frames"], spec["fps"], spec["pause"])

        pu = ex["powerups"]
        self.powerups = {kind: anim(pu[kind]) for kind in ("shield", "slow", "x2")}
        self.aura = anim(pu["aura"])

        # -- шлейфи за пташкою (малюються кодом, без картинок); self.trail -- обраний
        self.trails = [CustomTrail(price) if tid == "custom" else Trail(tid, price) for tid, price in TRAILS]
        self.trail_by_id = {tr.id: tr for tr in self.trails}
        self.trail = self.trails[0]
        self.custom_trail = self.trail_by_id["custom"]

        self.lang = "en"

    def set_lang(self, lang):
        if lang not in self.LANGS:
            lang = "en"
        self.lang = lang
        self.play.face = self.faces[lang]["play"]
        self.shop.face = self.faces[lang]["shop"]
        self.menu.face = self.faces[lang]["menu"]
        self.record.face = self.faces[lang]["record"]
        self.done.face = self.faces[lang]["done"]

    def set_skin(self, skin_id):
        self.bird = self.skin_by_id.get(skin_id, self.skins[0])
        return self.bird.id

    def set_trail(self, trail_id):
        self.trail = self.trail_by_id.get(trail_id, self.trails[0])
        return self.trail.id

    def set_background(self, bg_id):
        return self.scenery.set_theme(bg_id)

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
