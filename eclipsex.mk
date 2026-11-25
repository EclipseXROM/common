#
# EclipseX common product configuration.
#
# Provides the merged Manikineko userland: first-party app suite,
# EclipseX Home (launcher + OOBE), the signed app Store, branding
# assets, and the bloat strip.
#
# Inherit from a device product makefile:
#     $(call inherit-product, vendor/eclipsex/common/eclipsex.mk)
#

ECLIPSEX_COMMON := vendor/eclipsex/common

# ---- First-party app suite ----------------------------------------------
PRODUCT_PACKAGES += \
    EclipseXHome \
    EclipseXStore \
    EclipseXBrowser \
    EclipseXCalendar \
    EclipseXFiles \
    EclipseXLevel \
    EclipseXMusic \
    EclipseXNotes \
    EclipseXRadio \
    EclipseXRecorder \
    EclipseXTorch

# Privileged-permission allowlist for the apps above.
PRODUCT_COPY_FILES += \
    $(ECLIPSEX_COMMON)/config/privapp-permissions-eclipsex.xml:$(TARGET_COPY_OUT_PRODUCT)/etc/permissions/privapp-permissions-eclipsex.xml

# ---- Bloat strip ----------------------------------------------------------
# Removes AOSP/Google bundled apps from PRODUCT_PACKAGES. Set
# ECLIPSEX_NO_DEBLOAT := true in the device mk BEFORE inheriting this file
# to keep the full AOSP app set.
ifneq ($(ECLIPSEX_NO_DEBLOAT),true)
$(call inherit-product, $(ECLIPSEX_COMMON)/config/debloat.mk)
endif
