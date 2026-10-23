package com.extraside.flappybird;

import android.graphics.Bitmap;
import android.graphics.Canvas;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;

/** усі спрайти гри (assets/sprites + manifest.json + extra.json) -- як SpriteKit у src/sprites.py */
final class SpriteKit {
    static final String[] LANGS = {"en", "uk"};

    final int groundY;
    final Scenery scenery;
    final List<Scenery.Backdrop> backgrounds;
    final Ui.Title title;
    private final HashMap<String, HashMap<String, Ui.Face>> faces = new HashMap<>();
    private final HashMap<String, HashMap<String, Bitmap>> texts = new HashMap<>();
    final HashMap<String, Bitmap> langNames = new HashMap<>();
    // -- цифри: "dark" -- на кремовій панелі, "light" -- білі з контуром, "big" -- для рекорду,
    // -- "title" -- золоті для напису «РІВЕНЬ 2»
    private final HashMap<String, HashMap<Character, Bitmap>> digits = new HashMap<>();
    final Bitmap trophySmall, trophyBig;
    final Ui.SpriteButton play, shop, menu, done, record, settings;
    final List<PipeArt> pipes = new ArrayList<>();
    private final HashMap<String, PipeArt> pipeById = new HashMap<>();
    PipeArt pipe;
    final List<BirdArt> skins = new ArrayList<>();
    private final HashMap<String, BirdArt> skinById = new HashMap<>();
    BirdArt bird;
    final NineSlice panel;
    final Animation coin;
    final Bitmap coinIcon;
    final HashMap<String, Animation> powerups = new HashMap<>();
    final Animation aura;
    final List<Trail> trails = new ArrayList<>();
    private final HashMap<String, Trail> trailById = new HashMap<>();
    Trail trail;
    final Trail.Custom customTrail;
    String lang = "en";

    SpriteKit(Assets a, float pressDark) throws JSONException {
        JSONObject m = a.json("manifest.json");
        JSONObject ex = a.json("extra.json");

        int screenW = m.getJSONObject("screen").getInt("w");
        groundY = m.getJSONObject("screen").getInt("ground_y");
        // -- фони в порядку магазину (перший -- звичайний «день»); scenery малює обраний
        scenery = new Scenery(a, m, ex.getJSONArray("backgrounds"), screenW);
        backgrounds = scenery.themes;

        // -- заголовок FLAPPY BIRD -- назва, не перекладаємо
        JSONArray tl = m.getJSONArray("title");
        Ui.TitleLine[] lines = new Ui.TitleLine[tl.length()];
        for (int i = 0; i < tl.length(); i++) {
            JSONObject ln = tl.getJSONObject(i);
            lines[i] = new Ui.TitleLine(a.image(ln.getString("file")), ln.getInt("x"), ln.getInt("y"),
                    0.22f * i, 15 - 3 * i);
        }
        title = new Ui.Title(lines);

        // -- все, що залежить від мови: кнопки і тексти
        JSONObject buttons = ex.getJSONObject("buttons");
        String[] names = {"play", "shop", "menu", "record", "done"};
        float[] starts = {0f, 1.6f, 0f, 0.8f, 0f};
        for (String lang : LANGS) {
            HashMap<String, Ui.Face> f = new HashMap<>();
            JSONObject bl = buttons.getJSONObject(lang);
            for (int i = 0; i < names.length; i++) {
                JSONObject b = bl.getJSONObject(names[i]);
                f.put(names[i], new Ui.ShineFace(new Animation(a.image(b.getString("file")), b.getInt("frames"),
                        (float) b.getDouble("fps"), (float) b.getDouble("pause"), starts[i])));
            }
            faces.put(lang, f);
        }
        JSONObject tx = ex.getJSONObject("texts");
        for (Iterator<String> it = tx.keys(); it.hasNext(); ) {
            String lang = it.next();
            HashMap<String, Bitmap> items = new HashMap<>();
            JSONObject o = tx.getJSONObject(lang);
            for (Iterator<String> kt = o.keys(); kt.hasNext(); ) {
                String key = kt.next();
                items.put(key, a.image(o.getString(key)));
            }
            texts.put(lang, items);
        }
        JSONObject ln = ex.getJSONObject("lang_names");
        for (String lang : LANGS) {
            langNames.put(lang, a.image(ln.getString(lang)));
        }
        String[][] styles = {{"dark", "digits"}, {"light", "digits_light"}, {"big", "digits_big"}, {"title", "digits_title"}};
        for (String[] st : styles) {
            HashMap<Character, Bitmap> d = new HashMap<>();
            JSONObject o = ex.getJSONObject(st[1]);
            for (Iterator<String> kt = o.keys(); kt.hasNext(); ) {
                String ch = kt.next();
                d.put(ch.charAt(0), a.image(o.getString(ch)));
            }
            digits.put(st[0], d);
        }
        trophySmall = a.image(ex.getJSONObject("trophy").getString("small"));
        trophyBig = a.image(ex.getJSONObject("trophy").getString("big"));

        JSONObject bp = buttons.getJSONObject("en");
        HashMap<String, Ui.Face> en = faces.get("en");
        play = new Ui.SpriteButton(en.get("play"), bp.getJSONObject("play").getInt("x"),
                bp.getJSONObject("play").getInt("y"), 0f, 2f, pressDark);
        shop = new Ui.SpriteButton(en.get("shop"), bp.getJSONObject("shop").getInt("x"),
                bp.getJSONObject("shop").getInt("y"), 1.3f, 2f, pressDark);
        menu = new Ui.SpriteButton(en.get("menu"), 0, 0, 0.6f, 1.5f, pressDark);
        done = new Ui.SpriteButton(en.get("done"), 0, 0, 0.6f, 1.5f, pressDark);
        record = new Ui.SpriteButton(en.get("record"), bp.getJSONObject("record").getInt("x"),
                bp.getJSONObject("record").getInt("y"), 2.6f, 2f, pressDark);

        JSONObject st = m.getJSONObject("settings");
        JSONObject g = st.getJSONObject("gear");
        Animation gear = new Animation(a.image(g.getString("file")), g.getInt("frames"), (float) g.getDouble("fps"));
        Ui.GearFace face = new Ui.GearFace(a.image(st.getString("base")), gear, g.getInt("ox"), g.getInt("oy"));
        settings = new Ui.SpriteButton(face, st.getInt("x"), st.getInt("y"), 0f, 0f, pressDark);

        // -- скіни труб у порядку магазину; pipe -- ті, що в грі
        JSONArray ps = ex.getJSONArray("pipes");
        for (int i = 0; i < ps.length(); i++) {
            PipeArt p = new PipeArt(a, ps.getJSONObject(i));
            pipes.add(p);
            pipeById.put(p.id, p);
        }
        pipe = pipes.get(0);
        // -- скіни пташок у порядку магазину; bird -- та, якою граємо
        JSONArray ss = ex.getJSONArray("skins");
        for (int i = 0; i < ss.length(); i++) {
            BirdArt b = new BirdArt(a, ss.getJSONObject(i));
            skins.add(b);
            skinById.put(b.id, b);
        }
        bird = skins.get(0);
        JSONObject pn = ex.getJSONObject("panel");
        panel = new NineSlice(a.image(pn.getString("file")), pn.getInt("slice"));

        JSONObject c = ex.getJSONObject("coin");
        coin = new Animation(a.image(c.getString("file")), c.getInt("frames"), (float) c.getDouble("fps"));
        coinIcon = coin.frames[0];

        // -- бонуси (іконки в бульбашках) і бульбашка щита навколо пташки
        JSONObject pu = ex.getJSONObject("powerups");
        for (String kind : new String[]{"shield", "slow", "x2"}) {
            powerups.put(kind, anim(a, pu.getJSONObject(kind)));
        }
        aura = anim(a, pu.getJSONObject("aura"));

        // -- шлейфи за пташкою (малюються кодом, без картинок); trail -- обраний
        Trail.Custom custom = null;
        for (int i = 0; i < Trail.IDS.length; i++) {
            Trail tr;
            if (Trail.IDS[i].equals("custom")) {
                custom = new Trail.Custom(Trail.PRICES[i]);
                tr = custom;
            } else {
                tr = new Trail(Trail.IDS[i], Trail.PRICES[i]);
            }
            trails.add(tr);
            trailById.put(tr.id, tr);
        }
        trail = trails.get(0);
        customTrail = custom;
    }

    private static Animation anim(Assets a, JSONObject spec) throws JSONException {
        return new Animation(a.image(spec.getString("file")), spec.getInt("frames"), (float) spec.getDouble("fps"),
                (float) spec.getDouble("pause"), 0f);
    }

    void setLang(String l) {
        boolean known = false;
        for (String x : LANGS) {
            known |= x.equals(l);
        }
        lang = known ? l : "en";
        HashMap<String, Ui.Face> f = faces.get(lang);
        play.face = f.get("play");
        shop.face = f.get("shop");
        menu.face = f.get("menu");
        record.face = f.get("record");
        done.face = f.get("done");
    }

    String setSkin(String id) {
        BirdArt b = skinById.get(id);
        bird = b != null ? b : skins.get(0);
        return bird.id;
    }

    String setTrail(String id) {
        Trail t = trailById.get(id);
        trail = t != null ? t : trails.get(0);
        return trail.id;
    }

    String setBackground(String id) {
        return scenery.setTheme(id);
    }

    String setPipe(String id) {
        PipeArt p = pipeById.get(id);
        pipe = p != null ? p : pipes.get(0);
        return pipe.id;
    }

    Bitmap text(String key) {
        return texts.get(lang).get(key);
    }

    int digitHeight(String style) {
        int h = 0;
        for (Bitmap b : digits.get(style).values()) {
            h = Math.max(h, b.getHeight());
        }
        return h;
    }

    int numberWidth(String text) {
        return numberWidth(text, "light", 2);
    }

    int numberWidth(String text, String style, int gap) {
        HashMap<Character, Bitmap> d = digits.get(style);
        int w = 0, n = 0;
        for (int i = 0; i < text.length(); i++) {
            Bitmap b = d.get(text.charAt(i));
            if (b != null) {
                w += b.getWidth();
                n++;
            }
        }
        return w + gap * Math.max(0, n - 1);
    }

    void drawNumber(Canvas c, String text, float x, float cy) {
        drawNumber(c, text, x, cy, "light", 0, 2, 255);
    }

    /**
     * число зі спрайтів-цифр по вертикальному центру cy.
     * Усі цифри одного стилю однакової висоти (базова лінія на одному місці),
     * тому стоять рівно в рядок і з підписами того ж розміру.
     * align: 0 -- x це центр, -1 -- лівий край, 1 -- правий край
     */
    void drawNumber(Canvas c, String text, float x, float cy, String style, int align, int gap, int alpha) {
        HashMap<Character, Bitmap> d = digits.get(style);
        int w = numberWidth(text, style, gap);
        if (w == 0) {
            return;
        }
        int px = (int) x;
        if (align == 0) {
            px -= w / 2;
        } else if (align > 0) {
            px -= w;
        }
        for (int i = 0; i < text.length(); i++) {
            Bitmap b = d.get(text.charAt(i));
            if (b == null) {
                continue;
            }
            Gfx.blit(c, b, px, (int) cy - b.getHeight() / 2, alpha);
            px += b.getWidth() + gap;
        }
    }
}
