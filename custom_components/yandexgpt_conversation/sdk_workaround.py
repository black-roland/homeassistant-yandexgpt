# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Install the Yandex AI Studio SDK without downgrading protobuf.

Home Assistant 2026.10 pins protobuf 7. yandexcloud still declares
protobuf>=6.31.1,<7, so the resolver rejects yandex-ai-studio-sdk. The
shipped stubs are gencode 6.31.1 / grpc 1.78 and load on a newer runtime,
so the pin is metadata only. Installing those two wheels with --no-deps
keeps Home Assistant's protobuf and grpcio.

Do not install them without constraints instead: uv would downgrade
protobuf to satisfy yandexcloud and break other integrations.
"""

from __future__ import annotations

import importlib
import os
import site
import sys
from subprocess import PIPE, Popen
from urllib.parse import urlparse

from homeassistant.bootstrap import async_mount_local_lib_path
from homeassistant.core import HomeAssistant
from homeassistant.requirements import pip_kwargs
from homeassistant.util import package as pkg_util

from .const import LOGGER

# yandex-ai-studio-sdk 0.22.1 requires yandexcloud>=0.389.0. 0.412.0 is the
# release pip would select; both still pin protobuf<7.
NO_DEPS_REQUIREMENTS = (
    "yandexcloud==0.412.0",
    "yandex-ai-studio-sdk==0.22.1",
)


async def async_ensure_sdk(hass: HomeAssistant) -> bool:
    """Install SDK wheels that cannot be resolved against Home Assistant's protobuf pin."""
    missing = [req for req in NO_DEPS_REQUIREMENTS if not pkg_util.is_installed(req)]
    if not missing:
        return True

    skipped = set(hass.config.skip_pip_packages)
    if hass.config.skip_pip or any(
        (parsed := pkg_util.parse_requirement_safe(req)) is not None and parsed.name in skipped
        for req in missing
    ):
        LOGGER.error("YandexGPT dependencies are not installed: %s", ", ".join(missing))
        return False

    if not pkg_util.is_virtual_env():
        await async_mount_local_lib_path(hass.config.config_dir)

    installed = await hass.async_add_executor_job(
        _install_missing, missing, hass.config.config_dir
    )
    if installed:
        importlib.invalidate_caches()
    return installed


def _install_missing(requirements: list[str], config_dir: str) -> bool:
    """Install requirements with --no-deps so protobuf is not downgraded."""
    kwargs = pip_kwargs(config_dir)
    target = kwargs.get("target")
    timeout = kwargs.get("timeout")
    for requirement in requirements:
        LOGGER.info("Installing %s without dependency resolution", requirement)
        if not _install_no_deps(requirement, target=target, timeout=timeout):
            return False
    return True


def _install_no_deps(
    package: str, *, target: str | None, timeout: int | None
) -> bool:
    """Install one wheel the way Home Assistant does, plus --no-deps."""
    env = os.environ.copy()
    args = [
        sys.executable,
        "-m",
        "uv",
        "pip",
        "install",
        "--quiet",
        "--no-deps",
        "--upgrade",
        "--index-strategy",
        "unsafe-first-match",
        package,
    ]
    if timeout:
        env["HTTP_TIMEOUT"] = str(timeout)
    if target:
        args += ["--target", os.path.abspath(target)]
    elif (
        not pkg_util.is_virtual_env()
        and "UV_SYSTEM_PYTHON" not in env
        and "UV_PYTHON" not in env
        and (user_site := site.getusersitepackages())
    ):
        args += ["--python", sys.executable, "--target", user_site]

    if (stderr := _run_uv(args, env)) is None:
        return True

    extra_urls = env.get("UV_EXTRA_INDEX_URL", "").split()
    failing = {
        url: host
        for url in extra_urls
        if (host := urlparse(url).hostname) and host in stderr
    }
    if failing:
        LOGGER.warning(
            "Unable to install package %s using extra index host %s: %s; retrying without it",
            package,
            ", ".join(failing.values()),
            stderr,
        )
        retry_env = env.copy()
        if remaining := [url for url in extra_urls if url not in failing]:
            retry_env["UV_EXTRA_INDEX_URL"] = " ".join(remaining)
        else:
            del retry_env["UV_EXTRA_INDEX_URL"]
        if (stderr := _run_uv(args, retry_env)) is None:
            return True

    LOGGER.error("Unable to install package %s: %s", package, stderr)
    return False


def _run_uv(args: list[str], env: dict[str, str]) -> str | None:
    """Run uv and return stderr when the command fails."""
    LOGGER.debug("Running uv pip command: args=%s", args)
    with Popen(
        args,
        stdin=PIPE,
        stdout=PIPE,
        stderr=PIPE,
        env=env,
        close_fds=False,
    ) as process:
        _, stderr = process.communicate()
        if process.returncode != 0:
            return stderr.decode("utf-8").lstrip().strip()
    return None
