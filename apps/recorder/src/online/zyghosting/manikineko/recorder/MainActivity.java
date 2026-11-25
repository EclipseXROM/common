package online.zyghosting.manikineko.recorder;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.content.Intent;
import android.media.MediaPlayer;
import android.media.MediaRecorder;
import android.net.Uri;
import android.os.Bundle;
import android.os.Environment;
import android.os.Handler;
import android.os.SystemClock;
import android.text.format.DateFormat;
import android.text.format.Formatter;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AdapterView;
import android.widget.BaseAdapter;
import android.widget.Button;
import android.widget.ListView;
import android.widget.TextView;
import android.widget.Toast;

import java.io.File;
import java.text.SimpleDateFormat;
import java.util.Arrays;
import java.util.Comparator;
import java.util.Date;
import java.util.Locale;

/** Voice recorder: AAC/MPEG-4 into /sdcard/Recordings, tap to play, long-press to share or delete. */
public class MainActivity extends Activity {

    private final Handler handler = new Handler();
    private final RecAdapter adapter = new RecAdapter();
    private File dir;
    private File[] files = new File[0];
    private MediaRecorder recorder;
    private MediaPlayer player;
    private File playing;
    private long startedAt;
    private TextView timer, empty;
    private Button btn;
    private ListView list;

    private final Runnable tick = new Runnable() {
        @Override public void run() {
            long s = (SystemClock.elapsedRealtime() - startedAt) / 1000;
            timer.setText(String.format(Locale.US, "%02d:%02d", s / 60, s % 60));
            handler.postDelayed(this, 500);
        }
    };

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        setContentView(R.layout.activity_main);
        dir = new File(Environment.getExternalStorageDirectory(), "Recordings");
        timer = (TextView) findViewById(R.id.timer);
        empty = (TextView) findViewById(R.id.empty);
        btn = (Button) findViewById(R.id.btn_record);
        list = (ListView) findViewById(R.id.list);
        list.setAdapter(adapter);
        btn.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) { if (recorder == null) startRecording(); else stopRecording(); }
        });
        list.setOnItemClickListener(new AdapterView.OnItemClickListener() {
            @Override public void onItemClick(AdapterView<?> p, View v, int pos, long id) { toggle(files[pos]); }
        });
        list.setOnItemLongClickListener(new AdapterView.OnItemLongClickListener() {
            @Override public boolean onItemLongClick(AdapterView<?> p, View v, int pos, long id) { actions(files[pos]); return true; }
        });
        reload();
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (recorder != null) stopRecording();
        stopPlayback();
    }

    private void reload() {
        File[] f = dir.listFiles();
        if (f == null) f = new File[0];
        Arrays.sort(f, new Comparator<File>() {
            @Override public int compare(File a, File b) { return a.lastModified() < b.lastModified() ? 1 : a.lastModified() > b.lastModified() ? -1 : 0; }
        });
        files = f;
        adapter.notifyDataSetChanged();
        boolean none = files.length == 0;
        list.setVisibility(none ? View.GONE : View.VISIBLE);
        empty.setVisibility(none ? View.VISIBLE : View.GONE);
    }

    private void startRecording() {
        stopPlayback();
        dir.mkdirs();
        File out = new File(dir, "rec_" + new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(new Date()) + ".m4a");
        try {
            MediaRecorder r = new MediaRecorder();
            r.setAudioSource(MediaRecorder.AudioSource.MIC);
            r.setOutputFormat(MediaRecorder.OutputFormat.MPEG_4);
            r.setAudioEncoder(MediaRecorder.AudioEncoder.AAC);
            r.setAudioEncodingBitRate(64000);
            r.setAudioSamplingRate(44100);
            r.setOutputFile(out.getAbsolutePath());
            r.prepare();
            r.start();
            recorder = r;
        } catch (Exception e) {
            Toast.makeText(this, R.string.err, Toast.LENGTH_SHORT).show();
            out.delete();
            return;
        }
        startedAt = SystemClock.elapsedRealtime();
        handler.post(tick);
        btn.setText(R.string.stop);
        btn.setBackgroundColor(getResources().getColor(R.color.mk_danger));
    }

    private void stopRecording() {
        handler.removeCallbacks(tick);
        try { recorder.stop(); } catch (Exception ignored) { }
        recorder.release();
        recorder = null;
        timer.setText("00:00");
        btn.setText(R.string.record);
        btn.setBackgroundColor(getResources().getColor(R.color.mk_accent));
        reload();
    }

    private void toggle(File f) {
        boolean same = f.equals(playing);
        stopPlayback();
        if (same) return;
        try {
            player = new MediaPlayer();
            player.setDataSource(f.getAbsolutePath());
            player.prepare();
            player.start();
            playing = f;
            player.setOnCompletionListener(new MediaPlayer.OnCompletionListener() {
                @Override public void onCompletion(MediaPlayer m) { stopPlayback(); }
            });
        } catch (Exception e) {
            stopPlayback();
            Toast.makeText(this, R.string.err, Toast.LENGTH_SHORT).show();
        }
        adapter.notifyDataSetChanged();
    }

    private void stopPlayback() {
        if (player != null) { try { player.release(); } catch (Exception ignored) { } player = null; }
        playing = null;
        adapter.notifyDataSetChanged();
    }

    private void actions(final File f) {
        new AlertDialog.Builder(this)
                .setTitle(f.getName())
                .setItems(new String[] { getString(R.string.share), getString(R.string.delete) }, new DialogInterface.OnClickListener() {
                    @Override public void onClick(DialogInterface d, int which) {
                        if (which == 0) {
                            Intent s = new Intent(Intent.ACTION_SEND);
                            s.setType("audio/mp4");
                            s.putExtra(Intent.EXTRA_STREAM, Uri.fromFile(f));
                            startActivity(Intent.createChooser(s, getString(R.string.share)));
                        } else {
                            confirmDelete(f);
                        }
                    }
                }).show();
    }

    private void confirmDelete(final File f) {
        new AlertDialog.Builder(this)
                .setMessage(R.string.delete_confirm)
                .setPositiveButton(R.string.delete, new DialogInterface.OnClickListener() {
                    @Override public void onClick(DialogInterface d, int w) {
                        if (f.equals(playing)) stopPlayback();
                        f.delete();
                        reload();
                    }
                })
                .setNegativeButton(R.string.cancel, null)
                .show();
    }

    private final class RecAdapter extends BaseAdapter {
        @Override public int getCount() { return files.length; }
        @Override public Object getItem(int p) { return files[p]; }
        @Override public long getItemId(int p) { return p; }

        @Override
        public View getView(int position, View convertView, ViewGroup parent) {
            View v = convertView != null ? convertView : LayoutInflater.from(MainActivity.this).inflate(R.layout.item_rec, parent, false);
            File f = files[position];
            TextView name = (TextView) v.findViewById(R.id.rec_name);
            name.setText((f.equals(playing) ? "▶ " : "") + f.getName());
            name.setTextColor(getResources().getColor(f.equals(playing) ? R.color.mk_accent : R.color.mk_text));
            ((TextView) v.findViewById(R.id.rec_info)).setText(Formatter.formatShortFileSize(MainActivity.this, f.length()) + "  "
                    + DateFormat.getMediumDateFormat(MainActivity.this).format(new Date(f.lastModified())) + " "
                    + DateFormat.getTimeFormat(MainActivity.this).format(new Date(f.lastModified())));
            return v;
        }
    }
}
