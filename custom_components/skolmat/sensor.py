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

        self._attr_unique_id = f"skolmat_{abs(hash(url))}"
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

        if self.menu.isMenuValid():
            return False
        
        return True

    async def async_update(self):

        bResult = await self.menu.loadMenu(async_get_clientsession(self.hass))
        if bResult:
            if not self.menu.menuToday:
                self._state = "Ingen mat"
            else:

                # state can only be 255 chars, if longer, truncate each item equally
                state = ("\n".join(self.menu.menuToday))
                if len(state) > 255:
                    maxCourseLength = (255 // len(self.menu.menuToday)) - 5 # ...\n
                    courses = []
                    for i in range(len(self.menu.menuToday)):
                        if len(self.menu.menuToday[i]) >= maxCourseLength:
                            courses.append(self.menu.menuToday[i][:maxCourseLength] + "...")
                        else: 
                            courses.append(self.menu.menuToday[i])

                    state = "\n".join(courses)
                        
                self._state = state
            
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

