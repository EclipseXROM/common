package online.zyghosting.manikineko.radio;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AdapterView;
import android.widget.BaseAdapter;
import android.widget.ListView;
import android.widget.TextView;

/** Two MRPL stations; tap to play (service keeps streaming in the background), Stop to end. */
public class MainActivity extends Activity {

    private final Handler handler = new Handler();
    private final StationAdapter adapter = new StationAdapter();
    private TextView status;

    private final Runnable refresh = new Runnable() {
        @Override public void run() {
            switch (RadioService.state) {
                case RadioService.CONNECTING: status.setText(R.string.state_connecting); break;
                case RadioService.PLAYING: status.setText(getString(R.string.state_playing) + ": " + RadioService.STATIONS[RadioService.station][0]); break;
                case RadioService.ERROR: status.setText(R.string.state_error); break;
                default: status.setText(R.string.state_idle);
            }
            adapter.notifyDataSetChanged();
            handler.postDelayed(this, 500);
        }
    };

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        setContentView(R.layout.activity_main);
        status = (TextView) findViewById(R.id.status);
        ListView list = (ListView) findViewById(R.id.list);
        list.setAdapter(adapter);
        list.setOnItemClickListener(new AdapterView.OnItemClickListener() {
            @Override public void onItemClick(AdapterView<?> p, View v, int pos, long id) {
                startService(new Intent(MainActivity.this, RadioService.class).setAction(RadioService.ACTION_PLAY).putExtra("station", pos));
            }
        });
        findViewById(R.id.btn_stop).setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) {
                startService(new Intent(MainActivity.this, RadioService.class).setAction(RadioService.ACTION_STOP));
            }
        });
    }

    @Override
    protected void onResume() {
        super.onResume();
        handler.post(refresh);
    }

    @Override
    protected void onPause() {
        super.onPause();
        handler.removeCallbacks(refresh);
    }

    private final class StationAdapter extends BaseAdapter {
        @Override public int getCount() { return RadioService.STATIONS.length; }
        @Override public Object getItem(int p) { return RadioService.STATIONS[p]; }
        @Override public long getItemId(int p) { return p; }

        @Override
        public View getView(int position, View convertView, ViewGroup parent) {
            View v = convertView != null ? convertView : LayoutInflater.from(MainActivity.this).inflate(R.layout.item_station, parent, false);
            TextView name = (TextView) v.findViewById(R.id.st_name);
            name.setText(position == 0 ? getString(R.string.station_main) : getString(R.string.station_classics));
            ((TextView) v.findViewById(R.id.st_sub)).setText(position == 0 ? getString(R.string.station_main_sub) : getString(R.string.station_classics_sub));
            boolean cur = position == RadioService.station && RadioService.state != RadioService.IDLE;
            name.setTextColor(getResources().getColor(cur ? R.color.mk_accent : R.color.mk_text));
            return v;
        }
    }
}
