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

    def __init__(self, hass, entry, menu, url_hash):
        self.hass = hass
        self._entry = entry
        self._menu = menu

        self._name = entry.data[CONF_NAME]
        self._url = entry.data[CONF_URL]

        self._attr_unique_id = f"skolmat_calendar_{url_hash}"

        self._lunch_begin = self._parse_time(entry.data.get(CONF_LUNCH_BEGIN))
        self._lunch_end = self._parse_time(entry.data.get(CONF_LUNCH_END))

        self._events = []
        self._current_or_next = None

        self._store = Store(hass, 1, f"{DOMAIN}_{entry.entry_id}_calendar")
        self._history = {}
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

        hist = {}
        for item in data.get("events", []):
            hist[item["date"]] = item["course"]

        self._history = hist

    async def _async_save_history(self):
        if not self._history_dirty:
            return

        events = [{"date": d, "course": c} for d, c in sorted(self._history.items())]
        await self._store.async_save({"events": events})
        self._history_dirty = False

    async def async_update(self):
        session = async_get_clientsession(self.hass)
        await self._menu.loadMenu(session)

        today = dt_util.now().date()
        today_str = today.isoformat()

        # Add today's menu to history if needed
        courses = self._menu.menuToday or []
        if courses:
            course = courses[0]
            if self._history.get(today_str) != course:
                self._history[today_str] = course
                self._history_dirty = True

        # Prune history older than N days
        cutoff = today - timedelta(days=CALENDAR_HISTORY_DAYS)
        to_remove = [
            d for d in self._history if date.fromisoformat(d) < cutoff
        ]
        for d in to_remove:
            self._history.pop(d, None)
            self._history_dirty = True

        await self._async_save_history()

        # Build event list
        events = []

        # --------------------------------------------------------------
        # FIX: Only add *past* events from history.
        # Do NOT include today's event here, otherwise it is duplicated,
        # because the present/future loop below already includes today.
        # --------------------------------------------------------------
        for d, course in self._history.items():
            day_date = date.fromisoformat(d)
            if day_date < today:
                events.append(self._build_event(day_date, course))

        # Present + future events (today included)
        for week in self._menu.menu.values():
            for day in week:
                d = date.fromisoformat(day["date"])
                if d < today:
                    continue
                c = day["courses"]
                if not c:
                    continue
                events.append(self._build_event(d, c[0]))

        events.sort(key=lambda e: self._normalize(e.start))

        self._events = events
        self._current_or_next = self._find_current_or_next(events)

    def _build_event(self, d: date, course: str) -> CalendarEvent:
        # ALL-DAY event → use date objects
        if not (self._lunch_begin and self._lunch_end):
            return CalendarEvent(
                summary=course,
                description=course,
                start=d,
                end=d + timedelta(days=1),
            )

        # TIMED event → use datetime objects
        start = dt_util.start_of_local_day(d).replace(
            hour=self._lunch_begin.hour,
            minute=self._lunch_begin.minute,
        )
        end = dt_util.start_of_local_day(d).replace(
            hour=self._lunch_end.hour,
            minute=self._lunch_end.minute,
        )

        return CalendarEvent(
            summary=course,
            description=course,
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
