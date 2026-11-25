package online.zyghosting.manikineko.level;

import android.app.Activity;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.os.Bundle;
import android.widget.TextView;

/** Spirit level from the accelerometer (this phone has no magnetometer, so no compass). */
public class MainActivity extends Activity implements SensorEventListener {

    private SensorManager sm;
    private LevelView view;
    private TextView readout;
    private float ax, ay, az = 9.81f;

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        setContentView(R.layout.activity_main);
        view = (LevelView) findViewById(R.id.level);
        readout = (TextView) findViewById(R.id.readout);
        sm = (SensorManager) getSystemService(SENSOR_SERVICE);
        if (sm.getDefaultSensor(Sensor.TYPE_ACCELEROMETER) == null) readout.setText(R.string.no_sensor);
    }

    @Override
    protected void onResume() {
        super.onResume();
        Sensor s = sm.getDefaultSensor(Sensor.TYPE_ACCELEROMETER);
        if (s != null) sm.registerListener(this, s, SensorManager.SENSOR_DELAY_GAME);
    }

    @Override
    protected void onPause() {
        super.onPause();
        sm.unregisterListener(this);
    }

    @Override
    public void onSensorChanged(SensorEvent e) {
        final float k = 0.15f;                                   // low-pass filter
        ax += k * (e.values[0] - ax);
        ay += k * (e.values[1] - ay);
        az += k * (e.values[2] - az);
        float g = (float) Math.sqrt(ax * ax + ay * ay + az * az);
        if (g < 1f) return;
        float rollDeg = (float) Math.toDegrees(Math.asin(Math.max(-1, Math.min(1, ax / g))));
        float pitchDeg = (float) Math.toDegrees(Math.asin(Math.max(-1, Math.min(1, ay / g))));
        boolean flat = Math.abs(rollDeg) < 1f && Math.abs(pitchDeg) < 1f;
        view.setTilt(-ax / g * 3f, ay / g * 3f, flat);
        readout.setText(flat ? getString(R.string.flat) : String.format("%.1f°   %.1f°", rollDeg, pitchDeg));
    }

    @Override
    public void onAccuracyChanged(Sensor s, int a) { }
}
