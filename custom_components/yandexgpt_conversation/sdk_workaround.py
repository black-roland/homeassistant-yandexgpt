"""Workaround for the Yandex.Cloud SDK dependencies BS 💩."""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from homeassistant.util import package as pkg_util
from .const import LOGGER

# Details:
# https://github.com/black-roland/homeassistant-yandexgpt/issues/32
#
# The history of "we don't give a 💩 and don't test our SDK":
# https://github.com/yandex-cloud/python-sdk/issues?q=is%3Aissue%20dependencies%20OR%20requirements%20OR%20constraints
REQUIRED_PACKAGES = [
    "yandex-cloud-ml-sdk==0.12.0",
    "yandexcloud==0.353.0",
    "protobuf>=6.31.1",
]


def is_latest_sdk_installed() -> bool:
    """Check if the required versions of SDKs are installed."""
    try:
        for package in REQUIRED_PACKAGES:
            if not pkg_util.is_installed(package):
                LOGGER.debug("Package %s is not installed or not in the required version.", package)
                return False

        LOGGER.debug("All required Yandex Cloud SDK packages are installed in correct versions.")
        return True
    except Exception as e:
        LOGGER.warning("Error checking SDK package installation status: %s", e)
        return False


def upgrade_sdk() -> bool:
    """Use pkg_util to install the required versions of the SDKs."""

    # Empty args to avoid setting any package constraints
    _pip_kwargs = {}

    success = True
    for package in REQUIRED_PACKAGES:
        try:
            LOGGER.info("Attempting to install/upgrade Yandex Cloud SDK package: %s", package)

            install_success = pkg_util.install_package(package, **_pip_kwargs)
            if not install_success:
                LOGGER.error("Failed to install/upgrade Yandex Cloud SDK package: %s", package)
                success = False
                continue

            LOGGER.info("Successfully installed/upgraded Yandex Cloud SDK package: %s", package)
        except Exception as e:
            LOGGER.exception("Exception occurred while installing/upgrading package %s: %s", package, e)
            success = False
    return success
