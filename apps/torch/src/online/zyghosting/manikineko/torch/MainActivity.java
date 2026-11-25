package online.zyghosting.manikineko.torch;

import android.app.Activity;
import android.graphics.SurfaceTexture;
import android.hardware.Camera;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.Toast;

/** Flashlight: camera flash in torch mode. Stays on while the app lives; off when the app is closed or toggled. */
public class MainActivity extends Activity {

    private Camera cam;
    private Button toggle;

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        setContentView(R.layout.activity_main);
        toggle = (Button) findViewById(R.id.toggle);
        toggle.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) { set(cam == null); }
        });
        set(true);
    }

    private void set(boolean on) {
        if (on) {
            try {
                cam = Camera.open();
                Camera.Parameters p = cam.getParameters();
                p.setFlashMode(Camera.Parameters.FLASH_MODE_TORCH);
                cam.setParameters(p);
                cam.setPreviewTexture(new SurfaceTexture(0));
                cam.startPreview();
            } catch (Exception e) {
                release();
                Toast.makeText(this, R.string.err, Toast.LENGTH_SHORT).show();
            }
        } else {
            release();
        }
        boolean lit = cam != null;
        toggle.setText(lit ? R.string.on : R.string.off);
        toggle.setBackgroundColor(getResources().getColor(lit ? R.color.mk_accent : R.color.mk_surface_hi));
        toggle.setTextColor(getResources().getColor(lit ? R.color.mk_bg : R.color.mk_text));
    }

    private void release() {
        if (cam != null) {
            try { cam.stopPreview(); } catch (Exception ignored) { }
            cam.release();
            cam = null;
        }
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        release();
    }
}
