package com.extraside.flappybird;

import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.PorterDuff;
import android.graphics.PorterDuffXfermode;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Random;

/**
 * Фон: небо, хмари, шари гір/міста, кущів і землі (паралакс), світило і ефекти.
 * Малює в координатах полотна: x від 0 до viewW, y -- як у ігрового поля (0..700).
 * На високому екрані телефона небо продовжується вгору (top), а земля -- вниз (bottom).
 */
final class Scenery {

    // -- шар, що їде вліво і повторюється по горизонталі
    static final class ScrollLayer {
        Bitmap image;
        int y;
        float factor;
        float offset;
        int period;

        ScrollLayer(Layer l) {
            set(l);
        }

        /** інша картинка шару (інший фон); зсув лишається -- шар не стрибає */
        void set(Layer l) {
            image = l.image;
            y = l.y;
            factor = l.factor;
            period = image.getWidth() / 2;
            offset %= period * 2;
        }

        void update(float speed, float dt) {
            offset = (offset + speed * factor * dt) % (period * 2);
            if (offset < 0) {
                offset += period * 2;
            }
        }

        void draw(Canvas c, int width) {
            int x = -(int) offset;
            int w = image.getWidth();
            while (x < width) {
                Gfx.blit(c, image, x, y);
                x += w;
            }
        }
    }

    static final class Layer {
        final Bitmap image;
        final int y;
        final float factor;

        Layer(Bitmap image, int y, float factor) {
            this.image = image;
            this.y = y;
            this.factor = factor;
        }
    }

    /** хмара пливе вліво; idx -- яка це хмара з набору (у кожного фону свої кольори хмар) */
    static final class Cloud {
        final int idx;
        final int width;
        float x;
        final int baseY;
        int y;
        final float speed;
        final int screenW;
        private final Random rnd;

        Cloud(int idx, int width, float x, int y, float speed, int screenW, Random rnd) {
            this.idx = idx;
            this.width = width;
            this.x = x;
            this.baseY = y;
            this.y = y;
            this.speed = speed;
            this.screenW = screenW;
            this.rnd = rnd;
        }

        void update(float dt) {
            x -= speed * dt;
            if (x + width < 0) {
                x = screenW + 10 + rnd.nextFloat() * 130;
                y = baseY + rnd.nextInt(25) - 12;
            }
        }

        void draw(Canvas c, Bitmap image) {
            Gfx.blit(c, image, (int) x, y);
        }
    }

    // -- ефекти фонів: гра малює їх сама поверх картинок (на всю ширину полотна).
    // -- sky -- одразу після неба (за хмарами і горами), інакше -- перед кущами
    interface Fx {
        boolean sky();

        void update(float dt, float speed);

        void draw(Canvas c, float t);
    }

    /** зорі на нічному небі: мерехтять кожна у своєму темпі; зорі дуже далеко -- тому не їдуть */
    static final class Stars implements Fx {
        private final int[] xs, ys;
        private final float[] phase, rate;
        private final boolean[] cross;

        Stars(int viewW, int top) {
            Random rnd = new Random(3);    // -- однакове розташування щоразу
            int span = 460 + top;
            int n = (int) (viewW * 0.16f * span / 460f);
            xs = new int[n];
            ys = new int[n];
            phase = new float[n];
            rate = new float[n];
            cross = new boolean[n];
            for (int i = 0; i < n; i++) {
                xs[i] = rnd.nextInt(Math.max(1, viewW / 2)) * 2;
                ys[i] = rnd.nextInt(Math.max(1, span / 2)) * 2 - top;
                phase[i] = rnd.nextFloat() * 6.3f;
                rate[i] = 1.2f + rnd.nextFloat() * 2.3f;
                cross[i] = rnd.nextFloat() < 0.22f;
            }
        }

        public boolean sky() {
            return true;
        }

        public void update(float dt, float speed) {
        }

        public void draw(Canvas c, float t) {
            for (int i = 0; i < xs.length; i++) {
                float b = 0.6f + 0.4f * (float) Math.sin(t * rate[i] + phase[i]);
                int col = Gfx.rgb((int) (255 * b), (int) (248 * b), (int) (215 * b));
                int x = xs[i], y = ys[i];
                if (cross[i]) {                     // -- яскраві зорі -- хрестиком
                    Gfx.fill(c, col, x - 2, y, 6, 2);
                    Gfx.fill(c, col, x, y - 2, 2, 6);
                } else {
                    Gfx.fill(c, col, x, y, 2, 2);
                }
            }
        }
    }

    /** сніжинки: падають, гойдаються, вітер і рух світу зносять їх уліво (ближчі -- більші і швидші) */
    static final class Snow implements Fx {
        static final int BOTTOM = 640;
        private final Random rnd = new Random(5);
        private final int w, top;
        private final float[][] flakes;   // -- x, y, швидкість падіння, розмір, фаза

        Snow(int viewW, int top) {
            this.w = viewW;
            this.top = top;
            int n = (int) (viewW * 0.14f * (BOTTOM + top) / BOTTOM);
            flakes = new float[n][];
            int[] sizes = {2, 2, 2, 4};
            for (int i = 0; i < n; i++) {
                flakes[i] = new float[]{rnd.nextFloat() * viewW, rnd.nextFloat() * (BOTTOM + top) - top,
                        30 + rnd.nextFloat() * 40, sizes[rnd.nextInt(4)], rnd.nextFloat() * 6.3f};
            }
        }

        public boolean sky() {
            return false;
        }

        public void update(float dt, float speed) {
            for (float[] f : flakes) {
                f[1] += f[2] * dt;
                f[0] -= (speed * 0.3f + 12) * dt * f[3] / 3;
                if (f[1] > BOTTOM) {
                    f[1] -= BOTTOM + top + 10;
                    f[0] = rnd.nextFloat() * w;
                }
                if (f[0] < -10) {
                    f[0] += w + 20;
                }
            }
        }

        public void draw(Canvas c, float t) {
            for (float[] f : flakes) {
                int x = (int) Math.floor((f[0] + Math.sin(t * 1.3f + f[4]) * 5) / 2) * 2;   // -- по сітці 2 px
                int y = (int) Math.floor(f[1] / 2) * 2;
                Gfx.fill(c, f[3] > 2 ? Gfx.rgb(255, 255, 255) : Gfx.rgb(226, 238, 255), x, y, f[3], f[3]);
            }
        }
    }

    /** світлячки над нічними кущами: блимають і кружляють, їдуть разом з кущами */
    static final class Fireflies implements Fx {
        private static Bitmap glow;
        private final int w;
        private final float[][] flies;   // -- x, y, фаза, темп

        Fireflies(int viewW) {
            Random rnd = new Random(9);
            w = viewW;
            int n = Math.max(4, (int) (viewW * 0.035f));
            flies = new float[n][];
            for (int i = 0; i < n; i++) {
                flies[i] = new float[]{rnd.nextFloat() * viewW, 500 + rnd.nextFloat() * 100,
                        rnd.nextFloat() * 6.3f, 0.6f + rnd.nextFloat() * 0.6f};
            }
            if (glow == null) {
                // -- як у pygame: внутрішнє коло замінює (а не змішує) зовнішнє
                glow = Bitmap.createBitmap(12, 12, Bitmap.Config.ARGB_8888);
                Canvas g = new Canvas(glow);
                Paint p = new Paint();
                p.setColor(Gfx.withAlpha(Gfx.rgb(190, 255, 110), 60));
                g.drawCircle(6, 6, 6, p);
                p.setXfermode(new PorterDuffXfermode(PorterDuff.Mode.SRC));
                p.setColor(Gfx.withAlpha(Gfx.rgb(220, 255, 150), 120));
                g.drawCircle(6, 6, 3, p);
            }
        }

        public boolean sky() {
            return false;
        }

        public void update(float dt, float speed) {
            for (float[] f : flies) {
                f[0] -= speed * 0.45f * dt;
                if (f[0] < -30) {
                    f[0] += w + 60;
                }
            }
        }

        public void draw(Canvas c, float t) {
            for (float[] f : flies) {
                float k = 0.5f + 0.5f * (float) Math.sin(t * 2.5f * f[3] + f[2]);
                float x = f[0] + (float) Math.sin(t * 0.8f * f[3] + f[2]) * 14;
                float y = f[1] + (float) Math.sin(t * 1.3f * f[3] + f[2] * 2) * 8;
                Gfx.blit(c, glow, (int) x - 6, (int) y - 6, (int) (170 * k));
                if (k > 0.3f) {
                    Gfx.fill(c, Gfx.rgb(250, 255, 170), (int) Math.floor(x / 2) * 2, (int) Math.floor(y / 2) * 2, 2, 2);
                }
            }
        }
    }

    static Fx makeFx(String name, int viewW, int top) {
        switch (name) {
            case "stars":
                return new Stars(viewW, top);
            case "snow":
                return new Snow(viewW, top);
            case "fireflies":
                return new Fireflies(viewW);
            default:
                return null;
        }
    }

    /**
     * Один фон (з магазину): небо, шари гір/міста, кущів і землі, світило (сонце/місяць),
     * свої кольори хмар і ефекти. Розташування хмар -- спільне для всіх фонів (manifest.json).
     */
    static final class Backdrop implements ShopItem {
        final String id;
        final int price;
        final Bitmap sky;
        final int skyTop;          // -- колір верху неба: ним небо продовжується вгору
        final HashMap<String, Layer> layers = new HashMap<>();
        final Bitmap body;
        final int bodyX, bodyY, bodyThumbY;
        final Bitmap[] clouds;
        final List<String> fx = new ArrayList<>();

        Backdrop(Assets a, JSONObject spec, Bitmap[] defaultClouds) throws JSONException {
            id = spec.getString("id");
            price = spec.getInt("price");
            sky = a.image(spec.getString("sky"));
            skyTop = sky.getPixel(sky.getWidth() / 2, 0) | 0xFF000000;
            JSONObject ls = spec.getJSONObject("layers");
            for (String name : new String[]{"far", "bushes", "ground"}) {
                JSONObject l = ls.getJSONObject(name);
                layers.put(name, new Layer(a.image(l.getString("file")), l.getInt("y"), (float) l.getDouble("factor")));
            }
            if (spec.isNull("body")) {
                body = null;
                bodyX = bodyY = bodyThumbY = 0;
            } else {
                JSONObject b = spec.getJSONObject("body");
                body = a.image(b.getString("file"));
                bodyX = b.getInt("x");
                bodyY = b.getInt("y");
                bodyThumbY = b.getInt("thumb_y");
            }
            if (spec.isNull("clouds")) {
                clouds = defaultClouds;
            } else {
                JSONArray cs = spec.getJSONArray("clouds");
                clouds = new Bitmap[cs.length()];
                for (int i = 0; i < cs.length(); i++) {
                    clouds[i] = a.image(cs.getString(i));
                }
            }
            JSONArray f = spec.optJSONArray("fx");
            if (f != null) {
                for (int i = 0; i < f.length(); i++) {
                    String name = f.getString(i);
                    if (makeFx(name, 1, 0) != null) {
                        fx.add(name);
                    }
                }
            }
        }

        public String id() {
            return id;
        }

        public int price() {
            return price;
        }
    }

    // -- мініатюра фону в магазині: смуга сцени від неба над горизонтом до землі (у координатах поля)
    static final int THUMB_TOP = 360, THUMB_H = 320;
    // -- рядки картинки землі, якими земля продовжується вниз на високих екранах (без трави і без нижньої рамки)
    private static final int DIRT_FROM = 46, DIRT_TO = 75;

    final int screenW;
    final int groundY;
    final List<Backdrop> themes = new ArrayList<>();
    private final HashMap<String, Backdrop> themeById = new HashMap<>();
    private final int[][] cloudSpecs;     // -- x, y хмар з manifest.json
    private final float[] cloudSpeeds;
    private final Random rnd = new Random();
    private List<Cloud> clouds = new ArrayList<>();
    private List<Fx> fx = new ArrayList<>();
    Backdrop theme;
    Bitmap sky;
    float speed = 60f;
    float t = 0f;
    private final ScrollLayer far, bushes, ground;
    private final HashMap<String, Bitmap> thumbs = new HashMap<>();
    int viewW, ox, top, bottom;

    Scenery(Assets a, JSONObject manifest, JSONArray backdrops, int screenW) throws JSONException {
        this.screenW = screenW;
        JSONArray cs = manifest.getJSONArray("clouds");
        Bitmap[] defaultClouds = new Bitmap[cs.length()];
        cloudSpecs = new int[cs.length()][];
        cloudSpeeds = new float[cs.length()];
        for (int i = 0; i < cs.length(); i++) {
            JSONObject c = cs.getJSONObject(i);
            defaultClouds[i] = a.image(c.getString("file"));
            cloudSpecs[i] = new int[]{c.getInt("x"), c.getInt("y")};
            cloudSpeeds[i] = (float) c.getDouble("speed");
        }
        for (int i = 0; i < backdrops.length(); i++) {
            Backdrop th = new Backdrop(a, backdrops.getJSONObject(i), defaultClouds);
            themes.add(th);
            themeById.put(th.id, th);
        }
        groundY = manifest.getJSONObject("screen").getInt("ground_y");
        Backdrop first = themes.get(0);
        far = new ScrollLayer(first.layers.get("far"));
        bushes = new ScrollLayer(first.layers.get("bushes"));
        ground = new ScrollLayer(first.layers.get("ground"));
        theme = first;
        sky = first.sky;
        viewW = -1;
        setView(screenW, 0, 0, 0);
        setTheme(first.id);
    }

    /** змінює фон (шари їдуть далі з того ж місця); повертає id фону, який реально поставили */
    String setTheme(String themeId) {
        Backdrop th = themeById.get(themeId);
        theme = th != null ? th : themes.get(0);
        sky = theme.sky;
        far.set(theme.layers.get("far"));
        bushes.set(theme.layers.get("bushes"));
        ground.set(theme.layers.get("ground"));
        fx = makeFxList(theme, viewW, top);
        return theme.id;
    }

    Backdrop byId(String id) {
        return themeById.get(id);
    }

    private static List<Fx> makeFxList(Backdrop th, int w, int top) {
        List<Fx> out = new ArrayList<>();
        for (String name : th.fx) {
            out.add(makeFx(name, w, top));
        }
        return out;
    }

    /**
     * розмір полотна: ширина viewW (ігрове поле починається з ox), над полем ще top px неба,
     * під полем -- bottom px землі. Набір хмар повторюється кожні screenW пікселів, щоб по боках теж були хмари
     */
    void setView(int viewW, int ox, int top, int bottom) {
        if (viewW == this.viewW && ox == this.ox && top == this.top && bottom == this.bottom) {
            return;
        }
        this.viewW = viewW;
        this.ox = ox;
        this.top = top;
        this.bottom = bottom;
        int first = -(int) Math.ceil(ox / (double) screenW);
        int last = (int) Math.ceil((viewW - ox) / (double) screenW);
        clouds = new ArrayList<>();
        for (int k = first; k < last; k++) {
            for (int i = 0; i < cloudSpecs.length; i++) {
                clouds.add(new Cloud(i, theme.clouds[i].getWidth(), cloudSpecs[i][0] + ox + k * screenW,
                        cloudSpecs[i][1], cloudSpeeds[i], viewW, rnd));
            }
        }
        fx = makeFxList(theme, viewW, top);
    }

    void update(float dt, Float targetSpeed, boolean snap) {
        if (targetSpeed != null) {
            if (snap) {
                speed = targetSpeed;
            } else {
                speed += (targetSpeed - speed) * Math.min(1f, 4f * dt);
            }
        }
        t += dt;
        for (Cloud c : clouds) {
            c.update(dt);
        }
        far.update(speed, dt);
        bushes.update(speed, dt);
        ground.update(speed, dt);
        for (Fx f : fx) {
            f.update(dt, speed);
        }
    }

    /** світило, хмари, гори/місто, кущі і ефекти -- усе, що позаду труб (небо вже намальоване) */
    private void drawScene(Canvas c, Backdrop th, int ox, List<Cloud> clouds, List<Fx> fx, float t,
                           boolean thumb, int width) {
        for (Fx f : fx) {
            if (f.sky()) {
                f.draw(c, t);
            }
        }
        if (th.body != null) {
            Gfx.blit(c, th.body, ox + th.bodyX, thumb ? th.bodyThumbY : th.bodyY);
        }
        for (Cloud cl : clouds) {
            cl.draw(c, th.clouds[cl.idx]);
        }
        far.draw(c, width);
        bushes.draw(c, width);
        for (Fx f : fx) {
            if (!f.sky()) {
                f.draw(c, t);
            }
        }
    }

    /** небо і все, що позаду труб. Canvas -- у координатах ігрового поля */
    void drawBack(Canvas c) {
        c.save();
        c.translate(-ox, 0);
        if (top > 0) {
            Gfx.fill(c, theme.skyTop, 0, -top, viewW, top + 1);
        }
        Gfx.blitTo(c, sky, 0, 0, viewW, sky.getHeight(), false);
        drawScene(c, theme, ox, clouds, fx, t, false, viewW);
        c.restore();
    }

    /** земля (і її продовження вниз на високому екрані) */
    void drawGround(Canvas c) {
        c.save();
        c.translate(-ox, 0);
        ground.draw(c, viewW);
        if (bottom > 0) {
            Bitmap img = ground.image;
            int band = DIRT_TO - DIRT_FROM;
            int end = ground.y + img.getHeight() + bottom;
            for (int y = ground.y + img.getHeight() - 1; y < end; y += band) {
                int h = Math.min(band, end - y);
                int x = -(int) ground.offset;
                while (x < viewW) {
                    Gfx.blitTo(c, img, Gfx.src(0, DIRT_FROM, img.getWidth(), h), x, y, img.getWidth(), h);
                    x += img.getWidth();
                }
            }
        }
        c.restore();
    }

    /** мініатюра фону для картки магазину (малюється один раз і запам'ятовується; удвічі більша -- для чіткості) */
    Bitmap thumbnail(String themeId, int tw, int th) {
        String key = themeId + ":" + tw + "x" + th;
        Bitmap cached = thumbs.get(key);
        if (cached != null) {
            return cached;
        }
        Backdrop theme = themeById.get(themeId);
        int w = Math.round(THUMB_H * tw / (float) th);
        int ox = (w - screenW) / 2;
        int h = sky.getHeight();
        Bitmap surf = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888);
        Canvas c = new Canvas(surf);
        Gfx.blitTo(c, theme.sky, 0, 0, w, h, false);
        List<Cloud> cl = new ArrayList<>();
        for (int i = 0; i < cloudSpecs.length; i++) {
            cl.add(new Cloud(i, 0, cloudSpecs[i][0] + ox, cloudSpecs[i][1], 0, w, rnd));
        }
        // -- шари цього фону на час малювання, з нульовим зсувом
        ScrollLayer[] ls = {far, bushes, ground};
        String[] names = {"far", "bushes", "ground"};
        Layer[] saved = new Layer[3];
        float[] offsets = new float[3];
        for (int i = 0; i < 3; i++) {
            saved[i] = new Layer(ls[i].image, ls[i].y, ls[i].factor);
            offsets[i] = ls[i].offset;
            ls[i].set(theme.layers.get(names[i]));
            ls[i].offset = 0;
        }
        drawScene(c, theme, ox, cl, makeFxList(theme, w, 0), 0f, true, w);
        ground.draw(c, w);
        for (int i = 0; i < 3; i++) {
            ls[i].set(saved[i]);
            ls[i].offset = offsets[i];
        }
        Bitmap band = Bitmap.createBitmap(surf, 0, THUMB_TOP, w, THUMB_H);
        Bitmap out = Bitmap.createScaledBitmap(band, tw * 2, th * 2, true);
        thumbs.put(key, out);
        return out;
    }
}
