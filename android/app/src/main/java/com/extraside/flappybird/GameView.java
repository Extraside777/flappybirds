package com.extraside.flappybird;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.view.MotionEvent;
import android.view.View;

/**
 * Полотно гри. Масштаб -- як у src/display.py, але для телефона: ширина ігрового поля 400 тягнеться на
 * всю ширину екрана, а зайва висота йде на небо зверху і землю знизу (чорних смуг нема).
 * Цикл: кожен кадр екрана -- скільки треба кроків гри по 1/60 сек, потім малювання.
 */
final class GameView extends View {
    private static final double STEP = 1.0 / Game.FPS;
    private static final int MAX_VIEW_W = 2400;    // -- ширше за це сцену не розтягуємо

    private final Game game;
    private float k = 1f, destX, destY;
    private long lastNanos;
    private double acc;
    private boolean running;
    private int pointer = -1;      // -- палець, яким керуємо (перший)

    GameView(Context ctx) {
        super(ctx);
        game = new Game(ctx);
        setFocusable(true);
        setFocusableInTouchMode(true);
    }

    @Override
    protected void onSizeChanged(int w, int h, int oldw, int oldh) {
        if (w <= 0 || h <= 0) {
            return;
        }
        int viewW, viewH;
        if ((long) w * Game.HEIGHT >= (long) h * Game.WIDTH) {   // -- екран ширший за поле: розтягуємо вшир
            k = h / (float) Game.HEIGHT;
            viewH = Game.HEIGHT;
            viewW = Math.min(Math.round(w / k), MAX_VIEW_W);
        } else {                                                   // -- вищий: небо і земля довші
            k = w / (float) Game.WIDTH;
            viewW = Game.WIDTH;
            viewH = Math.round(h / k);
        }
        destX = (w - viewW * k) / 2;
        destY = (h - viewH * k) / 2;
        int ox = (viewW - Game.WIDTH) / 2;
        int oy = (viewH - Game.HEIGHT) / 2;
        game.setView(viewW, viewH, ox, oy);
    }

    @Override
    protected void onDraw(Canvas canvas) {
        long now = System.nanoTime();
        double dt = lastNanos == 0 ? 0 : (now - lastNanos) / 1e9;
        lastNanos = now;
        acc += Math.min(dt, 0.25);
        // -- +0.25 кроку: щоб тремтіння vsync (16.5 / 16.8 мс) не давало кадрів з 0 і 2 кроками
        int n = (int) Math.floor(acc / STEP + 0.25);
        if (n > 5) {
            n = 5;
            acc = 0;
        } else {
            acc -= n * STEP;
        }
        for (int i = 0; i < n; i++) {
            game.step();
        }

        canvas.drawColor(Color.BLACK);
        canvas.save();
        canvas.translate(destX, destY);
        canvas.scale(k, k);
        canvas.clipRect(0, 0, game.viewW, game.viewH);
        canvas.translate(game.ox, game.oy);
        game.render(canvas);
        canvas.restore();

        if (running) {
            postInvalidateOnAnimation();
        }
    }

    private int gx(float x) {
        return (int) ((x - destX) / k - game.ox);
    }

    private int gy(float y) {
        return (int) ((y - destY) / k - game.oy);
    }

    @Override
    public boolean onTouchEvent(MotionEvent e) {
        switch (e.getActionMasked()) {
            case MotionEvent.ACTION_DOWN:
                pointer = e.getPointerId(0);
                game.touchDown(gx(e.getX()), gy(e.getY()));
                return true;
            case MotionEvent.ACTION_POINTER_DOWN:
                game.extraTouch();
                return true;
            case MotionEvent.ACTION_MOVE: {
                int i = e.findPointerIndex(pointer);
                if (i >= 0) {
                    game.touchMove(gx(e.getX(i)), gy(e.getY(i)));
                }
                return true;
            }
            case MotionEvent.ACTION_POINTER_UP: {
                int i = e.getActionIndex();
                if (e.getPointerId(i) == pointer) {
                    game.touchUp(gx(e.getX(i)), gy(e.getY(i)));
                    pointer = -1;
                }
                return true;
            }
            case MotionEvent.ACTION_UP:
            case MotionEvent.ACTION_CANCEL: {
                int i = e.findPointerIndex(pointer);
                if (i >= 0) {
                    game.touchUp(gx(e.getX(i)), gy(e.getY(i)));
                }
                pointer = -1;
                return true;
            }
            default:
                return super.onTouchEvent(e);
        }
    }

    void resume() {
        running = true;
        lastNanos = 0;
        acc = 0;
        game.onResume();
        postInvalidateOnAnimation();
    }

    void pause() {
        running = false;
        game.onPause();
    }

    void focusLost() {
        game.autoPause();
    }

    boolean back() {
        return game.back();
    }

    void jumpKey() {
        game.jumpKey();
    }

    void release() {
        game.release();
    }
}
