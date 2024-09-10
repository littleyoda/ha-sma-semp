#from __future__ import annotations

#from ipaddress import ip_network
#from homeassistant.components import network

from typing import Any, Dict, List

#from attr import asdict
import logging
from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
#from homeassistant.helpers import device_registry as dr, entity_registry as er
from dataclasses import asdict
from pysmaplus.semp.device import sempDevice

from .const import DOMAIN, MY_KEY
#from .const import (
#    PYSMA_OBJECT,
#)
_LOGGER = logging.getLogger(__name__)


REDACT_KEYS = {"host", "password", "group", "city", "federalState",
               "latitude","longitude", "street", "streetNo", "zipCode"}


#async def getDevices(hass: HomeAssistant, entry_id: str):
    # devices = []

    # device_registry = dr.async_get(hass)
    # entity_registry = er.async_get(hass)

    # registry_devices = dr.async_entries_for_config_entry(device_registry, entry_id)

    # for device in registry_devices:
    #     entities = []

    #     registry_entities = er.async_entries_for_device(
    #         entity_registry,
    #         device_id=device.id,
    #         include_disabled_entities=True,
    #     )

    #     for entity in registry_entities:
    #         state_dict = None
    #         if state := hass.states.get(entity.entity_id):
    #             state_dict = dict(state.as_dict())
    #             state_dict.pop("context", None)

    #         entities.append({"entry": asdict(entity), "state": state_dict})

    #     devices.append({"device": asdict(device), "entities": entities})
    # return devices
 #   return None

# async def getnetworkConfig(hass: HomeAssistant) -> List[Dict[str, Any]]:
#     adapters = await network.async_get_adapters(hass)
#     netInfo = []
#     for adapter in adapters:
#         for ip_info in adapter["ipv4"]:
#             netInfo.append(
#                 {
#                     "local_ip": ip_info["address"],
#                     "network_prefix": ip_info["network_prefix"],
#                 }
#             )
#     return netInfo


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    diag: dict[str, Any] = {}
    data = hass.data[MY_KEY]
 #   details = hass.data[DOMAIN][entry_id]

    # diag["config"] = config_entry.as_dict()
    # diag["device_info"] = details["device_info"]
    # diag["devices"] = await getDevices(hass, entry_id)
    # diag["values"] = await details[PYSMA_OBJECT].get_debug()
#    diag["netinfo"] = await getnetworkConfig(hass)
    diag = {}
    diag["sendata"] = {}
    for key,item in hass.data[MY_KEY].sendata.items():
        diag["sendata"][key] = item.asdict()
    x = data.sempserver.getDebug()
    diag["status"] = x["status"]
    diag["version"] = "1"
    diag["history"] = []
    for h in x["history"]:
        hh = asdict(h)
        hh["deviceData"] = {}
        for key,item in h.deviceData.items():
            if isinstance(item, sempDevice):
                hh["deviceData"][key] = [item.power, item.status]
            else:
                hh["deviceData"][key] = item.power

        diag["history"].append(hh)
    return async_redact_data(diag, REDACT_KEYS)
