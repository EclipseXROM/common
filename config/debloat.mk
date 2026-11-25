#
# EclipseX debloat - product-level strip of AOSP/Google bundled apps.
#
# IMPORTANT: include this file LAST in your product makefile chain.
# $(filter-out) can only remove entries already present in
# PRODUCT_PACKAGES at include time.
#
# Module names (not java package names) are filtered. Names follow
# AOSP convention; verify against your branch if a name changed.
#
# This is a safety net: the manifest's debloat.xml already removes the
# SOURCE of everything below, so most entries are no-ops - they only
# matter when a product mk still lists a module whose repo is gone
# (that would be a build error otherwise).
#

# --- Google-branded / search / ads -----------------------------------------
ECLIPSEX_DEBLOAT := \
    QuickSearchBox \
    QuickAccessWallet \
    OnDeviceAppPrediction \
    SampleLocationAttribution \
    DeviceDiagnostics \
    com.android.adservices \
    com.android.ondevicepersonalization

# --- AOSP stock apps replaced by the EclipseX suite -------------------------
ECLIPSEX_DEBLOAT += \
    Browser2 \
    Calendar \
    AvatarPicker \
    Gallery \
    Gallery2 \
    Music \
    MusicFX \
    HTMLViewer \
    LegacyCamera

# --- Remaining stock/utility bloat (source removed in debloat.xml) ---------
ECLIPSEX_DEBLOAT += \
    DeskClock \
    Messaging \
    Stk \
    EmergencyInfo \
    SafetyRegulatoryInfo \
    SettingsIntelligence \
    PrivateSpace \
    ImsServiceEntitlement

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

# Kept on purpose (compatibility surface - do NOT add to the list):
#   WebView / chromium-webview   WebView API used by countless apps
#   DocumentsUI                  SAF picker backend (ACTION_OPEN_DOCUMENT)
#   KeyChain, CertInstaller      credential storage / cert install APIs
#   ManagedProvisioning          work-profile / device-owner provisioning
#   CarrierConfig                carrier settings database
#   CellBroadcastReceiver        emergency alerts (regulatory)
#   Contacts / providers         PIM APIs and content providers
#   Dialer, BasicSmsReceiver, PhoneCommon
#                                telephony + emergency-call surface
#   SecureElement                NFC/secure-element API surface
#   StorageManager               storage settings surface
#   SystemUI / SystemUIGo        system UI (Go variant for low-RAM)
#   CaptivePortalLogin, Provision  boot/setup flow
#   StatsD, Permission, SdkExtensions, ExtServices, IntentResolver,
#   MediaProvider, all other packages/modules/*
#                                API surface + runtime - removal breaks
#                                CTS and/or third-party apps

PRODUCT_PACKAGES := $(filter-out $(ECLIPSEX_DEBLOAT),$(PRODUCT_PACKAGES))
