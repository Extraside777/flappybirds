// -- фон: небо, хмари, шари гір/міста, кущів і землі (паралакс), світило і ефекти -- як Scenery.java.
// -- Малює в координатах полотна: x від 0 до viewW, y -- як у ігрового поля (0..700), зсунутого на dy вниз.
// -- На високому екрані телефона земля завжди внизу екрана, а небо продовжується вгору (top)
import * as Gfx from './gfx.js';
import { Pic, rgb } from './gfx.js';

/** випадкові числа з зерном (однакове розташування зірок і снігу щоразу) */
export function seeded(seed) {
    let s = seed >>> 0;
    return () => {
        s = (s + 0x6D2B79F5) >>> 0;
        let t = s;
        t = Math.imul(t ^ (t >>> 15), t | 1);
        t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
        return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
}

const randInt = (rnd, n) => Math.floor(rnd() * n);

// -- шар, що їде вліво і повторюється по горизонталі
class ScrollLayer {
    constructor(l) {
        this.offset = 0;
        this.set(l);
    }

    /** інша картинка шару (інший фон); зсув лишається -- шар не стрибає */
    set(l) {
        this.image = l.image;
        this.y = l.y;
        this.factor = l.factor;
        this.period = Math.trunc(this.image.width / 2);
        this.offset %= this.period * 2;
    }

    update(speed, dt) {
        this.offset = (this.offset + speed * this.factor * dt) % (this.period * 2);
        if (this.offset < 0) {
            this.offset += this.period * 2;
        }
    }

    draw(c, width) {
        const w = this.image.width;
        for (let x = -Math.trunc(this.offset); x < width; x += w) {
            Gfx.blit(c, this.image, x, this.y);
        }
    }
}

/** хмара пливе вліво; idx -- яка це хмара з набору (у кожного фону свої кольори хмар) */
class Cloud {
    constructor(idx, width, x, y, speed, screenW) {
        Object.assign(this, { idx, width, x, speed, screenW });
        this.baseY = y;
        this.y = y;
    }

    update(dt) {
        this.x -= this.speed * dt;
        if (this.x + this.width < 0) {
            this.x = this.screenW + 10 + Math.random() * 130;
            this.y = this.baseY + randInt(Math.random, 25) - 12;
        }
    }

    draw(c, image) {
        Gfx.blit(c, image, Math.trunc(this.x), this.y);
    }
}

// -- ефекти фонів: гра малює їх сама поверх картинок (на всю ширину полотна).
// -- sky -- одразу після неба (за хмарами і горами), інакше -- перед кущами

/** зорі на нічному небі: мерехтять кожна у своєму темпі; зорі дуже далеко -- тому не їдуть */
class Stars {
    constructor(viewW, top) {
        const rnd = seeded(3);
        const span = 460 + top;
        const n = Math.trunc(viewW * 0.16 * span / 460);
        this.stars = [];
        for (let i = 0; i < n; i++) {
            this.stars.push({
                x: randInt(rnd, Math.max(1, viewW / 2)) * 2, y: randInt(rnd, Math.max(1, span / 2)) * 2 - top,
                phase: rnd() * 6.3, rate: 1.2 + rnd() * 2.3, cross: rnd() < 0.22,
            });
        }
    }

    sky() {
        return true;
    }

    update() {
    }

    draw(c, t) {
        for (const s of this.stars) {
            const b = 0.6 + 0.4 * Math.sin(t * s.rate + s.phase);
            const col = rgb(255 * b, 248 * b, 215 * b);
            if (s.cross) {                      // -- яскраві зорі -- хрестиком
                Gfx.fill(c, col, s.x - 2, s.y, 6, 2);
                Gfx.fill(c, col, s.x, s.y - 2, 2, 6);
            } else {
                Gfx.fill(c, col, s.x, s.y, 2, 2);
            }
        }
    }
}

/** сніжинки: падають, гойдаються, вітер і рух світу зносять їх уліво (ближчі -- більші і швидші) */
class Snow {
    static BOTTOM = 640;

    constructor(viewW, top) {
        this.rnd = seeded(5);
        this.w = viewW;
        this.top = top;
        const n = Math.trunc(viewW * 0.14 * (Snow.BOTTOM + top) / Snow.BOTTOM);
        const sizes = [2, 2, 2, 4];
        this.flakes = [];
        for (let i = 0; i < n; i++) {
            this.flakes.push([this.rnd() * viewW, this.rnd() * (Snow.BOTTOM + top) - top, 30 + this.rnd() * 40,
                sizes[randInt(this.rnd, 4)], this.rnd() * 6.3]);
        }
    }

    sky() {
        return false;
    }

    update(dt, speed) {
        for (const f of this.flakes) {
            f[1] += f[2] * dt;
            f[0] -= (speed * 0.3 + 12) * dt * f[3] / 3;
            if (f[1] > Snow.BOTTOM) {
                f[1] -= Snow.BOTTOM + this.top + 10;
                f[0] = this.rnd() * this.w;
            }
            if (f[0] < -10) {
                f[0] += this.w + 20;
            }
        }
    }

    draw(c, t) {
        for (const f of this.flakes) {
            const x = Math.floor((f[0] + Math.sin(t * 1.3 + f[4]) * 5) / 2) * 2;    // -- по сітці 2 px
            const y = Math.floor(f[1] / 2) * 2;
            Gfx.fill(c, f[3] > 2 ? 0xFFFFFF : rgb(226, 238, 255), x, y, f[3], f[3]);
        }
    }
}

let glow = null;

/** світлячки над нічними кущами: блимають і кружляють, їдуть разом з кущами */
class Fireflies {
    constructor(viewW) {
        const rnd = seeded(9);
        this.w = viewW;
        const n = Math.max(4, Math.trunc(viewW * 0.035));
        this.flies = [];
        for (let i = 0; i < n; i++) {
            this.flies.push([rnd() * viewW, 500 + rnd() * 100, rnd() * 6.3, 0.6 + rnd() * 0.6]);
        }
        if (!glow) {
            const cv = Gfx.canvas(12, 12);
            const g = cv.getContext('2d');
            Gfx.circle(g, rgb(190, 255, 110), 6, 6, 6, 60);
            g.save();
            g.beginPath();
            g.arc(6, 6, 3, 0, Math.PI * 2);
            g.clip();
            g.clearRect(0, 0, 12, 12);      // -- як у pygame: внутрішнє коло замінює (а не змішує) зовнішнє
            Gfx.circle(g, rgb(220, 255, 150), 6, 6, 3, 120);
            g.restore();
            glow = new Pic(cv);
        }
    }

    sky() {
        return false;
    }

    update(dt, speed) {
        for (const f of this.flies) {
            f[0] -= speed * 0.45 * dt;
            if (f[0] < -30) {
                f[0] += this.w + 60;
            }
        }
    }

    draw(c, t) {
        for (const f of this.flies) {
            const k = 0.5 + 0.5 * Math.sin(t * 2.5 * f[3] + f[2]);
            const x = f[0] + Math.sin(t * 0.8 * f[3] + f[2]) * 14;
            const y = f[1] + Math.sin(t * 1.3 * f[3] + f[2] * 2) * 8;
            Gfx.blit(c, glow, Math.trunc(x) - 6, Math.trunc(y) - 6, Math.trunc(170 * k));
            if (k > 0.3) {
                Gfx.fill(c, rgb(250, 255, 170), Math.floor(x / 2) * 2, Math.floor(y / 2) * 2, 2, 2);
            }
        }
    }
}

const FX = { stars: (w, top) => new Stars(w, top), snow: (w, top) => new Snow(w, top), fireflies: (w) => new Fireflies(w) };

/** колір пікселя картинки (x, y) -- 0xRRGGBB */
function pixel(p, x, y) {
    const cv = Gfx.canvas(1, 1);
    const c = cv.getContext('2d', { willReadFrequently: true });
    c.drawImage(p.src, p.sx + x, p.sy + y, 1, 1, 0, 0, 1, 1);
    const d = c.getImageData(0, 0, 1, 1).data;
    return rgb(d[0], d[1], d[2]);
}

/**
 * Один фон (з магазину): небо, шари гір/міста, кущів і землі, світило (сонце/місяць), свої кольори хмар і ефекти.
 * Розташування хмар -- спільне для всіх фонів (manifest.json)
 */
class Backdrop {
    constructor(a, spec, defaultClouds) {
        this.id = spec.id;
        this.price = spec.price;
        this.sky = a.image(spec.sky);
        this.skyTop = pixel(this.sky, Math.trunc(this.sky.width / 2), 0);    // -- ним небо продовжується вгору
        this.layers = {};
        for (const name of ['far', 'bushes', 'ground']) {
            const l = spec.layers[name];
            this.layers[name] = { image: a.image(l.file), y: l.y, factor: l.factor };
        }
        this.body = spec.body ? a.image(spec.body.file) : null;
        this.bodyX = spec.body?.x ?? 0;
        this.bodyY = spec.body?.y ?? 0;
        this.bodyThumbY = spec.body?.thumb_y ?? 0;
        this.clouds = spec.clouds ? spec.clouds.map((f) => a.image(f)) : defaultClouds;
        this.fx = (spec.fx || []).filter((n) => FX[n]);
    }
}

export class Scenery {
    // -- мініатюра фону в магазині: смуга сцени від неба над горизонтом до землі (у координатах поля)
    static THUMB_TOP = 360;
    static THUMB_H = 320;

    constructor(a, manifest, backdrops, screenW) {
        this.screenW = screenW;
        const defaultClouds = manifest.clouds.map((c) => a.image(c.file));
        this.cloudSpecs = manifest.clouds.map((c) => [c.x, c.y]);
        this.cloudSpeeds = manifest.clouds.map((c) => c.speed);
        this.themes = backdrops.map((b) => new Backdrop(a, b, defaultClouds));
        this.groundY = manifest.screen.ground_y;
        const first = this.themes[0];
        this.far = new ScrollLayer(first.layers.far);
        this.bushes = new ScrollLayer(first.layers.bushes);
        this.ground = new ScrollLayer(first.layers.ground);
        this.theme = first;
        this.sky = first.sky;
        this.speed = 60;
        this.t = 0;
        this.clouds = [];
        this.fx = [];
        this.thumbs = new Map();
        this.viewW = -1;
        this.setView(screenW, 0, 0, 0);
        this.setTheme(first.id);
    }

    /** змінює фон (шари їдуть далі з того ж місця); повертає id фону, який реально поставили */
    setTheme(themeId) {
        this.theme = this.byId(themeId) || this.themes[0];
        this.sky = this.theme.sky;
        this.far.set(this.theme.layers.far);
        this.bushes.set(this.theme.layers.bushes);
        this.ground.set(this.theme.layers.ground);
        this.fx = this.theme.fx.map((n) => FX[n](this.viewW, this.top));
        return this.theme.id;
    }

    byId(id) {
        return this.themes.find((t) => t.id === id);
    }

    /**
     * розмір полотна: ширина viewW (ігрове поле починається з ox), над полем ще top px неба; dy -- на скільки
     * фон нижче за поле гри (щоб земля була внизу екрана). Набір хмар повторюється кожні screenW пікселів
     */
    setView(viewW, ox, top, dy) {
        if (viewW === this.viewW && ox === this.ox && top === this.top && dy === this.dy) {
            return;
        }
        Object.assign(this, { viewW, ox, top, dy });
        const first = -Math.ceil(ox / this.screenW), last = Math.ceil((viewW - ox) / this.screenW);
        this.clouds = [];
        for (let k = first; k < last; k++) {
            this.cloudSpecs.forEach(([x, y], i) => {
                this.clouds.push(new Cloud(i, this.theme.clouds[i].width, x + ox + k * this.screenW, y,
                    this.cloudSpeeds[i], viewW));
            });
        }
        this.fx = this.theme.fx.map((n) => FX[n](viewW, top));
    }

    update(dt, targetSpeed, snap) {
        if (targetSpeed != null) {
            this.speed = snap ? targetSpeed : this.speed + (targetSpeed - this.speed) * Math.min(1, 4 * dt);
        }
        this.t += dt;
        for (const c of this.clouds) {
            c.update(dt);
        }
        this.far.update(this.speed, dt);
        this.bushes.update(this.speed, dt);
        this.ground.update(this.speed, dt);
        for (const f of this.fx) {
            f.update(dt, this.speed);
        }
    }

    /** світило, хмари, гори/місто, кущі і ефекти -- усе, що позаду труб (небо вже намальоване) */
    drawScene(c, th, ox, clouds, fx, t, thumb, width) {
        for (const f of fx) {
            if (f.sky()) {
                f.draw(c, t);
            }
        }
        if (th.body) {
            Gfx.blit(c, th.body, ox + th.bodyX, thumb ? th.bodyThumbY : th.bodyY);
        }
        for (const cl of clouds) {
            cl.draw(c, th.clouds[cl.idx]);
        }
        this.far.draw(c, width);
        this.bushes.draw(c, width);
        for (const f of fx) {
            if (!f.sky()) {
                f.draw(c, t);
            }
        }
    }

    /** небо і все, що позаду труб. Canvas -- у координатах ігрового поля */
    drawBack(c) {
        c.save();
        c.translate(-this.ox, this.dy);
        if (this.top > 0) {
            Gfx.fill(c, this.theme.skyTop, 0, -this.top, this.viewW, this.top + 1);
        }
        Gfx.blitTo(c, this.sky, 0, 0, this.viewW, this.sky.height, false);
        this.drawScene(c, this.theme, this.ox, this.clouds, this.fx, this.t, false, this.viewW);
        c.restore();
    }

    /** земля -- по нижньому краю екрана */
    drawGround(c) {
        c.save();
        c.translate(-this.ox, this.dy);
        this.ground.draw(c, this.viewW);
        c.restore();
    }

    /** мініатюра фону для картки магазину (малюється один раз; удвічі більша за рамку -- для чіткості) */
    thumbnail(themeId, tw, th) {
        const key = themeId + ':' + tw + 'x' + th;
        const cached = this.thumbs.get(key);
        if (cached) {
            return cached;
        }
        const theme = this.byId(themeId);
        const w = Math.round(Scenery.THUMB_H * tw / th);
        const ox = Math.trunc((w - this.screenW) / 2);
        const h = this.sky.height;
        const cv = Gfx.canvas(w, h);
        const c = cv.getContext('2d');
        Gfx.blitTo(c, theme.sky, 0, 0, w, h, false);
        const cl = this.cloudSpecs.map(([x, y], i) => new Cloud(i, 0, x + ox, y, 0, w));
        // -- шари цього фону на час малювання, з нульовим зсувом
        const ls = [this.far, this.bushes, this.ground], names = ['far', 'bushes', 'ground'];
        const saved = ls.map((l) => ({ image: l.image, y: l.y, factor: l.factor, offset: l.offset }));
        ls.forEach((l, i) => {
            l.set(theme.layers[names[i]]);
            l.offset = 0;
        });
        this.drawScene(c, theme, ox, cl, theme.fx.map((n) => FX[n](w, 0)), 0, true, w);
        this.ground.draw(c, w);
        ls.forEach((l, i) => {
            l.set(saved[i]);
            l.offset = saved[i].offset;
        });
        const out = Gfx.canvas(tw * 2, th * 2);
        const o = out.getContext('2d');
        o.imageSmoothingEnabled = true;
        o.drawImage(cv, 0, Scenery.THUMB_TOP, w, Scenery.THUMB_H, 0, 0, tw * 2, th * 2);
        const pic = new Pic(out);
        this.thumbs.set(key, pic);
        return pic;
    }
}
