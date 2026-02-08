"""Sensor platform for Skolmat."""

from __future__ import annotations

from datetime import datetime, date
import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.util import slugify

from .const import DOMAIN, CONF_NAME, CONF_URL, CONF_PROVIDER
from .menu import Menu

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    menu: Menu = data["menu"]
    url_hash: str = data["url_hash"]

    add_entities(
        [
            SkolmatSensor(
                hass=hass,
                entry=entry,
                menu=menu,
                url_hash=url_hash,
            )
        ],
        update_before_add=True,
    )

class SkolmatSensor(RestoreEntity, SensorEntity):

    _attr_icon = "mdi:food"
    _attr_translation_key = "menu"

    def __init__(self, hass, entry, menu:Menu, url_hash):
        self.hass = hass
        self._entry = entry
        self._menu = menu

        self._name = entry.data[CONF_NAME]
        self._url = entry.data[CONF_URL]

        name_slug = slugify(self._name) or "unnamed"
        self._attr_unique_id = f"skolmat_sensor_{name_slug}_{entry.entry_id}"
        self._attr_available = True

        self._state: str | None = None
        self._attrs: dict[str, Any] = {}

    @property
    def name(self):
        return self._name

    @property
    def native_value(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._attrs

    @property
    def device_info(self):
        model = self._entry.data.get(CONF_PROVIDER) or getattr(self._menu, "provider", None)
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._name,
            manufacturer="Skolmat",
            model=model,
        )

    async def async_added_to_hass(self):
        # Restore state
        await super().async_added_to_hass()

        last = await self.async_get_last_state()
        if last is not None:
            self._state = last.state
            self._attrs = dict(last.attributes)

    async def async_update(self) -> None:

        session = async_get_clientsession(self.hass)
        menu_data = await self._menu.getMenu(session)
        if menu_data is None:
            self._attr_available = False
            return
        self._attr_available = True

        today_key = date.today().isoformat()
        if not menu_data.get(today_key):
            state = "no_food_today"
        else:
            state = self._menu.getReadableTodaySummary()

        if len(state) > 255:
            state = state[:252] + "..."

        self._state = state

        self._attrs = {
            "provider": self._menu.provider,
            "url": self._url,
            "updated": datetime.now().isoformat(),
            "calendar": menu_data,
            "name": self._name,
        }
