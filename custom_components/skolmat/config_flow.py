"""Config flow for Skolmat."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import voluptuous as vol
from yarl import URL

from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    DOMAIN,
    CONF_NAME,
    CONF_URL,
    CONF_LUNCH_BEGIN,
    CONF_LUNCH_END,
)


def _is_valid_url(url: str) -> bool:
    """Validate URL using yarl."""
    try:
        URL(url)
        return True
    except Exception:
        return False


def _parse_time(value: str | None):
    """Convert HH:MM string to time object, or None."""
    if not value:
        return None
    return datetime.strptime(value, "%H:%M").time()


class SkolmatConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Skolmat."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            name = user_input[CONF_NAME].strip()
            url = user_input[CONF_URL].rstrip(" /")

            # Validate URL manually
            if not _is_valid_url(url):
                errors["base"] = "invalid_url"
            else:
                begin = _parse_time(user_input.get(CONF_LUNCH_BEGIN))
                end = _parse_time(user_input.get(CONF_LUNCH_END))

                # Validate time range
                if begin and end and end <= begin:
                    errors["base"] = "invalid_lunch_interval"
                else:
                    data = {
                        CONF_NAME: name,
                        CONF_URL: url,
                    }

                    # Optional times - add only when provided
                    if begin:
                        data[CONF_LUNCH_BEGIN] = begin.strftime("%H:%M")
                    if end:
                        data[CONF_LUNCH_END] = end.strftime("%H:%M")

                    return self.async_create_entry(title=name, data=data)

        # Schema must use only serializable types (2025.x requirement)
        schema = vol.Schema(
            {
                vol.Required(CONF_NAME): str,
                vol.Required(CONF_URL): str,
                vol.Optional(CONF_LUNCH_BEGIN): str,
                vol.Optional(CONF_LUNCH_END): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(entry):
        return SkolmatOptionsFlowHandler(entry)


class SkolmatOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Skolmat options."""

    def __init__(self, entry):
        self.entry = entry

    async def async_step_init(self, user_input=None):
        errors: dict[str, str] = {}
        current = dict(self.entry.data)

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
                    data = {
                        CONF_NAME: name,
                        CONF_URL: url,
                    }

                    # Add times only when provided
                    if begin:
                        data[CONF_LUNCH_BEGIN] = begin.strftime("%H:%M")
                    if end:
                        data[CONF_LUNCH_END] = end.strftime("%H:%M")

                    # Update entry and reload
                    self.hass.config_entries.async_update_entry(self.entry, data=data)
                    await self.hass.config_entries.async_reload(self.entry.entry_id)

                    return self.async_create_entry(title="", data={})

        # Pre-fill defaults (None → empty field)
        defaults = {
            CONF_NAME: current.get(CONF_NAME),
            CONF_URL: current.get(CONF_URL),
            CONF_LUNCH_BEGIN: current.get(CONF_LUNCH_BEGIN, ""),
            CONF_LUNCH_END: current.get(CONF_LUNCH_END, ""),
        }

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=defaults[CONF_NAME]): str,
                vol.Required(CONF_URL, default=defaults[CONF_URL]): str,
                vol.Optional(CONF_LUNCH_BEGIN, default=defaults[CONF_LUNCH_BEGIN]): str,
                vol.Optional(CONF_LUNCH_END, default=defaults[CONF_LUNCH_END]): str,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
        )
