#!/bin/sh
# Build a Manikineko STORE app (signed with the separate store-apps key, NOT the platform key) and publish it.
#   sh scripts/81-store-app.sh <app-dir> <OutName> <versionCode> <versionName> "<one-line summary>" [--no-upload]
#   e.g. sh scripts/81-store-app.sh apps/torch ManikinekoTorch 1 1.0 "Flashlight"
set -eu
ROOT="${MK_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
APP="${1:?app dir}"; NAME="${2:?out name}"; VC="${3:?versionCode}"; VN="${4:?versionName}"; SUM="${5:?summary}"; shift 5
PASS="$(cat "${MK_BUILD:-C:/mkbuild}/store-signing/apps.pass")"
MK_KS=C:/mkbuild/store-apps.keystore MK_KS_PASS="$PASS" MK_KS_ALIAS=storeapps sh "$ROOT/scripts/70-build-app.sh" "$APP" "$NAME" "$VC" "$VN"
python -I "$ROOT/scripts/80-store-publish.py" add "$ROOT/build/$NAME.apk" --summary "$SUM" "$@"
