package com.extraside.flappybird;

import android.graphics.Canvas;

/**
 * Шлейф за пташкою: напівпрозора смуга по точках, де пташка вже пролетіла.
 * Точки -- від голови (k=0, біля пташки) до хвоста (k=1, майже зник);
 * seed 0..1 -- випадкове число точки (для іскорок).
 */
class Trail implements ShopItem {

    /** точки шлейфу для малювання: x, y, k (0 -- голова, 1 -- хвіст), seed */
    static final class Points {
        float[] x = new float[64], y = new float[64], k = new float[64], seed = new float[64];
        float[] nx = new float[64], ny = new float[64];
        int n;

        void clear() {
            n = 0;
        }

        void add(float px, float py, float pk, float ps) {
            if (n == x.length) {
                int m = n * 2;
                x = java.util.Arrays.copyOf(x, m);
                y = java.util.Arrays.copyOf(y, m);
                k = java.util.Arrays.copyOf(k, m);
                seed = java.util.Arrays.copyOf(seed, m);
                nx = java.util.Arrays.copyOf(nx, m);
                ny = java.util.Arrays.copyOf(ny, m);
            }
            x[n] = px;
            y[n] = py;
            k[n] = pk;
            seed[n] = ps;
            n++;
        }

        /** для кожної точки -- одиничний вектор поперек шлейфу (щоб товщина не залежала від нахилу) */
        void normals() {
            for (int i = 0; i < n; i++) {
                int a = Math.max(0, i - 1), b = Math.min(n - 1, i + 1);
                float dx = x[a] - x[b], dy = y[a] - y[b];
                float len = (float) Math.hypot(dx, dy);
                if (len == 0) {
                    len = 1;
                }
                nx[i] = -dy / len;
                ny[i] = dx / len;
            }
        }
    }

    // -- шлейфи в порядку магазину: (id, ціна). "none" -- без шлейфу, є в усіх;
    // -- "custom" -- свій: кольори, стиль і товщину гравець обирає сам (Custom)
    static final String[] IDS = {"none", "neon", "rainbow", "custom"};
    static final int[] PRICES = {0, 150, 250, 500};
    static final int[] RAINBOW = {
            Gfx.rgb(255, 72, 72), Gfx.rgb(255, 160, 48), Gfx.rgb(255, 228, 64),
            Gfx.rgb(96, 216, 88), Gfx.rgb(72, 160, 255), Gfx.rgb(164, 100, 240)};

    // -- палітра свого шлейфу (у редакторі -- 2 ряди по 8) і стилі (у порядку перемикача)
    static final int[] PALETTE = {
            Gfx.rgb(255, 64, 64), Gfx.rgb(255, 140, 40), Gfx.rgb(255, 222, 60), Gfx.rgb(150, 230, 60),
            Gfx.rgb(50, 200, 90), Gfx.rgb(50, 220, 220), Gfx.rgb(70, 150, 255), Gfx.rgb(64, 72, 230),
            Gfx.rgb(150, 80, 245), Gfx.rgb(230, 70, 220), Gfx.rgb(255, 120, 180), Gfx.rgb(255, 255, 255),
            Gfx.rgb(255, 200, 130), Gfx.rgb(150, 100, 60), Gfx.rgb(140, 140, 160), Gfx.rgb(40, 30, 50),
    };
    static final String[] STYLES = {"ribbon", "glow", "bubbles", "pixels", "sparks"};
    static final int WHITE = Gfx.rgb(255, 255, 255);

    static final float RAINBOW_BAND = 3;                      // -- px, товщина однієї смуги веселки
    static final float NEON_GLOW = 22, NEON_CORE = 8;         // -- px, ширина світіння і яскравої серединки
    static final int NEON_FROM = Gfx.rgb(255, 50, 190), NEON_TO = Gfx.rgb(120, 50, 255);

    final String id;
    final int price;

    Trail(String id, int price) {
        this.id = id;
        this.price = price;
    }

    public String id() {
        return id;
    }

    public int price() {
        return price;
    }

    static int mod(int a, int n) {
        return ((a % n) + n) % n;
    }

    void draw(Canvas c, Points p, float t) {
        if (id.equals("none") || p.n < 2) {
            return;
        }
        p.normals();
        paint(c, p, t);
    }

    void paint(Canvas c, Points p, float t) {
        if (id.equals("rainbow")) {
            rainbow(c, p);
        } else {
            glow(c, p, t, NEON_FROM, NEON_TO, NEON_GLOW, NEON_CORE);
        }
    }

    /** чотирикутник між сусідніми точками a і b: (oa0, oa1) / (ob0, ob1) -- від і до зсуву поперек шлейфу */
    static void band(Canvas c, Points p, int a, int b, float oa0, float oa1, float ob0, float ob1, int color) {
        Gfx.quad(c, color,
                p.x[a] + p.nx[a] * oa0, p.y[a] + p.ny[a] * oa0,
                p.x[b] + p.nx[b] * ob0, p.y[b] + p.ny[b] * ob0,
                p.x[b] + p.nx[b] * ob1, p.y[b] + p.ny[b] * ob1,
                p.x[a] + p.nx[a] * oa1, p.y[a] + p.ny[a] * oa1);
    }

    private static void rainbow(Canvas c, Points p) {
        int n = RAINBOW.length;
        for (int i = 0; i + 1 < p.n; i++) {
            float ha = RAINBOW_BAND * (1 - 0.35f * p.k[i]);        // -- до хвоста трохи тоншає
            float hb = RAINBOW_BAND * (1 - 0.35f * p.k[i + 1]);
            int alpha = (int) (210 * Math.pow(1 - p.k[i], 0.7));
            for (int j = 0; j < n; j++) {
                float o = j - n / 2f;
                band(c, p, i, i + 1, o * ha, (o + 1) * ha, o * hb, (o + 1) * hb, Gfx.withAlpha(RAINBOW[j], alpha));
            }
        }
    }

    /** неон: широке напівпрозоре світіння, яскрава серединка і іскорки поруч */
    static void glow(Canvas c, Points p, float t, int cFrom, int cTo, float glow, float core) {
        float[][] layers = {{glow, 150, 0f}, {core, 255, 0.5f}};
        for (float[] l : layers) {
            float width = l[0], alpha = l[1], light = l[2];
            for (int i = 0; i + 1 < p.n; i++) {
                int color = Gfx.lerp(Gfx.lerp(cFrom, cTo, p.k[i]), WHITE, light);
                float wa = width * (1 - 0.6f * p.k[i]) / 2;
                float wb = width * (1 - 0.6f * p.k[i + 1]) / 2;
                band(c, p, i, i + 1, -wa, wa, -wb, wb,
                        Gfx.withAlpha(color, (int) (alpha * Math.pow(1 - p.k[i], 0.7))));
            }
        }
        // -- іскорки: маленькі хрестики, що мерехтять поруч зі смугою
        for (int i = 0; i < p.n; i++) {
            float seed = p.seed[i], k = p.k[i];
            if (seed > 0.14f || k < 0.12f) {
                continue;
            }
            int r = Math.sin(t * 18 + seed * 90) > 0 ? 2 : 1;
            int col = Gfx.withAlpha(WHITE, (int) (255 * (1 - k)));
            float off = (seed - 0.07f) * 160 * glow / NEON_GLOW;
            int x = (int) (p.x[i] + p.nx[i] * off), y = (int) (p.y[i] + p.ny[i] * off);
            Gfx.fill(c, col, x - r, y, 2 * r + 1, 1);
            Gfx.fill(c, col, x, y - r, 1, 2 * r + 1);
        }
    }

    /**
     * Свій шлейф: колір біля пташки (c1) переходить у колір хвоста (c2), стиль -- з STYLES,
     * товщина 0..1. Усе це -- в config: гра підставляє сюди налаштування зі збереження,
     * і редактор у магазині міняє їх прямо на льоту.
     */
    static final class Custom extends Trail {
        static final float MIN_W = 6, MAX_W = 30;    // -- px, товщина шлейфу при повзунку на 0 і на 100%

        Store.TrailConfig config = new Store.TrailConfig();

        Custom(int price) {
            super("custom", price);
        }

        int c1() {
            return PALETTE[mod(config.c1, PALETTE.length)];
        }

        int c2() {
            return PALETTE[mod(config.c2, PALETTE.length)];
        }

        float width() {
            return MIN_W + (MAX_W - MIN_W) * config.width;
        }

        @Override
        void paint(Canvas c, Points p, float t) {
            int c1 = c1(), c2 = c2();
            float w = width();
            switch (config.style) {
                case "glow":
                    glow(c, p, t, c1, c2, w * 1.25f, w * 0.45f);
                    break;
                case "bubbles":
                    bubbles(c, p, c1, c2, w);
                    break;
                case "pixels":
                    pixels(c, p, c1, c2, w);
                    break;
                case "sparks":
                    sparks(c, p, t, c1, c2, w);
                    break;
                default:
                    ribbon(c, p, c1, c2, w);
            }
        }

        /** суцільна стрічка, до хвоста тоншає; уздовж верхнього краю -- світла смужка-блік */
        private static void ribbon(Canvas c, Points p, int c1, int c2, float w) {
            for (int i = 0; i + 1 < p.n; i++) {
                int color = Gfx.lerp(c1, c2, p.k[i]);
                int alpha = (int) (250 * Math.pow(1 - p.k[i], 0.55));
                float wa = w * (1 - 0.5f * p.k[i]) / 2, wb = w * (1 - 0.5f * p.k[i + 1]) / 2;
                band(c, p, i, i + 1, -wa, wa, -wb, wb, Gfx.withAlpha(color, alpha));
                band(c, p, i, i + 1, -wa * 0.7f, -wa * 0.2f, -wb * 0.7f, -wb * 0.2f,
                        Gfx.withAlpha(Gfx.lerp(color, WHITE, 0.45f), alpha));
            }
        }

        /** бульбашки: з'являються біля пташки маленькими, ростуть, розлітаються і зникають */
        private static void bubbles(Canvas c, Points p, int c1, int c2, float w) {
            for (int i = p.n - 1; i >= 0; i--) {          // -- старі (великі) знизу, нові зверху
                float seed = p.seed[i], k = p.k[i];
                if (seed > 0.2f) {
                    continue;
                }
                int r = Math.max(2, Math.round(w * (0.22f + 0.4f * k)));
                float cy = p.y[i] + (seed / 0.2f - 0.5f) * w * 1.2f * k;
                int color = Gfx.lerp(c1, c2, k);
                int alpha = (int) (250 * Math.sqrt(1 - k));
                int cx = Math.round(p.x[i]), cyi = Math.round(cy);
                Gfx.circle(c, Gfx.withAlpha(color, alpha / 2), cx, cyi, r);
                Gfx.ring(c, Gfx.withAlpha(Gfx.lerp(color, WHITE, 0.15f), alpha), cx, cyi, r, Math.max(2, r / 4));
                Gfx.fill(c, Gfx.withAlpha(WHITE, alpha), cx - r / 2, cyi - r / 2, 2, 2);
            }
        }

        /** 8-бітні «пікселі»: квадратики по сітці, розлітаються і зменшуються до хвоста */
        private static void pixels(Canvas c, Points p, int c1, int c2, float w) {
            int s = Math.max(4, Math.round(w / 3) / 2 * 2);
            for (int i = 0; i < p.n; i++) {
                float seed = p.seed[i], k = p.k[i];
                if (seed > 0.6f) {
                    continue;
                }
                int size = Math.max(2, Math.round(s * (1 - 0.6f * k)) / 2 * 2);
                float off = (seed / 0.6f - 0.5f) * w * (0.5f + 0.9f * k);
                int color = seed < 0.2f ? c1 : seed > 0.45f ? c2 : Gfx.lerp(c1, c2, k);
                Gfx.fill(c, Gfx.withAlpha(color, (int) (255 * Math.pow(1 - k, 0.4))),
                        (int) Math.floor(p.x[i] / 2) * 2 - size / 2,
                        (int) Math.floor((p.y[i] + off) / 2) * 2 - size / 2, size, size);
            }
        }

        /** тонка яскрава нитка і зірочки навколо неї, що мерехтять */
        private static void sparks(Canvas c, Points p, float t, int c1, int c2, float w) {
            float core = Math.max(3f, w * 0.22f);
            for (int i = 0; i + 1 < p.n; i++) {
                int color = Gfx.lerp(Gfx.lerp(c1, c2, p.k[i]), WHITE, 0.3f);
                float wa = core * (1 - 0.5f * p.k[i]) / 2, wb = core * (1 - 0.5f * p.k[i + 1]) / 2;
                band(c, p, i, i + 1, -wa, wa, -wb, wb, Gfx.withAlpha(color, (int) (230 * Math.pow(1 - p.k[i], 0.7))));
            }
            for (int i = 0; i < p.n; i++) {
                float seed = p.seed[i], k = p.k[i];
                if (seed > 0.32f || k < 0.05f) {
                    continue;
                }
                int r = Math.max(1, Math.round(w / 6 * (1 - k) * (0.6f + seed)));
                if (Math.sin(t * 16 + seed * 70) < -0.4) {
                    r = Math.max(1, r - 1);
                }
                int th = r >= 3 ? 2 : 1;                     // -- великі зірочки -- з товстішими променями
                float off = (seed / 0.32f - 0.5f) * w * 1.4f;
                int x = (int) (p.x[i] + p.nx[i] * off), y = (int) (p.y[i] + p.ny[i] * off);
                int alpha = (int) (255 * Math.pow(1 - k, 0.6));
                int color = Gfx.withAlpha(seed < 0.16f ? c1 : c2, alpha);
                Gfx.fill(c, color, x - r, y, 2 * r + th, th);
                Gfx.fill(c, color, x, y - r, th, 2 * r + th);
                Gfx.fill(c, Gfx.withAlpha(WHITE, alpha), x, y, th, th);
            }
        }
    }
}
