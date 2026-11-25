# EclipseX debloat

Three layers, in order of how early they act:

## 1. Tree level - `debloat.xml` (in EclipseXROM/manifest)

`<remove-project>` entries so the Google/bloat source is never synced.
Applied automatically by `repo sync` because `default.xml` includes it.
Groups: google-apps, aosp-stock-apps (replaced by our suite), dev-samples,
tv, automotive. A caveat group is commented out - enable it only after
checking the notes (drops named features / can break reference targets).

## 2. Product level - `config/debloat.mk`

`PRODUCT_PACKAGES` filter-out of the remaining bundled apps. Pulled in by
`../eclipsex.mk`; opt out per device with `ECLIPSEX_NO_DEBLOAT := true`.
Must be included last in the product makefile chain.

## 3. Device level - `debloat.sh` + `manifest-*.txt`

The original Manikineko runtime debloater: moves APK+odex out of `/system`
into `/data/local/debloat-backup` with a byte-exact, logged rollback.
Runs on-device (su or TWRP), targets stock/vendor ROMs where you cannot
rebuild the image. The `manifest-a/b/c` lists are for Samsung KitKat
(SM-G355HN); make per-device copies for other targets.

```
sh debloat.sh apply  manifest.txt
sh debloat.sh restore
```

## Compatibility rule

Anything that provides an API surface other apps call stays: WebView,
DocumentsUI (SAF), KeyChain, content providers, telephony, all mainline
modules. We remove end-user apps, Google search/ads surfaces, dev demos
and TV/car form-factor packages - not the platform.
