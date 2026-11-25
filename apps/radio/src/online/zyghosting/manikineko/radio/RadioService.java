package online.zyghosting.manikineko.radio;

import android.app.Notification;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.media.AudioManager;
import android.media.MediaPlayer;
import android.net.wifi.WifiManager;
import android.os.Handler;
import android.os.IBinder;
import android.os.PowerManager;

/** Streams the selected station in the background: foreground notification, Wi-Fi lock, one automatic retry on error. */
public class RadioService extends Service implements MediaPlayer.OnPreparedListener, MediaPlayer.OnErrorListener,
        AudioManager.OnAudioFocusChangeListener {

    static final String ACTION_PLAY = "play", ACTION_STOP = "stop";
    static final int IDLE = 0, CONNECTING = 1, PLAYING = 2, ERROR = 3;

    /** name, subtitle, url */
    static final String[][] STATIONS = {
        { "MRPL", "Main stream", "https://mrpl.babrai.com/stream.mp3" },
        { "MRPL Classics", "Classics stream", "https://mrpl.babrai.com/classics.mp3" },
    };

    // read by the activity (same process)
    static volatile int state = IDLE;
    static volatile int station = -1;

    private MediaPlayer player;
    private WifiManager.WifiLock wifiLock;
    private final Handler handler = new Handler();
    private int retries;

    @Override
    public int onStartCommand(Intent i, int flags, int startId) {
        String a = i == null ? null : i.getAction();
        if (ACTION_PLAY.equals(a)) start(i.getIntExtra("station", 0));
        else stopAll();
        return START_NOT_STICKY;
    }

    private void start(int s) {
        if (s < 0 || s >= STATIONS.length) return;
        release();
        handler.removeCallbacksAndMessages(null);
        station = s;
        state = CONNECTING;
        retries = 0;
        foreground();
        AudioManager am = (AudioManager) getSystemService(Context.AUDIO_SERVICE);
        am.requestAudioFocus(this, AudioManager.STREAM_MUSIC, AudioManager.AUDIOFOCUS_GAIN);
        WifiManager wm = (WifiManager) getSystemService(Context.WIFI_SERVICE);
        if (wifiLock == null) wifiLock = wm.createWifiLock(WifiManager.WIFI_MODE_FULL, "mrpl-radio");
        if (!wifiLock.isHeld()) wifiLock.acquire();
        open();
    }

    private void open() {
        release();
        try {
            MediaPlayer p = new MediaPlayer();
            p.setAudioStreamType(AudioManager.STREAM_MUSIC);
            p.setWakeMode(this, PowerManager.PARTIAL_WAKE_LOCK);
            p.setDataSource(STATIONS[station][2]);
            p.setOnPreparedListener(this);
            p.setOnErrorListener(this);
            player = p;
            p.prepareAsync();
        } catch (Exception e) {
            fail();
        }
    }

    @Override
    public void onPrepared(MediaPlayer mp) {
        if (mp != player) return;
        mp.start();
        state = PLAYING;
        retries = 0;
    }

    @Override
    public boolean onError(MediaPlayer mp, int what, int extra) {
        if (mp != player) return true;
        if (retries++ < 1) {                                   // one quiet retry, streams drop now and then
            state = CONNECTING;
            handler.postDelayed(new Runnable() { @Override public void run() { if (state == CONNECTING) open(); } }, 2500);
        } else {
            fail();
        }
        return true;
    }

    private void fail() {
        release();
        state = ERROR;
        stopForeground(true);
        releaseLocks();
    }

    @Override
    public void onAudioFocusChange(int change) {
        if (change == AudioManager.AUDIOFOCUS_LOSS || change == AudioManager.AUDIOFOCUS_LOSS_TRANSIENT) stopAll();
    }

    private void stopAll() {
        handler.removeCallbacksAndMessages(null);
        release();
        state = IDLE;
        station = -1;
        releaseLocks();
        ((AudioManager) getSystemService(Context.AUDIO_SERVICE)).abandonAudioFocus(this);
        stopForeground(true);
        stopSelf();
    }

    private void release() {
        if (player != null) {
            try { player.reset(); } catch (Exception ignored) { }
            player.release();
            player = null;
        }
    }

    private void releaseLocks() {
        if (wifiLock != null && wifiLock.isHeld()) wifiLock.release();
    }

    @SuppressWarnings("deprecation")
    private void foreground() {
        PendingIntent open = PendingIntent.getActivity(this, 0, new Intent(this, MainActivity.class), 0);
        PendingIntent stop = PendingIntent.getService(this, 1, new Intent(this, RadioService.class).setAction(ACTION_STOP), 0);
        Notification n = new Notification.Builder(this)
                .setSmallIcon(R.drawable.ic_launcher)
                .setContentTitle(STATIONS[station][0])
                .setContentText(STATIONS[station][1])
                .setContentIntent(open)
                .addAction(android.R.drawable.ic_media_pause, getString(R.string.stop), stop)
                .setOngoing(true)
                .getNotification();
        startForeground(2, n);
    }

    @Override
    public void onDestroy() {
        stateReset();
        release();
        releaseLocks();
        super.onDestroy();
    }

    private void stateReset() {
        if (state != ERROR) { state = IDLE; station = -1; }
    }

    @Override public IBinder onBind(Intent i) { return null; }
}
