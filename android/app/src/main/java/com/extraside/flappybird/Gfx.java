package com.extraside.flappybird;

import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.LightingColorFilter;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.Rect;
import android.graphics.RectF;

/**
 * Малювання в стилі pygame: blit картинок, прямокутники, многокутники.
 * Піксель-арт малюється без згладжування (чіткі пікселі), фігури -- зі згладжуванням.
 * Уся гра працює в одному (UI) потоці, тому спільні Paint-и тут безпечні.
 */
final class Gfx {
    private Gfx() {
    }

    private static final Paint SPRITE = new Paint();
    private static final Paint SMOOTH = new Paint(Paint.FILTER_BITMAP_FLAG);
    private static final Paint SHAPE = new Paint(Paint.ANTI_ALIAS_FLAG);
    private static final Paint SOLID = new Paint();
    private static final Path PATH = new Path();
    private static final RectF TMP = new RectF();
    private static final Rect SRC = new Rect();

    static int rgb(int r, int g, int b) {
        return Color.rgb(r, g, b);
    }

    static int withAlpha(int color, int alpha) {
        return (Math.max(0, Math.min(255, alpha)) << 24) | (color & 0xFFFFFF);
    }

    /** колір між c0 і c1 (k від 0 до 1) */
    static int lerp(int c0, int c1, float k) {
        int r = Math.round(Color.red(c0) + (Color.red(c1) - Color.red(c0)) * k);
        int g = Math.round(Color.green(c0) + (Color.green(c1) - Color.green(c0)) * k);
        int b = Math.round(Color.blue(c0) + (Color.blue(c1) - Color.blue(c0)) * k);
        return Color.rgb(r, g, b);
    }

    // -- картинки
    static Paint sprite(int alpha) {
        SPRITE.setAlpha(Math.max(0, Math.min(255, alpha)));
        SPRITE.setColorFilter(null);
        return SPRITE;
    }

    static Paint smooth(int alpha) {
        SMOOTH.setAlpha(Math.max(0, Math.min(255, alpha)));
        SMOOTH.setColorFilter(null);
        return SMOOTH;
    }

    /** множення RGB на m (як fill((m, m, m), BLEND_RGB_MULT) у pygame) -- для затемнення */
    static LightingColorFilter darken(float m) {
        int v = Math.max(0, Math.min(255, Math.round(255 * m)));
        return new LightingColorFilter(Color.rgb(v, v, v), 0);
    }

    static void blit(Canvas c, Bitmap b, float x, float y) {
        c.drawBitmap(b, x, y, sprite(255));
    }

    static void blit(Canvas c, Bitmap b, float x, float y, int alpha) {
        c.drawBitmap(b, x, y, sprite(alpha));
    }

    /** частина картинки src (як blit з area у pygame) */
    static void blitArea(Canvas c, Bitmap b, Rect src, float x, float y) {
        TMP.set(x, y, x + src.width(), y + src.height());
        c.drawBitmap(b, src, TMP, sprite(255));
    }

    static void blitCenter(Canvas c, Bitmap b, float cx, float cy) {
        blit(c, b, (int) cx - b.getWidth() / 2, (int) cy - b.getHeight() / 2);
    }

    static void blitCenter(Canvas c, Bitmap b, float cx, float cy, int alpha) {
        blit(c, b, (int) cx - b.getWidth() / 2, (int) cy - b.getHeight() / 2, alpha);
    }

    /** картинка, збільшена в s разів, по центру (cx, cy) */
    static void blitScaledCenter(Canvas c, Bitmap b, float cx, float cy, float s, int alpha, boolean smooth) {
        int w = (int) (b.getWidth() * s), h = (int) (b.getHeight() * s);
        int x = (int) cx - w / 2, y = (int) cy - h / 2;
        TMP.set(x, y, x + w, y + h);
        c.drawBitmap(b, null, TMP, smooth ? smooth(alpha) : sprite(alpha));
    }

    /** картинка, розтягнута на прямокутник */
    static void blitTo(Canvas c, Bitmap b, float x, float y, float w, float h, boolean smooth) {
        TMP.set(x, y, x + w, y + h);
        c.drawBitmap(b, null, TMP, smooth ? smooth(255) : sprite(255));
    }

    static void blitTo(Canvas c, Bitmap b, Rect src, float x, float y, float w, float h) {
        TMP.set(x, y, x + w, y + h);
        c.drawBitmap(b, src, TMP, sprite(255));
    }

    static Rect src(int x, int y, int w, int h) {
        SRC.set(x, y, x + w, y + h);
        return SRC;
    }

    // -- фігури
    /** суцільний прямокутник без згладжування (як surface.fill(color, rect)) */
    static void fill(Canvas c, int color, float x, float y, float w, float h) {
        SOLID.setColor(color);
        SOLID.setStyle(Paint.Style.FILL);
        c.drawRect(x, y, x + w, y + h, SOLID);
    }

    static void roundRect(Canvas c, int color, float x, float y, float w, float h, float radius) {
        SHAPE.setColor(color);
        SHAPE.setStyle(Paint.Style.FILL);
        TMP.set(x, y, x + w, y + h);
        c.drawRoundRect(TMP, radius, radius, SHAPE);
    }

    static void roundRect(Canvas c, int color, Box r, float radius) {
        roundRect(c, color, r.x, r.y, r.w, r.h, radius);
    }

    /** рамка товщини width всередині прямокутника (як pygame.draw.rect з width) */
    static void roundRectStroke(Canvas c, int color, Box r, float width, float radius) {
        SHAPE.setColor(color);
        SHAPE.setStyle(Paint.Style.STROKE);
        SHAPE.setStrokeWidth(width);
        float h = width / 2;
        TMP.set(r.x + h, r.y + h, r.right() - h, r.bottom() - h);
        c.drawRoundRect(TMP, Math.max(0, radius - h), Math.max(0, radius - h), SHAPE);
        SHAPE.setStyle(Paint.Style.FILL);
    }

    static void line(Canvas c, int color, float x0, float y0, float x1, float y1, float width) {
        SHAPE.setColor(color);
        SHAPE.setStyle(Paint.Style.STROKE);
        SHAPE.setStrokeWidth(width);
        c.drawLine(x0, y0, x1, y1, SHAPE);
        SHAPE.setStyle(Paint.Style.FILL);
    }

    /** многокутник: pts = x0, y0, x1, y1, ... */
    static void polygon(Canvas c, int color, float... pts) {
        PATH.reset();
        PATH.moveTo(pts[0], pts[1]);
        for (int i = 2; i < pts.length; i += 2) {
            PATH.lineTo(pts[i], pts[i + 1]);
        }
        PATH.close();
        SHAPE.setColor(color);
        SHAPE.setStyle(Paint.Style.FILL);
        c.drawPath(PATH, SHAPE);
    }

    /** чотирикутник без згладжування (сусідні смуги шлейфу стикуються без швів) */
    static void quad(Canvas c, int color, float x0, float y0, float x1, float y1,
                     float x2, float y2, float x3, float y3) {
        PATH.reset();
        PATH.moveTo(x0, y0);
        PATH.lineTo(x1, y1);
        PATH.lineTo(x2, y2);
        PATH.lineTo(x3, y3);
        PATH.close();
        SOLID.setColor(color);
        SOLID.setStyle(Paint.Style.FILL);
        c.drawPath(PATH, SOLID);
    }

    static void circle(Canvas c, int color, float cx, float cy, float r) {
        SHAPE.setColor(color);
        SHAPE.setStyle(Paint.Style.FILL);
        c.drawCircle(cx, cy, r, SHAPE);
    }

    /** кільце товщини width всередині кола радіуса r */
    static void ring(Canvas c, int color, float cx, float cy, float r, float width) {
        SHAPE.setColor(color);
        SHAPE.setStyle(Paint.Style.STROKE);
        SHAPE.setStrokeWidth(width);
        c.drawCircle(cx, cy, r - width / 2, SHAPE);
        SHAPE.setStyle(Paint.Style.FILL);
    }
}
