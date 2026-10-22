package com.extraside.flappybird;

import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Paint;

/** заголовок FLAPPY BIRD, що підстрибує, і анімовані кнопки-спрайти */
final class Ui {
    private Ui() {
    }

    static final class TitleLine {
        static final float CYCLE = 1.7f;
        static final float HOP = 0.75f;
        static final float LAND = 0.18f;

        final Bitmap image;
        final int x, y;
        final float delay, amp;

        TitleLine(Bitmap image, int x, int y, float delay, float amp) {
            this.image = image;
            this.x = x;
            this.y = y;
            this.delay = delay;
            this.amp = amp;
        }

        void draw(Canvas c, float t) {
            float cyc = (t - delay) % CYCLE;
            if (cyc < 0) {
                cyc += CYCLE;
            }
            float dy = 0f, squash = 0f;
            if (cyc < HOP) {
                float u = cyc / HOP;
                dy = -amp * 4 * u * (1 - u);
            } else if (cyc < HOP + LAND) {
                float k = (cyc - HOP) / LAND;
                squash = 0.10f * (float) Math.sin(Math.PI * k);
            }
            int w = image.getWidth(), h = image.getHeight();
            int px = x, py = y + Math.round(dy);
            if (squash > 0.005f) {
                int nw = (int) (w * (1 + squash * 0.5f)), nh = (int) (h * (1 - squash));
                px -= (nw - w) / 2;
                py += h - nh;
                Gfx.blitTo(c, image, px, py, nw, nh, true);
            } else {
                Gfx.blit(c, image, px, py);
            }
        }
    }

    static final class Title {
        final TitleLine[] lines;

        Title(TitleLine[] lines) {
            this.lines = lines;
        }

        void draw(Canvas c, float t) {
            for (int i = lines.length - 1; i >= 0; i--) {
                lines[i].draw(c, t);
            }
        }
    }

    /** що показує кнопка: картинку з бліком або основу з шестернею, що крутиться */
    interface Face {
        int width();

        int height();

        void update(float dt);

        void setSpeed(float speed);

        void draw(Canvas c, Paint p);
    }

    static final class GearFace implements Face {
        final Bitmap base;
        final Animation gear;
        final int ox, oy;
        float speed = 1f;

        GearFace(Bitmap base, Animation gear, int ox, int oy) {
            this.base = base;
            this.gear = gear;
            this.ox = ox;
            this.oy = oy;
        }

        public int width() {
            return base.getWidth();
        }

        public int height() {
            return base.getHeight();
        }

        public void update(float dt) {
            gear.update(dt * speed);
        }

        public void setSpeed(float s) {
            speed = s;
        }

        public void draw(Canvas c, Paint p) {
            c.drawBitmap(base, 0, 0, p);
            c.drawBitmap(gear.frame(), ox, oy, p);
        }
    }

    static final class ShineFace implements Face {
        final Animation anim;

        ShineFace(Animation anim) {
            this.anim = anim;
        }

        public int width() {
            return anim.frames[0].getWidth();
        }

        public int height() {
            return anim.frames[0].getHeight();
        }

        public void update(float dt) {
            anim.update(dt);
        }

        public void setSpeed(float s) {
        }

        public void draw(Canvas c, Paint p) {
            c.drawBitmap(anim.frame(), 0, 0, p);
        }
    }

    static final class SpriteButton {
        static final float BOB_SPEED = 2.4f;

        Face face;
        final int x, y;
        final float bobPhase, bobAmp, dark;
        float hover = 0f;
        float press = 0f;
        private final Paint paint = new Paint();

        SpriteButton(Face face, int x, int y, float bobPhase, float bobAmp, float dark) {
            this.face = face;
            this.x = x;
            this.y = y;
            this.bobPhase = bobPhase;
            this.bobAmp = bobAmp;
            this.dark = dark;
        }

        void update(float dt, boolean hovered, float press) {
            hover += ((hovered ? 1f : 0f) - hover) * Math.min(1f, 12f * dt);
            this.press = press;
            face.setSpeed(1f + 1.5f * hover + 7f * press);
            face.update(dt);
        }

        void draw(Canvas c, float t) {
            draw(c, t, x, y);
        }

        void draw(Canvas c, float t, float px, float py) {
            int w = face.width(), h = face.height();
            py += Math.round(Math.sin(t * BOB_SPEED + bobPhase) * bobAmp);
            paint.setColorFilter(press > 0.001f ? Gfx.darken(1 - dark * press) : null);
            float s = 1f + 0.03f * hover - 0.06f * press;
            c.save();
            if (Math.abs(s - 1f) > 0.004f) {
                int nw = (int) (w * s), nh = (int) (h * s);
                px += (w - nw) / 2;
                py += (h - nh) / 2;
                paint.setFilterBitmap(true);
                c.translate(px, py);
                c.scale(nw / (float) w, nh / (float) h);
            } else {
                paint.setFilterBitmap(false);
                c.translate(px, py);
            }
            face.draw(c, paint);
            c.restore();
        }
    }
}
