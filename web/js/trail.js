// -- шлейф за пташкою: напівпрозора смуга по точках, де пташка вже пролетіла (Trail.java).
// -- Точки -- від голови (k=0, біля пташки) до хвоста (k=1, майже зник); seed 0..1 -- випадкове число точки
import * as Gfx from './gfx.js';
import { rgb, lerp, css } from './gfx.js';

/** точки шлейфу для малювання: x, y, k (0 -- голова, 1 -- хвіст), seed */
export class Points {
    constructor() {
        this.x = [];
        this.y = [];
        this.k = [];
        this.seed = [];
        this.nx = [];
        this.ny = [];
        this.n = 0;
    }

    clear() {
        this.n = 0;
    }

    add(px, py, pk, ps) {
        const i = this.n++;
        this.x[i] = px;
        this.y[i] = py;
        this.k[i] = pk;
        this.seed[i] = ps;
    }

    /** для кожної точки -- одиничний вектор поперек шлейфу (щоб товщина не залежала від нахилу) */
    normals() {
        for (let i = 0; i < this.n; i++) {
            const a = Math.max(0, i - 1), b = Math.min(this.n - 1, i + 1);
            const dx = this.x[a] - this.x[b], dy = this.y[a] - this.y[b];
            const len = Math.hypot(dx, dy) || 1;
            this.nx[i] = -dy / len;
            this.ny[i] = dx / len;
        }
    }
}

// -- шлейфи в порядку магазину: (id, ціна). "none" -- без шлейфу, є в усіх; "custom" -- свій
export const TRAIL_IDS = ['none', 'neon', 'rainbow', 'custom'];
export const TRAIL_PRICES = [0, 150, 250, 500];
const RAINBOW = [rgb(255, 72, 72), rgb(255, 160, 48), rgb(255, 228, 64), rgb(96, 216, 88), rgb(72, 160, 255),
    rgb(164, 100, 240)];

// -- палітра свого шлейфу (у редакторі -- 2 ряди по 8) і стилі (у порядку перемикача)
export const PALETTE = [
    rgb(255, 64, 64), rgb(255, 140, 40), rgb(255, 222, 60), rgb(150, 230, 60),
    rgb(50, 200, 90), rgb(50, 220, 220), rgb(70, 150, 255), rgb(64, 72, 230),
    rgb(150, 80, 245), rgb(230, 70, 220), rgb(255, 120, 180), rgb(255, 255, 255),
    rgb(255, 200, 130), rgb(150, 100, 60), rgb(140, 140, 160), rgb(40, 30, 50),
];
export const STYLES = ['ribbon', 'glow', 'bubbles', 'pixels', 'sparks'];
const WHITE = 0xFFFFFF;

const RAINBOW_BAND = 3;                   // -- px, товщина однієї смуги веселки
const NEON_GLOW = 22, NEON_CORE = 8;      // -- px, ширина світіння і яскравої серединки
const NEON_FROM = rgb(255, 50, 190), NEON_TO = rgb(120, 50, 255);

export const mod = (a, n) => ((a % n) + n) % n;

/** чотирикутник між сусідніми точками a і b: (oa0, oa1) / (ob0, ob1) -- від і до зсуву поперек шлейфу */
function band(c, p, a, b, oa0, oa1, ob0, ob1, style) {
    Gfx.quad(c, style,
        p.x[a] + p.nx[a] * oa0, p.y[a] + p.ny[a] * oa0,
        p.x[b] + p.nx[b] * ob0, p.y[b] + p.ny[b] * ob0,
        p.x[b] + p.nx[b] * ob1, p.y[b] + p.ny[b] * ob1,
        p.x[a] + p.nx[a] * oa1, p.y[a] + p.ny[a] * oa1);
}

function rainbow(c, p) {
    const n = RAINBOW.length;
    for (let i = 0; i + 1 < p.n; i++) {
        const ha = RAINBOW_BAND * (1 - 0.35 * p.k[i]);         // -- до хвоста трохи тоншає
        const hb = RAINBOW_BAND * (1 - 0.35 * p.k[i + 1]);
        const alpha = Math.trunc(210 * Math.pow(1 - p.k[i], 0.7));
        for (let j = 0; j < n; j++) {
            const o = j - n / 2;
            band(c, p, i, i + 1, o * ha, (o + 1) * ha, o * hb, (o + 1) * hb, css(RAINBOW[j], alpha));
        }
    }
}

/** неон: широке напівпрозоре світіння, яскрава серединка і іскорки поруч */
function glow(c, p, t, cFrom, cTo, glowW, core) {
    for (const [width, alpha, light] of [[glowW, 150, 0], [core, 255, 0.5]]) {
        for (let i = 0; i + 1 < p.n; i++) {
            const color = lerp(lerp(cFrom, cTo, p.k[i]), WHITE, light);
            const wa = width * (1 - 0.6 * p.k[i]) / 2, wb = width * (1 - 0.6 * p.k[i + 1]) / 2;
            band(c, p, i, i + 1, -wa, wa, -wb, wb, css(color, Math.trunc(alpha * Math.pow(1 - p.k[i], 0.7))));
        }
    }
    // -- іскорки: маленькі хрестики, що мерехтять поруч зі смугою
    for (let i = 0; i < p.n; i++) {
        const seed = p.seed[i], k = p.k[i];
        if (seed > 0.14 || k < 0.12) {
            continue;
        }
        const r = Math.sin(t * 18 + seed * 90) > 0 ? 2 : 1;
        const a = Math.trunc(255 * (1 - k));
        const off = (seed - 0.07) * 160 * glowW / NEON_GLOW;
        const x = Math.trunc(p.x[i] + p.nx[i] * off), y = Math.trunc(p.y[i] + p.ny[i] * off);
        Gfx.fill(c, WHITE, x - r, y, 2 * r + 1, 1, a);
        Gfx.fill(c, WHITE, x, y - r, 1, 2 * r + 1, a);
    }
}

export class Trail {
    constructor(id, price) {
        this.id = id;
        this.price = price;
    }

    draw(c, p, t) {
        if (this.id === 'none' || p.n < 2) {
            return;
        }
        p.normals();
        this.paint(c, p, t);
    }

    paint(c, p, t) {
        if (this.id === 'rainbow') {
            rainbow(c, p);
        } else {
            glow(c, p, t, NEON_FROM, NEON_TO, NEON_GLOW, NEON_CORE);
        }
    }
}

/**
 * Свій шлейф: колір біля пташки (c1) переходить у колір хвоста (c2), стиль -- з STYLES, товщина 0..1.
 * Усе це -- в config: гра підставляє сюди налаштування зі збереження, і редактор міняє їх на льоту
 */
export class CustomTrail extends Trail {
    static MIN_W = 6;
    static MAX_W = 30;     // -- px, товщина шлейфу при повзунку на 0 і на 100%

    constructor(price) {
        super('custom', price);
        this.config = { c1: 9, c2: 6, style: 'glow', width: 0.5 };
    }

    width() {
        return CustomTrail.MIN_W + (CustomTrail.MAX_W - CustomTrail.MIN_W) * this.config.width;
    }

    paint(c, p, t) {
        const c1 = PALETTE[mod(this.config.c1, PALETTE.length)], c2 = PALETTE[mod(this.config.c2, PALETTE.length)];
        const w = this.width();
        switch (this.config.style) {
            case 'glow':
                glow(c, p, t, c1, c2, w * 1.25, w * 0.45);
                break;
            case 'bubbles':
                bubbles(c, p, c1, c2, w);
                break;
            case 'pixels':
                pixels(c, p, c1, c2, w);
                break;
            case 'sparks':
                sparks(c, p, t, c1, c2, w);
                break;
            default:
                ribbon(c, p, c1, c2, w);
        }
    }
}

/** суцільна стрічка, до хвоста тоншає; уздовж верхнього краю -- світла смужка-блік */
function ribbon(c, p, c1, c2, w) {
    for (let i = 0; i + 1 < p.n; i++) {
        const color = lerp(c1, c2, p.k[i]);
        const alpha = Math.trunc(250 * Math.pow(1 - p.k[i], 0.55));
        const wa = w * (1 - 0.5 * p.k[i]) / 2, wb = w * (1 - 0.5 * p.k[i + 1]) / 2;
        band(c, p, i, i + 1, -wa, wa, -wb, wb, css(color, alpha));
        band(c, p, i, i + 1, -wa * 0.7, -wa * 0.2, -wb * 0.7, -wb * 0.2, css(lerp(color, WHITE, 0.45), alpha));
    }
}

/** бульбашки: з'являються біля пташки маленькими, ростуть, розлітаються і зникають */
function bubbles(c, p, c1, c2, w) {
    for (let i = p.n - 1; i >= 0; i--) {          // -- старі (великі) знизу, нові зверху
        const seed = p.seed[i], k = p.k[i];
        if (seed > 0.2) {
            continue;
        }
        const r = Math.max(2, Math.round(w * (0.22 + 0.4 * k)));
        const cy = Math.round(p.y[i] + (seed / 0.2 - 0.5) * w * 1.2 * k);
        const color = lerp(c1, c2, k);
        const alpha = Math.trunc(250 * Math.sqrt(1 - k));
        const cx = Math.round(p.x[i]);
        Gfx.circle(c, color, cx, cy, r, alpha >> 1);
        Gfx.ring(c, lerp(color, WHITE, 0.15), cx, cy, r, Math.max(2, Math.trunc(r / 4)), alpha);
        Gfx.fill(c, WHITE, cx - Math.trunc(r / 2), cy - Math.trunc(r / 2), 2, 2, alpha);
    }
}

/** 8-бітні «пікселі»: квадратики по сітці, розлітаються і зменшуються до хвоста */
function pixels(c, p, c1, c2, w) {
    const s = Math.max(4, Math.trunc(Math.round(w / 3) / 2) * 2);
    for (let i = 0; i < p.n; i++) {
        const seed = p.seed[i], k = p.k[i];
        if (seed > 0.6) {
            continue;
        }
        const size = Math.max(2, Math.trunc(Math.round(s * (1 - 0.6 * k)) / 2) * 2);
        const off = (seed / 0.6 - 0.5) * w * (0.5 + 0.9 * k);
        const color = seed < 0.2 ? c1 : seed > 0.45 ? c2 : lerp(c1, c2, k);
        Gfx.fill(c, color, Math.floor(p.x[i] / 2) * 2 - (size >> 1), Math.floor((p.y[i] + off) / 2) * 2 - (size >> 1),
            size, size, Math.trunc(255 * Math.pow(1 - k, 0.4)));
    }
}

/** тонка яскрава нитка і зірочки навколо неї, що мерехтять */
function sparks(c, p, t, c1, c2, w) {
    const core = Math.max(3, w * 0.22);
    for (let i = 0; i + 1 < p.n; i++) {
        const color = lerp(lerp(c1, c2, p.k[i]), WHITE, 0.3);
        const wa = core * (1 - 0.5 * p.k[i]) / 2, wb = core * (1 - 0.5 * p.k[i + 1]) / 2;
        band(c, p, i, i + 1, -wa, wa, -wb, wb, css(color, Math.trunc(230 * Math.pow(1 - p.k[i], 0.7))));
    }
    for (let i = 0; i < p.n; i++) {
        const seed = p.seed[i], k = p.k[i];
        if (seed > 0.32 || k < 0.05) {
            continue;
        }
        let r = Math.max(1, Math.round(w / 6 * (1 - k) * (0.6 + seed)));
        if (Math.sin(t * 16 + seed * 70) < -0.4) {
            r = Math.max(1, r - 1);
        }
        const th = r >= 3 ? 2 : 1;                     // -- великі зірочки -- з товстішими променями
        const off = (seed / 0.32 - 0.5) * w * 1.4;
        const x = Math.trunc(p.x[i] + p.nx[i] * off), y = Math.trunc(p.y[i] + p.ny[i] * off);
        const alpha = Math.trunc(255 * Math.pow(1 - k, 0.6));
        const color = seed < 0.16 ? c1 : c2;
        Gfx.fill(c, color, x - r, y, 2 * r + th, th, alpha);
        Gfx.fill(c, color, x, y - r, th, 2 * r + th, alpha);
        Gfx.fill(c, WHITE, x, y, th, th, alpha);
    }
}
