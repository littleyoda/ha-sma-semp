"""Schema for the config-flow"""

import logging
import random
from typing import Any, Dict, List

from pysmaplus.semp import sempDevice
import voluptuous as vol

from homeassistant.components.calendar import DOMAIN as CALENDER_DOMAIN
from homeassistant.components.input_boolean import DOMAIN as INPUT_BOOLEAN_DOMAIN
from homeassistant.components.input_number import DOMAIN as INPUT_NUMBER_DOMAIN
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import ATTR_UNIT_OF_MEASUREMENT, CONF_ID, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import selector
from homeassistant.helpers.selector import SelectSelectorConfig, SelectSelectorMode

_LOGGER = logging.getLogger(__name__)


from .const import (
    CONF_CALENDAR,
    CONF_DEVICE_TYP,
    CONF_MAXRUNNINGTIME,
    CONF_MINOFFTIME,
    CONF_MINONTIME,
    CONF_MINRUNNINGTIME,
    CONF_ONOFFSWITCH,
    CONF_PREFIX,
    CONF_SOURCE_MAXCONSUMPTION,
    CONF_SOURCE_MINCONSUMPTION,
    CONF_SOURCE_SENSOR,
)

ALLOWED_DOMAINS = [INPUT_NUMBER_DOMAIN, SENSOR_DOMAIN]


def _getSchema(
    hass: HomeAssistant,
    include: int,
    values: Dict[str, Any] = {},
    reConfiguration: bool = False,
):
    """Basis Information"""

    entitiesPowerUsage = [
        ent.entity_id
        for ent in hass.states.async_all(ALLOWED_DOMAINS)
        if ent.attributes.get(ATTR_UNIT_OF_MEASUREMENT) in ["W", "kW"]
        or ent.domain == INPUT_NUMBER_DOMAIN
    ]
    entitiesCalendar = [ent.entity_id for ent in hass.states.async_all(CALENDER_DOMAIN)]

    entitiesSwitch = [
        ent.entity_id
        for ent in hass.states.async_all([SWITCH_DOMAIN, INPUT_BOOLEAN_DOMAIN])
    ]

    schema = vol.Schema(
        {
            vol.Required(
                CONF_NAME, default=values.get(CONF_NAME, "")
            ): selector.TextSelector(),
            vol.Required(
                CONF_SOURCE_SENSOR, default=values.get(CONF_SOURCE_SENSOR, None)
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(include_entities=entitiesPowerUsage)
            ),
            vol.Required(
                CONF_DEVICE_TYP, default=values.get(CONF_DEVICE_TYP, None)
            ): selector.SelectSelector(
                SelectSelectorConfig(
                    options=sempDevice.possibleDeviceType(),
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
        }
    )
    if not reConfiguration:
        schema = schema.extend(
            vol.Schema(
                {
                    vol.Optional(
                        CONF_ID,
                        default=values.get(
                            CONF_ID, random.randrange(100000000000, 999999999999)
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0,
                            max=999999999999,
                            step=1,
                            mode=selector.NumberSelectorMode.BOX,
                        ),
                    )
                }
            ).schema
        )

    schema = schema.extend(
        vol.Schema(
            {
                vol.Optional(
                    CONF_SOURCE_MAXCONSUMPTION,
                    default=values.get(CONF_SOURCE_MAXCONSUMPTION, 2000),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0,
                        max=10000,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                    ),
                )
            }
        ).schema
    )
    if include > 0:
        schema = schema.extend(
            vol.Schema(
                {
                    vol.Required(
                        CONF_SOURCE_MINCONSUMPTION,
                        default=values.get(CONF_SOURCE_MINCONSUMPTION, 2000),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0,
                            max=10000,
                            step=1,
                            mode=selector.NumberSelectorMode.BOX,
                        ),
                    ),
                    vol.Optional(
                        CONF_MINRUNNINGTIME,
                        default=values.get(CONF_MINRUNNINGTIME, {"hours": 1}),
                    ): selector.DurationSelector(selector.DurationSelectorConfig()),
                    vol.Optional(
                        CONF_MAXRUNNINGTIME,
                        default=values.get(CONF_MAXRUNNINGTIME, {"hours": 1}),
                    ): selector.DurationSelector(selector.DurationSelectorConfig()),
                    vol.Required(
                        CONF_CALENDAR, default=values.get(CONF_CALENDAR, None)
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(include_entities=entitiesCalendar)
                    ),
                    vol.Required(
                        CONF_ONOFFSWITCH,
                        default=values.get(CONF_ONOFFSWITCH, None),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(include_entities=entitiesSwitch)
                    ),
                }
            ).schema
        )

    if include > 1:
        schema = schema.extend(
            vol.Schema(
                {
                    vol.Optional(
                        CONF_MINONTIME, default={"minutes": 1}
                    ): selector.DurationSelector(selector.DurationSelectorConfig()),
                    vol.Optional(
                        CONF_MINOFFTIME, default={"minutes": 1}
                    ): selector.DurationSelector(selector.DurationSelectorConfig()),
                }
            ).schema
        )
        #
        # min Ausschaltdauer
        # Max Ausschaltdauer

    if reConfiguration:
        schema = schema.extend(
            vol.Schema(
                {
                    vol.Optional(
                        CONF_PREFIX, default=values.get(CONF_PREFIX, "11223344")
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0,
                            max=10**8 - 1,
                            step=1,
                            mode=selector.NumberSelectorMode.BOX,
                        ),
                    )
                }
            ).schema
        )

    return schema
