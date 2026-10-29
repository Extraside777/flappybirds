package com.extraside.flappybird;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.GraphicsMode;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;

/**
 * Проганяє гру без телефона: меню, налаштування, магазин, редактор шлейфу, рекорди, гра з автопілотом,
 * пауза, смерть. Кожен екран зберігається в app/build/screens/*.png (як на телефоні 1080x2400, вдвічі менше).
 */
@RunWith(RobolectricTestRunner.class)
@Config(sdk = 34)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
public class GameRenderTest {
    // -- телефон 1080x2400: поле 400 у ширину, полотно 400x889
    private static final int VIEW_W = 400, VIEW_H = 889;
    private static final float K = 1.35f;

    private final File out = new File("build/screens");
    private Game g;

    private void shot(String name) throws IOException {
        shot(name, K, 0);
    }

    /** cutout -- px полотна згори під камерою: там малюємо чорну «дірку», щоб було видно, що HUD нижче */
    private void shot(String name, float k, int cutout) throws IOException {
        Bitmap bmp = Bitmap.createBitmap(Math.round(g.viewW * k), Math.round(g.viewH * k), Bitmap.Config.ARGB_8888);
        Canvas c = new Canvas(bmp);
        c.drawColor(Color.BLACK);
        c.scale(k, k);
        c.clipRect(0, 0, g.viewW, g.viewH);
        c.save();
        c.translate(g.ox, g.oy);
        g.render(c);
        c.restore();
        if (cutout > 0) {
            Paint p = new Paint(Paint.ANTI_ALIAS_FLAG);
            p.setColor(Color.BLACK);
            c.drawCircle(g.viewW / 2f, cutout / 2f, cutout * 0.35f, p);
        }
        out.mkdirs();
        try (FileOutputStream f = new FileOutputStream(new File(out, name + ".png"))) {
            bmp.compress(Bitmap.CompressFormat.PNG, 100, f);
        }
    }

    private void steps(int n) {
        for (int i = 0; i < n; i++) {
            g.step();
        }
    }

    private void tap(int x, int y) {
        g.touchDown(x, y);
        g.step();
        g.touchUp(x, y);
    }

    private void tap(Box b) {
        tap(b.centerX(), b.centerY());
    }

    /** автопілот: стрибає, коли пташка от-от опуститься до низу наступного проходу (стрибок -- ~76 px вгору) */
    private void autopilot(int frames) {
        for (int i = 0; i < frames && !g.over; i++) {
            Game.Pipe next = null;
            for (Game.Pipe p : g.pipes) {
                if (p.x + Game.PIPE_WIDTH > Game.BIRD_START_X - 4) {
                    next = p;
                    break;
                }
            }
            float bottom = next == null ? 450 : next.y + next.gap - 14;
            if (g.birdY + Game.BIRD_SIZE + g.birdV * 2 > bottom && g.birdV > 0) {
                g.touchDown(200, 400);
                g.touchUp(200, 400);
            }
            g.step();
        }
    }

    @Test
    public void playsThroughAllScreens() throws IOException {
        g = new Game(RuntimeEnvironment.getApplication());
        g.setView(VIEW_W, VIEW_H, 0, (VIEW_H - Game.HEIGHT) / 2, 0);
        g.progress.coins = 2000;

        steps(90);
        shot("01_menu");

        tap(g.settingsBtn);
        steps(20);
        assertTrue(g.inSettings);
        g.touchDown(Game.SLIDERS[0].x + 50, Game.SLIDERS[0].centerY());   // -- тягнемо повзунок музики
        g.touchMove(Game.SLIDERS[0].x + 150, Game.SLIDERS[0].centerY());
        g.step();
        g.touchUp(Game.SLIDERS[0].x + 150, Game.SLIDERS[0].centerY());
        tap(Game.LANG_SELECTOR.right() - 10, Game.LANG_SELECTOR.centerY());   // -- мова: інша
        steps(5);
        shot("02_settings");
        tap(Game.BACK_BTN_RECT);
        steps(20);
        assertFalse(g.inSettings);

        tap(Game.SHOP_BTN);
        steps(20);
        assertTrue(g.inShop);
        shot("03_shop_birds");
        tap(Game.SHOP_PANEL.x + 260, Game.SHOP_PANEL.y + 60);    // -- купуємо другу пташку
        steps(10);
        assertEquals("blue", g.progress.skin);
        String[] tabs = {"trails", "pipes", "backgrounds"};
        for (String tab : tabs) {
            // -- вкладки: тапаємо по кожній (рахуємо їх як у грі -- рівні частини ряду)
            int i = java.util.Arrays.asList(Game.SHOP_TAB_NAMES).indexOf(tab);
            int x = Game.SHOP_TABS_ROW.x + Game.SHOP_TABS_ROW.w * (2 * i + 1) / 8;
            tap(x, Game.SHOP_TABS_ROW.centerY());
            steps(10);
            assertEquals(tab, g.shopTab);
            if (tab.equals("pipes")) {
                tap(Game.SHOP_PANEL.x + 100, Game.SHOP_PANEL.y + 200);   // -- третій скін труб
            }
            if (tab.equals("backgrounds")) {
                tap(Game.SHOP_PANEL.x + 260, Game.SHOP_PANEL.y + 200);   // -- зима
            }
            steps(10);
            shot("04_shop_" + tab);
        }
        // -- свій шлейф: купуємо -> відкривається редактор
        tap(Game.SHOP_TABS_ROW.x + Game.SHOP_TABS_ROW.w * 3 / 8, Game.SHOP_TABS_ROW.centerY());
        steps(5);
        tap(Game.SHOP_PANEL.x + 260, Game.SHOP_PANEL.y + 200);
        steps(5);
        assertTrue(g.editing);
        tap(Game.EDIT_SLOTS[1]);
        tap(Game.PALETTE_X + 5, Game.PALETTE_Y + 5);
        tap(Game.EDIT_STYLE.right() - 10, Game.EDIT_STYLE.centerY());
        steps(40);
        shot("05_editor");
        tap(Game.EDIT_BACK_RECT);
        steps(20);
        assertFalse(g.editing);
        tap(Game.SHOP_BACK_RECT);
        steps(20);
        assertFalse(g.inShop);

        tap(Game.RECORD_BTN);
        steps(20);
        shot("06_records");
        assertTrue(g.back());
        steps(5);
        assertFalse(g.inRecords);

        // -- гра
        tap(Game.PLAY_BTN);
        for (int i = 0; i < 60 && !g.start; i++) {   // -- кнопка темнішає, екран затемнюється -- і одразу гра
            g.step();
        }
        assertTrue(g.start);
        autopilot(20);
        shot("07_game_start");
        autopilot(400);
        g.shield = true;
        g.boost[Game.SLOW] = 4;
        g.boost[Game.X2] = 8;
        autopilot(40);
        shot("08_game_powerups");
        autopilot(1200);
        assertTrue("автопілот мав пролетіти хоч кілька труб, рахунок " + g.score, g.score >= 3);
        shot("09_game_later");

        g.onPause();
        assertTrue(g.paused);
        shot("10_paused");
        tap(200, 120);
        assertFalse(g.paused);

        // -- нічний фон і падіння до смерті
        g.kit.setBackground("night");
        for (int i = 0; i < 400 && !g.over; i++) {
            g.step();
        }
        assertTrue(g.over);
        steps(60);
        shot("11_game_over");
        tap(Game.MENU_BTN_RECT);
        steps(20);
        assertFalse(g.start);
        assertTrue(g.progress.games >= 1);
        shot("12_menu_after");

        // -- широкий екран (планшет 3:4): поле по центру, небо і труби на всю ширину
        g.setView(525, 700, 62, 0, 0);
        tap(Game.PLAY_BTN);
        for (int i = 0; i < 60 && !g.start; i++) {
            g.step();
        }
        autopilot(200);
        shot("13_tablet", 1f, 0);
    }

    /**
     * Різні екрани (розмір полотна рахується як у GameView: ширина 400, а на широкому -- висота 700).
     * Земля завжди внизу, HUD і шестерня -- біля верхнього краю (під вирізом камери) і біля бокових країв,
     * місця для польоту більшає порівну зверху і знизу. Знімки -- app/build/screens/screen_*.png
     */
    @Test
    public void layoutFitsEveryScreen() throws IOException {
        // -- назва, ширина і висота полотна, виріз камери (px полотна)
        Object[][] screens = {
                {"16x9", 400, 711, 0},          // -- 720x1280, старі телефони
                {"20x9", 400, 889, 41},         // -- 1080x2400 з камерою в екрані
                {"22x9", 400, 978, 30},         // -- вузький екран, як зовнішній у розкладних
                {"tablet", 525, 700, 0},        // -- планшет 3:4
                {"fold", 583, 700, 0},          // -- розкладний телефон, внутрішній екран
        };
        for (Object[] s : screens) {
            String name = (String) s[0];
            int vw = (Integer) s[1], vh = (Integer) s[2], cutout = (Integer) s[3];
            g = new Game(RuntimeEnvironment.getApplication());
            g.setView(vw, vh, (vw - Game.WIDTH) / 2, (vh - Game.HEIGHT) / 2, cutout);
            g.progress.coins = 2000;
            int top = -g.oy, bottom = vh - g.oy, left = -g.ox, right = vw - g.ox;

            // -- земля така ж товста, як на полі 400x700, і доходить до низу екрана
            assertEquals(name, Game.HEIGHT - g.groundY, bottom - g.floorY);
            // -- додаткове місце для польоту -- порівну над трубами (стеля -- верх екрана) і під ними
            assertTrue(name, Math.abs(-top - (g.floorY - g.groundY)) <= 1);
            // -- шестерня -- на тій самій відстані від правого верхнього кута (нижче вирізу)
            assertEquals(name, Game.SETTINGS_BTN.y + cutout, g.settingsBtn.y - top);
            assertEquals(name, Game.WIDTH - Game.SETTINGS_BTN.right(), right - g.settingsBtn.right());
            // -- монетки -- біля лівого краю, так само далеко від нього, як на полі 400x700
            assertEquals(name, left, g.hudLeft);

            steps(90);
            shot("screen_" + name + "_menu", 1f, cutout);

            tap(g.settingsBtn);
            steps(20);
            assertTrue(name, g.inSettings);
            assertTrue(name, g.back());
            steps(5);

            tap(Game.PLAY_BTN);
            for (int i = 0; i < 60 && !g.start; i++) {
                g.step();
            }
            assertTrue(name, g.start);
            autopilot(300);
            g.shield = true;
            g.boost[Game.X2] = 8;
            autopilot(30);
            shot("screen_" + name + "_game", 1f, cutout);
        }
    }
}
