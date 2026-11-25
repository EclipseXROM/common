#
# EclipseX debloat - product-level strip of AOSP/Google bundled apps.
#
# IMPORTANT: include this file LAST in your product makefile chain.
# $(filter-out) can only remove entries already present in
# PRODUCT_PACKAGES at include time.
#
# Module names (not java package names) are filtered. Names follow
# AOSP convention; verify against your branch with
#     m nothing && grep in out/... for installed module names
#
# The heavier, repo-level strip lives in the manifest's debloat.xml.
# The runtime, on-device strip tool is debloat/debloat.sh.
#

# --- Google-branded / search / ads -----------------------------------------
ECLIPSEX_DEBLOAT := \
    QuickSearchBox \
    QuickAccessWallet \
    OnDeviceAppPrediction \
    SampleLocationAttribution \
    DeviceDiagnostics

# --- AOSP stock apps replaced by the EclipseX suite -------------------------
ECLIPSEX_DEBLOAT += \
    Browser2 \
    Calendar \
    DeskClock \
    Gallery \
    Gallery2 \
    Music \
    MusicFX \
    HTMLViewer \
    LegacyCamera

# --- Dev / demo / leftover apps ---------------------------------------------
ECLIPSEX_DEBLOAT += \
    SpareParts \
    Protips \
    Traceur \
    Tag \
    EyeDropper \
    DevCamera \
    Multiuser \
    UniversalMediaPlayer

# --- Launchers / theming replaced by EclipseXHome ---------------------------
ECLIPSEX_DEBLOAT += \
    Launcher3 \
    Launcher3QuickStep \
    Launcher3ResLib \
    ThemePicker \
    WallpaperPicker2 \
    WallpaperPicker

# --- TV / automotive apps (no-op on phone targets) ---------------------------
ECLIPSEX_DEBLOAT += \
    TV \
    TvSettings \
    TvSystemUI \
    TvFeedbackConsent

# --- Caveat group (enabled, review before shipping) ---------------------------
# These drop a named feature or a carrier/compliance surface:
#   Stk                  - SIM Toolkit UI (some carrier certifications want it)
#   Messaging            - default SMS role holder; keep if you ship no SMS app
#   EmergencyInfo        - emergency medical info screen
#   SafetyRegulatoryInfo - regulatory marks (regional compliance)
#   PrivateSpace         - Android 15+ private space feature
#   SettingsIntelligence - settings search suggestions (search still works)
ECLIPSEX_DEBLOAT += \
    PrivateSpace \
    SettingsIntelligence

# Kept on purpose (compatibility surface - do NOT add to the list):
#   WebView / chromium-webview   WebView API used by countless apps
#   DocumentsUI                  SAF picker backend (ACTION_OPEN_DOCUMENT)
#   KeyChain, CertInstaller      credential storage / cert install APIs
#   ManagedProvisioning          work-profile / device-owner provisioning
#   CarrierConfig                carrier settings database
#   CellBroadcastReceiver        emergency alerts (regulatory)
#   Contacts / providers         PIM APIs and content providers
#   Dialer, BasicSmsReceiver     telephony + emergency-call surface
#   SecureElement, Stk, Messaging, EmergencyInfo, SafetyRegulatoryInfo
#                                see caveat notes above
#   StorageManager               storage settings surface
#   SystemUI / SystemUIGo        system UI (Go variant for low-RAM)
#   StatsD, Permission, SdkExtensions, ExtServices, IntentResolver,
#   MediaProvider, all packages/modules/* platform modules
#                                API surface + runtime - removal breaks
#                                CTS and/or third-party apps
#   AdServices, OnDevicePersonalization
#                                Privacy Sandbox APIs; see debloat.xml
#                                group "google-ads" to strip the source.

PRODUCT_PACKAGES := $(filter-out $(ECLIPSEX_DEBLOAT),$(PRODUCT_PACKAGES))
