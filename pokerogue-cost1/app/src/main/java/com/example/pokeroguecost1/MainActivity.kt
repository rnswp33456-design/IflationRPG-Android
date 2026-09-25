package com.example.pokeroguecost1

import android.annotation.SuppressLint
import android.os.Bundle
import android.webkit.CookieManager
import android.webkit.WebChromeClient
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {
    private lateinit var webView: WebView

    private val costOneScript = """
        (function installPokeRogueCostOne() {
          if (window.__prCostOneTimer) return;

          function patchScene(scene) {
            try {
              var gameData = scene && scene.gameData;
              if (gameData && typeof gameData.getSpeciesStarterValue === 'function') {
                if (!gameData.__costOneOriginal) {
                  gameData.__costOneOriginal = gameData.getSpeciesStarterValue.bind(gameData);
                }
                gameData.getSpeciesStarterValue = function() { return 1; };
                window.__prCostOnePatched = true;
              }
            } catch (e) {}
          }

          function patch() {
            try {
              var PhaserObj = window.Phaser;
              var pools = PhaserObj && PhaserObj.Display && PhaserObj.Display.Canvas &&
                          PhaserObj.Display.Canvas.CanvasPool && PhaserObj.Display.Canvas.CanvasPool.pool;
              if (pools && pools.length) {
                for (var i = 0; i < pools.length; i++) {
                  patchScene(pools[i] && pools[i].parent && pools[i].parent.scene);
                }
              }

              var canvases = document.querySelectorAll('canvas');
              for (var j = 0; j < canvases.length; j++) {
                patchScene(canvases[j] && canvases[j].parent && canvases[j].parent.scene);
              }
            } catch (e) {}
          }

          patch();
          window.__prCostOneTimer = setInterval(patch, 500);
        })();
    """.trimIndent()

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        webView = findViewById(R.id.webView)
        webView.settings.javaScriptEnabled = true
        webView.settings.domStorageEnabled = true
        webView.settings.mediaPlaybackRequiresUserGesture = false
        webView.settings.useWideViewPort = true
        webView.settings.loadWithOverviewMode = true
        webView.settings.userAgentString = webView.settings.userAgentString + " PokeRogueCost1/1.0"

        CookieManager.getInstance().setAcceptCookie(true)
        CookieManager.getInstance().setAcceptThirdPartyCookies(webView, true)

        webView.webChromeClient = WebChromeClient()
        webView.webViewClient = object : WebViewClient() {
            override fun onPageFinished(view: WebView, url: String) {
                super.onPageFinished(view, url)
                if (url.startsWith("https://pokerogue.net")) {
                    view.evaluateJavascript(costOneScript, null)
                }
            }
        }

        if (savedInstanceState == null) {
            webView.loadUrl("https://pokerogue.net/")
        } else {
            webView.restoreState(savedInstanceState)
        }
    }

    override fun onSaveInstanceState(outState: Bundle) {
        webView.saveState(outState)
        super.onSaveInstanceState(outState)
    }

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        if (webView.canGoBack()) webView.goBack() else super.onBackPressed()
    }

    override fun onPause() {
        CookieManager.getInstance().flush()
        webView.onPause()
        super.onPause()
    }

    override fun onResume() {
        super.onResume()
        webView.onResume()
        webView.evaluateJavascript(costOneScript, null)
    }
}
