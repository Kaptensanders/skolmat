"""
    Skolmat custom component - Anders Sandberg
"""

import voluptuous as vol
from .menu import Menu
from datetime import datetime, timedelta
from logging import getLogger

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.entity import generate_entity_id
from homeassistant.helpers.aiohttp_client import async_get_clientsession


log = getLogger(__name__)
AP_ENTITY_DOMAIN = "skolmat"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required("name"): cv.string,
        vol.Optional("url"): cv.string,
        vol.Optional("rss"): cv.string
    }
)

async def async_setup_platform(hass, conf, async_add_entities, discovery_info=None):
    sensor = SkolmatSensor(hass, conf)
    async_add_entities([sensor])
  
class SkolmatSensor(RestoreEntity):
    def __init__(self, hass, conf):
        super().__init__()
        self.hass               = hass # will be set again by homeassistant after added to hass     
        self._name              = conf.get("name")
        self._state             = None
        self._state_attributes  = {}
        self.entity_id          = generate_entity_id  (
            entity_id_format = AP_ENTITY_DOMAIN + '.{}',
            name = self._name,
            hass = hass
        )

        url = conf.get("url", None)
        if not url:
            raise KeyError("'url' config parameter missing")

        self.menu = Menu.createMenu(hass.async_add_executor_job, url)
    
    @property
    def name(self):
        return self._name
    @property
    def icon(self):
        return "mdi:food"
    @property
    def state(self):
        return self._state
    @property
    def extra_state_attributes(self):
        return self._state_attributes
    
    @property
    def force_update(self) -> bool:
        # Write each update to the state machine, even if the data is the same.
        return False
    @property
    def should_poll(self) -> bool:

        if isinstance(self.menu.last_menu_fetch, datetime):
            
            now = datetime.now()

            if now.date() != self.menu.last_menu_fetch.date():
                return True
        
            if now - self.menu.last_menu_fetch >= timedelta(hours=4):
                return True
            
            return False

        return True

    async def async_update(self):

        bResult = await self.menu.loadMenu(async_get_clientsession(self.hass))
        if bResult:
            if not self.menu.menuToday:
                self._state = "Ingen mat"
            else:
                self._state = "\n".join(self.menu.menuToday)
            
            self._state_attributes = {
                "calendar": self.menu.menu,
                "name": self._name
            }

    async def async_added_to_hass(self):
        # Restore state
        last_state = await self.async_get_last_state()
        if last_state:
            # Restore the calendar attribute
            self._state = last_state.state

            self._state_attributes = last_state.attributes.copy()
        else:
            log.info(f"No previous state found for {self._name}")

