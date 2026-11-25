package online.zyghosting.manikineko.home;

import android.app.Activity;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.res.Configuration;
import android.os.Bundle;
import android.provider.Settings;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import java.util.Locale;

/**
 * First-run setup (OOBE): welcome, language, Wi-Fi, date/time, the Store, done. Launched by HomeActivity until it is finished once, then never
 * again (flag in SharedPreferences, so a data wipe brings it back). The step survives the activity restart a language change causes.
 * This app is platform-signed, so it may change the system locale directly (CHANGE_CONFIGURATION); the other steps hand over to Settings.
 */
public class OobeActivity extends Activity {

    static final String PREFS = "oobe";
    static final String KEY_DONE = "done", KEY_STEP = "step";
    private static final int STEPS = 6;

    private SharedPreferences prefs;
    private int step;
    private TextView title, body, stepText;
    private LinearLayout actions;
    private Button next, back;

    static boolean isDone(android.content.Context c) {
        return c.getSharedPreferences(PREFS, MODE_PRIVATE).getBoolean(KEY_DONE, false);
    }

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        setContentView(R.layout.activity_oobe);
        prefs = getSharedPreferences(PREFS, MODE_PRIVATE);
        step = prefs.getInt(KEY_STEP, 0);
        title = (TextView) findViewById(R.id.oobe_title);
        body = (TextView) findViewById(R.id.oobe_body);
        stepText = (TextView) findViewById(R.id.oobe_step);
        actions = (LinearLayout) findViewById(R.id.oobe_actions);
        next = (Button) findViewById(R.id.oobe_next);
        back = (Button) findViewById(R.id.oobe_back);
        next.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) { go(step + 1); }
        });
        back.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) { go(step - 1); }
        });
        show();
    }

    private void go(int s) {
        if (s >= STEPS) {                                      // finished
            prefs.edit().putBoolean(KEY_DONE, true).remove(KEY_STEP).commit();
            finish();
            return;
        }
        step = Math.max(0, s);
        prefs.edit().putInt(KEY_STEP, step).commit();
        show();
    }

    private Button action(int textRes, View.OnClickListener l) {
        Button x = new Button(this);
        x.setText(textRes);
        x.setTextColor(getResources().getColor(R.color.mk_text));
        x.setBackgroundColor(getResources().getColor(R.color.mk_surface_hi));
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, (int) (56 * getResources().getDisplayMetrics().density));
        lp.bottomMargin = (int) (10 * getResources().getDisplayMetrics().density);
        x.setLayoutParams(lp);
        x.setOnClickListener(l);
        actions.addView(x);
        return x;
    }

    private void open(String settingsAction) {
        try {
            startActivity(new Intent(settingsAction));
        } catch (RuntimeException e) {
            Toast.makeText(this, R.string.info_unknown, Toast.LENGTH_SHORT).show();
        }
    }

    private void show() {
        actions.removeAllViews();
        back.setVisibility(step == 0 ? View.INVISIBLE : View.VISIBLE);
        stepText.setText(getString(R.string.oobe_step, step + 1, STEPS));
        next.setText(step == STEPS - 1 ? R.string.oobe_finish : step == 0 ? R.string.oobe_welcome_start : R.string.oobe_next);
        switch (step) {
            case 0:
                title.setText(R.string.oobe_welcome_title);
                body.setText(R.string.oobe_welcome_body);
                break;
            case 1:
                title.setText(R.string.oobe_lang_title);
                body.setText(R.string.oobe_lang_body);
                action(R.string.lang_english, new View.OnClickListener() {
                    @Override public void onClick(View v) { setLocale("en"); }
                });
                action(R.string.lang_lithuanian, new View.OnClickListener() {
                    @Override public void onClick(View v) { setLocale("lt"); }
                });
                break;
            case 2:
                title.setText(R.string.oobe_wifi_title);
                body.setText(R.string.oobe_wifi_body);
                action(R.string.oobe_wifi_open, new View.OnClickListener() {
                    @Override public void onClick(View v) { open(Settings.ACTION_WIFI_SETTINGS); }
                });
                break;
            case 3:
                title.setText(R.string.oobe_time_title);
                body.setText(R.string.oobe_time_body);
                action(R.string.oobe_time_open, new View.OnClickListener() {
                    @Override public void onClick(View v) { open(Settings.ACTION_DATE_SETTINGS); }
                });
                break;
            case 4:
                title.setText(R.string.oobe_store_title);
                body.setText(R.string.oobe_store_body);
                action(R.string.oobe_store_open, new View.OnClickListener() {
                    @Override public void onClick(View v) {
                        Intent i = getPackageManager().getLaunchIntentForPackage("online.zyghosting.manikineko.store");
                        if (i != null) startActivity(i);
                    }
                });
                break;
            default:
                title.setText(R.string.oobe_done_title);
                body.setText(R.string.oobe_done_body);
        }
    }

    /** Change the system language (persisted by the activity manager) through the hidden ActivityManagerNative API; the activity restarts itself. */
    private void setLocale(String lang) {
        try {
            Class<?> amn = Class.forName("android.app.ActivityManagerNative");
            Object am = amn.getMethod("getDefault").invoke(null);
            Configuration cfg = (Configuration) am.getClass().getMethod("getConfiguration").invoke(am);
            cfg.locale = new Locale(lang);
            cfg.getClass().getField("userSetLocale").setBoolean(cfg, true);
            am.getClass().getMethod("updateConfiguration", Configuration.class).invoke(am, cfg);
        } catch (Exception e) {
            open(Settings.ACTION_LOCALE_SETTINGS);             // not platform-signed (stock ROM): let the user pick the language in Settings
        }
    }

    @Override
    public void onBackPressed() {
        if (step > 0) go(step - 1);                            // the setup can only be left by finishing it
    }
}
