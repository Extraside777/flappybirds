package com.extraside.flappybird;

import android.graphics.Bitmap;
import android.graphics.Canvas;

import java.util.HashMap;

/**
 * Розтягує картинку-панель під будь-який розмір, не чіпаючи кути.
 * Середина по вертикалі -- один рядок з центру (інакше градієнт панелі розтягується смугами).
 */
final class NineSlice {
    private final Bitmap image;
    private final int b;
    private final HashMap<Long, Bitmap> cache = new HashMap<>();

    NineSlice(Bitmap src, int border) {
        b = border;
        int iw = src.getWidth(), ih = src.getHeight();
        image = Bitmap.createBitmap(iw, 2 * border + 1, Bitmap.Config.ARGB_8888);
        Canvas c = new Canvas(image);
        Gfx.blitArea(c, src, Gfx.src(0, 0, iw, border), 0, 0);
        Gfx.blitArea(c, src, Gfx.src(0, ih / 2, iw, 1), 0, border);
        Gfx.blitArea(c, src, Gfx.src(0, ih - border, iw, border), 0, border + 1);
    }

    Bitmap render(int w, int h) {
        long key = ((long) w << 32) | (h & 0xFFFFFFFFL);
        Bitmap out = cache.get(key);
        if (out != null) {
            return out;
        }
        int iw = image.getWidth(), ih = image.getHeight();
        out = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888);
        Canvas c = new Canvas(out);
        int[][] xs = {{0, b, 0, b}, {b, iw - b, b, w - b}, {iw - b, iw, w - b, w}};
        int[][] ys = {{0, b, 0, b}, {b, ih - b, b, h - b}, {ih - b, ih, h - b, h}};
        for (int[] x : xs) {
            for (int[] y : ys) {
                if (x[3] <= x[2] || y[3] <= y[2]) {
                    continue;
                }
                Gfx.blitTo(c, image, Gfx.src(x[0], y[0], x[1] - x[0], y[1] - y[0]), x[2], y[2], x[3] - x[2], y[3] - y[2]);
            }
        }
        cache.put(key, out);
        return out;
    }
}
