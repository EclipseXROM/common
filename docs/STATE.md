# Manikineko Phone — state after Phase 0 (2026-11-23)

## Device
- SM-G355HN, `kanas3gnfc`, serial `[device serial redacted]`
- Spreadtrum SC7735S / SC8830 (NOT Qualcomm MSM8210)
- Android 4.4.2 / API 19, build `KOT49H.G355HNXXU0AQA1`, baseband `G355HNXXU0AQA1`
- Kernel `3.10.17-8496516`, SELinux Enforcing, `ro.secure=1`, `ro.debuggable=0`
- NOT rooted: no `su` anywhere, `adb root` refused, `adb remount` denied, `/system` ro
- User decision: no backups, phone treated as disposable

## Recon output
`recon/20261123-181854/recon.txt`

## Partition map (`/dev/block/platform/sprd-sdhci.3/by-name/`)
KERNEL p17, RECOVERY p18, system p20, userdata p22, CSC p19 (mounted /cache),
efs p14, MODEM p7, MODEM_BACKUP p8, FIXNV1 p1, FIXNV2 p2, RUNTIMENV1 p11,
RUNTIMENV2 p12, prodnv p15, PARAM p13, HIDDEN p21, OTA p10, FOTA_SIG p9,
SBL1 p3, SBL2 p4, WDSP p5, WDSP_BACKUP p6, Odin_reserved p16.
Note: `fixnv1`/`fixnv2` by-name symlinks are swapped in firmware.

## TWRP artifact (verified)
`twrp/twrp-3.1.1-0-kanas3gnfc.img.tar`
- sha256 `d6434bbdcc07a7c36b6acd0bc62736d1f518e547b1bdc527f448530786e6dc95`
- md5 `1427b26315a58c23795dc4cb73d99993`
- contains `recovery.img` 8372224 bytes
`twrp/recovery.img`
- sha256 `d7997002ca794ecf7022fbf64926118bad148341c0a75ccad6739c22359fd8bb`
- Android bootimg, kernel 0x8000, ramdisk 0x1000000, page 2048

## Heimdall attempt — FAILED
Heimdall 1.4.0 (`twrp/heimdall-suite-1.4.0-win32/Heimdall Suite/`), libusb 1.0.14.
- `detect` -> "Device detected"
- `print-pit` -> "Initialising protocol... ERROR: Failed to send data!"
- Happens with WinUSB bound and interface claimed; repeated 3x, identical.
- Conclusion: Heimdall 1.4.0 + libusb 1.0.14 cannot talk to this S-Boot. Not pursued further.

## Current driver state (RESOLVED)
Driver rollback done by user. In normal mode `PID_6860 -> dg_ssudbus` (Samsung).
In download mode `USB\VID_04E8&PID_685D\5&1B51D3F&0&3 -> dg_ssudbus` — correct for Odin.

## Odin (present, ready)
`twrp/Odin3_v3.14.4/Odin3_v3.14.4/Odin3_v3.14.4.exe` (+ `SS_DL.dll`).
Note: 3.14.4 is much newer than the KitKat-era 3.09/3.13.1 usually recommended for
S-Boot devices. Untested here; fallback is Odin3 v3.09 if `ID:COM` stays empty.

## TWRP installed and working (2026-11-23)
Odin 3.14.4 `PASS!` -> TWRP 3.1.1-0 on RECOVERY (p18). `adb reboot recovery` works.
`product:cm_kanas3gnfc`, `ro.twrp.version=3.1.1-0`.
**Known issue: TWRP screen is WHITE** (panel `lcd_id=ID55c090` framebuffer init).
Recovery itself is fine — `adb shell` gives `uid=0(root)`, so all work is done headless.

## SuperSU 2.82 system-mode install — DONE, root works
Installed from `supersu-2-82.apk` assets (`supersu.arm.png` = ELF ARM `su`).
Files in /system: `xbin/su`, `xbin/daemonsu`, `xbin/supolicy`, `lib/libsupol.so`,
`app/SuperSU/SuperSU.apk`, `etc/install-recovery.sh`, `etc/install-recovery-2.sh`,
`etc/init.d/99SuperSUDaemon`. All root:root, contexts `u:object_r:system_file:s0`.
Verified after reboot: `su -v` -> `2.82:SUPERSU`, `su -c id` -> `uid=0(root)`,
`daemonsu:master` + `daemonsu:0` running.
`adb root` still refused (production build, `ro.secure=1`) — irrelevant, `su` covers it.

## Open item: SuperSU APK not registered as a package
KitKat PackageManager scans only `/system/app/*.apk`, NOT subdirectories
(subdir scanning arrived in Lollipop). APK sits in `/system/app/SuperSU/SuperSU.apk`
so `pm list packages` does not show `eu.chainfire.supersu`.
Fix (needs user confirmation, gate refused it): move to `/system/app/SuperSU.apk`, remove the dir.

## Phase 1 debloat — prepared, awaiting approval
`pm uninstall --user 0` does NOT exist on KitKat (only `[-k]`), so the brief's path is
unavailable. `pm disable-user` triggers a full bugreport dump on this Samsung build and
fails. Chosen path: move APK+odex out of /system into `/data/local/debloat-backup`,
byte-exact rollback via a logged manifest.

Manifests: `debloat/manifest-a-safe.txt` (26 pkgs, 194.3 MB apk+odex),
`debloat/manifest-b-caveat.txt` (107 pkgs, 141.9 MB apk+odex).
Scripts: `debloat/debloat.sh` (device-side, apply|restore, works in Android and TWRP),
`scripts/10-debloat.sh` (host wrapper), `recon/pkgmap.txt` (pkg -> apk path, 178 entries).
All pass `sh -n`. Not executed yet.

## Phase 1 Group A — APPLIED AND VERIFIED (2026-11-23)
`sh scripts/10-debloat.sh apply a-safe` -> moved=26 skipped=0 missing=0.
Backup: `/data/local/debloat-backup` (198952 KB = 194.3 MB), log 27 lines, root:root 600.
`/system` free: 86.3 MB -> 256.2 MB (+169.9 MB).
`MemFree`: 32736 kB -> 145232 kB (+112 MB). Package count 178 -> 152.
Core packages all still present: phone, mms, contacts, clockpackage, popupcalculator,
camera, settings, systemui, launcher, inputmethod. Telephony up (`mCallState=0`,
`com.android.phone` running as radio), launcher/contacts/mms running.
Rollback: `sh scripts/10-debloat.sh restore`.

Device-side script notes: this toolbox has NO awk/sed/basename/dirname/head/printf/wc,
and `mv` across /system -> /data fails with "Cross-device link". Script uses only
builtins + grep + cp + rm. `/tmp` does not exist in normal Android mode; use
`/data/local/tmp`.

## Phase 1 Group B — APPLIED AND VERIFIED (2026-11-23)
`sh scripts/10-debloat.sh apply b-caveat` -> moved=107 skipped=0 missing=0.
Cumulative backup `/data/local/debloat-backup` = 344304 KB (336.2 MB).
`/system` free: 256.2 MB -> 422.5 MB. `MemFree`: 145232 -> 252236 kB.
Package count 152 -> 45. `sys.boot_completed=1`, crash buffer empty, 0 ANR/FATAL.
Core still present: phone, mms, contacts, clockpackage, popupcalculator, camera,
settings, systemui, launcher, inputmethod, providers.media, keyguard, logsprovider.
Telephony up, `com.android.phone` running as radio.
Rollback: `sh scripts/10-debloat.sh restore` (restores all 133 entries).

## Next step: Odin flash
1. Device is in download mode now (`PID_685D`, `dg_ssudbus`).
2. Odin as admin, `AP`/`PDA` = `twrp/twrp-3.1.1-0-kanas3gnfc.img.tar`, uncheck Auto Reboot.
3. After PASS: pull battery, boot `Volume Up + Home + Power` into TWRP.
4. Then flash SuperSU zip from TWRP to get `su`.

## Battery warning
Was 14% at recon. Must be 60%+ before flashing RECOVERY.

## Phase 2 Manikineko launcher — DONE (2026-11-23)
`launcher/` (plain SDK, `sh scripts/22-build-launcher.sh`, install `adb install -r build/manikineko-home.apk`).
Bug fixed: two HOME apps -> chooser on every Home press. Stock Samsung launcher moved to backup via
`debloat/manifest-c-launcher.txt` (`sh scripts/10-debloat.sh apply c-launcher`; `restore` brings it back, along with all
other debloat groups). Theme is now Holo.Wallpaper with dark scrim (`mk_scrim` in colors.xml) so the wallpaper shows.
Status/nav bar NOT hidden (optional, not requested).

## Phase 3 Branding — DONE (2026-11-23), not yet seen on screen: boot animation
Originals backed up: device `/data/local/branding-backup/`, host `branding/orig/`.
- `sh scripts/31-branding.sh apply|restore`: bootanimation.zip (built by `scripts/30-bootanim.py`, 480x800),
  `ro.build.display.id=Manikineko 1.0` (model number untouched), `ro.config.ringtone/notification_sound/alarm_alert`,
  system wallpaper (800x800 padded by `scripts/32-wallpaper-pad.py`; KitKat wallpaper service insists on 800x800),
  lockscreen wallpaper via new `/system/wallpaper/lockscreen_default_wallpaper.jpg` (Samsung keyguard default path).
- `sh scripts/34-sounds.sh apply|defaults|restore`: Samsung ringtones/notifications/alarms (24/19/8 files) replaced by
  synthesized `Manikineko_Ring/Note/Alarm.wav` (`scripts/33-sounds.py`); originals in `/data/local/branding-backup/audio`.
  `ui` sounds untouched. Run `apply`, reboot, then `defaults`.
- Boot logo (bootloader splash) deliberately NOT touched.

## Phase 4 — LineageOS 13.0 (Android 6.0.1) INSTALLED AND BOOTING (2026-11-23)
Stock KitKat + Phase 1-3 work was replaced (user: phone is e-waste, no backups wanted; stock ROM kept by user).
- Zip: `twrp/lineage-13.0-20170317-UNOFFICIAL-kanas-SandroidTeam-Ih24n.zip` (from AndroidFileHost, sha256
  `d1de7038c57e1a6dc61415b101ef7d949f944f17e20e7244019390c623c8a243`). sandroidteam.com is now a parked domain: do NOT
  use its bit.ly links. updater-script allows kanas3gnfc/SM-G355HN. Flashed via TWRP (`twrp wipe data/dalvik/cache`,
  `twrp install`). It writes only `system` (p20) and `KERNEL` (p17); bootloader/modem/EFS untouched.
- First boot hung on the boot animation: the ROM's `fstab.sc8830` mounts `/productinfo` (by-name/PRODNV) but the
  `prodnv` partition (p15) holds no ext4 and stock never mounted it -> `mount_all` fails -> `ro.crypto.state` never set
  -> `on nonencrypted` / `class_start main` never fires -> no zygote. Workaround test: `setprop vold.decrypt
  trigger_restart_framework`. Permanent fix: `scripts/40-patch-boot.py` comments that fstab line out of the ramdisk
  (same-length edit) -> `recon/boot/boot-patched.img` (sha256 `42f602e4...d7324`), dd'd to KERNEL (p17), verified by
  readback. Original boot image: `recon/boot/boot-orig.img` (also inside the zip) for rollback.
- Now: `sys.boot_completed=1`, `ro.crypto.state=unencrypted`, setup wizard on screen. Uptime ~83 s at boot done.
- KNOWN BROKEN: modem/RIL (`gsm.sim.state=NOT_READY`, no rild). modemd logs `Failed to open /dev/stty_w0`,
  `/dev/spipe_w2` at start; configs also reference `by-name/modem` and `by-name/DSP` but device has `MODEM`, `WDSP`
  (case/name mismatch, likely related). User has no SIM to test with, so parked.
- Gone with the wipe: Manikineko launcher, branding (bootanimation, wallpapers, tones), debloat. Sources still in
  `launcher/`, `scripts/22..34`, `branding/`; they were written for KitKat paths and need re-checking on Android 6.

## SIM test on LineageOS 13 (2026-11-23) — FAILED
With a (dummy) SIM inserted the phone hangs at the Samsung logo on boot (no USB enumeration at all, so it dies before
adbd: bootloader/early-kernel stage). Without SIM it boots normally. Fix for recovery: remove SIM and battery-pull.
Cause not diagnosed; /proc/last_kmsg after a no-SIM boot may show it. Phone must be used WITHOUT SIM on this ROM.

## Manikineko on LineageOS 13 — launcher + branding restored (2026-11-23), confirmed by user on screen
- Launcher: whitelist in `launcher/res/values/arrays.xml` now has LOS names first (dialer, contacts, messaging, deskclock,
  calculator2, camera2, gallery3d, settings). Setup wizard and `com.cyanogenmod.trebuchet` disabled via `pm disable`,
  provisioning flags set, so Manikineko is the only HOME. User confirmed: boot animation and Home work.
- Branding: `sh scripts/50-los-branding.sh apply` (reboot, SIM OUT) then `... defaults`; `restore` uses
  `/data/local/branding-backup-los/`. Do NOT use scripts 31/34 on LOS (they'd overwrite build.prop with KitKat's).
  Wallpaper is 960x800 here (`scripts/32-wallpaper-pad.py frame_6 960 wallpaper_960.jpg`).
- Tones set: ringtone 242, notification 241, alarm 240 (Manikineko_*.wav). Not listened to yet.
- Android 6 quirks: `screencap` segfaults and /dev/fb0 can't be opened, so no host screenshots; ask the user to look.
- Still open: modem/RIL (phone only boots WITHOUT a SIM), status bar not hidden.

## DECISION (2026-11-23): Manikineko Phone is built on LineageOS 13 (kanas), no return to stock KitKat
User: "we already started creating Manikineko Phone, which will become a ROM, so leave it and keep building".
Current limits on this base: no SIM allowed (boot hang), no sound, no calls: modem (CP2) never answers.
Audio cards exist (sprdphone, all-i2s) but playback goes through the CP2 DSP (saudio sblock "not ready").
Candidate fixes, in order: (1) experiment: load MODEM/WDSP images into /proc/cpw/{modem,dsp} + /proc/cpw/start by hand
(RAM only, partitions read-only; NEEDS user OK because it touches the modem path); (2) fix partition names for
modem/DSP/WDSP (ROM expects by-name/modem, DSP, wmodem; device has MODEM, WDSP); (3) build our own ROM from
Samsung-Galaxy-Core-II lineage-15.1 trees (needs Linux build host, see Phase 4 evaluation).

## Modem experiment on LOS13 (2026-11-23, user approved) — modem still does not answer
- Read-only dumps (also an offline backup): `recon/modem/MODEM.img` (p7, 10 MiB, ARM code, 6.66 MB used, base 0x90300000)
  and `recon/modem/WDSP.img` (p5, 5 MiB, DSP, header "versionTD1.0001"). `recon/modem/modemd` = LOS modemd binary.
- S-Boot already loads MODEM->0x90300000, WDSP->0x90020000, fixnv->0x90240000, runtimenv->0x90280000 and logs
  "cpload success!" (recon/last_kmsg.txt). /proc/iomem shows 0x90000000-0x920fffff is NOT System RAM (reserved for CP),
  so Linux does not overwrite the images.
- `echo 1 > /proc/cpw/start` (exit 0, no effect): sblock-2-13/17 stay "not ready", spipe 2-4 not ready, no rild.
  `ril-daemon` is `disabled` in init.kanas3g_base.rc and is started when modemd reports the modem alive; never happens.
  `/proc/cpw/{modem,dsp,start,stop}` exist. Not tried: stop+start cycle, loading images via /proc/cpw/modem|dsp.
- Next idea: compare with the STOCK KitKat firmware (user owns it): its boot.img init.sc8830.rc and modemd show how
  CP2 is really started. Needs the stock AP .tar.md5 path from the user.

## Stock firmware analysis + 2nd modem experiment (2026-11-24)
User supplied `twrp/SAMFW.COM_SM-G355HN_SEB_G355HNXXU0AQA1_fac.zip` (official, same build as the phone's stock).
Extracted to `recon/stock/` (AP: boot.img, recovery.img, system.img; CP: SPRDCP.img, SPRDDSP.img, nvitem.bin;
`system.raw.img` via `scripts/41-unsparse.py`, files read with 7-Zip; `ramdisk/` = unpacked stock boot ramdisk).
- Stock CP images == the phone's MODEM/WDSP partitions (nonzero length 6661028 / 1968128): modem partitions are intact.
- Stock fstab does mount /productinfo from by-name/prodnv (lowercase) but the mount is allowed to fail on stock init;
  the partition holds no ext4 on this unit. Our boot.img patch (comment the line out) is therefore still right.
- Stock `init.sc8830.rc` (persist.modem.w.enable=1) creates by-name symlinks FIXNV1<->fixnv2, RUNTIMENV1/2 -> lowercase
  names; LOS rc lacks them (LOS nvitemd uses the uppercase names and reads them fine).
- Stock modemd (25884 B) differs from LOS modemd (21780 B): stock has VLX/"nk" hypervisor code (/proc/nk/*,
  guestOS_2_bank, "Check and load vlx modem img"). Stock kernel is 12 MB and carries no IKCONFIG.
- LOS kernel source (Samsung-Galaxy-Core-II/kernel_samsung_kanas lineage-15.1): /proc/cpw is drivers/misc/sprd_cproc;
  `start` = native_wcdmamodem_start() in arch/arm/mach-sc/devices-sc8830.c: writes a jump stub (entry CPW_START_ADDR+0x300000
  for !SCX15) into IRAM and releases CP reset. defconfig kanas3g_hw04: SCX35, SIPC_WCDMA, SPRD_CPROC (SCX15 off), so the
  entry 0x90300000 matches where S-Boot loads MODEM: start-address mismatch is RULED OUT. Copies in recon/kernel/.
- Experiment 2: stop -> dd WDSP.img to /proc/cpw/dsp (481x4096) -> dd MODEM.img to /proc/cpw/modem (1627x4096) -> start:
  all returned 0, but right afterwards `adb shell` stopped answering (adb transport still listed the device): the phone
  appears to have hung (same kind of hang as booting with a SIM). Needs battery pull; nothing was written to flash.
- Next ideas: (a) check whether CP release hangs the AP (watchdog / IRQ storm; wdtirq), (b) compare the LOS ramdisk
  init (modem props, symlinks, modem_control) with stock, (c) the stock boot.img is VLX-based, so a VLX-less kernel
  may simply not be able to run this CP image: the real fix may need kernel/modem pairing work.

## Experiment: hybrid boot (stock Samsung kernel 3.10.17 + LOS13 ramdisk) (2026-11-24)
Stock kernel has NO VLX/nk (strings /proc/nk, NKERNEL, VLX absent), only plain sprd_cproc + sipc, so the stock modemd
VLX strings are dead code; the real difference is the kernel build (stock 3.10.17-8496516 vs LOS 3.10.104 SandroidTeam).
`scripts/42-hybrid-boot.py` -> `recon/boot/boot-hybrid.img` (sha256 c23973c8...e3ee): stock kernel + LOS ramdisk with
(1) /productinfo fstab line commented, (2) sepolicy policydb version 30->29 (stock 3.10 kernel max 29).
Flashed to KERNEL (p17) and verified by readback. ROLLBACK: boot TWRP (Vol Up+Home+Power), adb push
`recon/boot/boot-patched.img` to /data/local/tmp and `dd if=... of=/dev/block/platform/sprd-sdhci.3/by-name/KERNEL bs=2048`
(boot-patched.img = LOS own kernel, boots to Android w/o modem). Risks: init may fail to load policy (M init then
reboots to recovery), Mali/ALSA/wifi userspace vs stock kernel, LOS modules (/system/lib/modules only mmc_test.ko).

### Hybrid boot attempt 1 failed, attempt 2 flashed (2026-11-24)
Attempt 1 (policy version field patched 30->29): kernel log (recon/last_kmsg_hybrid.txt, hybrid section after the S-Boot
block) says `SELinux: policydb version 29 does not match my version range 15-28` -> init "Security failure; rebooting into
recovery mode". The stock 3.10.17 kernel DID boot to init (Samsung sec_log keeps its log), i.e. the stock kernel is viable.
Rolled back from TWRP (boot-patched.img verified by hash), then wrote `scripts/43-sepolicy-downgrade.py`: real v30->v28
conversion (drops the 85 CEXPR_NAMES type_set blocks; parser sanity-checked: 5 commons, 87 classes, 2 roles, identical
tail). `scripts/42-hybrid-boot.py` now uses it. Attempt 2 = recon/boot/boot-hybrid.img sha256 0d5bb4d0...09c0, flashed to
KERNEL and verified. If it fails again init reboots into TWRP by itself; read /proc/last_kmsg there (stock kernel keeps
its log), roll back with boot-patched.img.

### Hybrid attempt 2 failed, attempt 3 flashed (2026-11-24)
Attempt 2 log (recon/last_kmsg_hybrid2.txt): v28 header accepted, then `SELinux: avtab: more than one specifier`.
Cause: the M policy contains 29 "xperms" avtab entries (spec flag 0x0100; layout = 8-byte key + 1 byte type + 8*u32 = 33 bytes).
`scripts/43-sepolicy-downgrade.py` now also parses roles/types/users/bools/levels/cats + the main avtab (5394 rules,
same count the kernel printed) and drops the 29 xperms entries (ioctl whitelist rules, so ioctls get broader: fine,
kernel is permissive). Tail after avtab copied verbatim (checked). Attempt 3 = boot-hybrid.img sha256 b40fe514...a308,
flashed + verified. Same failure mode = auto reboot to TWRP, read /proc/last_kmsg. Rollback = boot-patched.img.

### Hybrid attempt 3 result + rollback (2026-11-24)
Attempt 3 log (recon/last_kmsg_hybrid3.txt): the downgraded policy LOADED on the stock kernel
("5365 rules, 1 users 2 roles 582 types ... policy loaded"). Next fatal step:
`init: SELinux: Could not set context for /init: Operation not supported on transport endpoint` -> `restorecon failed`
-> `Security failure; rebooting into recovery mode`. Cause: stock kernel's rootfs has no security xattr support
("dev rootfs ... uses genfs_contexts"); Android 6 init treats restorecon("/init") failure as fatal.
Only fix is to binary-patch LOS /init (skip security_failure after restorecon). Located string "restorecon failed: %s\n" at
va 0x80a8d in recon/losramdisk/init (ELF32 ARM static) but found NO movw/movt, literal-pool, adr or PIC references by
hand-rolled scans. A disassembler (pip capstone) was blocked by the auto-mode classifier (executing a downloaded package),
so this was NOT pursued. Further blockers likely after init (Mali/ALSA/wifi userspace vs stock kernel, modem props).
STATE NOW: LOS own kernel boot image (boot-patched.img, sha256 42f602e4...7324) restored to KERNEL and verified; phone is
rebooting into LOS (no modem, no sound, no SIM). Hybrid image stays on disk in recon/boot/boot-hybrid.img.

### Hybrid attempt 4 flashed (2026-11-24)
User authorised capstone ("leidziam"). capstone 5.0.1 needs distutils (not in py3.15); capstone 5.0.6 wheel works, unpacked in the
scratchpad only (pylib2). Disassembly of /init (ELF ARM static; code is mostly Thumb-2, PIC style) found NO reference to the
"restorecon failed" string by movw/movt, literal-pool, adr or ldr+add-pc patterns, so no binary patch was made.
Alternative without patching init: restorecon("/init") only calls setxattr when the current context != file_contexts label.
The inode's in-core context comes from policy genfscon (rootfs) via getxattr -> `u:object_r:rootfs:s0`. So
`scripts/42-hybrid-boot.py` now rewrites file_contexts `/init  u:object_r:init_exec:s0` -> `u:object_r:rootfs:s0`
(permissive kernel: no domain transition needed). Attempt 4 = boot-hybrid.img sha256 7d36c0a9...e319 (also contains
the v28 sepolicy), flashed to KERNEL from running LOS (dd) and verified. Rollback = boot-patched.img via TWRP.

### Hybrid attempt 4 result, attempt 5 flashed (2026-11-24)
Attempt 4 log (recon/last_kmsg_hybrid4.txt): policy loaded, restorecon("/init") PASSED (file_contexts trick works), but init then
set enforcing=1 (the stock kernel has no forced-permissive hack like the LOS kernel) and
`avc: denied { execute } scontext=u:r:kernel:s0 tcontext=u:object_r:rootfs:s0` -> `execv("/init") failed: Permission denied`
-> Security failure -> recovery. Fix in `scripts/43-sepolicy-downgrade.py`: rewrite the policy's permissive_map ebitmap so
EVERY type (values 1..582) is permissive (mapunit 64, highbit 640, 10 nodes; independently re-read OK), so enforcing mode
denies nothing. Attempt 5 = boot-hybrid.img sha256 aa3707a7...b624, flashed from TWRP + verified, rebooted.
Rollback unchanged: boot-patched.img (sha256 42f602e4...7324) via TWRP/dd.

### Hybrid attempt 5 result, attempt 6 flashed (2026-11-24)
Attempt 5 (all types permissive): init got through BOTH stages (second stage started, ueventd coldboot, rc files parsed) and ran ~118 s,
then was powered off by the user: it never mounted /data nor started USB because the stock kernel passes no androidboot.hardware, so
`ro.hardware=unknown` -> init.rc imports /init.unknown.rc (missing), `fstab.unknown` missing, ueventd.unknown.rc missing.
Hence no adb / no Samsung USB device on the PC. Attempt 6: `scripts/42-hybrid-boot.py` adds ramdisk aliases
init.unknown.rc, ueventd.unknown.rc, fstab.unknown (byte-identical copies of the sc8830 files, verified).
boot-hybrid.img sha256 57ce8aa4...bace (12904448 B). Flashed from TWRP + verified; rebooting next.

### Hybrid attempt 6 result (2026-11-24): Android userspace starts on the stock kernel
Log (recon/last_kmsg_hybrid6.txt): /system, /data, /cache, /efs mount via mount_all; logd, vold, servicemanager, surfaceflinger, modemd,
netd, debuggerd, drm, media, installd, keystore, gpsd, zygote, phoneserver_w, ril-daemon (+2), engpcclientw, adbd all START;
USB gadget enabled (mtp,acm,adb). Seen: init.unknown.rc "invalid command 'pipe'" (Spreadtrum init extension; harmless in LOS
too?), debuggerd tombstone at ~7 s (something crashed), surfaceflinger/media/zygote re-starting at ~19.8 s (crash loop),
no panic/oops. Kernel ring ends at 19.8 s (reset/user reboot). NEXT: reboot into the hybrid and read `adb logcat` live instead of
power-cycling (adbd is up) to see why surfaceflinger/zygote crash (Mali/gralloc userspace vs stock kernel is the prime suspect),
and check ril-daemon/modemd state. Rollback unchanged (boot-patched.img).

## BREAKTHROUGH (2026-11-24): hybrid boot = stock kernel 3.10.17 + LOS13 ramdisk BOOTS, modem + SIM work
Final hybrid (recon/boot/boot-hybrid.img, sha256 986dc48d...4489, 14354432 B, built by scripts/42-hybrid-boot.py) contains:
stock Samsung kernel + LOS ramdisk with: /productinfo fstab line commented; sepolicy v30->v28 (85 type_sets dropped, 29 xperms
avtab rules dropped, ALL 582 types permissive) via scripts/43-sepolicy-downgrade.py; file_contexts /init -> rootfs; aliases
init.unknown.rc / ueventd.unknown.rc / fstab.unknown (stock kernel gives no androidboot.hardware -> ro.hardware=unknown);
/mali.ko (stock Mali r4p0 module, vermagic 3.10.17-8496516; LOS libMali.so is byte-identical to stock r4p0) loaded by
`on post-fs insmod /mali.ko` appended to init.unknown.rc.
Why it was needed: with the LOS kernel the CP2 modem never answers (no SIM, no RIL, no sound). Under the stock kernel modemd gets
`OK` to AT on /dev/stty_w0 and saudio reports "modem boot and handshake ok".
Verified live: sys.boot_completed=1, SurfaceFlinger "Boot is finished (12976 ms)", Manikineko home focused,
gsm.sim.state=READY (slot 1, dummy SIM), rild "android reference-ril 1.0", mali module live, /dev/mali0 present.
Not yet verified: audible sound, network registration (mServiceState 3/1 = radio off/out of service with dummy SIM), calls/SMS,
Wi-Fi, camera. Notes: adbd runs as shell (not root) in the hybrid -> flash KERNEL from TWRP; old tombstones in recon/tombstones.
Rollback to LOS own kernel = boot-patched.img (sha256 42f602e4...7324).

### Hybrid: network + audio stack fixed (2026-11-24)
- Network: registers on `Tele2 LT` (gsm.operator.alpha), SIM READY in slot 1, network time set. (User's "dummy" SIM is a Tele2 card.)
- LOS ROM bug (also present with the LOS kernel, explains "no sound" there): init.rc `service media` listed 15 supplementary
  groups; Android 6 init allows 12 and DROPS the whole group option -> mediaserver ran with gid 0 / no groups -> `open snd control
  failed: Permission denied` -> "Unable to load sound card". Fix (42-hybrid-boot.py, init.rc): 11 groups (dropped qcom_diag,
  sdcard_r, shell).
- Then mediaserver aborted `FORTIFY: FD_SET: file descriptor < 0`: the audio HAL select()s on /dev/pipe/mmi.audio.ctrl, a FIFO that
  Spreadtrum's custom init `pipe` command creates (Android 6 init: "invalid command 'pipe'"). Fix: init.unknown.rc service
  mk_pipes (/system/bin/mkfifo for /dev/pipe/mmi.audio.ctrl + /dev/rpipe/ril.vt.{0,1,2}) started `on boot` (after early-boot
  creates /dev/pipe), plus `on property:init.svc.mk_pipes=stopped` chmod 0666 (init services run with umask 077).
- Result (boot-hybrid.img sha256 a9cbd87e...1d97): sys.boot_completed=1, mediaserver running, 0 crashes, AudioFlinger MIXER output
  thread on SPEAKER. Audible sound to be confirmed by the user.
- Still broken: camera (camera.sc8830.so: missing `android::MemoryHeapIon::MemoryHeapIon(const char*, unsigned, unsigned,
  unsigned long)`; LD_SHIM_LIBS -> libmemoryheapion_sprd.so in the media service is apparently not applied), Wi-Fi (driver
  "unloaded", wlan0 present: bcmdhd built into the stock kernel).

### CALLS WORK (2026-11-24) — single-SIM fix
The SIM is Tele2 "Pildyk" (SPN "PILDYK"). Calls first failed with "Cellular network not available" although the modem was
registered (VOICE_REGISTRATION_STATE 1, Tele2 LT 24603, UMTS): SubscriptionInfoUpdater waited for "SIM2 IccId" forever because
this LOS build is configured dual-SIM (SM-G355H DUOS) while SM-G355HN is single-SIM -> no subId, emergency-only.
Fix: /system/build.prop ro.modem.w.count=1, ro.msms.phone_count=1, persist.msms.phone_count=1,
persist.radio.multisim.config=ssss (backup: branding/los/build.prop.pre-singlesim, new: branding/los/build.prop.singlesim);
deleted stale /data/property/persist.radio.multisim.config + persist.msms.phone_count; ramdisk init.kanas3g_base.rc
`setprop ro.multisim.simslotcount 1` (42-hybrid-boot.py). boot-hybrid.img sha256 e81641a1...f127.
Result: mServiceState=0 IN_SERVICE Tele2 LT (EDGE); outgoing test call to the user's phone CONFIRMED working by the user.
NOTE: scripts/50-los-branding.sh `restore` would put back the dual-SIM build.prop (its backup predates this fix).
Open: SMS test, audible ringtone/speaker check, camera (MemoryHeapIon symbol), Wi-Fi (driver unloaded), SELinux all-permissive.

### SMS WORKS (2026-11-24)
Test SMS via com.android.messaging (compose intent + uiautomator dump to locate send_message_button, input tap): RIL `SEND_SMS` -> `{mMessageRef = 5, mErrorCode = 0}` = accepted by the Tele2 network. Receipt CONFIRMED by the user. Tip: `uiautomator dump` works where screencap segfaults.

### CAMERA WORKS (2026-11-24)
Two more LOS packaging bugs fixed:
1. init.rc media service LD_SHIM_LIBS pointed camera.sc8830.so/camera2.sc8830.so at `libmemoryheapion_sprd.so` (not shipped);
   the exported android::MemoryHeapIon ctor is in /system/lib/libmemoryheapion.so -> 42-hybrid-boot.py rewrites the shim name.
   Result: "Number of camera devices: 2" (back + front).
2. gralloc.sc8830.so needs `libion_sprd.so`; the ROM ships it as /system/lib/libion.so (SONAME libion_sprd.so), which only
   works in processes where libion.so was already loaded (surfaceflinger), not in mediaserver -> startPreview SIGSEGV in
   GraphicBufferMapper. Fix (on /system, done in TWRP): `cp /system/lib/libion.so /system/lib/libion_sprd.so` (644, system_file).
Verified: camera2 app preview + shutter -> /sdcard/DCIM/Camera/IMG_20261124_030147.jpg, 2560x1920, real image.
Current boot-hybrid.img sha256 47b3400d...ef08. Remaining: Wi-Fi, SELinux all-permissive, ro.hardware=unknown aliases.

### SOUND CONFIRMED (2026-11-24)
User heard the camera shutter sound on the speaker. Calls, SMS, camera, sound all working on the hybrid.

### WI-FI WORKS (2026-11-24) — scanning OK, not yet connected to a network
Stock kernel bcmdhd (built in) looks for nvram /system/etc/wifi/bcmdhd.cal and default fw /system/etc/firmware/fw_bcmdhd.bin;
LOS ships /system/etc/wifi/nvram_net.txt and /system/vendor/firmware/fw_bcmdhd.bin -> "dongle nvram file download failed",
dhd_open -35. Fix on /system (TWRP), nothing of LOS overwritten: stock nvram_net.txt -> /system/etc/wifi/bcmdhd.cal, stock
bcmdhd_sta.bin -> /system/etc/firmware/fw_bcmdhd.bin, stock bcmdhd_apsta.bin -> /system/etc/firmware/fw_bcmdhd_apsta.bin
(copies in recon/wifi/stock). Result: "Firmware up", wlan0 UP, p2p_supplicant running, "Wi-Fi is enabled", scan sees 2 networks.
(First HAL attempt with the LOS vendor fw path still logs wl_android_wifi_on failed (-14); the retry via wpa_supplicant works.)
Notes: adb in the hybrid is not root (svc wifi fails with SecurityException) -> toggle via Settings UI (uiautomator dump + tap).

## DECISION (2026-11-24): SELinux stays all-permissive
User: Manikineko Phone will not be advertised as Android, will not be APK-based; this LineageOS 13 hybrid stays only as the base.
SELinux's main job on Android is sandboxing untrusted APKs; with no third-party apps that attack surface is gone, so no policy
hardening for now (revisit if a browser / app installation / other open surface is added). Next planned step: package the whole
hybrid (boot image + /system fixes + branding) as ONE TWRP-flashable zip for reproducible installs.

## DECISION REVISED (2026-11-24, later): product has its own app store -> SELinux hardening is on the roadmap
User clarified: no Google, own store (F-Droid-like), own compatibility layer, security patched by the team itself. So the earlier
"SELinux irrelevant" call is withdrawn. Plan: (1) bring-up stays all-permissive; (2) before release collect `avc: denied` from real
use, keep permissive only for kernel/init/modem-side types, make app/system domains enforcing (tool: scripts/43-sepolicy-downgrade.py
permissive_map); (3) self-patching Android 6.0.1 + kernel 3.10.17 needs a source build host (Linux/WSL, ~200 GB, see Phase 4 notes) or a
move to a newer base (lineage-15.1 trees by Samsung-Galaxy-Core-II). Next: one TWRP-flashable zip of the current hybrid.

## TWRP ZIP BUILT (2026-11-24) — offline-verified, NOT yet flash-tested
`python -I scripts/60-build-zip.py` -> build/manikineko-phone-1.0-kanas3gnfc.zip (352358677 B, sha256 7fee47ed...fffb).
Contents: LOS13 base (update-binary + system.new.dat/transfer.list/patch.dat/file_contexts, byte-identical to the SandroidTeam zip),
boot.img = recon/boot/boot-hybrid.img (sha 47b3400d...), overlay manikineko/system/: build.prop (single-SIM + branding; only 8 keys
differ from the LOS base build.prop, asserted by the builder), bootanimation, 3 tones, Wi-Fi nvram+fw (stock), libion_sprd.so,
launcher APK as /system/app/ManikinekoHome, wallpaper, init.d/50manikineko-firstboot.
updater-script: device assert (kanas*/SM-G355*), block_image_update system, delete Trebuchet + CyanogenSetupWizard + stock tones,
extract overlay, set_metadata (system_file), write KERNEL. No otasigcheck/backuptool (fresh-install package, unsigned).
First boot: init.d script (via LOS `sysinit`) waits for sys.boot_completed, sets device_provisioned=1 / user_setup_complete=1, installs
the wallpaper if missing, writes /data/misc/manikineko_firstboot_done and reboots ONCE.
Checks done: zipfile.testzip OK; system.new.dat/update-binary/boot.img identical to sources; updater-script reviewed.
TO DO: flash test on the phone (wipe data/cache/dalvik in TWRP, install zip, expect auto-reboot once, then verify calls/SMS/camera/
sound/Wi-Fi/launcher/wallpaper). Rollback to the previous working state = the same zip minus nothing; or LOS zip + boot-patched.img.

## ZIP FLASH TEST PASSED (2026-11-24): clean install of build/manikineko-phone-1.0-kanas3gnfc.zip
TWRP: wiped cache/dalvik/data (kept /data/media), `twrp install /sdcard/manikineko.zip` (pushed zip sha256 verified on device:
7fee47ed...fffb) -> "script succeeded". Pre-boot check in TWRP: Trebuchet + CyanogenSetupWizard gone, overlay files present with
system_file contexts, build.prop has display.id/single-SIM keys. First boot -> init.d first-boot script ran
(/data/misc/manikineko_firstboot_done present, one automatic reboot) -> device_provisioned=1, user_setup_complete=1, Manikineko
launcher focused, wallpaper service 960x800, default ringtone/notification/alarm = Manikineko tones, SurfaceFlinger/media/zygote
running, 0 crashes, mali module loaded, 2 cameras, AudioFlinger MIXER on SPEAKER, Wi-Fi driver ok (wlan0 UP), camera photo saved
(IMG_20261124_032835.jpg). Modem registered Tele2 LT again.
OBSERVATION: right after the first-boot auto reboot the SIM showed gsm.sim.state=ABSENT (modem AT+EUICC? -> 0,2,1) and recovered
after a full power-off/power-on. Earlier ordinary `adb reboot`s kept the SIM READY, so cause unknown (warm reboot straight after the
first boot? SIM detection after the fresh-NV first boot?). To investigate: repeat a warm reboot and see if ABSENT reproduces; if so
replace the first-boot `reboot` by a framework restart (`setprop ctl.restart zygote`) which does not touch the modem.
Not yet re-tested on the clean install by the user: calls, SMS, audible sound.

### Clean-install call + SMS verified by the assistant (2026-11-24, ~03:30)
Call to the user's phone: Telecom SET_CONNECTING -> SET_DIALING -> SET_ACTIVE (user answered) -> hung up locally. SMS: RIL `SEND_SMS`
mMessageRef=6, mErrorCode=0 (accepted by the network). The user's confirmation of audible call audio / SMS receipt: pending.

### SIM ABSENT after first-boot reboot: did not recur (user, 2026-11-24)
User reports the SIM problem has not come back. Treated as a transient modem/SIM detection glitch; no script change made. If it
reappears after a fresh install, switch the first-boot `reboot` to a framework restart (`setprop ctl.restart zygote`).
Call + SMS + camera + Wi-Fi + sound confirmed on the zip-built system. Project milestone: "Manikineko Phone 1.0" reproducible zip.

## OWN APPS + MANIKINEKO ICON PACK (2026-11-24)
Direction change: F-Droid dropped for now (installed 1.23.2 to test, needed ISRG Root X1 in /system/etc/security/cacerts/6187b673.0
because Android 6 lacks it; uninstalled again). We write our own small apps instead (Java, no AndroidX, minSdk/targetSdk 19,
dark palette mk_*, strings EN + LT), built with `sh scripts/70-build-app.sh <app-dir> <OutName> <vcode> <vname>`.
- apps/notes -> package online.zyghosting.manikineko.notes ("Notes"/"Užrašai"): plain-file store (one .txt per note in app files
  dir), list newest first, auto-save on pause, long-press delete, share. Tested on the phone: create, persist across force-stop, delete.
- Next app: Files (online.zyghosting.manikineko.files, glyph already in the icon set). Calculator/clock/etc. stay AOSP for now.
- Launcher 1.1 (versionCode 2): whitelist system apps first (Notes added after the calculator) + every non-system launchable app
  appended alphabetically (store apps show up); icon pack: `scripts/71-app-icons.py launcher/res --pack` makes drawable-nodpi
  ic_app_{phone,contacts,messages,clock,calculator,camera,gallery,settings,notes,files}.png and AppEntry.ICON_PACK maps AOSP
  and Samsung package names to them (icons of other apps stay their own). Glyphs drawn with PIL (see `--sheet` for a contact sheet).
- LOS flag found: HOME key is blocked while CMSettings.Secure cm_setup_wizard_completed=0 ("Not starting activity because user setup
  is in progress"); first-boot script now also runs `settings --cm put secure cm_setup_wizard_completed 1`.
- Zip builder (scripts/60-build-zip.py, VERSION 1.1) now also ships ISRG Root X1, Notes as /system/app/ManikinekoNotes and the
  updated launcher. NOT yet rebuilt/flash-tested after these additions.

## ABOUT-PHONE ROWS: /system RE-SIGN (2026-11-24)
The three rows `Device maintainer`, `My(Ih24n) Sweetheart`, `Maintainer organisation` are literal strings in
`res/xml/device_info_settings.xml` inside `/system/priv-app/Settings/Settings.apk`, not build.prop. The original platform key
is not available, so the whole signature cluster was re-signed with the project keystore (`C:/mkbuild/manikineko.keystore`,
alias `manikineko`).
- `scripts/45-signature-dependents.py` -> `work/signature-dependents.json`: 259 signature-level permissions defined by
  framework-res.apk + org.cyanogenmod.platform-res.apk, 53 packages request them, 27 belong to android.uid.system; union = 61 APKs.
- `scripts/46-resign-system.py`: zipalign + apksigner for those 61, patches the Settings rows in place with equal-length text
  (binary XML string pool stays valid), verifies each signature. Output `work/resigned/`.
- `scripts/47-flash-resigned.py --confirm`: pushes the 61 APKs, sets 644/root:root/system_file, removes stale `<sigs>` blocks
  from /data/system/packages.xml (104 -> 0) so PMS adopts the new certificate instead of throwing
  INSTALL_FAILED_SHARED_USER_INCOMPATIBLE.
- `scripts/48-sdat2img.py` + `scripts/49-ext4-extract.py` + `scripts/50-restore-oat.py`: the ROM ships stripped APKs (no
  classes.dex), so deleting oat dirs breaks the boot classpath ("No original dex files found"). The oat trees were pulled back
  out of the ROM image (transfer list v3: `new <n> <start>,<end>,...`, half-open ranges, written at their block offsets).
- `scripts/51-mac-permissions.py`: mac_permissions.xml maps signer cert -> seinfo; without our certificate every re-signed
  package fell back to seinfo `default` and died in selinux_android_setcontext ("No match for app with uid 1000"). Added
  `<signer signature="<our DER hex>"><seinfo value="platform"/></signer>`.
- Verified on the device: boot_completed=1, system_server + SystemUI up, Settings uid 1000 with 204 granted permissions
  (WRITE_SECURE_SETTINGS, MANAGE_USERS, REBOOT all granted), About phone shows `Manikineko`, `Manikineko Phone`,
  `manikineko.nl`, `ZygHosting`, `Manikineko Phone 1.2 (LineageOS 13.0)`.
- Backups: `backup/apks-backup.tar` (94 original /system APKs), `backup/packages.xml`, `work/mac_permissions.xml.orig`,
  `recon/boot/boot-hybrid.img.bak-1.1`.

### Launcher + Notes after the /system re-sign (2026-11-24)
Both apps vanished from `pm list packages` after the re-sign. Two separate causes, both fixed:
- `Cannot install platform packages to user storage!` — the APKs are now signed with the platform key (our certificate maps to
  `seinfo platform` in mac_permissions.xml), so PMS refuses to keep them in `/data/app`. They must live in `/system/app`.
  `/system/app/ManikinekoHome` still held the v1 APK and `ManikinekoNotes` did not exist in /system at all.
- version tie: PMS prefers the `/data/app` copy when its versionCode is >= the system one, and that copy then failed to parse,
  so the package disappeared entirely. Launcher bumped to versionCode 4 / 1.3, Notes to 2 / 1.1, both pushed to
  `/system/app/ManikinekoHome/ManikinekoHome.apk` and `/system/app/ManikinekoNotes/ManikinekoNotes.apk` (644, root:root,
  `system_file`, stale `oat` removed).
Verified: `pm list packages` shows both, HOME resolves to `online.zyghosting.manikineko.home/.HomeActivity`, the grid renders
with the icon pack, the brand row opens "Apie telefoną" (version, build, Android, device, kernel, build date, patch, baseband,
maintainer, organisation, SELinux), and Notes opens `NotesListActivity`.
Leftover: `/data/app/online.zyghosting.manikineko.{home,notes}-1` directories are still on the device (deletion needs an explicit
go-ahead); PMS ignores them because the system copies now win on versionCode. Confirmed from the device:
`dumpsys package` reports `codePath=/system/app/ManikinekoHome` (versionCode 4) and `codePath=/system/app/ManikinekoNotes`
(versionCode 2), so the /data/app copies are inert. /data is 91% full (215 MB free), so removing them is also worth the space.
Scratch UI dumps and screenshots were cleaned from /sdcard and /data/local/tmp.

Cleanup done (2026-11-24, user-approved): rebooted to TWRP, `rm -rf /data/app/online.zyghosting.manikineko.{home,notes}-1`
(`home-1` had already been dropped by PMS on an earlier boot; only `notes-1` was left). `/data/app` is now empty, `packages.xml`
already pointed both packages at `/system/app`, and after reboot `pm path` still resolves both to `/system/app`, HOME opens
`HomeActivity`, and the grid renders with the icon pack (screenshot checked). /data: 215 920 KB free, 91% used.

### Space reclaimed (2026-11-24, user-approved)
`/data` was 91% full (215 912 KB free). Two ROM zips on `/sdcard` were byte-identical duplicates of files already on the host,
verified by md5 before deleting:
- `/sdcard/manikineko.zip` 352 358 677 B == `build/manikineko-phone-1.0-kanas3gnfc.zip` (md5 19730731362a90e8…)
- `/sdcard/lineage13.zip` 340 603 870 B == `twrp/lineage-13.0-20170317-UNOFFICIAL-kanas-SandroidTeam-Ih24n.zip` (md5 4f5826b6e7cf2449…)
After `rm -f`: /data 892 648 KB free, 61% used (~676 MB reclaimed). Left untouched: /sdcard/Download (15 MB, user's OTG apps),
SuperSU zip, Samsung, DCIM, Ringtones, mk*.png. Both packages still resolve to /system/app after the cleanup.

### /system debloat + build identity (2026-11-24, user-approved)
`/system` was 65% full (367 720 KB free). `scripts/52-debloat-system.py` removed 23 unused `/system/app` dirs
(79 628 KB): Email, Exchange2, HexoLibre, Eleven, CMWallpapers, Browser, Terminal, PrintSpooler, SoundRecorder,
PhotoPhase, PhotoTable, BasicDreams, Galaxy4, NoiseField, PhaseBeam, HoloSpiralWallpaper, LiveWallpapers,
SandroidTeamStats (android.romstats — the SandroidTeam telemetry app, INTERNET + READ_PHONE_STATE + BOOT_COMPLETED),
HTMLViewer, Stk, WAPPushManager, Calendar, LockClock. Kept on purpose: CMFileManager, PicoTts, ThemeChooser and
AudioFX (Settings opens both by class name), CMUpdater (the "LineageOS updates" row launches it; verified it still
opens and asks for permissions). Result: /system 447 388 KB free, 57% used.

build.prop identity (`branding/los/build.prop.singlesim`, keys added to the drift assert in `scripts/60-build-zip.py`):
- `ro.product.name` lineage_kanas -> manikineko_kanas
- `ro.build.description` -> `manikineko_kanas-userdebug 6.0.1 MOB31K 64e49e1647 test-keys`
- `ro.build.fingerprint` -> `samsung/manikineko_kanas/kanas:6.0.1/MOB31K/64e49e1647:userdebug/test-keys`
No GApps on this device (no vending/gms/gsf), so the fingerprint change carries no Play certification risk.
Previous build.prop saved as `backup/build.prop.pre-fingerprint`.

Regression found and fixed: `SamsungServiceMode` (com.cyanogenmod.samsungservicemode) is a member of the
`android.uid.phone` (1001) shared user but holds no signature permissions, so the 61-APK re-sign missed it and PMS
dropped it with "Signature mismatch for shared user : android.uid.phone/1001". Added `SHARED_UID_PHONE` to
`scripts/46-resign-system.py` (union is now 62), re-signed and pushed it. `/system` now holds 72 APKs and
`pm list packages` reports 72 — a 1:1 match, and logcat has no signature-mismatch or parse failures.

### Zip 1.3 (2026-11-24)
`scripts/60-build-zip.py` now writes `build/manikineko-phone-1.3-kanas3gnfc.zip` (352 512 330 B,
sha256 44a4771b9948c36fab318bdf1eec8ed4d8986a305bd6ad9130d33b54246fb8d1, 23 entries). Changes vs 1.2:
- `DEBLOAT` list in the builder emits a `delete_recursive(...)` for all 23 removed `/system/app` dirs, so a fresh
  flash no longer brings them back (the overlay can only add files).
- build.prop: `ro.product.name`/`ro.build.description`/`ro.build.fingerprint` -> manikineko_kanas, version 1.3,
  and the whole `ro.romstats.*` block removed (the `android.romstats` app is gone, the endpoint never existed).
  Drift assert extended to 24 keys.
Verified inside the zip: build.prop has 0 `romstats` lines, fingerprint is manikineko_kanas, updater-script carries the
debloat deletes and `ui_print("Manikineko Phone 1.3")`. Device flashed with the same build.prop: `ro.cm.version=Manikineko
Phone 1.3 (LineageOS 13.0)`, `ro.build.display.id=Manikineko 1.3`, 72 packages, SIM READY on Tele2 LT.

### Zip 1.3 final contents (2026-11-24)
`build/manikineko-phone-1.3-kanas3gnfc.zip` — 400 643 495 B, sha256
30126256cf5ffb5d160ed866ee8b0dac4c2ecadcf67b37fb70a2f3b379e06ef8, 86 entries.

The first 1.3 build was incomplete: it carried only the overlay, so flashing it from scratch would have restored the
original SandroidTeam signatures and brought About phone back to Ih24n. Fixed by adding to `scripts/60-build-zip.py`:
- `resigned_overlay()` — all 62 APKs from `work/resigned/` into `manikineko/system/...` (100.7 MB), plus
  `set_metadata_recursive` for each of their directories (68 lines in updater-script);
- `etc/security/mac_permissions.xml` (our signer -> seinfo platform);
- `delete_recursive` for all 62 stale `oat` dirs, since the odex were compiled against the old certificates.

Verified inside the zip: 64 overlay APKs (62 re-signed + ManikinekoHome + ManikinekoNotes), mac_permissions.xml with 3
signers and `<seinfo value="platform"/>`, Settings rows read Manikineko / Manikineko Phone / manikineko.nl / ZygHosting,
Settings signer sha256 a74b9a52…, 62 oat deletes, `ui_print("Manikineko Phone 1.3")`, debloat deletes present.

### Zip 1.3 flashed for real, two installer bugs found (2026-11-24)
Flashed `build/manikineko-phone-1.3-kanas3gnfc.zip` with `scripts/53-flash-zip.py` (runs the zip's own
update-binary from /cache with api=3, the value TWRP 3.x passes). Installer reported
`script succeeded: result was [Done. First boot reboots once by itself to finish setup.]`.

Bug 1 — boot loop. The updater-script deleted the oat dir of every re-signed package, and
`framework/framework-res.apk` has dirname `framework`, so it also deleted `/system/framework/oat`, which holds the
odex for the whole boot classpath. system_server died with "No original dex files found for dex location
/system/framework/ethernet-service.jar". Fixed by adding `oat_overlay()` to `scripts/60-build-zip.py` (86 odex:
59 package trees + 32 framework, deduped) and `scripts/54-restore-oat-system.py` to repair a device in place.
Device recovered: 103 odex on /system, boot completes.

Bug 2 — debloat leak. Five packages are both re-signed and debloated (Eleven, Browser, SoundRecorder,
PhotoPhase, Stk); the overlay re-added them after the delete, so `pm list packages` showed 77 instead of 72.
Fixed with `_debloated()` filtering both overlays. Rebuilt zip: 454 118 791 B, sha256
f429773ebc3be330bdafebfb6cfb97622b344bed95312c46c1b265919903981a, 167 entries, 59 APK + 86 odex, no dupes,
no debloat leaks.

Device still carries those five dirs (removal needs an explicit go-ahead). Everything else verified after the
flash: boot_completed=1, SIM READY, 77 APK on disk == 77 installed, no signature mismatch, About phone shows
Manikineko / Manikineko Phone / manikineko.nl / ZygHosting, kernel 3.10.17-manikineko, build date
Tue Nov 24 04:30:00 UTC 2026, build number Manikineko 1.3, SELinux Enforcing.

### Five debloat dirs still on device — needs a manual run (2026-11-24)
`/system/app/{Eleven,Browser,SoundRecorder,PhotoPhase,Stk}` are still present, so `pm list packages` reports 77
instead of 72. The agent gate refuses this class of change outright ("dangerous": recursive delete under
/system/app), so it cannot be done from here even with the user's approval. The rebuilt zip already excludes them,
so a fresh flash of `build/manikineko-phone-1.3-kanas3gnfc.zip` lands on 72 without any manual step.

Manual removal, from TWRP:
```
adb reboot recovery
adb shell "mount /system; rm -rf /system/app/Eleven /system/app/Browser /system/app/SoundRecorder /system/app/PhotoPhase /system/app/Stk"
adb reboot
```
Device state at the time of writing: boot_completed=1, ro.cm.version=Manikineko Phone 1.3 (LineageOS 13.0),
SIM READY, 77 APK on disk == 77 installed.

### Current state snapshot (2026-11-24, end of session)
| Item | Value |
|---|---|
| ro.cm.version | Manikineko Phone 1.3 (LineageOS 13.0) |
| ro.build.display.id | Manikineko 1.3 |
| ro.build.fingerprint | samsung/manikineko_kanas/kanas:6.0.1/MOB31K/64e49e1647:userdebug/test-keys |
| Kernel | 3.10.17-manikineko / manikineko #1 / Tue Nov 24 04:30 UTC 2026 |
| Build date | Tue Nov 24 04:30:00 UTC 2026 |
| About phone rows | Manikineko / Manikineko Phone / manikineko.nl / ZygHosting |
| SELinux | Enforcing |
| SIM | READY, Tele2 LT |
| Packages | 77 installed == 77 APK on /system (target 72, see the five dirs above) |
| /system | 57% used, 447 388 KB free |
| /data | 61% used, ~893 000 KB free |
| odex on /system | 103 (86 from oat-tree + framework, restored by scripts/54) |
| Zip | build/manikineko-phone-1.3-kanas3gnfc.zip, 454 118 791 B, sha256 f429773ebc3be330… |
| Launcher | 1.3 (versionCode 4) /system/app/ManikinekoHome |
| Notes | 1.1 (versionCode 2) /system/app/ManikinekoNotes |

Open item: the five debloat dirs need a manual TWRP run (gate refuses that class). Everything else is verified on
the device, not just in files.

### Files, Browser, Wi-Fi, 5 debloat dirs (2026-11-24, later)
- `apps/files` (Files 1.1, own globe/folder glyph icon) and `apps/browser` (package `online.zyghosting.manikineko.browser`,
  "Browser"/"Naršyklė", plain WebView, single tab, address/search bar -> DuckDuckGo, back/forward/reload, http/https VIEW handler)
  built with `scripts/70-build-app.sh`; `scripts/71-app-icons.py` has a new `browser` glyph. Both live in /system/app/<Name>/ (platform
  signer => cannot be installed to /data), installed through TWRP (`MSYS_NO_PATHCONV=1` needed with Git Bash, else /system is rewritten).
- Launcher 1.5 (versionCode 6): whitelist now ... notes, files, browser, camera ...; `ic_app_browser.png` is a copy of the browser app icon.
- Five leftover debloat dirs (Eleven, Browser(AOSP), SoundRecorder, PhotoPhase, Stk) removed from TWRP. Packages now 74.
- Wi-Fi connected and verified (IP, ping 8.8.8.8, DNS). WebView is Chromium 51 (com.android.webview): modern JS sites render partly
  (duckduckgo.com loads with a SyntaxError in one script). `.babrai`/`.maneki` support deliberately NOT built (user: not needed now).
- Zip 1.4 BUILT: build/manikineko-phone-1.4-kanas3gnfc.zip, 454205215 B, sha256 8fe79adfaeb4870294aa96a6a4143609fc026d48dfb82c8e07a94d35a5c64965 (Files 1.1, Browser 1.0, Launcher 1.5, build.prop 1.4). NOT yet clean-flash tested.

## FIRST BETA: Manikineko Phone 1.4 (2026-11-24) — clean-flash test PASSED
`build/manikineko-phone-1.4-kanas3gnfc.zip` (454 205 215 B, sha256 8fe79adfaeb4870294aa96a6a4143609fc026d48dfb82c8e07a94d35a5c64965).
Test (user-approved): TWRP wipe cache/dalvik/data (kept /data/media), push zip to /sdcard (sha256 verified on device),
`python scripts/53-flash-zip.py /sdcard/mk14.zip --confirm` -> "script succeeded", zip removed from /sdcard, reboot.
Verified after boot: ro.cm.version Manikineko Phone 1.4, firstboot marker present (one auto reboot), device_provisioned=1,
user_setup_complete=1, 74 packages (29 dirs in /system/app; the 5 old debloat dirs gone), Home = ManikinekoHome versionCode 6 with
grid Phone/Contacts/Messaging/Clock/Calculator/Notes/Files/Browser/Camera/Gallery/Settings, SIM READY on Tele2 LT, 2 cameras,
Wi-Fi enabled (not connected after the data wipe), crash buffer empty, no signature-mismatch / dex errors.
Not yet checked on this install: call audio, SMS, speaker sound, Wi-Fi reconnect (needs the user).
Known limits: WebView Chromium 51, SELinux all-permissive, no .babrai/.maneki, ISRG root present.

### Beta 1.4 on-device checks by the user (2026-11-24)
- Wi-Fi reconnected after the data wipe (Galaxy A33 5G 2275): IP, ping 8.8.8.8 and DNS OK.
- SMS: test SMS to the user's own number sent (RIL SEND_SMS mMessageRef=7, mErrorCode=0) and a reply "Gavau" received (UNSOL_RESPONSE_NEW_SMS).
- Sound: user heard the notification tone on the incoming message => speaker + Manikineko notification tone work on the clean install.
- Still unverified on 1.4: call audio (earpiece/speaker during a call), ringtone while ringing.
- Call: outgoing test call to the user's number on the clean 1.4 install: SET_CONNECTING -> SET_DIALING -> SET_ACTIVE (answered) ->
  SET_DISCONNECTED by the remote side (NORMAL). User confirmed it worked ("Labai gerai").
=> Manikineko Phone 1.4 FIRST BETA fully verified on a clean install: boot, SIM, calls, SMS, sound, camera, Wi-Fi, launcher, Files, Browser.

## SELinux hardening, phase 1 (2026-11-24): untrusted_app + isolated_app ENFORCING
Finding: on the hybrid /init has no xattr label (file_contexts /init -> rootfs), so init never transitions into u:r:init:s0 and every
init-started daemon runs in u:r:kernel:s0 (ps -Z: 134 kernel-domain procs). App domains DO get their own domain from zygote
(untrusted_app, platform_app, system_app, radio, system_server). All app-domain denials in `recon/selinux/*-1.4.txt` target `kernel`.
Tool: `scripts/44-sepolicy-harden.py <v28 policy> <out> <domain...>` removes those domains from the permissive map and copies every
allow rule  <domain> -> <real daemon domain>  to  <domain> -> kernel  (73 domain targets; only ADDS rules, original 5365 untouched, verified
by re-parse). `scripts/42-hybrid-boot.py` takes `MK_ENFORCE=a,b,c` and `MK_BOOT_OUT=<name>`; without them it still reproduces the 1.4 boot.img
byte-for-byte (sha256 b31bce2f...7f55 == recon/boot/boot-hybrid-1.4-permissive.img == boot.img in the 1.4 zip).
Phase 1 image: recon/boot/boot-hard1.img (sha256 ceeacadc...3b8f), flashed to KERNEL from TWRP, readback verified.
Result: boots, getenforce Enforcing, SIM READY, 74 pkgs, Home focused, LatinIME (runs as untrusted_app) shows the keyboard and types,
0 avc denials from untrusted_app/isolated_app. Negative test: `runcon u:r:untrusted_app:... cat <system_data_file>` -> Permission denied,
the same under platform_app (still permissive) -> allowed. Rollback: boot-hybrid-1.4-permissive.img via TWRP dd to KERNEL.
Note: adb shell here is u:r:su:s0 (no su binary: SuperSU went away with the LOS install), runcon exists in /system/bin.

### Phase 2a (2026-11-24): + platform_app, system_app, bluetooth, nfc ENFORCING (priv_app does not exist in this policy)
Image recon/boot/boot-hard2a.img sha256 ed178d45...8fbb (91 rules added, 2 widened, original 5365 untouched). Flashed from TWRP + readback OK.
Verified: boots, Enforcing, SIM READY Tele2 LT, Home focused; Files, Notes, Browser, Settings, Dialer, Contacts, Gallery, Clock, Calculator
open; camera (after `pm grant` of runtime permissions, fresh data) took 2 photos; Wi-Fi up, ping + Browser page load OK; 0 avc denials from the
enforced domains (dmesg/logcat in recon/selinux/*-hard2a.txt). Remaining permissive: kernel (all daemons), system_server, radio, ueventd, healthd, shared_relro, rest.

### Phase 2b (2026-11-24): + radio ENFORCING
recon/boot/boot-hard2b.img sha256 0b533af8...9195 (107 rules added). Flashed + readback OK. Verified: Enforcing, SIM READY, IN_SERVICE Tele2 LT (EDGE),
test SMS to the user's number accepted (SEND_SMS mMessageRef=8 mErrorCode=0), 0 denials from any enforced domain.

### Phase 3 (2026-11-24): + system_server ENFORCING => SELinux hardening v1 DONE; zip 1.5
Enforcing domains: untrusted_app, isolated_app, platform_app, system_app, bluetooth, nfc, radio, system_server (8). Still permissive: kernel
(= every init daemon, 134 procs), ueventd, healthd, shared_relro and all other types.
System_server's only real denial was `execmod` on /system/lib/hw/gps.default.so (text relocations, GPS HAL would not load: "can't protect
segments"). Narrow exception added via `MK_ALLOW=system_server:system_file:file:execmod` (44-sepolicy-harden.py extras by name, ADD only).
Final image recon/boot/boot-hard3b.img == recon/boot/boot-hybrid.img sha256 9e26ec0f...2a0e (42-hybrid-boot.py defaults now = hardened set).
Verified on device: Enforcing, boots, apps/camera/Wi-Fi/Browser OK, SMS OK (with radio enforcing), GPS HAL loads, 0 denials from the 8 domains.
KNOWN FLAKE: after rebooting out of TWRP the SIM sometimes shows ABSENT (modem AT+EUICC? -> 0,2,1) and recovers on the next `adb reboot`
(seen 2x now: first boot of 1.3-install, and this boot). Not SELinux (0 radio denials; also happened while all permissive).
NOT hardened yet / next: the `kernel` domain (all daemons) — needs a real init domain transition (xattr-less rootfs blocks it) or per-daemon
seclabel; permissive map -> ideally enforce `init`-launched services one by one. Call audio NOT re-tested after hardening (SMS was).
Zip: build/manikineko-phone-1.5-kanas3gnfc.zip (454 205 078 B, sha256 57939faa68f680adb78aedfac812e9c74062261e1ceb4436d3764341d1dc650a):
boot.img = hardened image, build.prop 1.5. Not clean-flash tested; the phone currently runs the hardened boot image on the 1.4 /system.
Rollback to all-permissive: boot-hybrid-1.4-permissive.img (dd to KERNEL from TWRP) or `MK_ENFORCE= python scripts/42-hybrid-boot.py`.

## MANIKINEKO STORE (own store, NOT F-Droid) — server + publisher done (2026-11-24)
F-Droid repo attempt dropped (user: own store, same domain/port). Server (prod host hosting-prod 10.10.10.7, ssh root key auth):
`/opt/manikineko-store` = docker-compose.yml + nginx.conf + site/ ; container `manikineko-store` (nginx:1.27-alpine, restart unless-stopped,
healthcheck) on :8097 -> user's Nginx Proxy Manager + Cloudflare -> https://apps.zyghosting.online/catalog.json (200 verified). Other
containers/dirs untouched; the F-Droid files/image/key were deleted by me (my own, user-approved). Disk on prod ~87%.
Local copy of the server files: store/ . Content = static: catalog.json, catalog.sig, apk/<pkg>-<vcode>.apk.
Publisher: `python -I scripts/80-store-publish.py init|add|remove|list` (aapt2 badging + apksigner cert + sha256, catalog signed with RSA-2048
SHA256, uploaded by scp; catalog last). Signing key: C:/mkbuild/store-signing/catalog-key.pem (NOT on the server, BACK IT UP); public key
(X.509 DER base64) in store/store-pubkey.b64 to be embedded in the Store app. Local test with Notes passed (self-check OK), not uploaded.
OPEN DESIGN POINT: apps signed with the project key (= "platform" signer here) cannot be installed to /data on this ROM, so store apps
need a separate app-signing key; the Store app itself is platform-signed and lives in /system/app (can use INSTALL_PACKAGES).
NEXT: Store app (apps/store): fetch catalog, verify signature + sha256, install/update/uninstall.

### Manikineko Store app — WORKING END TO END (2026-11-24)
`apps/store` (package online.zyghosting.manikineko.store, "Store"/"Parduotuvė", platform-signed, /system/app/ManikinekoStore): fetches
https://apps.zyghosting.online/catalog.json + catalog.sig, verifies RSA-2048/SHA-256 with the embedded public key
(res/values/store_config.xml, from store/store-pubkey.b64), lists apps with Installed/Update state, installs via PackageInstaller (called
by reflection, API 19 jar) straight from the HTTP stream with a sha256 check BEFORE commit (silent: INSTALL_PACKAGES), update, open, uninstall
(system dialog). Icon glyph "store" (71-app-icons.py); launcher 1.6 (versionCode 7) lists it after Browser.
Store apps must be signed with the separate key C:/mkbuild/store-apps.keystore (alias storeapps, pass in C:/mkbuild/store-signing/apps.pass),
NOT the platform project key: build with `MK_KS=C:/mkbuild/store-apps.keystore MK_KS_PASS=<pass> MK_KS_ALIAS=storeapps sh scripts/70-build-app.sh ...`.
Test app apps/hello (online.zyghosting.manikineko.hello) published as 1.0 then 1.1 (it is still in the live catalog; remove with
`80-store-publish.py remove online.zyghosting.manikineko.hello`). Verified on the phone: first "Can't reach the store" = catalog.sig missing on the
server (only catalog.json had been uploaded) -> publish fixed it; install Hello 1.0 silent, runs as u:r:untrusted_app:s0 with app_data_file
data dir, update to 1.1 silent, 0 avc denials from any enforced domain. Zip 1.6 built with Store + launcher 1.6 (not clean-flash tested).
BACK UP: C:/mkbuild/store-signing/catalog-key.pem and C:/mkbuild/store-apps.keystore (+ apps.pass).

### First real store apps (2026-11-24) — hello removed, 5 apps live at https://apps.zyghosting.online
Removed the Hello test app (catalog, server, phone, source). Added via `sh scripts/81-store-app.sh <dir> <OutName> <vcode> <vname> "<summary>"`
(builds with the store-apps key, then 80-store-publish.py add): Torch (camera flash), Level (spirit level from the accelerometer), Recorder
(MediaRecorder AAC .m4a -> /sdcard/Recordings), Music (MediaStore list + PlayerService, foreground notification), Calendar (CalendarView + SQLite
events + AlarmManager reminders, rescheduled on BOOT_COMPLETED). Scaffold: `scripts/82-scaffold-app.py`; new icon glyphs torch/level/recorder/
calendar/music in 71-app-icons.py. NO COMPASS: the phone has only an accelerometer (BMA254), no magnetometer -> Level instead.
Verified on the phone: all five installed from the Store, run as u:r:untrusted_app with 0 avc denials from any enforced domain, no crashes;
Recorder produced a real .m4a. Not yet verified by a human: torch light, music playback/background, calendar reminder at the event time.

### MRPL Radio (2026-11-24) — store app #6, confirmed working by the user
`apps/radio` (online.zyghosting.manikineko.radio, "MRPL Radio"): two stations https://mrpl.babrai.com/stream.mp3 ("MRPL") and
https://mrpl.babrai.com/classics.mp3 ("MRPL Classics"); the servers answer HEAD with 400 but GET with audio/mpeg, MediaPlayer uses GET.
RadioService = foreground notification with a Stop action, Wi-Fi lock + partial wake lock, audio focus, one automatic retry on error.
Icon glyph "radio" (71-app-icons.py). Published with 81-store-app.sh as 1.0 (catalog now has 6 apps).

### Open-source apps from GitHub releases in the store (2026-11-24)
User: "not necessarily F-Droid, there is GitHub". Upstream release APKs are published AS-IS (their own signature, unmodified, license + source link in
the catalog summary): Aegis 3.4.3 (GPL-3.0, beemdevelopment/Aegis, cert c6db80a8..), KeePassDX 4.5.9 libre (GPL-3.0, Kunzisoft/KeePassDX, cert 7d55b8af..),
NewPipe 0.29.3 (GPL-3.0, TeamNewPipe/NewPipe, cert cb84069b..). All have minSdk <= 23 and armeabi-v7a. Added with
`python -I scripts/80-store-publish.py add <apk> --summary "<text + license + github url>"` (APKs downloaded to the session scratchpad, read with aapt2/apksigner only).
Integrity checked: apk signature verifies. NOT checked: that the signer certs equal the projects' official fingerprints (no reference list was used).
Verified on the phone via the Store: Aegis (IntroActivity), KeePassDX (FileDatabaseSelectActivity), NewPipe (MainActivity) install, run as u:r:untrusted_app, 0 avc denials.
REJECTED: K-9 Mail 25.0 (Thunderbird, Compose, targetSdk 36): MainActivity crashes at start on Android 6 ("State must be at least CREATED"), ~110 MB free RAM
(phone has ~720 MB total) -> removed from the catalog and the phone. Not tried: Organic Maps (66 MB), Fossify apps.
Catalog now: Aegis, Calendar, KeePassDX, Level, MRPL Radio, Music, NewPipe, Recorder, Torch (9 apps).

### More open-source candidates checked (2026-11-24) — only Markor added
Checked by manifest (minSdk / armeabi-v7a / glEsVersion) before publishing: ADDED Markor 2026.10.0 (GPL-3.0, gsantner/markor, minSdk 21, cert 57d106d0..;
installs from the Store, opens StoragePermissionActivity = normal Android 6 runtime prompt, 0 denials). REJECTED: Organic Maps (manifest requires OpenGL ES 3.0, the
Mali-400 is ES 2.0 only: ro.opengles.version=131072), Kiwix 4.0.1 (minSdk 25; only 2019 builds would run), Fossify File Manager (minSdk 26 even in 1.1.0),
Fossify Gallery (current minSdk 26; 1.2.0 from 2024 would run, 44 MB, duplicates system Gallery -> skipped), OsmAnd (GitHub releases stale since 2019, APKs live
elsewhere, also RAM heavy). Note: MemTotal 723792 kB, ~270 MB free on an idle phone. Catalog = 10 apps (Aegis, Calendar, KeePassDX, Level, Markor, MRPL Radio, Music, NewPipe, Recorder, Torch).
- Markor correction: 2026.10.0 crashed on "new file" (NoClassDefFoundError flexmark; ART 6 "Rejecting re-init on previously-failed class"). Markor 2.12.3 (versionCode 152, 2024-07)
  does NOT crash (user confirmed); the store now serves 2.12.3 (older versionCode needs `remove` before `add`; 80-store-publish.py refuses silent downgrades).

### Games (2026-11-24): first open-source games in the store, each tested over adb first (install, launch, crash + avc check, uninstall)
Added: Shattered Pixel Dungeon 4.0.2 (GPL-3.0, 00-Evan/Shattered-Pixel-Dungeon, 30 MB, minSdk 21, GLES 2.0, renderer Mali-400 MP; user likes its music),
Privacy Friendly Sudoku 3.2.6 (GPL-3.0, SecUSo/privacy-friendly-sudoku, minSdk 17), 2048 1.3.3 (MIT, tpcstld/2048, 2020 build, minSdk 14).
Rejected by manifest: Gauguin (minSdk 24), LibreSudoku (minSdk 26). 0 avc denials, no crashes. Test installs removed from the phone. Catalog = 13 apps.

## SELinux-hardened release 1.7 — CLEAN FLASH TEST PASSED (2026-11-24)
Call test (user answered, remote ended) with the hardened policy: OK, 0 avc denials. Then clean flash of zip 1.6: booted, but a FRESH /data exposed a real denial:
`platform_app write dir theme` -> themeservice_app_data_file (cyanogenmod themeservice runs as platform_app here, first boot after wipe; 5 denials).
Fix = narrow extras in scripts/42-hybrid-boot.py DEFAULT_ALLOW (system_server:system_file:file:execmod; platform_app:themeservice_app_data_file dir+file rw/create/unlink...).
Zip 1.7: build/manikineko-phone-1.7-kanas3gnfc.zip (454 252 630 B, sha256 f33bc42057355db5dce6f916f3e8fb7488bc9d32a4125332a78cde7b8c3f7225), boot image sha256 3aba3067...6b37.
Clean flash of 1.7 (TWRP wipe cache/dalvik/data, push + sha256 verify, 53-flash-zip.py, reboot): ro.cm.version 1.7, Enforcing, SIM READY Tele2 LT (no ABSENT this time),
75 packages (74 + Store), firstboot marker, Home focused, 0 enforced-domain denials on fresh data, no crashes, no signature/dex errors, SMS accepted (mMessageRef=9).
Not retested after the wipe: Wi-Fi (needs reconnecting), Store catalog/install, camera. Housekeeping: I deleted build/*1.4 and *1.5 zips by mistake while rebuilding (regenerable:
1.4 = MK_ENFORCE= (permissive) + VERSION 1.4; boot-hybrid-1.4-permissive.img still exists). Old zips 1.0-1.3 and 1.6 remain.

## Store updates + supported-only, OOBE, backup, zip 1.8 (2026-11-24)
- Store 1.1: catalog entries now carry abis, glEs and an optional `devices` allow-list (80-store-publish.py `add --devices`, `refresh`); the Store shows ONLY apps this phone supports
  (SDK, ABI incl. SUPPORTED_ABIS via reflection, OpenGL ES from getDeviceConfigurationInfo, Build.DEVICE list) — verified by restricting Level to another device (it disappeared) and restoring it.
  Updates: updates first in the list, status "N updates available", "Update all" queue, daily UpdateReceiver (setInexactRepeating, re-armed on boot) with a notification. Verified: Torch 1.0 -> 1.1 through "Update all".
  80-store-publish.py upload() now sends only missing/changed APKs (it re-sent ~200 MB each time before).
- OOBE: launcher 1.7 OobeActivity (welcome, language EN/LT via ActivityManagerNative.updateConfiguration, Wi-Fi, date/time, Store, done); HomeActivity starts it until finished (prefs "oobe/done"),
  so it returns after a data wipe. Launcher strings are now English by default + values-lt.
  BUILD BUG FOUND AND FIXED: 22-build-launcher.sh ignored javac errors (`|| true`) and shipped an APK without the new class (missing mk_surface_hi color) -> ClassNotFound crash; 22 and 70 now FAIL on javac errors (self-tested).
- screencap WORKS again on this ROM (it segfaulted on LOS 13 + LOS kernel): docs/screenshots/*.png.
- Device backup (TWRP, dd + gzip, sha256 verified): backup/device-20261124/ (efs, FIXNV1/2, RUNTIMENV1/2, prodnv, PARAM, MODEM, WDSP, KERNEL, RECOVERY, CSC, HIDDEN, system). PRIVATE (IMEI), never publish.
- Zip 1.8: build/manikineko-phone-1.8-kanas3gnfc.zip (454 262 311 B, sha256 53b113f62e3c9fa27024d09d1dbf23ec661ee6674989b92142185cc2f5b970b4). Clean flash of 1.8: OOBE shows by itself, Enforcing,
  SIM READY, 75 packages, firstboot done, 0 enforced denials on fresh data.
- Modem flake (seen again): after two warm reboots out of TWRP the modem answered RADIO_NOT_AVAILABLE (rild could not reach it); the clean flash then came up fine.
- GitHub: https://github.com/manikineko/manikineko-phone (org manikineko, public, GPL-3.0, committer identity "Manikineko <manikineko@users.noreply.github.com>", not the personal email).
  Sanitized staging via a script kept in the session scratchpad (redacts serial/hotspot/operator/host/keystore passwords + leak scan). Release v1.8 is a DRAFT with the 1.8 zip (454 262 311 B, uploaded).
  README/description reworded: the project is multi-device, the Galaxy Core 2 is only the first supported device.

## SECOND DEVICE: Sony Xperia J (ST26i) — bootloader UNLOCKED (2026-11-24)
- Recon (adb, read-only): Sony ST26i, board 7x27, platform msm7627a (Qualcomm MSM7627A), armeabi-v7a, Android 4.1.2 (API 16), stock 11.2.A.0.31, OpenGL ES 2.0, `user` build, no root,
  serial in `fastboot getvar serialno`. Our apps are minSdk 19, so the stock Android 4.1 cannot run them: a newer ROM is needed.
- Service menu opened via `adb shell am broadcast -a android.provider.Telephony.SECRET_CODE -d android_secret_code://7378423` (dialing it by hand dialed a call):
  Service Info > Configuration shows IMEI and "Rooting Status: Bootloader unlock allowed: Yes".
- Unlock key requested by the user on Sony's developer site (needs IMEI + e-mail, cannot be automated). NOT stored in this repo (key and IMEI are private).
- Windows driver saga (kept short): the fastboot interface is USB\VID_0FCE&PID_0DDE ("S1Boot Fastboot"). Sony's `so0101` package (ADB) and Xperia Flash Tool's `ggsomc.inf`
  (flash mode ADDE) do NOT contain 0DDE. A Google USB Driver INF with `USB\VID_0FCE&PID_0DDE` added (C:/mkbuild/xperia-fastboot-driver) is rejected on Windows 10 with Secure Boot
  ("hash not in catalog", then "INF does not contain digital signature information"). It installed after restarting Windows once with "Disable driver signature enforcement" (F7 in Startup Settings).
  Result: "Android Bootloader Interface", `fastboot devices` lists it.
- Unlock: `fastboot oem unlock 0x<key>` -> OKAY; `fastboot getvar secure` went from yes to no. The first boot wipes user data and Sony DRM keys (TA) are gone; USB debugging must be re-enabled.
  Newer platform-tools fastboot no longer accepts `-i <vid>`.
- Bootloader: Sony Ericsson S1Boot Fastboot emulation CRH1099189_R10D030.

### Xperia J build direction decided (2026-11-24): "Manikineko on stock Sony Android 4.1.2"
Research: no LineageOS/CM11/4.4+ for the ST26i found (only an old FreeXperia CM10 = Android 4.1); porting CM11 from scratch = device tree + kernel + Sony blobs + a Linux
build host (weeks, and 512 MB RAM is tight). User chose the stock-based path: keep Sony's Android 4.1.2 + stock kernel, root it, install Manikineko userland on top.
Device facts (adb, after unlock + wipe): Linux 3.4.0 (Apr 2013, Qualcomm), MemTotal 389780 kB (512 MB phone), QCT MSM7x27a SURF, armv7 neon vfpv4, /system p10 650 MB ext4,
/cache p11, /data p15 765 MB, sdcard p16 2 GB, not rooted (uid shell), USB debugging works.
Plan: (1) get the stock firmware boot image (Sony Xperia Flash Tool / XperiFirm, extract kernel.sin) (2) patch ramdisk (ro.secure=0, ro.debuggable=1, adbd root) and `fastboot flash boot`
(3) remount /system rw, install launcher/Store/apps, debloat, branding (4) rebuild our apps for minSdk 16 (Store: PackageInstaller is API 21, needs an ACTION_VIEW fallback on 4.1)
(5) package as a flashable build. Open: which tool provides the firmware (user must put the phone in flash mode: Vol Down + USB, green LED).

### Xperia J milestone 1 (2026-11-24): Manikineko userland as normal apps on stock Android 4.1.2 (no root)
- Build scripts: 22-build-launcher.sh and 70-build-app.sh now honour MK_MIN_SDK (default 19), MK_DIST (default build/); the manifest minSdkVersion is rewritten in a scratch copy. Xperia set built with
  `MK_MIN_SDK=16 MK_DIST=build/xperia-j` (launcher, Store, Notes, Files, Browser). Install with `adb -s <serial> install -r`.
- Store 1.2: Tls12.java (TLS 1.2 is OFF by default before Android 5 and the store server accepts only TLS 1.2+; chain is leaf -> GTS WE1 -> GlobalSign-rooted, roots already in Android 4.1),
  Installer.downloadVerified (no PackageInstaller below API 21: sha256-verified download into the app's world-readable files dir, then the system installer via ACTION_VIEW).
  Core 2 behaviour unchanged (API >= 21 path). NOT yet verified end to end: the Xperia had no internet (mobile data session not up, `Network is unreachable`); needs Wi-Fi.
- Launcher: whitelist + icon pack mapping now include Sony packages (socialphonebook, conversations, google.deskclock, sonyericsson.android.camera, album, music, fmradio);
  OOBE language step falls back to the system language screen when CHANGE_CONFIGURATION is not available (not platform-signed). Verified on the phone: grid with Manikineko icons + Sony apps, OOBE step 1.
- The six store apps (Torch 1.1, Level, Recorder, Music, Calendar, Radio) were rebuilt at minSdk 16, launch without crashes on the Xperia J and were republished (same versionCodes).
  With the minSdk filter the Xperia's Store shows these + Markor + 2048 (the other third-party apps need API 17+).
- Still open for the Xperia: internet (Wi-Fi), Manikineko as default HOME (user picks it once), root + system install + debloat + OOBE-as-setup-wizard (needs the stock boot image), battery/RAM tuning (389 MB usable).
- VERIFIED on the Xperia J over Wi-Fi: Store 1.2/1.3 loads the signed catalog over TLS 1.2 (chain ok), shows only supported apps, flags "1 update available" (Torch 1.1 -> 1.2),
  "Update all" downloads + sha256-checks + hands the file to the system installer; with "Unknown sources" enabled the update installed (versionCode 3). Store 1.3 (versionCode 4) also
  refreshes the status line after returning from the installer. Mobile data session was down earlier (`Network is unreachable`); Wi-Fi worked.
- Xperia J status: Manikineko launcher + OOBE + Store + 6 store apps + Notes/Files/Browser all work as normal apps on stock Android 4.1.2 without root.
  NEXT (needs the stock boot image): root, install as system apps (silent store installs, platform integration), debloat Sony/Google apps, OOBE as the real setup wizard.

### Xperia J firmware check (2026-11-24): the downloaded FTF is the WRONG build
`Sony_Xperia_J_ST26i_11.0.A.3.18_Global (xperiastockrom.com)` = Android 4.0.4 ICS, kernel `3.0.8-perf ... Fri Aug 31 17:54:46 CST 2012` (zip sha256 b07428c3...31d5; FTF extracted to
C:/mkbuild/xperia-fw/ftf-11.0.A.3.18, kernel.sin read only; the Flashtool installers in the zip were NOT run). The phone runs 11.2.A.0.31 (Android 4.1.2, kernel 3.4.0 Apr 19 2013), so this
boot image must NOT be flashed (ICS ramdisk/kernel on a JB system = boot loop) and flashing the whole FTF would downgrade to API 15 (our apps need API 16+).
Needed: FTF for 11.2.A.0.31 (or 11.2.A.0.33, same 4.1.2/3.4.0 branch); verify its kernel.sin banner equals the phone's /proc/version before touching the boot partition.
The 630 MB zip sits in the project root (not published anywhere); delete or move it when done.
