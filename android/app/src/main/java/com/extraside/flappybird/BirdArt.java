package com.extraside.flappybird;

import android.graphics.Canvas;

import org.json.JSONException;
import org.json.JSONObject;

/**
 * Пташка (скін): махає крилами і нахиляється залежно від швидкості.
 * (ax, ay) -- де в кадрі центр тіла; саме ця точка ставиться в центр хітбокса
 * (у великих пташок крила виходять далеко за тіло).
 */
final class BirdArt implements ShopItem {
    final String id;
    final int price;
    final Animation anim;
    final int w, h;
    final float ax, ay;
    final int artPx;    // -- піксель-арт: розмір художнього пікселя (0 -- звичайна картинка)

    BirdArt(Assets a, JSONObject spec) throws JSONException {
        id = spec.getString("id");
        price = spec.getInt("price");
        anim = new Animation(a.image(spec.getString("file")), spec.getInt("frames"), (float) spec.getDouble("fps"));
        w = spec.getInt("fw");
        h = spec.getInt("fh");
        ax = (float) spec.optDouble("ax", w / 2.0);
        ay = (float) spec.optDouble("ay", h / 2.0);
        artPx = spec.optInt("art_px", 0);
    }

    public String id() {
        return id;
    }

    public int price() {
        return price;
    }

    void update(float dt, float flapSpeed) {
        anim.update(dt * flapSpeed);
    }

    void draw(Canvas c, float cx, float cy, float angle) {
        draw(c, cx, cy, angle, -1);
    }

    /** центр тіла -- в (cx, cy); кут -- в градусах, плюс -- дзьоб вгору */
    void draw(Canvas c, float cx, float cy, float angle, int frame) {
        android.graphics.Bitmap img = frame < 0 ? anim.frame() : anim.frames[frame % anim.frames.length];
        if (Math.abs(angle) > 0.5f) {
            c.save();
            c.translate(cx, cy);
            c.rotate(-angle);
            Gfx.blit(c, img, -ax, -ay);
            c.restore();
        } else {
            Gfx.blit(c, img, (int) (cx - ax), (int) (cy - ay));
        }
    }
}
