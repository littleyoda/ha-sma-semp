from typing import Any, Dict, cast
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ID, CONF_NAME
from homeassistant.config_entries import ConfigEntry, ConfigFlowResult
import voluptuous as vol
from homeassistant import config_entries, core
from homeassistant.config_entries import ConfigEntry, ConfigFlowResult
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.issue_registry import IssueSeverity, async_create_issue
from .config_flow_schema import _getSchema, _getConfElemente
from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)


class SMASEMpOptionsConfigFlow(config_entries.OptionsFlow):
    """Handle a pyscript options flow."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize pyscript options flow."""
        self.config_entry = config_entry
        self._show_form = False

    async def async_step_init(
        self, user_input: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        """Manage the pyscript options."""
        if user_input is None:
            _LOGGER.error(f"Values {self.config_entry.data}")
            schemaTyp = 0
            if self.config_entry.data.get("minontime", None) is not None:
                schemaTyp = 1
            if self.config_entry.data.get("onoffswitch", None) is not None:
                schemaTyp = 2

            #            self.config_entry.
            _LOGGER.error(f"Default-Values {self.config_entry.data}")
            return self.async_show_form(
                step_id="init",
                data_schema=_getSchema(
                    self.hass,
                    schemaTyp,
                    cast(Dict[str, Any], self.config_entry.data),
                    True,
                ),
                # TODO data_schema=vol.Schema(
                #     {
                #         vol.Required(
                #             CONF_SCAN_INTERVAL,
                #             default=self.config_entry.data.get(CONF_SCAN_INTERVAL, 5),
                #         ): int
                #     },
                #     extra=vol.ALLOW_EXTRA,
                # ),
            )

        _LOGGER.error(f"User_input  {user_input}")
        if any(
            parameterName not in self.config_entry.data
            or user_input[parameterName] != self.config_entry.data[parameterName]
            for parameterName in _getConfElemente()
        ):
            _LOGGER.error(f"Update started")
            updated_data = self.config_entry.data.copy()
            updated_data.update(user_input)
            self.hass.config_entries.async_update_entry(
                entry=self.config_entry, data=updated_data
            )

            ir.async_create_issue(
                hass=self.hass,
                domain=DOMAIN,
                issue_id=f"restart_required_{self.config_entry.data[CONF_ID]}",
                is_fixable=True,
                is_persistent=False,
                #                    issue_domain=self.data.domain or DOMAIN,
                severity=IssueSeverity.ERROR,
                translation_key="restart_required",
                # translation_placeholders={
                #     "name": self.display_name,
                # },
            )

            return self.async_create_entry(title="", data={})

        # self._show_form = True
        return await self.async_step_no_update()

    async def async_step_no_update(
        self, user_input: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        """Tell user no update to process."""
        # if self._show_form:
        #     self._show_form = False
        #     return self.async_show_form(step_id="no_update", data_schema=vol.Schema({}))

        return self.async_create_entry(title="", data={})
