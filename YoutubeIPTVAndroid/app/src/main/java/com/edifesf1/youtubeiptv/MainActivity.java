package com.edifesf1.youtubeiptv;

import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.KeyEvent;
import android.view.View;
import android.view.WindowManager;
import android.webkit.CookieManager;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;
import android.widget.TextView;
import android.graphics.Color;
import android.graphics.Typeface;
import android.view.Gravity;
import android.view.accessibility.AccessibilityEvent;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

public class MainActivity extends Activity {
    private static final String LINK_TXT = "https://raw.githubusercontent.com/edifesf1/r/refs/heads/main/link.txt";
    private WebView webView;
    private TextView status;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private boolean pageLoaded = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        enterImmersiveMode();
        buildScreen();
        loadAddressFromTxt();
    }

    private void buildScreen() {
        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.BLACK);

        webView = new WebView(this);
        webView.setBackgroundColor(Color.BLACK);
        webView.setFocusable(true);
        webView.setFocusableInTouchMode(true);

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setMediaPlaybackRequiresUserGesture(false);
        settings.setSupportMultipleWindows(false);
        settings.setJavaScriptCanOpenWindowsAutomatically(false);
        settings.setLoadsImagesAutomatically(true);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_COMPATIBILITY_MODE);
        settings.setUserAgentString(settings.getUserAgentString() + " YoutubeIPTVAndroid/1.0");
        CookieManager.getInstance().setAcceptCookie(true);
        CookieManager.getInstance().setAcceptThirdPartyCookies(webView, true);

        webView.setWebChromeClient(new WebChromeClient());
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                // Keep website navigation inside the app's embedded browser.
                return false;
            }
            @Override
            public void onPageFinished(WebView view, String url) {
                pageLoaded = true;
                status.setVisibility(View.GONE);
                view.requestFocus(View.FOCUS_DOWN);
            }
            @Override
            public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                if (request.isForMainFrame()) showStatus("Não foi possível abrir o site. Verifique a internet e pressione OK para tentar novamente.");
            }
        });

        root.addView(webView, new FrameLayout.LayoutParams(FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.MATCH_PARENT));
        status = new TextView(this);
        status.setText("Edifesf\n\nSeja Bem Vindo");
        status.setTextColor(Color.WHITE);
        status.setTextSize(22);
        status.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        status.setGravity(Gravity.CENTER);
        status.setFocusable(true);
        status.setFocusableInTouchMode(true);
        status.setBackgroundColor(Color.BLACK);
        root.addView(status, new FrameLayout.LayoutParams(FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.MATCH_PARENT));
        setContentView(root);
        status.requestFocus();
    }

    private void loadAddressFromTxt() {
        showStatus("Edifesf\n\nSeja Bem Vindo");
        new Thread(() -> {
            HttpURLConnection connection = null;
            try {
                URL url = new URL(LINK_TXT);
                connection = (HttpURLConnection) url.openConnection();
                connection.setConnectTimeout(12000);
                connection.setReadTimeout(12000);
                connection.setRequestMethod("GET");
                connection.setUseCaches(false);
                connection.setRequestProperty("Cache-Control", "no-cache");
                connection.setRequestProperty("User-Agent", "YoutubeIPTVAndroid/1.0");
                int code = connection.getResponseCode();
                if (code < 200 || code >= 300) throw new Exception("HTTP " + code);
                StringBuilder body = new StringBuilder();
                try (InputStream in = connection.getInputStream();
                     BufferedReader reader = new BufferedReader(new InputStreamReader(in, StandardCharsets.UTF_8))) {
                    String line;
                    while ((line = reader.readLine()) != null) body.append(line.trim());
                }
                String address = body.toString().replace("\uFEFF", "").trim();
                if (!(address.startsWith("https://") || address.startsWith("http://"))) {
                    throw new Exception("O link.txt não contém um endereço HTTP/HTTPS válido.");
                }
                final String finalAddress = address;
                handler.post(() -> {
                    showStatus("Edifesf\n\nSeja Bem Vindo");
                    webView.loadUrl(finalAddress);
                });
            } catch (Exception e) {
                handler.post(() -> showStatus("Não consegui ler o link.txt.\n\nVerifique a conexão com a internet.\n\nPressione OK para tentar novamente."));
            } finally {
                if (connection != null) connection.disconnect();
            }
        }).start();
    }

    private void showStatus(String message) {
        if (status != null) {
            status.setText(message);
            status.setVisibility(View.VISIBLE);
            status.requestFocus();
        }
    }

    private void enterImmersiveMode() {
        getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                | View.SYSTEM_UI_FLAG_FULLSCREEN
                | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                | View.SYSTEM_UI_FLAG_LAYOUT_STABLE
        );
    }

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) enterImmersiveMode();
    }

    @Override
    public boolean dispatchKeyEvent(KeyEvent event) {
        if (event.getAction() == KeyEvent.ACTION_UP && event.getKeyCode() == KeyEvent.KEYCODE_DPAD_CENTER && status != null && status.getVisibility() == View.VISIBLE) {
            loadAddressFromTxt();
            return true;
        }
        if (event.getAction() == KeyEvent.ACTION_UP && (event.getKeyCode() == KeyEvent.KEYCODE_BACK || event.getKeyCode() == KeyEvent.KEYCODE_ESCAPE)) {
            if (webView != null && webView.canGoBack()) {
                webView.goBack();
                return true;
            }
        }
        return super.dispatchKeyEvent(event);
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) webView.goBack();
        else super.onBackPressed();
    }

    @Override
    protected void onDestroy() {
        if (webView != null) {
            webView.stopLoading();
            webView.destroy();
            webView = null;
        }
        super.onDestroy();
    }
}
