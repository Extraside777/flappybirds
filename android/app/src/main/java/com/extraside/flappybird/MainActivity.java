package com.extraside.flappybird;

import android.app.Activity;
import android.os.Build;
import android.os.Bundle;
import android.view.Display;
import android.view.KeyEvent;
import android.view.View;
import android.view.Window;
import android.view.WindowInsets;
import android.view.WindowInsetsController;
import android.view.WindowManager;

/** весь екран під гру: без статус-бару і кнопок навігації (з'являються свайпом від краю) */
public final class MainActivity extends Activity {
    private GameView view;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        prefer60Hz();
        view = new GameView(this);
        setContentView(view);
        hideSystemUi();
    }

    /**
     * гра рахує кадри по 1/60 сек (як у пайтоні), тому на екранах 90/120 Гц просимо 60 Гц --
     * рух рівніший і батарея живе довше
     */
    @SuppressWarnings("deprecation")
    private void prefer60Hz() {
        if (Build.VERSION.SDK_INT < 23) {
            return;
        }
        Display d = getWindowManager().getDefaultDisplay();
        Display.Mode cur = d.getMode();
        for (Display.Mode m : d.getSupportedModes()) {
            if (m.getPhysicalWidth() == cur.getPhysicalWidth() && m.getPhysicalHeight() == cur.getPhysicalHeight()
                    && Math.abs(m.getRefreshRate() - 60f) < 1f) {
                WindowManager.LayoutParams lp = getWindow().getAttributes();
                lp.preferredDisplayModeId = m.getModeId();
                getWindow().setAttributes(lp);
                return;
            }
        }
    }

    @SuppressWarnings("deprecation")
    private void hideSystemUi() {
        Window w = getWindow();
        if (Build.VERSION.SDK_INT >= 30) {
            w.setDecorFitsSystemWindows(false);
            WindowInsetsController c = w.getInsetsController();
            if (c != null) {
                c.hide(WindowInsets.Type.statusBars() | WindowInsets.Type.navigationBars());
                c.setSystemBarsBehavior(WindowInsetsController.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE);
            }
        } else {
            w.getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                    | View.SYSTEM_UI_FLAG_FULLSCREEN
                    | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                    | View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                    | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                    | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN);
        }
    }

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) {
            hideSystemUi();
        } else {
            view.focusLost();   // -- шторка сповіщень, дзвінок поверх гри -- ставимо на паузу
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        view.resume();
    }

    @Override
    protected void onPause() {
        view.pause();
        super.onPause();
    }

    @Override
    protected void onDestroy() {
        view.release();
        super.onDestroy();
    }

    @Override
    @SuppressWarnings("deprecation")
    public void onBackPressed() {
        if (!view.back()) {
            super.onBackPressed();
        }
    }

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_SPACE) {
            view.jumpKey();
            return true;
        }
        return super.onKeyDown(keyCode, event);
    }
}
