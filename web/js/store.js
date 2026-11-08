// -- налаштування і прогрес у пам'яті браузера (localStorage) -- той самий формат, що settings.json / save.json
// -- (src/settings.py, Store.java): відомі ключі потрібного типу беруться зі збереження, решта -- стандартні

const KEY_SETTINGS = 'flappybird.settings';
const KEY_SAVE = 'flappybird.save';

function read(key) {
    try {
        const v = JSON.parse(localStorage.getItem(key));
        return v && typeof v === 'object' ? v : {};
    } catch (e) {
        return {};     // -- нема або битий -- беремо стандартні
    }
}

const unit = (o, k, d) => (typeof o[k] === 'number' ? Math.max(0, Math.min(1, o[k])) : d);
const count = (o, k, d) => (Number.isInteger(o[k]) ? Math.max(0, o[k]) : d);
const str = (o, k, d) => (typeof o[k] === 'string' ? o[k] : d);
const strings = (o, k, d) => (Array.isArray(o[k]) ? o[k].filter((v) => typeof v === 'string') : d);
const numbers = (o, k) => (Array.isArray(o[k]) ? o[k].filter((v) => Number.isInteger(v)) : []);

/** налаштування гравця; мова за замовчуванням -- як на телефоні (українська або англійська) */
export function loadConfig() {
    const o = read(KEY_SETTINGS);
    const lang = (navigator.language || '').toLowerCase().startsWith('uk') ? 'uk' : 'en';
    return {
        lang: str(o, 'lang', lang),
        menu_music: unit(o, 'menu_music', 0.5),     // -- повзунки 0..1
        game_music: unit(o, 'game_music', 0.5),
        sfx: unit(o, 'sfx', 0.6),
    };
}

/** прогрес: рекорд, монетки, куплене і обране в магазині, свій шлейф, перегляди реклами */
export function loadProgress() {
    const o = read(KEY_SAVE);
    const ct = o.custom_trail && typeof o.custom_trail === 'object' ? o.custom_trail : {};
    return {
        best: count(o, 'best', 0),
        coins: count(o, 'coins', 0),
        games: count(o, 'games', 0),
        skin: str(o, 'skin', 'classic'),                    // -- якою пташкою граємо
        owned: strings(o, 'owned', ['classic']),            // -- куплені пташки
        trail: str(o, 'trail', 'none'),
        owned_trails: strings(o, 'owned_trails', ['none']),
        background: str(o, 'background', 'day'),
        owned_backgrounds: strings(o, 'owned_backgrounds', ['day']),
        pipe: str(o, 'pipe', 'classic'),
        owned_pipes: strings(o, 'owned_pipes', ['classic']),
        // -- свій шлейф: кольори з палітри (номери), стиль, товщина 0..1
        custom_trail: {
            c1: count(ct, 'c1', 9), c2: count(ct, 'c2', 6), style: str(ct, 'style', 'glow'), width: unit(ct, 'width', 0.5),
        },
        ad_views: numbers(o, 'ad_views'),      // -- коли дивились рекламу за монети (сек від 1970), лише за добу
    };
}

function write(key, obj) {
    try {
        localStorage.setItem(key, JSON.stringify(obj));
    } catch (e) {
        // -- пам'ять браузера заборонена (приватний режим) -- граємо без збереження
    }
}

const r2 = (v) => Math.round(v * 100) / 100;    // -- 0.15 замість 0.15000000596

export function saveConfig(c) {
    write(KEY_SETTINGS, { lang: c.lang, menu_music: r2(c.menu_music), game_music: r2(c.game_music), sfx: r2(c.sfx) });
}

export function saveProgress(p) {
    write(KEY_SAVE, { ...p, custom_trail: { ...p.custom_trail, width: r2(p.custom_trail.width) } });
}
