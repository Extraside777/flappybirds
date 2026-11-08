// -- усі спрайти гри (assets/sprites + manifest.json + extra.json) -- як SpriteKit.java / src/sprites.py
import * as Gfx from './gfx.js';
import { Pic } from './gfx.js';
import { Scenery } from './scenery.js';
import { Trail, CustomTrail, TRAIL_IDS, TRAIL_PRICES } from './trail.js';

/** читання assets/sprites: json-описи і картинки (усі вантажаться наперед, потім видаються миттєво) */
export class Assets {
    constructor(dir) {
        this.dir = dir.endsWith('/') ? dir : dir + '/';
        this.images = new Map();
    }

    async json(rel) {
        const r = await fetch(this.dir + rel);
        if (!r.ok) {
            throw new Error('нема ' + this.dir + rel);
        }
        return r.json();
    }

    /** завантажити всі картинки, згадані в json-описах (будь-який рядок, що закінчується на .png / .webp) */
    async preload(...specs) {
        const files = new Set();
        const walk = (v) => {
            if (typeof v === 'string') {
                if (/\.(png|webp)$/i.test(v)) {
                    files.add(v);
                }
            } else if (v && typeof v === 'object') {
                Object.values(v).forEach(walk);
            }
        };
        specs.forEach(walk);
        await Promise.all([...files].map((rel) => new Promise((ok, fail) => {
            const img = new Image();
            img.onload = () => {
                this.images.set(rel, new Pic(img));
                ok();
            };
            img.onerror = () => fail(new Error('нема картинки ' + this.dir + rel));
            img.src = this.dir + rel;
        })));
    }

    image(rel) {
        const p = this.images.get(rel);
        if (!p) {
            throw new Error('картинку не завантажено: ' + rel);
        }
        return p;
    }
}

/** кадри з горизонтальної смуги (sheet); pause -- скільки секунд стоїть перший кадр між повторами */
export class Animation {
    constructor(sheet, count, fps, pause = 0, start = 0) {
        const fw = Math.trunc(sheet.width / count), fh = sheet.height;
        this.frames = [];
        for (let i = 0; i < count; i++) {
            this.frames.push(new Pic(sheet.src, sheet.sx + i * fw, sheet.sy, fw, fh));
        }
        this.fps = fps;
        this.pause = pause;
        this.playTime = count / fps;
        this.t = start % (this.playTime + pause);
    }

    update(dt) {
        this.t = (this.t + dt) % (this.playTime + this.pause);
    }

    frame() {
        if (this.t >= this.playTime) {
            return this.frames[0];
        }
        return this.frames[Math.min(Math.trunc(this.t * this.fps), this.frames.length - 1)];
    }
}

/**
 * Розтягує картинку-панель під будь-який розмір, не чіпаючи кути.
 * Середина по вертикалі -- один рядок з центру (інакше градієнт панелі розтягується смугами)
 */
export class NineSlice {
    constructor(src, border) {
        this.b = border;
        const iw = src.width, ih = src.height;
        const cv = Gfx.canvas(iw, 2 * border + 1);
        const c = cv.getContext('2d');
        Gfx.blitArea(c, src, 0, 0, iw, border, 0, 0);
        Gfx.blitArea(c, src, 0, Math.trunc(ih / 2), iw, 1, 0, border);
        Gfx.blitArea(c, src, 0, ih - border, iw, border, 0, border + 1);
        this.image = new Pic(cv);
        this.cache = new Map();
    }

    render(w, h) {
        const key = w + 'x' + h;
        let out = this.cache.get(key);
        if (out) {
            return out;
        }
        const img = this.image, b = this.b;
        const iw = img.width, ih = img.height;
        const cv = Gfx.canvas(w, h);
        const c = cv.getContext('2d');
        const xs = [[0, b, 0, b], [b, iw - b, b, w - b], [iw - b, iw, w - b, w]];
        const ys = [[0, b, 0, b], [b, ih - b, b, h - b], [ih - b, ih, h - b, h]];
        for (const x of xs) {
            for (const y of ys) {
                if (x[3] > x[2] && y[3] > y[2]) {
                    Gfx.blitAreaTo(c, img, x[0], y[0], x[1] - x[0], y[1] - y[0], x[2], y[2], x[3] - x[2], y[3] - y[2]);
                }
            }
        }
        out = new Pic(cv);
        this.cache.set(key, out);
        return out;
    }
}

/**
 * Пташка (скін): махає крилами і нахиляється залежно від швидкості.
 * (ax, ay) -- де в кадрі центр тіла; саме ця точка ставиться в центр хітбокса
 */
export class BirdArt {
    constructor(a, spec) {
        this.id = spec.id;
        this.price = spec.price;
        this.anim = new Animation(a.image(spec.file), spec.frames, spec.fps);
        this.w = spec.fw;
        this.h = spec.fh;
        this.ax = spec.ax ?? this.w / 2;
        this.ay = spec.ay ?? this.h / 2;
        this.artPx = spec.art_px ?? 0;      // -- піксель-арт: розмір художнього пікселя (0 -- звичайна картинка)
    }

    update(dt, flapSpeed) {
        this.anim.update(dt * flapSpeed);
    }

    /** центр тіла -- в (cx, cy); кут -- в градусах, плюс -- дзьоб вгору */
    draw(c, cx, cy, angle, frame = -1) {
        const img = frame < 0 ? this.anim.frame() : this.anim.frames[frame % this.anim.frames.length];
        if (Math.abs(angle) > 0.5) {
            c.save();
            c.translate(cx, cy);
            c.rotate(-angle * Math.PI / 180);
            Gfx.blit(c, img, -this.ax, -this.ay);
            c.restore();
        } else {
            Gfx.blit(c, img, Math.trunc(cx - this.ax), Math.trunc(cy - this.ay));
        }
    }
}

/**
 * Труба зі спрайтів (скін з магазину): тіло повторюється по вертикалі, зверху/знизу капелюшок.
 * mini -- зменшена копія для картки магазину (кожен художній піксель стає одним, тому чітко)
 */
export class PipeArt {
    constructor(a, spec, scale = 1) {
        this.id = spec.id;
        this.price = spec.price;
        const img = (f) => {
            const im = a.image(f);
            return scale === 1 ? im : Gfx.scaled(im, Math.max(1, Math.round(im.width * scale)),
                Math.max(1, Math.round(im.height * scale)));
        };
        this.body = img(spec.body);
        this.neck = img(spec.neck);
        this.cap = img(spec.cap);
        this.capFlip = Gfx.flipV(this.cap);
        this.neckFlip = Gfx.flipV(this.neck);
        this.bodyW = Math.round(spec.body_w * scale);
        this.capW = Math.round(spec.cap_w * scale);
        this.capH = Math.round(spec.cap_h * scale);
        this.mini = scale === 1 ? new PipeArt(a, spec, 1 / spec.art_px) : this;
    }

    /** тіло труби від y0 до y1 */
    column(c, x, y0, y1) {
        const th = this.body.height;
        for (let y = y0; y < y1;) {
            const h = Math.min(th, y1 - y);
            Gfx.blitArea(c, this.body, 0, 0, this.bodyW, h, x, y);
            y += h;
        }
    }

    /** x, width -- хітбокс труби; gapY..gapY+gap -- прохід; bottom -- де закінчується нижня труба, top -- звідки верхня */
    draw(c, x, width, gapY, gap, bottom, top) {
        const cx = x + Math.trunc((width - this.capW) / 2);
        const bx = x + Math.trunc((width - this.bodyW) / 2);
        // -- верхня труба (капелюшок знизу)
        const topCap = gapY - this.capH;
        this.column(c, bx, top, topCap);
        Gfx.blit(c, this.neckFlip, bx, topCap - this.neck.height);
        Gfx.blit(c, this.capFlip, cx, topCap);
        // -- нижня труба
        const low = gapY + gap;
        this.column(c, bx, low + this.capH, bottom);
        Gfx.blit(c, this.neck, bx, low + this.capH);
        Gfx.blit(c, this.cap, cx, low);
    }
}

// -- заголовок FLAPPY BIRD, що підстрибує, і анімовані кнопки-спрайти (Ui.java)
export class TitleLine {
    static CYCLE = 1.7;
    static HOP = 0.75;
    static LAND = 0.18;

    constructor(image, x, y, delay, amp) {
        Object.assign(this, { image, x, y, delay, amp });
    }

    draw(c, t) {
        let cyc = (t - this.delay) % TitleLine.CYCLE;
        if (cyc < 0) {
            cyc += TitleLine.CYCLE;
        }
        let dy = 0, squash = 0;
        if (cyc < TitleLine.HOP) {
            const u = cyc / TitleLine.HOP;
            dy = -this.amp * 4 * u * (1 - u);
        } else if (cyc < TitleLine.HOP + TitleLine.LAND) {
            squash = 0.10 * Math.sin(Math.PI * (cyc - TitleLine.HOP) / TitleLine.LAND);
        }
        const w = this.image.width, h = this.image.height;
        let px = this.x, py = this.y + Math.round(dy);
        if (squash > 0.005) {
            const nw = Math.trunc(w * (1 + squash * 0.5)), nh = Math.trunc(h * (1 - squash));
            px -= Math.trunc((nw - w) / 2);
            py += h - nh;
            Gfx.blitTo(c, this.image, px, py, nw, nh, true);
        } else {
            Gfx.blit(c, this.image, px, py);
        }
    }
}

export class Title {
    constructor(lines) {
        this.lines = lines;
    }

    draw(c, t) {
        for (let i = this.lines.length - 1; i >= 0; i--) {
            this.lines[i].draw(c, t);
        }
    }
}

/** обличчя кнопки: картинка з бліком, що пробігає */
export class ShineFace {
    constructor(anim) {
        this.anim = anim;
    }

    width() {
        return this.anim.frames[0].width;
    }

    height() {
        return this.anim.frames[0].height;
    }

    update(dt) {
        this.anim.update(dt);
    }

    setSpeed() {
    }

    image() {
        return this.anim.frame();
    }
}

/** обличчя кнопки налаштувань: основа і шестерня, що крутиться (кадри складаються один раз) */
export class GearFace {
    constructor(base, gear, ox, oy) {
        this.base = base;
        this.gear = gear;
        this.speed = 1;
        this.frames = gear.frames.map((f) => {
            const cv = Gfx.canvas(base.width, base.height);
            const c = cv.getContext('2d');
            Gfx.blit(c, base, 0, 0);
            Gfx.blit(c, f, ox, oy);
            return new Pic(cv);
        });
    }

    width() {
        return this.base.width;
    }

    height() {
        return this.base.height;
    }

    update(dt) {
        this.gear.update(dt * this.speed);
    }

    setSpeed(s) {
        this.speed = s;
    }

    image() {
        return this.frames[this.gear.frames.indexOf(this.gear.frame())];
    }
}

export class SpriteButton {
    static BOB_SPEED = 2.4;
    static OFF_DIM = 0.72;     // -- вимкнена кнопка (зараз не спрацює) темніша

    constructor(face, x, y, bobPhase, bobAmp, dark) {
        Object.assign(this, { face, x, y, bobPhase, bobAmp, dark });
        this.hover = 0;
        this.press = 0;
        this.off = false;
    }

    update(dt, hovered, press) {
        this.hover += ((hovered ? 1 : 0) - this.hover) * Math.min(1, 12 * dt);
        this.press = press;
        this.face.setSpeed(1 + 1.5 * this.hover + 7 * press);
        this.face.update(dt);
    }

    draw(c, t, px = this.x, py = this.y) {
        const w = this.face.width(), h = this.face.height();
        py += Math.round(Math.sin(t * SpriteButton.BOB_SPEED + this.bobPhase) * this.bobAmp);
        let img = this.face.image();
        const m = (1 - this.dark * this.press) * (this.off ? SpriteButton.OFF_DIM : 1);
        if (m < 0.999) {
            img = Gfx.darkened(img, m);
        }
        const s = 1 + 0.03 * this.hover - 0.06 * this.press;
        if (Math.abs(s - 1) > 0.004) {
            const nw = Math.trunc(w * s), nh = Math.trunc(h * s);
            Gfx.blitTo(c, img, px + Math.trunc((w - nw) / 2), py + Math.trunc((h - nh) / 2), nw, nh, true);
        } else {
            Gfx.blit(c, img, px, py);
        }
    }
}

export const LANGS = ['en', 'uk'];

export class SpriteKit {
    /** м -- manifest.json, ex -- extra.json (картинки з них уже завантажені в a) */
    constructor(a, m, ex, pressDark) {
        const screenW = m.screen.w;
        this.groundY = m.screen.ground_y;
        // -- фони в порядку магазину (перший -- звичайний «день»); scenery малює обраний
        this.scenery = new Scenery(a, m, ex.backgrounds, screenW);
        this.backgrounds = this.scenery.themes;

        // -- заголовок FLAPPY BIRD -- назва, не перекладаємо
        this.title = new Title(m.title.map((ln, i) => new TitleLine(a.image(ln.file), ln.x, ln.y, 0.22 * i, 15 - 3 * i)));

        // -- все, що залежить від мови: кнопки і тексти
        const names = ['play', 'shop', 'menu', 'record', 'done'];
        const starts = [0, 1.6, 0, 0.8, 0];
        this.faces = {};
        for (const lang of LANGS) {
            this.faces[lang] = {};
            names.forEach((n, i) => {
                const b = ex.buttons[lang][n];
                this.faces[lang][n] = new ShineFace(new Animation(a.image(b.file), b.frames, b.fps, b.pause, starts[i]));
            });
        }
        this.texts = {};
        for (const [lang, items] of Object.entries(ex.texts)) {
            this.texts[lang] = {};
            for (const [key, file] of Object.entries(items)) {
                this.texts[lang][key] = a.image(file);
            }
        }
        this.langNames = {};
        for (const lang of LANGS) {
            this.langNames[lang] = a.image(ex.lang_names[lang]);
        }
        // -- цифри: "dark" -- на кремовій панелі, "light" -- білі з контуром, "big" -- для рекорду, "title" -- золоті
        this.digits = {};
        for (const [style, key] of [['dark', 'digits'], ['light', 'digits_light'], ['big', 'digits_big'], ['title', 'digits_title']]) {
            this.digits[style] = {};
            for (const [ch, file] of Object.entries(ex[key])) {
                this.digits[style][ch] = a.image(file);
            }
        }
        this.trophySmall = a.image(ex.trophy.small);
        this.trophyBig = a.image(ex.trophy.big);

        const bp = ex.buttons.en, en = this.faces.en;
        this.play = new SpriteButton(en.play, bp.play.x, bp.play.y, 0, 2, pressDark);
        this.shop = new SpriteButton(en.shop, bp.shop.x, bp.shop.y, 1.3, 2, pressDark);
        this.menu = new SpriteButton(en.menu, 0, 0, 0.6, 1.5, pressDark);
        this.done = new SpriteButton(en.done, 0, 0, 0.6, 1.5, pressDark);
        this.record = new SpriteButton(en.record, bp.record.x, bp.record.y, 2.6, 2, pressDark);

        const st = m.settings, g = st.gear;
        const gear = new Animation(a.image(g.file), g.frames, g.fps);
        this.settings = new SpriteButton(new GearFace(a.image(st.base), gear, g.ox, g.oy), st.x, st.y, 0, 0, pressDark);
        // -- «монети за рекламу» під лічильником монет: слів на кнопці нема, тож одна на обидві мови
        const ab = ex.ad;
        this.ad = new SpriteButton(new ShineFace(new Animation(a.image(ab.file), ab.frames, ab.fps, ab.pause, 2.4)),
            ab.x, ab.y, 0, 0, pressDark);

        // -- скіни труб і пташок у порядку магазину; pipe / bird -- ті, що в грі
        this.pipes = ex.pipes.map((s) => new PipeArt(a, s));
        this.pipe = this.pipes[0];
        this.skins = ex.skins.map((s) => new BirdArt(a, s));
        this.bird = this.skins[0];
        this.panel = new NineSlice(a.image(ex.panel.file), ex.panel.slice);

        this.coin = new Animation(a.image(ex.coin.file), ex.coin.frames, ex.coin.fps);
        this.coinIcon = this.coin.frames[0];

        // -- бонуси (іконки в бульбашках) і бульбашка щита навколо пташки
        const anim = (s) => new Animation(a.image(s.file), s.frames, s.fps, s.pause, 0);
        this.powerups = {};
        for (const kind of ['shield', 'slow', 'x2']) {
            this.powerups[kind] = anim(ex.powerups[kind]);
        }
        this.aura = anim(ex.powerups.aura);

        // -- шлейфи за пташкою (малюються кодом, без картинок); trail -- обраний
        this.trails = TRAIL_IDS.map((id, i) => id === 'custom' ? new CustomTrail(TRAIL_PRICES[i]) : new Trail(id, TRAIL_PRICES[i]));
        this.trail = this.trails[0];
        this.customTrail = this.trails.find((t) => t.id === 'custom');
        this.lang = 'en';
    }

    setLang(l) {
        this.lang = LANGS.includes(l) ? l : 'en';
        const f = this.faces[this.lang];
        this.play.face = f.play;
        this.shop.face = f.shop;
        this.menu.face = f.menu;
        this.record.face = f.record;
        this.done.face = f.done;
    }

    setSkin(id) {
        this.bird = this.skins.find((b) => b.id === id) || this.skins[0];
        return this.bird.id;
    }

    setTrail(id) {
        this.trail = this.trails.find((t) => t.id === id) || this.trails[0];
        return this.trail.id;
    }

    setBackground(id) {
        return this.scenery.setTheme(id);
    }

    setPipe(id) {
        this.pipe = this.pipes.find((p) => p.id === id) || this.pipes[0];
        return this.pipe.id;
    }

    text(key) {
        return this.texts[this.lang][key];
    }

    digitHeight(style) {
        return Math.max(...Object.values(this.digits[style]).map((b) => b.height));
    }

    numberWidth(text, style = 'light', gap = 2) {
        const d = this.digits[style];
        let w = 0, n = 0;
        for (const ch of text) {
            const b = d[ch];
            if (b) {
                w += b.width;
                n++;
            }
        }
        return w + gap * Math.max(0, n - 1);
    }

    /**
     * число зі спрайтів-цифр по вертикальному центру cy. align: 0 -- x це центр, -1 -- лівий край, 1 -- правий
     */
    drawNumber(c, text, x, cy, style = 'light', align = 0, gap = 2, alpha = 255) {
        const d = this.digits[style];
        const w = this.numberWidth(text, style, gap);
        if (w === 0) {
            return;
        }
        let px = Math.trunc(x);
        if (align === 0) {
            px -= Math.trunc(w / 2);
        } else if (align > 0) {
            px -= w;
        }
        for (const ch of text) {
            const b = d[ch];
            if (!b) {
                continue;
            }
            Gfx.blit(c, b, px, Math.trunc(cy) - Math.trunc(b.height / 2), alpha);
            px += b.width + gap;
        }
    }
}
