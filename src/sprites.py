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
        self.clouds = [
            Cloud(_load(base_dir, c["file"]), c["x"], c["y"], c["speed"], screen_w)
            for c in manifest["clouds"]
        ]
        layers = manifest["layers"]
        self.far = ScrollLayer(_load(base_dir, layers["far"]["file"]), layers["far"]["y"], layers["far"]["factor"])
        self.bushes = ScrollLayer(_load(base_dir, layers["bushes"]["file"]), layers["bushes"]["y"], layers["bushes"]["factor"])
        self.ground = ScrollLayer(_load(base_dir, layers["ground"]["file"]), layers["ground"]["y"], layers["ground"]["factor"])
        self.ground_y = manifest["screen"]["ground_y"]
        self.speed = 60.0  

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
        surf.blit(self.sky, (0, 0))
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


class SpriteKit:
    def __init__(self, base_dir, press_dark=0.27):
        path = os.path.join(base_dir, "manifest.json")
        if not os.path.exists(path):
            raise FileNotFoundError(
            )
        with open(path, encoding="utf-8") as fh:
            m = json.load(fh)

        screen_w = m["screen"]["w"]
        self.ground_y = m["screen"]["ground_y"]
        self.scenery = Scenery(base_dir, m, screen_w)
        self.title = Title(base_dir, m["title"])

        def shine(key, start=0.0):
            b = m["buttons"][key]
            return ShineFace(Animation(_load(base_dir, b["file"]), b["frames"], b["fps"], b["pause"], start))

        self.play = SpriteButton(shine("play"), m["buttons"]["play"]["x"], m["buttons"]["play"]["y"],
                                 bob_phase=0.0, dark=press_dark)
        self.shop = SpriteButton(shine("shop", start=1.6), m["buttons"]["shop"]["x"], m["buttons"]["shop"]["y"],
                                 bob_phase=1.3, dark=press_dark)
        self.menu = SpriteButton(shine("menu"), 0, 0, bob_phase=0.6, bob_amp=1.5, dark=press_dark)

        st = m["settings"]
        g = st["gear"]
        gear = Animation(_load(base_dir, g["file"]), g["frames"], g["fps"])
        face = GearFace(_load(base_dir, st["base"]), gear, g["ox"], g["oy"])
        self.settings = SpriteButton(face, st["x"], st["y"], bob_amp=0.0, dark=press_dark)
