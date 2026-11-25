package online.zyghosting.manikineko.store;

import android.util.Base64;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.security.KeyFactory;
import java.security.PublicKey;
import java.security.Signature;
import java.security.spec.X509EncodedKeySpec;
import java.util.ArrayList;
import java.util.List;

/** The signed app catalog: catalog.json + catalog.sig (base64 RSA-2048 SHA-256 over the exact catalog.json bytes). */
final class Catalog {

    /** The catalog or its signature did not verify: never trust anything in it. */
    static final class BadSignatureException extends IOException {
        BadSignatureException(String m) { super(m); }
    }

    static final class App {
        String pkg, name, versionName, apk, sha256, summary;
        int versionCode, minSdk, glEs;
        String[] abis = new String[0];
        String[] devices = new String[0];
        long size;
    }

    final List<App> apps = new ArrayList<App>();
    String updated = "";

    static HttpURLConnection open(String url) throws IOException {
        if (!url.startsWith("https://")) throw new IOException("https only");
        HttpURLConnection c = (HttpURLConnection) new URL(url).openConnection();
        c.setConnectTimeout(10000);
        c.setReadTimeout(30000);
        c.setInstanceFollowRedirects(true);
        c.setRequestProperty("User-Agent", "ManikinekoStore/1");
        if (android.os.Build.VERSION.SDK_INT < 21) {                   // TLS 1.2 is off by default before Android 5
            try { ((javax.net.ssl.HttpsURLConnection) c).setSSLSocketFactory(Tls12.create()); } catch (Exception ignored) { }
        }
        return c;
    }

    private static byte[] get(String url, int max) throws IOException {
        HttpURLConnection c = open(url);
        try {
            if (c.getResponseCode() != 200) throw new IOException("HTTP " + c.getResponseCode());
            InputStream in = c.getInputStream();
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            byte[] buf = new byte[8192];
            int n;
            while ((n = in.read(buf)) > 0) {
                out.write(buf, 0, n);
                if (out.size() > max) throw new IOException("too large");
            }
            return out.toByteArray();
        } finally {
            c.disconnect();
        }
    }

    private static String[] strings(JSONArray arr) {
        if (arr == null) return new String[0];
        String[] out = new String[arr.length()];
        for (int i = 0; i < out.length; i++) out[i] = arr.optString(i, "");
        return out;
    }

    static Catalog fetch(String base, String pubKeyB64) throws Exception {
        byte[] json = get(base + "catalog.json", 1 << 20);
        byte[] sig = Base64.decode(new String(get(base + "catalog.sig", 4096), "UTF-8").trim(), Base64.DEFAULT);

        PublicKey key = KeyFactory.getInstance("RSA").generatePublic(
                new X509EncodedKeySpec(Base64.decode(pubKeyB64.trim(), Base64.DEFAULT)));
        Signature s = Signature.getInstance("SHA256withRSA");
        s.initVerify(key);
        s.update(json);
        if (!s.verify(sig)) throw new BadSignatureException("catalog signature mismatch");

        JSONObject root = new JSONObject(new String(json, "UTF-8"));
        Catalog cat = new Catalog();
        cat.updated = root.optString("updated", "");
        JSONArray arr = root.getJSONArray("apps");
        for (int i = 0; i < arr.length(); i++) {
            JSONObject o = arr.getJSONObject(i);
            App a = new App();
            a.pkg = o.getString("package");
            a.name = o.getString("name");
            a.versionName = o.optString("versionName", "");
            a.versionCode = o.getInt("versionCode");
            a.minSdk = o.optInt("minSdk", 1);
            a.apk = o.getString("apk");
            a.sha256 = o.getString("sha256").toLowerCase();
            a.size = o.optLong("size", -1);
            a.summary = o.optString("summary", "");
            a.glEs = o.optInt("glEs", 0);
            a.abis = strings(o.optJSONArray("abis"));
            a.devices = strings(o.optJSONArray("devices"));
            // the APK path comes from a signed catalog but stay strict anyway: relative, inside apk/, no traversal
            if (!a.apk.startsWith("apk/") || a.apk.contains("..") || a.apk.indexOf(':') >= 0) continue;
            cat.apps.add(a);
        }
        return cat;
    }
}
