package online.zyghosting.manikineko.calendar;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.ContentValues;
import android.content.Context;
import android.content.Intent;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;

import java.util.ArrayList;
import java.util.List;

/** SQLite store of events (title + start time) and their one-shot reminder alarms. */
final class EventStore extends SQLiteOpenHelper {

    static final class Event {
        long id, time;
        String title;
    }

    private final Context ctx;

    EventStore(Context c) {
        super(c, "events.db", null, 1);
        ctx = c.getApplicationContext();
    }

    @Override
    public void onCreate(SQLiteDatabase db) {
        db.execSQL("CREATE TABLE events (_id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, time INTEGER NOT NULL)");
        db.execSQL("CREATE INDEX events_time ON events(time)");
    }

    @Override public void onUpgrade(SQLiteDatabase db, int o, int n) { }

    long add(String title, long time) {
        ContentValues v = new ContentValues();
        v.put("title", title);
        v.put("time", time);
        long id = getWritableDatabase().insert("events", null, v);
        if (id > 0) schedule(id, title, time);
        return id;
    }

    void delete(Event e) {
        getWritableDatabase().delete("events", "_id=?", new String[] { String.valueOf(e.id) });
        cancel(e.id);
    }

    List<Event> between(long from, long to) {
        return query("time >= ? AND time < ?", new String[] { String.valueOf(from), String.valueOf(to) });
    }

    List<Event> upcoming() {
        return query("time > ?", new String[] { String.valueOf(System.currentTimeMillis()) });
    }

    private List<Event> query(String where, String[] args) {
        List<Event> out = new ArrayList<Event>();
        Cursor c = getReadableDatabase().query("events", new String[] { "_id", "title", "time" }, where, args, null, null, "time");
        try {
            while (c.moveToNext()) {
                Event e = new Event();
                e.id = c.getLong(0);
                e.title = c.getString(1);
                e.time = c.getLong(2);
                out.add(e);
            }
        } finally {
            c.close();
        }
        return out;
    }

    private PendingIntent pending(long id, String title) {
        Intent i = new Intent(ctx, AlarmReceiver.class).setAction(AlarmReceiver.ACTION_ALARM).setData(android.net.Uri.parse("event://" + id));
        i.putExtra("title", title == null ? "" : title);
        i.putExtra("id", id);
        return PendingIntent.getBroadcast(ctx, 0, i, PendingIntent.FLAG_UPDATE_CURRENT);
    }

    void schedule(long id, String title, long time) {
        if (time <= System.currentTimeMillis()) return;
        ((AlarmManager) ctx.getSystemService(Context.ALARM_SERVICE)).set(AlarmManager.RTC_WAKEUP, time, pending(id, title));
    }

    private void cancel(long id) {
        ((AlarmManager) ctx.getSystemService(Context.ALARM_SERVICE)).cancel(pending(id, null));
    }

    /** After a reboot all alarms are gone: put the future ones back. */
    void rescheduleAll() {
        for (Event e : upcoming()) schedule(e.id, e.title, e.time);
    }
}
