package online.zyghosting.manikineko.calendar;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.os.Bundle;
import android.text.format.DateFormat;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AdapterView;
import android.widget.BaseAdapter;
import android.widget.CalendarView;
import android.widget.EditText;
import android.widget.ListView;
import android.widget.TextView;
import android.widget.TimePicker;

import java.util.Calendar;
import java.util.Date;
import java.util.List;

/** Month calendar with a per-day event list. Events live in SQLite; each future event gets a reminder notification. */
public class MainActivity extends Activity {

    private EventStore store;
    private CalendarView cal;
    private ListView list;
    private TextView empty;
    private List<EventStore.Event> events;
    private final EventAdapter adapter = new EventAdapter();
    private long day;                                   // midnight of the selected day

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        setContentView(R.layout.activity_main);
        store = new EventStore(this);
        cal = (CalendarView) findViewById(R.id.cal);
        list = (ListView) findViewById(R.id.list);
        empty = (TextView) findViewById(R.id.empty);
        list.setAdapter(adapter);
        day = midnight(System.currentTimeMillis());
        cal.setOnDateChangeListener(new CalendarView.OnDateChangeListener() {
            @Override public void onSelectedDayChange(CalendarView v, int y, int m, int d) {
                Calendar c = Calendar.getInstance();
                c.clear();
                c.set(y, m, d);
                day = c.getTimeInMillis();
                reload();
            }
        });
        findViewById(R.id.btn_new).setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) { newEvent(); }
        });
        list.setOnItemLongClickListener(new AdapterView.OnItemLongClickListener() {
            @Override public boolean onItemLongClick(AdapterView<?> p, View v, int pos, long id) { confirmDelete(events.get(pos)); return true; }
        });
        reload();
    }

    private static long midnight(long t) {
        Calendar c = Calendar.getInstance();
        c.setTimeInMillis(t);
        c.set(Calendar.HOUR_OF_DAY, 0); c.set(Calendar.MINUTE, 0); c.set(Calendar.SECOND, 0); c.set(Calendar.MILLISECOND, 0);
        return c.getTimeInMillis();
    }

    private void reload() {
        Calendar next = Calendar.getInstance();
        next.setTimeInMillis(day);
        next.add(Calendar.DAY_OF_MONTH, 1);
        events = store.between(day, next.getTimeInMillis());
        adapter.notifyDataSetChanged();
        boolean none = events.isEmpty();
        list.setVisibility(none ? View.GONE : View.VISIBLE);
        empty.setVisibility(none ? View.VISIBLE : View.GONE);
    }

    private void newEvent() {
        View form = LayoutInflater.from(this).inflate(R.layout.dialog_new, null);
        final EditText input = (EditText) form.findViewById(R.id.ev_input);
        final TimePicker tp = (TimePicker) form.findViewById(R.id.ev_picker);
        tp.setIs24HourView(true);
        Calendar now = Calendar.getInstance();
        tp.setCurrentHour(now.get(Calendar.HOUR_OF_DAY));
        tp.setCurrentMinute(now.get(Calendar.MINUTE));
        new AlertDialog.Builder(this)
                .setTitle(DateFormat.getLongDateFormat(this).format(new Date(day)))
                .setView(form)
                .setPositiveButton(R.string.save, new DialogInterface.OnClickListener() {
                    @Override public void onClick(DialogInterface d, int w) {
                        String title = input.getText().toString().trim();
                        if (title.length() == 0) return;
                        Calendar c = Calendar.getInstance();
                        c.setTimeInMillis(day);
                        c.set(Calendar.HOUR_OF_DAY, tp.getCurrentHour());
                        c.set(Calendar.MINUTE, tp.getCurrentMinute());
                        store.add(title, c.getTimeInMillis());
                        reload();
                    }
                })
                .setNegativeButton(R.string.cancel, null)
                .show();
    }

    private void confirmDelete(final EventStore.Event e) {
        new AlertDialog.Builder(this)
                .setMessage(getString(R.string.delete_confirm, e.title))
                .setPositiveButton(R.string.delete, new DialogInterface.OnClickListener() {
                    @Override public void onClick(DialogInterface d, int w) { store.delete(e); reload(); }
                })
                .setNegativeButton(R.string.cancel, null)
                .show();
    }

    private final class EventAdapter extends BaseAdapter {
        @Override public int getCount() { return events == null ? 0 : events.size(); }
        @Override public Object getItem(int p) { return events.get(p); }
        @Override public long getItemId(int p) { return events.get(p).id; }

        @Override
        public View getView(int position, View convertView, ViewGroup parent) {
            View v = convertView != null ? convertView : LayoutInflater.from(MainActivity.this).inflate(R.layout.item_event, parent, false);
            EventStore.Event e = events.get(position);
            ((TextView) v.findViewById(R.id.ev_time)).setText(DateFormat.getTimeFormat(MainActivity.this).format(new Date(e.time)));
            ((TextView) v.findViewById(R.id.ev_title)).setText(e.title);
            return v;
        }
    }
}
