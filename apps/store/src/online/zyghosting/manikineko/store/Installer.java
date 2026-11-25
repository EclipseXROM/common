package online.zyghosting.manikineko.store;

import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.IntentSender;
import android.content.pm.PackageManager;

import java.io.InputStream;
import java.io.OutputStream;
import java.lang.reflect.Constructor;
import java.lang.reflect.Method;
import java.security.MessageDigest;

/**
 * Downloads an APK straight into a PackageInstaller session (no file on disk), hashing it on the way, and commits ONLY if the
 * SHA-256 matches the signed catalog. PackageInstaller is API 21+, the build compiles against API 19, so it is called by
 * reflection. Because this app is platform-signed (INSTALL_PACKAGES), the commit is silent.
 */
final class Installer {

    static final String ACTION_RESULT = "online.zyghosting.manikineko.store.INSTALL_RESULT";

    interface Progress { void onProgress(int percent); }

    /** Thrown when the downloaded bytes do not match the catalog. */
    static final class HashMismatchException extends Exception {
        HashMismatchException() { super("sha256 mismatch"); }
    }

    /**
     * Android before 5.0 has no PackageInstaller. Download the APK into the app's private files directory (world-readable so the system
     * installer can open it), hash it while writing and refuse to hand it over unless the SHA-256 matches the signed catalog.
     */
    @SuppressWarnings("deprecation")
    static java.io.File downloadVerified(Context ctx, String base, Catalog.App app, Progress progress) throws Exception {
        String name = app.pkg + ".apk";
        MessageDigest md = MessageDigest.getInstance("SHA-256");
        java.net.HttpURLConnection c = Catalog.open(base + app.apk);
        OutputStream out = ctx.openFileOutput(name, Context.MODE_WORLD_READABLE);
        try {
            if (c.getResponseCode() != 200) throw new java.io.IOException("HTTP " + c.getResponseCode());
            long total = c.getContentLength() > 0 ? c.getContentLength() : app.size;
            InputStream in = c.getInputStream();
            byte[] buf = new byte[16384];
            long done = 0;
            int n, last = -1;
            while ((n = in.read(buf)) > 0) {
                out.write(buf, 0, n);
                md.update(buf, 0, n);
                done += n;
                int p = total > 0 ? (int) (done * 100 / total) : 0;
                if (p != last && progress != null) { last = p; progress.onProgress(p); }
            }
        } finally {
            out.close();
            c.disconnect();
        }
        StringBuilder hex = new StringBuilder();
        for (byte b : md.digest()) hex.append(String.format("%02x", b & 0xff));
        java.io.File f = ctx.getFileStreamPath(name);
        if (!hex.toString().equals(app.sha256)) { f.delete(); throw new HashMismatchException(); }
        return f;
    }

    static void install(Context ctx, String base, Catalog.App app, Progress progress) throws Exception {
        PackageManager pm = ctx.getPackageManager();
        Object pi = PackageManager.class.getMethod("getPackageInstaller").invoke(pm);
        Class<?> installerCls = Class.forName("android.content.pm.PackageInstaller");
        Class<?> paramsCls = Class.forName("android.content.pm.PackageInstaller$SessionParams");
        Class<?> sessionCls = Class.forName("android.content.pm.PackageInstaller$Session");

        Constructor<?> pc = paramsCls.getConstructor(int.class);
        Object params = pc.newInstance(1);                                   // MODE_FULL_INSTALL
        paramsCls.getMethod("setAppPackageName", String.class).invoke(params, app.pkg);
        if (app.size > 0) paramsCls.getMethod("setSize", long.class).invoke(params, app.size);

        int id = (Integer) installerCls.getMethod("createSession", paramsCls).invoke(pi, params);
        Object session = installerCls.getMethod("openSession", int.class).invoke(pi, id);
        boolean committed = false;
        try {
            Method openWrite = sessionCls.getMethod("openWrite", String.class, long.class, long.class);
            OutputStream out = (OutputStream) openWrite.invoke(session, "base.apk", 0L, app.size > 0 ? app.size : -1L);
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            java.net.HttpURLConnection c = Catalog.open(base + app.apk);
            try {
                if (c.getResponseCode() != 200) throw new java.io.IOException("HTTP " + c.getResponseCode());
                long total = c.getContentLength() > 0 ? c.getContentLength() : app.size;
                InputStream in = c.getInputStream();
                byte[] buf = new byte[16384];
                long done = 0;
                int n, last = -1;
                while ((n = in.read(buf)) > 0) {
                    out.write(buf, 0, n);
                    md.update(buf, 0, n);
                    done += n;
                    int p = total > 0 ? (int) (done * 100 / total) : 0;
                    if (p != last && progress != null) { last = p; progress.onProgress(p); }
                }
            } finally {
                c.disconnect();
            }
            sessionCls.getMethod("fsync", OutputStream.class).invoke(session, out);
            out.close();

            StringBuilder hex = new StringBuilder();
            for (byte b : md.digest()) hex.append(String.format("%02x", b & 0xff));
            if (!hex.toString().equals(app.sha256)) throw new HashMismatchException();

            Intent result = new Intent(ACTION_RESULT).setPackage(ctx.getPackageName());
            IntentSender sender = PendingIntent.getBroadcast(ctx, id, result, PendingIntent.FLAG_UPDATE_CURRENT).getIntentSender();
            sessionCls.getMethod("commit", IntentSender.class).invoke(session, sender);
            committed = true;
        } finally {
            if (!committed) {
                try { sessionCls.getMethod("abandon").invoke(session); } catch (Exception ignored) { }
            }
            try { sessionCls.getMethod("close").invoke(session); } catch (Exception ignored) { }
        }
    }
}
