package com.extraside.flappybird;

import android.content.res.AssetManager;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;

import org.json.JSONException;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.Charset;
import java.util.HashMap;

/** читання assets/ гри: картинки зі sprites/ (кожна вантажиться один раз) і json-описи */
final class Assets {
    final AssetManager am;
    private final String dir;
    private final HashMap<String, Bitmap> cache = new HashMap<>();

    Assets(AssetManager am, String dir) {
        this.am = am;
        this.dir = dir.endsWith("/") ? dir : dir + "/";
    }

    Bitmap image(String rel) {
        Bitmap b = cache.get(rel);
        if (b != null) {
            return b;
        }
        BitmapFactory.Options o = new BitmapFactory.Options();
        o.inScaled = false;
        o.inPreferredConfig = Bitmap.Config.ARGB_8888;
        try (InputStream in = am.open(dir + rel)) {
            b = BitmapFactory.decodeStream(in, null, o);
        } catch (IOException e) {
            throw new IllegalStateException("нема картинки " + dir + rel, e);
        }
        if (b == null) {
            throw new IllegalStateException("не вдалося прочитати " + dir + rel);
        }
        cache.put(rel, b);
        return b;
    }

    JSONObject json(String rel) {
        try (InputStream in = am.open(dir + rel)) {
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            byte[] buf = new byte[8192];
            int n;
            while ((n = in.read(buf)) > 0) {
                out.write(buf, 0, n);
            }
            return new JSONObject(new String(out.toByteArray(), Charset.forName("UTF-8")));
        } catch (IOException | JSONException e) {
            throw new IllegalStateException("нема або битий " + dir + rel, e);
        }
    }
}
