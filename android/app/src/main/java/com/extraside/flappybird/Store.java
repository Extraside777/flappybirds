package com.extraside.flappybird;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.Charset;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * Налаштування (settings.json) і прогрес (save.json) у пам'яті застосунку -- той самий формат, що й у
 * src/settings.py: відомі ключі потрібного типу беруться з файлу, решта -- стандартні.
 */
final class Store {
    private Store() {
    }

    private static final Charset UTF8 = Charset.forName("UTF-8");

    /** налаштування гравця */
    static final class Config {
        String lang = Locale.getDefault().getLanguage().equals("uk") ? "uk" : "en";
        float menuMusic = 0.5f;     // -- повзунки 0..1
        float gameMusic = 0.5f;
        float sfx = 0.6f;

        float get(String name) {
            switch (name) {
                case "menu_music":
                    return menuMusic;
                case "game_music":
                    return gameMusic;
                default:
                    return sfx;
            }
        }

        void set(String name, float value) {
            switch (name) {
                case "menu_music":
                    menuMusic = value;
                    break;
                case "game_music":
                    gameMusic = value;
                    break;
                default:
                    sfx = value;
            }
        }
    }

    /** свій шлейф: кольори з палітри (номери, Trail.PALETTE), стиль, товщина 0..1 */
    static final class TrailConfig {
        int c1 = 9;
        int c2 = 6;
        String style = "glow";
        float width = 0.5f;
    }

    /** прогрес: рекорд, монетки, куплене і обране в магазині */
    static final class Progress {
        int best = 0;
        int coins = 0;
        int games = 0;
        String skin = "classic";                    // -- якою пташкою граємо
        List<String> owned = list("classic");       // -- куплені пташки
        String trail = "none";                      // -- який шлейф тягнеться за пташкою
        List<String> ownedTrails = list("none");    // -- куплені шлейфи
        String background = "day";                  // -- який фон
        List<String> ownedBackgrounds = list("day");
        String pipe = "classic";                    // -- скін труб
        List<String> ownedPipes = list("classic");
        TrailConfig customTrail = new TrailConfig();
    }

    private static List<String> list(String first) {
        List<String> l = new ArrayList<>();
        l.add(first);
        return l;
    }

    // -- читання
    private static JSONObject read(File f) {
        try (InputStream in = new FileInputStream(f)) {
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            byte[] buf = new byte[4096];
            int n;
            while ((n = in.read(buf)) > 0) {
                out.write(buf, 0, n);
            }
            return new JSONObject(new String(out.toByteArray(), UTF8));
        } catch (IOException | JSONException e) {
            return new JSONObject();   // -- нема файлу або він битий -- беремо стандартні
        }
    }

    private static float unit(JSONObject o, String key, float def) {
        Object v = o.opt(key);
        if (v instanceof Number && !(v instanceof Boolean)) {
            return Math.max(0f, Math.min(1f, ((Number) v).floatValue()));
        }
        return def;
    }

    private static int count(JSONObject o, String key, int def) {
        Object v = o.opt(key);
        if (v instanceof Integer || v instanceof Long) {
            return (int) Math.max(0, Math.min(Integer.MAX_VALUE, ((Number) v).longValue()));
        }
        return def;
    }

    private static String str(JSONObject o, String key, String def) {
        Object v = o.opt(key);
        return v instanceof String ? (String) v : def;
    }

    private static List<String> strings(JSONObject o, String key, List<String> def) {
        JSONArray a = o.optJSONArray(key);
        if (a == null) {
            return def;
        }
        List<String> out = new ArrayList<>();
        for (int i = 0; i < a.length(); i++) {
            Object v = a.opt(i);
            if (v instanceof String) {
                out.add((String) v);
            }
        }
        return out;
    }

    static Config loadConfig(File f) {
        JSONObject o = read(f);
        Config c = new Config();
        c.lang = str(o, "lang", c.lang);
        c.menuMusic = unit(o, "menu_music", c.menuMusic);
        c.gameMusic = unit(o, "game_music", c.gameMusic);
        c.sfx = unit(o, "sfx", c.sfx);
        return c;
    }

    static Progress loadProgress(File f) {
        JSONObject o = read(f);
        Progress p = new Progress();
        p.best = count(o, "best", p.best);
        p.coins = count(o, "coins", p.coins);
        p.games = count(o, "games", p.games);
        p.skin = str(o, "skin", p.skin);
        p.owned = strings(o, "owned", p.owned);
        p.trail = str(o, "trail", p.trail);
        p.ownedTrails = strings(o, "owned_trails", p.ownedTrails);
        p.background = str(o, "background", p.background);
        p.ownedBackgrounds = strings(o, "owned_backgrounds", p.ownedBackgrounds);
        p.pipe = str(o, "pipe", p.pipe);
        p.ownedPipes = strings(o, "owned_pipes", p.ownedPipes);
        JSONObject ct = o.optJSONObject("custom_trail");
        if (ct != null) {
            p.customTrail.c1 = count(ct, "c1", p.customTrail.c1);
            p.customTrail.c2 = count(ct, "c2", p.customTrail.c2);
            p.customTrail.style = str(ct, "style", p.customTrail.style);
            p.customTrail.width = unit(ct, "width", p.customTrail.width);
        }
        return p;
    }

    // -- запис
    private static void write(File f, JSONObject o) {
        File tmp = new File(f.getPath() + ".tmp");
        try (FileOutputStream out = new FileOutputStream(tmp)) {
            out.write(o.toString(2).getBytes(UTF8));
            out.getFD().sync();
        } catch (IOException | JSONException e) {
            return;
        }
        // -- щоб файл не побився, якщо гру закриють посеред запису
        if (!tmp.renameTo(f)) {
            f.delete();
            tmp.renameTo(f);
        }
    }

    /** 0.15f -> 0.15 (а не 0.15000000596) */
    private static double r2(float v) {
        return Math.round(v * 100) / 100.0;
    }

    static void save(File f, Config c) {
        try {
            JSONObject o = new JSONObject();
            o.put("lang", c.lang);
            o.put("menu_music", r2(c.menuMusic));
            o.put("game_music", r2(c.gameMusic));
            o.put("sfx", r2(c.sfx));
            write(f, o);
        } catch (JSONException ignored) {
        }
    }

    static void save(File f, Progress p) {
        try {
            JSONObject o = new JSONObject();
            o.put("best", p.best);
            o.put("coins", p.coins);
            o.put("games", p.games);
            o.put("skin", p.skin);
            o.put("owned", new JSONArray(p.owned));
            o.put("trail", p.trail);
            o.put("owned_trails", new JSONArray(p.ownedTrails));
            o.put("background", p.background);
            o.put("owned_backgrounds", new JSONArray(p.ownedBackgrounds));
            o.put("pipe", p.pipe);
            o.put("owned_pipes", new JSONArray(p.ownedPipes));
            JSONObject ct = new JSONObject();
            ct.put("c1", p.customTrail.c1);
            ct.put("c2", p.customTrail.c2);
            ct.put("style", p.customTrail.style);
            ct.put("width", r2(p.customTrail.width));
            o.put("custom_trail", ct);
            write(f, o);
        } catch (JSONException ignored) {
        }
    }
}
