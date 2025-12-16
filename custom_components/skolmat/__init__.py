"""The Skolmat integration."""

from __future__ import annotations

import logging
from hashlib import sha1
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from .const import DOMAIN, CONF_URL
from .menu import Menu

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.CALENDAR]


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """YAML configuration is no longer supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    url: str = entry.data[CONF_URL].rstrip(" /")
    url_hash = sha1(url.encode("utf-8")).hexdigest()

    menu = Menu.createMenu(hass.async_add_executor_job, url)

    hass.data[DOMAIN][entry.entry_id] = {
        "menu": menu,
        "url_hash": url_hash,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
