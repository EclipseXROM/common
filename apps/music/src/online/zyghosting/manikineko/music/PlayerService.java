package online.zyghosting.manikineko.music;

import android.app.Notification;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Intent;
import android.media.AudioManager;
import android.media.MediaPlayer;
import android.os.IBinder;

import java.util.ArrayList;
import java.util.List;

/** Plays the shared playlist in the background (started service, foreground notification while a track is loaded). */
public class PlayerService extends Service {

    static final class Track {
        String title, artist, path;
    }

    // process-wide state shared with the activity (same process, no IPC needed)
    static final List<Track> playlist = new ArrayList<Track>();
    static int index = -1;
    static MediaPlayer player;

    static final String ACTION_PLAY_INDEX = "play_index", ACTION_TOGGLE = "toggle", ACTION_NEXT = "next", ACTION_PREV = "prev";

    @Override
    public int onStartCommand(Intent i, int flags, int startId) {
        String a = i == null ? null : i.getAction();
        if (ACTION_PLAY_INDEX.equals(a)) play(i.getIntExtra("index", 0));
        else if (ACTION_TOGGLE.equals(a)) toggle();
        else if (ACTION_NEXT.equals(a)) play(index + 1);
        else if (ACTION_PREV.equals(a)) play(index - 1);
        return START_NOT_STICKY;
    }

    private void play(int i) {
        if (playlist.isEmpty()) return;
        if (i < 0) i = playlist.size() - 1;
        if (i >= playlist.size()) i = 0;
        release();
        index = i;
        try {
            MediaPlayer p = new MediaPlayer();
            p.setAudioStreamType(AudioManager.STREAM_MUSIC);
            p.setDataSource(playlist.get(i).path);
            p.prepare();
            p.start();
            p.setOnCompletionListener(new MediaPlayer.OnCompletionListener() {
                @Override public void onCompletion(MediaPlayer m) { play(index + 1); }
            });
            player = p;
            foreground();
        } catch (Exception e) {
            player = null;
            stopForeground(true);
        }
    }

    private void toggle() {
        if (player == null) return;
        if (player.isPlaying()) { player.pause(); stopForeground(false); } else { player.start(); foreground(); }
    }

    @SuppressWarnings("deprecation")
    private void foreground() {
        Track t = playlist.get(index);
        PendingIntent pi = PendingIntent.getActivity(this, 0, new Intent(this, MainActivity.class), 0);
        Notification n = new Notification.Builder(this)
                .setSmallIcon(R.drawable.ic_launcher)
                .setContentTitle(t.title)
                .setContentText(t.artist)
                .setContentIntent(pi)
                .setOngoing(true)
                .getNotification();
        startForeground(1, n);
    }

    private void release() {
        if (player != null) { try { player.release(); } catch (Exception ignored) { } player = null; }
    }

    @Override
    public void onDestroy() {
        release();
        super.onDestroy();
    }

    @Override public IBinder onBind(Intent i) { return null; }
}
