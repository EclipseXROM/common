package online.zyghosting.manikineko.home;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.view.WindowManager;
import android.widget.AdapterView;
import android.widget.GridView;
import android.widget.TextView;

import java.util.List;

/**
 * The Manikineko home screen: a fixed grid of whitelisted apps on a dark surface.
 *
 * Deliberately minimal for 768 MB of RAM: no fragments, no support library, no
 * background services, no observers. The grid is rebuilt on resume so that an
 * app installed or removed while the launcher is backgrounded shows up.
 */
public class HomeActivity extends Activity implements AdapterView.OnItemClickListener {

    private GridView grid;
    private TextView empty;
    private AppGridAdapter adapter;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_home);

        grid = (GridView) findViewById(R.id.grid);
        empty = (TextView) findViewById(R.id.empty);
        grid.setOnItemClickListener(this);
        // The brand row is the only chrome on this screen: tapping it opens "Apie telefoną".
        findViewById(R.id.brand_row).setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                startActivity(new Intent(HomeActivity.this, AboutActivity.class));
            }
        });
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (!OobeActivity.isDone(this)) {                      // first run after a wipe: the setup comes before the grid
            startActivity(new Intent(this, OobeActivity.class));
            return;
        }
        reload();
    }

    private void reload() {
        List<AppEntry> entries = AppEntry.load(this);

        adapter = new AppGridAdapter(this, entries);
        grid.setAdapter(adapter);

        boolean none = entries.isEmpty();
        grid.setVisibility(none ? View.GONE : View.VISIBLE);
        empty.setVisibility(none ? View.VISIBLE : View.GONE);
    }

    @Override
    public void onItemClick(AdapterView<?> parent, View view, int position, long id) {
        AppEntry e = adapter.getItem(position);
        if (e == null) {
            return;
        }
        try {
            startActivity(e.intent);
        } catch (RuntimeException ignored) {
            // A whitelisted app can be removed between reload and tap.
            reload();
        }
    }

    @Override
    public void onBackPressed() {
        // Home is a root: back does nothing instead of leaving a blank task.
    }
}
