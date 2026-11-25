package online.zyghosting.manikineko.home;

import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.graphics.drawable.Drawable;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.List;
import java.util.Set;

/**
 * Resolves what the launcher shows.
 *
 * 1. System apps: only the packages listed in R.array.allowed_packages, in that order, if they are
 *    installed and expose a MAIN/LAUNCHER activity. Missing packages are skipped silently.
 * 2. Store apps: every launchable app that is NOT a system app (installed from F-Droid / the
 *    Manikineko store / adb) is appended after the whitelist, sorted by label.
 */
final class AppEntry {

    /** package -> glyph name; the launcher draws its own Manikineko icon for these (drawable ic_app_<glyph>). */
    private static final Map<String, String> ICON_PACK = new HashMap<String, String>();
    static {
        String[][] m = {
            {"com.android.dialer", "phone"}, {"com.android.phone", "phone"}, {"com.android.contacts", "contacts"},
            {"com.android.messaging", "messages"}, {"com.android.mms", "messages"},
            {"com.android.deskclock", "clock"}, {"com.sec.android.app.clockpackage", "clock"},
            {"com.android.calculator2", "calculator"}, {"com.sec.android.app.popupcalculator", "calculator"},
            {"com.android.camera2", "camera"}, {"com.sec.android.app.camera", "camera"},
            {"com.android.gallery3d", "gallery"}, {"com.sec.android.gallery3d", "gallery"},
            {"com.android.settings", "settings"},
            {"com.sonyericsson.android.socialphonebook", "phone"}, {"com.sonyericsson.conversations", "messages"},
            {"com.google.android.deskclock", "clock"}, {"com.sonyericsson.android.camera", "camera"}, {"com.sonyericsson.album", "gallery"},
            {"online.zyghosting.manikineko.notes", "notes"}, {"online.zyghosting.manikineko.files", "files"}, {"online.zyghosting.manikineko.browser", "browser"}, {"online.zyghosting.manikineko.store", "store"},
        };
        for (String[] e : m) {
            ICON_PACK.put(e[0], e[1]);
        }
    }

    final String label;
    final Drawable icon;
    final Intent intent;

    private AppEntry(String label, Drawable icon, Intent intent) {
        this.label = label;
        this.icon = icon;
        this.intent = intent;
    }

    static List<AppEntry> load(Context ctx) {
        PackageManager pm = ctx.getPackageManager();
        String[] allowed = ctx.getResources().getStringArray(R.array.allowed_packages);

        List<AppEntry> out = new ArrayList<AppEntry>(allowed.length + 8);
        Set<String> seen = new HashSet<String>();
        seen.add(ctx.getPackageName());

        for (String pkg : allowed) {
            Intent launch = pm.getLaunchIntentForPackage(pkg);
            if (launch == null) {
                continue;
            }

            ResolveInfo ri = pm.resolveActivity(launch, 0);
            if (ri == null || ri.activityInfo == null) {
                continue;
            }

            out.add(build(ctx, pm, ri, pkg));
            seen.add(pkg);
        }

        // Store apps: launchable, not part of the system image.
        Intent main = new Intent(Intent.ACTION_MAIN);
        main.addCategory(Intent.CATEGORY_LAUNCHER);
        List<ResolveInfo> all = pm.queryIntentActivities(main, 0);
        List<AppEntry> extra = new ArrayList<AppEntry>();
        if (all != null) {
            for (ResolveInfo ri : all) {
                if (ri.activityInfo == null) {
                    continue;
                }
                String pkg = ri.activityInfo.packageName;
                ApplicationInfo ai = ri.activityInfo.applicationInfo;
                if (seen.contains(pkg) || ai == null || (ai.flags & ApplicationInfo.FLAG_SYSTEM) != 0) {
                    continue;
                }
                seen.add(pkg);
                extra.add(build(ctx, pm, ri, pkg));
            }
        }
        Collections.sort(extra, new Comparator<AppEntry>() {
            @Override
            public int compare(AppEntry a, AppEntry b) {
                return a.label.compareToIgnoreCase(b.label);
            }
        });
        out.addAll(extra);

        return out;
    }

    private static AppEntry build(Context ctx, PackageManager pm, ResolveInfo ri, String pkg) {
        ComponentName cn = new ComponentName(ri.activityInfo.packageName, ri.activityInfo.name);
        Intent launch = new Intent(Intent.ACTION_MAIN);
        launch.addCategory(Intent.CATEGORY_LAUNCHER);
        launch.setComponent(cn);
        launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED);

        CharSequence label = ri.loadLabel(pm);
        Drawable icon = null;
        String glyph = ICON_PACK.get(pkg);
        if (glyph != null) {
            int id = ctx.getResources().getIdentifier("ic_app_" + glyph, "drawable", ctx.getPackageName());
            if (id != 0) {
                icon = ctx.getResources().getDrawable(id);
            }
        }
        if (icon == null) {
            icon = ri.loadIcon(pm);
        }
        return new AppEntry(label == null ? pkg : label.toString(), icon, launch);
    }
}
