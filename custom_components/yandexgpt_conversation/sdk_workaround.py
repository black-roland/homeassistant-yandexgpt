"""Workaround for the Yandex.Cloud SDK dependencies BS 💩."""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import asyncio

from homeassistant.bootstrap import async_mount_local_lib_path
from homeassistant.config import get_default_config_dir
from homeassistant.requirements import pip_kwargs
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

    LOGGER.warning(
        "Этой интеграции требуется старая версия Protobuf из-за чего могут "
        "возникать конфликты с другими компонентами Home Assistant.\n"
        "Иногда это может влиять на работу других интеграций (например, ESPHome).\n"
        "Это ограничение Yandex Cloud SDK. Для постоянного решения команде "
        "Yandex Cloud SDK необходимо добавить поддержку Protobuf 6.x. "
        "Пожалуйста, поддержите issue на GitHub, чтобы ускорить исправление:\n"
        "https://github.com/yandex-cloud/python-sdk/issues/151"
    )

    # Get config directory
    config_dir = get_default_config_dir()

    # Mount local lib path if not in a virtual environment
    if not pkg_util.is_virtual_env():
        asyncio.run(async_mount_local_lib_path(config_dir))

    # Get pip kwargs
    _pip_kwargs = pip_kwargs(config_dir)

    success = True
    for package in REQUIRED_PACKAGES:
        try:
            LOGGER.info("Attempting to install/upgrade YandexGPT dependency: %s", package)

            # Use empty kwargs for yandex packages, otherwise use pip_kwargs
            package_kwargs = {} if "yandex" in package else _pip_kwargs
            LOGGER.debug("Contraints for package %s: %s", package, package_kwargs.get("constraints", "None"))

            install_success = pkg_util.install_package(package, **package_kwargs)
            if not install_success:
                LOGGER.error("Failed to install/upgrade YandexGPT dependency: %s", package)
                success = False
                continue

            LOGGER.info("Successfully installed/upgraded YandexGPT dependency: %s", package)
        except Exception as e:
            LOGGER.exception("Exception occurred while installing/upgrading package %s: %s", package, e)
            success = False
    return success
