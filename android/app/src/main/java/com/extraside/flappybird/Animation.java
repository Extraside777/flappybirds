package com.extraside.flappybird;

import android.graphics.Bitmap;

/** кадри з горизонтальної смуги (sheet); pause -- скільки секунд стоїть перший кадр між повторами */
final class Animation {
    final Bitmap[] frames;
    final float fps;
    final float pause;
    final float playTime;
    float t;

    Animation(Bitmap sheet, int count, float fps, float pause, float start) {
        int fw = sheet.getWidth() / count, fh = sheet.getHeight();
        frames = new Bitmap[count];
        for (int i = 0; i < count; i++) {
            frames[i] = Bitmap.createBitmap(sheet, i * fw, 0, fw, fh);
        }
        this.fps = fps;
        this.pause = pause;
        playTime = count / fps;
        t = start % (playTime + pause);
    }

    Animation(Bitmap sheet, int count, float fps) {
        this(sheet, count, fps, 0f, 0f);
    }

    void update(float dt) {
        t = (t + dt) % (playTime + pause);
    }

    Bitmap frame() {
        if (t >= playTime) {
            return frames[0];
        }
        return frames[Math.min((int) (t * fps), frames.length - 1)];
    }
}
