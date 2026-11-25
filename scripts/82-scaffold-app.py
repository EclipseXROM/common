"""Scaffold a Manikineko store app: manifest, dark palette/theme, EN+LT app_name, icon from the glyph set.
  python -I scripts/82-scaffold-app.py <dir-name> <label-en> <label-lt> <glyph> [PERMISSION ...]
  e.g. python -I scripts/82-scaffold-app.py torch Torch Žibintuvėlis torch CAMERA FLASHLIGHT
Creates apps/<dir-name>/ with package online.zyghosting.manikineko.<dir-name> and MainActivity as the only launcher activity
(layouts/strings/code are then written by hand). Never overwrites an existing app dir."""
import os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
name, en, lt, glyph, perms = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5:]
base = os.path.join(ROOT, "apps", name)
if os.path.exists(base): raise SystemExit("exists: " + base)
pkg = "online.zyghosting.manikineko." + name
for d in ("res/values", "res/values-lt", "res/layout", "src/" + pkg.replace(".", "/")):
    os.makedirs(os.path.join(base, d))

def w(rel, text):
    with open(os.path.join(base, rel), "w", encoding="utf-8", newline="\n") as f: f.write(text)

uses = "".join('    <uses-permission android:name="android.permission.%s" />\n' % p for p in perms)
w("AndroidManifest.xml", f'''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="{pkg}"
    android:versionCode="1"
    android:versionName="1.0">

    <uses-sdk android:minSdkVersion="19" android:targetSdkVersion="19" />
{uses}
    <application
        android:label="@string/app_name"
        android:icon="@drawable/ic_launcher"
        android:theme="@style/ManikinekoTheme"
        android:allowBackup="false"
        android:hardwareAccelerated="true">
        <activity
            android:name=".MainActivity"
            android:label="@string/app_name"
            android:configChanges="keyboardHidden|orientation|screenSize">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
''')
w("res/values/colors.xml", '''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="mk_bg">#FF0B0F14</color>
    <color name="mk_surface">#FF141A22</color>
    <color name="mk_surface_hi">#FF1B2430</color>
    <color name="mk_accent">#FF4FA3E3</color>
    <color name="mk_text">#FFE8EEF5</color>
    <color name="mk_text_dim">#FF7C8A9A</color>
    <color name="mk_danger">#FFE35F5F</color>
</resources>
''')
w("res/values/styles.xml", '''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="ManikinekoTheme" parent="@android:style/Theme.Holo.NoActionBar">
        <item name="android:windowBackground">@color/mk_bg</item>
        <item name="android:colorBackground">@color/mk_bg</item>
        <item name="android:windowNoTitle">true</item>
        <item name="android:windowContentOverlay">@null</item>
    </style>
</resources>
''')
w("res/values/strings.xml", f'<?xml version="1.0" encoding="utf-8"?>\n<resources>\n    <string name="app_name">{en}</string>\n</resources>\n')
w("res/values-lt/strings.xml", f'<?xml version="1.0" encoding="utf-8"?>\n<resources>\n    <string name="app_name">{lt}</string>\n</resources>\n')
subprocess.run([sys.executable, "-I", os.path.join(ROOT, "scripts", "71-app-icons.py"), os.path.join(base, "res"), glyph], check=True)
print("scaffolded", base, "package", pkg)
