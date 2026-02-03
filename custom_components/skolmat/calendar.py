"""Calendar platform for Skolmat."""

from __future__ import annotations

from datetime import datetime, timedelta, date
import logging
from typing import Any

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util
from homeassistant.util import slugify

from .const import (
    DOMAIN,
    CONF_NAME,
    CONF_URL,
    CONF_LUNCH_BEGIN,
    CONF_LUNCH_END,
    CALENDAR_HISTORY_DAYS,
)
from .menu import Menu

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    menu: Menu = data["menu"]
    url_hash: str = data["url_hash"]

    add_entities(
        [
            SkolmatCalendarEntity(
                hass=hass,
                entry=entry,
                menu=menu,
                url_hash=url_hash,
            )
        ],
        update_before_add=True,
    )


class SkolmatCalendarEntity(CalendarEntity):

    _attr_icon = "mdi:calendar"

    def __init__(self, hass, entry, menu:Menu, url_hash):
        self.hass = hass
        self._entry = entry
        self._menu = menu

        self._name = entry.data[CONF_NAME]
        self._url = entry.data[CONF_URL]

        name_slug = slugify(self._name) or "unnamed"
        self._attr_unique_id = f"skolmat_calendar_{name_slug}_{entry.entry_id}"
        self._attr_available = True

        self._lunch_begin = self._parse_time(entry.data.get(CONF_LUNCH_BEGIN))
        self._lunch_end = self._parse_time(entry.data.get(CONF_LUNCH_END))

        self._events = []
        self._current_or_next = None

        self._store = Store(hass, 1, f"{DOMAIN}_{entry.entry_id}_calendar")
        self._history: dict[str, dict[str, str]] = {}
        self._history_dirty = False

    @staticmethod
    def _parse_time(v):
        if not v:
            return None
        return datetime.strptime(v, "%H:%M").time()

    @property
    def name(self):
        return self._name

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._name,
            manufacturer="Skolmat",
        )

    @property
    def event(self) -> CalendarEvent | None:
        return self._current_or_next

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        await self._async_load_history()

    async def _async_load_history(self):
        data = await self._store.async_load()
        if not data:
            self._history = {}
            return

        hist: dict[str, dict[str, str]] = {}
        for item in data.get("events", []):
            date_str = item.get("date")
            if not date_str:
                continue
            hist[date_str] = {
                "summary": item.get("summary") or item.get("course") or "",
                "menu": item.get("menu") or item.get("description") or "",
            }

        self._history = hist

    async def _async_save_history(self):
        if not self._history_dirty:
            return

        events = [
            {
                "date": d,
                "course": info.get("summary", ""),
                "menu": info.get("menu", ""),
            }
            for d, info in sorted(self._history.items())
        ]
        await self._store.async_save({"events": events})
        self._history_dirty = False

    async def async_update(self):
        session = async_get_clientsession(self.hass)
        menu_data = await self._menu.getMenu(session)
        if menu_data is None:
            self._attr_available = False
            self._events = []
            self._current_or_next = None
            return
        self._attr_available = True

        today = dt_util.now().date()
        today_str = today.isoformat()

        # Add today's menu to history if needed
        summary = self._menu.getReadableDaySummary(today)
        menu_text = self._menu.getReadableDayMenu(today)
        if self._history.get(today_str) != {"summary": summary, "menu": menu_text}:
            self._history[today_str] = {"summary": summary, "menu": menu_text}
            self._history_dirty = True

        # Prune history older than N days
        cutoff = today - timedelta(days=CALENDAR_HISTORY_DAYS)
        to_remove = [d for d in self._history if date.fromisoformat(d) < cutoff]
        for d in to_remove:
            self._history.pop(d, None)
            self._history_dirty = True

        await self._async_save_history()

        # Build event list
        events = []

        # Past events come from history to avoid rewriting summaries.
        # Today's event is built from menu data below unless missing.
        menu_dates: set[date] = set()
        for d, info in self._history.items():
            day_date = date.fromisoformat(d)
            if day_date < today:
                description = info.get("menu") or self._menu.getReadableDayMenu(day_date)
                events.append(
                    self._build_event(
                        day=day_date,
                        summary=info.get("summary", ""),
                        description=description,
                    )
                )

        # Present + future events (today included)
        for iso in menu_data:
            day_date = date.fromisoformat(iso)
            menu_dates.add(day_date)
            if day_date < today:
                continue
            events.append(
                self._build_event(
                    day=day_date,
                    summary=self._menu.getReadableDaySummary(day_date),
                    description=self._menu.getReadableDayMenu(day_date),
                )
            )

        if today not in menu_dates and today_str in self._history:
            info = self._history[today_str]
            description = info.get("menu") or menu_text
            events.append(
                self._build_event(
                    day=today,
                    summary=info.get("summary", ""),
                    description=description,
                )
            )

        events.sort(key=lambda e: self._normalize(e.start))

        self._events = events
        self._current_or_next = self._find_current_or_next(events)

    def _build_event(self, day: date, summary: str, description: str) -> CalendarEvent:

        if not (self._lunch_begin and self._lunch_end):
            # ALL-DAY event → use date objects
            start = day
            end = day + timedelta(days=1)
        else:
            # TIMED event → use datetime objects
            start = dt_util.start_of_local_day(day).replace(
                hour=self._lunch_begin.hour,
                minute=self._lunch_begin.minute,
            )
            end = dt_util.start_of_local_day(day).replace(
                hour=self._lunch_end.hour,
                minute=self._lunch_end.minute,
            )

        return CalendarEvent(
            summary=summary or "",
            description=description or "",
            start=start,
            end=end,
        )

    @staticmethod
    def _normalize(value: Any) -> datetime:
        if isinstance(value, datetime):
            return dt_util.as_local(value)
        if isinstance(value, date):
            return dt_util.start_of_local_day(value)
        return dt_util.now()

    def _find_current_or_next(self, events):
        now = dt_util.now()
        for e in events:
            start = self._normalize(e.start)
            end = self._normalize(e.end)
            if start <= now < end:
                return e
            if start > now:
                return e
        return None

    async def async_get_events(self, hass, start_date, end_date):
        await self.async_update()
        if not self.available:
            return []
        result = []

        for e in self._events:
            s = self._normalize(e.start)
            t = self._normalize(e.end)

            if t <= start_date:
                continue
            if s >= end_date:
                continue

            result.append(e)

        return result
