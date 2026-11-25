# EclipseX common

Common product layer for EclipseXROM builds. Contains the merged
**Manikineko** userland: a small, self-contained first-party app suite
written in plain Java (no Gradle), the EclipseX Home launcher with a
built-in OOBE setup wizard, a signed-catalog app Store with its server
backend, branding assets, and the debloat tooling.

Syncs to `vendor/eclipsex/common` via the org manifest.

## Layout

| Path           | Contents |
|----------------|----------|
| `launcher/`    | EclipseX Home: launcher + OOBE (welcome, language, Wi-Fi, date/time, store) |
| `apps/`        | First-party apps: browser, calendar, files, level, music, notes, radio, recorder, store, torch |
| `store/`       | Store backend: nginx + docker-compose serving a signed `catalog.json` + APKs |
| `branding/`    | Boot animation, sounds, wallpapers, build.prop overlays |
| `debloat/`     | Runtime debloater + device manifests; see `debloat/README.md` |
| `scripts/`     | Whole pipeline: recon, backup, debloat, build apps, branding, boot patching, SELinux policy, zip packaging, store publish |
| `docs/`        | State journal (`docs/STATE.md`) + screenshots |
| `config/`      | Privapp-permission allowlist, debloat makefile |
| `eclipsex.mk`  | Product fragment to inherit from device trees |

## Using it in a build

```make
# in your device product mk, e.g. eclipsex_bluejay.mk
$(call inherit-product, vendor/eclipsex/common/eclipsex.mk)
```

Every app is a Soong `android_app` module (`EclipseXHome`, `EclipseXStore`,
`EclipseXBrowser`, ...). Apps build against `system_current` because some
use internal APIs; all are platform-signed, launcher and store are
privileged (allowlist in `config/`). Apps install to `/product` so the
system image stays GSI-compatible.

## Debloat / no-Google stance

EclipseX ships no GApps and strips the AOSP/Google bundled apps that
duplicate the suite or leak data - three layers, see `debloat/README.md`.
App compatibility is preserved: WebView, SAF, providers, telephony and all
API-surface components stay. Optional Play-compatibility (sandboxed GMS
a la GrapheneOS) is a per-device decision, not part of common.

## Building the apps standalone

The suite also builds off-tree with javac+aapt2+d8 (that's how the
minSdk 16/19 variants for legacy devices are produced):

```bash
# Linux/macOS shell or Git Bash on Windows
sh scripts/22-build-launcher.sh          # launcher + keystore bootstrap
sh scripts/70-build-app.sh apps/torch EclipseXTorch 1 1.0
```

Env knobs: `MK_ROOT` (repo root override), `MK_BUILD` (scratch dir,
default `C:/mkbuild` for the original Windows host), `MK_MIN_SDK`
(default 19), `MK_KS`/`MK_KS_PASS`/`MK_KS_ALIAS`, `MK_DIST`.

## Store backend

`store/` is a static, signed-catalog host: `docker compose up` serves
`catalog.json`, `catalog.sig` and `apk/` on :8097 behind your TLS
terminator. Content is produced and signed on the dev machine with
`scripts/80-store-publish.py`; the signing key never touches the server.

## License

GPL-3.0, same as the Manikineko project it merges. Third-party apps
referenced by the store catalog keep their own licenses and signatures.
