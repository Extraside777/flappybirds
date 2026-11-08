// -- малювання в стилі pygame / android/.../Gfx.java: картинки, прямокутники, многокутники на Canvas 2D.
// -- Піксель-арт -- без згладжування (чіткі пікселі), фігури -- зі згладжуванням.
// -- Колір -- число 0xRRGGBB (як Gfx.rgb у Java), прозорість передається окремо (0..255)

/** прямокутник як pygame.Rect / Box.java: x, y, ширина, висота -- у пікселях ігрового поля 400x700 */
export class Box {
    constructor(x, y, w, h) {
        this.x = x;
        this.y = y;
        this.w = w;
        this.h = h;
    }

    /** прямокутник ширини w і висоти h, у якого середина верхнього краю -- (cx, top) */
    static midTop(w, h, cx, top) {
        return new Box(cx - Math.trunc(w / 2), top, w, h);
    }

    right() {
        return this.x + this.w;
    }

    bottom() {
        return this.y + this.h;
    }

    centerX() {
        return this.x + Math.trunc(this.w / 2);
    }

    centerY() {
        return this.y + Math.trunc(this.h / 2);
    }

    inflate(dx, dy) {
        return new Box(this.x - Math.trunc(dx / 2), this.y - Math.trunc(dy / 2), this.w + dx, this.h + dy);
    }

    move(dx, dy) {
        return new Box(this.x + dx, this.y + dy, this.w, this.h);
    }

    contains(px, py) {
        return px >= this.x && px < this.x + this.w && py >= this.y && py < this.y + this.h;
    }

    overlaps(o) {
        return this.x < o.x + o.w && this.x + this.w > o.x && this.y < o.y + o.h && this.y + this.h > o.y;
    }

    /** спільна частина двох прямокутників */
    clip(o) {
        const l = Math.max(this.x, o.x), t = Math.max(this.y, o.y);
        const r = Math.min(this.right(), o.right()), b = Math.min(this.bottom(), o.bottom());
        return new Box(l, t, Math.max(0, r - l), Math.max(0, b - t));
    }
}

/**
 * Картинка або її частина (кадр зі смуги): src -- Image / Canvas, (sx, sy, w, h) -- яка частина.
 * Так кадри анімацій не копіюються, а малюються прямо з листа
 */
export class Pic {
    constructor(src, sx = 0, sy = 0, w = src.width, h = src.height) {
        this.src = src;
        this.sx = sx;
        this.sy = sy;
        this.width = w;
        this.height = h;
    }
}

export const rgb = (r, g, b) => ((r & 255) << 16) | ((g & 255) << 8) | (b & 255);
const R = (c) => (c >> 16) & 255, G = (c) => (c >> 8) & 255, B = (c) => c & 255;

/** колір між c0 і c1 (k від 0 до 1) */
export function lerp(c0, c1, k) {
    return rgb(Math.round(R(c0) + (R(c1) - R(c0)) * k), Math.round(G(c0) + (G(c1) - G(c0)) * k),
        Math.round(B(c0) + (B(c1) - B(c0)) * k));
}

export function css(c, alpha = 255) {
    const a = Math.max(0, Math.min(255, alpha));
    return a >= 255 ? `rgb(${R(c)},${G(c)},${B(c)})` : `rgba(${R(c)},${G(c)},${B(c)},${a / 255})`;
}

/** нове полотно w x h і його контекст (для картинок, що гра малює сама) */
export function canvas(w, h) {
    const cv = document.createElement('canvas');
    cv.width = Math.max(1, Math.round(w));
    cv.height = Math.max(1, Math.round(h));
    return cv;
}

// -- картинки
function draw(c, p, x, y, w, h, alpha, smooth) {
    c.imageSmoothingEnabled = smooth;
    c.globalAlpha = Math.max(0, Math.min(255, alpha)) / 255;
    c.drawImage(p.src, p.sx, p.sy, p.width, p.height, x, y, w, h);
    c.globalAlpha = 1;
}

export function blit(c, p, x, y, alpha = 255) {
    if (alpha > 0) {
        draw(c, p, x, y, p.width, p.height, alpha, false);
    }
}

/** частина картинки (sx, sy, w, h) -- як blit з area у pygame */
export function blitArea(c, p, sx, sy, w, h, x, y) {
    if (w <= 0 || h <= 0) {
        return;
    }
    c.imageSmoothingEnabled = false;
    c.drawImage(p.src, p.sx + sx, p.sy + sy, w, h, x, y, w, h);
}

export function blitCenter(c, p, cx, cy, alpha = 255) {
    blit(c, p, Math.trunc(cx) - Math.trunc(p.width / 2), Math.trunc(cy) - Math.trunc(p.height / 2), alpha);
}

/** картинка, збільшена в s разів, по центру (cx, cy) */
export function blitScaledCenter(c, p, cx, cy, s, alpha, smooth) {
    const w = Math.trunc(p.width * s), h = Math.trunc(p.height * s);
    if (alpha > 0) {
        draw(c, p, Math.trunc(cx) - Math.trunc(w / 2), Math.trunc(cy) - Math.trunc(h / 2), w, h, alpha, smooth);
    }
}

/** картинка, розтягнута на прямокутник */
export function blitTo(c, p, x, y, w, h, smooth) {
    draw(c, p, x, y, w, h, 255, smooth);
}

/** частина картинки (sx, sy, sw, sh), розтягнута на прямокутник */
export function blitAreaTo(c, p, sx, sy, sw, sh, x, y, w, h, smooth = false) {
    if (sw <= 0 || sh <= 0 || w <= 0 || h <= 0) {
        return;
    }
    c.imageSmoothingEnabled = smooth;
    c.drawImage(p.src, p.sx + sx, p.sy + sy, sw, sh, x, y, w, h);
}

/** копія картинки, віддзеркалена згори донизу */
export function flipV(p) {
    const cv = canvas(p.width, p.height);
    const c = cv.getContext('2d');
    c.translate(0, p.height);
    c.scale(1, -1);
    c.drawImage(p.src, p.sx, p.sy, p.width, p.height, 0, 0, p.width, p.height);
    return new Pic(cv);
}

/** копія картинки, збільшена/зменшена до w x h (без згладжування -- піксель-арт лишається чітким) */
export function scaled(p, w, h, smooth = false) {
    const cv = canvas(w, h);
    const c = cv.getContext('2d');
    c.imageSmoothingEnabled = smooth;
    c.drawImage(p.src, p.sx, p.sy, p.width, p.height, 0, 0, cv.width, cv.height);
    return new Pic(cv);
}

const darkCache = new WeakMap();

/**
 * картинка з RGB, помноженим на m (як fill((m, m, m), BLEND_RGB_MULT) у pygame) -- для затемнення кнопок.
 * Затемнені копії запам'ятовуються (m округлюється до 1/32), тож щокадрово нічого не перемальовується
 */
export function darkened(p, m) {
    const level = Math.max(0, Math.min(32, Math.round(m * 32)));
    if (level >= 32) {
        return p;
    }
    let byLevel = darkCache.get(p);
    if (!byLevel) {
        byLevel = new Map();
        darkCache.set(p, byLevel);
    }
    let out = byLevel.get(level);
    if (!out) {
        const cv = canvas(p.width, p.height);
        const c = cv.getContext('2d');
        c.drawImage(p.src, p.sx, p.sy, p.width, p.height, 0, 0, p.width, p.height);
        c.globalCompositeOperation = 'source-atop';      // -- чорне -- тільки поверх непрозорого
        c.fillStyle = `rgba(0,0,0,${1 - level / 32})`;
        c.fillRect(0, 0, p.width, p.height);
        out = new Pic(cv);
        byLevel.set(level, out);
    }
    return out;
}

// -- фігури
/** суцільний прямокутник (як surface.fill(color, rect)) */
export function fill(c, color, x, y, w, h, alpha = 255) {
    c.fillStyle = css(color, alpha);
    c.fillRect(x, y, w, h);
}

function roundPath(c, x, y, w, h, r) {
    r = Math.max(0, Math.min(r, w / 2, h / 2));
    c.beginPath();
    c.moveTo(x + r, y);
    c.arcTo(x + w, y, x + w, y + h, r);
    c.arcTo(x + w, y + h, x, y + h, r);
    c.arcTo(x, y + h, x, y, r);
    c.arcTo(x, y, x + w, y, r);
    c.closePath();
}

export function roundRect(c, color, x, y, w, h, radius) {
    c.fillStyle = css(color);
    roundPath(c, x, y, w, h, radius);
    c.fill();
}

export function roundBox(c, color, b, radius) {
    roundRect(c, color, b.x, b.y, b.w, b.h, radius);
}

/** рамка товщини width всередині прямокутника (як pygame.draw.rect з width) */
export function roundBoxStroke(c, color, b, width, radius) {
    const h = width / 2;
    c.strokeStyle = css(color);
    c.lineWidth = width;
    roundPath(c, b.x + h, b.y + h, b.w - width, b.h - width, Math.max(0, radius - h));
    c.stroke();
}

export function line(c, color, x0, y0, x1, y1, width) {
    c.strokeStyle = css(color);
    c.lineWidth = width;
    c.beginPath();
    c.moveTo(x0, y0);
    c.lineTo(x1, y1);
    c.stroke();
}

/** многокутник: pts = x0, y0, x1, y1, ... */
export function polygon(c, color, ...pts) {
    c.fillStyle = css(color);
    c.beginPath();
    c.moveTo(pts[0], pts[1]);
    for (let i = 2; i < pts.length; i += 2) {
        c.lineTo(pts[i], pts[i + 1]);
    }
    c.closePath();
    c.fill();
}

/** чотирикутник смуги шлейфу (колір уже з прозорістю -- рядок css) */
export function quad(c, style, x0, y0, x1, y1, x2, y2, x3, y3) {
    c.fillStyle = style;
    c.beginPath();
    c.moveTo(x0, y0);
    c.lineTo(x1, y1);
    c.lineTo(x2, y2);
    c.lineTo(x3, y3);
    c.closePath();
    c.fill();
}

export function circle(c, color, cx, cy, r, alpha = 255) {
    c.fillStyle = css(color, alpha);
    c.beginPath();
    c.arc(cx, cy, r, 0, Math.PI * 2);
    c.fill();
}

/** кільце товщини width всередині кола радіуса r */
export function ring(c, color, cx, cy, r, width, alpha = 255) {
    c.strokeStyle = css(color, alpha);
    c.lineWidth = width;
    c.beginPath();
    c.arc(cx, cy, Math.max(0, r - width / 2), 0, Math.PI * 2);
    c.stroke();
}

/** обрізати малювання прямокутником (до c.restore()) */
export function clipBox(c, b) {
    c.beginPath();
    c.rect(b.x, b.y, b.w, b.h);
    c.clip();
}
