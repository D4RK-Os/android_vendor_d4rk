# Increase Havoc-OS Version with each major release.
HAVOC_VERSION := 3.0-END

HAVOC_BUILD_DATE := $(shell date -u +%Y%m%d)

# Build type
ifndef HAVOC_BUILD_TYPE
    HAVOC_BUILD_TYPE := Official
endif

# Build variant
HAVOC_BUILD_VARIANT := Vanilla

# Internal version
LINEAGE_VERSION := D4RK-Os-v$(HAVOC_VERSION)-$(shell date +%Y%m%d)-$(LINEAGE_BUILD)-$(HAVOC_BUILD_TYPE)-$(HAVOC_BUILD_VARIANT)

# Display version
LINEAGE_DISPLAY_VERSION := D4RK-Os-v$(HAVOC_VERSION)-$(LINEAGE_BUILD)
