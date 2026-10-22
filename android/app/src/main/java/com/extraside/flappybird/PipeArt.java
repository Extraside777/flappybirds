package com.extraside.flappybird;

import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Matrix;

import org.json.JSONException;
import org.json.JSONObject;

/**
 * Труба зі спрайтів (скін з магазину): тіло повторюється по вертикалі, зверху/знизу капелюшок.
 * mini -- зменшена копія для картки магазину: 1 / art_px -- кожен художній піксель стає одним, тому чітко
 */
final class PipeArt implements ShopItem {
    final String id;
    final int price;
    final Bitmap body, neck, cap, capFlip, neckFlip;
    final int bodyW, capW, capH;
    final PipeArt mini;

    PipeArt(Assets a, JSONObject spec) throws JSONException {
        this(a, spec, 1f);
    }

    private PipeArt(Assets a, JSONObject spec, float scale) throws JSONException {
        id = spec.getString("id");
        price = spec.getInt("price");
        body = img(a, spec.getString("body"), scale);
        neck = img(a, spec.getString("neck"), scale);
        cap = img(a, spec.getString("cap"), scale);
        capFlip = flip(cap);
        neckFlip = flip(neck);
        bodyW = Math.round(spec.getInt("body_w") * scale);
        capW = Math.round(spec.getInt("cap_w") * scale);
        capH = Math.round(spec.getInt("cap_h") * scale);
        mini = scale == 1f ? new PipeArt(a, spec, 1f / spec.getInt("art_px")) : this;
    }

    private static Bitmap img(Assets a, String file, float scale) {
        Bitmap im = a.image(file);
        if (scale == 1f) {
            return im;
        }
        return Bitmap.createScaledBitmap(im, Math.max(1, Math.round(im.getWidth() * scale)),
                Math.max(1, Math.round(im.getHeight() * scale)), false);
    }

    private static Bitmap flip(Bitmap b) {
        Matrix m = new Matrix();
        m.setScale(1, -1);
        return Bitmap.createBitmap(b, 0, 0, b.getWidth(), b.getHeight(), m, false);
    }

    public String id() {
        return id;
    }

    public int price() {
        return price;
    }

    /** тіло труби від y0 до y1 */
    private void column(Canvas c, int x, int y0, int y1) {
        int th = body.getHeight();
        int y = y0;
        while (y < y1) {
            int h = Math.min(th, y1 - y);
            Gfx.blitArea(c, body, Gfx.src(0, 0, bodyW, h), x, y);
            y += h;
        }
    }

    /**
     * x, width -- хітбокс труби; gapY..gapY+gap -- прохід; bottom -- де закінчується нижня труба,
     * top -- звідки звисає верхня
     */
    void draw(Canvas c, int x, int width, int gapY, int gap, int bottom, int top) {
        int cx = x + (width - capW) / 2;
        int bx = x + (width - bodyW) / 2;
        // -- верхня труба (капелюшок знизу)
        int topCap = gapY - capH;
        column(c, bx, top, topCap);
        Gfx.blit(c, neckFlip, bx, topCap - neck.getHeight());
        Gfx.blit(c, capFlip, cx, topCap);
        // -- нижня труба
        int low = gapY + gap;
        column(c, bx, low + capH, bottom);
        Gfx.blit(c, neck, bx, low + capH);
        Gfx.blit(c, cap, cx, low);
    }
}
