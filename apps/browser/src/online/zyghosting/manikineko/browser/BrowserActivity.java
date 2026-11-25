package online.zyghosting.manikineko.browser;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.graphics.Bitmap;
import android.net.Uri;
import android.os.Bundle;
import android.view.KeyEvent;
import android.view.View;
import android.view.inputmethod.EditorInfo;
import android.view.inputmethod.InputMethodManager;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import java.net.URLEncoder;

/** Single-tab browser: address/search bar, back/forward, reload/stop, progress. Plain WebView, no accounts, no sync. */
public class BrowserActivity extends Activity {

    private static final String SEARCH = "https://duckduckgo.com/?q=";
    private static final String START = "https://duckduckgo.com/";

    private WebView web;
    private EditText url;
    private ProgressBar progress;
    private Button reload;
    private boolean loading;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_browser);
        web = (WebView) findViewById(R.id.web);
        url = (EditText) findViewById(R.id.url);
        progress = (ProgressBar) findViewById(R.id.progress);
        reload = (Button) findViewById(R.id.btn_reload);

        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setBuiltInZoomControls(true);
        s.setDisplayZoomControls(false);
        s.setLoadWithOverviewMode(true);
        s.setUseWideViewPort(true);
        s.setSaveFormData(false);
        s.setAllowFileAccess(false);
        s.setGeolocationEnabled(false);

        web.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView v, String u) {
                Uri uri = Uri.parse(u);
                String scheme = uri.getScheme();
                if ("http".equals(scheme) || "https".equals(scheme)) return false;
                if ("tel".equals(scheme) || "mailto".equals(scheme) || "sms".equals(scheme)) {
                    try {
                        startActivity(new Intent(Intent.ACTION_VIEW, uri));
                    } catch (Exception e) {
                        Toast.makeText(BrowserActivity.this, R.string.no_app, Toast.LENGTH_SHORT).show();
                    }
                }
                return true;
            }

            @Override
            public void onPageStarted(WebView v, String u, Bitmap icon) {
                setLoading(true);
                if (!url.hasFocus()) url.setText(u);
            }

            @Override
            public void onPageFinished(WebView v, String u) {
                setLoading(false);
                if (!url.hasFocus()) url.setText(u);
                updateNav();
            }
        });
        web.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onProgressChanged(WebView v, int p) {
                progress.setProgress(p);
            }
        });

        url.setOnEditorActionListener(new TextView.OnEditorActionListener() {
            @Override
            public boolean onEditorAction(TextView v, int actionId, KeyEvent e) {
                if (actionId == EditorInfo.IME_ACTION_GO || (e != null && e.getKeyCode() == KeyEvent.KEYCODE_ENTER)) {
                    go(url.getText().toString());
                    return true;
                }
                return false;
            }
        });
        reload.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                if (loading) web.stopLoading(); else web.reload();
            }
        });
        findViewById(R.id.btn_back).setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                if (web.canGoBack()) web.goBack();
            }
        });
        findViewById(R.id.btn_forward).setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                if (web.canGoForward()) web.goForward();
            }
        });

        if (savedInstanceState != null) {
            web.restoreState(savedInstanceState);
        } else {
            Uri data = getIntent().getData();
            go(data != null ? data.toString() : START);
        }
        updateNav();
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        Uri data = intent.getData();
        if (data != null) go(data.toString());
    }

    @Override
    protected void onSaveInstanceState(Bundle out) {
        super.onSaveInstanceState(out);
        web.saveState(out);
    }

    @Override
    protected void onPause() {
        super.onPause();
        web.onPause();
    }

    @Override
    protected void onResume() {
        super.onResume();
        web.onResume();
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        web.destroy();
    }

    @Override
    public void onBackPressed() {
        if (web.canGoBack()) web.goBack(); else super.onBackPressed();
    }

    private void setLoading(boolean on) {
        loading = on;
        progress.setVisibility(on ? View.VISIBLE : View.GONE);
        reload.setText(on ? R.string.stop : R.string.reload);
    }

    private void updateNav() {
        findViewById(R.id.btn_back).setEnabled(web.canGoBack());
        findViewById(R.id.btn_forward).setEnabled(web.canGoForward());
    }

    /** Address-bar input: full URL, host-looking text becomes https://, anything else is a search. */
    private void go(String input) {
        String t = input == null ? "" : input.trim();
        if (t.length() == 0) return;
        String target;
        if (t.startsWith("http://") || t.startsWith("https://")) {
            target = t;
        } else if (t.indexOf(' ') < 0 && t.indexOf('.') > 0) {
            target = "https://" + t;
        } else {
            try {
                target = SEARCH + URLEncoder.encode(t, "UTF-8");
            } catch (Exception e) {
                return;
            }
        }
        web.loadUrl(target);
        url.clearFocus();
        InputMethodManager imm = (InputMethodManager) getSystemService(Context.INPUT_METHOD_SERVICE);
        imm.hideSoftInputFromWindow(url.getWindowToken(), 0);
    }
}
