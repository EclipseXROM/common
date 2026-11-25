package online.zyghosting.manikineko.store;

import java.io.IOException;
import java.net.InetAddress;
import java.net.Socket;
import java.util.ArrayList;
import java.util.List;

import javax.net.ssl.SSLContext;
import javax.net.ssl.SSLSocket;
import javax.net.ssl.SSLSocketFactory;

/**
 * Android 4.1-4.4 (API 16-20) can speak TLS 1.1/1.2 but leaves them OFF by default, while the store server accepts TLS 1.2 or newer only.
 * This factory wraps the platform one and switches the newest protocols on. Certificate and host name checks stay the platform defaults.
 */
final class Tls12 extends SSLSocketFactory {

    private static final String[] WANTED = { "TLSv1.2", "TLSv1.1", "TLSv1" };
    private final SSLSocketFactory base;

    static SSLSocketFactory create() throws Exception {
        SSLContext ctx = SSLContext.getInstance("TLS");
        ctx.init(null, null, null);
        return new Tls12(ctx.getSocketFactory());
    }

    private Tls12(SSLSocketFactory base) { this.base = base; }

    private Socket enable(Socket s) {
        if (s instanceof SSLSocket) {
            SSLSocket ss = (SSLSocket) s;
            List<String> ok = new ArrayList<String>();
            List<String> supported = java.util.Arrays.asList(ss.getSupportedProtocols());
            for (String p : WANTED) if (supported.contains(p)) ok.add(p);
            if (!ok.isEmpty()) ss.setEnabledProtocols(ok.toArray(new String[0]));
        }
        return s;
    }

    @Override public String[] getDefaultCipherSuites() { return base.getDefaultCipherSuites(); }
    @Override public String[] getSupportedCipherSuites() { return base.getSupportedCipherSuites(); }
    @Override public Socket createSocket(Socket s, String host, int port, boolean autoClose) throws IOException { return enable(base.createSocket(s, host, port, autoClose)); }
    @Override public Socket createSocket(String host, int port) throws IOException { return enable(base.createSocket(host, port)); }
    @Override public Socket createSocket(String host, int port, InetAddress la, int lp) throws IOException { return enable(base.createSocket(host, port, la, lp)); }
    @Override public Socket createSocket(InetAddress host, int port) throws IOException { return enable(base.createSocket(host, port)); }
    @Override public Socket createSocket(InetAddress a, int port, InetAddress la, int lp) throws IOException { return enable(base.createSocket(a, port, la, lp)); }
}
