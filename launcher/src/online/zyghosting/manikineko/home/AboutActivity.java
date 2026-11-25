package online.zyghosting.manikineko.home;

import android.app.Activity;
import android.os.Build;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.io.BufferedReader;
import java.io.FileReader;

/**
 * "Apie" screen: the same facts the system About-phone page shows, but owned by us.
 *
 * The stock Settings.apk cannot be re-signed (shared uid android.uid.system plus 40 signature
 * permissions), so its maintainer/sweetheart/organisation rows stay as the original ROM author
 * left them. This screen is the place where the device actually reports Manikineko Phone.
 */
public class AboutActivity extends Activity {

    private LinearLayout rows;
    private LayoutInflater inflater;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_about);

        rows = (LinearLayout) findViewById(R.id.rows);
        inflater = LayoutInflater.from(this);

        addRow(getString(R.string.info_version), prop("ro.cm.version", getString(R.string.info_unknown)));
        addRow(getString(R.string.info_build), prop("ro.build.display.id", getString(R.string.info_unknown)));
        addRow(getString(R.string.info_android), Build.VERSION.RELEASE + " (API " + Build.VERSION.SDK_INT + ")");
        addRow(getString(R.string.info_device), Build.MODEL + " / " + Build.DEVICE);
        addRow(getString(R.string.info_kernel), kernelVersion());
        addRow(getString(R.string.info_build_date), prop("ro.build.date", getString(R.string.info_unknown)));
        addRow(getString(R.string.info_patch), prop("ro.build.version.security_patch", getString(R.string.info_unknown)));
        addRow(getString(R.string.info_baseband), baseband());
        addRow(getString(R.string.info_maintainer), getString(R.string.info_maintainer_value));
        addRow(getString(R.string.info_org), getString(R.string.info_org_value));
        addRow(getString(R.string.info_selinux), selinux());
    }

    private void addRow(String label, String value) {
        View row = inflater.inflate(R.layout.item_info, rows, false);
        ((TextView) row.findViewById(R.id.info_label)).setText(label);
        ((TextView) row.findViewById(R.id.info_value)).setText(value);
        rows.addView(row);
    }

    /** uname -r plus the build stamp, i.e. what "Kernel version" shows in Settings. */
    private String kernelVersion() {
        String release = prop("ro.kernel.version", null);
        if (release == null) {
            release = System.getProperty("os.version");
        }
        String stamp = "";
        BufferedReader r = null;
        try {
            r = new BufferedReader(new FileReader("/proc/version"));
            String line = r.readLine();
            if (line != null) {
                int i = line.indexOf(" version ");
                if (i >= 0) {
                    stamp = line.substring(i + 9).trim();
                }
            }
        } catch (Exception ignored) {
            // /proc/version is always readable, but never let About crash over it.
        } finally {
            if (r != null) {
                try {
                    r.close();
                } catch (Exception ignored) {
                }
            }
        }
        if (release == null || release.isEmpty()) {
            return stamp.isEmpty() ? getString(R.string.info_unknown) : stamp;
        }
        return stamp.isEmpty() ? release : release + "\n" + stamp;
    }

    private String baseband() {
        String v = prop("gsm.version.baseband", null);
        return v == null || v.isEmpty() ? getString(R.string.info_unknown) : v;
    }

    private String selinux() {
        String v = prop("ro.boot.selinux", null);
        if (v == null || v.isEmpty()) {
            v = prop("ro.build.selinux", null);
        }
        return "1".equals(v) ? "Enforcing" : (v == null ? getString(R.string.info_unknown) : v);
    }

    /**
     * android.os.SystemProperties is hidden but present in the boot classpath on this ROM;
     * reflection keeps the app compiling against the public SDK only.
     */
    private static String prop(String key, String def) {
        try {
            Class<?> c = Class.forName("android.os.SystemProperties");
            Object v = c.getMethod("get", String.class, String.class).invoke(null, key, def);
            return v == null ? def : (String) v;
        } catch (Exception ignored) {
            return def;
        }
    }

    @Override
    public void onBackPressed() {
        finish();
    }
}
