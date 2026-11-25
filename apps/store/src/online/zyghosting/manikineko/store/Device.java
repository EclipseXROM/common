package online.zyghosting.manikineko.store;

import android.app.ActivityManager;
import android.content.Context;
import android.os.Build;

import java.util.ArrayList;
import java.util.List;

/** What this phone can run. The Store shows only apps the catalog marks as compatible with it (the same catalog serves many devices). */
final class Device {

    private Device() { }

    /** Primary + secondary ABI, and the full SUPPORTED_ABIS list on API 21+ (read by reflection, the build targets API 19). */
    static List<String> abis() {
        List<String> out = new ArrayList<String>();
        try {
            String[] all = (String[]) Build.class.getField("SUPPORTED_ABIS").get(null);
            for (String a : all) out.add(a);
        } catch (Exception e) {
            if (Build.CPU_ABI != null) out.add(Build.CPU_ABI);
            if (Build.CPU_ABI2 != null && Build.CPU_ABI2.length() > 0) out.add(Build.CPU_ABI2);
        }
        return out;
    }

    static boolean supports(Context c, Catalog.App a) {
        if (a.minSdk > Build.VERSION.SDK_INT) return false;
        if (a.glEs > 0) {
            int have = ((ActivityManager) c.getSystemService(Context.ACTIVITY_SERVICE)).getDeviceConfigurationInfo().reqGlEsVersion;
            if (a.glEs > have) return false;
        }
        if (a.abis.length > 0) {                                  // an app with native code must ship at least one ABI this CPU runs
            boolean ok = false;
            List<String> mine = abis();
            for (String abi : a.abis) if (mine.contains(abi)) { ok = true; break; }
            if (!ok) return false;
        }
        if (a.devices.length > 0) {                               // optional per-device allow list (Build.DEVICE codenames)
            boolean ok = false;
            for (String d : a.devices) if (d.equalsIgnoreCase(Build.DEVICE)) { ok = true; break; }
            if (!ok) return false;
        }
        return true;
    }
}
