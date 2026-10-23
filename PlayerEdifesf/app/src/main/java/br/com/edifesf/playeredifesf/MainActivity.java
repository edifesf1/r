
package br.com.edifesf.playeredifesf;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.widget.Toast;

public class MainActivity extends Activity {

    private static final String SITE_URL =
            "https://edifesf.github.io/r/";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        try {
            Intent intent = new Intent(
                    Intent.ACTION_VIEW,
                    Uri.parse(SITE_URL)
            );

            intent.setPackage("com.amazon.cloud9");
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);

            startActivity(intent);
            finish();

        } catch (Exception e) {
            Toast.makeText(
                    this,
                    "Não foi possível abrir o Silk. Verifique se está instalado.",
                    Toast.LENGTH_LONG
            ).show();
            finish();
        }
    }
}
