// -- запуск гри в браузері / на iPhone (як GameView.java + MainActivity.java): полотно на весь екран,
// -- ширина ігрового поля 400 тягнеться на всю ширину, зайва висота йде на небо (земля завжди внизу).
// -- Цикл: кожен кадр екрана -- скільки треба кроків гри по 1/60 сек, потім малювання
import { Assets, SpriteKit } from './kit.js';
import { Game, WIDTH, HEIGHT, FPS, MUSIC_MAX_VOLUME, SFX_MAX_VOLUME, PRESS_DARK } from './game.js';
import { Music, Sounds, audioContext } from './audio.js';
import * as Store from './store.js';
import { createAds } from './ads.js';

const STEP = 1 / FPS;
const MAX_VIEW_W = 2400;      // -- ширше за це сцену не розтягуємо
const WHEEL_STEP = 40;        // -- px, на скільки гортає магазин один «клік» коліщатка

const cv = document.getElementById('game');
const ctx = cv.getContext('2d');
const safe = document.getElementById('safe');

async function boot() {
    const assets = new Assets('assets/sprites');
    const [manifest, extra] = await Promise.all([assets.json('manifest.json'), assets.json('extra.json')]);
    const font = new FontFace('OutlineStyle', 'url(assets/fonts/OutlineStyleRegular.ttf)');
    await Promise.all([assets.preload(manifest, extra), font.load().then((f) => document.fonts.add(f), () => {
    })]);
    const kit = new SpriteKit(assets, manifest, extra, PRESS_DARK);

    const actx = audioContext();
    const music = new Music(actx, { menu: 'assets/music/menu.mp3', game: 'assets/music/game.mp3' }, MUSIC_MAX_VOLUME);
    const sounds = {};
    for (const name of ['coin', 'powerup', 'shield_break', 'level_up']) {
        sounds[name] = `assets/sounds/${name}.wav`;
    }
    const sfx = new Sounds(actx, sounds, SFX_MAX_VOLUME);
    const game = new Game(kit, music, sfx, Store.loadConfig(), Store.loadProgress(), Store, createAds());
    window.game = game;       // -- для перевірки з консолі браузера
    document.getElementById('loading').remove();

    // -- розмір: k -- скільки px екрана на px гри, dest -- де на екрані ліва верхня точка полотна
    let k = 1, destX = 0, destY = 0, dpr = 1;
    const layout = () => {
        const w = window.innerWidth, h = window.innerHeight;
        dpr = window.devicePixelRatio || 1;
        cv.width = Math.round(w * dpr);
        cv.height = Math.round(h * dpr);
        let viewW, viewH;
        if (w * HEIGHT >= h * WIDTH) {       // -- екран ширший за поле: розтягуємо вшир
            k = h / HEIGHT;
            viewH = HEIGHT;
            viewW = Math.min(Math.round(w / k), MAX_VIEW_W);
        } else {                             // -- вищий: небо довше
            k = w / WIDTH;
            viewW = WIDTH;
            viewH = Math.round(h / k);
        }
        destX = (w - viewW * k) / 2;
        destY = (h - viewH * k) / 2;
        // -- виріз камери / «острівець» iPhone: HUD опускається нижче нього
        const cutout = parseFloat(getComputedStyle(safe).paddingTop) || 0;
        const safeTop = Math.max(0, Math.ceil((cutout - destY) / k));
        game.setView(viewW, viewH, Math.trunc((viewW - WIDTH) / 2), Math.trunc((viewH - HEIGHT) / 2), safeTop);
    };
    layout();
    window.addEventListener('resize', layout);

    const gx = (x) => Math.trunc((x - destX) / k - game.ox);
    const gy = (y) => Math.trunc((y - destY) / k - game.oy);

    // -- дотики і мишка: перший палець керує, другий під час гри -- теж стрибок
    let pointer = null, unlocked = false;
    cv.addEventListener('pointerdown', (e) => {
        e.preventDefault();
        if (!unlocked && actx) {       // -- iPhone дає грати звук лише після першого дотику
            unlocked = true;
            actx.resume().catch(() => {
            });
            music.unlock();
        }
        if (pointer === null) {
            pointer = e.pointerId;
            cv.setPointerCapture(e.pointerId);
            game.touchDown(gx(e.clientX), gy(e.clientY));
        } else {
            game.extraTouch();
        }
    });
    cv.addEventListener('pointermove', (e) => {
        if (e.pointerId === pointer) {
            game.touchMove(gx(e.clientX), gy(e.clientY));
        }
    });
    const up = (e) => {
        if (e.pointerId === pointer) {
            game.touchUp(gx(e.clientX), gy(e.clientY));
            pointer = null;
        }
    };
    cv.addEventListener('pointerup', up);
    cv.addEventListener('pointercancel', up);
    // -- без цього iPhone на подвійний тап збільшує сторінку, а на довгий -- показує лупу
    for (const type of ['touchstart', 'touchmove', 'touchend']) {
        cv.addEventListener(type, (e) => e.preventDefault(), { passive: false });
    }
    cv.addEventListener('wheel', (e) => {
        e.preventDefault();
        game.wheel(Math.sign(e.deltaY) * WHEEL_STEP);
    }, { passive: false });
    window.addEventListener('keydown', (e) => {
        if (e.code === 'Space') {
            e.preventDefault();
            game.jumpKey();
        } else if (e.code === 'Escape') {
            game.back();
        }
    });

    // -- гру згорнули / перемкнулись на іншу вкладку -- пауза і збереження; повернулись -- музика грає далі
    let running = true;
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            running = false;
            game.onPause();
        } else {
            running = true;
            last = 0;
            game.onResume();
            requestAnimationFrame(frame);
        }
    });
    window.addEventListener('pagehide', () => game.save());

    let last = 0, acc = 0;
    const frame = (time) => {
        if (!running) {
            return;
        }
        const dt = last ? (time - last) / 1000 : 0;
        last = time;
        acc += Math.min(dt, 0.25);
        // -- +0.25 кроку: щоб тремтіння vsync не давало кадрів з 0 і 2 кроками
        let n = Math.floor(acc / STEP + 0.25);
        if (n > 5) {
            n = 5;
            acc = 0;
        } else {
            acc -= n * STEP;
        }
        for (let i = 0; i < n; i++) {
            game.step();
        }
        ctx.setTransform(1, 0, 0, 1, 0, 0);
        ctx.fillStyle = '#000';
        ctx.fillRect(0, 0, cv.width, cv.height);
        ctx.setTransform(k * dpr, 0, 0, k * dpr, destX * dpr, destY * dpr);
        ctx.save();
        ctx.beginPath();
        ctx.rect(0, 0, game.viewW, game.viewH);
        ctx.clip();
        ctx.translate(game.ox, game.oy);
        game.render(ctx);
        ctx.restore();
        requestAnimationFrame(frame);
    };
    requestAnimationFrame(frame);
}

boot().catch((e) => {
    document.getElementById('loading').textContent = 'Помилка: ' + e.message;
    throw e;
});
