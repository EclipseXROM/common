package online.zyghosting.manikineko.files;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.os.Environment;
import android.text.format.DateFormat;
import android.text.format.Formatter;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.webkit.MimeTypeMap;
import android.widget.AdapterView;
import android.widget.BaseAdapter;
import android.widget.EditText;
import android.widget.ListView;
import android.widget.TextView;
import android.widget.Toast;

import java.io.File;
import java.util.Arrays;
import java.util.Comparator;
import java.util.Date;
import java.util.Locale;

/** Minimal file browser rooted at shared storage: folders first, tap to open, long-press for share/delete. */
public class FilesActivity extends Activity {

    private File root;
    private File dir;
    private File[] entries = new File[0];
    private ListView list;
    private TextView empty;
    private TextView pathView;
    private final FileAdapter adapter = new FileAdapter();

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_files);
        root = Environment.getExternalStorageDirectory();
        dir = root;
        if (savedInstanceState != null) {
            String p = savedInstanceState.getString("dir");
            if (p != null && isInsideRoot(new File(p))) dir = new File(p);
        }

        list = (ListView) findViewById(R.id.list);
        empty = (TextView) findViewById(R.id.empty);
        pathView = (TextView) findViewById(R.id.path);
        list.setAdapter(adapter);

        findViewById(R.id.btn_new).setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                newFolder();
            }
        });
        list.setOnItemClickListener(new AdapterView.OnItemClickListener() {
            @Override
            public void onItemClick(AdapterView<?> parent, View view, int position, long id) {
                File f = entries[position];
                if (f.isDirectory()) {
                    dir = f;
                    reload();
                } else {
                    openFile(f);
                }
            }
        });
        list.setOnItemLongClickListener(new AdapterView.OnItemLongClickListener() {
            @Override
            public boolean onItemLongClick(AdapterView<?> parent, View view, int position, long id) {
                actions(entries[position]);
                return true;
            }
        });
    }

    @Override
    protected void onResume() {
        super.onResume();
        reload();
    }

    @Override
    protected void onSaveInstanceState(Bundle out) {
        super.onSaveInstanceState(out);
        out.putString("dir", dir.getAbsolutePath());
    }

    @Override
    public void onBackPressed() {
        File parent = dir.getParentFile();
        if (!dir.equals(root) && parent != null && isInsideRoot(parent)) {
            dir = parent;
            reload();
        } else {
            super.onBackPressed();
        }
    }

    private boolean isInsideRoot(File f) {
        try {
            String r = root.getCanonicalPath();
            String p = f.getCanonicalPath();
            return p.equals(r) || p.startsWith(r + "/");
        } catch (Exception e) {
            return false;
        }
    }

    private void reload() {
        File[] found = dir.listFiles();
        if (found == null) found = new File[0];
        Arrays.sort(found, new Comparator<File>() {
            @Override
            public int compare(File a, File b) {
                if (a.isDirectory() != b.isDirectory()) return a.isDirectory() ? -1 : 1;
                return a.getName().toLowerCase(Locale.getDefault()).compareTo(b.getName().toLowerCase(Locale.getDefault()));
            }
        });
        entries = found;
        String rel = dir.equals(root) ? "/" : dir.getAbsolutePath().substring(root.getAbsolutePath().length());
        pathView.setText(rel);
        adapter.notifyDataSetChanged();
        boolean none = entries.length == 0;
        list.setVisibility(none ? View.GONE : View.VISIBLE);
        empty.setVisibility(none ? View.VISIBLE : View.GONE);
    }

    private static String mimeOf(File f) {
        String name = f.getName();
        int dot = name.lastIndexOf('.');
        if (dot < 0) return "*/*";
        String m = MimeTypeMap.getSingleton().getMimeTypeFromExtension(name.substring(dot + 1).toLowerCase(Locale.US));
        return m == null ? "*/*" : m;
    }

    private void openFile(File f) {
        Intent i = new Intent(Intent.ACTION_VIEW);
        i.setDataAndType(Uri.fromFile(f), mimeOf(f));
        try {
            startActivity(i);
        } catch (Exception e) {
            Toast.makeText(this, R.string.no_app, Toast.LENGTH_SHORT).show();
        }
    }

    private void actions(final File f) {
        String[] items = f.isDirectory()
                ? new String[] { getString(R.string.delete) }
                : new String[] { getString(R.string.share), getString(R.string.delete) };
        new AlertDialog.Builder(this)
                .setTitle(f.getName())
                .setItems(items, new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface d, int which) {
                        boolean share = !f.isDirectory() && which == 0;
                        if (share) {
                            Intent s = new Intent(Intent.ACTION_SEND);
                            s.setType(mimeOf(f));
                            s.putExtra(Intent.EXTRA_STREAM, Uri.fromFile(f));
                            startActivity(Intent.createChooser(s, getString(R.string.share)));
                        } else {
                            confirmDelete(f);
                        }
                    }
                })
                .show();
    }

    private void confirmDelete(final File f) {
        new AlertDialog.Builder(this)
                .setMessage(getString(R.string.delete_confirm, f.getName()))
                .setPositiveButton(R.string.delete, new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface d, int which) {
                        if (!deleteTree(f)) Toast.makeText(FilesActivity.this, R.string.failed, Toast.LENGTH_SHORT).show();
                        reload();
                    }
                })
                .setNegativeButton(R.string.cancel, null)
                .show();
    }

    /** Deletes a file or folder; a symlinked folder is unlinked, never followed. */
    private static boolean deleteTree(File f) {
        try {
            if (f.isDirectory() && f.getCanonicalPath().equals(f.getAbsolutePath())) {
                File[] kids = f.listFiles();
                if (kids != null) for (File k : kids) deleteTree(k);
            }
        } catch (Exception ignored) {
        }
        return f.delete();
    }

    private void newFolder() {
        final EditText input = new EditText(this);
        input.setSingleLine(true);
        input.setHint(R.string.folder_name);
        new AlertDialog.Builder(this)
                .setTitle(R.string.new_folder)
                .setView(input)
                .setPositiveButton(R.string.create, new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface d, int which) {
                        String name = input.getText().toString().trim();
                        if (name.length() == 0 || name.indexOf('/') >= 0 || name.equals(".") || name.equals("..")
                                || !new File(dir, name).mkdir()) {
                            Toast.makeText(FilesActivity.this, R.string.failed, Toast.LENGTH_SHORT).show();
                        }
                        reload();
                    }
                })
                .setNegativeButton(R.string.cancel, null)
                .show();
    }

    private final class FileAdapter extends BaseAdapter {
        @Override public int getCount() { return entries.length; }
        @Override public Object getItem(int p) { return entries[p]; }
        @Override public long getItemId(int p) { return p; }

        @Override
        public View getView(int position, View convertView, ViewGroup parent) {
            View v = convertView;
            if (v == null) v = LayoutInflater.from(FilesActivity.this).inflate(R.layout.item_file, parent, false);
            File f = entries[position];
            TextView name = (TextView) v.findViewById(R.id.file_name);
            name.setText(f.isDirectory() ? f.getName() + "/" : f.getName());
            name.setTextColor(getResources().getColor(f.isDirectory() ? R.color.mk_accent : R.color.mk_text));
            String info;
            if (f.isDirectory()) {
                String[] n = f.list();
                info = getString(R.string.items, n == null ? 0 : n.length);
            } else {
                info = Formatter.formatShortFileSize(FilesActivity.this, f.length()) + "  "
                        + DateFormat.getMediumDateFormat(FilesActivity.this).format(new Date(f.lastModified()));
            }
            ((TextView) v.findViewById(R.id.file_info)).setText(info);
            return v;
        }
    }
}
