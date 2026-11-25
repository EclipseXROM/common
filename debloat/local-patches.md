# Local build patches (uncommitted, aosp-remote repos)

The debloat strips source at the manifest level (`debloat.xml`). Some
upstream `Android.bp`/`.mk` files still reference modules whose provider
repos are intentionally removed. Soong/kati validates ALL dep references
at analysis time, so these upstream files are patched **locally in the
working tree** (they live in aosp-remote projects we do not fork).

These edits are uncommitted local modifications. `repo sync` will flag
them as dirty but they survive normal syncs; a `repo sync --force-sync`
or fresh checkout will drop them — reapply then.

To reapply from scratch: check out this list, open each file, remove the
named dep entries (or module blocks) listed below.

| Project | File | Change |
|---|---|---|
| packages/modules/ExtServices | java/tests/hosttests/Android.bp | removed `adservices-host-side-test-utility` from static_libs of CtsExtServicesHostTests-{tplus,sminus} |
| cts | tests/tests/neuralnetworks/benchmark/Android.bp | removed CtsNNAPIBenchmarkTestCases (needs mlts model assets) |
| test/vts-testcase/hal | neuralnetworks/V1_2/benchmark/java/Android.bp | removed VtsHalNeuralnetworksV1_2BenchmarkTestCases |
| test/vts-testcase/hal | neuralnetworks/V1_3/benchmark/java/Android.bp | removed VtsHalNeuralnetworksV1_3BenchmarkTestCases |
| hardware/interfaces | security/see/hwcrypto/aidl/vts/functional/Android.bp | removed hwcrypto rust VTS tests (libhwcryptohal_common provider repo unknown/removed) |
| system/bpf | include/vmlinux/Android.bp | removed vmlinux_h_{6_1,6_6,6_12}_x86_64 genrules + x86/x86_64 arch blocks (x86_64 GKI prebuilts removed; arm64-only builds) |
| trusty/vendor/google/aosp/scripts | scripts/Android.bp | removed `:trusty_dirgroup_trusty_user_app_sample` (trusty/app/sample removed) |
| platform_testing | Android.bp | removed NeuralNetworksApiBenchmark, CalendarTests, ConnectivityUIDTest, PMC, TvSystemUITests, EmergencyInfoUnitTests from test_package lists |
| tools/tradefederation/core | Android.bp | removed `tradefed-contrib` refs (tools/tradefederation/contrib removed) |
| packages/modules/Virtualization | build/microdroid/initrd/Android.bp | removed all *_x86_64 initrd genrules + x86_64 arch src blocks |
| build/make | target/product/generic/Android.bp | removed tradeinmode, DeviceDiagnostics, HTMLViewer, MusicFX, PrivateSpace, Stk, Tag from system_image_defaults deps |
| device/google/cuttlefish | host/commands/assemble_cvd/Android.bp | removed bootloader_* + cvd_avb_pubkey_* + extract-ikconfig from required (cuttlefish_prebuilts removed) |
| build/soong | ui/build/androidmk_denylist.go | added `vendor/eclipsex/magisk/` to `ignore_androidmks` (upstream Magisk Android.mk's `libbase` collides with system/libbase); blockAndroidMks() denylist check disabled earlier on request |

## Restored-but-payload-stripped

These repos had to come BACK into the sync because real build modules
(services.jar, SystemUI-core, libassemblevintf, generic product wiring)
hard-depend on them. Their shipping payloads are filtered out of
PRODUCT_PACKAGES by `config/debloat.mk` instead — source in tree,
nothing lands on the image:

- packages/apps/Launcher3 (com_android_launcher3_flags_lib, launcher-aosp-tapl)
- packages/apps/EyeDropper (flags-aconfig-java lib used by Intent.java)
- packages/apps/Car/* (all source repos; only *Prebuilt blobs stay out)
- packages/apps/TvSettings, packages/apps/SettingsIntelligence, packages/apps/Traceur
- packages/modules/AdServices + OnDevicePersonalization (sdksandbox stubs/flags for services.jar)
- platform/development (platform_tools_version for fastboot/adb)
- prebuilts/sdk + prebuilts/ndk (api stubs + ndk_system)
- prebuilts/vndk v31-v34 (vndk apex builds every snapshot version)
- kernel/configs, device/generic/cuttlefish (source), device/sample (apns xml)
- kernel/prebuilts/common-modules/trusty/* (microdroid vendor image)
- test/{csuite,cts,mts,vts,vts-testcase/{hal,kernel,vndk},suite_harness,robolectric-extensions}
- tools/tradefederation core
