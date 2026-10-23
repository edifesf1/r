package com.edifesf1.novoapp;

import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.InputDevice;
import android.view.KeyEvent;
import android.view.MotionEvent;
import android.view.View;
import android.view.WindowManager;
import android.webkit.CookieManager;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.TextView;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

public class MainActivity extends Activity {
    private static final String LINK_URL = "https://raw.githubusercontent.com/edifesf1/r/refs/heads/main/link.txt";
    private WebView webView;
    private TextView tvStatus;
    private final Handler handler = new Handler(Looper.getMainLooper());

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        setContentView(R.layout.activity_main);
        tvStatus = findViewById(R.id.tvStatus);
        webView = findViewById(R.id.webView);
        configurarWebView();
        carregarLink();
    }

    private void configurarWebView() {
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setMediaPlaybackRequiresUserGesture(false);
        settings.setLoadsImagesAutomatically(true);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_COMPATIBILITY_MODE);
        CookieManager.getInstance().setAcceptCookie(true);
        CookieManager.getInstance().setAcceptThirdPartyCookies(webView, true);
        webView.setFocusable(true);
        webView.setFocusableInTouchMode(true);
        webView.setOnTouchListener((v, e) -> { v.performClick(); return false; });
        webView.setOnHoverListener((v, e) -> { webView.onHoverEvent(e); return false; });
        webView.setWebChromeClient(new WebChromeClient());
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest r) { return false; }
            @Override
            public void onPageFinished(WebView v, String u) { tvStatus.setVisibility(View.GONE); }
        });
    }

    @Override
    public boolean onGenericMotionEvent(MotionEvent e) {
        if (webView != null) {
            int s = e.getSource();
            if ((s & InputDevice.SOURCE_MOUSE) != 0 ||
                (s & InputDevice.SOURCE_JOYSTICK) != 0 ||
                (s & InputDevice.SOURCE_DPAD) != 0) {
                webView.onGenericMotionEvent(e);
            }
        }
        return super.onGenericMotionEvent(e);
    }

    private void carregarLink() {
        tvStatus.setText("Carregando...");
        new Thread(() -> {
            String end = null;
            try {
                HttpURLConnection c = (HttpURLConnection) new URL(LINK_URL).openConnection();
                c.setConnectTimeout(15000); c.setReadTimeout(15000); c.setRequestMethod("GET");
                if (c.getResponseCode() == 200) {
                    BufferedReader r = new BufferedReader(new InputStreamReader(c.getInputStream(), StandardCharsets.UTF_8));
                    end = r.readLine().trim().replace("\uFEFF", "");
                    r.close();
                }
                c.disconnect();
            } catch (Exception x) {
                handler.post(() -> tvStatus.setText("Erro\nPressione VOLTAR para tentar"));
                return;
            }
            String url = end;
            handler.post(() -> {
                if (url != null && url.startsWith("http")) webView.loadUrl(url);
                else tvStatus.setText("Link inválido\nPressione VOLTAR para tentar");
            });
        }).start();
    }

    @Override
    public boolean dispatchKeyEvent(KeyEvent e) {
        if (e.getAction() == KeyEvent.ACTION_UP && e.getKeyCode() == KeyEvent.KEYCODE_BACK) {
            if (tvStatus.getVisibility() == View.VISIBLE) { carregarLink(); return true; }
            if (webView.canGoBack()) { webView.goBack(); return true; }
        }
        return super.dispatchKeyEvent(e);
    }

    @Override
    protected void onDestroy() { if (webView != null) webView.destroy(); super.onDestroy(); }
}

