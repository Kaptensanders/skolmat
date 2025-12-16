"""Sensor platform for Skolmat."""

from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, CONF_NAME, CONF_URL
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

    def __init__(self, hass, entry, menu, url_hash):
        self.hass = hass
        self._entry = entry
        self._menu = menu

        self._name = entry.data[CONF_NAME]
        self._url = entry.data[CONF_URL]

        self._attr_unique_id = f"skolmat_sensor_{url_hash}"

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
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._name,
            manufacturer="Skolmat",
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
        await self._menu.loadMenu(session)

        today_courses = self._menu.menuToday or []

        if not today_courses:
            state = "Ingen meny idag"
        else:
            state = ", ".join(today_courses)

        if len(state) > 255:
            state = state[:252] + "..."

        self._state = state

        self._attrs = {
            "url": self._url,
            "updated": datetime.now().isoformat(),
            "calendar": self._menu.menu,
            "name": self._name,
        }
