// -- реклама за винагороду: гра питає, чи ролик уже завантажений, і просить його показати (як Ads.java).
// -- На iPhone (застосунок на Capacitor) -- Google AdMob через плагін @capacitor-community/admob;
// -- у звичайному браузері реклами Google нема, тому кнопка дає монети одразу (як на ПК)
import { REWARDED_ID, TESTING } from './admob-ids.js';

/** браузер: ролика нема, монети -- одразу (той самий ліміт 5 разів за добу рахує гра) */
class WebAds {
    ready() {
        return true;
    }

    load() {
    }

    show(reward) {
        reward();
    }

    privacyRequired() {
        return false;
    }

    showPrivacy() {
    }
}

const AD_LIFE = 55 * 60 * 1000;          // -- мс: завантажений ролик дійсний годину, беремо з запасом
const RETRY_MIN = 5000, RETRY_MAX = 5 * 60000;   // -- мс: після невдачі -- пауза, далі вдвічі довша

/**
 * AdMob (як AdMob.java): спершу -- згода на рекламу (UMP: у ЄС/Великій Британії Google вимагає спитати
 * гравця, деінде форми нема), потім ролик вантажиться заздалегідь, поки гравець у меню
 */
class AdMobAds {
    constructor(plugin) {
        this.ad = plugin;
        this.asking = false;
        this.started = false;
        this.loading = false;
        this.loaded = false;
        this.privacy = false;
        this.loadedAt = 0;
        this.retryAt = 0;
        this.fails = 0;
        this.reward = null;
        plugin.addListener('onRewardedVideoAdReward', () => {
            const r = this.reward;
            this.reward = null;
            if (r) {
                r();
            }
        });
        plugin.addListener('onRewardedVideoAdFailedToShow', () => this.failed());
        this.askConsent();
    }

    /** згода на рекламу: Google вимагає оновлювати її на кожному запуску, форму показує сам, коли треба */
    async askConsent() {
        this.asking = true;
        try {
            let info = await this.ad.requestConsentInfo();
            if (info.status === 'REQUIRED' && info.isConsentFormAvailable) {
                info = await this.ad.showConsentForm();
            }
            this.consentDone(info);
        } catch (e) {
            this.consentDone(null);
        }
    }

    consentDone(info) {
        this.asking = false;
        if (info) {
            this.privacy = info.privacyOptionsRequirementStatus === 'REQUIRED';
        }
        if (info && info.canRequestAds) {
            this.start();
        } else {
            this.failed();
        }
    }

    start() {
        if (!this.started) {
            this.started = true;
            this.ad.initialize({ initializeForTesting: TESTING }).catch(() => {
            });
        }
    }

    /** нема інтернету або реклами: наступна спроба -- через 5 сек, потім 10, 20... (не частіше, ніж раз на 5 хв) */
    failed() {
        this.retryAt = Date.now() + Math.min(RETRY_MAX, RETRY_MIN * 2 ** Math.min(this.fails, 6));
        this.fails++;
    }

    load() {
        if (this.asking || this.loading || this.loaded || Date.now() < this.retryAt) {
            return;
        }
        if (!this.started) {
            this.askConsent();     // -- на старті згоду спитати не вдалося (нема інтернету) -- ще раз
            return;
        }
        this.loading = true;
        this.ad.prepareRewardVideoAd({ adId: REWARDED_ID, isTesting: TESTING }).then(() => {
            this.loading = false;
            this.loaded = true;
            this.fails = 0;
            this.loadedAt = Date.now();
        }, () => {
            this.loading = false;
            this.failed();
        });
    }

    ready() {
        if (this.loaded && Date.now() - this.loadedAt > AD_LIFE) {
            this.loaded = false;     // -- застарів -- load() завантажить новий
        }
        return this.loaded;
    }

    show(reward) {
        if (!this.ready()) {
            return;
        }
        this.loaded = false;       // -- ролик показується один раз; наступний load() вантажить новий
        this.reward = reward;
        this.ad.showRewardVideoAd().catch(() => {
            this.reward = null;
            this.failed();
        });
    }

    privacyRequired() {
        return this.privacy;
    }

    showPrivacy() {
        this.ad.showPrivacyOptionsForm().then(() => this.ad.requestConsentInfo()).then((info) => this.consentDone(info),
            () => {
            });
    }
}

export function createAds() {
    const cap = window.Capacitor;
    if (cap && cap.isNativePlatform && cap.isNativePlatform()) {
        const plugin = cap.registerPlugin ? cap.registerPlugin('AdMob') : cap.Plugins && cap.Plugins.AdMob;
        if (plugin) {
            return new AdMobAds(plugin);
        }
    }
    return new WebAds();
}
