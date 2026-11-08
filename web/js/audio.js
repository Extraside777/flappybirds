// -- музика і звуки -- як Audio.java / src/audio.py, на Web Audio.
// -- iPhone не дає грати звук, поки гравець не торкнувся екрана: unlock() викликається з першого дотику

export function audioContext() {
    const AC = window.AudioContext || window.webkitAudioContext;
    try {
        return AC ? new AC() : null;
    } catch (e) {
        return null;
    }
}

/**
 * Фонова музика з плавним переходом між треками: старий трек тихо згасає -> вмикаємо новий (з початку)
 * і він плавно наростає. Треки -- <audio> (не розпаковуються в пам'ять цілком), гучність -- через GainNode,
 * бо на iPhone audio.volume не працює
 */
export class Music {
    static FADE = 0.5;      // -- сек, за скільки згасає/наростає трек

    constructor(ctx, tracks, maxVolume) {
        this.ctx = ctx;
        this.maxVolume = maxVolume;
        this.players = {};
        this.levels = {};
        for (const [name, url] of Object.entries(tracks)) {
            const el = new Audio(url);
            el.loop = true;
            el.preload = 'auto';
            const p = { el, gain: null };
            if (ctx) {
                try {
                    p.gain = ctx.createGain();
                    p.gain.gain.value = 0;
                    ctx.createMediaElementSource(el).connect(p.gain).connect(ctx.destination);
                } catch (e) {
                    p.gain = null;
                }
            }
            this.players[name] = p;
            this.levels[name] = 0.5;
        }
        this.current = null;
        this.wanted = null;
        this.fade = 0;       // -- 0 = тиша, 1 = повна гучність
        this.paused = false;
    }

    /** перший дотик: «розблоковуємо» кожен трек (iPhone дозволяє play() лише з дотику, далі -- будь-коли) */
    unlock() {
        for (const [name, p] of Object.entries(this.players)) {
            const pr = p.el.play();
            if (pr) {
                pr.then(() => {
                    if (name !== this.current || this.paused) {
                        p.el.pause();
                    }
                }).catch(() => {
                });
            }
        }
    }

    setLevel(name, value) {
        this.levels[name] = Math.max(0, Math.min(1, value));
    }

    play(name) {
        this.wanted = name;
    }

    volume() {
        if (!this.current) {
            return 0;
        }
        return Math.pow(this.levels[this.current] ?? 0, 1.5) * this.maxVolume * this.fade;
    }

    setVolume(p, v) {
        if (p.gain) {
            p.gain.gain.value = v;
        } else {
            p.el.volume = Math.max(0, Math.min(1, v));
        }
    }

    update(dt) {
        if (this.paused) {
            return;
        }
        const step = dt / Music.FADE;
        if (this.wanted && this.wanted !== this.current) {
            this.fade -= step;
            if (this.fade <= 0 || !this.current) {
                this.fade = 0;
                const old = this.current && this.players[this.current];
                if (old) {
                    old.el.pause();
                }
                this.current = this.wanted;
                const p = this.players[this.current];
                if (p) {
                    this.setVolume(p, 0);
                    p.el.currentTime = 0;
                    p.el.play().catch(() => {
                    });
                }
            }
        } else {
            this.fade = Math.min(1, this.fade + step);
        }
        const p = this.current && this.players[this.current];
        if (p) {
            this.setVolume(p, this.volume());
        }
    }

    /** гру згорнули -- музика замовкає, розгорнули -- грає далі */
    pause() {
        this.paused = true;
        const p = this.current && this.players[this.current];
        if (p) {
            p.el.pause();
        }
    }

    resume() {
        this.paused = false;
        const p = this.current && this.players[this.current];
        if (p) {
            p.el.play().catch(() => {
            });
        }
    }
}

/** короткі звуки (монетка і т.д.) з одним спільним повзунком гучності */
export class Sounds {
    constructor(ctx, files, maxVolume) {
        this.ctx = ctx;
        this.maxVolume = maxVolume;
        this.level = 0.6;
        this.buffers = {};
        if (!ctx) {
            return;
        }
        for (const [name, url] of Object.entries(files)) {
            fetch(url).then((r) => r.arrayBuffer())
                .then((data) => new Promise((ok, fail) => ctx.decodeAudioData(data, ok, fail)))
                .then((buf) => {
                    this.buffers[name] = buf;
                })
                .catch(() => {
                });     // -- нема файлу -- просто мовчимо
        }
    }

    setLevel(value) {
        this.level = Math.max(0, Math.min(1, value));
    }

    play(name) {
        const buf = this.buffers[name];
        if (!buf || this.level <= 0 || this.ctx.state !== 'running') {
            return;
        }
        const src = this.ctx.createBufferSource();
        const gain = this.ctx.createGain();
        gain.gain.value = Math.pow(this.level, 1.5) * this.maxVolume;
        src.buffer = buf;
        src.connect(gain).connect(this.ctx.destination);
        src.start();
    }
}
