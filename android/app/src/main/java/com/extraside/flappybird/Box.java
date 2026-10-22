package com.extraside.flappybird;

import android.graphics.RectF;

/** прямокутник як pygame.Rect: x, y, ширина, висота -- у пікселях ігрового поля 400x700 */
final class Box {
    final int x, y, w, h;

    Box(int x, int y, int w, int h) {
        this.x = x;
        this.y = y;
        this.w = w;
        this.h = h;
    }

    /** прямокутник ширини w і висоти h, у якого середина верхнього краю -- (cx, top) */
    static Box midTop(int w, int h, int cx, int top) {
        return new Box(cx - w / 2, top, w, h);
    }

    int right() {
        return x + w;
    }

    int bottom() {
        return y + h;
    }

    int centerX() {
        return x + w / 2;
    }

    int centerY() {
        return y + h / 2;
    }

    Box inflate(int dx, int dy) {
        return new Box(x - dx / 2, y - dy / 2, w + dx, h + dy);
    }

    Box move(int dx, int dy) {
        return new Box(x + dx, y + dy, w, h);
    }

    boolean contains(float px, float py) {
        return px >= x && px < x + w && py >= y && py < y + h;
    }

    boolean overlaps(Box o) {
        return x < o.x + o.w && x + w > o.x && y < o.y + o.h && y + h > o.y;
    }

    /** спільна частина двох прямокутників */
    Box clip(Box o) {
        int l = Math.max(x, o.x), t = Math.max(y, o.y);
        int r = Math.min(right(), o.right()), b = Math.min(bottom(), o.bottom());
        return new Box(l, t, Math.max(0, r - l), Math.max(0, b - t));
    }

    RectF f() {
        return new RectF(x, y, x + w, y + h);
    }
}
