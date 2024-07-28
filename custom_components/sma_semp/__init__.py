"""The sma integration."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from http import HTTPStatus
from typing import Dict

import aiohttp
from homeassistant.components import http
from homeassistant.components.network import async_get_source_ip
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ConfigEntryNotReady
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.typing import ConfigType
from homeassistant.util import dt as dt_util
from pysmaplus.semp import semp
from pysmaplus.semp.device import sempDevice

from .const import (
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MY_KEY,
    PLATFORMS,
    SempDeviceInfo,
    SempIntegrationData,
    sensor_configuration,
)
from .dataupdater import sempCoordinator

_LOGGER = logging.getLogger(__name__)


class HTTPEndpoint(http.HomeAssistantView):
    """HTTP Endpoint."""

    name = "test"
    url = ""

    def __init__(self, definition) -> None:
        super().__init__()
        self.definition = definition
        self.url = definition["path"]
        self.requires_auth = False

    def addNoCache(self, response: aiohttp.web.Reponse):
        """Add No Cache Header to the responses"""
        response.headers.setdefault(
            "Cache-Control", "no-cache, private, no-store, must-revalidate, max-age=0"
        )
        response.headers.setdefault("Expires", "Thu, 01 Jan 1970 00:00:00 GMT")
        response.headers.setdefault("Pragma", "no-cache")
        return response

    async def get(self, request):
        """Return a get request."""
        if "GET" in self.definition["callback"]:
            return self.addNoCache(await self.definition["callback"]["GET"](request))
        return aiohttp.web.Response(status=HTTPStatus.METHOD_NOT_ALLOWED)

    async def post(self, request):
        """Return a get request."""
        if "POST" in self.definition["callback"]:
            return self.addNoCache(await self.definition["callback"]["POST"](request))
        return aiohttp.web.Response(status=HTTPStatus.METHOD_NOT_ALLOWED)


async def async_setup(
    hass: HomeAssistant, config: ConfigType  # pylint: disable=W0613
) -> bool:
    """Setup Coordinator and start semp-services"""
    tz = dt_util.get_default_time_zone()
    ip = await async_get_source_ip(hass)
    port = None
    if hass.config and hass.config.api:
        port = hass.config.api.port
    if ip is None or ip == "" or port is None:
        _LOGGER.error(f"ip-address and/or port cannot be determined: {ip}:{port}")
        raise HomeAssistantError(
            f"ip-address and/or port cannot be determined: {ip}:{port}"
        )
    _LOGGER.info(f"Binding to {ip}:{port}")
    interval = timedelta(seconds=DEFAULT_SCAN_INTERVAL)

    coordinator = sempCoordinator(hass, _LOGGER, "smasemp", interval)
    control = semp(ip, port, tz, coordinator.sempcallback)
    for route in control.getRoutes():
        x = HTTPEndpoint(route)
        hass.http.register_view(x)

    hass.data[MY_KEY] = SempIntegrationData(control, coordinator, ip, port, {})
    await control.start(embeddedHttpd=False)
    _LOGGER.info("Finish setup %s", hass.data[MY_KEY])
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setup DeviceInfo and start creating sensors"""
    # _LOGGER.error(f"{entry.data["prefix"]} {type(entry.data["prefix"])}")
    sensorConfiguration = sensor_configuration.from_dict(entry.data)
    integrationData = hass.data[MY_KEY]
    prefix = f'{int(entry.data.get("prefix", "11223344")):8}'
    myId = f'{int(entry.data["id"]):12}'
    device_info = DeviceInfo(
        configuration_url="http://"
        + str(integrationData.ip)
        + ":"
        + str(integrationData.port)
        + "/sempinfo",
        identifiers={(DOMAIN, myId)},
        manufacturer="SMA",
        model="SMA Semp Adapter",
        name=entry.data["name"],
        sw_version="0.0.1",
    )
    _LOGGER.debug(
        f"Setup Entry: Testing for {sensorConfiguration.source} {sensorConfiguration.onoffswitch}"
    )
    if hass.states.get(sensorConfiguration.source) is None:
        raise ConfigEntryNotReady(
            f"Sensor {sensorConfiguration.source} not (yet) found for {sensorConfiguration.name}"
        )

    if (
        sensorConfiguration.onoffswitch is not None
        and hass.states.get(sensorConfiguration.onoffswitch) is None
    ):
        raise ConfigEntryNotReady(
            f"Sensor {sensorConfiguration.onoffswitch} not (yet) found for {sensorConfiguration.name}"
        )

    integrationData.sendata[myId] = SempDeviceInfo(
        myId, device_info, entry.unique_id, sensorConfiguration
    )
    await createDevice(integrationData, prefix, myId)
    await integrationData.coordinator.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def createDevice(data: SempIntegrationData, prefix: str, myId: str):
    """Create a pysma.semp.device"""
    assert isinstance(prefix, str)
    assert isinstance(myId, str)
    assert len(myId) == 12
    assert len(prefix) == 8
    devId = f"F-{prefix}-{myId}-00"
    config = data.sendata[myId].configdata
    pysmaDev = sempDevice(
        devId,
        config.name,
        config.semptyp,
        f"{config.id}",
        "None",
        config.sempmaxconsumption,
        config.sempminconsumption,
        timedelta(**config.minontime) if config.minontime else None,
        timedelta(**config.minofftime) if config.minofftime else None,
    )
    data.sempserver.addDevice(pysmaDev)
    data.sendata[myId].device = data.sempserver.getDevice(devId)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    _LOGGER.info("Unload ConfigEntry")
    if unload_ok:
        integrationData = hass.data[MY_KEY]
        myId = f'{int(entry.data["id"]):012}'
        x = integrationData.sendata.pop(myId)
        integrationData.sempserver.removeDevice(x.device)
    return unload_ok
