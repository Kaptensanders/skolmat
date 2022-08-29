"""
    Avanza Personal - Anders Sandberg
"""

import feedparser, voluptuous as vol
from .menu import Menu
from datetime import datetime
from logging import getLogger

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity, generate_entity_id
from homeassistant.const import EVENT_HOMEASSISTANT_STOP

log = getLogger(__name__)
AP_ENTITY_DOMAIN = "skolmat"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required("name"): cv.string,
        vol.Required("rss"): cv.string
    }
)

async def async_setup_platform(hass, conf, async_add_entities, discovery_info=None):

    sensor = SkolmenySensor(hass, conf)
    async_add_entities([sensor])
  
class SkolmenySensor(Entity):
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

        self.menu               = Menu(rss = conf.get("rss"))
    
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
    def device_state_attributes (self):
        # just in for bw compability in case needed, extra_state_attributes is used since 2012.12.x
        return self._state_attributes
    
    @property
    def force_update(self) -> bool:
        # Write each update to the state machine, even if the data is the same.
        return False
    @property
    def should_poll(self) -> bool:
        if isinstance(self.menu.last_menu_fetch, datetime):
            return self.menu.last_menu_fetch.date() != datetime.now().date()
        return True

    async def async_update(self):
        await self.hass.async_add_executor_job(self.loadMenu)

    # does io, call in separate 
    def loadMenu(self):

        try:
            self.menu.loadMenu()

            if self.menu.menuToday is None:
                self._state = "Ingen mat"
            else:
                self._state = "\n".join(self.menu.menuToday)
            
            self._state_attributes = {
                "calendar": self.menu.menu,
                "name": self._name
            }
        
        except Exception as e: 
            log.critical (f"Error fetching/parsing {self._rss}\n{e}")
