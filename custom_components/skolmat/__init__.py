"""The Skolmat integration."""

from __future__ import annotations

import logging
import importlib
import sys
from hashlib import sha1
from typing import Any
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from .const import DOMAIN, CONF_URL, CONF_PROCESSOR_FILE, CONF_PROCESSOR_FN
from .menu import Menu

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.CALENDAR]

async def _load_processor(
    hass: HomeAssistant,
    processor_file: str | None,
    processor_fn: str | None,
):
    if not processor_file and not processor_fn:
        return None
    if not processor_file or not processor_fn:
        _LOGGER.warning("Processor config incomplete; skipping processor load.")
        return None

    filename = processor_file.strip()
    if not filename:
        _LOGGER.warning("Processor file name empty; skipping processor load.")
        return None
    if not filename.endswith(".py"):
        filename = f"{filename}.py"

    processor_path = Path(__file__).resolve().parent / "processors" / filename
    if not processor_path.exists():
        _LOGGER.warning("Processor file not found: %s", processor_path)
        return None

    module_name = f"custom_components.skolmat.processors.{processor_path.stem}"

    def _import_with_alias(name: str):
        try:
            menu_module = importlib.import_module("custom_components.skolmat.menu")
            sys.modules.setdefault("menu", menu_module)
        except Exception:
            pass
        return importlib.import_module(name)

    try:
        module = await hass.async_add_executor_job(_import_with_alias, module_name)
    except Exception as exc:
        _LOGGER.warning("Processor import failed: module=%s error=%s", module_name, exc)
        return None

    processor = getattr(module, processor_fn.strip(), None)
    if not callable(processor):
        _LOGGER.warning("Processor function missing/not callable: %s.%s", module_name, processor_fn)
        return None

    return processor


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    url: str = entry.data[CONF_URL].rstrip(" /")
    url_hash = sha1(url.encode("utf-8")).hexdigest()

    config = dict(entry.data)
    for key, value in entry.options.items():
        if value is None:
            continue
        if isinstance(value, str) and value == "":
            continue
        config[key] = value
    processor_cb = await _load_processor(
        hass,
        config.get(CONF_PROCESSOR_FILE),
        config.get(CONF_PROCESSOR_FN),
    )
    if processor_cb:
        _LOGGER.info(
            "Processor active: %s.%s",
            config.get(CONF_PROCESSOR_FILE),
            config.get(CONF_PROCESSOR_FN),
        )
    menu = Menu.createMenu(hass.async_add_executor_job, url, customMenuEntryProcessorCB=processor_cb)
    menu.setSummaryFilters(config)

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
