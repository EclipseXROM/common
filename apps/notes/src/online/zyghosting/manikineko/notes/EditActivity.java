package online.zyghosting.manikineko.notes;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.EditText;

/**
 * Edits one note. Saves when the screen is left (back, Home, or another app on top), so there is no
 * save button to forget; a blank note is discarded by the store.
 */
public class EditActivity extends Activity {

    static final String EXTRA_ID = "note_id";

    private NoteStore store;
    private EditText editor;
    private String id;
    private boolean deleted;
    private String loaded = "";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_edit);

        store = new NoteStore(this);
        editor = (EditText) findViewById(R.id.editor);

        id = getIntent().getStringExtra(EXTRA_ID);
        if (id == null) {
            id = store.newId();
        }
        loaded = store.read(id);
        editor.setText(loaded);
        editor.setSelection(editor.getText().length());

        findViewById(R.id.btn_share).setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                Intent send = new Intent(Intent.ACTION_SEND);
                send.setType("text/plain");
                send.putExtra(Intent.EXTRA_TEXT, editor.getText().toString());
                startActivity(Intent.createChooser(send, getString(R.string.share)));
            }
        });

        findViewById(R.id.btn_delete).setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                new AlertDialog.Builder(EditActivity.this)
                        .setMessage(R.string.delete_confirm)
                        .setPositiveButton(R.string.delete, new DialogInterface.OnClickListener() {
                            @Override
                            public void onClick(DialogInterface dialog, int which) {
                                deleted = true;
                                store.delete(id);
                                finish();
                            }
                        })
                        .setNegativeButton(R.string.cancel, null)
                        .show();
            }
        });
    }

    @Override
    protected void onPause() {
        super.onPause();
        if (deleted) {
            return;
        }
        String now = editor.getText().toString();
        if (!now.equals(loaded)) {
            store.write(id, now);
            loaded = now;
        } else if (now.trim().length() == 0) {
            store.delete(id);
        }
    }
}
