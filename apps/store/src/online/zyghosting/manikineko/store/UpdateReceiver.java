package online.zyghosting.manikineko.store;

import android.app.AlarmManager;
import android.app.Notification;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;

/** Daily update check (also re-armed after a reboot). Notifies when installed store apps have a newer, compatible version. */
public class UpdateReceiver extends BroadcastReceiver {

    static final String ACTION_CHECK = "online.zyghosting.manikineko.store.CHECK_UPDATES";

    static void schedule(Context c) {
        PendingIntent pi = PendingIntent.getBroadcast(c, 0, new Intent(c, UpdateReceiver.class).setAction(ACTION_CHECK), PendingIntent.FLAG_UPDATE_CURRENT);
        ((AlarmManager) c.getSystemService(Context.ALARM_SERVICE)).setInexactRepeating(AlarmManager.ELAPSED_REALTIME,
                android.os.SystemClock.elapsedRealtime() + AlarmManager.INTERVAL_HOUR, AlarmManager.INTERVAL_DAY, pi);
    }

    /** Number of installed apps that have a compatible newer version in the (verified) catalog. */
    static int countUpdates(Context c, Catalog cat) {
        int n = 0;
        for (Catalog.App a : cat.apps) {
            if (!Device.supports(c, a)) continue;
            try {
                if (c.getPackageManager().getPackageInfo(a.pkg, 0).versionCode < a.versionCode) n++;
            } catch (PackageManager.NameNotFoundException ignored) { }
        }
        return n;
    }

    @SuppressWarnings("deprecation")
    @Override
    public void onReceive(final Context c, Intent i) {
        if (Intent.ACTION_BOOT_COMPLETED.equals(i.getAction())) { schedule(c); return; }
        if (!ACTION_CHECK.equals(i.getAction())) return;
        final PendingResult pr = goAsync();
        new Thread(new Runnable() {
            @Override public void run() {
                try {
                    Catalog cat = Catalog.fetch(c.getString(R.string.catalog_base), c.getString(R.string.catalog_pubkey));
                    int n = countUpdates(c, cat);
                    if (n > 0) {
                        PendingIntent open = PendingIntent.getActivity(c, 0, new Intent(c, StoreActivity.class), 0);
                        Notification note = new Notification.Builder(c)
                                .setSmallIcon(R.drawable.ic_launcher)
                                .setContentTitle(c.getString(R.string.app_name))
                                .setContentText(c.getResources().getQuantityString(R.plurals.updates_available, n, n))
                                .setContentIntent(open)
                                .setAutoCancel(true)
                                .getNotification();
                        ((NotificationManager) c.getSystemService(Context.NOTIFICATION_SERVICE)).notify(7, note);
                    }
                } catch (Exception ignored) {
                    // offline or bad signature: stay silent, try again tomorrow
                } finally {
                    pr.finish();
                }
            }
        }).start();
    }
}
