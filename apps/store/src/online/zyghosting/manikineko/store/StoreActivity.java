package online.zyghosting.manikineko.store;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AdapterView;
import android.widget.BaseAdapter;
import android.widget.Button;
import android.widget.ListView;
import android.widget.ProgressBar;
import android.widget.TextView;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.LinkedList;
import java.util.List;

/**
 * Manikineko Store: signed catalog -> apps THIS device supports (SDK, ABI, OpenGL ES, optional device allow-list) -> install / update /
 * update all / uninstall / open. Apps with updates are listed first; a daily background check notifies about new versions.
 */
public class StoreActivity extends Activity {

    private final List<Catalog.App> apps = new ArrayList<Catalog.App>();
    private final LinkedList<Catalog.App> queue = new LinkedList<Catalog.App>();
    private final AppAdapter adapter = new AppAdapter();
    private ListView list;
    private TextView empty, status;
    private ProgressBar progress;
    private Button updateAll;
    private boolean busy, loading;
    private String lastName = "";
    private String updated = "";

    private final BroadcastReceiver resultReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context c, Intent i) {
            int st = i.getIntExtra("android.content.pm.extra.STATUS", -99);
            String msg = i.getStringExtra("android.content.pm.extra.STATUS_MESSAGE");
            if (st == -1) {                                   // STATUS_PENDING_USER_ACTION: not silent on this device
                Intent confirm = (Intent) i.getParcelableExtra(Intent.EXTRA_INTENT);
                if (confirm != null) { confirm.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK); startActivity(confirm); return; }
            }
            busy = false;
            progress.setVisibility(View.GONE);
            if (st == 0) setStatus(getString(R.string.done, lastName));
            else setStatus(getString(R.string.err_install, msg == null ? ("code " + st) : msg));
            refreshList();
            nextInQueue();
        }
    };

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        setContentView(R.layout.activity_store);
        list = (ListView) findViewById(R.id.list);
        empty = (TextView) findViewById(R.id.empty);
        status = (TextView) findViewById(R.id.status);
        progress = (ProgressBar) findViewById(R.id.progress);
        updateAll = (Button) findViewById(R.id.btn_update_all);
        list.setAdapter(adapter);
        findViewById(R.id.btn_refresh).setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) { load(); }
        });
        updateAll.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) { startUpdateAll(); }
        });
        list.setOnItemClickListener(new AdapterView.OnItemClickListener() {
            @Override public void onItemClick(AdapterView<?> p, View v, int pos, long id) { actions(apps.get(pos)); }
        });
        registerReceiver(resultReceiver, new IntentFilter(Installer.ACTION_RESULT));
        UpdateReceiver.schedule(this);                        // (re)arm the daily update check
        load();
    }

    @Override
    protected void onResume() {
        super.onResume();
        refreshList();
        if (!busy && !loading && !apps.isEmpty()) setStatus(summary());   // e.g. back from the system installer on old Android
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        unregisterReceiver(resultReceiver);
    }

    private void setStatus(String s) { status.setText(s); }

    // ---- catalog -------------------------------------------------------------------------------------------------

    private void load() {
        if (loading) return;
        loading = true;
        setStatus(getString(R.string.loading));
        new Thread(new Runnable() {
            @Override public void run() {
                Catalog cat = null;
                String err = null;
                try {
                    cat = Catalog.fetch(getString(R.string.catalog_base), getString(R.string.catalog_pubkey));
                } catch (Catalog.BadSignatureException e) {
                    err = getString(R.string.err_signature);
                } catch (Exception e) {
                    err = getString(R.string.err_network);
                }
                final Catalog c = cat; final String e = err;
                runOnUiThread(new Runnable() {
                    @Override public void run() {
                        loading = false;
                        if (isFinishing()) return;
                        apps.clear();
                        if (c != null) {
                            for (Catalog.App a : c.apps) if (Device.supports(StoreActivity.this, a)) apps.add(a);
                            updated = c.updated;
                        } else {
                            updated = "";
                            setStatus(e);
                        }
                        refreshList();
                        if (c != null) setStatus(summary());
                    }
                });
            }
        }).start();
    }

    private int installedCode(String pkg) {
        try {
            PackageInfo pi = getPackageManager().getPackageInfo(pkg, 0);
            return pi.versionCode;
        } catch (PackageManager.NameNotFoundException e) {
            return -1;
        }
    }

    private String installedName(String pkg) {
        try { return getPackageManager().getPackageInfo(pkg, 0).versionName; } catch (Exception e) { return ""; }
    }

    private boolean hasUpdate(Catalog.App a) {
        int have = installedCode(a.pkg);
        return have >= 0 && have < a.versionCode;
    }

    private int updateCount() {
        int n = 0;
        for (Catalog.App a : apps) if (hasUpdate(a)) n++;
        return n;
    }

    private String summary() {
        int n = updateCount();
        return n > 0 ? getResources().getQuantityString(R.plurals.updates_available, n, n) : getString(R.string.up_to_date, updated);
    }

    /** Updates first, then installed, then the rest, each group by name. */
    private void sortApps() {
        Collections.sort(apps, new Comparator<Catalog.App>() {
            @Override public int compare(Catalog.App a, Catalog.App b) {
                int ra = rank(a), rb = rank(b);
                return ra != rb ? ra - rb : a.name.compareToIgnoreCase(b.name);
            }
            private int rank(Catalog.App a) { return hasUpdate(a) ? 0 : installedCode(a.pkg) >= 0 ? 1 : 2; }
        });
    }

    private void refreshList() {
        sortApps();
        adapter.notifyDataSetChanged();
        boolean none = apps.isEmpty();
        list.setVisibility(none ? View.GONE : View.VISIBLE);
        empty.setVisibility(none ? View.VISIBLE : View.GONE);
        updateAll.setVisibility(updateCount() > 0 ? View.VISIBLE : View.GONE);
    }

    // ---- actions -------------------------------------------------------------------------------------------------

    private void actions(final Catalog.App a) {
        final int have = installedCode(a.pkg);
        final List<String> labels = new ArrayList<String>();
        final List<Runnable> acts = new ArrayList<Runnable>();
        if (have < 0 || have < a.versionCode) {
            labels.add(getString(have < 0 ? R.string.install : R.string.update));
            acts.add(new Runnable() { @Override public void run() { startInstall(a); } });
        }
        if (have >= 0) {
            labels.add(getString(R.string.open));
            acts.add(new Runnable() { @Override public void run() {
                Intent li = getPackageManager().getLaunchIntentForPackage(a.pkg);
                if (li != null) startActivity(li);
            } });
            labels.add(getString(R.string.uninstall));
            acts.add(new Runnable() { @Override public void run() {
                startActivity(new Intent(Intent.ACTION_DELETE, Uri.parse("package:" + a.pkg)));
            } });
        }
        if (labels.isEmpty()) return;
        new AlertDialog.Builder(this)
                .setTitle(a.name)
                .setItems(labels.toArray(new String[0]), new DialogInterface.OnClickListener() {
                    @Override public void onClick(DialogInterface d, int which) { acts.get(which).run(); }
                })
                .show();
    }

    private void startUpdateAll() {
        if (busy) return;
        queue.clear();
        for (Catalog.App a : apps) if (hasUpdate(a)) queue.add(a);
        nextInQueue();
    }

    private void nextInQueue() {
        if (busy || queue.isEmpty()) return;
        startInstall(queue.removeFirst());
    }

    private void startInstall(final Catalog.App a) {
        if (busy) return;
        busy = true;
        lastName = a.name;
        progress.setProgress(0);
        progress.setVisibility(View.VISIBLE);
        setStatus(getString(R.string.downloading, a.name));
        new Thread(new Runnable() {
            @Override public void run() {
                String err = null;
                java.io.File legacyApk = null;
                try {
                    Installer.Progress prog = new Installer.Progress() {
                        @Override public void onProgress(final int p) {
                            runOnUiThread(new Runnable() { @Override public void run() { progress.setProgress(p); } });
                        }
                    };
                    if (android.os.Build.VERSION.SDK_INT >= 21) {
                        Installer.install(StoreActivity.this, getString(R.string.catalog_base), a, prog);
                    } else {                                       // no PackageInstaller: verified download, then the system installer dialog
                        legacyApk = Installer.downloadVerified(StoreActivity.this, getString(R.string.catalog_base), a, prog);
                    }
                } catch (Installer.HashMismatchException e) {
                    err = getString(R.string.err_hash);
                } catch (Exception e) {
                    Throwable t = e.getCause() != null ? e.getCause() : e;
                    err = getString(R.string.err_install, String.valueOf(t.getMessage()));
                }
                final String fe = err;
                final java.io.File fl = legacyApk;
                runOnUiThread(new Runnable() { @Override public void run() {
                    if (fl != null) {                                  // legacy path: hand the verified file to the system installer
                        busy = false;
                        progress.setVisibility(View.GONE);
                        setStatus(getString(R.string.confirm_install, a.name));
                        Intent view = new Intent(Intent.ACTION_VIEW).setDataAndType(Uri.fromFile(fl), "application/vnd.android.package-archive");
                        view.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                        startActivity(view);
                    } else if (fe != null) {
                        busy = false;
                        progress.setVisibility(View.GONE);
                        setStatus(fe);
                        queue.clear();
                    } else {
                        setStatus(getString(R.string.installing, a.name));   // the result broadcast finishes the job
                    }
                } });
            }
        }).start();
    }

    private final class AppAdapter extends BaseAdapter {
        @Override public int getCount() { return apps.size(); }
        @Override public Object getItem(int p) { return apps.get(p); }
        @Override public long getItemId(int p) { return p; }

        @Override
        public View getView(int position, View convertView, ViewGroup parent) {
            View v = convertView != null ? convertView
                    : LayoutInflater.from(StoreActivity.this).inflate(R.layout.item_app, parent, false);
            Catalog.App a = apps.get(position);
            ((TextView) v.findViewById(R.id.app_name)).setText(a.name + "  " + a.versionName);
            ((TextView) v.findViewById(R.id.app_summary)).setText(a.summary);
            int have = installedCode(a.pkg);
            String st;
            if (have < 0) st = getString(R.string.state_new);
            else if (have < a.versionCode) st = getString(R.string.state_update, installedName(a.pkg), a.versionName);
            else st = getString(R.string.state_installed, installedName(a.pkg));
            TextView state = (TextView) v.findViewById(R.id.app_state);
            state.setText(st);
            state.setTextColor(getResources().getColor(have >= 0 && have < a.versionCode ? R.color.mk_danger : R.color.mk_accent));
            return v;
        }
    }
}
