"""Config flow for SMA Semp integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ID, CONF_NAME

from .config_flow_schema import _getSchema
from .const import (
    DOMAIN,
    MY_KEY,
)

_LOGGER = logging.getLogger(__name__)


class SempConfigFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SMA Semp."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize."""

    async def validate_input(self, user_input: dict[str, Any]) -> dict[str, str]:
        """Validate the user input"""
        errors: dict[str, str] = {}
        # TODO Check min < max ...
        if MY_KEY not in self.hass.data:
            # No other device created yet
            return errors

        # Check for duplicate IDs
        data = self.hass.data[MY_KEY]
        if str(int(user_input[CONF_ID])) in data.sendata:
            errors["base"] = "dupe id"

        # Check for duplicate names
        name = user_input[CONF_NAME].lower()
        for dev in data.sendata.values():
            if name == dev.configdata.name.lower():
                errors["base"] = "dupe name"
        return errors

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return self.async_show_menu(
            step_id="user",
            menu_options=[
                "energyusageonly",
                "energyusagecontrollable",
                "energyusagecontrollableinterruptable",
            ],
        )

    async def async_step_energyusageonly(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configuration for report energy usage only"""
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = await self.validate_input(user_input)
            if not errors:
                return self.async_create_entry(
                    title=f"{user_input[CONF_NAME]} ({int(user_input[CONF_ID])})",
                    data=user_input,
                )
        return self.async_show_form(
            step_id="energyusageonly",
            data_schema=_getSchema(self.hass, 0),
            errors=errors,
        )

    async def async_step_energyusagecontrollable(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configuration for controllable devices"""
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = await self.validate_input(user_input)
            if not errors:
                return self.async_create_entry(
                    title=f"{user_input[CONF_NAME]} ({int(user_input[CONF_ID])})",
                    data=user_input,
                )
        return self.async_show_form(
            step_id="energyusagecontrollable",
            data_schema=_getSchema(self.hass, 1),
            errors=errors,
        )

    async def async_step_energyusagecontrollableinterruptable(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configuration for controllable and interruptable devices"""
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = await self.validate_input(user_input)
            if not errors:
                return self.async_create_entry(
                    title=f"{user_input[CONF_NAME]} ({int(user_input[CONF_ID])})",
                    data=user_input,
                )
        return self.async_show_form(
            step_id="energyusagecontrollableinterruptable",
            data_schema=_getSchema(self.hass, 2),
            errors=errors,
        )
