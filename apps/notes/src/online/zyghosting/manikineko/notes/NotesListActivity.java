package online.zyghosting.manikineko.notes;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.content.Intent;
import android.os.Bundle;
import android.text.format.DateFormat;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AdapterView;
import android.widget.BaseAdapter;
import android.widget.ListView;
import android.widget.TextView;

import java.util.Date;
import java.util.List;

/** The note list: newest first, tap to edit, long-press to delete. */
public class NotesListActivity extends Activity {

    private NoteStore store;
    private ListView list;
    private TextView empty;
    private List<NoteStore.Note> notes;
    private final NotesAdapter adapter = new NotesAdapter();

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_list);

        store = new NoteStore(this);
        list = (ListView) findViewById(R.id.list);
        empty = (TextView) findViewById(R.id.empty);
        list.setAdapter(adapter);

        findViewById(R.id.btn_new).setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                open(store.newId());
            }
        });

        list.setOnItemClickListener(new AdapterView.OnItemClickListener() {
            @Override
            public void onItemClick(AdapterView<?> parent, View view, int position, long id) {
                open(notes.get(position).id);
            }
        });

        list.setOnItemLongClickListener(new AdapterView.OnItemLongClickListener() {
            @Override
            public boolean onItemLongClick(AdapterView<?> parent, View view, int position, long id) {
                confirmDelete(notes.get(position).id);
                return true;
            }
        });
    }

    @Override
    protected void onResume() {
        super.onResume();
        notes = store.list();
        adapter.notifyDataSetChanged();
        boolean none = notes.isEmpty();
        list.setVisibility(none ? View.GONE : View.VISIBLE);
        empty.setVisibility(none ? View.VISIBLE : View.GONE);
    }

    private void open(String id) {
        Intent i = new Intent(this, EditActivity.class);
        i.putExtra(EditActivity.EXTRA_ID, id);
        startActivity(i);
    }

    private void confirmDelete(final String id) {
        new AlertDialog.Builder(this)
                .setMessage(R.string.delete_confirm)
                .setPositiveButton(R.string.delete, new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface dialog, int which) {
                        store.delete(id);
                        onResume();
                    }
                })
                .setNegativeButton(R.string.cancel, null)
                .show();
    }

    private final class NotesAdapter extends BaseAdapter {

        @Override
        public int getCount() {
            return notes == null ? 0 : notes.size();
        }

        @Override
        public Object getItem(int position) {
            return notes.get(position);
        }

        @Override
        public long getItemId(int position) {
            return position;
        }

        @Override
        public View getView(int position, View convertView, ViewGroup parent) {
            View v = convertView;
            if (v == null) {
                v = LayoutInflater.from(NotesListActivity.this).inflate(R.layout.item_note, parent, false);
            }
            NoteStore.Note n = notes.get(position);
            ((TextView) v.findViewById(R.id.note_title)).setText(
                    n.title.length() == 0 ? getString(R.string.untitled) : n.title);
            ((TextView) v.findViewById(R.id.note_preview)).setText(n.preview);
            ((TextView) v.findViewById(R.id.note_date)).setText(
                    DateFormat.getMediumDateFormat(NotesListActivity.this).format(new Date(n.modified))
                            + "  "
                            + DateFormat.getTimeFormat(NotesListActivity.this).format(new Date(n.modified)));
            return v;
        }
    }
}
