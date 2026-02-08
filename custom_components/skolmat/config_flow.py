"""Config flow for Skolmat."""

from __future__ import annotations

from datetime import date, datetime
import logging
import importlib
import re
import sys
from pathlib import Path
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    DOMAIN,
    CONF_NAME,
    CONF_URL,
    CONF_PROVIDER,
    CONF_LUNCH_BEGIN,
    CONF_LUNCH_END,
    CONF_MEALS_SELECTED,
    CONF_EXCLUDE_REGEX,
    CONF_PREFER_REGEX,
    CONF_MAX_ENTRIES,
    CONF_PROCESSOR_FILE,
    CONF_PROCESSOR_FN,
)
from .menu import Menu, MenuEntry

_LOGGER = logging.getLogger(__name__)

_SELECTED_DATE = "selected_date"
_DONE_CONFIGURING = "done_configuring"
_DISPLAY_INPUT = "display_input"
_DISPLAY_SUMMARY = "display_summary"
_RELOAD_PROCESSOR = "reload_processor"
_EXCLUDE_LABEL = "exclude_label"
_PREFER_LABEL = "prefer_label"
_PROCESSOR_LABEL = "processor_label"

def _is_valid_url(url: str) -> bool:
    """Validate URL using yarl."""
    try:
        from yarl import URL
        URL(url)
        return True
    except Exception:
        return False


def _parse_time(value: str | None):
    """Convert HH:MM string to time object, or None."""
    if not value:
        return None
    return datetime.strptime(value, "%H:%M").time()


class _SkolmatFlowMixin:
    def _init_flow_state(self, base_data: dict[str, Any]) -> None:
        self._data = dict(base_data)
        self._original_processor_file = self._data.get(CONF_PROCESSOR_FILE)
        self._original_processor_fn = self._data.get(CONF_PROCESSOR_FN)
        self._menu: Menu | None = None
        self._discovery: dict[str, Any] = {"meals": [], "labels": [], "info": ""}
        self._available_dates: list[date] = []
        self._date_index = 0
        self._input_data = ""
        self._summary = ""
        self._summary_count = ""
        self._warning = ""
        self._exclude_keywords = self._format_regex_defaults(self._data.get(CONF_EXCLUDE_REGEX, []))
        self._prefer_keywords = self._format_regex_defaults(self._data.get(CONF_PREFER_REGEX, []))
        self._processor_error: str | None = None

    def _parse_regex_list(self, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            values = value
        elif isinstance(value, str):
            values = value.splitlines()
        else:
            values = [value]

        patterns: list[str] = []
        for raw in values:
            if not isinstance(raw, str):
                continue
            line = raw.strip()
            if not line:
                continue
            if line.startswith("/") and line.endswith("/") and len(line) > 1:
                pattern = line[1:-1].strip()
                if pattern:
                    patterns.append(pattern)
                continue
            patterns.append(re.escape(line))
        return patterns

    def _parse_keyword_values(self, value: Any) -> tuple[list[str], list[str]]:
        if not value:
            return [], []
        values = value if isinstance(value, list) else [value]
        raw_values = [v.strip() for v in values if isinstance(v, str) and v.strip()]
        return raw_values, self._parse_regex_list(raw_values)

    def _format_regex_defaults(self, patterns: Any) -> list[str]:
        if not patterns:
            return []
        values = patterns if isinstance(patterns, list) else [patterns]
        return [f"/{p}/" for p in values if isinstance(p, str) and p.strip()]

    def _parse_int(self, value: Any) -> int | None:
        if value in (None, ""):
            return None
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return None
        return None if parsed <= 0 else parsed

    async def _run_discovery(self) -> bool:
        url = self._data[CONF_URL]
        processor_cb, self._processor_error = await self._load_processor(
            self._data.get(CONF_PROCESSOR_FILE),
            self._data.get(CONF_PROCESSOR_FN),
            force_reload=True,
        )

        self._menu = Menu.createMenu(
            self.hass.async_add_executor_job,
            url,
            customMenuEntryProcessorCB=processor_cb,
        )
        self._data[CONF_PROVIDER] = self._menu.provider

        session = async_get_clientsession(self.hass)
        menu_data = await self._menu.getMenu(session)
        if menu_data is None:
            self._discovery = {"meals": [], "labels": [], "info": "Discovery failed; menu fetch failed."}
            self._available_dates = []
            self._date_index = 0
            self._input_data = ""
            self._summary = ""
            self._summary_count = ""
            return False

        self._discovery = self._menu.getSummaryFilterKeywords()
        self._available_dates = self._menu_dates_with_entries(menu_data)
        self._date_index = self._pick_initial_date_index(self._available_dates)

        entries = self._entries_for_current_date()
        available_meals = self._all_meals_from_entries(entries)
        selected = list(self._data.get(CONF_MEALS_SELECTED, []))
        if selected:
            self._data[CONF_MEALS_SELECTED] = [m for m in selected if m in available_meals]
        else:
            # Empty selection means "all"; keep empty to avoid preselecting meals.
            self._data[CONF_MEALS_SELECTED] = []

        self._build_preview()
        return True

    def _menu_dates_with_entries(self, menu_data: dict[str, list[MenuEntry]]) -> list[date]:
        dates = []
        for iso, entries in menu_data.items():
            if not entries:
                continue
            try:
                dates.append(date.fromisoformat(iso))
            except ValueError:
                continue
        return sorted(dates)

    def _pick_initial_date_index(self, dates: list[date]) -> int:
        if not dates:
            return 0
        today = date.today()
        for idx, d in enumerate(dates):
            if d >= today:
                return idx
        return len(dates) - 1

    def _set_date_index_for(self, preferred: date | None) -> None:
        if not self._available_dates:
            self._date_index = 0
            return
        if preferred and preferred in self._available_dates:
            self._date_index = self._available_dates.index(preferred)
        else:
            self._date_index = 0

    def _entries_for_current_date(self) -> list[MenuEntry]:
        if not self._menu or not self._available_dates:
            return []
        current = self._available_dates[self._date_index]
        return self._menu._menu.get(current.isoformat(), [])

    async def _load_processor(
        self,
        processor_file: str | None,
        processor_fn: str | None,
        *,
        force_reload: bool,
    ) -> tuple[Any, str | None]:
        if not processor_file and not processor_fn:
            return None, None
        if not processor_file or not processor_fn:
            return None, "processor_missing_fields"

        filename = processor_file.strip()
        if not filename:
            return None, "processor_missing_fields"
        if not filename.endswith(".py"):
            filename = f"{filename}.py"

        processor_path = Path(__file__).resolve().parent / "processors" / filename
        if not processor_path.exists():
            return None, "processor_file_missing"

        module_name = f"custom_components.skolmat.processors.{processor_path.stem}"
        if force_reload and module_name in sys.modules:
            sys.modules.pop(module_name, None)

        def _import_with_alias(name: str):
            try:
                menu_module = importlib.import_module("custom_components.skolmat.menu")
                sys.modules.setdefault("menu", menu_module)
            except Exception:
                pass
            return importlib.import_module(name)

        try:
            module = await self.hass.async_add_executor_job(_import_with_alias, module_name)
        except Exception as exc:
            _LOGGER.info("Processor import failed: module=%s error=%s", module_name, exc)
            return None, "processor_import_failed"

        processor = getattr(module, processor_fn.strip(), None)
        if not callable(processor):
            _LOGGER.info(
                "Processor function missing/not callable: module=%s fn=%s",
                module_name,
                processor_fn,
            )
            return None, "processor_fn_missing"

        return processor, None

    def _all_meals_from_entries(self, entries: list[MenuEntry]) -> list[str]:
        seen = set()
        meals: list[str] = []
        for entry in entries:
            meal = entry.get("meal") or ""
            if meal and meal not in seen:
                seen.add(meal)
                meals.append(meal)
        return meals

    def _format_input_data(self, entries: list[MenuEntry]) -> str:
        if not entries:
            return "(no entries for this day)"

        grouped: dict[str, list[MenuEntry]] = {}
        order: list[str] = []
        for entry in entries:
            meal = entry.get("meal") or "Unknown"
            if meal not in grouped:
                grouped[meal] = []
                order.append(meal)
            grouped[meal].append(entry)

        lines: list[str] = []
        for meal in order:
            lines.append(f"[{meal}]")
            for entry in grouped[meal]:
                label = entry.get("label") or ""
                dish = entry.get("dish") or ""
                if label:
                    lines.append(f"- {label}: {dish}")
                else:
                    lines.append(f"- {dish}")
            lines.append("")

        return "\n".join(lines).rstrip()

    def _build_preview(self) -> None:
        entries = self._entries_for_current_date()
        self._input_data = self._format_input_data(entries)

        if not entries or not self._menu:
            self._summary = ""
            self._summary_count = ""
            return

        selected = list(self._data.get(CONF_MEALS_SELECTED, []))
        preview_selected = selected or self._all_meals_from_entries(entries)

        filters = self._current_filters()
        filters[CONF_MEALS_SELECTED] = preview_selected
        self._menu.setSummaryFilters(filters)
        filtered = self._menu._dayFilter.filter(entries)
        self._summary = self._menu._defaultReadableDaySummary(filtered) or ""

        labels = {e.get("label") for e in filtered if e.get("label")}
        if filtered:
            self._summary_count = f"{len(filtered)} entries from {len(set(e.get('meal') for e in filtered))} meals ({len(labels)} labels detected)."
        else:
            self._summary_count = "No entries found for summary."

        self._warning = ""
        if not selected:
            self._warning = "No meals selected; showing all meals."
        elif not any(e.get("meal") in selected for e in entries):
            self._warning = "No entries matched today; showing all meals."

    def _current_filters(self) -> dict[str, Any]:
        return {
            CONF_MEALS_SELECTED: self._data.get(CONF_MEALS_SELECTED, []),
            CONF_EXCLUDE_REGEX: self._data.get(CONF_EXCLUDE_REGEX, []),
            CONF_PREFER_REGEX: self._data.get(CONF_PREFER_REGEX, []),
            CONF_MAX_ENTRIES: self._data.get(CONF_MAX_ENTRIES),
        }

    def _description_placeholders(self) -> dict[str, str]:
        discovery_info = self._discovery.get("info", "")
        current_date = "(no date)"
        if self._available_dates:
            current_date = self._available_dates[self._date_index].isoformat()
        warning = self._warning
        if self._processor_error:
            warning = f"{warning} Processor error: {self._processor_error}".strip()
        return {
            "name": self._data.get(CONF_NAME, ""),
            "discovery_info": discovery_info,
            "current_date": current_date,
            "input_data": self._input_data or "(no input data)",
            "summary": self._summary or "(no summary)",
            "summary_count": self._summary_count or "",
            "warning": warning,
        }

    def _schema_configure(self) -> vol.Schema:
        options = self._discovery.get("meals", [])
        if not options and self._menu:
            options = self._all_meals_from_entries(self._entries_for_current_date())
        selected_meals = list(self._data.get(CONF_MEALS_SELECTED, []))
        if options:
            selected_meals = [meal for meal in selected_meals if meal in options]
            self._data[CONF_MEALS_SELECTED] = selected_meals
        options_map = {opt: opt for opt in options}
        for value in selected_meals:
            if isinstance(value, str) and value not in options_map:
                options_map[value] = value

        fields: dict[Any, Any] = {}
        if self._available_dates:
            date_options = [d.isoformat() for d in self._available_dates]
            current_date = self._available_dates[self._date_index].isoformat()
            fields[vol.Optional(_SELECTED_DATE, default=current_date)] = SelectSelector(
                SelectSelectorConfig(
                    options=date_options,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            )

        fields[vol.Optional(
            _DISPLAY_INPUT,
            default=self._input_data or "",
        )] = TextSelector(TextSelectorConfig(multiline=True))
        fields[vol.Optional(
            _DISPLAY_SUMMARY,
            default=self._summary or "",
        )] = TextSelector(TextSelectorConfig(multiline=True))

        fields[vol.Optional(
            CONF_MEALS_SELECTED,
            default=selected_meals,
        )] = cv.multi_select(options_map)
        fields[vol.Optional(_EXCLUDE_LABEL, default=[])] = cv.multi_select({})
        fields[vol.Optional(
            CONF_EXCLUDE_REGEX,
            default=self._exclude_keywords,
        )] = SelectSelector(
            SelectSelectorConfig(
                options=[],
                multiple=True,
                custom_value=True,
                mode=SelectSelectorMode.DROPDOWN,
            )
        )
        fields[vol.Optional(_PREFER_LABEL, default=[])] = cv.multi_select({})
        fields[vol.Optional(
            CONF_PREFER_REGEX,
            default=self._prefer_keywords,
        )] = SelectSelector(
            SelectSelectorConfig(
                options=[],
                multiple=True,
                custom_value=True,
                mode=SelectSelectorMode.DROPDOWN,
            )
        )
        max_entries_value = self._data.get(CONF_MAX_ENTRIES)
        fields[vol.Optional(
            CONF_MAX_ENTRIES,
            description={
                "suggested_value": "" if max_entries_value is None else str(max_entries_value)
            },
        )] = TextSelector(TextSelectorConfig(type=TextSelectorType.NUMBER))
        fields[vol.Optional(_PROCESSOR_LABEL, default=[])] = cv.multi_select({})
        fields[vol.Optional(
            CONF_PROCESSOR_FILE,
            description={"suggested_value": self._data.get(CONF_PROCESSOR_FILE) or ""},
        )] = str
        fields[vol.Optional(
            CONF_PROCESSOR_FN,
            description={"suggested_value": self._data.get(CONF_PROCESSOR_FN) or ""},
        )] = str
        fields[vol.Optional(_RELOAD_PROCESSOR, default=False)] = bool
        fields[vol.Optional(_DONE_CONFIGURING, default=False)] = bool

        return vol.Schema(fields)


class SkolmatConfigFlow(_SkolmatFlowMixin, config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Skolmat."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            name = user_input[CONF_NAME].strip()
            url = user_input[CONF_URL].rstrip(" /")

            if not _is_valid_url(url):
                errors["base"] = "invalid_url"
            else:
                begin = _parse_time(user_input.get(CONF_LUNCH_BEGIN))
                end = _parse_time(user_input.get(CONF_LUNCH_END))

                if begin and end and end <= begin:
                    errors["base"] = "invalid_lunch_interval"
                else:
                    self._init_flow_state(
                        {
                            CONF_NAME: name,
                            CONF_URL: url,
                            CONF_LUNCH_BEGIN: begin.strftime("%H:%M") if begin else None,
                            CONF_LUNCH_END: end.strftime("%H:%M") if end else None,
                        }
                    )
                    ok = await self._run_discovery()
                    if not ok:
                        errors["base"] = "menu_fetch_failed"
                    else:
                        return await self.async_step_configure()

        defaults = {}
        if user_input:
            defaults = {
                CONF_NAME: user_input.get(CONF_NAME, ""),
                CONF_URL: user_input.get(CONF_URL, ""),
                CONF_LUNCH_BEGIN: user_input.get(CONF_LUNCH_BEGIN, ""),
                CONF_LUNCH_END: user_input.get(CONF_LUNCH_END, ""),
            }

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, "")): str,
                vol.Required(CONF_URL, default=defaults.get(CONF_URL, "")): str,
                vol.Optional(CONF_LUNCH_BEGIN, default=defaults.get(CONF_LUNCH_BEGIN, "")): str,
                vol.Optional(CONF_LUNCH_END, default=defaults.get(CONF_LUNCH_END, "")): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_configure(self, user_input=None):
        if user_input is not None:
            errors: dict[str, str] = {}
            selected_date = user_input.get(_SELECTED_DATE)
            if selected_date and self._available_dates:
                try:
                    chosen = date.fromisoformat(selected_date)
                    if chosen in self._available_dates:
                        self._date_index = self._available_dates.index(chosen)
                except ValueError:
                    pass

            self._data[CONF_MEALS_SELECTED] = list(user_input.get(CONF_MEALS_SELECTED, []))
            self._exclude_keywords, self._data[CONF_EXCLUDE_REGEX] = self._parse_keyword_values(
                user_input.get(CONF_EXCLUDE_REGEX)
            )
            self._prefer_keywords, self._data[CONF_PREFER_REGEX] = self._parse_keyword_values(
                user_input.get(CONF_PREFER_REGEX)
            )
            self._data[CONF_MAX_ENTRIES] = self._parse_int(user_input.get(CONF_MAX_ENTRIES))
            user_input.pop(_EXCLUDE_LABEL, None)
            user_input.pop(_PREFER_LABEL, None)
            user_input.pop(_PROCESSOR_LABEL, None)
            self._data[CONF_PROCESSOR_FILE] = (user_input.get(CONF_PROCESSOR_FILE) or "").strip() or None
            self._data[CONF_PROCESSOR_FN] = (user_input.get(CONF_PROCESSOR_FN) or "").strip() or None
            processor_changed = (
                self._data.get(CONF_PROCESSOR_FILE) != self._original_processor_file
                or self._data.get(CONF_PROCESSOR_FN) != self._original_processor_fn
            )
            reload_requested = bool(user_input.get(_RELOAD_PROCESSOR))
            if processor_changed or reload_requested:
                preferred_date = self._available_dates[self._date_index] if self._available_dates else None
                await self._run_discovery()
                self._set_date_index_for(preferred_date)
                if self._processor_error:
                    errors["base"] = self._processor_error
                else:
                    self._original_processor_file = self._data.get(CONF_PROCESSOR_FILE)
                    self._original_processor_fn = self._data.get(CONF_PROCESSOR_FN)
            else:
                self._processor_error = None
            self._build_preview()

            if errors:
                return self.async_show_form(
                    step_id="configure",
                    data_schema=self._schema_configure(),
                    errors=errors,
                    description_placeholders=self._description_placeholders(),
                )

            if user_input.get(_DONE_CONFIGURING):
                return self.async_create_entry(title=self._data[CONF_NAME], data=self._data)

        self._build_preview()
        return self.async_show_form(
            step_id="configure",
            data_schema=self._schema_configure(),
            description_placeholders=self._description_placeholders(),
        )

    @staticmethod
    @callback
    def async_get_options_flow(entry):
        return SkolmatOptionsFlowHandler(entry)


class SkolmatOptionsFlowHandler(_SkolmatFlowMixin, config_entries.OptionsFlow):
    """Handle Skolmat options."""

    def __init__(self, entry):
        self.entry = entry
        self._init_flow_state(dict(entry.data))

    async def async_step_init(self, user_input=None):
        if user_input is None:
            await self._run_discovery()
            return await self.async_step_configure()

        return await self.async_step_configure(user_input)

    async def async_step_configure(self, user_input=None):
        if user_input is not None:
            errors: dict[str, str] = {}
            selected_date = user_input.get(_SELECTED_DATE)
            if selected_date and self._available_dates:
                try:
                    chosen = date.fromisoformat(selected_date)
                    if chosen in self._available_dates:
                        self._date_index = self._available_dates.index(chosen)
                except ValueError:
                    pass

            self._data[CONF_MEALS_SELECTED] = list(user_input.get(CONF_MEALS_SELECTED, []))
            self._exclude_keywords, self._data[CONF_EXCLUDE_REGEX] = self._parse_keyword_values(
                user_input.get(CONF_EXCLUDE_REGEX)
            )
            self._prefer_keywords, self._data[CONF_PREFER_REGEX] = self._parse_keyword_values(
                user_input.get(CONF_PREFER_REGEX)
            )
            self._data[CONF_MAX_ENTRIES] = self._parse_int(user_input.get(CONF_MAX_ENTRIES))
            user_input.pop(_EXCLUDE_LABEL, None)
            user_input.pop(_PREFER_LABEL, None)
            user_input.pop(_PROCESSOR_LABEL, None)
            self._data[CONF_PROCESSOR_FILE] = (user_input.get(CONF_PROCESSOR_FILE) or "").strip() or None
            self._data[CONF_PROCESSOR_FN] = (user_input.get(CONF_PROCESSOR_FN) or "").strip() or None
            processor_changed = (
                self._data.get(CONF_PROCESSOR_FILE) != self._original_processor_file
                or self._data.get(CONF_PROCESSOR_FN) != self._original_processor_fn
            )
            reload_requested = bool(user_input.get(_RELOAD_PROCESSOR))
            if processor_changed or reload_requested:
                preferred_date = self._available_dates[self._date_index] if self._available_dates else None
                await self._run_discovery()
                self._set_date_index_for(preferred_date)
                if self._processor_error:
                    errors["base"] = self._processor_error
                else:
                    self._original_processor_file = self._data.get(CONF_PROCESSOR_FILE)
                    self._original_processor_fn = self._data.get(CONF_PROCESSOR_FN)
            else:
                self._processor_error = None
            self._build_preview()

            if errors:
                return self.async_show_form(
                    step_id="configure",
                    data_schema=self._schema_configure(),
                    errors=errors,
                    description_placeholders=self._description_placeholders(),
                )

            if user_input.get(_DONE_CONFIGURING):
                self.hass.config_entries.async_update_entry(self.entry, data=self._data)
                await self.hass.config_entries.async_reload(self.entry.entry_id)
                return self.async_create_entry(title="", data={})

        self._build_preview()
        return self.async_show_form(
            step_id="configure",
            data_schema=self._schema_configure(),
            description_placeholders=self._description_placeholders(),
        )
