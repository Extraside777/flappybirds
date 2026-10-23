package com.extraside.flappybird;

import android.content.res.AssetFileDescriptor;
import android.content.res.AssetManager;
import android.media.AudioAttributes;
import android.media.MediaPlayer;
import android.media.SoundPool;

import java.util.HashMap;
import java.util.Map;

/** музика і звуки -- як src/audio.py */
final class Audio {
    private Audio() {
    }

    /**
     * Фонова музика з плавним переходом між треками:
     * старий трек тихо згасає -> вмикаємо новий (з початку) і він плавно наростає.
     */
    static final class Music {
        static final float FADE = 0.5f;      // -- сек, за скільки згасає/наростає трек

        private final HashMap<String, MediaPlayer> players = new HashMap<>();
        private final HashMap<String, Float> levels = new HashMap<>();   // -- повзунки 0..1
        private final float maxVolume;       // -- гучність при повзунку на 100%
        private String current;
        private String wanted;
        private float fade = 0f;             // -- 0 = тиша, 1 = повна гучність
        private boolean paused;

        Music(AssetManager am, Map<String, String> tracks, float maxVolume) {
            this.maxVolume = maxVolume;
            for (Map.Entry<String, String> e : tracks.entrySet()) {
                levels.put(e.getKey(), 0.5f);
                try (AssetFileDescriptor fd = am.openFd(e.getValue())) {
                    MediaPlayer mp = new MediaPlayer();
                    mp.setAudioAttributes(new AudioAttributes.Builder()
                            .setUsage(AudioAttributes.USAGE_GAME)
                            .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC).build());
                    mp.setDataSource(fd.getFileDescriptor(), fd.getStartOffset(), fd.getLength());
                    mp.setLooping(true);
                    mp.prepare();
                    players.put(e.getKey(), mp);
                } catch (Exception ignored) {
                    // -- нема файлу або плеєр не відкрився -- граємо без цього треку
                }
            }
        }

        void setLevel(String name, float value) {
            levels.put(name, Math.max(0f, Math.min(1f, value)));
        }

        void play(String name) {
            wanted = name;
        }

        private float volume() {
            if (current == null) {
                return 0f;
            }
            Float lv = levels.get(current);
            return (float) Math.pow(lv == null ? 0f : lv, 1.5) * maxVolume * fade;
        }

        void update(float dt) {
            if (paused) {
                return;
            }
            float step = dt / FADE;
            if (wanted != null && !wanted.equals(current)) {
                fade -= step;
                if (fade <= 0 || current == null) {
                    fade = 0f;
                    MediaPlayer old = current == null ? null : players.get(current);
                    if (old != null && old.isPlaying()) {
                        old.pause();
                    }
                    current = wanted;
                    MediaPlayer mp = players.get(current);
                    if (mp != null) {
                        mp.setVolume(0f, 0f);
                        mp.seekTo(0);
                        mp.start();
                    }
                }
            } else {
                fade = Math.min(1f, fade + step);
            }
            MediaPlayer mp = current == null ? null : players.get(current);
            if (mp != null) {
                float v = volume();
                mp.setVolume(v, v);
            }
        }

        /** застосунок згорнули -- музика замовкає, розгорнули -- грає далі */
        void pause() {
            paused = true;
            MediaPlayer mp = current == null ? null : players.get(current);
            if (mp != null && mp.isPlaying()) {
                mp.pause();
            }
        }

        void resume() {
            paused = false;
            MediaPlayer mp = current == null ? null : players.get(current);
            if (mp != null && !mp.isPlaying()) {
                mp.start();
            }
        }

        void release() {
            for (MediaPlayer mp : players.values()) {
                mp.release();
            }
            players.clear();
        }
    }

    /** короткі звуки (монетка і т.д.) з одним спільним повзунком гучності */
    static final class Sounds {
        private final SoundPool pool;
        private final HashMap<String, Integer> ids = new HashMap<>();
        private final float maxVolume;
        private float level = 0.6f;

        Sounds(AssetManager am, Map<String, String> files, float maxVolume) {
            this.maxVolume = maxVolume;
            pool = new SoundPool.Builder().setMaxStreams(6).setAudioAttributes(new AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_GAME)
                    .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build()).build();
            for (Map.Entry<String, String> e : files.entrySet()) {
                try (AssetFileDescriptor fd = am.openFd(e.getValue())) {
                    ids.put(e.getKey(), pool.load(fd, 1));
                } catch (Exception ignored) {
                    // -- нема файлу -- просто мовчимо
                }
            }
        }

        void setLevel(float value) {
            level = Math.max(0f, Math.min(1f, value));
        }

        void play(String name) {
            Integer id = ids.get(name);
            if (id == null || level <= 0) {
                return;
            }
            float v = (float) Math.pow(level, 1.5) * maxVolume;
            pool.play(id, v, v, 1, 0, 1f);
        }

        void release() {
            pool.release();
        }
    }
}
