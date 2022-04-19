"""
    Avanza Personal - Anders Sandberg
"""

import feedparser, voluptuous as vol
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
        vol.Required("rss"): cv.string,
        # first, second, both - formats the state from the available course alternatives (normal/veg)
        # courses will be separated with "|" 
        vol.Optional("format", default = "first"): cv.string 
    }
)

async def async_setup_platform(hass, conf, async_add_entities, discovery_info=None):

    sensor = SkolmenySensor(hass, conf)
    async_add_entities([sensor])
  
class SkolmenySensor(Entity):
    def __init__(self, hass, conf):
        super().__init__()
        self.hass               = hass # will be set again by homeassistant after added to hass
        self._rss               = conf.get("rss")
        self._weeks             = 2
        self._name              = conf.get("name")
        self._stateFormat       = conf.get("format")
        self._last_menu_fetch   = None
        self._state             = None
        self._state_attributes  = {}
        self.entity_id          = generate_entity_id  (
            entity_id_format = AP_ENTITY_DOMAIN + '.{}',
            name = self._name,
            hass = hass
        )
    
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
    def device_state_attributes(self):
        return self._state_attributes
    @property
    def force_update(self) -> bool:
        # Write each update to the state machine, even if the data is the same.
        return False
    @property
    def should_poll(self) -> bool:
        if isinstance(self._last_menu_fetch, datetime):
            return self._last_menu_fetch.date() != datetime.now().date()
        return True

    async def async_update(self):
        await self.hass.async_add_executor_job(self.loadMenu)

    # does io, call in separate 
    def loadMenu(self):
        global last_load_date
        try:
            menu = feedparser.parse(f"{self._rss}?limit={self._weeks}")
            calendar = {}
            today = datetime.now().date()
            menuToday = None
            for day in menu["entries"]:
                weekday = day['title'].split()[0]
                date = datetime(day['published_parsed'][0], day['published_parsed'][1], day['published_parsed'][2]).date()
                week = date.isocalendar().week
                if not week in calendar:
                    calendar[week] = []
                dayEntry = {
                    "weekday": weekday,
                    "date" : date.isoformat(),
                    "week": date.isocalendar().week,
                    "courses": day['summary'].split('<br />')
                }
                calendar[week].append(dayEntry)
                if date == today:
                    if self._stateFormat == "first":
                        menuToday = dayEntry["courses"][0]
                    elif self._stateFormat == "second":
                        menuToday = dayEntry["courses"][1] if len(dayEntry["courses"]) > 1  else dayEntry["courses"][0]
                    else: #"both"
                        menuToday = "\n".join(dayEntry["courses"])
                
                if menuToday is None:
                    self._state = "Ingen mat"
                else:
                    self._state = menuToday
            
            self._state_attributes = {
                "calendar": calendar,
                "name": self._name
            }

            self._last_menu_fetch = datetime.now()
        
        except Exception as e: 
            log.error (f"Error fetching/parsing {self._rss}\n{e}")
