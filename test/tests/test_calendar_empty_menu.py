import asyncio
import importlib.util
import sys
import types
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CALENDAR_PATH = ROOT / "custom_components" / "skolmat" / "calendar.py"


def _install_homeassistant_stubs() -> None:
    if "homeassistant" in sys.modules:
        return

    homeassistant = types.ModuleType("homeassistant")
    components = types.ModuleType("homeassistant.components")
    calendar_mod = types.ModuleType("homeassistant.components.calendar")
    core_mod = types.ModuleType("homeassistant.core")
    config_entries_mod = types.ModuleType("homeassistant.config_entries")
    helpers_mod = types.ModuleType("homeassistant.helpers")
    entity_mod = types.ModuleType("homeassistant.helpers.entity")
    aiohttp_client_mod = types.ModuleType("homeassistant.helpers.aiohttp_client")
    storage_mod = types.ModuleType("homeassistant.helpers.storage")
    util_mod = types.ModuleType("homeassistant.util")
    dt_mod = types.ModuleType("homeassistant.util.dt")

    class CalendarEntity:
        @property
        def available(self):
            return getattr(self, "_attr_available", True)

        async def async_added_to_hass(self):
            return None

    @dataclass
    class CalendarEvent:
        summary: str
        description: str
        start: object
        end: object

    class HomeAssistant:
        pass

    class ConfigEntry:
        pass

    class DeviceInfo(dict):
        pass

    class Store:
        def __init__(self, hass, version, key):
            self.data = None

        async def async_load(self):
            return self.data

        async def async_save(self, data):
            self.data = data

    def async_get_clientsession(hass):
        return None

    def start_of_local_day(day):
        return datetime.combine(day, datetime.min.time())

    def as_local(value):
        return value

    def now():
        return datetime.now()

    def slugify(value):
        return value.lower().replace(" ", "-")

    calendar_mod.CalendarEntity = CalendarEntity
    calendar_mod.CalendarEvent = CalendarEvent
    core_mod.HomeAssistant = HomeAssistant
    config_entries_mod.ConfigEntry = ConfigEntry
    entity_mod.DeviceInfo = DeviceInfo
    aiohttp_client_mod.async_get_clientsession = async_get_clientsession
    storage_mod.Store = Store
    dt_mod.start_of_local_day = start_of_local_day
    dt_mod.as_local = as_local
    dt_mod.now = now
    util_mod.slugify = slugify
    util_mod.dt = dt_mod

    sys.modules["homeassistant"] = homeassistant
    sys.modules["homeassistant.components"] = components
    sys.modules["homeassistant.components.calendar"] = calendar_mod
    sys.modules["homeassistant.core"] = core_mod
    sys.modules["homeassistant.config_entries"] = config_entries_mod
    sys.modules["homeassistant.helpers"] = helpers_mod
    sys.modules["homeassistant.helpers.entity"] = entity_mod
    sys.modules["homeassistant.helpers.aiohttp_client"] = aiohttp_client_mod
    sys.modules["homeassistant.helpers.storage"] = storage_mod
    sys.modules["homeassistant.util"] = util_mod
    sys.modules["homeassistant.util.dt"] = dt_mod


def _load_calendar_entity():
    _install_homeassistant_stubs()

    custom_components = types.ModuleType("custom_components")
    skolmat_pkg = types.ModuleType("custom_components.skolmat")
    skolmat_pkg.__path__ = [str(CALENDAR_PATH.parent)]

    const_mod = types.ModuleType("custom_components.skolmat.const")
    const_mod.DOMAIN = "skolmat"
    const_mod.CONF_NAME = "name"
    const_mod.CONF_URL = "url"
    const_mod.CONF_PROVIDER = "provider"
    const_mod.CONF_LUNCH_BEGIN = "lunch_begin"
    const_mod.CONF_LUNCH_END = "lunch_end"
    const_mod.CALENDAR_HISTORY_DAYS = 90

    menu_mod = types.ModuleType("custom_components.skolmat.menu")

    class Menu:
        pass

    menu_mod.Menu = Menu

    sys.modules["custom_components"] = custom_components
    sys.modules["custom_components.skolmat"] = skolmat_pkg
    sys.modules["custom_components.skolmat.const"] = const_mod
    sys.modules["custom_components.skolmat.menu"] = menu_mod

    spec = importlib.util.spec_from_file_location(
        "custom_components.skolmat.calendar",
        CALENDAR_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["custom_components.skolmat.calendar"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.SkolmatCalendarEntity


SkolmatCalendarEntity = _load_calendar_entity()


class FakeMenu:
    provider = "skolmaten.se"

    def __init__(self, menu_data, summaries=None, menus=None):
        self.menu_data = menu_data
        self.summaries = summaries or {}
        self.menus = menus or {}

    async def getMenu(self, session):
        return self.menu_data

    def getReadableDaySummary(self, day):
        key = day.isoformat() if hasattr(day, "isoformat") else str(day)
        return self.summaries.get(key, "")

    def getReadableDayMenu(self, day):
        key = day.isoformat() if hasattr(day, "isoformat") else str(day)
        return self.menus.get(key, "")


class FakeEntry:
    entry_id = "entry-1"
    data = {
        "name": "Restaurang Rosengarden",
        "url": "https://skolmaten.se/restaurang-rosengarden",
        "provider": "skolmaten.se",
    }


def _make_entity(menu):
    return SkolmatCalendarEntity(
        hass=object(),
        entry=FakeEntry(),
        menu=menu,
        url_hash="hash",
    )


def test_empty_menu_does_not_create_blank_event_for_today():
    entity = _make_entity(FakeMenu(menu_data={}))

    asyncio.run(entity.async_update())

    assert entity._events == []
    assert entity.event is None
    assert entity._history == {}


def test_empty_today_history_entry_is_pruned_when_menu_is_blank():
    entity = _make_entity(FakeMenu(menu_data={}))
    today = date.today().isoformat()
    entity._history = {today: {"summary": "", "menu": ""}}

    asyncio.run(entity.async_update())

    assert today not in entity._history
    assert entity._events == []
    assert entity.event is None


if __name__ == "__main__":
    test_empty_menu_does_not_create_blank_event_for_today()
    test_empty_today_history_entry_is_pruned_when_menu_is_blank()
    print("test_calendar_empty_menu: ok")
