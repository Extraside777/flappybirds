package com.extraside.flappybird;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.ColorFilter;
import android.graphics.Paint;
import android.graphics.Rect;
import android.graphics.RectF;
import android.graphics.Typeface;

import org.json.JSONException;

import java.io.File;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;

/**
 * Уся гра -- порт src/main.py. Координати -- як у пайтоні: ігрове поле 400x700, VIEW_X (ox) -- скільки
 * полотна є ліворуч від поля. На телефоні екран вищий за поле, тому над полем ще oy px неба, а під ним --
 * землі; Canvas у render() уже зсунутий так, що (0, 0) -- лівий верхній кут поля.
 * Один виклик step() -- один кадр пайтон-версії (1/60 сек).
 */
final class Game {
    // -- віконечко: ігрове поле 400x700 завжди по центру, а небо/земля/труби тягнуться на весь екран
    static final int WIDTH = 400, HEIGHT = 700;
    static final float FPS = 60f;

    static final float GRAVITY = 0.4f;
    static final float JUMP_VELOCITY = -8f;
    static final int BIRD_START_X = 80, BIRD_START_Y = 300;
    static final int BIRD_SIZE = 30;          // -- хітбокс пташки по осі x+y
    static final float BIRD_MAX_UP = 25;      // -- градуси: наскільки пташка задирає дзьоб при стрибку
    static final float BIRD_MAX_DOWN = -75;   // -- і наскільки опускає при падінні

    // -- швидкість труб, висота проходу і відстань між трубами залежать від рівня (Levels)
    static final int PIPE_WIDTH = 70;
    static final int PIPE_GAP_LO = 225, PIPE_GAP_HI = 525;   // -- у яких межах по висоті може бути середина проходу
    static final float PIPE_SHIFT_PER_FRAME = 3.6f;

    // -- рівні
    static final float LEVEL_EASE = 1.5f;
    static final float LEVEL_BANNER_TIME = 1.8f;
    static final float LEVEL_BANNER_POP = 0.3f;
    static final int LEVEL_BANNER_Y = 150;
    static final int LEVEL_HUD_RIGHT = WIDTH - 14, LEVEL_HUD_Y = 30;
    static final int LEVEL_BAR_COLOR = Gfx.rgb(86, 180, 50), LEVEL_BAR_SHINE = Gfx.rgb(160, 225, 100);

    // -- монетки
    static final float COIN_CHANCE_GAP = 0.6f;
    static final float COIN_CHANCE_BETWEEN = 0.3f;
    static final int COIN_GAP_JITTER = 35;
    static final int COIN_HITBOX = 24;
    static final float COIN_PICKUP_TIME = 0.35f;
    static final float COIN_FPS = 10;

    // -- бонуси: щит рятує від одного удару, сповільнення пригальмовує світ, x2 -- монетка за дві
    static final float POWERUP_CHANCE = 0.18f;
    static final int POWERUP_HITBOX = 30;
    static final float POWERUP_BOB = 4;
    static final String[] BOOST_KINDS = {"slow", "x2"};
    static final float[] BOOST_TIME = {5.0f, 10.0f};
    static final int[][] BOOST_COLORS = {{Gfx.rgb(176, 112, 255), Gfx.rgb(220, 190, 255)},
            {Gfx.rgb(255, 196, 50), Gfx.rgb(255, 236, 150)}};
    static final int SLOW = 0, X2 = 1;
    static final float SLOW_FACTOR = 0.55f;
    static final int SLOW_TINT = Gfx.rgb(70, 30, 150);
    static final int SLOW_TINT_ALPHA = 45;
    static final float SHIELD_GRACE = 1.0f;
    static final float SHIELD_POP_TIME = 0.35f;
    static final int POWERUP_HUD_Y = 72;
    static final int POWERUP_HUD_STEP = 44;

    static final float TRAIL_LIFE = 0.6f;

    static final float MENU_SCROLL_SPEED = 60;
    static final float GAME_OVER_ANIM = 0.45f;

    static final float PRESS_ACTION_DELAY = 120;   // -- мс від натискання кнопки до дії (поки вона темнішає)
    static final int FADE_SPEED = 12;

    // -- хітбокси кнопок меню
    static final Box PLAY_BTN = new Box(65, 360, 270, 62);
    static final Box SHOP_BTN = new Box(65, 440, 270, 62);
    static final Box RECORD_BTN = new Box(65, 520, 270, 62);
    static final Box SETTINGS_BTN = new Box(328, 8, 56, 56);

    static final int MENU_BTN_W = 220, MENU_BTN_H = 94;

    static final int PANEL_INNER_TOP = 8;
    static final int PANEL_INNER_BOTTOM = 16;

    // -- екран після смерті
    static final int GAME_OVER_Y = 190;
    static final Box RESULT_PANEL = new Box(62, 226, 276, 192);
    static final Box MENU_BTN_RECT = Box.midTop(MENU_BTN_W, MENU_BTN_H, WIDTH / 2, RESULT_PANEL.bottom() + 34);

    // -- пауза (згорнули гру або натиснули «назад»): велика кнопка «грати» і MENU під нею
    static final Box PAUSE_PLAY = new Box(140, 230, 120, 120);
    static final Box PAUSE_MENU_RECT = Box.midTop(MENU_BTN_W, MENU_BTN_H, WIDTH / 2, PAUSE_PLAY.bottom() + 30);

    // -- екран рекордів
    static final int RECORDS_TITLE_Y = 70;
    static final Box RECORDS_PANEL = new Box(40, 112, 320, 326);

    // -- магазин: вкладки ПТАШКИ | ШЛЕЙФИ | ТРУБИ | ФОНИ, під ними вікно з картками по 2 в ряд
    static final int SHOP_TITLE_Y = 80;
    static final String[] SHOP_TAB_NAMES = {"birds", "trails", "pipes", "backgrounds"};
    static final Box SHOP_TABS_ROW = new Box(14, 106, 372, 46);
    static final int SHOP_TAB_GAP = 4;
    static final Box SHOP_PANEL = new Box(14, 156, 372, 328);
    static final int SHOP_COLS = 2;
    static final int CARD_W = 164, CARD_H = 137, CARD_GAP = 10;
    static final int CARD_PAD_TOP = 10;
    static final int SHOP_DRAG_SLOP = 8;          // -- px: далі цього палець уже гортає, а не тицяє
    static final float NOT_ENOUGH_TIME = 1.6f;
    static final int[] CARD_PREVIEW = {124, 86};
    static final int[] TRAIL_PREVIEW = {70, 60};
    static final int[] BG_THUMB = {132, 74};
    static final int[][] PIPE_PREVIEW = {{20, 4}, {77, 56}};
    static final int PIPE_PREVIEW_GAP = 30;
    static final float TAB_DIM = 0.78f;

    // -- налаштування: на телефоні нема розміру вікна, тому 4 рядки (мова + 3 повзунки гучності)
    static final int SETTINGS_TITLE_Y = 96;
    static final Box SETTINGS_PANEL = new Box(24, 130, 352, 362);
    static final int ROW_Y0 = SETTINGS_PANEL.y + 20;
    static final int ROW_H = 84;
    static final String[] ROWS = {"language", "menu_music", "game_music", "sounds"};
    static final Box LANG_SELECTOR = new Box(52, ROW_Y0 + 30, 296, 44);
    static final int SELECTOR_ARROW = 46;
    static final String[] SLIDER_NAMES = {"menu_music", "game_music", "sfx"};
    static final Box[] SLIDERS = {
            new Box(58, ROW_Y0 + ROW_H + 46, 214, 16),
            new Box(58, ROW_Y0 + 2 * ROW_H + 46, 214, 16),
            new Box(58, ROW_Y0 + 3 * ROW_H + 46, 214, 16),
    };
    static final int SLIDER_GRAB = 14;
    static final Box BACK_BTN_RECT = Box.midTop(MENU_BTN_W, MENU_BTN_H, WIDTH / 2, SETTINGS_PANEL.bottom() + 6);
    static final Box RECORDS_BACK_RECT = Box.midTop(MENU_BTN_W, MENU_BTN_H, WIDTH / 2, RECORDS_PANEL.bottom() + 14);
    static final Box SHOP_BACK_RECT = Box.midTop(MENU_BTN_W, MENU_BTN_H, WIDTH / 2, SHOP_PANEL.bottom() + 24);

    // -- редактор свого шлейфу
    static final int EDIT_TITLE_Y = 56;
    static final Box EDIT_PANEL = new Box(24, 86, 352, 430);
    static final Box EDIT_PREVIEW = new Box(46, 104, 308, 100);
    static final int EDIT_BIRD_X = EDIT_PREVIEW.right() - 64;
    static final float EDIT_BIRD_BOB = 10;
    static final int EDIT_LABEL_X = EDIT_PANEL.x + 26;
    static final Box[] EDIT_SLOTS = {new Box(232, 222, 44, 28), new Box(306, 222, 44, 28)};
    static final int PALETTE_COLS = 8;
    static final int SWATCH_W = 28, SWATCH_H = 24, SWATCH_GAP = 10;
    static final int PALETTE_X = WIDTH / 2 - (PALETTE_COLS * SWATCH_W + (PALETTE_COLS - 1) * SWATCH_GAP) / 2;
    static final int PALETTE_Y = 266;
    static final int EDIT_STYLE_Y = 332;
    static final Box EDIT_STYLE = new Box(52, EDIT_STYLE_Y + 30, 296, 44);
    static final int EDIT_WIDTH_Y = 416;
    static final Box EDIT_WIDTH = new Box(58, EDIT_WIDTH_Y + 46, 214, 16);
    static final Box EDIT_BACK_RECT = Box.midTop(MENU_BTN_W, MENU_BTN_H, WIDTH / 2, EDIT_PANEL.bottom() + 6);

    static final Box COINS_CHIP = new Box(10, 12, 128, 46);

    static final float MUSIC_MAX_VOLUME = 0.5f;
    static final float SFX_MAX_VOLUME = 0.6f;

    // -- кольори
    static final int COLOR_TEXT_SHADOW = Gfx.rgb(65, 40, 70);
    static final int COLOR_TEXT_MAIN = Gfx.rgb(255, 255, 255);
    static final float PRESS_OVERLAY_MAX_ALPHA = 70;
    static final int COLOR_OUTLINE = Gfx.rgb(45, 16, 40);
    static final int COLOR_SLIDER_BACK = Gfx.rgb(150, 96, 60);
    static final int COLOR_SLIDER_FILL = Gfx.rgb(86, 180, 50);
    static final int COLOR_SLIDER_SHINE = Gfx.rgb(160, 225, 100);
    static final int COLOR_KNOB = Gfx.rgb(255, 236, 200);
    static final int COLOR_KNOB_SHADE = Gfx.rgb(240, 180, 90);
    static final int COLOR_ARROW = Gfx.rgb(70, 175, 50);
    static final int COLOR_ARROW_HOVER = Gfx.rgb(120, 215, 80);
    static final int COLOR_CARD_HOVER = Gfx.rgb(255, 255, 255);

    // -- об'єкти на полі
    static final class Pipe {
        float x;
        final int y, gap;          // -- верх проходу і його висота
        boolean passed;

        Pipe(float x, int y, int gap) {
            this.x = x;
            this.y = y;
            this.gap = gap;
        }
    }

    static final class Coin {
        float x, y;
        final float phase;
        boolean taken;
        float takenT;              // -- час після підбору
        int value = 1;             // -- скільки дала монет

        Coin(float x, float y, float phase) {
            this.x = x;
            this.y = y;
            this.phase = phase;
        }
    }

    static final class Powerup {
        float x, y;
        final String kind;
        final float phase;
        boolean taken;
        float takenT;

        Powerup(float x, float y, String kind, float phase) {
            this.x = x;
            this.y = y;
            this.kind = kind;
            this.phase = phase;
        }
    }

    // -- сервіси
    private final File settingsFile, saveFile;
    final Store.Config config;
    final Store.Progress progress;
    final SpriteKit kit;
    final Scenery scenery;
    final Audio.Music music;
    final Audio.Sounds sfx;
    final int groundY;
    private final Paint titlePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint panelPaint = new Paint();
    private final ColorFilter tabDim = Gfx.darken(TAB_DIM);
    private final Random rnd = new Random();
    private final Trail.Points pts = new Trail.Points();
    private final LinkedHashMap<String, Ui.SpriteButton> menuSprites = new LinkedHashMap<>();
    private final LinkedHashMap<String, Box> menuButtons = new LinkedHashMap<>();
    private final HashMap<String, Rect> previewBoxes = new HashMap<>();

    // -- розмір полотна
    int viewW = WIDTH, viewH = HEIGHT, ox = 0, oy = 0;

    // -- стан гри
    float birdY = BIRD_START_Y;
    float birdV = 0;
    final List<Pipe> pipes = new ArrayList<>();
    final List<Coin> coins = new ArrayList<>();
    final List<Powerup> powerups = new ArrayList<>();
    int score = 0;
    int level = 0;
    float levelSpeed = Levels.LEVELS[0].speed;
    float levelTime = LEVEL_BANNER_TIME;
    int runCoins = 0;
    boolean shield = false;
    float grace = 0f;
    final float[] boost = new float[BOOST_KINDS.length];
    final List<float[]> trailPts = new ArrayList<>();   // -- x, y, вік, випадкове 0..1
    float speedK = 1f;
    final List<float[]> pops = new ArrayList<>();       // -- x, y, час після удару
    boolean newRecord = false;
    boolean runSaved = true;

    boolean start = false;
    boolean over = false;
    boolean paused = false;

    boolean inSettings = false;
    boolean inRecords = false;
    boolean inShop = false;
    String shopTab = "birds";
    int shopScroll = 0;
    boolean editing = false;
    int editSlot = 0;
    final List<float[]> editPts = new ArrayList<>();
    float notEnough = 0f;
    String dragging = null;

    String pressed = null;
    float pressTime = 0;
    float pressProgress = 0;

    int fade = 0;
    boolean fading = false;

    float tTotal = 0f;
    float overTime = 0f;
    float dts = 1f / FPS;

    // -- палець: де він зараз (для «наведення» на кнопки) і чи гортає магазин
    private boolean touching = false;
    private int touchX, touchY;
    private boolean shopTouch = false, shopDragged = false;
    private int shopTouchX, shopTouchY, shopScrollStart;

    Game(Context ctx) {
        settingsFile = new File(ctx.getFilesDir(), "settings.json");
        saveFile = new File(ctx.getFilesDir(), "save.json");
        config = Store.loadConfig(settingsFile);
        progress = Store.loadProgress(saveFile);

        Assets assets = new Assets(ctx.getAssets(), "sprites");
        try {
            kit = new SpriteKit(assets, PRESS_OVERLAY_MAX_ALPHA / 255f);
        } catch (JSONException e) {
            throw new IllegalStateException("битий manifest.json / extra.json", e);
        }
        scenery = kit.scenery;
        kit.setLang(config.lang);
        config.lang = kit.lang;

        // -- скін: стара гра могла зберегти пташку, якої вже нема -- тоді класична
        fixOwned(progress.owned, "classic");
        if (!progress.owned.contains(progress.skin)) {
            progress.skin = "classic";
        }
        progress.skin = kit.setSkin(progress.skin);
        fixOwned(progress.ownedTrails, "none");
        if (!progress.ownedTrails.contains(progress.trail)) {
            progress.trail = "none";
        }
        progress.trail = kit.setTrail(progress.trail);
        fixOwned(progress.ownedBackgrounds, "day");
        if (!progress.ownedBackgrounds.contains(progress.background)) {
            progress.background = "day";
        }
        progress.background = kit.setBackground(progress.background);
        fixOwned(progress.ownedPipes, "classic");
        if (!progress.ownedPipes.contains(progress.pipe)) {
            progress.pipe = "classic";
        }
        progress.pipe = kit.setPipe(progress.pipe);
        // -- свій шлейф: номери кольорів -- у межах палітри, стиль -- з відомих; редактор міняє ці налаштування
        Store.TrailConfig custom = progress.customTrail;
        custom.c1 = Trail.mod(custom.c1, Trail.PALETTE.length);
        custom.c2 = Trail.mod(custom.c2, Trail.PALETTE.length);
        if (indexOf(Trail.STYLES, custom.style) < 0) {
            custom.style = new Store.TrailConfig().style;
        }
        kit.customTrail.config = custom;
        groundY = kit.groundY;

        Map<String, String> tracks = new HashMap<>();
        tracks.put("menu", "music/menu.mp3");
        tracks.put("game", "music/game.mp3");
        music = new Audio.Music(ctx.getAssets(), tracks, MUSIC_MAX_VOLUME);
        music.setLevel("menu", config.menuMusic);
        music.setLevel("game", config.gameMusic);

        Map<String, String> sounds = new HashMap<>();
        for (String name : new String[]{"coin", "powerup", "shield_break", "level_up"}) {
            sounds.put(name, "sounds/" + name + ".wav");
        }
        sfx = new Audio.Sounds(ctx.getAssets(), sounds, SFX_MAX_VOLUME);
        sfx.setLevel(config.sfx);

        titlePaint.setTypeface(Typeface.createFromAsset(ctx.getAssets(), "fonts/OutlineStyleRegular.ttf"));
        titlePaint.setTextSize(48);
        titlePaint.setTextAlign(Paint.Align.CENTER);

        // -- який спрайт малює яку кнопку меню і їхні хітбокси
        menuSprites.put("play", kit.play);
        menuSprites.put("shop", kit.shop);
        menuSprites.put("record", kit.record);
        menuSprites.put("settings", kit.settings);
        menuButtons.put("play", PLAY_BTN);
        menuButtons.put("shop", SHOP_BTN);
        menuButtons.put("record", RECORD_BTN);
        menuButtons.put("settings", SETTINGS_BTN);

        newPipes();
    }

    private static void fixOwned(List<String> owned, String free) {
        if (!owned.contains(free)) {
            owned.add(0, free);
        }
    }

    private static int indexOf(String[] arr, String v) {
        for (int i = 0; i < arr.length; i++) {
            if (arr[i].equals(v)) {
                return i;
            }
        }
        return -1;
    }

    private int randint(int lo, int hi) {
        return lo + rnd.nextInt(hi - lo + 1);
    }

    /** розмір полотна змінився (повернули екран, інший телефон) */
    void setView(int viewW, int viewH, int ox, int oy) {
        this.viewW = viewW;
        this.viewH = viewH;
        this.ox = ox;
        this.oy = oy;
        scenery.setView(viewW, ox, oy, viewH - HEIGHT - oy);
        fillPipes();
    }

    // -- доп функціонал
    /** нова труба (прохід -- як на поточному рівні) + можливо монетки: у проході і між нею та попередньою трубою */
    private void addPipe(float x) {
        Levels.Level lv = Levels.LEVELS[level];
        int lo = PIPE_GAP_LO, hi = PIPE_GAP_HI;
        Pipe prev = pipes.isEmpty() ? null : pipes.get(pipes.size() - 1);
        if (prev != null) {
            int shift = Math.round(PIPE_SHIFT_PER_FRAME * lv.spacing / lv.speed);
            int prevMid = prev.y + prev.gap / 2;
            lo = Math.max(lo, prevMid - shift);
            hi = Math.min(hi, prevMid + shift);
        }
        int gapMid = randint(lo, hi);
        pipes.add(new Pipe(x, gapMid - lv.gap / 2, lv.gap));

        if (rnd.nextFloat() < COIN_CHANCE_GAP) {
            int cy = gapMid + randint(-COIN_GAP_JITTER, COIN_GAP_JITTER);
            coins.add(new Coin(x + PIPE_WIDTH / 2f, cy, rnd.nextFloat() * 8));
        }

        if (prev == null) {
            return;
        }
        float midX = (prev.x + x) / 2 + PIPE_WIDTH / 2f;
        float midY = (prev.y + prev.gap / 2f + gapMid) / 2 + randint(-30, 30);
        List<String> kinds = freePowerups();
        if (!kinds.isEmpty() && rnd.nextFloat() < POWERUP_CHANCE) {
            powerups.add(new Powerup(midX, midY, kinds.get(rnd.nextInt(kinds.size())), rnd.nextFloat() * 6));
        } else if (rnd.nextFloat() < COIN_CHANCE_BETWEEN) {
            coins.add(new Coin(midX, midY, rnd.nextFloat() * 8));
        }
    }

    /** які бонуси можна поставити: не той, що вже діє, і не той, що вже чекає на полі */
    private List<String> freePowerups() {
        List<String> waiting = new ArrayList<>();
        for (Powerup p : powerups) {
            if (!p.taken) {
                waiting.add(p.kind);
            }
        }
        List<String> kinds = new ArrayList<>();
        if (!shield && !waiting.contains("shield")) {
            kinds.add("shield");
        }
        for (int i = 0; i < BOOST_KINDS.length; i++) {
            if (boost[i] <= 0 && !waiting.contains(BOOST_KINDS[i])) {
                kinds.add(BOOST_KINDS[i]);
            }
        }
        return kinds;
    }

    /** бонус гойдається вгору-вниз (і хітбокс разом з ним) */
    private float powerupY(Powerup p) {
        return p.y + (float) Math.sin(tTotal * 3 + p.phase) * POWERUP_BOB;
    }

    /** труби, поки не заповнимо все видиме полотно праворуч (на широкому екрані їх більше) */
    private void fillPipes() {
        int right = WIDTH + ox;
        while (pipes.isEmpty() || pipes.get(pipes.size() - 1).x <= right) {
            addPipe(pipes.isEmpty() ? WIDTH : pipes.get(pipes.size() - 1).x + Levels.LEVELS[level].spacing);
        }
    }

    private void newPipes() {
        pipes.clear();
        coins.clear();
        powerups.clear();
        fillPipes();
    }

    /** текст + тінь, по центру (x, y) */
    private void drawText(Canvas c, String text, float x, float y) {
        Paint.FontMetrics fm = titlePaint.getFontMetrics();
        float base = y - (fm.ascent + fm.descent) / 2;
        titlePaint.setColor(COLOR_TEXT_SHADOW);
        c.drawText(text, x + 2, base + 3, titlePaint);
        titlePaint.setColor(COLOR_TEXT_MAIN);
        c.drawText(text, x, base, titlePaint);
    }

    /** спрайт пташки по центру хітбокса, нахил залежить від швидкості */
    private void drawBird(Canvas c, float x, float y, float v) {
        float angle = Math.max(BIRD_MAX_DOWN, Math.min(BIRD_MAX_UP, -v * 4));
        float cx = x + BIRD_SIZE / 2f, cy = y + BIRD_SIZE / 2f;
        // -- після удару щитом пташка блимає, поки невразлива
        if (!(grace > 0 && !over && ((int) (grace * 12)) % 2 == 1)) {
            kit.bird.draw(c, cx, cy, angle);
        }
        if (shield) {
            Gfx.blitCenter(c, kit.aura.frame(), cx, cy);
        }
        // -- лопнутий щит: бульбашка роздувається і зникає
        for (float[] p : pops) {
            float k = p[2] / SHIELD_POP_TIME;
            Gfx.blitScaledCenter(c, kit.aura.frames[0], p[0], p[1], 1 + 0.6f * k, (int) (255 * (1 - k)), false);
        }
    }

    /** бонуси на полі (на всьому полотні, як монетки); підібраний -- летить вгору і зникає */
    private void drawPowerups(Canvas c) {
        for (Powerup p : powerups) {
            Bitmap img = kit.powerups.get(p.kind).frame();
            if (!p.taken) {
                Gfx.blitCenter(c, img, (int) p.x, (int) powerupY(p));
            } else {
                float k = p.takenT / COIN_PICKUP_TIME;
                Gfx.blitScaledCenter(c, img, (int) p.x, (int) (p.y - 34 * k), 1 + 0.5f * k, (int) (255 * (1 - k)), false);
            }
        }
    }

    /** активні бонуси під лічильником монет: щит -- іконка, сповільнення і x2 -- іконка і смужка часу */
    private void drawPowerupHud(Canvas c) {
        int x = 10, y = POWERUP_HUD_Y;
        if (shield) {
            Bitmap img = kit.powerups.get("shield").frames[0];
            Gfx.blit(c, img, x, y - img.getHeight() / 2);
            y += POWERUP_HUD_STEP;
        }
        for (int i = 0; i < BOOST_KINDS.length; i++) {
            float left = boost[i];
            if (left <= 0) {
                continue;
            }
            Bitmap img = kit.powerups.get(BOOST_KINDS[i]).frame();
            Gfx.blit(c, img, x, y - img.getHeight() / 2);
            if (!(left < 1.5f && ((int) (left * 8)) % 2 == 1)) {
                drawTimerBar(c, new Box(x + img.getWidth() + 6, y - 5, 60, 10), left / BOOST_TIME[i],
                        BOOST_COLORS[i][0], BOOST_COLORS[i][1]);
            }
            y += POWERUP_HUD_STEP;
        }
    }

    /** рахунок дійшов до наступного рівня: нові труби вже як на ньому, світ поступово розганяється */
    private void levelUp() {
        level = Levels.levelFor(score);
        levelTime = 0f;
        sfx.play("level_up");
    }

    /** поточний рівень праворуч угорі, під ним -- смужка, скільки лишилось до наступного */
    private void drawLevelHud(Canvas c) {
        int right = LEVEL_HUD_RIGHT, y = LEVEL_HUD_Y;
        Bitmap label = kit.text("level");
        String num = String.valueOf(level + 1);
        int w = label.getWidth() + 6 + kit.numberWidth(num);
        Gfx.blit(c, label, right - w, y - label.getHeight() / 2);
        kit.drawNumber(c, num, right, y, "light", 1, 2, 255);
        if (level + 1 < Levels.LEVELS.length) {
            int lo = Levels.LEVELS[level].score, hi = Levels.LEVELS[level + 1].score;
            drawTimerBar(c, new Box(right - w + 3, y + 22, w - 6, 8), (score - lo) / (float) (hi - lo),
                    LEVEL_BAR_COLOR, LEVEL_BAR_SHINE);
        }
    }

    /** на початку рівня посеред екрана вискакує «РІВЕНЬ 2» (росте з пружинкою), трохи висить і тане */
    private void drawLevelBanner(Canvas c) {
        if (levelTime >= LEVEL_BANNER_TIME) {
            return;
        }
        Bitmap label = kit.text("level_title");
        String num = String.valueOf(level + 1);
        int gap = 14;
        int numW = kit.numberWidth(num, "title", 2), numH = kit.digitHeight("title");
        int w = label.getWidth() + gap + numW, h = Math.max(label.getHeight(), numH);
        float k = Math.min(1f, levelTime / LEVEL_BANNER_POP);
        float s = 1 + 2.7f * (k - 1) * (k - 1) * (k - 1) + 1.7f * (k - 1) * (k - 1);   // -- ease-out-back
        int sw = w, sh = h;
        if (k < 1) {
            sw = Math.max(1, (int) (w * s));
            sh = Math.max(1, (int) (h * s));
        }
        int alpha = (int) (255 * Math.min(1f, (LEVEL_BANNER_TIME - levelTime) / 0.4f));
        c.save();
        c.translate(WIDTH / 2 - sw / 2, LEVEL_BANNER_Y - sh / 2);
        c.scale(sw / (float) w, sh / (float) h);
        Gfx.blit(c, label, 0, (h - label.getHeight()) / 2, alpha);
        kit.drawNumber(c, num, label.getWidth() + gap, (h - numH) / 2 + numH / 2, "title", -1, 2, alpha);
        c.restore();
    }

    private void drawTimerBar(Canvas c, Box bar, float value, int color, int shine) {
        int fillW = (int) (bar.w * value);
        Gfx.roundRect(c, COLOR_OUTLINE, bar.inflate(6, 6), 6);
        Gfx.roundRect(c, COLOR_SLIDER_BACK, bar, 4);
        if (fillW > 0) {
            Gfx.roundRect(c, color, bar.x, bar.y, fillW, bar.h, 4);
            Gfx.fill(c, shine, bar.x + 2, bar.y + 2, Math.max(0, fillW - 4), 2);
        }
    }

    /** поки діє сповільнення, все трохи фіолетовіє (плавно з'являється і зникає разом зі швидкістю) */
    private void drawSlowTint(Canvas c) {
        float k = (1 - speedK) / (1 - SLOW_FACTOR);
        if (k < 0.02f) {
            return;
        }
        c.drawColor(Gfx.withAlpha(SLOW_TINT, (int) (SLOW_TINT_ALPHA * Math.min(1f, k))));
    }

    private void takePowerup(String kind) {
        if (kind.equals("shield")) {
            shield = true;
        } else {
            int i = indexOf(BOOST_KINDS, kind);
            boost[i] = BOOST_TIME[i];
        }
        sfx.play("powerup");
    }

    /** удар об трубу / землю / стелю: щит лопає і дає секунду невразливості, без щита -- кінець гри */
    private void hit() {
        if (grace > 0) {
            return;
        }
        if (shield) {
            shield = false;
            grace = SHIELD_GRACE;
            pops.add(new float[]{BIRD_START_X + BIRD_SIZE / 2f, birdY + BIRD_SIZE / 2f, 0f});
            sfx.play("shield_break");
        } else {
            over = true;
        }
    }

    /** монетки малюються на всьому полотні (як і труби) */
    private void drawCoins(Canvas c) {
        Bitmap[] frames = kit.coin.frames;
        for (Coin coin : coins) {
            Bitmap img = frames[((int) (tTotal * COIN_FPS + coin.phase)) % frames.length];
            if (!coin.taken) {
                Gfx.blitCenter(c, img, (int) coin.x, (int) coin.y);
            } else {
                // -- підібрана: летить вгору, трохи росте і зникає
                float k = coin.takenT / COIN_PICKUP_TIME;
                Gfx.blitScaledCenter(c, img, (int) coin.x, (int) (coin.y - 34 * k), 1 + 0.5f * k, (int) (255 * (1 - k)), false);
                if (coin.value > 1) {               // -- з x2 над монеткою вилітає «+2»
                    kit.drawNumber(c, "+" + coin.value, (int) coin.x, (int) (coin.y - 22 - 40 * k), "light", 0, 2,
                            (int) (255 * (1 - k * k)));
                }
            }
        }
    }

    private int counterWidth(Bitmap icon, String value) {
        return icon.getWidth() + 6 + kit.numberWidth(value);
    }

    /** іконка + число (світлі цифри), x -- лівий край, y -- центр */
    private void drawCounter(Canvas c, Bitmap icon, String value, int x, int y) {
        Gfx.blitCenter(c, icon, x + icon.getWidth() / 2, y);
        kit.drawNumber(c, value, x + icon.getWidth() + 6, y, "light", -1, 2, 255);
    }

    /** рядок панелі: підпис зліва, значення (і іконка) справа, все по центру y */
    private void drawRow(Canvas c, Box panel, int y, String key, String value, Bitmap icon) {
        Bitmap label = kit.text(key);
        Gfx.blit(c, label, panel.x + 26, y - label.getHeight() / 2);
        if (icon == null) {
            kit.drawNumber(c, value, panel.right() - 26, y, "light", 1, 2, 255);
        } else {
            drawCounter(c, icon, value, panel.right() - 26 - counterWidth(icon, value), y);
        }
    }

    /** y центрів n рядків, рівномірно всередині панелі */
    private static int[] panelRows(Box panel, int n) {
        int top = panel.y + PANEL_INNER_TOP;
        int h = panel.h - PANEL_INNER_TOP - PANEL_INNER_BOTTOM;
        int[] out = new int[n];
        for (int i = 0; i < n; i++) {
            out[i] = Math.round(top + h * (i + 0.5f) / n);
        }
        return out;
    }

    private void drawPanel(Canvas c, Box r) {
        Gfx.blit(c, kit.panel.render(r.w, r.h), r.x, r.y);
    }

    /** смерть: оновлюємо рекорд і зберігаємо прогрес */
    private void finishRun() {
        if (runSaved) {
            return;
        }
        newRecord = score > progress.best;
        if (newRecord) {
            progress.best = score;
        }
        progress.games += 1;
        Store.save(saveFile, progress);
        runSaved = true;
    }

    // -- налаштування
    private static float sliderValue(Box rect, float mouseX) {
        return Math.max(0f, Math.min(1f, (mouseX - rect.x) / rect.w));
    }

    private static float round2(float v) {
        return Math.round(v * 100) / 100f;
    }

    /** повзунок, який тягнуть: гучність у налаштуваннях або товщина свого шлейфу в редакторі */
    private void dragSlider(String name, float mouseX) {
        if (name.equals("trail_width")) {
            kit.customTrail.config.width = round2(sliderValue(EDIT_WIDTH, mouseX));
        } else {
            setSlider(name, sliderValue(SLIDERS[indexOf(SLIDER_NAMES, name)], mouseX));
        }
    }

    private void setSlider(String name, float value) {
        config.set(name, round2(value));
        if (name.equals("sfx")) {
            sfx.setLevel(config.sfx);
        } else {
            music.setLevel(name.split("_")[0], config.get(name));
        }
    }

    /** перемикає мову вперед/назад по колу */
    private void langStep(int step) {
        int i = Math.max(0, indexOf(SpriteKit.LANGS, config.lang));
        String value = SpriteKit.LANGS[Trail.mod(i + step, SpriteKit.LANGS.length)];
        config.lang = value;
        kit.setLang(value);
        Store.save(settingsFile, config);
    }

    private void drawSliderBar(Canvas c, Box rect, float value, int numberX) {
        int fillW = (int) (rect.w * value);

        Gfx.roundRect(c, COLOR_OUTLINE, rect.inflate(6, 6), 6);
        Gfx.roundRect(c, COLOR_SLIDER_BACK, rect, 4);
        if (fillW > 0) {
            Gfx.roundRect(c, COLOR_SLIDER_FILL, rect.x, rect.y, fillW, rect.h, 4);
            Gfx.fill(c, COLOR_SLIDER_SHINE, rect.x + 3, rect.y + 3, Math.max(0, fillW - 6), 3);
        }

        // -- ручка
        Box knob = new Box(rect.x + fillW - 11, rect.centerY() - 15, 22, 30);
        Gfx.roundRect(c, COLOR_OUTLINE, knob.inflate(6, 6), 7);
        Gfx.roundRect(c, COLOR_KNOB_SHADE, knob, 5);
        Gfx.roundRect(c, COLOR_KNOB, knob.x, knob.y, knob.w, knob.h - 6, 5);

        kit.drawNumber(c, Math.round(value * 100) + "%", numberX, rect.centerY(), "dark", 0, 2, 255);
    }

    /** зелений трикутник-стрілка з контуром (як іконка PLAY) */
    private void drawArrow(Canvas c, float cx, float cy, int dir, boolean hover) {
        float w = 12, h = 14;
        Gfx.polygon(c, COLOR_OUTLINE, cx - w * dir, cy - h, cx + w * dir, cy, cx - w * dir, cy + h);
        Gfx.polygon(c, hover ? COLOR_ARROW_HOVER : COLOR_ARROW,
                cx - (w - 4) * dir, cy - h + 6, cx + (w - 5) * dir, cy, cx - (w - 4) * dir, cy + h - 6);
    }

    /** панель перемикача зі стрілками < ... >, посередині -- картинка label */
    private void drawSelectorBox(Canvas c, Box rect, Bitmap label) {
        drawPanel(c, rect);
        if (label != null) {
            Gfx.blitCenter(c, label, rect.centerX(), rect.centerY() - 1);
        }
        Box left = new Box(rect.x, rect.y, SELECTOR_ARROW, rect.h);
        Box right = new Box(rect.right() - SELECTOR_ARROW, rect.y, SELECTOR_ARROW, rect.h);
        drawArrow(c, left.centerX() + 2, rect.centerY() - 1, -1, hover(left));
        drawArrow(c, right.centerX() - 2, rect.centerY() - 1, 1, hover(right));
    }

    private void drawSettings(Canvas c) {
        Gfx.blitCenter(c, kit.text("settings"), WIDTH / 2, SETTINGS_TITLE_Y);
        drawPanel(c, SETTINGS_PANEL);

        for (int i = 0; i < ROWS.length; i++) {
            Gfx.blit(c, kit.text(ROWS[i]), SETTINGS_PANEL.x + 26, ROW_Y0 + i * ROW_H);
        }
        drawSelectorBox(c, LANG_SELECTOR, kit.langNames.get(config.lang));
        for (int i = 0; i < SLIDERS.length; i++) {
            drawSliderBar(c, SLIDERS[i], config.get(SLIDER_NAMES[i]), SETTINGS_PANEL.right() - 44);
        }
    }

    private void settingsClick(int x, int y) {
        if (LANG_SELECTOR.contains(x, y)) {
            langStep(x < LANG_SELECTOR.x + SELECTOR_ARROW ? -1 : 1);
            return;
        }
        for (int i = 0; i < SLIDERS.length; i++) {
            if (SLIDERS[i].inflate(SLIDER_GRAB * 2, SLIDER_GRAB * 2).contains(x, y)) {
                dragging = SLIDER_NAMES[i];
                dragSlider(dragging, x);
                return;
            }
        }
        if (BACK_BTN_RECT.contains(x, y)) {
            press("back");
        }
    }

    private void press(String name) {
        pressed = name;
        pressTime = 0;
    }

    // -- екрани
    /** монетки зліва вгорі (валюта магазину) */
    private void drawMenuCounters(Canvas c) {
        drawPanel(c, COINS_CHIP);
        drawCounter(c, kit.coinIcon, String.valueOf(progress.coins), COINS_CHIP.x + 12, COINS_CHIP.centerY() - 3);
    }

    /** панель після смерті: рахунок, рекорд, монетки за гру */
    private void drawResult(Canvas c, int slide) {
        Box panel = RESULT_PANEL.move(0, slide);
        drawPanel(c, panel);

        int[] ys = panelRows(panel, 4);
        drawRow(c, panel, ys[0], "score", String.valueOf(score), null);
        drawRow(c, panel, ys[1], "level", String.valueOf(level + 1), null);
        drawRow(c, panel, ys[2], "best", String.valueOf(progress.best), null);
        drawRow(c, panel, ys[3], "coins", "+" + runCoins, kit.coinIcon);

        if (newRecord) {
            int bob = Math.round((float) Math.sin(tTotal * 6) * 3);
            Gfx.blitCenter(c, kit.text("new_record"), WIDTH / 2, panel.bottom() + 16 + bob);
        }
    }

    /** екран рекордів: кубок, найкращий рахунок великими цифрами, скільки ігор і монет */
    private void drawRecords(Canvas c) {
        Gfx.blitCenter(c, kit.text("records"), WIDTH / 2, RECORDS_TITLE_Y);
        Box panel = RECORDS_PANEL;
        drawPanel(c, panel);

        Bitmap trophy = kit.trophyBig;
        int bob = Math.round((float) Math.sin(tTotal * 2.4f) * 3);
        Gfx.blitCenter(c, trophy, WIDTH / 2, panel.y + 26 + trophy.getHeight() / 2 + bob);
        kit.drawNumber(c, String.valueOf(progress.best), WIDTH / 2, panel.y + 150, "big", 0, 3, 255);

        Box rows = new Box(panel.x, panel.y + 190, panel.w, panel.h - 190);
        int[] ys = panelRows(rows, 2);
        Gfx.line(c, COLOR_KNOB_SHADE, panel.x + 24, rows.y, panel.right() - 24, rows.y, 2);
        drawRow(c, panel, ys[0], "games", String.valueOf(progress.games), null);
        drawRow(c, panel, ys[1], "coins", String.valueOf(progress.coins), kit.coinIcon);
    }

    // -- магазин: на кожній вкладці -- що продається, де в збереженні обране і куплене
    private List<? extends ShopItem> shopItems(String tab) {
        switch (tab) {
            case "birds":
                return kit.skins;
            case "trails":
                return kit.trails;
            case "pipes":
                return kit.pipes;
            default:
                return kit.backgrounds;
        }
    }

    private String shopPick(String tab) {
        switch (tab) {
            case "birds":
                return progress.skin;
            case "trails":
                return progress.trail;
            case "pipes":
                return progress.pipe;
            default:
                return progress.background;
        }
    }

    private List<String> shopOwned(String tab) {
        switch (tab) {
            case "birds":
                return progress.owned;
            case "trails":
                return progress.ownedTrails;
            case "pipes":
                return progress.ownedPipes;
            default:
                return progress.ownedBackgrounds;
        }
    }

    private void shopSelect(String tab, String id) {
        switch (tab) {
            case "birds":
                progress.skin = kit.setSkin(id);
                break;
            case "trails":
                progress.trail = kit.setTrail(id);
                break;
            case "pipes":
                progress.pipe = kit.setPipe(id);
                break;
            default:
                progress.background = kit.setBackground(id);
        }
    }

    /**
     * прямокутники вкладок в один ряд: написи різної довжини (і на кожній мові свої),
     * тому кожна вкладка ширша за свій напис на однаковий запас
     */
    private LinkedHashMap<String, Box> shopTabs() {
        int sum = 0;
        int[] widths = new int[SHOP_TAB_NAMES.length];
        for (int i = 0; i < widths.length; i++) {
            widths[i] = kit.text("tab_" + SHOP_TAB_NAMES[i]).getWidth();
            sum += widths[i];
        }
        float pad = (SHOP_TABS_ROW.w - SHOP_TAB_GAP * (widths.length - 1) - sum) / (float) widths.length;
        LinkedHashMap<String, Box> rects = new LinkedHashMap<>();
        float x = SHOP_TABS_ROW.x;
        for (int i = 0; i < widths.length; i++) {
            int l = Math.round(x);
            rects.put(SHOP_TAB_NAMES[i], new Box(l, SHOP_TABS_ROW.y, Math.round(x + widths[i] + pad) - l, SHOP_TABS_ROW.h));
            x += widths[i] + pad + SHOP_TAB_GAP;
        }
        return rects;
    }

    /** прямокутник i-ї картки поточної вкладки з урахуванням прокрутки */
    private Box shopCard(int i) {
        int x0 = SHOP_PANEL.x + (SHOP_PANEL.w - SHOP_COLS * CARD_W - (SHOP_COLS - 1) * CARD_GAP) / 2;
        int y0 = SHOP_PANEL.y + CARD_PAD_TOP - shopScroll;
        int row = i / SHOP_COLS, col = i % SHOP_COLS;
        return new Box(x0 + col * (CARD_W + CARD_GAP), y0 + row * (CARD_H + CARD_GAP), CARD_W, CARD_H);
    }

    /** видима частина вікна магазину (все, що нижче/вище -- обрізається) */
    private static Box shopView() {
        return new Box(SHOP_PANEL.x, SHOP_PANEL.y + PANEL_INNER_TOP,
                SHOP_PANEL.w, SHOP_PANEL.h - PANEL_INNER_TOP - PANEL_INNER_BOTTOM);
    }

    private int shopMaxScroll() {
        int rows = (shopItems(shopTab).size() + SHOP_COLS - 1) / SHOP_COLS;
        int content = CARD_PAD_TOP * 2 + rows * CARD_H + (rows - 1) * CARD_GAP;
        return Math.max(0, content - shopView().h);
    }

    /**
     * тап по вкладці -- перемикаємо; по картці -- купити (якщо вистачає монет) або обрати.
     * Свій шлейф: щойно купили або тапнули по вже обраному -- відкривається редактор
     */
    private void shopClick(int x, int y) {
        for (Map.Entry<String, Box> e : shopTabs().entrySet()) {
            if (e.getValue().contains(x, y)) {
                shopTab = e.getKey();
                shopScroll = 0;
                notEnough = 0f;
                return;
            }
        }
        if (!shopView().contains(x, y)) {
            return;
        }
        List<? extends ShopItem> items = shopItems(shopTab);
        List<String> owned = shopOwned(shopTab);
        for (int i = 0; i < items.size(); i++) {
            ShopItem item = items.get(i);
            if (!shopCard(i).contains(x, y)) {
                continue;
            }
            boolean edit = item == kit.customTrail && shopPick(shopTab).equals(item.id());
            if (!owned.contains(item.id())) {
                if (progress.coins < item.price()) {
                    notEnough = NOT_ENOUGH_TIME;
                    return;
                }
                progress.coins -= item.price();
                owned.add(item.id());
                sfx.play("coin");
                edit = item == kit.customTrail;
            }
            shopSelect(shopTab, item.id());
            Store.save(saveFile, progress);
            if (edit) {
                openEditor();
            }
            return;
        }
    }

    /**
     * рамка кадру пташки без порожніх країв (запас під крила) -- одна на всі кадри, щоб пташка не смикалась,
     * і розмір, до якого її збільшити під frameBox. Піксель-арт збільшуємо так, щоб кожен
     * художній піксель став цілим числом пікселів -- тоді картинка не розмивається
     */
    private Rect previewBox(BirdArt bird) {
        Rect box = previewBoxes.get(bird.id);
        if (box == null) {
            box = new Rect();
            for (Bitmap f : bird.anim.frames) {
                Rect b = boundingRect(f);
                if (b != null) {
                    box.union(b);
                }
            }
            previewBoxes.put(bird.id, box);
        }
        return box;
    }

    private static Rect boundingRect(Bitmap b) {
        int w = b.getWidth(), h = b.getHeight();
        int[] px = new int[w * h];
        b.getPixels(px, 0, w, 0, 0, w, h);
        int l = w, t = h, r = -1, bt = -1;
        for (int y = 0; y < h; y++) {
            for (int x = 0; x < w; x++) {
                if ((px[y * w + x] >>> 24) != 0) {
                    l = Math.min(l, x);
                    r = Math.max(r, x);
                    t = Math.min(t, y);
                    bt = Math.max(bt, y);
                }
            }
        }
        return r < 0 ? null : new Rect(l, t, r + 1, bt + 1);
    }

    /** розмір кадру пташки на картці */
    private int[] previewSize(BirdArt bird, int[] frameBox) {
        Rect box = previewBox(bird);
        float k = Math.min(frameBox[0] / (float) box.width(), frameBox[1] / (float) box.height());
        if (bird.artPx > 0 && k >= 1) {
            k = Math.max(1, (int) Math.floor(k * bird.artPx)) / (float) bird.artPx;
        } else if (k >= 2) {
            k = (int) k;
        }
        return new int[]{Math.round(box.width() * k), Math.round(box.height() * k), (bird.artPx > 0 || k == (int) k) ? 1 : 0};
    }

    private void drawPreview(Canvas c, BirdArt bird, int frame, int[] frameBox, float cx, float cy) {
        int[] size = previewSize(bird, frameBox);
        Rect box = previewBox(bird);
        int x = (int) cx - size[0] / 2, y = (int) cy - size[1] / 2;
        RectF dst = new RectF(x, y, x + size[0], y + size[1]);
        c.drawBitmap(bird.anim.frames[frame], box, dst, size[2] == 1 ? Gfx.sprite(255) : Gfx.smooth(255));
    }

    /** картка шлейфу: обрана пташка гойдається, а за нею тягнеться шлейф (там, де вона щойно була) */
    private void drawTrailPreview(Canvas c, Trail trail, Box rect) {
        BirdArt bird = kit.bird;
        int frame = ((int) (tTotal * bird.anim.fps)) % bird.anim.frames.length;
        int[] size = previewSize(bird, TRAIL_PREVIEW);
        int bx = rect.right() - 14 - size[0] / 2;

        int n = 24;
        float length = bx - rect.x - 2;
        pts.clear();
        for (int j = 0; j <= n; j++) {
            pts.add(bx - 6 - length * j / n, waveY(rect, tTotal - 0.8f * j / n), j / (float) n, (j * 0.618f) % 1);
        }
        c.save();
        Box clip = rect.inflate(-6, -6).clip(shopView());
        c.clipRect(clip.x, clip.y, clip.right(), clip.bottom());
        trail.draw(c, pts, tTotal);
        c.restore();
        drawPreview(c, bird, frame, TRAIL_PREVIEW, bx, waveY(rect, tTotal));
    }

    private static float waveY(Box rect, float t) {
        return rect.y + 50 + (float) Math.sin(t * 3) * 8;
    }

    /** мініатюра фону на картці (картинка вдвічі більша за рамку -- для чіткості) */
    private Box drawThumb(Canvas c, String themeId, Box rect) {
        Bitmap img = scenery.thumbnail(themeId, BG_THUMB[0], BG_THUMB[1]);
        Box box = new Box(rect.centerX() - BG_THUMB[0] / 2, rect.y + 48 - BG_THUMB[1] / 2, BG_THUMB[0], BG_THUMB[1]);
        Gfx.roundRect(c, COLOR_OUTLINE, box.inflate(6, 6), 5);
        Gfx.blitTo(c, img, box.x, box.y, box.w, box.h, true);
        return box;
    }

    /**
     * картка труб: мініатюра обраного фону, на ній дві маленькі труби, як у грі --
     * одна росте з землі, друга звисає з неба
     */
    private void drawPipePreview(Canvas c, PipeArt pipe, Box rect) {
        Box box = drawThumb(c, progress.background, rect);
        int ground = box.y + Math.round((groundY - Scenery.THUMB_TOP) * box.h / (float) Scenery.THUMB_H);
        c.save();
        Box clip = new Box(box.x, box.y, box.w, ground - box.y).clip(shopView());
        c.clipRect(clip.x, clip.y, clip.right(), clip.bottom());
        PipeArt mini = pipe.mini;
        for (int[] p : PIPE_PREVIEW) {
            mini.draw(c, box.x + p[0], mini.capW, box.y + p[1] - PIPE_PREVIEW_GAP / 2, PIPE_PREVIEW_GAP, ground, box.y);
        }
        c.restore();
    }

    private void drawCard(Canvas c, ShopItem item, Box rect) {
        boolean selected = item.id().equals(shopPick(shopTab));
        boolean owned = shopOwned(shopTab).contains(item.id());

        drawPanel(c, rect);
        Box frame = rect.inflate(-4, -6).move(0, -2);
        if (selected) {
            Gfx.roundRectStroke(c, COLOR_ARROW, frame, 3, 8);
        } else if (hover(rect) && hover(shopView())) {
            Gfx.roundRectStroke(c, COLOR_CARD_HOVER, frame, 2, 8);
        }

        switch (shopTab) {
            case "birds": {
                // -- пташка махає крилами (кожна зі своєю швидкістю кадрів)
                BirdArt bird = (BirdArt) item;
                int i = ((int) (tTotal * bird.anim.fps)) % bird.anim.frames.length;
                drawPreview(c, bird, i, CARD_PREVIEW, rect.centerX(), rect.y + 50);
                break;
            }
            case "trails":
                drawTrailPreview(c, (Trail) item, rect);
                break;
            case "pipes":
                drawPipePreview(c, (PipeArt) item, rect);
                break;
            default:
                drawThumb(c, item.id(), rect);
        }

        int y = rect.bottom() - 34;
        if (selected) {
            // -- обраний свій шлейф можна змінити (тап по картці відкриває редактор)
            Gfx.blitCenter(c, kit.text(item == kit.customTrail ? "edit" : "selected"), rect.centerX(), y);
        } else if (owned) {
            Gfx.blitCenter(c, kit.text("select"), rect.centerX(), y);
        } else {
            String price = String.valueOf(item.price());
            int w = counterWidth(kit.coinIcon, price);
            drawCounter(c, kit.coinIcon, price, rect.centerX() - w / 2, y);
        }
    }

    /** вкладки: активна -- з зеленою рамкою, інші -- трохи темніші */
    private void drawTabs(Canvas c) {
        for (Map.Entry<String, Box> e : shopTabs().entrySet()) {
            Box rect = e.getValue();
            boolean active = e.getKey().equals(shopTab);
            panelPaint.setColorFilter(active ? null : tabDim);
            c.drawBitmap(kit.panel.render(rect.w, rect.h), rect.x, rect.y, panelPaint);
            Box frame = rect.inflate(-4, -6).move(0, -2);
            if (active) {
                Gfx.roundRectStroke(c, COLOR_ARROW, frame, 3, 8);
            } else if (hover(rect)) {
                Gfx.roundRectStroke(c, COLOR_CARD_HOVER, frame, 2, 8);
            }
            Gfx.blitCenter(c, kit.text("tab_" + e.getKey()), rect.centerX(), rect.centerY() - 3);
        }
    }

    private void drawShop(Canvas c) {
        Gfx.blitCenter(c, kit.text("shop_title"), WIDTH / 2, SHOP_TITLE_Y);
        drawTabs(c);
        drawPanel(c, SHOP_PANEL);

        Box view = shopView();
        c.save();
        c.clipRect(view.x, view.y, view.right(), view.bottom());
        List<? extends ShopItem> items = shopItems(shopTab);
        for (int i = 0; i < items.size(); i++) {
            Box rect = shopCard(i);
            if (rect.overlaps(view)) {
                drawCard(c, items.get(i), rect);
            }
        }
        c.restore();

        // -- смужка прокрутки, якщо карток більше, ніж влазить
        int top = shopMaxScroll();
        if (top > 0) {
            int h = Math.max(30, view.h * view.h / (view.h + top));
            int y = view.y + (view.h - h) * shopScroll / top;
            Gfx.roundRect(c, COLOR_KNOB_SHADE, SHOP_PANEL.right() - 12, y, 5, h, 3);
        }

        if (notEnough > 0 && ((int) ((NOT_ENOUGH_TIME - notEnough) * 6)) % 2 == 0) {
            Gfx.blitCenter(c, kit.text("not_enough"), WIDTH / 2, SHOP_PANEL.bottom() + 10);
        }
    }

    // -- редактор свого шлейфу
    private void openEditor() {
        editing = true;
        editSlot = 0;
        notEnough = 0f;
        editPts.clear();
    }

    /** назад у магазин; вибір уже діє (редактор міняє налаштування шлейфу на льоту) -- лишається зберегти */
    private void closeEditor() {
        editing = false;
        dragging = null;
        Store.save(saveFile, progress);
    }

    /** квадратик i-го кольору палітри: 2 ряди по PALETTE_COLS */
    private static Box paletteRect(int i) {
        int row = i / PALETTE_COLS, col = i % PALETTE_COLS;
        return new Box(PALETTE_X + col * (SWATCH_W + SWATCH_GAP), PALETTE_Y + row * (SWATCH_H + SWATCH_GAP),
                SWATCH_W, SWATCH_H);
    }

    /** у перегляді пташка плавно літає вгору-вниз; це y центру тіла -- зсуваємо, щоб уся картинка була по центру */
    private float editBirdY(float t) {
        BirdArt bird = kit.bird;
        return EDIT_PREVIEW.centerY() + (bird.ay - bird.h / 2f) + (float) Math.sin(t * 3) * EDIT_BIRD_BOB;
    }

    /** точки шлейфу в перегляді: як у грі -- їдуть разом зі світом і згасають */
    private void updateEditPreview() {
        for (float[] p : editPts) {
            p[0] -= Levels.LEVELS[0].speed;
            p[2] += dts;
        }
        removeOld(editPts, TRAIL_LIFE);
        editPts.add(new float[]{EDIT_BIRD_X - 6, editBirdY(tTotal), 0f, rnd.nextFloat()});
    }

    private static void removeOld(List<float[]> list, float life) {
        for (int i = list.size() - 1; i >= 0; i--) {
            if (list.get(i)[2] >= life) {
                list.remove(i);
            }
        }
    }

    /** квадратик кольору з контуром і бліком (як доріжка повзунка); frame -- колір рамки навколо (0 -- без неї) */
    private void drawSwatch(Canvas c, Box rect, int color, int frame) {
        Gfx.roundRect(c, COLOR_OUTLINE, rect.inflate(6, 6), 6);
        Gfx.roundRect(c, color, rect, 4);
        int r = (color >> 16) & 0xFF, g = (color >> 8) & 0xFF, b = color & 0xFF;
        int shine = Gfx.rgb(r + (255 - r) * 2 / 5, g + (255 - g) * 2 / 5, b + (255 - b) * 2 / 5);
        Gfx.fill(c, shine, rect.x + 3, rect.y + 3, rect.w - 6, 3);
        if (frame != 0) {
            Gfx.roundRectStroke(c, frame, rect.inflate(12, 12), 2, 8);
        }
    }

    /** небо поточного фону, на ньому пташка зі своїм шлейфом */
    private void drawEditPreview(Canvas c) {
        Box box = EDIT_PREVIEW;
        Gfx.roundRect(c, COLOR_OUTLINE, box.inflate(6, 6), 6);
        Gfx.blitArea(c, scenery.sky, Gfx.src(box.x, box.y + 160, box.w, box.h), box.x, box.y);
        c.save();
        c.clipRect(box.x, box.y, box.right(), box.bottom());
        trailPoints(editPts);
        kit.customTrail.draw(c, pts, tTotal);
        BirdArt bird = kit.bird;
        float y = editBirdY(tTotal);
        float v = editBirdY(tTotal + 1 / FPS) - y;          // -- px за кадр, як birdV у грі
        float angle = Math.max(BIRD_MAX_DOWN, Math.min(BIRD_MAX_UP, -v * 8));
        bird.draw(c, EDIT_BIRD_X, y, angle, (int) (tTotal * bird.anim.fps));
        c.restore();
    }

    /** точки шлейфу (від найстаріших до найновіших) -> pts від голови до хвоста */
    private void trailPoints(List<float[]> list) {
        pts.clear();
        for (int i = list.size() - 1; i >= 0; i--) {
            float[] p = list.get(i);
            pts.add(p[0], p[1], p[2] / TRAIL_LIFE, p[3]);
        }
    }

    private void drawEditor(Canvas c) {
        Store.TrailConfig cfg = kit.customTrail.config;
        Gfx.blitCenter(c, kit.text("custom_title"), WIDTH / 2, EDIT_TITLE_Y);
        drawPanel(c, EDIT_PANEL);
        drawEditPreview(c);

        // -- кольори: два квадратики (біля пташки -> хвіст), обраний -- у зеленій рамці; під ними палітра
        Bitmap label = kit.text("colors");
        Gfx.blit(c, label, EDIT_LABEL_X, EDIT_SLOTS[0].centerY() - label.getHeight() / 2);
        for (int i = 0; i < EDIT_SLOTS.length; i++) {
            Box rect = EDIT_SLOTS[i];
            int frame = i == editSlot ? COLOR_ARROW : hover(rect) ? COLOR_CARD_HOVER : 0;
            drawSwatch(c, rect, Trail.PALETTE[i == 0 ? cfg.c1 : cfg.c2], frame);
        }
        drawArrow(c, (EDIT_SLOTS[0].right() + EDIT_SLOTS[1].x) / 2f, EDIT_SLOTS[0].centerY(), 1, false);
        int current = editSlot == 0 ? cfg.c1 : cfg.c2;
        for (int i = 0; i < Trail.PALETTE.length; i++) {
            Box rect = paletteRect(i);
            int frame = i == current ? COLOR_ARROW : hover(rect) ? COLOR_CARD_HOVER : 0;
            drawSwatch(c, rect, Trail.PALETTE[i], frame);
        }

        Gfx.blit(c, kit.text("style"), EDIT_LABEL_X, EDIT_STYLE_Y);
        drawSelectorBox(c, EDIT_STYLE, kit.text("style_" + cfg.style));
        Gfx.blit(c, kit.text("width"), EDIT_LABEL_X, EDIT_WIDTH_Y);
        drawSliderBar(c, EDIT_WIDTH, cfg.width, EDIT_PANEL.right() - 44);
    }

    private void editorClick(int x, int y) {
        Store.TrailConfig cfg = kit.customTrail.config;
        for (int i = 0; i < EDIT_SLOTS.length; i++) {
            if (EDIT_SLOTS[i].inflate(8, 8).contains(x, y)) {
                editSlot = i;
                return;
            }
        }
        for (int i = 0; i < Trail.PALETTE.length; i++) {
            if (paletteRect(i).inflate(SWATCH_GAP, SWATCH_GAP).contains(x, y)) {
                if (editSlot == 0) {
                    cfg.c1 = i;
                } else {
                    cfg.c2 = i;
                }
                return;
            }
        }
        if (EDIT_STYLE.contains(x, y)) {
            int step = x < EDIT_STYLE.x + SELECTOR_ARROW ? -1 : 1;
            cfg.style = Trail.STYLES[Trail.mod(indexOf(Trail.STYLES, cfg.style) + step, Trail.STYLES.length)];
            return;
        }
        if (EDIT_WIDTH.inflate(SLIDER_GRAB * 2, SLIDER_GRAB * 2).contains(x, y)) {
            dragging = "trail_width";
            dragSlider(dragging, x);
        }
    }

    private void resetGame() {
        birdY = BIRD_START_Y;
        birdV = 0;
        score = 0;
        level = 0;
        levelSpeed = Levels.LEVELS[0].speed;
        levelTime = 0f;       // -- на старті теж показуємо «РІВЕНЬ 1»
        runCoins = 0;
        newRecord = false;
        runSaved = false;
        over = false;
        paused = false;
        start = true;
        shield = false;
        grace = 0f;
        for (int i = 0; i < boost.length; i++) {
            boost[i] = 0f;
        }
        speedK = 1f;
        pops.clear();
        trailPts.clear();

        newPipes();
        scenery.update(0, levelSpeed * FPS, true);   // -- фон їде з тією ж швидкістю, що й труби
    }

    /** повертання в головне меню після смерті */
    private void goToMenu() {
        start = false;
        over = false;
        paused = false;
    }

    /** повернення в головне меню з налаштувань / рекордів / магазину */
    private void closeSettings() {
        inSettings = false;
        inRecords = false;
        inShop = false;
        editing = false;
        dragging = null;
        shopTouch = false;
        Store.save(settingsFile, config);
    }

    private boolean hover(Box r) {
        return touching && r.contains(touchX, touchY);
    }

    // -- дотики (як мишка в пайтон-версії: натиснули, повели, відпустили)
    void touchDown(int x, int y) {
        touching = true;
        touchX = x;
        touchY = y;

        if (inSettings) {
            if (pressed == null) {
                settingsClick(x, y);
            }
        } else if (inRecords) {
            if (pressed == null && RECORDS_BACK_RECT.contains(x, y)) {
                press("back");
            }
        } else if (inShop && editing) {
            if (pressed == null) {
                if (EDIT_BACK_RECT.contains(x, y)) {
                    press("back");
                } else {
                    editorClick(x, y);
                }
            }
        } else if (inShop) {
            if (pressed == null) {
                if (SHOP_BACK_RECT.contains(x, y)) {
                    press("back");
                } else {
                    // -- тап по картці спрацьовує, коли палець відпустили; якщо повели -- магазин гортається
                    shopTouch = true;
                    shopDragged = false;
                    shopTouchX = x;
                    shopTouchY = y;
                    shopScrollStart = shopScroll;
                }
            }
        } else if (!start) {
            if (pressed != null || fading) {
                return;
            }
            for (Map.Entry<String, Box> e : menuButtons.entrySet()) {
                if (e.getValue().contains(x, y)) {
                    press(e.getKey());
                    break;
                }
            }
        } else if (paused) {
            if (pressed == null) {
                if (PAUSE_MENU_RECT.contains(x, y)) {
                    press("quit");
                } else {
                    paused = false;
                }
            }
        } else if (over) {
            if (overTime >= GAME_OVER_ANIM && MENU_BTN_RECT.contains(x, y)) {
                press("menu");
            }
        } else {
            birdV = JUMP_VELOCITY;
        }
    }

    void touchMove(int x, int y) {
        touchX = x;
        touchY = y;
        if (dragging != null) {
            dragSlider(dragging, x);
        }
        if (shopTouch) {
            int dy = y - shopTouchY;
            if (!shopDragged && Math.abs(dy) > SHOP_DRAG_SLOP) {
                shopDragged = true;
            }
            if (shopDragged) {
                shopScroll = Math.max(0, Math.min(shopMaxScroll(), shopScrollStart - dy));
            }
        }
    }

    void touchUp(int x, int y) {
        touching = false;
        if ("trail_width".equals(dragging)) {
            Store.save(saveFile, progress);
        } else if (dragging != null) {
            Store.save(settingsFile, config);
        }
        dragging = null;
        if (shopTouch) {
            shopTouch = false;
            if (!shopDragged && inShop && !editing && pressed == null) {
                shopClick(shopTouchX, shopTouchY);
            }
        }
    }

    /** другий палець під час гри -- теж стрибок (можна тапати двома руками по черзі) */
    void extraTouch() {
        if (start && !over && !paused && !fading) {
            birdV = JUMP_VELOCITY;
        }
    }

    /** пробіл на клавіатурі */
    void jumpKey() {
        if (start && !over && !paused) {
            birdV = JUMP_VELOCITY;
        }
    }

    /** системна кнопка «назад»; false -- ми в головному меню, можна виходити */
    boolean back() {
        if (fading || pressed != null) {
            return true;
        }
        if (editing) {
            closeEditor();
        } else if (inSettings || inRecords || inShop) {
            closeSettings();
        } else if (start && !over) {
            paused = !paused;
        } else if (over) {
            if (overTime >= GAME_OVER_ANIM) {
                goToMenu();
            }
        } else {
            return false;
        }
        return true;
    }

    /** гра не на екрані або під шторкою -- пауза, щоб пташка не впала, поки гравець не бачить */
    void autoPause() {
        if (start && !over && !fading) {
            paused = true;
        }
    }

    /** гру згорнули: ставимо на паузу і зберігаємо (монетки з незакінченої гри теж) */
    void onPause() {
        autoPause();
        touching = false;
        dragging = null;
        shopTouch = false;
        music.pause();
        save();
    }

    void onResume() {
        music.resume();
    }

    void save() {
        Store.save(saveFile, progress);
        Store.save(settingsFile, config);
    }

    void release() {
        music.release();
        sfx.release();
    }

    // -- один кадр (1/60 сек)
    void step() {
        float dt = 1000f / FPS;
        tTotal += dts;

        // -- затримка після натискання кнопки меню перед дією
        if (pressed != null) {
            pressTime += dt;
            if (pressTime > PRESS_ACTION_DELAY) {
                switch (pressed) {
                    case "play":
                        fading = true;
                        fade = 0;
                        break;
                    case "shop":
                        inShop = true;
                        shopScroll = 0;
                        break;
                    case "settings":
                        inSettings = true;
                        break;
                    case "record":
                        inRecords = true;
                        break;
                    case "back":
                        if (editing) {
                            closeEditor();
                        } else {
                            closeSettings();
                        }
                        break;
                    case "menu":
                        goToMenu();
                        break;
                    case "quit":
                        // -- з паузи в меню: гра зараховується як закінчена
                        over = true;
                        finishRun();
                        goToMenu();
                        break;
                    default:
                        break;
                }
                pressed = null;
            }
        }
        pressProgress = pressed != null ? pressTime / PRESS_ACTION_DELAY : 0;

        // -- затемнення екрану перед стартом гри
        if (fading) {
            fade += FADE_SPEED;
            if (fade >= 255) {
                fade = 255;
                fading = false;
                resetGame();
            }
        }

        if (paused) {
            kit.menu.update(dts, hover(PAUSE_MENU_RECT), "quit".equals(pressed) ? pressProgress : 0f);
            music.play("game");
            music.update(dts);
            return;
        }

        // -- сповільнення: швидкість світу плавно йде до потрібної (гравітація і стрибок не змінюються)
        boolean slowed = start && !over && boost[SLOW] > 0;
        speedK += ((slowed ? SLOW_FACTOR : 1f) - speedK) * Math.min(1f, 5f * dts);
        // -- на новому рівні світ розганяється поступово
        levelSpeed += (Levels.LEVELS[level].speed - levelSpeed) * Math.min(1f, LEVEL_EASE * dts);
        float speed = levelSpeed * speedK;

        // -- фізика
        if (start && !over) {
            for (int i = 0; i < boost.length; i++) {
                boost[i] = Math.max(0f, boost[i] - dts);
            }
            grace = Math.max(0f, grace - dts);
            levelTime += dts;

            birdV += GRAVITY;
            birdY += birdV;
            Box birdRect = new Box(BIRD_START_X, (int) birdY, BIRD_SIZE, BIRD_SIZE);

            for (Pipe pipe : pipes) {
                pipe.x -= speed;

                if (!pipe.passed && pipe.x + PIPE_WIDTH < BIRD_START_X) {
                    pipe.passed = true;
                    score += 1;
                }

                if (BIRD_START_X + BIRD_SIZE > pipe.x && BIRD_START_X < pipe.x + PIPE_WIDTH) {
                    if (birdY < pipe.y || birdY + BIRD_SIZE > pipe.y + pipe.gap) {
                        hit();
                    }
                }
            }

            if (Levels.levelFor(score) > level) {
                levelUp();
            }

            // -- труба зникає, коли повністю виїхала за лівий край полотна
            for (int i = pipes.size() - 1; i >= 0; i--) {
                if (pipes.get(i).x <= -PIPE_WIDTH - ox) {
                    pipes.remove(i);
                }
            }
            fillPipes();

            // -- монетки їдуть разом з трубами; зачепив -- підібрав
            for (Coin coin : coins) {
                coin.x -= speed;
                if (!coin.taken) {
                    Box box = new Box((int) coin.x - COIN_HITBOX / 2, (int) coin.y - COIN_HITBOX / 2, COIN_HITBOX, COIN_HITBOX);
                    if (!over && box.overlaps(birdRect)) {
                        coin.taken = true;
                        coin.takenT = 0f;
                        coin.value = boost[X2] > 0 ? 2 : 1;
                        runCoins += coin.value;
                        progress.coins += coin.value;
                        sfx.play("coin");
                    }
                }
            }

            // -- бонуси теж їдуть з трубами; підібраний одразу діє
            for (Powerup p : powerups) {
                p.x -= speed;
                if (!p.taken) {
                    float py = powerupY(p);
                    Box box = new Box((int) p.x - POWERUP_HITBOX / 2, (int) py - POWERUP_HITBOX / 2, POWERUP_HITBOX, POWERUP_HITBOX);
                    if (!over && box.overlaps(birdRect)) {
                        p.taken = true;
                        p.takenT = 0f;
                        p.y = py;
                        takePowerup(p.kind);
                    }
                }
            }

            // -- земля і стеля (верх екрана): зі щитом пташка відскакує, без щита -- кінець гри
            int ceiling = -oy;
            if (birdY + BIRD_SIZE > groundY) {
                hit();
                if (!over) {
                    birdY = groundY - BIRD_SIZE;
                    birdV = JUMP_VELOCITY;
                }
            } else if (birdY < ceiling) {
                hit();
                if (!over) {
                    birdY = ceiling;
                    birdV = Math.max(birdV, 0);
                }
            }
        }

        // -- анімація підбору монеток і бонусів йде і після смерті
        for (int i = coins.size() - 1; i >= 0; i--) {
            Coin coin = coins.get(i);
            if (coin.taken) {
                coin.takenT += dts;
            }
            if (coin.x <= -COIN_HITBOX - ox || (coin.taken && coin.takenT >= COIN_PICKUP_TIME)) {
                coins.remove(i);
            }
        }
        for (int i = powerups.size() - 1; i >= 0; i--) {
            Powerup p = powerups.get(i);
            if (p.taken) {
                p.takenT += dts;
            }
            if (p.x <= -POWERUP_HITBOX - ox || (p.taken && p.takenT >= COIN_PICKUP_TIME)) {
                powerups.remove(i);
            }
        }
        for (float[] pop : pops) {
            pop[2] += dts;
        }
        removeOld(pops, SHIELD_POP_TIME);

        // -- шлейф: точки, де пролетіла пташка; їдуть разом зі світом і згасають.
        // -- після смерті нові не додаються -- шлейф просто тане
        for (float[] tp : trailPts) {
            tp[2] += dts;
            if (start && !over) {
                tp[0] -= speed;
            }
        }
        removeOld(trailPts, TRAIL_LIFE);
        if (start && !over && !kit.trail.id.equals("none")) {
            trailPts.add(new float[]{BIRD_START_X + BIRD_SIZE / 2f - 6, birdY + BIRD_SIZE / 2f, 0f, rnd.nextFloat()});
        }

        if (editing) {
            updateEditPreview();
        }

        if (over) {
            finishRun();
        }

        // -- крила: під час гри махає швидше при стрибку, після смерті завмирає
        if (start && !over) {
            kit.bird.update(dts, birdV < 0 ? 2f : 1f);
        }
        if (start) {
            kit.aura.update(dts);
            for (Animation a : kit.powerups.values()) {
                a.update(dts);
            }
        }

        // -- музика: у меню своя, у грі своя; поки тягнуть повзунок гри -- грає музика гри
        music.play(start || "game_music".equals(dragging) ? "game" : "menu");
        music.update(dts);

        notEnough = Math.max(0f, notEnough - dts);
        overTime = over ? overTime + dts : 0f;

        // -- анімація фону: у меню повільно, у грі як труби, після смерті стоїть
        if (over) {
            scenery.update(dts, 0f, true);
        } else {
            scenery.update(dts, start ? speed * FPS : MENU_SCROLL_SPEED, false);
        }

        // -- кнопки: наведення (палець на кнопці) і натискання
        if (!start && (inSettings || inRecords || inShop)) {
            Box back = inSettings ? BACK_BTN_RECT : inRecords ? RECORDS_BACK_RECT : editing ? EDIT_BACK_RECT : SHOP_BACK_RECT;
            Ui.SpriteButton button = editing && inShop ? kit.done : kit.menu;
            button.update(dts, hover(back), "back".equals(pressed) ? pressProgress : 0f);
        } else if (!start) {
            for (Map.Entry<String, Ui.SpriteButton> e : menuSprites.entrySet()) {
                e.getValue().update(dts, hover(menuButtons.get(e.getKey())),
                        e.getKey().equals(pressed) ? pressProgress : 0f);
            }
        } else if (over) {
            kit.menu.update(dts, hover(MENU_BTN_RECT), "menu".equals(pressed) ? pressProgress : 0f);
        }
    }

    // -- малювання; Canvas: (0, 0) -- лівий верхній кут ігрового поля, видно від -ox до viewW - ox по x
    // -- і від -oy до viewH - oy по y
    void render(Canvas c) {
        if (!start && (inSettings || inRecords || inShop)) {
            scenery.drawBack(c);
            scenery.drawGround(c);
            Ui.SpriteButton button = kit.menu;
            Box back;
            if (inSettings) {
                back = BACK_BTN_RECT;
                drawSettings(c);
            } else if (inRecords) {
                back = RECORDS_BACK_RECT;
                drawRecords(c);
            } else if (editing) {
                back = EDIT_BACK_RECT;
                button = kit.done;     // -- з редактора -- назад у магазин
                drawEditor(c);
            } else {
                back = SHOP_BACK_RECT;
                drawShop(c);
                drawMenuCounters(c);    // -- баланс монет видно в магазині
            }
            button.draw(c, tTotal, back.x, back.y);

        } else if (!start) {
            scenery.drawBack(c);
            scenery.drawGround(c);
            kit.title.draw(c, tTotal);
            for (Ui.SpriteButton sprite : menuSprites.values()) {
                sprite.draw(c, tTotal);
            }
            drawMenuCounters(c);

        } else {
            scenery.drawBack(c);

            for (Pipe pipe : pipes) {
                kit.pipe.draw(c, (int) pipe.x, PIPE_WIDTH, pipe.y, pipe.gap, groundY, -oy);
            }

            drawCoins(c);
            drawPowerups(c);
            scenery.drawGround(c);
            drawSlowTint(c);

            trailPoints(trailPts);
            kit.trail.draw(c, pts, tTotal);
            drawBird(c, BIRD_START_X, birdY, birdV);
            drawText(c, String.valueOf(score), WIDTH / 2f, 50);
            drawCounter(c, kit.coinIcon, String.valueOf(runCoins), 14, 30);
            drawPowerupHud(c);
            drawLevelHud(c);
            if (!over) {
                drawLevelBanner(c);
            }

            if (over) {
                // -- напис, панель і кнопка виїжджають зверху (ease-out)
                float k = Math.min(1f, overTime / GAME_OVER_ANIM);
                int slide = (int) (-40 * (1 - k) * (1 - k) * (1 - k));

                Gfx.blitCenter(c, kit.text("game_over"), WIDTH / 2, GAME_OVER_Y + slide);
                drawResult(c, slide);
                kit.menu.draw(c, tTotal, MENU_BTN_RECT.x, MENU_BTN_RECT.y + slide);
            } else if (paused) {
                drawPause(c);
            }
        }

        if (fading) {
            c.drawColor(Gfx.withAlpha(0, fade));
        }
    }

    /** пауза: екран темнішає, посередині -- кнопка «грати» (тап будь-де продовжує), під нею MENU */
    private void drawPause(Canvas c) {
        c.drawColor(Gfx.withAlpha(0, 110));
        drawPanel(c, PAUSE_PLAY);
        float cx = PAUSE_PLAY.centerX() + 4, cy = PAUSE_PLAY.centerY() - 4;
        Gfx.polygon(c, COLOR_OUTLINE, cx - 26, cy - 32, cx + 32, cy, cx - 26, cy + 32);
        Gfx.polygon(c, COLOR_ARROW, cx - 18, cy - 20, cx + 19, cy, cx - 18, cy + 20);
        kit.menu.draw(c, tTotal, PAUSE_MENU_RECT.x, PAUSE_MENU_RECT.y);
    }
}
