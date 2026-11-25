package online.zyghosting.manikineko.calendar;

import android.app.Notification;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** Fires event reminders and restores the alarms after a reboot. */
public class AlarmReceiver extends BroadcastReceiver {

    static final String ACTION_ALARM = "online.zyghosting.manikineko.calendar.ALARM";

    @SuppressWarnings("deprecation")
    @Override
    public void onReceive(Context c, Intent i) {
        if (Intent.ACTION_BOOT_COMPLETED.equals(i.getAction())) {
            new EventStore(c).rescheduleAll();
            return;
        }
        if (!ACTION_ALARM.equals(i.getAction())) return;
        String title = i.getStringExtra("title");
        PendingIntent open = PendingIntent.getActivity(c, 0, new Intent(c, MainActivity.class), 0);
        Notification n = new Notification.Builder(c)
                .setSmallIcon(R.drawable.ic_launcher)
                .setContentTitle(title)
                .setContentText(c.getString(R.string.reminder))
                .setContentIntent(open)
                .setAutoCancel(true)
                .setDefaults(Notification.DEFAULT_SOUND | Notification.DEFAULT_VIBRATE)
                .getNotification();
        ((NotificationManager) c.getSystemService(Context.NOTIFICATION_SERVICE)).notify((int) i.getLongExtra("id", 0), n);
    }
}
