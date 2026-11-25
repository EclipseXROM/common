#!/bin/sh
# Build one Manikineko app with the plain SDK toolchain (same pipeline as 22-build-launcher.sh).
#   sh scripts/70-build-app.sh <app-dir> <out-name> <version-code> <version-name>
#   e.g. sh scripts/70-build-app.sh apps/notes ManikinekoNotes 1 1.0   ->  build/ManikinekoNotes.apk
set -eu
ROOT="${MK_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
APP="${1:?app dir}"; NAME="${2:?out name}"; VCODE="${3:-1}"; VNAME="${4:-1.0}"
BT="$ROOT/tools/sdk/build-tools/30.0.3"
PLATFORM="$ROOT/tools/sdk/platforms/android-19/android.jar"
JAVA_HOME="$ROOT/tools/jdk-17.0.21.1+2"; export JAVA_HOME
SRC="$ROOT/$APP"
OUT="${MK_BUILD:-C:/mkbuild}/$NAME"          # space-free scratch dir (javac/d8 argfiles cannot take spaces)
DIST="${MK_DIST:-$ROOT/build}"
MIN="${MK_MIN_SDK:-19}"            # e.g. MK_MIN_SDK=16 for the Xperia J (Android 4.1) builds
KS="${MK_KS:-C:/mkbuild/manikineko.keystore}"; KS_PASS="${MK_KS_PASS:-manikineko}"; KS_ALIAS="${MK_KS_ALIAS:-manikineko}"   # MK_KS* = sign store apps with the separate (non-platform) key
[ -f "$KS" ] || { echo "FATAL: keystore $KS missing (run scripts/22-build-launcher.sh once)"; exit 1; }

rm -rf "$OUT"; mkdir -p "$OUT/res" "$OUT/gen" "$OUT/classes" "$OUT/dex" "$DIST"
sed "s/android:minSdkVersion=\"[0-9]*\"/android:minSdkVersion=\"$MIN\"/" "$SRC/AndroidManifest.xml" > "$OUT/AndroidManifest.xml"
echo "== $NAME: aapt2 compile/link =="
"$BT/aapt2.exe" compile --dir "$SRC/res" -o "$OUT/res/resources.zip"
"$BT/aapt2.exe" link -o "$OUT/base.apk" -I "$PLATFORM" --manifest "$OUT/AndroidManifest.xml" \
  --java "$OUT/gen" --min-sdk-version $MIN --target-sdk-version 19 \
  --version-code "$VCODE" --version-name "$VNAME" "$OUT/res/resources.zip"
echo "== javac / d8 =="
rm -rf "$OUT/src"; cp -r "$SRC/src" "$OUT/src"
find "$OUT/src" "$OUT/gen" -name '*.java' > "$OUT/sources.txt"
JOUT="$("$JAVA_HOME/bin/javac.exe" -source 8 -target 8 -encoding UTF-8 -Xlint:-options \
  -bootclasspath "$PLATFORM" -classpath "$PLATFORM" -d "$OUT/classes" @"$OUT/sources.txt" 2>&1 || true)"
echo "$JOUT" | grep -v 'bootstrap class path' || true
if echo "$JOUT" | grep -q 'error:'; then echo "FATAL: javac reported errors, not building an APK from stale classes"; exit 1; fi
find "$OUT/classes" -name '*.class' > "$OUT/classes.txt"
"$JAVA_HOME/bin/java.exe" -cp "$BT/lib/d8.jar" com.android.tools.r8.D8 --min-api $MIN --lib "$PLATFORM" --output "$OUT/dex" @"$OUT/classes.txt"
test -f "$OUT/dex/classes.dex" || { echo "FATAL: no classes.dex"; exit 1; }
cp "$OUT/base.apk" "$OUT/unsigned.apk"
(cd "$OUT/dex" && "$JAVA_HOME/bin/jar.exe" uf "$OUT/unsigned.apk" classes.dex)
echo "== zipalign / sign =="
"$BT/zipalign.exe" -f -p 4 "$OUT/unsigned.apk" "$OUT/aligned.apk"
"$BT/apksigner.bat" sign --ks "$KS" --ks-pass "pass:$KS_PASS" --key-pass "pass:$KS_PASS" --ks-key-alias "$KS_ALIAS" \
  --min-sdk-version $MIN --out "$OUT/$NAME.apk" "$OUT/aligned.apk"
"$BT/apksigner.bat" verify --min-sdk-version $MIN "$OUT/$NAME.apk"
cp -f "$OUT/$NAME.apk" "$DIST/$NAME.apk"; ls -l "$DIST/$NAME.apk"
