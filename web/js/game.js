// -- уся гра -- порт android/.../Game.java (а той -- src/main.py). Координати -- як у пайтоні: ігрове поле 400x700,
// -- ox -- скільки полотна ліворуч від поля, oy -- над ним. Canvas у render() уже зсунутий так, що (0, 0) --
// -- лівий верхній кут поля. Меню і панелі -- по центру екрана, а земля (floorY) -- донизу, HUD -- до країв.
// -- Один виклик step() -- один кадр (1/60 сек)
import * as Gfx from './gfx.js';
import { Box, rgb } from './gfx.js';
import { LANGS } from './kit.js';
import { Points, PALETTE, STYLES, mod } from './trail.js';
import { Scenery } from './scenery.js';

// -- віконечко: ігрове поле 400x700 завжди по центру, а небо/земля/труби тягнуться на весь екран
export const WIDTH = 400, HEIGHT = 700;
export const FPS = 60;

const GRAVITY = 0.4;
const JUMP_VELOCITY = -8;
const BIRD_START_X = 80, BIRD_START_Y = 300;
const BIRD_SIZE = 30;          // -- хітбокс пташки по осі x+y
const BIRD_MAX_UP = 25;        // -- градуси: наскільки пташка задирає дзьоб при стрибку
const BIRD_MAX_DOWN = -75;     // -- і наскільки опускає при падінні

// -- рівні складності: що більший рахунок, то швидше, вужче і частіше труби (src/levels.py)
export const LEVELS = [
    { score: 0, speed: 3.0, gap: 150, spacing: 250 },
    { score: 10, speed: 3.3, gap: 144, spacing: 240 },
    { score: 20, speed: 3.6, gap: 138, spacing: 230 },
    { score: 30, speed: 3.9, gap: 132, spacing: 220 },
    { score: 45, speed: 4.2, gap: 126, spacing: 210 },
    { score: 60, speed: 4.5, gap: 120, spacing: 200 },
];

function levelFor(score) {
    let lv = 0;
    LEVELS.forEach((l, i) => {
        if (score >= l.score) {
            lv = i;
        }
    });
    return lv;
}

export const PIPE_WIDTH = 70;
const PIPE_GAP_LO = 225, PIPE_GAP_HI = 525;     // -- у яких межах по висоті може бути середина проходу
const PIPE_SHIFT_PER_FRAME = 3.6;

// -- рівні
const LEVEL_EASE = 1.5;
const LEVEL_BANNER_TIME = 1.8;
const LEVEL_BANNER_POP = 0.3;
const LEVEL_BANNER_Y = 150;
const LEVEL_HUD_RIGHT = WIDTH - 14, LEVEL_HUD_Y = 30;
const LEVEL_BAR_COLOR = rgb(86, 180, 50), LEVEL_BAR_SHINE = rgb(160, 225, 100);

// -- монетки
const COIN_CHANCE_GAP = 0.6;
const COIN_CHANCE_BETWEEN = 0.3;
const COIN_GAP_JITTER = 35;
const COIN_HITBOX = 24;
const COIN_PICKUP_TIME = 0.35;
const COIN_FPS = 10;

// -- бонуси: щит рятує від одного удару, сповільнення пригальмовує світ, x2 -- монетка за дві
const POWERUP_CHANCE = 0.18;
const POWERUP_HITBOX = 30;
const POWERUP_BOB = 4;
const BOOST_KINDS = ['slow', 'x2'];
const BOOST_TIME = [5.0, 10.0];
const BOOST_COLORS = [[rgb(176, 112, 255), rgb(220, 190, 255)], [rgb(255, 196, 50), rgb(255, 236, 150)]];
export const SLOW = 0, X2 = 1;
const SLOW_FACTOR = 0.55;
const SLOW_TINT = rgb(70, 30, 150);
const SLOW_TINT_ALPHA = 45;
const SHIELD_GRACE = 1.0;
const SHIELD_POP_TIME = 0.35;
const POWERUP_HUD_Y = 72;
const POWERUP_HUD_STEP = 44;

const TRAIL_LIFE = 0.6;

const MENU_SCROLL_SPEED = 60;
const GAME_OVER_ANIM = 0.45;

const PRESS_ACTION_DELAY = 120;     // -- мс від натискання кнопки до дії (поки вона темнішає)
const FADE_SPEED = 12;

// -- хітбокси кнопок меню
export const PLAY_BTN = new Box(65, 360, 270, 62);
export const SHOP_BTN = new Box(65, 440, 270, 62);
export const RECORD_BTN = new Box(65, 520, 270, 62);
const SETTINGS_BTN = new Box(328, 8, 56, 56);

const MENU_BTN_W = 220, MENU_BTN_H = 94;

const PANEL_INNER_TOP = 8;
const PANEL_INNER_BOTTOM = 16;

// -- екран після смерті
const GAME_OVER_Y = 190;
const RESULT_PANEL = new Box(62, 226, 276, 192);
export const MENU_BTN_RECT = Box.midTop(MENU_BTN_W, MENU_BTN_H, WIDTH / 2, RESULT_PANEL.bottom() + 34);

// -- пауза (гру згорнули): велика кнопка «грати» і MENU під нею
const PAUSE_PLAY = new Box(140, 230, 120, 120);
const PAUSE_MENU_RECT = Box.midTop(MENU_BTN_W, MENU_BTN_H, WIDTH / 2, PAUSE_PLAY.bottom() + 30);

// -- екран рекордів
const RECORDS_TITLE_Y = 70;
const RECORDS_PANEL = new Box(40, 112, 320, 326);

// -- магазин: вкладки ПТАШКИ | ШЛЕЙФИ | ТРУБИ | ФОНИ, під ними вікно з картками по 2 в ряд
const SHOP_TITLE_Y = 80;
const SHOP_TAB_NAMES = ['birds', 'trails', 'pipes', 'backgrounds'];
const SHOP_TABS_ROW = new Box(14, 106, 372, 46);
const SHOP_TAB_GAP = 4;
const SHOP_PANEL = new Box(14, 156, 372, 328);
const SHOP_COLS = 2;
const CARD_W = 164, CARD_H = 137, CARD_GAP = 10;
const CARD_PAD_TOP = 10;
const SHOP_DRAG_SLOP = 8;          // -- px: далі цього палець уже гортає, а не тицяє
const NOT_ENOUGH_TIME = 1.6;
const CARD_PREVIEW = [124, 86];
const TRAIL_PREVIEW = [70, 60];
const BG_THUMB = [132, 74];
const PIPE_PREVIEW = [[20, 4], [77, 56]];
const PIPE_PREVIEW_GAP = 30;
const TAB_DIM = 0.78;

// -- налаштування: мова + 3 повзунки гучності
const SETTINGS_TITLE_Y = 96;
const SETTINGS_PANEL = new Box(24, 130, 352, 362);
const ROW_Y0 = SETTINGS_PANEL.y + 20;
const ROW_H = 84;
const ROWS = ['language', 'menu_music', 'game_music', 'sounds'];
const LANG_SELECTOR = new Box(52, ROW_Y0 + 30, 296, 44);
const SELECTOR_ARROW = 46;
const SLIDER_NAMES = ['menu_music', 'game_music', 'sfx'];
const SLIDERS = [
    new Box(58, ROW_Y0 + ROW_H + 46, 214, 16),
    new Box(58, ROW_Y0 + 2 * ROW_H + 46, 214, 16),
    new Box(58, ROW_Y0 + 3 * ROW_H + 46, 214, 16),
];
const SLIDER_GRAB = 14;
const BACK_BTN_RECT = Box.midTop(MENU_BTN_W, MENU_BTN_H, WIDTH / 2, SETTINGS_PANEL.bottom() + 6);
const RECORDS_BACK_RECT = Box.midTop(MENU_BTN_W, MENU_BTN_H, WIDTH / 2, RECORDS_PANEL.bottom() + 14);
const SHOP_BACK_RECT = Box.midTop(MENU_BTN_W, MENU_BTN_H, WIDTH / 2, SHOP_PANEL.bottom() + 24);
// -- кнопка «конфіденційність» (форма Google зі згодою на рекламу) -- окремим рядком унизу панелі,
// -- лише там, де Google її вимагає (ЄС, Велика Британія); тоді панель довша, а MENU нижче
const PRIVACY_ROW_H = 64;
const PRIVACY_BTN = new Box(52, SETTINGS_PANEL.bottom() - 4, 296, 44);
const SETTINGS_PANEL_PRIVACY = new Box(SETTINGS_PANEL.x, SETTINGS_PANEL.y, SETTINGS_PANEL.w, SETTINGS_PANEL.h + PRIVACY_ROW_H);
const BACK_BTN_PRIVACY = BACK_BTN_RECT.move(0, PRIVACY_ROW_H);

// -- редактор свого шлейфу
const EDIT_TITLE_Y = 56;
const EDIT_PANEL = new Box(24, 86, 352, 430);
const EDIT_PREVIEW = new Box(46, 104, 308, 100);
const EDIT_BIRD_X = EDIT_PREVIEW.right() - 64;
const EDIT_BIRD_BOB = 10;
const EDIT_LABEL_X = EDIT_PANEL.x + 26;
const EDIT_SLOTS = [new Box(232, 222, 44, 28), new Box(306, 222, 44, 28)];
const PALETTE_COLS = 8;
const SWATCH_W = 28, SWATCH_H = 24, SWATCH_GAP = 10;
const PALETTE_X = WIDTH / 2 - Math.trunc((PALETTE_COLS * SWATCH_W + (PALETTE_COLS - 1) * SWATCH_GAP) / 2);
const PALETTE_Y = 266;
const EDIT_STYLE_Y = 332;
const EDIT_STYLE = new Box(52, EDIT_STYLE_Y + 30, 296, 44);
const EDIT_WIDTH_Y = 416;
const EDIT_WIDTH = new Box(58, EDIT_WIDTH_Y + 46, 214, 16);
const EDIT_BACK_RECT = Box.midTop(MENU_BTN_W, MENU_BTN_H, WIDTH / 2, EDIT_PANEL.bottom() + 6);

const COINS_CHIP = new Box(10, 12, 128, 46);

// -- монети за рекламу: кнопка під лічильником монет. AD_LIMIT переглядів за AD_WINDOW, кожен перегляд
// -- «звільняється» через добу після себе; монети -- коли гравець додивився ролик
export const AD_REWARD = 5;
export const AD_LIMIT = 5;
export const AD_WINDOW = 24 * 3600;      // -- сек
const AD_BTN = new Box(10, 64, 128, 50);
const AD_PIP = 10, AD_PIP_GAP = 10;     // -- під кнопкою -- AD_LIMIT квадратиків: золоті -- скільки ще можна
const AD_PIP_COLOR = rgb(255, 196, 50), AD_PIP_SHINE = rgb(255, 236, 150);
const AD_INFO_Y = AD_BTN.bottom() + 14;
const AD_NOTE_Y = 328;                  // -- «повертайся пізніше» -- між заголовком і кнопкою PLAY
const AD_NOTE_TIME = 1.6;
const AD_REWARD_TIME = 1;               // -- сек, скільки злітає «+5» біля кнопки

export const MUSIC_MAX_VOLUME = 0.5;
export const SFX_MAX_VOLUME = 0.6;
export const PRESS_DARK = 70 / 255;      // -- наскільки темнішає кнопка при натисканні

// -- кольори
const COLOR_TEXT_SHADOW = rgb(65, 40, 70);
const COLOR_TEXT_MAIN = rgb(255, 255, 255);
const COLOR_OUTLINE = rgb(45, 16, 40);
const COLOR_SLIDER_BACK = rgb(150, 96, 60);
const COLOR_SLIDER_FILL = rgb(86, 180, 50);
const COLOR_SLIDER_SHINE = rgb(160, 225, 100);
const COLOR_KNOB = rgb(255, 236, 200);
const COLOR_KNOB_SHADE = rgb(240, 180, 90);
const COLOR_ARROW = rgb(70, 175, 50);
const COLOR_ARROW_HOVER = rgb(120, 215, 80);
const COLOR_CARD_HOVER = rgb(255, 255, 255);

const randint = (lo, hi) => lo + Math.floor(Math.random() * (hi - lo + 1));
const round2 = (v) => Math.round(v * 100) / 100;

/** сек від 1970 за годинником пристрою -- від нього рахується ліміт переглядів реклами */
export const now = () => Math.floor(Date.now() / 1000);

function removeOld(list, life) {
    for (let i = list.length - 1; i >= 0; i--) {
        if (list[i][2] >= life) {
            list.splice(i, 1);
        }
    }
}

function fixOwned(owned, free) {
    if (!owned.includes(free)) {
        owned.unshift(free);
    }
}

export class Game {
    /**
     * kit -- спрайти, music / sfx -- звук, config / progress -- налаштування і прогрес,
     * store -- як їх зберегти ({saveConfig, saveProgress}), ads -- реклама за монети
     */
    constructor(kit, music, sfx, config, progress, store, ads) {
        Object.assign(this, { kit, music, sfx, config, progress, store, ads });
        this.scenery = kit.scenery;
        kit.setLang(config.lang);
        config.lang = kit.lang;

        // -- скін: стара гра могла зберегти пташку, якої вже нема -- тоді класична
        const p = progress;
        fixOwned(p.owned, 'classic');
        if (!p.owned.includes(p.skin)) {
            p.skin = 'classic';
        }
        p.skin = kit.setSkin(p.skin);
        fixOwned(p.owned_trails, 'none');
        if (!p.owned_trails.includes(p.trail)) {
            p.trail = 'none';
        }
        p.trail = kit.setTrail(p.trail);
        fixOwned(p.owned_backgrounds, 'day');
        if (!p.owned_backgrounds.includes(p.background)) {
            p.background = 'day';
        }
        p.background = kit.setBackground(p.background);
        fixOwned(p.owned_pipes, 'classic');
        if (!p.owned_pipes.includes(p.pipe)) {
            p.pipe = 'classic';
        }
        p.pipe = kit.setPipe(p.pipe);
        // -- свій шлейф: номери кольорів -- у межах палітри, стиль -- з відомих; редактор міняє ці налаштування
        const custom = p.custom_trail;
        custom.c1 = mod(custom.c1, PALETTE.length);
        custom.c2 = mod(custom.c2, PALETTE.length);
        if (!STYLES.includes(custom.style)) {
            custom.style = 'glow';
        }
        kit.customTrail.config = custom;
        this.groundY = kit.groundY;
        this.floorY = this.groundY;

        music.setLevel('menu', config.menu_music);
        music.setLevel('game', config.game_music);
        sfx.setLevel(config.sfx);

        this.pts = new Points();
        this.previewBoxes = new Map();
        // -- розмір полотна; floorY -- де земля (низ екрана), hud* -- на скільки зсунути HUD до країв екрана
        this.viewW = WIDTH;
        this.viewH = HEIGHT;
        this.ox = 0;
        this.oy = 0;
        this.hudTop = 0;
        this.hudLeft = 0;
        this.hudRight = 0;
        this.settingsBtn = SETTINGS_BTN;
        this.adBtn = AD_BTN;

        // -- стан гри
        this.birdY = BIRD_START_Y;
        this.birdV = 0;
        this.pipes = [];          // -- {x, y (верх проходу), gap, passed}
        this.coins = [];          // -- {x, y, phase, taken, takenT, value}
        this.powerups = [];       // -- {x, y, kind, phase, taken, takenT}
        this.score = 0;
        this.level = 0;
        this.levelSpeed = LEVELS[0].speed;
        this.levelTime = LEVEL_BANNER_TIME;
        this.runCoins = 0;
        this.shield = false;
        this.grace = 0;
        this.boost = [0, 0];
        this.trailPts = [];       // -- x, y, вік, випадкове 0..1
        this.speedK = 1;
        this.pops = [];           // -- x, y, час після удару
        this.newRecord = false;
        this.runSaved = true;

        this.start = false;
        this.over = false;
        this.paused = false;

        this.inSettings = false;
        this.inRecords = false;
        this.inShop = false;
        this.shopTab = 'birds';
        this.shopScroll = 0;
        this.editing = false;
        this.editSlot = 0;
        this.editPts = [];
        this.notEnough = 0;
        this.dragging = null;

        this.pressed = null;
        this.pressTime = 0;
        this.pressProgress = 0;

        this.fade = 0;
        this.fading = false;

        this.tTotal = 0;
        this.overTime = 0;
        this.dts = 1 / FPS;

        // -- реклама за монети
        this.adNote = 'ad_limit';     // -- який напис показати після натискання кнопки реклами
        this.adNoteTime = 0;
        this.adRewardT = -1;          // -- скільки сек тому нарахували монети (-1 -- «+5» не летить)
        this.adRewardFx = false;      // -- монети дали, поки гра була за роликом: звук і «+5» -- коли повернулись

        // -- палець: де він зараз (для «наведення» на кнопки) і чи гортає магазин
        this.touching = false;
        this.touchX = 0;
        this.touchY = 0;
        this.shopTouch = false;
        this.shopDragged = false;

        // -- який спрайт малює яку кнопку меню і їхні хітбокси
        this.menuSprites = { play: kit.play, shop: kit.shop, record: kit.record, settings: kit.settings, ad: kit.ad };
        this.menuButtons = { play: PLAY_BTN, shop: SHOP_BTN, record: RECORD_BTN, settings: this.settingsBtn, ad: this.adBtn };

        this.newPipes();
    }

    /**
     * розмір полотна змінився (повернули екран, інший телефон). safeTop -- скільки px згори займає виріз камери:
     * HUD опускається нижче нього
     */
    setView(viewW, viewH, ox, oy, safeTop) {
        Object.assign(this, { viewW, viewH, ox, oy });
        // -- фон з землею -- донизу екрана, тож місця для польоту більше і зверху, і знизу (порівну)
        const below = viewH - HEIGHT - oy;
        this.floorY = this.groundY + below;
        this.hudTop = safeTop - oy;
        this.hudLeft = -ox;
        this.hudRight = viewW - WIDTH - ox;
        this.settingsBtn = SETTINGS_BTN.move(this.hudRight, this.hudTop);
        this.menuButtons.settings = this.settingsBtn;
        this.adBtn = AD_BTN.move(this.hudLeft, this.hudTop);   // -- кнопка реклами -- під монетками
        this.menuButtons.ad = this.adBtn;
        this.scenery.setView(viewW, ox, viewH - HEIGHT, below);
        this.fillPipes();
    }

    // -- доп функціонал
    /** нова труба (прохід -- як на поточному рівні) + можливо монетки: у проході і між нею та попередньою трубою */
    addPipe(x) {
        const lv = LEVELS[this.level];
        let lo = PIPE_GAP_LO, hi = PIPE_GAP_HI;
        const prev = this.pipes.length ? this.pipes[this.pipes.length - 1] : null;
        if (prev) {
            const shift = Math.round(PIPE_SHIFT_PER_FRAME * lv.spacing / lv.speed);
            const prevMid = prev.y + Math.trunc(prev.gap / 2);
            lo = Math.max(lo, prevMid - shift);
            hi = Math.min(hi, prevMid + shift);
        }
        const gapMid = randint(lo, hi);
        this.pipes.push({ x, y: gapMid - Math.trunc(lv.gap / 2), gap: lv.gap, passed: false });

        if (Math.random() < COIN_CHANCE_GAP) {
            const cy = gapMid + randint(-COIN_GAP_JITTER, COIN_GAP_JITTER);
            this.coins.push(this.coin(x + PIPE_WIDTH / 2, cy));
        }
        if (!prev) {
            return;
        }
        const midX = (prev.x + x) / 2 + PIPE_WIDTH / 2;
        const midY = (prev.y + prev.gap / 2 + gapMid) / 2 + randint(-30, 30);
        const kinds = this.freePowerups();
        if (kinds.length && Math.random() < POWERUP_CHANCE) {
            this.powerups.push({
                x: midX, y: midY, kind: kinds[Math.floor(Math.random() * kinds.length)], phase: Math.random() * 6,
                taken: false, takenT: 0,
            });
        } else if (Math.random() < COIN_CHANCE_BETWEEN) {
            this.coins.push(this.coin(midX, midY));
        }
    }

    coin(x, y) {
        return { x, y, phase: Math.random() * 8, taken: false, takenT: 0, value: 1 };
    }

    /** які бонуси можна поставити: не той, що вже діє, і не той, що вже чекає на полі */
    freePowerups() {
        const waiting = this.powerups.filter((p) => !p.taken).map((p) => p.kind);
        const kinds = [];
        if (!this.shield && !waiting.includes('shield')) {
            kinds.push('shield');
        }
        BOOST_KINDS.forEach((k, i) => {
            if (this.boost[i] <= 0 && !waiting.includes(k)) {
                kinds.push(k);
            }
        });
        return kinds;
    }

    /** бонус гойдається вгору-вниз (і хітбокс разом з ним) */
    powerupY(p) {
        return p.y + Math.sin(this.tTotal * 3 + p.phase) * POWERUP_BOB;
    }

    /** труби, поки не заповнимо все видиме полотно праворуч (на широкому екрані їх більше) */
    fillPipes() {
        const right = WIDTH + this.ox;
        while (!this.pipes.length || this.pipes[this.pipes.length - 1].x <= right) {
            this.addPipe(this.pipes.length ? this.pipes[this.pipes.length - 1].x + LEVELS[this.level].spacing : WIDTH);
        }
    }

    newPipes() {
        this.pipes = [];
        this.coins = [];
        this.powerups = [];
        this.fillPipes();
    }

    /** текст + тінь, по центру (x, y) -- рахунок у грі, шрифтом гри */
    drawText(c, text, x, y) {
        c.font = '48px OutlineStyle, sans-serif';
        c.textAlign = 'center';
        c.textBaseline = 'alphabetic';
        const m = c.measureText(text);
        const asc = m.fontBoundingBoxAscent ?? m.actualBoundingBoxAscent, desc = m.fontBoundingBoxDescent ?? m.actualBoundingBoxDescent;
        const base = y + (asc - desc) / 2;
        c.fillStyle = Gfx.css(COLOR_TEXT_SHADOW);
        c.fillText(text, x + 2, base + 3);
        c.fillStyle = Gfx.css(COLOR_TEXT_MAIN);
        c.fillText(text, x, base);
    }

    /** спрайт пташки по центру хітбокса, нахил залежить від швидкості */
    drawBird(c, x, y, v) {
        const angle = Math.max(BIRD_MAX_DOWN, Math.min(BIRD_MAX_UP, -v * 4));
        const cx = x + BIRD_SIZE / 2, cy = y + BIRD_SIZE / 2;
        // -- після удару щитом пташка блимає, поки невразлива
        if (!(this.grace > 0 && !this.over && Math.trunc(this.grace * 12) % 2 === 1)) {
            this.kit.bird.draw(c, cx, cy, angle);
        }
        if (this.shield) {
            Gfx.blitCenter(c, this.kit.aura.frame(), cx, cy);
        }
        // -- лопнутий щит: бульбашка роздувається і зникає
        for (const p of this.pops) {
            const k = p[2] / SHIELD_POP_TIME;
            Gfx.blitScaledCenter(c, this.kit.aura.frames[0], p[0], p[1], 1 + 0.6 * k, Math.trunc(255 * (1 - k)), false);
        }
    }

    /** бонуси на полі (на всьому полотні, як монетки); підібраний -- летить вгору і зникає */
    drawPowerups(c) {
        for (const p of this.powerups) {
            const img = this.kit.powerups[p.kind].frame();
            if (!p.taken) {
                Gfx.blitCenter(c, img, Math.trunc(p.x), Math.trunc(this.powerupY(p)));
            } else {
                const k = p.takenT / COIN_PICKUP_TIME;
                Gfx.blitScaledCenter(c, img, Math.trunc(p.x), Math.trunc(p.y - 34 * k), 1 + 0.5 * k, Math.trunc(255 * (1 - k)), false);
            }
        }
    }

    /** активні бонуси під лічильником монет: щит -- іконка, сповільнення і x2 -- іконка і смужка часу */
    drawPowerupHud(c) {
        const x = 10;
        let y = POWERUP_HUD_Y;
        if (this.shield) {
            const img = this.kit.powerups.shield.frames[0];
            Gfx.blit(c, img, x, y - Math.trunc(img.height / 2));
            y += POWERUP_HUD_STEP;
        }
        BOOST_KINDS.forEach((kind, i) => {
            const left = this.boost[i];
            if (left <= 0) {
                return;
            }
            const img = this.kit.powerups[kind].frame();
            Gfx.blit(c, img, x, y - Math.trunc(img.height / 2));
            if (!(left < 1.5 && Math.trunc(left * 8) % 2 === 1)) {
                this.drawTimerBar(c, new Box(x + img.width + 6, y - 5, 60, 10), left / BOOST_TIME[i], BOOST_COLORS[i][0], BOOST_COLORS[i][1]);
            }
            y += POWERUP_HUD_STEP;
        });
    }

    /** рахунок дійшов до наступного рівня: нові труби вже як на ньому, світ поступово розганяється */
    levelUp() {
        this.level = levelFor(this.score);
        this.levelTime = 0;
        this.sfx.play('level_up');
    }

    /** поточний рівень праворуч угорі, під ним -- смужка, скільки лишилось до наступного */
    drawLevelHud(c) {
        const right = LEVEL_HUD_RIGHT, y = LEVEL_HUD_Y;
        const label = this.kit.text('level');
        const num = String(this.level + 1);
        const w = label.width + 6 + this.kit.numberWidth(num);
        Gfx.blit(c, label, right - w, y - Math.trunc(label.height / 2));
        this.kit.drawNumber(c, num, right, y, 'light', 1, 2, 255);
        if (this.level + 1 < LEVELS.length) {
            const lo = LEVELS[this.level].score, hi = LEVELS[this.level + 1].score;
            this.drawTimerBar(c, new Box(right - w + 3, y + 22, w - 6, 8), (this.score - lo) / (hi - lo), LEVEL_BAR_COLOR, LEVEL_BAR_SHINE);
        }
    }

    /** на початку рівня посеред екрана вискакує «РІВЕНЬ 2» (росте з пружинкою), трохи висить і тане */
    drawLevelBanner(c) {
        if (this.levelTime >= LEVEL_BANNER_TIME) {
            return;
        }
        const label = this.kit.text('level_title');
        const num = String(this.level + 1);
        const gap = 14;
        const numW = this.kit.numberWidth(num, 'title', 2), numH = this.kit.digitHeight('title');
        const w = label.width + gap + numW, h = Math.max(label.height, numH);
        const k = Math.min(1, this.levelTime / LEVEL_BANNER_POP);
        const s = 1 + 2.7 * (k - 1) ** 3 + 1.7 * (k - 1) ** 2;    // -- ease-out-back
        let sw = w, sh = h;
        if (k < 1) {
            sw = Math.max(1, Math.trunc(w * s));
            sh = Math.max(1, Math.trunc(h * s));
        }
        const alpha = Math.trunc(255 * Math.min(1, (LEVEL_BANNER_TIME - this.levelTime) / 0.4));
        c.save();
        c.translate(WIDTH / 2 - Math.trunc(sw / 2), LEVEL_BANNER_Y - Math.trunc(sh / 2));
        c.scale(sw / w, sh / h);
        Gfx.blit(c, label, 0, Math.trunc((h - label.height) / 2), alpha);
        this.kit.drawNumber(c, num, label.width + gap, Math.trunc((h - numH) / 2) + Math.trunc(numH / 2), 'title', -1, 2, alpha);
        c.restore();
    }

    drawTimerBar(c, bar, value, color, shine) {
        const fillW = Math.trunc(bar.w * value);
        Gfx.roundBox(c, COLOR_OUTLINE, bar.inflate(6, 6), 6);
        Gfx.roundBox(c, COLOR_SLIDER_BACK, bar, 4);
        if (fillW > 0) {
            Gfx.roundRect(c, color, bar.x, bar.y, fillW, bar.h, 4);
            Gfx.fill(c, shine, bar.x + 2, bar.y + 2, Math.max(0, fillW - 4), 2);
        }
    }

    /** поки діє сповільнення, все трохи фіолетовіє (плавно з'являється і зникає разом зі швидкістю) */
    drawSlowTint(c) {
        const k = (1 - this.speedK) / (1 - SLOW_FACTOR);
        if (k < 0.02) {
            return;
        }
        Gfx.fill(c, SLOW_TINT, -this.ox, -this.oy, this.viewW, this.viewH, Math.trunc(SLOW_TINT_ALPHA * Math.min(1, k)));
    }

    takePowerup(kind) {
        if (kind === 'shield') {
            this.shield = true;
        } else {
            const i = BOOST_KINDS.indexOf(kind);
            this.boost[i] = BOOST_TIME[i];
        }
        this.sfx.play('powerup');
    }

    /** удар об трубу / землю / стелю: щит лопає і дає секунду невразливості, без щита -- кінець гри */
    hit() {
        if (this.grace > 0) {
            return;
        }
        if (this.shield) {
            this.shield = false;
            this.grace = SHIELD_GRACE;
            this.pops.push([BIRD_START_X + BIRD_SIZE / 2, this.birdY + BIRD_SIZE / 2, 0]);
            this.sfx.play('shield_break');
        } else {
            this.over = true;
        }
    }

    /** монетки малюються на всьому полотні (як і труби) */
    drawCoins(c) {
        const frames = this.kit.coin.frames;
        for (const coin of this.coins) {
            const img = frames[Math.trunc(this.tTotal * COIN_FPS + coin.phase) % frames.length];
            if (!coin.taken) {
                Gfx.blitCenter(c, img, Math.trunc(coin.x), Math.trunc(coin.y));
            } else {
                // -- підібрана: летить вгору, трохи росте і зникає
                const k = coin.takenT / COIN_PICKUP_TIME;
                Gfx.blitScaledCenter(c, img, Math.trunc(coin.x), Math.trunc(coin.y - 34 * k), 1 + 0.5 * k, Math.trunc(255 * (1 - k)), false);
                if (coin.value > 1) {           // -- з x2 над монеткою вилітає «+2»
                    this.kit.drawNumber(c, '+' + coin.value, Math.trunc(coin.x), Math.trunc(coin.y - 22 - 40 * k), 'light', 0, 2,
                        Math.trunc(255 * (1 - k * k)));
                }
            }
        }
    }

    counterWidth(icon, value) {
        return icon.width + 6 + this.kit.numberWidth(value);
    }

    /** іконка + число (світлі цифри), x -- лівий край, y -- центр */
    drawCounter(c, icon, value, x, y) {
        Gfx.blitCenter(c, icon, x + Math.trunc(icon.width / 2), y);
        this.kit.drawNumber(c, value, x + icon.width + 6, y, 'light', -1, 2, 255);
    }

    /** рядок панелі: підпис зліва, значення (і іконка) справа, все по центру y */
    drawRow(c, panel, y, key, value, icon) {
        const label = this.kit.text(key);
        Gfx.blit(c, label, panel.x + 26, y - Math.trunc(label.height / 2));
        if (!icon) {
            this.kit.drawNumber(c, value, panel.right() - 26, y, 'light', 1, 2, 255);
        } else {
            this.drawCounter(c, icon, value, panel.right() - 26 - this.counterWidth(icon, value), y);
        }
    }

    /** y центрів n рядків, рівномірно всередині панелі */
    static panelRows(panel, n) {
        const top = panel.y + PANEL_INNER_TOP;
        const h = panel.h - PANEL_INNER_TOP - PANEL_INNER_BOTTOM;
        return Array.from({ length: n }, (_, i) => Math.round(top + h * (i + 0.5) / n));
    }

    drawPanel(c, r) {
        Gfx.blit(c, this.kit.panel.render(r.w, r.h), r.x, r.y);
    }

    /** смерть: оновлюємо рекорд і зберігаємо прогрес */
    finishRun() {
        if (this.runSaved) {
            return;
        }
        this.newRecord = this.score > this.progress.best;
        if (this.newRecord) {
            this.progress.best = this.score;
        }
        this.progress.games += 1;
        this.store.saveProgress(this.progress);
        this.runSaved = true;
    }

    // -- налаштування
    static sliderValue(rect, x) {
        return Math.max(0, Math.min(1, (x - rect.x) / rect.w));
    }

    /** повзунок, який тягнуть: гучність у налаштуваннях або товщина свого шлейфу в редакторі */
    dragSlider(name, x) {
        if (name === 'trail_width') {
            this.kit.customTrail.config.width = round2(Game.sliderValue(EDIT_WIDTH, x));
        } else {
            this.setSlider(name, Game.sliderValue(SLIDERS[SLIDER_NAMES.indexOf(name)], x));
        }
    }

    setSlider(name, value) {
        this.config[name] = round2(value);
        if (name === 'sfx') {
            this.sfx.setLevel(this.config.sfx);
        } else {
            this.music.setLevel(name.split('_')[0], this.config[name]);
        }
    }

    /** перемикає мову вперед/назад по колу */
    langStep(step) {
        const i = Math.max(0, LANGS.indexOf(this.config.lang));
        this.config.lang = LANGS[mod(i + step, LANGS.length)];
        this.kit.setLang(this.config.lang);
        this.store.saveConfig(this.config);
    }

    drawSliderBar(c, rect, value, numberX) {
        const fillW = Math.trunc(rect.w * value);
        Gfx.roundBox(c, COLOR_OUTLINE, rect.inflate(6, 6), 6);
        Gfx.roundBox(c, COLOR_SLIDER_BACK, rect, 4);
        if (fillW > 0) {
            Gfx.roundRect(c, COLOR_SLIDER_FILL, rect.x, rect.y, fillW, rect.h, 4);
            Gfx.fill(c, COLOR_SLIDER_SHINE, rect.x + 3, rect.y + 3, Math.max(0, fillW - 6), 3);
        }
        // -- ручка
        const knob = new Box(rect.x + fillW - 11, rect.centerY() - 15, 22, 30);
        Gfx.roundBox(c, COLOR_OUTLINE, knob.inflate(6, 6), 7);
        Gfx.roundBox(c, COLOR_KNOB_SHADE, knob, 5);
        Gfx.roundRect(c, COLOR_KNOB, knob.x, knob.y, knob.w, knob.h - 6, 5);
        this.kit.drawNumber(c, Math.round(value * 100) + '%', numberX, rect.centerY(), 'dark', 0, 2, 255);
    }

    /** зелений трикутник-стрілка з контуром (як іконка PLAY) */
    drawArrow(c, cx, cy, dir, hover) {
        const w = 12, h = 14;
        Gfx.polygon(c, COLOR_OUTLINE, cx - w * dir, cy - h, cx + w * dir, cy, cx - w * dir, cy + h);
        Gfx.polygon(c, hover ? COLOR_ARROW_HOVER : COLOR_ARROW,
            cx - (w - 4) * dir, cy - h + 6, cx + (w - 5) * dir, cy, cx - (w - 4) * dir, cy + h - 6);
    }

    /** панель перемикача зі стрілками < ... >, посередині -- картинка label */
    drawSelectorBox(c, rect, label) {
        this.drawPanel(c, rect);
        if (label) {
            Gfx.blitCenter(c, label, rect.centerX(), rect.centerY() - 1);
        }
        const left = new Box(rect.x, rect.y, SELECTOR_ARROW, rect.h);
        const right = new Box(rect.right() - SELECTOR_ARROW, rect.y, SELECTOR_ARROW, rect.h);
        this.drawArrow(c, left.centerX() + 2, rect.centerY() - 1, -1, this.hover(left));
        this.drawArrow(c, right.centerX() - 2, rect.centerY() - 1, 1, this.hover(right));
    }

    /** кнопка MENU під панеллю налаштувань (з рядком «конфіденційність» панель довша) */
    settingsBack() {
        return this.ads.privacyRequired() ? BACK_BTN_PRIVACY : BACK_BTN_RECT;
    }

    drawSettings(c) {
        Gfx.blitCenter(c, this.kit.text('settings'), WIDTH / 2, SETTINGS_TITLE_Y);
        this.drawPanel(c, this.ads.privacyRequired() ? SETTINGS_PANEL_PRIVACY : SETTINGS_PANEL);
        ROWS.forEach((r, i) => Gfx.blit(c, this.kit.text(r), SETTINGS_PANEL.x + 26, ROW_Y0 + i * ROW_H));
        this.drawSelectorBox(c, LANG_SELECTOR, this.kit.langNames[this.config.lang]);
        SLIDERS.forEach((s, i) => this.drawSliderBar(c, s, this.config[SLIDER_NAMES[i]], SETTINGS_PANEL.right() - 44));
        if (this.ads.privacyRequired()) {
            this.drawPanel(c, PRIVACY_BTN);
            if (this.hover(PRIVACY_BTN)) {
                Gfx.roundBoxStroke(c, COLOR_CARD_HOVER, PRIVACY_BTN.inflate(-4, -6).move(0, -2), 2, 8);
            }
            Gfx.blitCenter(c, this.kit.text('privacy'), PRIVACY_BTN.centerX(), PRIVACY_BTN.centerY() - 1);
        }
    }

    settingsClick(x, y) {
        if (this.ads.privacyRequired() && PRIVACY_BTN.contains(x, y)) {
            this.ads.showPrivacy();
            return;
        }
        if (LANG_SELECTOR.contains(x, y)) {
            this.langStep(x < LANG_SELECTOR.x + SELECTOR_ARROW ? -1 : 1);
            return;
        }
        for (let i = 0; i < SLIDERS.length; i++) {
            if (SLIDERS[i].inflate(SLIDER_GRAB * 2, SLIDER_GRAB * 2).contains(x, y)) {
                this.dragging = SLIDER_NAMES[i];
                this.dragSlider(this.dragging, x);
                return;
            }
        }
        if (this.settingsBack().contains(x, y)) {
            this.press('back');
        }
    }

    press(name) {
        this.pressed = name;
        this.pressTime = 0;
    }

    // -- екрани
    /** монетки в лівому верхньому куті екрана (валюта магазину) */
    drawMenuCounters(c) {
        c.save();
        c.translate(this.hudLeft, this.hudTop);
        this.drawPanel(c, COINS_CHIP);
        this.drawCounter(c, this.kit.coinIcon, String(this.progress.coins), COINS_CHIP.x + 12, COINS_CHIP.centerY() - 3);
        c.restore();
    }

    // -- монети за рекламу
    /** скільки ще переглядів можна зараз (старші за добу не рахуються; «майбутні» -- ніби щойно) */
    adsLeft(t) {
        return Math.max(0, AD_LIMIT - this.progress.ad_views.filter((v) => t - v < AD_WINDOW).length);
    }

    /** через скільки сек звільниться наступний перегляд */
    adWait(t) {
        const views = this.progress.ad_views.filter((v) => t - v < AD_WINDOW).map((v) => Math.min(v, t));
        return views.length ? Math.min(...views) + AD_WINDOW - t : 0;
    }

    /** кнопка «монети за рекламу»: ліміт -- «повертайся пізніше»; ролик ще не завантажився -- «ще не готова» */
    watchAd() {
        if (this.adsLeft(now()) === 0) {
            this.adNote = 'ad_limit';
            this.adNoteTime = AD_NOTE_TIME;
        } else if (!this.ads.ready()) {
            this.ads.load();
            this.adNote = 'ad_wait';
            this.adNoteTime = AD_NOTE_TIME;
        } else {
            this.ads.show(() => this.adReward());
        }
    }

    /** ролик додивились: монети, перегляд записуємо (для ліміту) і одразу зберігаємо */
    adReward() {
        const t = now();
        this.progress.ad_views = this.progress.ad_views.filter((v) => t - v < AD_WINDOW).map((v) => Math.min(v, t));
        this.progress.ad_views.push(t);
        this.progress.coins += AD_REWARD;
        this.store.saveProgress(this.progress);
        this.adRewardFx = true;
        this.adNoteTime = 0;     // -- «ще не готова» від попереднього натискання вже не до речі
    }

    /** 4:05:09 -- скільки годин, хвилин і секунд лишилось */
    static clock(sec) {
        sec = Math.max(0, sec);
        const m = Math.floor(sec / 60) % 60, s = sec % 60;
        return Math.floor(sec / 3600) + (m < 10 ? ':0' : ':') + m + (s < 10 ? ':0' : ':') + s;
    }

    /**
     * кнопка реклами під лічильником монет (біля лівого верхнього краю екрана). Під нею -- золоті квадратики
     * (скільки переглядів ще можна, сірі -- вже використані) або таймер до наступного; над нею злітає «+5»
     */
    drawAd(c) {
        const t = now();
        const left = this.adsLeft(t);
        c.save();
        c.translate(this.hudLeft, this.hudTop);
        this.kit.ad.draw(c, this.tTotal);
        if (left > 0) {
            let x = AD_BTN.centerX() - Math.trunc((AD_LIMIT * AD_PIP + (AD_LIMIT - 1) * AD_PIP_GAP) / 2);
            const y = AD_INFO_Y - AD_PIP / 2;
            for (let i = 0; i < AD_LIMIT; i++, x += AD_PIP + AD_PIP_GAP) {
                Gfx.roundRect(c, COLOR_OUTLINE, x - 3, y - 3, AD_PIP + 6, AD_PIP + 6, 5);
                Gfx.roundRect(c, i < left ? AD_PIP_COLOR : COLOR_SLIDER_BACK, x, y, AD_PIP, AD_PIP, 3);
                if (i < left) {
                    Gfx.fill(c, AD_PIP_SHINE, x + 2, y + 2, AD_PIP - 4, 2);
                }
            }
        } else {
            this.kit.drawNumber(c, Game.clock(this.adWait(t)), AD_BTN.centerX(), AD_INFO_Y + 2);
        }
        if (this.adRewardT >= 0) {
            const k = this.adRewardT / AD_REWARD_TIME;
            this.kit.drawNumber(c, '+' + AD_REWARD, AD_BTN.right() + 26, AD_BTN.centerY() - 6 - 36 * k, 'light', 0, 2,
                Math.trunc(255 * (1 - k * k)));
        }
        c.restore();
        if (this.adNoteTime > 0 && Math.trunc((AD_NOTE_TIME - this.adNoteTime) * 6) % 2 === 0) {
            Gfx.blitCenter(c, this.kit.text(this.adNote), WIDTH / 2, AD_NOTE_Y);
        }
    }

    /** панель після смерті: рахунок, рекорд, монетки за гру */
    drawResult(c, slide) {
        const panel = RESULT_PANEL.move(0, slide);
        this.drawPanel(c, panel);
        const ys = Game.panelRows(panel, 4);
        this.drawRow(c, panel, ys[0], 'score', String(this.score), null);
        this.drawRow(c, panel, ys[1], 'level', String(this.level + 1), null);
        this.drawRow(c, panel, ys[2], 'best', String(this.progress.best), null);
        this.drawRow(c, panel, ys[3], 'coins', '+' + this.runCoins, this.kit.coinIcon);
        if (this.newRecord) {
            const bob = Math.round(Math.sin(this.tTotal * 6) * 3);
            Gfx.blitCenter(c, this.kit.text('new_record'), WIDTH / 2, panel.bottom() + 16 + bob);
        }
    }

    /** екран рекордів: кубок, найкращий рахунок великими цифрами, скільки ігор і монет */
    drawRecords(c) {
        Gfx.blitCenter(c, this.kit.text('records'), WIDTH / 2, RECORDS_TITLE_Y);
        const panel = RECORDS_PANEL;
        this.drawPanel(c, panel);
        const trophy = this.kit.trophyBig;
        const bob = Math.round(Math.sin(this.tTotal * 2.4) * 3);
        Gfx.blitCenter(c, trophy, WIDTH / 2, panel.y + 26 + Math.trunc(trophy.height / 2) + bob);
        this.kit.drawNumber(c, String(this.progress.best), WIDTH / 2, panel.y + 150, 'big', 0, 3, 255);
        const rows = new Box(panel.x, panel.y + 190, panel.w, panel.h - 190);
        const ys = Game.panelRows(rows, 2);
        Gfx.line(c, COLOR_KNOB_SHADE, panel.x + 24, rows.y, panel.right() - 24, rows.y, 2);
        this.drawRow(c, panel, ys[0], 'games', String(this.progress.games), null);
        this.drawRow(c, panel, ys[1], 'coins', String(this.progress.coins), this.kit.coinIcon);
    }

    // -- магазин: на кожній вкладці -- що продається, де в збереженні обране і куплене
    shopItems(tab) {
        return { birds: this.kit.skins, trails: this.kit.trails, pipes: this.kit.pipes }[tab] || this.kit.backgrounds;
    }

    static PICK = { birds: 'skin', trails: 'trail', pipes: 'pipe', backgrounds: 'background' };
    static OWNED = { birds: 'owned', trails: 'owned_trails', pipes: 'owned_pipes', backgrounds: 'owned_backgrounds' };

    shopPick(tab) {
        return this.progress[Game.PICK[tab]];
    }

    shopOwned(tab) {
        return this.progress[Game.OWNED[tab]];
    }

    shopSelect(tab, id) {
        const set = { birds: 'setSkin', trails: 'setTrail', pipes: 'setPipe', backgrounds: 'setBackground' }[tab];
        this.progress[Game.PICK[tab]] = this.kit[set](id);
    }

    /** прямокутники вкладок в один ряд: кожна вкладка ширша за свій напис на однаковий запас */
    shopTabs() {
        const widths = SHOP_TAB_NAMES.map((n) => this.kit.text('tab_' + n).width);
        const sum = widths.reduce((a, b) => a + b, 0);
        const pad = (SHOP_TABS_ROW.w - SHOP_TAB_GAP * (widths.length - 1) - sum) / widths.length;
        const rects = {};
        let x = SHOP_TABS_ROW.x;
        SHOP_TAB_NAMES.forEach((name, i) => {
            const l = Math.round(x);
            rects[name] = new Box(l, SHOP_TABS_ROW.y, Math.round(x + widths[i] + pad) - l, SHOP_TABS_ROW.h);
            x += widths[i] + pad + SHOP_TAB_GAP;
        });
        return rects;
    }

    /** прямокутник i-ї картки поточної вкладки з урахуванням прокрутки */
    shopCard(i) {
        const x0 = SHOP_PANEL.x + Math.trunc((SHOP_PANEL.w - SHOP_COLS * CARD_W - (SHOP_COLS - 1) * CARD_GAP) / 2);
        const y0 = SHOP_PANEL.y + CARD_PAD_TOP - this.shopScroll;
        const row = Math.trunc(i / SHOP_COLS), col = i % SHOP_COLS;
        return new Box(x0 + col * (CARD_W + CARD_GAP), y0 + row * (CARD_H + CARD_GAP), CARD_W, CARD_H);
    }

    /** видима частина вікна магазину (все, що нижче/вище -- обрізається) */
    static shopView() {
        return new Box(SHOP_PANEL.x, SHOP_PANEL.y + PANEL_INNER_TOP, SHOP_PANEL.w, SHOP_PANEL.h - PANEL_INNER_TOP - PANEL_INNER_BOTTOM);
    }

    shopMaxScroll() {
        const rows = Math.ceil(this.shopItems(this.shopTab).length / SHOP_COLS);
        const content = CARD_PAD_TOP * 2 + rows * CARD_H + (rows - 1) * CARD_GAP;
        return Math.max(0, content - Game.shopView().h);
    }

    /** тап по вкладці -- перемикаємо; по картці -- купити або обрати; свій шлейф -- відкривається редактор */
    shopClick(x, y) {
        for (const [name, rect] of Object.entries(this.shopTabs())) {
            if (rect.contains(x, y)) {
                this.shopTab = name;
                this.shopScroll = 0;
                this.notEnough = 0;
                return;
            }
        }
        if (!Game.shopView().contains(x, y)) {
            return;
        }
        const items = this.shopItems(this.shopTab);
        const owned = this.shopOwned(this.shopTab);
        for (let i = 0; i < items.length; i++) {
            const item = items[i];
            if (!this.shopCard(i).contains(x, y)) {
                continue;
            }
            let edit = item === this.kit.customTrail && this.shopPick(this.shopTab) === item.id;
            if (!owned.includes(item.id)) {
                if (this.progress.coins < item.price) {
                    this.notEnough = NOT_ENOUGH_TIME;
                    return;
                }
                this.progress.coins -= item.price;
                owned.push(item.id);
                this.sfx.play('coin');
                edit = item === this.kit.customTrail;
            }
            this.shopSelect(this.shopTab, item.id);
            this.store.saveProgress(this.progress);
            if (edit) {
                this.openEditor();
            }
            return;
        }
    }

    /**
     * рамка кадру пташки без порожніх країв (запас під крила) -- одна на всі кадри, щоб пташка не смикалась.
     * Піксель-арт збільшуємо так, щоб кожен художній піксель став цілим числом пікселів
     */
    previewBox(bird) {
        let box = this.previewBoxes.get(bird.id);
        if (!box) {
            let l = Infinity, t = Infinity, r = -1, b = -1;
            for (const f of bird.anim.frames) {
                const cv = Gfx.canvas(f.width, f.height);
                const c = cv.getContext('2d', { willReadFrequently: true });
                c.drawImage(f.src, f.sx, f.sy, f.width, f.height, 0, 0, f.width, f.height);
                const d = c.getImageData(0, 0, f.width, f.height).data;
                for (let y = 0; y < f.height; y++) {
                    for (let x = 0; x < f.width; x++) {
                        if (d[(y * f.width + x) * 4 + 3] !== 0) {
                            l = Math.min(l, x);
                            r = Math.max(r, x);
                            t = Math.min(t, y);
                            b = Math.max(b, y);
                        }
                    }
                }
            }
            box = r < 0 ? new Box(0, 0, bird.w, bird.h) : new Box(l, t, r + 1 - l, b + 1 - t);
            this.previewBoxes.set(bird.id, box);
        }
        return box;
    }

    /** розмір кадру пташки на картці: [w, h, чи чітко (без згладжування)] */
    previewSize(bird, frameBox) {
        const box = this.previewBox(bird);
        let k = Math.min(frameBox[0] / box.w, frameBox[1] / box.h);
        if (bird.artPx > 0 && k >= 1) {
            k = Math.max(1, Math.floor(k * bird.artPx)) / bird.artPx;
        } else if (k >= 2) {
            k = Math.trunc(k);
        }
        return [Math.round(box.w * k), Math.round(box.h * k), bird.artPx > 0 || k === Math.trunc(k)];
    }

    drawPreview(c, bird, frame, frameBox, cx, cy) {
        const [w, h, crisp] = this.previewSize(bird, frameBox);
        const box = this.previewBox(bird);
        Gfx.blitAreaTo(c, bird.anim.frames[frame], box.x, box.y, box.w, box.h,
            Math.trunc(cx) - Math.trunc(w / 2), Math.trunc(cy) - Math.trunc(h / 2), w, h, !crisp);
    }

    /** картка шлейфу: обрана пташка гойдається, а за нею тягнеться шлейф (там, де вона щойно була) */
    drawTrailPreview(c, trail, rect) {
        const bird = this.kit.bird;
        const frame = Math.trunc(this.tTotal * bird.anim.fps) % bird.anim.frames.length;
        const size = this.previewSize(bird, TRAIL_PREVIEW);
        const bx = rect.right() - 14 - Math.trunc(size[0] / 2);
        const n = 24, length = bx - rect.x - 2;
        const waveY = (t) => rect.y + 50 + Math.sin(t * 3) * 8;
        this.pts.clear();
        for (let j = 0; j <= n; j++) {
            this.pts.add(bx - 6 - length * j / n, waveY(this.tTotal - 0.8 * j / n), j / n, (j * 0.618) % 1);
        }
        c.save();
        Gfx.clipBox(c, rect.inflate(-6, -6).clip(Game.shopView()));
        trail.draw(c, this.pts, this.tTotal);
        c.restore();
        this.drawPreview(c, bird, frame, TRAIL_PREVIEW, bx, waveY(this.tTotal));
    }

    /** мініатюра фону на картці (картинка вдвічі більша за рамку -- для чіткості) */
    drawThumb(c, themeId, rect) {
        const img = this.scenery.thumbnail(themeId, BG_THUMB[0], BG_THUMB[1]);
        const box = new Box(rect.centerX() - BG_THUMB[0] / 2, rect.y + 48 - BG_THUMB[1] / 2, BG_THUMB[0], BG_THUMB[1]);
        Gfx.roundBox(c, COLOR_OUTLINE, box.inflate(6, 6), 5);
        Gfx.blitTo(c, img, box.x, box.y, box.w, box.h, true);
        return box;
    }

    /** картка труб: мініатюра обраного фону, на ній дві маленькі труби -- одна росте з землі, друга звисає з неба */
    drawPipePreview(c, pipe, rect) {
        const box = this.drawThumb(c, this.progress.background, rect);
        const ground = box.y + Math.round((this.groundY - Scenery.THUMB_TOP) * box.h / Scenery.THUMB_H);
        c.save();
        Gfx.clipBox(c, new Box(box.x, box.y, box.w, ground - box.y).clip(Game.shopView()));
        const mini = pipe.mini;
        for (const [px, mid] of PIPE_PREVIEW) {
            mini.draw(c, box.x + px, mini.capW, box.y + mid - PIPE_PREVIEW_GAP / 2, PIPE_PREVIEW_GAP, ground, box.y);
        }
        c.restore();
    }

    drawCard(c, item, rect) {
        const selected = item.id === this.shopPick(this.shopTab);
        const owned = this.shopOwned(this.shopTab).includes(item.id);
        this.drawPanel(c, rect);
        const frame = rect.inflate(-4, -6).move(0, -2);
        if (selected) {
            Gfx.roundBoxStroke(c, COLOR_ARROW, frame, 3, 8);
        } else if (this.hover(rect) && this.hover(Game.shopView())) {
            Gfx.roundBoxStroke(c, COLOR_CARD_HOVER, frame, 2, 8);
        }
        if (this.shopTab === 'birds') {
            // -- пташка махає крилами (кожна зі своєю швидкістю кадрів)
            const i = Math.trunc(this.tTotal * item.anim.fps) % item.anim.frames.length;
            this.drawPreview(c, item, i, CARD_PREVIEW, rect.centerX(), rect.y + 50);
        } else if (this.shopTab === 'trails') {
            this.drawTrailPreview(c, item, rect);
        } else if (this.shopTab === 'pipes') {
            this.drawPipePreview(c, item, rect);
        } else {
            this.drawThumb(c, item.id, rect);
        }
        const y = rect.bottom() - 34;
        if (selected) {
            // -- обраний свій шлейф можна змінити (тап по картці відкриває редактор)
            Gfx.blitCenter(c, this.kit.text(item === this.kit.customTrail ? 'edit' : 'selected'), rect.centerX(), y);
        } else if (owned) {
            Gfx.blitCenter(c, this.kit.text('select'), rect.centerX(), y);
        } else {
            const price = String(item.price);
            const w = this.counterWidth(this.kit.coinIcon, price);
            this.drawCounter(c, this.kit.coinIcon, price, rect.centerX() - Math.trunc(w / 2), y);
        }
    }

    /** вкладки: активна -- з зеленою рамкою, інші -- трохи темніші */
    drawTabs(c) {
        for (const [name, rect] of Object.entries(this.shopTabs())) {
            const active = name === this.shopTab;
            const img = this.kit.panel.render(rect.w, rect.h);
            Gfx.blit(c, active ? img : Gfx.darkened(img, TAB_DIM), rect.x, rect.y);
            const frame = rect.inflate(-4, -6).move(0, -2);
            if (active) {
                Gfx.roundBoxStroke(c, COLOR_ARROW, frame, 3, 8);
            } else if (this.hover(rect)) {
                Gfx.roundBoxStroke(c, COLOR_CARD_HOVER, frame, 2, 8);
            }
            Gfx.blitCenter(c, this.kit.text('tab_' + name), rect.centerX(), rect.centerY() - 3);
        }
    }

    drawShop(c) {
        Gfx.blitCenter(c, this.kit.text('shop_title'), WIDTH / 2, SHOP_TITLE_Y);
        this.drawTabs(c);
        this.drawPanel(c, SHOP_PANEL);
        const view = Game.shopView();
        c.save();
        Gfx.clipBox(c, view);
        this.shopItems(this.shopTab).forEach((item, i) => {
            const rect = this.shopCard(i);
            if (rect.overlaps(view)) {
                this.drawCard(c, item, rect);
            }
        });
        c.restore();
        // -- смужка прокрутки, якщо карток більше, ніж влазить
        const top = this.shopMaxScroll();
        if (top > 0) {
            const h = Math.max(30, Math.trunc(view.h * view.h / (view.h + top)));
            const y = view.y + Math.trunc((view.h - h) * this.shopScroll / top);
            Gfx.roundRect(c, COLOR_KNOB_SHADE, SHOP_PANEL.right() - 12, y, 5, h, 3);
        }
        if (this.notEnough > 0 && Math.trunc((NOT_ENOUGH_TIME - this.notEnough) * 6) % 2 === 0) {
            Gfx.blitCenter(c, this.kit.text('not_enough'), WIDTH / 2, SHOP_PANEL.bottom() + 10);
        }
    }

    // -- редактор свого шлейфу
    openEditor() {
        this.editing = true;
        this.editSlot = 0;
        this.notEnough = 0;
        this.editPts = [];
    }

    /** назад у магазин; вибір уже діє (редактор міняє налаштування шлейфу на льоту) -- лишається зберегти */
    closeEditor() {
        this.editing = false;
        this.dragging = null;
        this.store.saveProgress(this.progress);
    }

    /** квадратик i-го кольору палітри: 2 ряди по PALETTE_COLS */
    static paletteRect(i) {
        const row = Math.trunc(i / PALETTE_COLS), col = i % PALETTE_COLS;
        return new Box(PALETTE_X + col * (SWATCH_W + SWATCH_GAP), PALETTE_Y + row * (SWATCH_H + SWATCH_GAP), SWATCH_W, SWATCH_H);
    }

    /** у перегляді пташка плавно літає вгору-вниз; це y центру тіла -- зсуваємо, щоб уся картинка була по центру */
    editBirdY(t) {
        const bird = this.kit.bird;
        return EDIT_PREVIEW.centerY() + (bird.ay - bird.h / 2) + Math.sin(t * 3) * EDIT_BIRD_BOB;
    }

    /** точки шлейфу в перегляді: як у грі -- їдуть разом зі світом і згасають */
    updateEditPreview() {
        for (const p of this.editPts) {
            p[0] -= LEVELS[0].speed;
            p[2] += this.dts;
        }
        removeOld(this.editPts, TRAIL_LIFE);
        this.editPts.push([EDIT_BIRD_X - 6, this.editBirdY(this.tTotal), 0, Math.random()]);
    }

    /** квадратик кольору з контуром і бліком (як доріжка повзунка); frame -- колір рамки навколо (null -- без неї) */
    drawSwatch(c, rect, color, frame) {
        Gfx.roundBox(c, COLOR_OUTLINE, rect.inflate(6, 6), 6);
        Gfx.roundBox(c, color, rect, 4);
        const r = (color >> 16) & 255, g = (color >> 8) & 255, b = color & 255;
        const shine = rgb(r + Math.trunc((255 - r) * 2 / 5), g + Math.trunc((255 - g) * 2 / 5), b + Math.trunc((255 - b) * 2 / 5));
        Gfx.fill(c, shine, rect.x + 3, rect.y + 3, rect.w - 6, 3);
        if (frame != null) {
            Gfx.roundBoxStroke(c, frame, rect.inflate(12, 12), 2, 8);
        }
    }

    /** небо поточного фону, на ньому пташка зі своїм шлейфом */
    drawEditPreview(c) {
        const box = EDIT_PREVIEW;
        Gfx.roundBox(c, COLOR_OUTLINE, box.inflate(6, 6), 6);
        Gfx.blitArea(c, this.scenery.sky, box.x, box.y + 160, box.w, box.h, box.x, box.y);
        c.save();
        Gfx.clipBox(c, box);
        this.trailPoints(this.editPts);
        this.kit.customTrail.draw(c, this.pts, this.tTotal);
        const bird = this.kit.bird;
        const y = this.editBirdY(this.tTotal);
        const v = this.editBirdY(this.tTotal + 1 / FPS) - y;          // -- px за кадр, як birdV у грі
        const angle = Math.max(BIRD_MAX_DOWN, Math.min(BIRD_MAX_UP, -v * 8));
        bird.draw(c, EDIT_BIRD_X, y, angle, Math.trunc(this.tTotal * bird.anim.fps));
        c.restore();
    }

    /** точки шлейфу (від найстаріших до найновіших) -> pts від голови до хвоста */
    trailPoints(list) {
        this.pts.clear();
        for (let i = list.length - 1; i >= 0; i--) {
            const p = list[i];
            this.pts.add(p[0], p[1], p[2] / TRAIL_LIFE, p[3]);
        }
    }

    drawEditor(c) {
        const cfg = this.kit.customTrail.config;
        Gfx.blitCenter(c, this.kit.text('custom_title'), WIDTH / 2, EDIT_TITLE_Y);
        this.drawPanel(c, EDIT_PANEL);
        this.drawEditPreview(c);
        // -- кольори: два квадратики (біля пташки -> хвіст), обраний -- у зеленій рамці; під ними палітра
        const label = this.kit.text('colors');
        Gfx.blit(c, label, EDIT_LABEL_X, EDIT_SLOTS[0].centerY() - Math.trunc(label.height / 2));
        EDIT_SLOTS.forEach((rect, i) => {
            const frame = i === this.editSlot ? COLOR_ARROW : this.hover(rect) ? COLOR_CARD_HOVER : null;
            this.drawSwatch(c, rect, PALETTE[i === 0 ? cfg.c1 : cfg.c2], frame);
        });
        this.drawArrow(c, (EDIT_SLOTS[0].right() + EDIT_SLOTS[1].x) / 2, EDIT_SLOTS[0].centerY(), 1, false);
        const current = this.editSlot === 0 ? cfg.c1 : cfg.c2;
        PALETTE.forEach((color, i) => {
            const rect = Game.paletteRect(i);
            const frame = i === current ? COLOR_ARROW : this.hover(rect) ? COLOR_CARD_HOVER : null;
            this.drawSwatch(c, rect, color, frame);
        });
        Gfx.blit(c, this.kit.text('style'), EDIT_LABEL_X, EDIT_STYLE_Y);
        this.drawSelectorBox(c, EDIT_STYLE, this.kit.text('style_' + cfg.style));
        Gfx.blit(c, this.kit.text('width'), EDIT_LABEL_X, EDIT_WIDTH_Y);
        this.drawSliderBar(c, EDIT_WIDTH, cfg.width, EDIT_PANEL.right() - 44);
    }

    editorClick(x, y) {
        const cfg = this.kit.customTrail.config;
        for (let i = 0; i < EDIT_SLOTS.length; i++) {
            if (EDIT_SLOTS[i].inflate(8, 8).contains(x, y)) {
                this.editSlot = i;
                return;
            }
        }
        for (let i = 0; i < PALETTE.length; i++) {
            if (Game.paletteRect(i).inflate(SWATCH_GAP, SWATCH_GAP).contains(x, y)) {
                cfg[this.editSlot === 0 ? 'c1' : 'c2'] = i;
                return;
            }
        }
        if (EDIT_STYLE.contains(x, y)) {
            const step = x < EDIT_STYLE.x + SELECTOR_ARROW ? -1 : 1;
            cfg.style = STYLES[mod(STYLES.indexOf(cfg.style) + step, STYLES.length)];
            return;
        }
        if (EDIT_WIDTH.inflate(SLIDER_GRAB * 2, SLIDER_GRAB * 2).contains(x, y)) {
            this.dragging = 'trail_width';
            this.dragSlider(this.dragging, x);
        }
    }

    resetGame() {
        this.birdY = BIRD_START_Y;
        this.birdV = 0;
        this.score = 0;
        this.level = 0;
        this.levelSpeed = LEVELS[0].speed;
        this.levelTime = 0;        // -- на старті теж показуємо «РІВЕНЬ 1»
        this.runCoins = 0;
        this.newRecord = false;
        this.runSaved = false;
        this.over = false;
        this.paused = false;
        this.start = true;
        this.shield = false;
        this.grace = 0;
        this.boost = [0, 0];
        this.speedK = 1;
        this.pops = [];
        this.trailPts = [];
        this.newPipes();
        this.scenery.update(0, this.levelSpeed * FPS, true);   // -- фон їде з тією ж швидкістю, що й труби
    }

    /** повертання в головне меню після смерті */
    goToMenu() {
        this.start = false;
        this.over = false;
        this.paused = false;
    }

    /** повернення в головне меню з налаштувань / рекордів / магазину */
    closeSettings() {
        this.inSettings = false;
        this.inRecords = false;
        this.inShop = false;
        this.editing = false;
        this.dragging = null;
        this.shopTouch = false;
        this.store.saveConfig(this.config);
    }

    hover(r) {
        return this.touching && r.contains(this.touchX, this.touchY);
    }

    // -- дотики (як мишка в пайтон-версії: натиснули, повели, відпустили)
    touchDown(x, y) {
        this.touching = true;
        this.touchX = x;
        this.touchY = y;
        if (this.inSettings) {
            if (this.pressed == null) {
                this.settingsClick(x, y);
            }
        } else if (this.inRecords) {
            if (this.pressed == null && RECORDS_BACK_RECT.contains(x, y)) {
                this.press('back');
            }
        } else if (this.inShop && this.editing) {
            if (this.pressed == null) {
                if (EDIT_BACK_RECT.contains(x, y)) {
                    this.press('back');
                } else {
                    this.editorClick(x, y);
                }
            }
        } else if (this.inShop) {
            if (this.pressed == null) {
                if (SHOP_BACK_RECT.contains(x, y)) {
                    this.press('back');
                } else {
                    // -- тап по картці спрацьовує, коли палець відпустили; якщо повели -- магазин гортається
                    this.shopTouch = true;
                    this.shopDragged = false;
                    this.shopTouchX = x;
                    this.shopTouchY = y;
                    this.shopScrollStart = this.shopScroll;
                }
            }
        } else if (!this.start) {
            if (this.pressed != null || this.fading) {
                return;
            }
            for (const [name, box] of Object.entries(this.menuButtons)) {
                if (box.contains(x, y)) {
                    this.press(name);
                    break;
                }
            }
        } else if (this.paused) {
            if (this.pressed == null) {
                if (PAUSE_MENU_RECT.contains(x, y)) {
                    this.press('quit');
                } else {
                    this.paused = false;
                }
            }
        } else if (this.over) {
            if (this.overTime >= GAME_OVER_ANIM && MENU_BTN_RECT.contains(x, y)) {
                this.press('menu');
            }
        } else {
            this.birdV = JUMP_VELOCITY;
        }
    }

    touchMove(x, y) {
        this.touchX = x;
        this.touchY = y;
        if (this.dragging != null) {
            this.dragSlider(this.dragging, x);
        }
        if (this.shopTouch) {
            const dy = y - this.shopTouchY;
            if (!this.shopDragged && Math.abs(dy) > SHOP_DRAG_SLOP) {
                this.shopDragged = true;
            }
            if (this.shopDragged) {
                this.shopScroll = Math.max(0, Math.min(this.shopMaxScroll(), this.shopScrollStart - dy));
            }
        }
    }

    touchUp() {
        this.touching = false;
        if (this.dragging === 'trail_width') {
            this.store.saveProgress(this.progress);
        } else if (this.dragging != null) {
            this.store.saveConfig(this.config);
        }
        this.dragging = null;
        if (this.shopTouch) {
            this.shopTouch = false;
            if (!this.shopDragged && this.inShop && !this.editing && this.pressed == null) {
                this.shopClick(this.shopTouchX, this.shopTouchY);
            }
        }
    }

    /** коліщатко мишки в магазині (на комп'ютері) */
    wheel(dy) {
        if (this.inShop && !this.editing) {
            this.shopScroll = Math.max(0, Math.min(this.shopMaxScroll(), this.shopScroll + dy));
        }
    }

    /** другий палець під час гри -- теж стрибок (можна тапати двома руками по черзі) */
    extraTouch() {
        if (this.start && !this.over && !this.paused && !this.fading) {
            this.birdV = JUMP_VELOCITY;
        }
    }

    /** пробіл на клавіатурі */
    jumpKey() {
        if (this.start && !this.over && !this.paused) {
            this.birdV = JUMP_VELOCITY;
        }
    }

    /** «назад» (Esc на клавіатурі); false -- ми в головному меню */
    back() {
        if (this.fading || this.pressed != null) {
            return true;
        }
        if (this.editing) {
            this.closeEditor();
        } else if (this.inSettings || this.inRecords || this.inShop) {
            this.closeSettings();
        } else if (this.start && !this.over) {
            this.paused = !this.paused;
        } else if (this.over) {
            if (this.overTime >= GAME_OVER_ANIM) {
                this.goToMenu();
            }
        } else {
            return false;
        }
        return true;
    }

    /** гра не на екрані -- пауза, щоб пташка не впала, поки гравець не бачить */
    autoPause() {
        if (this.start && !this.over && !this.fading) {
            this.paused = true;
        }
    }

    /** гру згорнули: ставимо на паузу і зберігаємо (монетки з незакінченої гри теж) */
    onPause() {
        this.autoPause();
        this.touching = false;
        this.dragging = null;
        this.shopTouch = false;
        this.music.pause();
        this.save();
    }

    onResume() {
        this.music.resume();
    }

    save() {
        this.store.saveProgress(this.progress);
        this.store.saveConfig(this.config);
    }

    // -- один кадр (1/60 сек)
    step() {
        const dt = 1000 / FPS, dts = this.dts;
        this.tTotal += dts;

        // -- затримка після натискання кнопки меню перед дією
        if (this.pressed != null) {
            this.pressTime += dt;
            if (this.pressTime > PRESS_ACTION_DELAY) {
                switch (this.pressed) {
                    case 'play':
                        this.fading = true;
                        this.fade = 0;
                        break;
                    case 'shop':
                        this.inShop = true;
                        this.shopScroll = 0;
                        break;
                    case 'settings':
                        this.inSettings = true;
                        break;
                    case 'record':
                        this.inRecords = true;
                        break;
                    case 'ad':
                        this.watchAd();
                        break;
                    case 'back':
                        if (this.editing) {
                            this.closeEditor();
                        } else {
                            this.closeSettings();
                        }
                        break;
                    case 'menu':
                        this.goToMenu();
                        break;
                    case 'quit':
                        // -- з паузи в меню: гра зараховується як закінчена
                        this.over = true;
                        this.finishRun();
                        this.goToMenu();
                        break;
                    default:
                        break;
                }
                this.pressed = null;
            }
        }
        this.pressProgress = this.pressed != null ? this.pressTime / PRESS_ACTION_DELAY : 0;

        // -- затемнення екрану перед стартом гри
        if (this.fading) {
            this.fade += FADE_SPEED;
            if (this.fade >= 255) {
                this.fade = 255;
                this.fading = false;
                this.resetGame();
            }
        }

        if (this.paused) {
            this.kit.menu.update(dts, this.hover(PAUSE_MENU_RECT), this.pressed === 'quit' ? this.pressProgress : 0);
            this.music.play('game');
            this.music.update(dts);
            return;
        }

        // -- сповільнення: швидкість світу плавно йде до потрібної (гравітація і стрибок не змінюються)
        const slowed = this.start && !this.over && this.boost[SLOW] > 0;
        this.speedK += ((slowed ? SLOW_FACTOR : 1) - this.speedK) * Math.min(1, 5 * dts);
        // -- на новому рівні світ розганяється поступово
        this.levelSpeed += (LEVELS[this.level].speed - this.levelSpeed) * Math.min(1, LEVEL_EASE * dts);
        const speed = this.levelSpeed * this.speedK;

        // -- фізика
        if (this.start && !this.over) {
            this.boost = this.boost.map((b) => Math.max(0, b - dts));
            this.grace = Math.max(0, this.grace - dts);
            this.levelTime += dts;

            this.birdV += GRAVITY;
            this.birdY += this.birdV;
            const birdRect = new Box(BIRD_START_X, Math.trunc(this.birdY), BIRD_SIZE, BIRD_SIZE);

            for (const pipe of this.pipes) {
                pipe.x -= speed;
                if (!pipe.passed && pipe.x + PIPE_WIDTH < BIRD_START_X) {
                    pipe.passed = true;
                    this.score += 1;
                }
                if (BIRD_START_X + BIRD_SIZE > pipe.x && BIRD_START_X < pipe.x + PIPE_WIDTH) {
                    if (this.birdY < pipe.y || this.birdY + BIRD_SIZE > pipe.y + pipe.gap) {
                        this.hit();
                    }
                }
            }
            if (levelFor(this.score) > this.level) {
                this.levelUp();
            }
            // -- труба зникає, коли повністю виїхала за лівий край полотна
            this.pipes = this.pipes.filter((p) => p.x > -PIPE_WIDTH - this.ox);
            this.fillPipes();

            // -- монетки їдуть разом з трубами; зачепив -- підібрав
            for (const coin of this.coins) {
                coin.x -= speed;
                if (!coin.taken) {
                    const box = new Box(Math.trunc(coin.x) - COIN_HITBOX / 2, Math.trunc(coin.y) - COIN_HITBOX / 2, COIN_HITBOX, COIN_HITBOX);
                    if (!this.over && box.overlaps(birdRect)) {
                        coin.taken = true;
                        coin.takenT = 0;
                        coin.value = this.boost[X2] > 0 ? 2 : 1;
                        this.runCoins += coin.value;
                        this.progress.coins += coin.value;
                        this.sfx.play('coin');
                    }
                }
            }
            // -- бонуси теж їдуть з трубами; підібраний одразу діє
            for (const p of this.powerups) {
                p.x -= speed;
                if (!p.taken) {
                    const py = this.powerupY(p);
                    const box = new Box(Math.trunc(p.x) - POWERUP_HITBOX / 2, Math.trunc(py) - POWERUP_HITBOX / 2, POWERUP_HITBOX, POWERUP_HITBOX);
                    if (!this.over && box.overlaps(birdRect)) {
                        p.taken = true;
                        p.takenT = 0;
                        p.y = py;
                        this.takePowerup(p.kind);
                    }
                }
            }
            // -- земля і стеля (верх екрана): зі щитом пташка відскакує, без щита -- кінець гри
            const ceiling = -this.oy;
            if (this.birdY + BIRD_SIZE > this.floorY) {
                this.hit();
                if (!this.over) {
                    this.birdY = this.floorY - BIRD_SIZE;
                    this.birdV = JUMP_VELOCITY;
                }
            } else if (this.birdY < ceiling) {
                this.hit();
                if (!this.over) {
                    this.birdY = ceiling;
                    this.birdV = Math.max(this.birdV, 0);
                }
            }
        }

        // -- анімація підбору монеток і бонусів йде і після смерті
        for (const coin of this.coins) {
            if (coin.taken) {
                coin.takenT += dts;
            }
        }
        this.coins = this.coins.filter((c) => c.x > -COIN_HITBOX - this.ox && !(c.taken && c.takenT >= COIN_PICKUP_TIME));
        for (const p of this.powerups) {
            if (p.taken) {
                p.takenT += dts;
            }
        }
        this.powerups = this.powerups.filter((p) => p.x > -POWERUP_HITBOX - this.ox && !(p.taken && p.takenT >= COIN_PICKUP_TIME));
        for (const pop of this.pops) {
            pop[2] += dts;
        }
        removeOld(this.pops, SHIELD_POP_TIME);

        // -- шлейф: точки, де пролетіла пташка; їдуть разом зі світом і згасають. Після смерті нові не додаються
        for (const tp of this.trailPts) {
            tp[2] += dts;
            if (this.start && !this.over) {
                tp[0] -= speed;
            }
        }
        removeOld(this.trailPts, TRAIL_LIFE);
        if (this.start && !this.over && this.kit.trail.id !== 'none') {
            this.trailPts.push([BIRD_START_X + BIRD_SIZE / 2 - 6, this.birdY + BIRD_SIZE / 2, 0, Math.random()]);
        }

        if (this.editing) {
            this.updateEditPreview();
        }
        if (this.over) {
            this.finishRun();
        }

        // -- крила: під час гри махає швидше при стрибку, після смерті завмирає
        if (this.start && !this.over) {
            this.kit.bird.update(dts, this.birdV < 0 ? 2 : 1);
        }
        if (this.start) {
            this.kit.aura.update(dts);
            for (const a of Object.values(this.kit.powerups)) {
                a.update(dts);
            }
        }

        // -- музика: у меню своя, у грі своя; поки тягнуть повзунок гри -- грає музика гри
        this.music.play(this.start || this.dragging === 'game_music' ? 'game' : 'menu');
        this.music.update(dts);

        this.notEnough = Math.max(0, this.notEnough - dts);
        this.adNoteTime = Math.max(0, this.adNoteTime - dts);
        if (this.adRewardFx) {
            this.adRewardFx = false;
            this.adRewardT = 0;
            this.sfx.play('coin');
        } else if (this.adRewardT >= 0) {
            this.adRewardT = this.adRewardT + dts < AD_REWARD_TIME ? this.adRewardT + dts : -1;
        }
        this.overTime = this.over ? this.overTime + dts : 0;

        // -- анімація фону: у меню повільно, у грі як труби, після смерті стоїть
        if (this.over) {
            this.scenery.update(dts, 0, true);
        } else {
            this.scenery.update(dts, this.start ? speed * FPS : MENU_SCROLL_SPEED, false);
        }

        // -- поки гравець не в грі, наступний ролик вантажиться заздалегідь (якщо ліміт ще не вичерпано)
        const freeAds = this.start ? 0 : this.adsLeft(now());
        if (freeAds > 0) {
            this.ads.load();
        }
        // -- кнопки: наведення (палець на кнопці) і натискання
        if (!this.start && (this.inSettings || this.inRecords || this.inShop)) {
            const back = this.inSettings ? this.settingsBack() : this.inRecords ? RECORDS_BACK_RECT
                : this.editing ? EDIT_BACK_RECT : SHOP_BACK_RECT;
            const button = this.editing && this.inShop ? this.kit.done : this.kit.menu;
            button.update(dts, this.hover(back), this.pressed === 'back' ? this.pressProgress : 0);
        } else if (!this.start) {
            // -- кнопка реклами темніша, коли зараз не спрацює: ліміт вичерпано або ролик ще не завантажився
            this.kit.ad.off = freeAds === 0 || !this.ads.ready();
            for (const [name, sprite] of Object.entries(this.menuSprites)) {
                sprite.update(dts, this.hover(this.menuButtons[name]), name === this.pressed ? this.pressProgress : 0);
            }
        } else if (this.over) {
            this.kit.menu.update(dts, this.hover(MENU_BTN_RECT), this.pressed === 'menu' ? this.pressProgress : 0);
        }
    }

    // -- малювання; Canvas: (0, 0) -- лівий верхній кут ігрового поля, видно від -ox до viewW - ox по x
    // -- і від -oy до viewH - oy по y
    render(c) {
        const kit = this.kit;
        if (!this.start && (this.inSettings || this.inRecords || this.inShop)) {
            this.scenery.drawBack(c);
            this.scenery.drawGround(c);
            let button = kit.menu, back;
            if (this.inSettings) {
                back = this.settingsBack();
                this.drawSettings(c);
            } else if (this.inRecords) {
                back = RECORDS_BACK_RECT;
                this.drawRecords(c);
            } else if (this.editing) {
                back = EDIT_BACK_RECT;
                button = kit.done;     // -- з редактора -- назад у магазин
                this.drawEditor(c);
            } else {
                back = SHOP_BACK_RECT;
                this.drawShop(c);
                this.drawMenuCounters(c);    // -- баланс монет видно в магазині
            }
            button.draw(c, this.tTotal, back.x, back.y);
        } else if (!this.start) {
            this.scenery.drawBack(c);
            this.scenery.drawGround(c);
            kit.title.draw(c, this.tTotal);
            for (const sprite of Object.values(this.menuSprites)) {
                if (sprite !== kit.settings && sprite !== kit.ad) {
                    sprite.draw(c, this.tTotal);
                }
            }
            // -- шестерня -- у правому верхньому куті екрана, разом зі своїм хітбоксом settingsBtn
            kit.settings.draw(c, this.tTotal, kit.settings.x + this.hudRight, kit.settings.y + this.hudTop);
            this.drawMenuCounters(c);
            this.drawAd(c);
        } else {
            this.scenery.drawBack(c);
            for (const pipe of this.pipes) {
                kit.pipe.draw(c, Math.trunc(pipe.x), PIPE_WIDTH, pipe.y, pipe.gap, this.floorY, -this.oy);
            }
            this.drawCoins(c);
            this.drawPowerups(c);
            this.scenery.drawGround(c);
            this.drawSlowTint(c);

            this.trailPoints(this.trailPts);
            kit.trail.draw(c, this.pts, this.tTotal);
            this.drawBird(c, BIRD_START_X, this.birdY, this.birdV);
            // -- HUD -- біля верхнього краю екрана: рахунок по центру, монетки і бонуси зліва, рівень справа
            c.save();
            c.translate(0, this.hudTop);
            this.drawText(c, String(this.score), WIDTH / 2, 50);
            c.translate(this.hudLeft, 0);
            this.drawCounter(c, kit.coinIcon, String(this.runCoins), 14, 30);
            this.drawPowerupHud(c);
            c.translate(this.hudRight - this.hudLeft, 0);
            this.drawLevelHud(c);
            c.restore();
            if (!this.over) {
                this.drawLevelBanner(c);
            }
            if (this.over) {
                // -- напис, панель і кнопка виїжджають зверху (ease-out)
                const k = Math.min(1, this.overTime / GAME_OVER_ANIM);
                const slide = Math.trunc(-40 * (1 - k) ** 3);
                Gfx.blitCenter(c, kit.text('game_over'), WIDTH / 2, GAME_OVER_Y + slide);
                this.drawResult(c, slide);
                kit.menu.draw(c, this.tTotal, MENU_BTN_RECT.x, MENU_BTN_RECT.y + slide);
            } else if (this.paused) {
                this.drawPause(c);
            }
        }
        if (this.fading) {
            Gfx.fill(c, 0, -this.ox, -this.oy, this.viewW, this.viewH, this.fade);
        }
    }

    /** пауза: екран темнішає, посередині -- кнопка «грати» (тап будь-де продовжує), під нею MENU */
    drawPause(c) {
        Gfx.fill(c, 0, -this.ox, -this.oy, this.viewW, this.viewH, 110);
        this.drawPanel(c, PAUSE_PLAY);
        const cx = PAUSE_PLAY.centerX() + 4, cy = PAUSE_PLAY.centerY() - 4;
        Gfx.polygon(c, COLOR_OUTLINE, cx - 26, cy - 32, cx + 32, cy, cx - 26, cy + 32);
        Gfx.polygon(c, COLOR_ARROW, cx - 18, cy - 20, cx + 19, cy, cx - 18, cy + 20);
        this.kit.menu.draw(c, this.tTotal, PAUSE_MENU_RECT.x, PAUSE_MENU_RECT.y);
    }
}
