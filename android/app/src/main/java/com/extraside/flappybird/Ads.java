package com.extraside.flappybird;

/**
 * Реклама за винагороду: гра питає, чи ролик уже завантажений, і просить його показати.
 * Справжня реклама -- AdMob (Google), у тестах -- підробка. Усе викликається з UI-потоку (як і вся гра).
 */
interface Ads {
    /** ролик завантажений -- можна показувати */
    boolean ready();

    /** завантажити наступний ролик, якщо його ще нема (гра викликає це кожен кадр у меню -- зайве відкидається) */
    void load();

    /** показати ролик; reward -- гравець додивився до кінця (лише тоді даємо монети) */
    void show(Runnable reward);

    /** чи потрібна в налаштуваннях кнопка «конфіденційність» (згода на рекламу: у ЄС/Великій Британії) */
    boolean privacyRequired();

    /** форма Google, де гравець міняє згоду на рекламу */
    void showPrivacy();

    /** реклами нема зовсім (поки гру не підключили до AdMob) */
    Ads NONE = new Ads() {
        public boolean ready() {
            return false;
        }

        public void load() {
        }

        public void show(Runnable reward) {
        }

        public boolean privacyRequired() {
            return false;
        }

        public void showPrivacy() {
        }
    };
}
