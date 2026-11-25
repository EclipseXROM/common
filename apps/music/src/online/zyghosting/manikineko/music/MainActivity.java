package online.zyghosting.manikineko.music;

import android.app.Activity;
import android.content.Intent;
import android.database.Cursor;
import android.os.Bundle;
import android.os.Handler;
import android.provider.MediaStore;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AdapterView;
import android.widget.BaseAdapter;
import android.widget.Button;
import android.widget.ListView;
import android.widget.TextView;

/** Music player: tracks from MediaStore, playback in PlayerService so it continues with the screen off. */
public class MainActivity extends Activity {

    private final Handler handler = new Handler();
    private final TrackAdapter adapter = new TrackAdapter();
    private ListView list;
    private TextView empty, now;
    private Button play;

    private final Runnable refresh = new Runnable() {
        @Override public void run() {
            int i = PlayerService.index;
            boolean on = PlayerService.player != null;
            if (on && i >= 0 && i < PlayerService.playlist.size()) {
                PlayerService.Track t = PlayerService.playlist.get(i);
                now.setText(t.title + " - " + t.artist);
                play.setText(PlayerService.player.isPlaying() ? R.string.pause : R.string.play);
            } else {
                now.setText(R.string.nothing);
                play.setText(R.string.play);
            }
            adapter.notifyDataSetChanged();
            handler.postDelayed(this, 700);
        }
    };

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        setContentView(R.layout.activity_main);
        list = (ListView) findViewById(R.id.list);
        empty = (TextView) findViewById(R.id.empty);
        now = (TextView) findViewById(R.id.now);
        play = (Button) findViewById(R.id.btn_play);
        list.setAdapter(adapter);
        list.setOnItemClickListener(new AdapterView.OnItemClickListener() {
            @Override public void onItemClick(AdapterView<?> p, View v, int pos, long id) {
                startService(send(PlayerService.ACTION_PLAY_INDEX).putExtra("index", pos));
            }
        });
        findViewById(R.id.btn_prev).setOnClickListener(cmd(PlayerService.ACTION_PREV));
        findViewById(R.id.btn_next).setOnClickListener(cmd(PlayerService.ACTION_NEXT));
        play.setOnClickListener(cmd(PlayerService.ACTION_TOGGLE));
        load();
    }

    private Intent send(String action) {
        return new Intent(this, PlayerService.class).setAction(action);
    }

    private View.OnClickListener cmd(final String action) {
        return new View.OnClickListener() {
            @Override public void onClick(View v) { startService(send(action)); }
        };
    }

    private void load() {
        PlayerService.playlist.clear();
        Cursor c = getContentResolver().query(MediaStore.Audio.Media.EXTERNAL_CONTENT_URI,
                new String[] { MediaStore.Audio.Media.TITLE, MediaStore.Audio.Media.ARTIST, MediaStore.Audio.Media.DATA },
                MediaStore.Audio.Media.IS_MUSIC + " != 0", null, MediaStore.Audio.Media.TITLE + " COLLATE NOCASE");
        if (c != null) {
            try {
                while (c.moveToNext()) {
                    PlayerService.Track t = new PlayerService.Track();
                    t.title = c.getString(0);
                    t.artist = c.getString(1);
                    t.path = c.getString(2);
                    if (t.artist == null || t.artist.equals("<unknown>")) t.artist = getString(R.string.unknown_artist);
                    PlayerService.playlist.add(t);
                }
            } finally {
                c.close();
            }
        }
        boolean none = PlayerService.playlist.isEmpty();
        list.setVisibility(none ? View.GONE : View.VISIBLE);
        empty.setVisibility(none ? View.VISIBLE : View.GONE);
        adapter.notifyDataSetChanged();
    }

    @Override
    protected void onResume() {
        super.onResume();
        load();
        handler.post(refresh);
    }

    @Override
    protected void onPause() {
        super.onPause();
        handler.removeCallbacks(refresh);
    }

    private final class TrackAdapter extends BaseAdapter {
        @Override public int getCount() { return PlayerService.playlist.size(); }
        @Override public Object getItem(int p) { return PlayerService.playlist.get(p); }
        @Override public long getItemId(int p) { return p; }

        @Override
        public View getView(int position, View convertView, ViewGroup parent) {
            View v = convertView != null ? convertView : LayoutInflater.from(MainActivity.this).inflate(R.layout.item_track, parent, false);
            PlayerService.Track t = PlayerService.playlist.get(position);
            TextView title = (TextView) v.findViewById(R.id.track_title);
            boolean cur = position == PlayerService.index && PlayerService.player != null;
            title.setText(t.title);
            title.setTextColor(getResources().getColor(cur ? R.color.mk_accent : R.color.mk_text));
            ((TextView) v.findViewById(R.id.track_artist)).setText(t.artist);
            return v;
        }
    }
}
