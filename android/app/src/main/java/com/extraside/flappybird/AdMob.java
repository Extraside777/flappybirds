package com.extraside.flappybird;

import android.app.Activity;
import android.os.SystemClock;

import com.google.android.gms.ads.AdError;
import com.google.android.gms.ads.AdRequest;
import com.google.android.gms.ads.FullScreenContentCallback;
import com.google.android.gms.ads.LoadAdError;
import com.google.android.gms.ads.MobileAds;
import com.google.android.gms.ads.rewarded.RewardedAd;
import com.google.android.gms.ads.rewarded.RewardedAdLoadCallback;
import com.google.android.ump.ConsentInformation;
import com.google.android.ump.ConsentRequestParameters;
import com.google.android.ump.UserMessagingPlatform;

/**
 * Реклама за винагороду від Google (AdMob). ID рекламного блоку -- BuildConfig.REWARDED_ID: з android/admob.properties,
 * а в debug-збірці -- завжди тестовий (свою рекламу клацати не можна -- AdMob за це блокує акаунт).
 * Спершу -- згода на рекламу (UMP): у ЄС/Великій Британії Google вимагає спитати гравця, деінде форми нема.
 * Ролик вантажиться заздалегідь (поки гравець у меню), тож після натискання кнопки показується одразу.
 */
final class AdMob implements Ads {
    private static final long AD_LIFE = 55 * 60 * 1000L;      // -- мс: завантажений ролик дійсний годину, беремо з запасом
    private static final long RETRY_MIN = 5_000, RETRY_MAX = 5 * 60_000;   // -- мс: після невдачі -- пауза, далі вдвічі довша

    private final Activity activity;
    private final ConsentInformation consent;
    private boolean asking, started, loading, privacy;
    private RewardedAd ad;
    private long loadedAt, retryAt;
    private int fails;

    AdMob(Activity activity) {
        this.activity = activity;
        consent = UserMessagingPlatform.getConsentInformation(activity);
        askConsent();
        if (consent.canRequestAds()) {
            start();    // -- згода є з минулого запуску -- рекламу вантажимо, не чекаючи відповіді Google
        }
    }

    /** згода на рекламу: Google вимагає оновлювати її на кожному запуску, а форму показує сам, коли треба */
    private void askConsent() {
        asking = true;
        consent.requestConsentInfoUpdate(activity, new ConsentRequestParameters.Builder().build(),
                () -> UserMessagingPlatform.loadAndShowConsentFormIfRequired(activity, error -> consentDone()),
                error -> consentDone());
    }

    private void consentDone() {
        asking = false;
        privacy = consent.getPrivacyOptionsRequirementStatus()
                == ConsentInformation.PrivacyOptionsRequirementStatus.REQUIRED;
        if (consent.canRequestAds()) {
            start();
        } else {
            failed();
        }
    }

    private void start() {
        if (started) {
            return;
        }
        started = true;
        // -- SDK ініціалізується у фоновому потоці (так радить Google) -- гра на старті не підвисає
        new Thread(() -> MobileAds.initialize(activity, status -> {
        })).start();
    }

    /** нема інтернету або реклами: наступна спроба -- через 5 сек, потім 10, 20... (не частіше, ніж раз на 5 хв) */
    private void failed() {
        retryAt = SystemClock.uptimeMillis() + Math.min(RETRY_MAX, RETRY_MIN << Math.min(fails, 6));
        fails++;
    }

    @Override
    public void load() {
        if (asking || loading || ad != null || SystemClock.uptimeMillis() < retryAt) {
            return;
        }
        if (!started) {
            askConsent();    // -- на старті згоду спитати не вдалося (нема інтернету) -- ще раз
            return;
        }
        loading = true;
        RewardedAd.load(activity, BuildConfig.REWARDED_ID, new AdRequest.Builder().build(),
                new RewardedAdLoadCallback() {
                    @Override
                    public void onAdLoaded(RewardedAd loaded) {
                        loading = false;
                        fails = 0;
                        ad = loaded;
                        loadedAt = SystemClock.uptimeMillis();
                    }

                    @Override
                    public void onAdFailedToLoad(LoadAdError error) {
                        loading = false;
                        failed();
                    }
                });
    }

    @Override
    public boolean ready() {
        if (ad != null && SystemClock.uptimeMillis() - loadedAt > AD_LIFE) {
            ad = null;    // -- застарів -- load() завантажить новий
        }
        return ad != null;
    }

    @Override
    public void show(Runnable reward) {
        if (!ready()) {
            return;
        }
        RewardedAd shown = ad;
        ad = null;       // -- ролик показується один раз; наступний load() вантажить новий
        shown.setFullScreenContentCallback(new FullScreenContentCallback() {
            @Override
            public void onAdFailedToShowFullScreenContent(AdError error) {
                failed();
            }
        });
        shown.show(activity, item -> reward.run());
    }

    @Override
    public boolean privacyRequired() {
        return privacy;
    }

    @Override
    public void showPrivacy() {
        UserMessagingPlatform.showPrivacyOptionsForm(activity, error -> consentDone());
    }
}
