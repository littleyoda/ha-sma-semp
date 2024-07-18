""" Helper functions """

# from homeassistant.core import HomeAssistant
# from homeassistant.helpers import network
# from urllib.parse import urlparse


async def switchOnOff(hass, entitiyName, onoff: bool) -> None:
    """Switch a entity on or off"""
    status = "on" if onoff else "off"

    await hass.services.async_call(
        "homeassistant",
        "turn_" + status,
        service_data={
            "entity_id": entitiyName,
        },
        blocking=True,
    )


# def getHostip(hass: HomeAssistant):
#     external_url = network.get_url(
#         hass,
#         allow_internal=True,
#         allow_ip=True,
#         require_ssl=False,
#         require_standard_port=False,
#         prefer_external=False,
#         prefer_cloud=False,
#     )
#     parsed = urlparse(external_url)
#     return (parsed.hostname, parsed.port)
