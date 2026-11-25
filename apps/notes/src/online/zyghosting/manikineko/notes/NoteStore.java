package online.zyghosting.manikineko.notes;

import android.content.Context;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;

/**
 * Plain-file note storage: one UTF-8 text file per note in the app's private directory.
 * The file name is the creation time in milliseconds, which doubles as the note id.
 * No database, no indexes: at the sizes this phone will ever see, listing the directory is instant.
 */
final class NoteStore {

    static final class Note {
        final String id;
        final String title;
        final String preview;
        final long modified;

        Note(String id, String title, String preview, long modified) {
            this.id = id;
            this.title = title;
            this.preview = preview;
            this.modified = modified;
        }
    }

    private final File dir;

    NoteStore(Context ctx) {
        dir = new File(ctx.getFilesDir(), "notes");
        if (!dir.exists()) {
            dir.mkdirs();
        }
    }

    String newId() {
        return Long.toString(System.currentTimeMillis());
    }

    private File file(String id) {
        // ids are digits only; refuse anything else so a crafted extra can never escape the directory
        for (int i = 0; i < id.length(); i++) {
            if (!Character.isDigit(id.charAt(i))) {
                throw new IllegalArgumentException("bad note id");
            }
        }
        return new File(dir, id + ".txt");
    }

    String read(String id) {
        File f = file(id);
        if (!f.exists()) {
            return "";
        }
        InputStream in = null;
        try {
            in = new FileInputStream(f);
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            byte[] buf = new byte[4096];
            int n;
            while ((n = in.read(buf)) > 0) {
                out.write(buf, 0, n);
            }
            return new String(out.toByteArray(), "UTF-8");
        } catch (IOException e) {
            return "";
        } finally {
            closeQuietly(in);
        }
    }

    /** Writes the text; a blank note is removed instead of saved. */
    void write(String id, String text) {
        File f = file(id);
        if (text.trim().length() == 0) {
            f.delete();
            return;
        }
        OutputStream out = null;
        try {
            out = new FileOutputStream(f);
            out.write(text.getBytes("UTF-8"));
        } catch (IOException ignored) {
            // storage full or gone: nothing sensible to do for a note app
        } finally {
            closeQuietly(out);
        }
    }

    void delete(String id) {
        file(id).delete();
    }

    List<Note> list() {
        File[] files = dir.listFiles();
        List<Note> out = new ArrayList<Note>();
        if (files == null) {
            return out;
        }
        Arrays.sort(files, new Comparator<File>() {
            @Override
            public int compare(File a, File b) {
                long x = a.lastModified(), y = b.lastModified();
                return x < y ? 1 : (x > y ? -1 : 0);
            }
        });
        for (File f : files) {
            String name = f.getName();
            if (!name.endsWith(".txt")) {
                continue;
            }
            String id = name.substring(0, name.length() - 4);
            String text = read(id);
            String title = firstLine(text, 0);
            String preview = firstLine(text, 1);
            out.add(new Note(id, title, preview, f.lastModified()));
        }
        return out;
    }

    /** The n-th non-empty line of the text, trimmed; empty string if there is none. */
    private static String firstLine(String text, int skipNonEmpty) {
        String[] lines = text.split("\n");
        int seen = 0;
        for (String l : lines) {
            String t = l.trim();
            if (t.length() == 0) {
                continue;
            }
            if (seen == skipNonEmpty) {
                return t;
            }
            seen++;
        }
        return "";
    }

    private static void closeQuietly(java.io.Closeable c) {
        if (c != null) {
            try {
                c.close();
            } catch (IOException ignored) {
            }
        }
    }

    /** Newest first helper kept for symmetry with list(): sorts notes by modification time. */
    static void sortNewestFirst(List<Note> notes) {
        Collections.sort(notes, new Comparator<Note>() {
            @Override
            public int compare(Note a, Note b) {
                return a.modified < b.modified ? 1 : (a.modified > b.modified ? -1 : 0);
            }
        });
    }
}
