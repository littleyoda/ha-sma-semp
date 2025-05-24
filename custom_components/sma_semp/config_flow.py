"""Config flow for SMA Semp integration."""

from __future__ import annotations

import logging
from typing import Any, cast

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ID, CONF_NAME

from .config_flow_schema import _getSchema
from .const import DOMAIN, MY_KEY

_LOGGER = logging.getLogger(__name__)


class SempConfigFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SMA Semp."""

    VERSION = 1

    async def validate_input(self, user_input: dict[str, Any]) -> dict[str, str]:
        """Validate the user input"""
        errors: dict[str, str] = {}
        # TODO Check min < max ...
        if MY_KEY not in self.hass.data:
            # No other device created yet
            return errors
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
            self._async_abort_entries_match({CONF_NAME: user_input[CONF_NAME]})
            self._async_abort_entries_match({CONF_ID: user_input[CONF_ID]})

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
            self._async_abort_entries_match({CONF_NAME: user_input[CONF_NAME]})
            self._async_abort_entries_match({CONF_ID: user_input[CONF_ID]})

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
            self._async_abort_entries_match({CONF_NAME: user_input[CONF_NAME]})
            self._async_abort_entries_match({CONF_ID: user_input[CONF_ID]})

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

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Reconfigure an existing entry."""
        reconfigure_entry = self._get_reconfigure_entry()

        if user_input is None:
            _LOGGER.error(f"Values {reconfigure_entry.data}")
            schema_typ = 0
            if reconfigure_entry.data.get("minontime", None) is not None:
                schema_typ = 1
            if reconfigure_entry.data.get("onoffswitch", None) is not None:
                schema_typ = 2

            _LOGGER.error(f"Default-Values {reconfigure_entry.data}")
            return self.async_show_form(
                step_id="reconfigure",
                data_schema=self.add_suggested_values_to_schema(
                    _getSchema(
                        self.hass,
                        schema_typ,
                        cast(dict[str, Any], reconfigure_entry.data),
                    ),
                    reconfigure_entry.data,
                ),
            )

        _LOGGER.error(f"User_input  {user_input}")
        self._async_abort_entries_match({CONF_NAME: user_input[CONF_NAME]})
        self._async_abort_entries_match({CONF_ID: user_input[CONF_ID]})

        if (errors := await self.validate_input(user_input)) == {}:
            return self.async_update_reload_and_abort(
                reconfigure_entry, data_updates=user_input
            )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                _getSchema(self.hass, schema_typ, user_input),
                reconfigure_entry.data,
            ),
            errors=errors,
        )
