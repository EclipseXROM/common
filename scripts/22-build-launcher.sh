#!/bin/sh
# Build the Manikineko launcher APK with the plain SDK toolchain (no Gradle).
#   aapt2 compile -> aapt2 link -> javac -> d8 -> zipalign -> apksigner
# Usage: sh scripts/22-build-launcher.sh
set -eu

ROOT="${MK_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
BT="$ROOT/tools/sdk/build-tools/30.0.3"
PLATFORM="$ROOT/tools/sdk/platforms/android-19/android.jar"
JAVA_HOME="$ROOT/tools/jdk-17.0.21.1+2"
export JAVA_HOME

SRC="$ROOT/launcher"
# javac @argfiles and d8 cannot handle spaces in paths, and the project path has
# one ("manikineko phone"), so all intermediate output goes to a space-free dir.
OUT="${MK_BUILD:-C:/mkbuild}/launcher"
DIST="${MK_DIST:-$ROOT/build}"
MIN="${MK_MIN_SDK:-19}"            # e.g. MK_MIN_SDK=16 for the Xperia J (Android 4.1) builds
KS="${MK_KS:-${MK_BUILD:-C:/mkbuild}/manikineko.keystore}"
KS_PASS="${MK_KS_PASS:-manikineko}"   # throwaway dev-key default; override for real keys
KS_ALIAS="manikineko"

rm -rf "$OUT"
mkdir -p "$OUT/res" "$OUT/gen" "$OUT/classes" "$OUT/dex" "$DIST"
sed "s/android:minSdkVersion=\"[0-9]*\"/android:minSdkVersion=\"$MIN\"/" "$SRC/AndroidManifest.xml" > "$OUT/AndroidManifest.xml"

echo "== 1/7 aapt2 compile =="
"$BT/aapt2.exe" compile --dir "$SRC/res" -o "$OUT/res/resources.zip"

echo "== 2/7 aapt2 link =="
"$BT/aapt2.exe" link \
  -o "$OUT/base.apk" \
  -I "$PLATFORM" \
  --manifest "$OUT/AndroidManifest.xml" \
  --java "$OUT/gen" \
  --min-sdk-version $MIN \
  --target-sdk-version 19 \
  --version-code 4 \
  --version-name 1.3 \
  "$OUT/res/resources.zip"

echo "== 3/7 javac =="
# javac reads @argfiles by splitting on whitespace, so the sources must live at
# space-free paths too: copy them next to the generated R.java.
rm -rf "$OUT/src"
cp -r "$SRC/src" "$OUT/src"
find "$OUT/src" "$OUT/gen" -name '*.java' > "$OUT/sources.txt"
JOUT="$("$JAVA_HOME/bin/javac.exe" -source 8 -target 8 -encoding UTF-8 \
  -bootclasspath "$PLATFORM" \
  -classpath "$PLATFORM" \
  -d "$OUT/classes" \
  @"$OUT/sources.txt" 2>&1 || true)"
echo "$JOUT" | grep -v 'bootstrap class path' || true
if echo "$JOUT" | grep -q 'error:'; then echo "FATAL: javac reported errors, not building an APK from stale classes"; exit 1; fi

echo "== 4/7 d8 =="
# d8.bat silently produces nothing under this shell, so invoke the jar directly.
find "$OUT/classes" -name '*.class' > "$OUT/classes.txt"
"$JAVA_HOME/bin/java.exe" -cp "$BT/lib/d8.jar" com.android.tools.r8.D8 \
  --min-api $MIN \
  --lib "$PLATFORM" \
  --output "$OUT/dex" \
  @"$OUT/classes.txt"
test -f "$OUT/dex/classes.dex" || { echo "FATAL: d8 produced no classes.dex"; exit 1; }

echo "== 5/7 add classes.dex =="
cp "$OUT/base.apk" "$OUT/unsigned.apk"
(cd "$OUT/dex" && "$JAVA_HOME/bin/jar.exe" uf "$OUT/unsigned.apk" classes.dex)

echo "== 6/7 zipalign =="
"$BT/zipalign.exe" -f -p 4 "$OUT/unsigned.apk" "$OUT/aligned.apk"

echo "== 7/7 apksigner =="
if [ ! -f "$KS" ]; then
  "$JAVA_HOME/bin/keytool.exe" -genkeypair -v \
    -keystore "$KS" -storepass "$KS_PASS" -keypass "$KS_PASS" \
    -alias "$KS_ALIAS" -keyalg RSA -keysize 2048 -validity 10000 \
    -dname "CN=Manikineko, OU=Phone, O=ZygHosting, L=Marijampole, C=LT" >/dev/null 2>&1
  echo "keystore created: $KS"
fi

"$BT/apksigner.bat" sign \
  --ks "$KS" --ks-pass "pass:$KS_PASS" --key-pass "pass:$KS_PASS" \
  --ks-key-alias "$KS_ALIAS" \
  --min-sdk-version $MIN \
  --out "$OUT/manikineko-home.apk" "$OUT/aligned.apk"

"$BT/apksigner.bat" verify --min-sdk-version $MIN "$OUT/manikineko-home.apk"

cp -f "$OUT/manikineko-home.apk" "$DIST/manikineko-home.apk"

echo "== result =="
ls -l "$DIST/manikineko-home.apk"
