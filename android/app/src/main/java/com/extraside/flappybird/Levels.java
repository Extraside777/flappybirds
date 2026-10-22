package com.extraside.flappybird;

/**
 * Рівні складності: що більший рахунок, то швидше летять труби, вужчий прохід між верхньою і нижньою
 * трубою і ближче труби одна до одної (на екрані їх більше). Останній рівень триває до кінця гри.
 * Ті самі числа, що й у src/levels.py.
 */
final class Levels {
    private Levels() {
    }

    static final class Level {
        final int score;      // -- з якого рахунку починається рівень
        final float speed;    // -- px за кадр, з якою швидкістю їдуть труби (і весь світ)
        final int gap;        // -- висота проходу між верхньою і нижньою трубою
        final int spacing;    // -- відстань між трубами по горизонталі

        Level(int score, float speed, int gap, int spacing) {
            this.score = score;
            this.speed = speed;
            this.gap = gap;
            this.spacing = spacing;
        }
    }

    static final Level[] LEVELS = {
            new Level(0, 3.0f, 150, 250),
            new Level(10, 3.3f, 144, 240),
            new Level(20, 3.6f, 138, 230),
            new Level(30, 3.9f, 132, 220),
            new Level(45, 4.2f, 126, 210),
            new Level(60, 4.5f, 120, 200),
    };

    /** номер рівня (0 -- перший) для рахунку */
    static int levelFor(int score) {
        int lv = 0;
        for (int i = 0; i < LEVELS.length; i++) {
            if (score >= LEVELS[i].score) {
                lv = i;
            }
        }
        return lv;
    }
}
